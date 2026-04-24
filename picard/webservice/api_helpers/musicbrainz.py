# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2018-2023, 2026 Philipp Wolfer
# Copyright (C) 2026 metaisfacil
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from collections.abc import (
    Generator,
    Iterable,
    Sequence,
)
import re
from xml.sax.saxutils import quoteattr  # nosec: B406

from PyQt6.QtCore import QUrl

from picard.config import get_config
from picard.const import MUSICBRAINZ_SERVERS
from picard.webservice import (
    CLIENT_STRING,
    PendingRequest,
    ReplyHandler,
)
from picard.webservice.utils import host_port_to_url

from .apihelper import APIHelper


def escape_lucene_query(text: str) -> str:
    return re.sub(r'([+\-&|!(){}\[\]\^"~*?:\\/])', r'\\\1', text)


def build_lucene_query(args: dict) -> str:
    return ' '.join('%s:(%s)' % (item, escape_lucene_query(value)) for item, value in args.items() if value)


def wrap_xml_metadata(data: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">%s</metadata>' % data
    )


class MBAPIHelper(APIHelper):
    @property
    def base_url(self) -> QUrl:
        # we have to keep it dynamic since host/port can be changed via options
        config = get_config()
        host = config.setting['server_host']
        # FIXME: We should get rid of this hard coded exception and move the
        #        configuration to use proper URLs everywhere.
        port = 443 if host in MUSICBRAINZ_SERVERS else config.setting['server_port']
        self._base_url = host_port_to_url(host, port)
        self._base_url.setPath('/ws/2')
        return self._base_url

    def post(self, path: str, data: str | None, handler: ReplyHandler, **kwargs) -> PendingRequest:
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return super().post(path, data, handler, **kwargs)

    def put(self, path: str, data: str | None, handler: ReplyHandler, **kwargs) -> PendingRequest:
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return super().put(path, data, handler, **kwargs)

    def delete(self, path: str, handler: ReplyHandler, **kwargs) -> PendingRequest:
        kwargs['mblogin'] = kwargs.get('mblogin', True)
        return super().delete(path, handler, **kwargs)

    def _get_by_id(
        self, entitytype: str, entityid: str, handler: ReplyHandler, inc: Iterable[str] | None = None, **kwargs
    ) -> PendingRequest:
        if inc:
            kwargs['unencoded_queryargs'] = kwargs.get('queryargs', {})
            kwargs['unencoded_queryargs']['inc'] = self._make_inc_arg(inc)
        return self.get(f"/{entitytype}/{entityid}", handler, **kwargs)

    def get_release_by_id(
        self, releaseid: str, handler: ReplyHandler, inc: Iterable[str] | None = None, **kwargs
    ) -> PendingRequest:
        return self._get_by_id('release', releaseid, handler, inc, **kwargs)

    def get_track_by_id(
        self, trackid: str, handler: ReplyHandler, inc: Iterable[str] | None = None, **kwargs
    ) -> PendingRequest:
        return self._get_by_id('recording', trackid, handler, inc, **kwargs)

    def lookup_discid(
        self, discid: str, handler: ReplyHandler, priority=True, important=True, refresh=False
    ) -> PendingRequest:
        inc = ('artist-credits', 'labels')
        return self._get_by_id(
            'discid',
            discid,
            handler,
            inc,
            queryargs={'cdstubs': 'no'},
            priority=priority,
            important=important,
            refresh=refresh,
        )

    def lookup_toc(
        self, toc: str, handler: ReplyHandler, priority: bool = True, important: bool = True, refresh: bool = False
    ) -> PendingRequest:
        """Lookup a discid by table of contents (TOC) string."""
        inc = ('artist-credits', 'labels')
        queryargs = {
            'toc': toc,
            'cdstubs': 'no',
            'inc': self._make_inc_arg(inc),
        }
        return self.get(
            '/discid/',
            handler,
            unencoded_queryargs=queryargs,
            priority=priority,
            important=important,
            refresh=refresh,
        )

    def _find(self, entitytype: str, handler: ReplyHandler, **kwargs) -> PendingRequest:
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

        return self.get(
            f"/{entitytype}",
            handler,
            unencoded_queryargs=filters,
            priority=True,
            important=True,
            mblogin=False,
            refresh=False,
        )

    def find_releases(self, handler: ReplyHandler, **kwargs) -> PendingRequest:
        return self._find('release', handler, **kwargs)

    def find_tracks(self, handler: ReplyHandler, **kwargs) -> PendingRequest:
        return self._find('recording', handler, **kwargs)

    def find_artists(self, handler: ReplyHandler, **kwargs) -> PendingRequest:
        return self._find('artist', handler, **kwargs)

    @staticmethod
    def _make_inc_arg(inc: Iterable) -> str:
        """
        Convert an iterable to a string to be passed as inc parameter to MB

        It drops non-unique and empty elements, and sort them before joining
        them as a '+'-separated string
        """
        return '+'.join(sorted(set(str(e) for e in inc if e)))

    def _browse(
        self,
        entitytype: str,
        handler: ReplyHandler,
        inc: Iterable[str] | None = None,
        queryargs: dict[str, str] | None = None,
        mblogin: bool = False,
    ) -> PendingRequest:
        if queryargs is None:
            queryargs = {}
        if inc:
            queryargs['inc'] = self._make_inc_arg(inc)
        return self.get(
            f"/{entitytype}",
            handler,
            unencoded_queryargs=queryargs,
            priority=True,
            important=True,
            mblogin=mblogin,
            refresh=False,
        )

    def browse_releases(self, handler: ReplyHandler, **kwargs) -> PendingRequest:
        inc = ('media', 'labels')
        return self._browse('release', handler, inc, queryargs=kwargs)

    def browse_recordings(self, handler: ReplyHandler, inc: Iterable[str], **kwargs) -> PendingRequest:
        return self._browse('recording', handler, inc, queryargs=kwargs)

    @staticmethod
    def _xml_ratings(ratings: dict[tuple[str, str], int]) -> str:
        recordings = ''.join(
            '<recording id=%s><user-rating>%s</user-rating></recording>' % (quoteattr(i[1]), int(j) * 20)
            for i, j in ratings.items()
            if i[0] == 'recording'
        )
        return wrap_xml_metadata('<recording-list>%s</recording-list>' % recordings)

    def submit_ratings(self, ratings: dict[tuple[str, str], int], handler: ReplyHandler) -> PendingRequest:
        params = {'client': CLIENT_STRING}
        data = self._xml_ratings(ratings)
        return self.post(
            "/rating",
            data,
            handler,
            priority=True,
            unencoded_queryargs=params,
            parse_response_type='xml',
            request_mimetype='application/xml; charset=utf-8',
        )

    def get_collection(
        self, collection_id: str | None, handler: ReplyHandler, limit: int = 100, offset: int = 0
    ) -> PendingRequest:
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
        return self.get(path, handler, priority=True, important=True, mblogin=True, unencoded_queryargs=queryargs)

    def get_collection_list(self, handler: ReplyHandler) -> PendingRequest:
        return self.get_collection(None, handler)

    @staticmethod
    def _collection_request(
        collection_id: str, releases: Sequence[str], batchsize: int = 400
    ) -> Generator[str, None, None]:
        for i in range(0, len(releases), batchsize):
            ids = ';'.join(releases[i : i + batchsize])
            yield f"/collection/{collection_id}/releases/{ids}"

    @staticmethod
    def _get_client_queryarg():
        return {'client': CLIENT_STRING}

    def put_to_collection(self, collection_id: str, releases: Sequence[str], handler: ReplyHandler) -> None:
        for path in self._collection_request(collection_id, releases):
            self.put(path, "", handler, unencoded_queryargs=self._get_client_queryarg())

    def delete_from_collection(self, collection_id: str, releases: Sequence[str], handler: ReplyHandler) -> None:
        for path in self._collection_request(collection_id, releases):
            self.delete(path, handler, unencoded_queryargs=self._get_client_queryarg())
