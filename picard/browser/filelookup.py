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

from PyQt4 import QtCore
import os.path
import re
from picard import log
from picard.util import webbrowser2


class FileLookup(object):

    def __init__(self, parent, server, port, localPort):
        self.server = server
        self.localPort = int(localPort)
        self.port = port

    def _encode(self, text):
        return str(QtCore.QUrl.toPercentEncoding(text))

    def launch(self, url):
        log.debug("webbrowser2: %s" % url)
        webbrowser2.open(url)
        return True

    def discLookup(self, url):
        return self.launch("%s&tport=%d" % (url, self.localPort))

    def _lookup(self, type_, id_):
        url = "http://%s:%d/%s/%s?tport=%d" % (
            self._encode(self.server),
            self.port,
            type_,
            id_,
            self.localPort)
        return self.launch(url)

    def trackLookup(self, track_id):
        return self._lookup('recording', track_id)

    def albumLookup(self, album_id):
        return self._lookup('release', album_id)

    def artistLookup(self, artist_id):
        return self._lookup('artist', artist_id)

    def mbidLookup(self, string, type_):
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
        if entity == 'release':
            QtCore.QObject.tagger.load_album(mbid)
            return True
        return self._lookup(entity, mbid)

    def _search(self, type_, query, adv=False):
        if self.mbidLookup(query, type_):
            return True
        url = "http://%s:%d/search/textsearch?limit=25&type=%s&query=%s&tport=%d" % (
            self._encode(self.server),
            self.port,
            type_,
            self._encode(query),
            self.localPort)
        if adv:
            url += "&adv=on"
        return self.launch(url)

    def artistSearch(self, query, adv=False):
        return self._search('artist', query, adv)

    def albumSearch(self, query, adv=False):
        return self._search('release', query, adv)

    def trackSearch(self, query, adv=False):
        return self._search('recording', query, adv)

    def tagLookup(self, artist, release, track, trackNum, duration, filename):
        url = "http://%s:%d/taglookup?tport=%d&artist=%s&release=%s&track=%s&tracknum=%s&duration=%s&filename=%s" % (
            self._encode(self.server),
            self.port,
            self.localPort,
            self._encode(artist),
            self._encode(release),
            self._encode(track),
            trackNum,
            duration,
            self._encode(os.path.basename(filename)))
        return self.launch(url)
