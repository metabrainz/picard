# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2015, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2021 Philipp Wolfer
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


from enum import IntEnum

from picard.const import MB_ATTRIBUTES
from picard.i18n import (
    N_,
    gettext as _,
    pgettext_attributes,
)


# list of types from http://musicbrainz.org/doc/Cover_Art/Types
# order of declaration is preserved in selection box
CAA_TYPES = []
for k, v in sorted(MB_ATTRIBUTES.items(), key=lambda k_v: k_v[0]):
    if k.startswith('DB:cover_art_archive.art_type/name:'):
        CAA_TYPES.append({'name': v.lower(), 'title': v})

# pseudo type, used for the no type case
CAA_TYPES.append({'name': 'unknown', 'title': N_("Unknown")})

CAA_TYPES_TR = {}
for t in CAA_TYPES:
    CAA_TYPES_TR[t['name']] = t['title']


def translate_caa_type(name):
    if name == 'unknown':
        return _(CAA_TYPES_TR[name])
    else:
        title = CAA_TYPES_TR.get(name, name)
        return pgettext_attributes("cover_art_type", title)


# See https://id3.org/id3v2.4.0-frames, 4.14 Attached picture
class Id3ImageType(IntEnum):
    OTHER = 0
    FILE_ICON = 1
    FILE_ICON_OTHER = 2
    COVER_FRONT = 3
    COVER_BACK = 4
    LEAFLET_PAGE = 5
    MEDIA = 6
    LEAD_ARTIST = 7
    ARTIST = 8
    CONDUCTOR = 9
    BAND = 10
    COMPOSER = 11
    LYRICIST = 12
    RECORDING_DURATION = 13
    DURING_RECORDING = 14
    DURING_PERFORMANCE = 15
    VIDEO_SCREEN_CAPTURE = 16
    BRIGHT_COLOURED_FISH = 17
    ILLUSTRATION = 18
    LOGO_ARTIST = 19
    LOGO_STUDIO = 20


__ID3_IMAGE_TYPE_MAP = {
    'obi': Id3ImageType.OTHER,
    'tray': Id3ImageType.OTHER,
    'spine': Id3ImageType.OTHER,
    'sticker': Id3ImageType.OTHER,
    'other': Id3ImageType.OTHER,
    'front': Id3ImageType.COVER_FRONT,
    'back': Id3ImageType.COVER_BACK,
    'booklet': Id3ImageType.LEAFLET_PAGE,
    'track': Id3ImageType.MEDIA,
    'medium': Id3ImageType.MEDIA,
}

__ID3_REVERSE_IMAGE_TYPE_MAP = {v: k for k, v in __ID3_IMAGE_TYPE_MAP.items()}


def image_type_from_id3_num(id3type):
    return __ID3_REVERSE_IMAGE_TYPE_MAP.get(id3type, 'other')


def image_type_as_id3_num(texttype):
    return __ID3_IMAGE_TYPE_MAP.get(texttype, Id3ImageType.OTHER)


def types_from_id3(id3type):
    return [image_type_from_id3_num(id3type)]
