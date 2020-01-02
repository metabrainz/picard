# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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


class VersionError(Exception):
    pass


class Version(tuple):
    _version_re = re.compile(r"(\d+)[._](\d+)(?:[._](\d+)[._]?(?:(dev|a|alpha|b|beta|rc|final)[._]?(\d+))?)?$")

    _identifiers = {
        'dev': 0,
        'alpha': 1,
        'a': 1,
        'beta': 2,
        'b': 2,
        'rc': 3,
        'final': 4
    }

    def __new__(cls, major, minor, patch, identifier='final', revision=0):
        if identifier not in cls.valid_identifiers():
            raise VersionError("Should be either 'final', 'dev', 'alpha', 'beta' or 'rc'")
        identifier = {'a': 'alpha', 'b': 'beta'}.get(identifier, identifier)
        return super(Version, cls).__new__(cls, (major, minor, patch, identifier, revision))

    @classmethod
    def from_string(cls, version_str):
        m = cls._version_re.search(version_str)
        if m:
            g = m.groups()
            if g[2] is None:
                return Version(int(g[0]), int(g[1]), 0, 'final', 0)
            if g[3] is None:
                return Version(int(g[0]), int(g[1]), int(g[2]), 'final', 0)
            return Version(int(g[0]), int(g[1]), int(g[2]), g[3], int(g[4]))
        raise VersionError("String '%s' does not match regex '%s'" % (version_str,
                                                                      cls._version_re.pattern))

    @classmethod
    def valid_identifiers(cls):
        return cls._identifiers.keys()

    def to_string(self, short=False):
        _version = []
        for p in self:
            try:
                n = int(p)
            except ValueError:
                n = p
            _version.append(n)
        if short and _version[3] in ('alpha', 'beta'):
            _version[3] = _version[3][:1]
        version = tuple(_version)
        if short and version[3] == 'final':
            if version[2] == 0:
                version_str = '%d.%d' % version[:2]
            else:
                version_str = '%d.%d.%d' % version[:3]
        elif short and version[3] in ('a', 'b', 'rc'):
            version_str = '%d.%d.%d%s%d' % version
        else:
            version_str = '%d.%d.%d.%s%d' % version
        return version_str

    @property
    def sortkey(self):
        return self[:3] + (self._identifiers.get(self[3], 0), self[4])

    def __str__(self):
        return self.to_string()

    def __lt__(self, other):
        if not isinstance(other, Version):
            other = Version(*other)
        return self.sortkey < other.sortkey

    def __le__(self, other):
        if not isinstance(other, Version):
            other = Version(*other)
        return self.sortkey <= other.sortkey

    def __gt__(self, other):
        if not isinstance(other, Version):
            other = Version(*other)
        return self.sortkey > other.sortkey

    def __ge__(self, other):
        if not isinstance(other, Version):
            other = Version(*other)
        return self.sortkey >= other.sortkey

    def __eq__(self, other):
        if not isinstance(other, Version):
            other = Version(*other)
        return self.sortkey == other.sortkey

    def __ne__(self, other):
        if not isinstance(other, Version):
            other = Version(*other)
        return self.sortkey != other.sortkey

    def __hash__(self):
        return super().__hash__()
