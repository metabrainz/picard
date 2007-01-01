# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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
from PyQt4 import QtCore
from copy import copy
from picard.similarity import similarity
from picard.util import LockableObject, needs_read_lock, needs_write_lock
from musicbrainz2.utils import extractUuid, extractFragment

def _decamelcase(text):
    return re.sub(r'([A-Z])', r' \1', text).strip()

_EXTRA_ATTRS = ['Guest', 'Additional', 'Minor']
def _parse_attributes(attrs):
    attrs = map(_decamelcase, map(extractFragment, attrs))
    prefix = ' '.join([a for a in attrs if a in _EXTRA_ATTRS])
    attrs = [a for a in attrs if a not in _EXTRA_ATTRS]
    if len(attrs) > 1:
        attrs = _('%s and %s') % (', '.join(attrs[:-1]), attrs[-1:][0])
    elif len(attrs) == 1:
        attrs = attrs[0]
    else:
        attrs = ''
    return ' '.join([prefix, attrs]).strip().lower()

class Metadata(LockableObject):
    """List of metadata items with dict-like access."""

    __weights = [
        ('~#length', 16),
        ('title', 20),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 5),
        ('totaltracks', 5),
    ]

    def __init__(self):
        LockableObject.__init__(self)
        self._items = {}
        self.changed = False

    @needs_read_lock
    def __repr__(self):
        return repr(self._items)

    def compare(self, other):
        parts = []
        total = 0.0
        for name, weight in self.__weights:
            a = self[name]
            b = other[name]
            if a and b:
                if name in ('tracknumber', 'totaltracks'):
                    score = 1.0 - abs(cmp(a, b))
                elif name == '~#length':
                    score = 1.0 - min(abs(a - b), 30000) / 30000.0
                else:
                    score = similarity(a, b)
                parts.append((score, weight))
                total += weight
        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    @needs_write_lock
    def copy(self, other):
        self._items = copy(other._items)

    @needs_write_lock
    def update(self, other):
        for name, values in other._items.iteritems():
            self._items[name] = values

    @needs_write_lock
    def clear(self):
        self._items = {}

    def __get(self, name, default=None):
        values = self._items.get(name, None)
        if values:
            if isinstance(values[0], basestring):
                return '; '.join(values)
            else:
                return values[0]
        else:
            return default

    def __set(self, name, values):
        if not isinstance(values, list):
            if isinstance(values, basestring):
                values = list(values.split('; '))
            else:
                values = [values]
        self._items[name] = values

    @needs_read_lock
    def getall(self, name):
        return self._items[name]

    @needs_read_lock
    def get(self, name, default=None):
        return self.__get(name, default)

    @needs_read_lock
    def __getitem__(self, name):
        return self.__get(name, u'')

    @needs_write_lock
    def set(self, name, value):
        self.__set(name, value)

    @needs_write_lock
    def __setitem__(self, name, value):
        self.__set(name, value)
        self.changed = True

    @needs_write_lock
    def add(self, name, value):
        self._items.setdefault(name, []).append(value)

    @needs_read_lock
    def keys(self):
        return self._items.keys()

    def iteritems(self):
        for name, values in self._items.iteritems():
            for value in values:
                yield name, value

    def items(self):
        return list(self.iteritems())

    @needs_read_lock
    def __contains__(self, name):
        for n, v in self._items.iteritems():
            if n == name:
                return True
        return False

    @needs_write_lock
    def __delitem__(self, name):
        del self._items[name]

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
        sortname = self[field + "_sortorder"]
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
            self[field + "_sortorder"] = artist.sortName
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
            "Engineer": "engineer",
            "Audio": "engineer",
            #"Mastering": "engineer",
            "Sound": "engineer",
            "LiveSound": "engineer",
            #"Mix": "engineer",
            #"Recording": "engineer",
            }
        ar_data = {}
        for rel in relations:
            name = None
            if rel.getTargetType() == rel.TO_ARTIST:
                value = rel.target.name
            elif rel.getTargetType() == rel.TO_URL:
                name = "website"
                value = rel.targetId
            else:
                continue
            if name is None:
                reltype = extractFragment(rel.type)
                if reltype == 'Vocal':
                    name = 'performer:' + ' '.join([_parse_attributes(rel.attributes), 'vocal'])
                elif reltype == 'Instrument':
                    name = 'performer:' + _parse_attributes(rel.attributes)
                else:
                    try: name = ar_types[reltype]
                    except KeyError: continue
            ar_data.setdefault(name, []).append(value)
        for name, values in ar_data.items():
            for value in values:
                self.add(name, value)
