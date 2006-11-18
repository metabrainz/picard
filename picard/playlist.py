# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2005,2006 Lukáš Lalinský
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

from picard.util import encode_filename


class PlaylistError(Exception):
    pass


class Playlist:
    """Playlist (M3U/PLS/XSPF) generator. """

    formats = [
      (N_("M3U Playlist (*.m3u)"), ".m3u"), 
      (N_("PLS Playlist (*.pls)"), ".pls"),
      (N_("XSPF Playlist (*.xspf)"), ".xspf"), 
    ]

    def __init__(self, album):
        self.album = album

    def saveM3U(self, w):
        """M3U playlist generator."""
        w("#EXTM3U")
        for track in self.album.tracks:
            w("#EXTINF:%d,%s - %s" % (track.metadata["~#length"] / 1000, track.metadata["artist"], track.metadata["title"]))
            if track.is_linked():
                w(track.linked_file.filename)

    def savePLS(self, w):
        """PLS playlist generator."""
        w("[playlist]")
        i = 1
        for track in self.album.tracks:
            if track.is_linked():
                w(u'File%d=%s' % (i, track.linked_file.filename))
            w("Title%d=%s - %s" % (i, track.metadata["artist"], track.metadata["title"]))
            w("Length%d=%d" % (i, track.metadata["~#length"] / 1000))
            i += 1
        w("NumberOfEntries=%d" % len(self.album.tracks))
        w("Version=2")

    def saveXSPF(self, w):
        """XSPF playlist generator."""
        def escape(string):
            string = string.replace('&', '&amp;') 
            string = string.replace('<', '&lt;')
            string = string.replace('>', '&gt;')
            return string
        w(u'<?xml version="1.0" encoding="UTF-8"?>')
        w(u'<playlist version="1" xmlns="http://xspf.org/ns/0/">')
        w(u'\t<identifier>http://musicbrainz.org/album/%s</identifier>' % escape(self.album.metadata["musicbrainz_albumid"]))
        w(u'\t<trackList>')
        for track in self.album.tracks:
            w(u'\t\t<track>')
            w(u'\t\t\t<title>%s</title>' % escape(track.metadata["title"]))
            w(u'\t\t\t<creator>%s</creator>' % escape(track.metadata["artist"]))
            w(u'\t\t\t<album>%s</album>' % escape(track.metadata["album"]))
            w(u'\t\t\t<trackNum>%s</trackNum>' % track.metadata["tracknumber"])
            w(u'\t\t\t<duration>%d</duration>' % track.metadata["~#length"])
            w(u'\t\t\t<identifier>http://musicbrainz.org/track/%s</identifier>' % escape(track.metadata["musicbrainz_trackid"]))
            if track.is_linked():
                w(u'\t\t\t<location>file://%s</location>' % track.linked_file.filename)
            w(u'\t\t</track>')
        w(u'\t</trackList>')
        w(u'</playlist>')

    def save(self, filename, format):
        lines = []
        w = lines.append
        if format == 0:
            self.saveM3U(w)
        elif format == 1:
            self.savePLS(w)
        elif format == 2:
            self.saveXSPF(w)
        else:
            raise PlaylistError("Unknown playlist format.")
        if not filename.endswith(self.formats[format][1]):
            filename += self.formats[format][1]
        f = file(encode_filename(filename), "wt")
        f.write("\n".join(lines).encode("utf-8"))
        f.close()
