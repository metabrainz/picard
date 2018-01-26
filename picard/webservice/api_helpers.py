# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Sambhav Kothari
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
from PyQt5.QtCore import QUrl
from picard import config, PICARD_VERSION_STR
from picard.const import (ACOUSTID_KEY,
                          ACOUSTID_HOST,
                          ACOUSTID_PORT,
                          CAA_HOST,
                          CAA_PORT)

from picard.webservice import (
    CLIENT_STRING,
    DEFAULT_RESPONSE_PARSER_TYPE,
    ratecontrol,
)

ratecontrol.set_minimum_delay((ACOUSTID_HOST, ACOUSTID_PORT), 333)
ratecontrol.set_minimum_delay((CAA_HOST, CAA_PORT), 0)


def escape_lucene_query(text):
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\/])', r'\\\1', text)


def _wrap_xml_metadata(data):
    return ('<?xml version="1.0" encoding="UTF-8"?>' +
            '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">%s</metadata>' % data)


class APIHelper(object):

    def __init__(self, host, port, api_path, webservice):
        self.host = host
        self.port = port
        self.api_path = api_path
        self._webservice = webservice

    def get(self, path_list, handler, priority=False, important=False, mblogin=False,
                cacheloadcontrol=None, refresh=False, queryargs=None, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE):
        path = self.api_path + "/".join(path_list)
        return self._webservice.get(self.host, self.port, path, handler,
                 priority=priority, important=important, mblogin=mblogin,
                 refresh=refresh, queryargs=queryargs, parse_response_type=parse_response_type)

    def post(self, path_list, data, handler, priority=False, important=False,
                 mblogin=True, queryargs=None, parse_response_type=DEFAULT_RESPONSE_PARSER_TYPE):
        path = self.api_path + "/".join(path_list)
        return self._webservice.post(self.host, self.port, path, data, handler,
                  priority=priority, important=important, mblogin=mblogin,
                  queryargs=queryargs, parse_response_type=parse_response_type)

    def put(self, path_list, data, handler, priority=True, important=False,
                mblogin=True, queryargs=None):
        path = self.api_path + "/".join(path_list)
        return self._webservice.put(self.host, self.port, path, data, handler,
                 priority=priority, important=important, mblogin=mblogin,
                 queryargs=queryargs)

    def delete(self, path_list, handler, priority=True, important=False,
                   mblogin=True, queryargs=None):
        path = self.api_path + "/".join(path_list)
        return self._webservice.delete(self.host, self.port, path, handler,
                 priority=priority, important=important, mblogin=mblogin,
                 queryargs=queryargs)


class MBAPIHelper(APIHelper):

    def __init__(self, webservice):
        super().__init__(config.setting['server_host'], config.setting['server_port'],
                                  "/ws/2/", webservice)

    def _get_by_id(self, entitytype, entityid, handler, inc=None, queryargs=None,
                   priority=False, important=False, mblogin=False, refresh=False):
        path_list = [entitytype, entityid]
        if queryargs is None:
            queryargs = {}
        if inc:
            queryargs["inc"] = "+".join(inc)
        return self.get(path_list, handler,
                        priority=priority, important=important, mblogin=mblogin,
                        refresh=refresh, queryargs=queryargs)

    def get_release_by_id(self, releaseid, handler, inc=None,
                          priority=False, important=False, mblogin=False, refresh=False):
        if inc is None:
            inc = []
        return self._get_by_id('release', releaseid, handler, inc,
                               priority=priority, important=important, mblogin=mblogin, refresh=refresh)

    def get_track_by_id(self, trackid, handler, inc=None,
                        priority=False, important=False, mblogin=False, refresh=False):
        if inc is None:
            inc = []
        return self._get_by_id('recording', trackid, handler, inc,
                               priority=priority, important=important, mblogin=mblogin, refresh=refresh)

    def lookup_discid(self, discid, handler, priority=True, important=True, refresh=False):
        inc = ['artist-credits', 'labels']
        return self._get_by_id('discid', discid, handler, inc, queryargs={"cdstubs": "no"},
                               priority=priority, important=important, refresh=refresh)

    def _find(self, entitytype, handler, **kwargs):
        filters = []

        limit = kwargs.pop("limit")
        if limit:
            filters.append(("limit", limit))

        is_search = kwargs.pop("search", False)
        if is_search:
            if config.setting["use_adv_search_syntax"]:
                query = kwargs["query"]
            else:
                query = escape_lucene_query(kwargs["query"]).strip().lower()
                filters.append(("dismax", 'true'))
        else:
            query = []
            for name, value in kwargs.items():
                value = escape_lucene_query(value).strip().lower()
                if value:
                    query.append('%s:(%s)' % (name, value))
            query = ' '.join(query)

        if query:
            filters.append(("query", query))
        queryargs = {}
        for name, value in filters:
            value = QUrl.toPercentEncoding(string_(value))
            queryargs[string_(name)] = value
        path_list = [entitytype]
        return self.get(path_list, handler, queryargs=queryargs,
                            priority=True, important=True, mblogin=False,
                            refresh=False)

    def find_releases(self, handler, **kwargs):
        return self._find('release', handler, **kwargs)

    def find_tracks(self, handler, **kwargs):
        return self._find('recording', handler, **kwargs)

    def find_artists(self, handler, **kwargs):
        return self._find('artist', handler, **kwargs)

    def _browse(self, entitytype, handler, inc=None, **kwargs):
        path_list = [entitytype]
        queryargs = kwargs
        if inc:
            queryargs["inc"] = "+".join(inc)
        return self.get(path_list, handler, queryargs=queryargs,
                            priority=True, important=True, mblogin=False,
                            refresh=False)

    def browse_releases(self, handler, **kwargs):
        inc = ["media", "labels"]
        return self._browse("release", handler, inc, **kwargs)

    def submit_ratings(self, ratings, handler):
        path_list = ['rating']
        params = {"client": CLIENT_STRING}
        recordings = (''.join(['<recording id="%s"><user-rating>%s</user-rating></recording>' %
            (i[1], j*20) for i, j in ratings.items() if i[0] == 'recording']))

        data = _wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)
        return self.post(path_list, data, handler, priority=True, queryargs=params, parse_response_type="xml")

    def get_collection(self, collection_id, handler, limit=100, offset=0):
        path_list = ["collection"]
        queryargs = None
        if collection_id is not None:
            inc = ["releases", "artist-credits", "media"]
            path_list.extend([collection_id, "releases"])
            queryargs = {}
            queryargs["inc"] = "+".join(inc)
            queryargs["limit"] = limit
            queryargs["offset"] = offset
        return self.get(path_list, handler, priority=True, important=True,
                            mblogin=True, queryargs=queryargs)

    def get_collection_list(self, handler):
        return self.get_collection(None, handler)

    def _collection_request(self, collection_id, releases):
        while releases:
            ids = ";".join(releases if len(releases) <= 400 else releases[:400])
            releases = releases[400:]
            yield ["collection", collection_id, "releases", ids]

    def _get_client_queryarg(self):
        return {"client": CLIENT_STRING}

    def put_to_collection(self, collection_id, releases, handler):
        for path_list in self._collection_request(collection_id, releases):
            self.put(path_list, "", handler,
                     queryargs=self._get_client_queryarg())

    def delete_from_collection(self, collection_id, releases, handler):
        for path_list in self._collection_request(collection_id, releases):
            self.delete(path_list, handler,
                        queryargs=self._get_client_queryarg())


class AcoustIdAPIHelper(APIHelper):

    def __init__(self, webservice):
        super().__init__(ACOUSTID_HOST, ACOUSTID_PORT,
                                    '/v2/', webservice)

    def _encode_acoustid_args(self, args, format_='json'):
        filters = []
        args['client'] = ACOUSTID_KEY
        args['clientversion'] = PICARD_VERSION_STR
        args['format'] = format_
        for name, value in args.items():
            value = string_(QUrl.toPercentEncoding(value))
            filters.append('%s=%s' % (string_(name), value))
        return '&'.join(filters)

    def query_acoustid(self, handler, **args):
        path_list = ['lookup']
        body = self._encode_acoustid_args(args)
        return self.post(path_list, body, handler, priority=False, important=False, mblogin=False)

    def submit_acoustid_fingerprints(self, submissions, handler):
        path_list = ['submit']
        args = {'user': config.setting["acoustid_apikey"]}
        for i, submission in enumerate(submissions):
            args['fingerprint.%d' % i] = string_(submission.fingerprint)
            args['duration.%d' % i] = string_(submission.duration)
            args['mbid.%d' % i] = string_(submission.recordingid)
            if submission.puid:
                args['puid.%d' % i] = string_(submission.puid)
        body = self._encode_acoustid_args(args, format_='json')
        return self.post(path_list, body, handler, priority=True, important=False, mblogin=False)
