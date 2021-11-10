# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Vladislav Karbovskii
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


# List of available scripts (character sets)
SCRIPTS = {
    'GREEK': N_('Greek'),
    'CYRILLIC': N_('Cyrillic'),
    'LATIN': N_('Latin'),
    'ARABIC': N_('Arabic'),
    'HEBREW': N_('Hebrew'),
    'CJK': N_('Chinese'),
    'HANGUL': N_('Hangul'),
    'HIRAGANA': N_('Hiragana'),
    'KATAKANA': N_('Katakana'),
    'THAI': N_('Thai')
}


def scripts_sorted_by_localized_name():
    for script_id, label in sorted([(k, _(v)) for k, v in SCRIPTS.items()], key=lambda i: i[1]):
        yield script_id, label
