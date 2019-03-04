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

import re

PICARD_ORG_NAME = "MusicBrainz"
PICARD_APP_NAME = "Picard"
PICARD_VERSION = (2, 2, 0, 'dev', 1)


# optional build version
# it should be in the form '<platform>_<YYMMDDHHMMSS>'
# ie. win32_20140415091256
PICARD_BUILD_VERSION_STR = ""


class VersionError(Exception):
    pass


def version_to_string(version, short=False):
    if len(version) != 5:
        raise VersionError("Length != 5")
    if version[3] not in ('final', 'dev'):
        raise VersionError("Should be either 'final' or 'dev'")
    _version = []
    for p in version:
        try:
            n = int(p)
        except ValueError:
            n = p
        _version.append(n)
    version = tuple(_version)
    if short and version[3] == 'final':
        if version[2] == 0:
            version_str = '%d.%d' % version[:2]
        else:
            version_str = '%d.%d.%d' % version[:3]
    else:
        version_str = '%d.%d.%d.%s%d' % version
    return version_str


_version_re = re.compile(r"(\d+)[._](\d+)(?:[._](\d+)[._]?(?:(dev|final)[._]?(\d+))?)?$")


def version_from_string(version_str):
    m = _version_re.search(version_str)
    if m:
        g = m.groups()
        if g[2] is None:
            return (int(g[0]), int(g[1]), 0, 'final', 0)
        if g[3] is None:
            return (int(g[0]), int(g[1]), int(g[2]), 'final', 0)
        return (int(g[0]), int(g[1]), int(g[2]), g[3], int(g[4]))
    raise VersionError("String '%s' does not match regex '%s'" % (version_str,
                                                                  _version_re.pattern))


PICARD_VERSION_STR = version_to_string(PICARD_VERSION)
PICARD_VERSION_STR_SHORT = version_to_string(PICARD_VERSION, short=True)
if PICARD_BUILD_VERSION_STR:
    __version__ = "%s_%s" % (PICARD_VERSION_STR, PICARD_BUILD_VERSION_STR)
    PICARD_FANCY_VERSION_STR = "%s (%s)" % (PICARD_VERSION_STR_SHORT,
                                            PICARD_BUILD_VERSION_STR)
else:
    __version__ = PICARD_VERSION_STR_SHORT
    PICARD_FANCY_VERSION_STR = PICARD_VERSION_STR_SHORT

# Keep those ordered
api_versions = [
    "2.0",
    "2.1",
    "2.2",
]
