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

PICARD_VERSION = (1, 3, 0, 'dev', 1)


def version_to_string(version_tuple, short=False):
    assert len(version_tuple) == 5
    assert version_tuple[3] in ('final', 'dev')
    if short and version_tuple[3] == 'final':
        if version_tuple[2] == 0:
            version_str = '%d.%d' % version_tuple[:2]
        else:
            version_str = '%d.%d.%d' % version_tuple[:3]
    else:
        version_str = '%d.%d.%d%s%d' % version_tuple
    return version_str


def version_from_string(version_str):
    g = re.match(r"^(\d+).(\d+).(\d+)(dev|final)(\d+)$", version_str).groups()
    return (int(g[0]), int(g[1]), int(g[2]), g[3], int(g[4]))


__version__ = PICARD_VERSION_STR = version_to_string(PICARD_VERSION)
PICARD_VERSION_STR_SHORT = version_to_string(PICARD_VERSION, short=True)

api_versions = ["0.15.0", "0.15.1", "0.16.0", "1.0.0", "1.1.0", "1.2.0"]
