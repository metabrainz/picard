# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (c) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
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

import os.path
import re

from PyQt5 import QtCore

from picard import log
from picard.const import (
    PICARD_URLS,
    QUERY_LIMIT,
)
from picard.util import (
    build_qurl,
    webbrowser2,
)


class FileLookup(object):

    def __init__(self, parent, server, port, local_port):
        self.server = server
        self.local_port = int(local_port)
        self.port = port

    def _url(self, path, params=None):
        if params is None:
            params = {}
        if self.local_port:
            params['tport'] = self.local_port
        url = build_qurl(self.server, self.port, path=path, queryargs=params)
        return bytes(url.toEncoded()).decode()

    def _build_launch(self, path, params=None):
        if params is None:
            params = {}
        return self.launch(self._url(path, params))

    def launch(self, url):
        log.debug("webbrowser2: %s" % url)
        webbrowser2.open(url)
        return True

    def disc_lookup(self, url):
        if self.local_port:
            url = "%s&tport=%d" % (url, self.local_port)
        return self.launch(url)

    def _lookup(self, type_, id_):
        return self._build_launch("/%s/%s" % (type_, id_))

    def recording_lookup(self, recording_id):
        return self._lookup('recording', recording_id)

    def album_lookup(self, album_id):
        return self._lookup('release', album_id)

    def artist_lookup(self, artist_id):
        return self._lookup('artist', artist_id)

    def track_lookup(self, track_id):
        return self._lookup('track', track_id)

    def work_lookup(self, work_id):
        return self._lookup('work', work_id)

    def release_group_lookup(self, release_group_id):
        return self._lookup('release-group', release_group_id)

    def acoust_lookup(self, acoust_id):
        return self.launch(PICARD_URLS['acoustid_track'] + acoust_id)

    def mbid_lookup(self, string, type_, mbid_matched_callback=None):
        """Parses string for known entity type and mbid, open browser for it
        If entity type is 'release', it will load corresponding release if
        possible.
        """
        uuid = '[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}'
        entity_type = '(?:release-group|release|recording|work|artist|label|url|area|track)'
        regex = r"\b(%s)?\W*(%s)" % (entity_type, uuid)
        m = re.search(regex, string, re.IGNORECASE)
        if m is None:
            return False
        if m.group(1) is None:
            entity = type_
        else:
            entity = m.group(1).lower()
        mbid = m.group(2).lower()
        if mbid_matched_callback:
            mbid_matched_callback(entity, mbid)
        if entity == 'release':
            QtCore.QObject.tagger.load_album(mbid)
            return True
        return self._lookup(entity, mbid)

    def tag_lookup(self, artist, release, track, trackNum, duration, filename):
        params = {
            'artist': artist,
            'release': release,
            'track': track,
            'tracknum': trackNum,
            'duration': duration,
            'filename': os.path.basename(filename),
        }
        return self._build_launch('/taglookup', params)

    def collection_lookup(self, userid):
        return self._build_launch('/user/%s/collections' % userid)

    def search_entity(self, type_, query, adv=False, mbid_matched_callback=None):
        if self.mbid_lookup(query, type_, mbid_matched_callback=mbid_matched_callback):
            return True
        params = {
            'limit': QUERY_LIMIT,
            'type': type_,
            'query': query,
        }
        if adv:
            params['adv'] = 'on'
        return self._build_launch('/search/textsearch', params)
