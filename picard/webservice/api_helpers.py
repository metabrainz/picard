# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2018-2023 Philipp Wolfer
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import re
from xml.sax.saxutils import quoteattr  # nosec: B404

from PyQt6.QtCore import QUrl

from picard import PICARD_VERSION_STR
from picard.config import get_config
from picard.const import (
    ACOUSTID_KEY,
    ACOUSTID_URL,
    MUSICBRAINZ_SERVERS,
)
from picard.util import encoded_queryargs
from picard.webservice import (
    CLIENT_STRING,
    ratecontrol,
)
from picard.webservice.utils import host_port_to_url


ratecontrol.set_minimum_delay_for_url(ACOUSTID_URL, 333)


def escape_lucene_query(text):
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\/])', r'\\\1', text)


def build_lucene_query(args):
    return ' '.join('%s:(%s)' % (item, escape_lucene_query(value))
                    for item, value in args.items() if value)


def _wrap_xml_metadata(data):
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">%s</metadata>'
            % data)


class APIHelper:
    _base_url = None

    def __init__(self, webservice, base_url=None):
        self._webservice = webservice
        if base_url is not None:
            self.base_url = base_url

    @property
    def base_url(self):
        if self._base_url is None:
            raise ValueError("base_url undefined")
        return self._base_url

    @base_url.setter
    def base_url(self, url):
        if not isinstance(url, QUrl):
            url = QUrl(url)
        self._base_url = url

    @property
    def webservice(self):
        return self._webservice

    def url_from_path(self, path):
        url = QUrl(self.base_url)
        url.setPath(url.path() + path)
        return url

    def get(self, path, handler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        return self._webservice.get_url(**kwargs)

    def post(self, path, data, handler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        kwargs['data'] = data
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self._webservice.post_url(**kwargs)

    def put(self, path, data, handler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        kwargs['data'] = data
        kwargs['priority'] = kwargs.get('priority', True)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self._webservice.put_url(**kwargs)

    def delete(self, path, handler, **kwargs):
        kwargs['url'] = self.url_from_path(path)
        kwargs['handler'] = handler
        kwargs['priority'] = kwargs.get('priority', True)
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return self._webservice.delete_url(**kwargs)


class MBAPIHelper(APIHelper):
    @property
    def base_url(self):
        # we have to keep it dynamic since host/port can be changed via options
        config = get_config()
        host = config.setting['server_host']
        # FIXME: We should get rid of this hard coded exception and move the
        #        configuration to use proper URLs everywhere.
        port = 443 if host in MUSICBRAINZ_SERVERS else config.setting['server_port']
        self._base_url = host_port_to_url(host, port)
        self._base_url.setPath('/ws/2')
        return self._base_url

    def _get_by_id(self, entitytype, entityid, handler, inc=None, **kwargs):
        if inc:
            kwargs['unencoded_queryargs'] = kwargs.get('queryargs', {})
            kwargs['unencoded_queryargs']['inc'] = self._make_inc_arg(inc)
        return self.get(f"/{entitytype}/{entityid}", handler, **kwargs)

    def get_release_by_id(self, releaseid, handler, inc=None, **kwargs):
        return self._get_by_id('release', releaseid, handler, inc, **kwargs)

    def get_track_by_id(self, trackid, handler, inc=None, **kwargs):
        return self._get_by_id('recording', trackid, handler, inc, **kwargs)

    def lookup_discid(self, discid, handler, priority=True, important=True, refresh=False):
        inc = ('artist-credits', 'labels')
        return self._get_by_id('discid', discid, handler, inc, queryargs={'cdstubs': 'no'},
                               priority=priority, important=important, refresh=refresh)

    def _find(self, entitytype, handler, **kwargs):
        filters = {}

        limit = kwargs.pop('limit')
        if limit:
            filters['limit'] = limit

        is_search = kwargs.pop('search', False)
        if is_search:
            config = get_config()
            use_advanced_search = kwargs.pop('advanced_search', config.setting['use_adv_search_syntax'])
            if use_advanced_search:
                query = kwargs['query']
            else:
                query = escape_lucene_query(kwargs['query']).strip().lower()
                filters['dismax'] = 'true'
        else:
            query = build_lucene_query(kwargs)

        if query:
            filters['query'] = query

        return self.get(f"/{entitytype}", handler, unencoded_queryargs=filters,
                        priority=True, important=True, mblogin=False,
                        refresh=False)

    def find_releases(self, handler, **kwargs):
        return self._find('release', handler, **kwargs)

    def find_tracks(self, handler, **kwargs):
        return self._find('recording', handler, **kwargs)

    def find_artists(self, handler, **kwargs):
        return self._find('artist', handler, **kwargs)

    @staticmethod
    def _make_inc_arg(inc):
        """
        Convert an iterable to a string to be passed as inc paramater to MB

        It drops non-unique and empty elements, and sort them before joining
        them as a '+'-separated string
        """
        return '+'.join(sorted(set(str(e) for e in inc if e)))

    def _browse(self, entitytype, handler, inc=None, queryargs=None, mblogin=False):
        if queryargs is None:
            queryargs = {}
        if inc:
            queryargs['inc'] = self._make_inc_arg(inc)
        return self.get(f"/{entitytype}", handler, unencoded_queryargs=queryargs,
                        priority=True, important=True, mblogin=mblogin,
                        refresh=False)

    def browse_releases(self, handler, **kwargs):
        inc = ('media', 'labels')
        return self._browse('release', handler, inc, queryargs=kwargs)

    def browse_recordings(self, handler, inc, **kwargs):
        return self._browse('recording', handler, inc, queryargs=kwargs)

    @staticmethod
    def _xml_ratings(ratings):
        recordings = ''.join(
            '<recording id=%s><user-rating>%s</user-rating></recording>' %
            (quoteattr(i[1]), int(j)*20) for i, j in ratings.items() if i[0] == 'recording'
        )
        return _wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)

    def submit_ratings(self, ratings, handler):
        params = {'client': CLIENT_STRING}
        data = self._xml_ratings(ratings)
        return self.post("/rating", data, handler, priority=True,
                         unencoded_queryargs=params, parse_response_type='xml',
                         request_mimetype='application/xml; charset=utf-8')

    def get_collection(self, collection_id, handler, limit=100, offset=0):
        if collection_id is not None:
            inc = ('releases', 'artist-credits', 'media')
            path = f"/collection/{collection_id}/releases"
            queryargs = {
                'inc': self._make_inc_arg(inc),
                'limit': limit,
                'offset': offset,
            }
        else:
            path = '/collection'
            queryargs = None
        return self.get(path, handler, priority=True, important=True,
                        mblogin=True, unencoded_queryargs=queryargs)

    def get_collection_list(self, handler):
        return self.get_collection(None, handler)

    @staticmethod
    def _collection_request(collection_id, releases, batchsize=400):
        for i in range(0, len(releases), batchsize):
            ids = ';'.join(releases[i:i+batchsize])
            yield f"/collection/{collection_id}/releases/{ids}"

    @staticmethod
    def _get_client_queryarg():
        return {'client': CLIENT_STRING}

    def put_to_collection(self, collection_id, releases, handler):
        for path in self._collection_request(collection_id, releases):
            self.put(path, "", handler,
                     unencoded_queryargs=self._get_client_queryarg())

    def delete_from_collection(self, collection_id, releases, handler):
        for path in self._collection_request(collection_id, releases):
            self.delete(path, handler,
                        unencoded_queryargs=self._get_client_queryarg())


class AcoustIdAPIHelper(APIHelper):

    client_key = ACOUSTID_KEY
    client_version = PICARD_VERSION_STR

    def __init__(self, webservice):
        super().__init__(webservice, base_url=ACOUSTID_URL)

    def _encode_acoustid_args(self, args):
        args['client'] = self.client_key
        args['clientversion'] = self.client_version
        args['format'] = 'json'
        return '&'.join((k + '=' + v for k, v in encoded_queryargs(args).items()))

    def query_acoustid(self, handler, **args):
        body = self._encode_acoustid_args(args)
        return self.post(
            "/lookup", body, handler, priority=False, important=False,
            mblogin=False, request_mimetype='application/x-www-form-urlencoded'
        )

    @staticmethod
    def _submissions_to_args(submissions):
        config = get_config()
        args = {'user': config.setting['acoustid_apikey']}
        for i, submission in enumerate(submissions):
            for key, value in submission.args.items():
                if value:
                    args[".".join((key, str(i)))] = value
        return args

    def submit_acoustid_fingerprints(self, submissions, handler):
        args = self._submissions_to_args(submissions)
        body = self._encode_acoustid_args(args)
        return self.post(
            "/submit", body, handler, priority=True, important=False,
            mblogin=False, request_mimetype='application/x-www-form-urlencoded'
        )
