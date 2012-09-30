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
from picard.util import webbrowser2

class FileLookup(object):

    def __init__(self, parent, server, port, localPort):
        self.server = server
        self.localPort = int(localPort)
        self.port = port

    def _encode(self, text):
        return str(QtCore.QUrl.toPercentEncoding(text))

    def launch(self, url):
        webbrowser2.open(url)

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

    def _search(self, type_, query, adv=False):
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
