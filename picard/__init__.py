# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2014 Lukáš Lalinský
# Copyright (C) 2009, 2018-2020 Philipp Wolfer
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013-2019 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Wieland Hoffmann
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2018 Bob Swift
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


from picard.version import (
    Version,
    VersionError,
)


PICARD_ORG_NAME = "MusicBrainz"
PICARD_APP_NAME = "Picard"
PICARD_DISPLAY_NAME = "MusicBrainz Picard"
PICARD_APP_ID = "org.musicbrainz.Picard"
PICARD_DESKTOP_NAME = PICARD_APP_ID + ".desktop"
PICARD_VERSION = Version(2, 6, 0, 'final', 0)


# optional build version
# it should be in the form '<platform>_<YYMMDDHHMMSS>'
# ie. win32_20140415091256
PICARD_BUILD_VERSION_STR = ""


def version_to_string(version, short=False):
    """Deprecated: Use picard.version.Version.to_string instead"""
    if len(version) != 5:
        raise VersionError("Length != 5")
    if not isinstance(version, Version):
        version = Version(*version)
    return version.to_string(short=short)


def version_from_string(version_str):
    """Deprecated: Use picard.version.Version.from_string instead"""
    return Version.from_string(version_str)


PICARD_VERSION_STR = PICARD_VERSION.to_string()
PICARD_VERSION_STR_SHORT = PICARD_VERSION.to_string(short=True)
if PICARD_BUILD_VERSION_STR:
    __version__ = "%s+%s" % (PICARD_VERSION_STR, PICARD_BUILD_VERSION_STR)
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
    "2.3",
    "2.4",
    "2.5",
    "2.6",
]

api_versions_tuple = [Version.from_string(v) for v in api_versions]
