# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Laurent Monin
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

from picard.const import MB_ATTRIBUTES
from picard.i18n import gettext_attr

# list of types from http://musicbrainz.org/doc/Cover_Art/Types
# order of declaration is preserved in selection box
CAA_TYPES = []
for k, v in sorted(MB_ATTRIBUTES.items(), key=lambda k_v: k_v[0]):
    if k.startswith('DB:cover_art_archive.art_type/name:'):
        CAA_TYPES.append({'name': v.lower(), 'title': v})

# pseudo type, used for the no type case
CAA_TYPES.append({'name': "unknown", 'title': N_("Unknown")})

CAA_TYPES_TR = {}
for t in CAA_TYPES:
    CAA_TYPES_TR[t['name']] = t['title']


def translate_caa_type(name):
    if name == 'unknown':
        return _(CAA_TYPES_TR[name])
    else:
        title = CAA_TYPES_TR.get(name, name)
        return gettext_attr(title, "cover_art_type")
