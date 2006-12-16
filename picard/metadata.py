# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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
from copy import copy
from picard.similarity import similarity
from picard.util import LockableObject, needs_read_lock, needs_write_lock
from musicbrainz2.model import Artist
from musicbrainz2.utils import extractUuid, extractFragment


class Metadata(LockableObject):
    
    """List of metadata items with dict-like access.

    Special tags:
        * ~#length
        * ~filename
    
    @see http://wiki.musicbrainz.org/UnifiedTagging
    """
    
    def __init__(self):
        LockableObject.__init__(self)
        self._items = []
        self.changed = False

    @needs_read_lock
    def __repr__(self):
        return repr(self._items)

    def compare(self, other):
        parts = []
        
        tags = {
            "~#length": 16,
            "title": 20,
            "artist": 6,
            "album": 12,
            "tracknumber": 5,
            "totaltracks": 5,
        }

        identical = [
            "musicbrainz_trackid",
            "musicbrainz_artistid",
            "musicbrainz_albumid",
            "tracknumber",
            "totaltracks",
            "discnumber",
            "totaldiscs",
        ]

        #for tag in self.keys():
        #    if tag not in tags and not tag.startswith("~"):
        #        tags[tag] = 1

        #for tag in other.keys():
        #    if tag not in tags and not tag.startswith("~"):
        #        tags[tag] = 1

        for tag, weight in tags.items():
            if self[tag] and other[tag]:
                if tag in identical:
                    sim = 1.0 - abs(cmp(self[tag], other[tag]))
                elif tag == "~#length":
                    sim = 1.0 - min(abs(self[tag] - other[tag]), 30000) / 30000.0
                else:
                    sim = similarity(self[tag], other[tag])
                parts.append((sim, weight))

        total = reduce(lambda x, y: x + y[1], parts, 0.0)
        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    @needs_write_lock
    def copy(self, other):
        self._items = copy(other.items())

    @needs_write_lock
    def clear(self):
        self._items = []

    def __get(self, name, default=None):
        name = name.lower()
        values = self.getall(name)
        if values:
            if isinstance(values[0], basestring):
                return " / ".join(values)
            else:
                return values[0]
        else:
            return default

    def __set(self, name, values):
        name = name.lower()
        self._items = filter(lambda a: a[0] != name, self._items)
        if not isinstance(values, list):
            self._items.append((name, values))
        else:
            for value in values:
                self._items.append((name, value))

    @needs_read_lock
    def getall(self, name):
        return [v for n, v in self._items if n == name]

    @needs_read_lock
    def get(self, name, default=None):
        return self.__get(name, default)

    @needs_write_lock
    def add(self, name, value):
        self._items.append((name.lower(), value))

    @needs_write_lock
    def set(self, name, value):
        self.set(name, value)

    @needs_read_lock
    def __getitem__(self, name):
        return self.__get(name, u"")
        
    @needs_write_lock
    def __setitem__(self, name, value):
        self.__set(name, value)
        self.changed = True

    @needs_read_lock
    def keys(self):
        return list(set([n for n, v in self._items]))

    @needs_read_lock
    def items(self):
        return self._items

    @needs_read_lock
    def __contains__(self, name):
        name = name.lower()
        for n, v in self._items:
            if n == name:
                return True
        return False

    @needs_write_lock
    def __delitem__(self, name):
        name = name.lower()
        self._items = filter(lambda a: a[0] != name, self._items)

    @needs_write_lock
    def set_changed(self, changed=True):
        self.changed = changed

    def _reverse_sortname(self, sortname):
        """Reverse sortnames."""
        chunks = map(unicode.strip, sortname.split(u","))
        if len(chunks) == 2:
            return u"%s %s" % (chunks[1], chunks[0])
        elif len(chunks) == 3:
            return u"%s %s %s" % (chunks[2], chunks[1], chunks[0])
        elif len(chunks) == 4:
            return u"%s %s, %s %s" % (chunks[1], chunks[0], chunks[3], chunks[2])
        else:
            return sortname.strip()

    def _translate_artist(self, field="artist"):
        """'Translate' the artist name by reversing the sortname."""
        import unicodedata
        name = self[field]
        sortname = self[field + "_sortname"]
        for c in name:
            ctg = unicodedata.category(c)
            if (ctg[0] not in ("P", "Z") and ctg != "Nd" and
                unicodedata.name(c).find("LATIN") == -1):
                return " & ".join(map(reverse_sortname, sortname.split("&")))
        return name 

    def from_artist(self, artist, field="artist"):
        """Generate metadata items from an artist."""
        self["musicbrainz_" + field + "id"] = extractUuid(artist.id)
        if artist.name is not None:
            self[field] = artist.name
        if artist.sortName is not None:
            self[field + "_sortname"] = artist.sortName
        if self.config.setting["translate_artist_names"]:
            self._translate_artist(field)

    def from_track(self, track, release=None):
        """Generate metadata items from a track."""
        self["musicbrainz_trackid"] = extractUuid(track.id)
        if track.title is not None:
            self["title"] = track.title
        self["~#length"] = track.duration or 0
        if not release and track.releases:
            release = track.releases[0]
        self.from_release(release)
        if track.artist is not None:
            self.from_artist(track.artist)
        elif release and release.artist is not None:
            self.from_artist(release.artist)
        if release and release.tracks:
            self["tracknumber"] = str(release.tracks.index(track) + 1)
            self["totaltracks"] = str(len(release.tracks))

    def from_release(self, release):
        """Generate metadata items from a release."""
        self["musicbrainz_albumid"] = extractUuid(release.id)
        if release.title is not None:
            self["album"] = release.title
        if release.artist is not None:
            self.from_artist(release.artist, field="albumartist")
            self["artist"] = self["albumartist"]
        if release.tracks:
            if release.isSingleArtistRelease():
                self["compilation"] = "0"
            else:
                self["compilation"] = "1"
        if release.releaseEvents:
            date = release.getEarliestReleaseDate()
            if date is not None:
                self["date"] = date
        if release.asin is not None:
            self["asin"] = release.asin
        if hasattr(release, "tracksOffset") and release.tracksOffset:
            self["tracknumber"] = release.tracksOffset
        if hasattr(release, "tracksCount") and release.tracksCount:
            self["totaltracks"] = release.tracksCount

    def from_relations(self, relations):
        """Generate metadata items from ARs."""
        ar_types = {
            "Composer": "composer",
            "Conductor": "conductor", 
            "PerformingOrchestra": "ensemble",
            "Arranger": "arranger",
            "Orchestrator": "arranger",
            "Instrumentator": "arranger",
            "Lyricist": "lyricist",
            "Remixer": "remixer",
            "Producer": "producer",
            }
        ar_data = {}
        for rel in relations:
            if isinstance(rel.target, Artist):
                value = rel.target.name
            else:
                continue
            try:
                name = ar_types[extractFragment(rel.type)]
            except KeyError:
                continue
            ar_data.setdefault(name, []).append(value)
        for name, values in ar_data.items():
            for value in values:
                self.add(name, value)
