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

# list of types from http://musicbrainz.org/doc/Cover_Art/Types
# order of declaration is preserved in selection box
CAA_TYPES = [
    {'name': "front",   'title': N_("Front")},
    {'name': "back",    'title': N_("Back")},
    {'name': "booklet", 'title': N_("Booklet")},
    {'name': "medium",  'title': N_("Medium")},
    {'name': "tray",    'title': N_("Tray")},
    {'name': "obi",     'title': N_("Obi")},
    {'name': "spine",   'title': N_("Spine")},
    {'name': "track",   'title': N_("Track")},
    {'name': "sticker", 'title': N_("Sticker")},
    {'name': "other",   'title': N_("Other")},
    {'name': "unknown", 'title': N_("Unknown")}, # pseudo type, used for the no type case
]

CAA_TYPES_SEPARATOR = ' '  #separator to use when joining/splitting list of types
