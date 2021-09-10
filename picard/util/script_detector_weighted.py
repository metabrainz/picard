# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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


from enum import (
    IntEnum,
    unique,
)
import unicodedata as ud


@unique
class ScriptSelectionOrder(IntEnum):
    """Character set script selection order
    """
    SPECIFIED = 0
    WEIGHTED = 1


# Provide weighting factors to take into account character sets that use fewer (or more)
# characters to convey the same information as other characters sets.  The factor is generally
# based on the relative number of characters in the alphabet compared with the LATIN alphabet.
SCRIPT_WEIGHTING_FACTORS = {
    "LATIN": 1.0,
    "CYRILLIC": 1.02,
    "GREEK": 0.92,
    "ARABIC": 1.08,
    "HEBREW": 0.85,
    "CJK": 2.5,
    "HANGUL": 0.92,
    "HIRAGANA": 1.77,
    "KATAKANA": 1.77,
    "THAI": 1.69,
}


def detect_script_weighted(string_to_check, threshhold=0.0):
    """Provide a dictionary of the unicode scripts found in the supplied string that meet
    or exceed the specified weighting threshhold based on the number of characters matching
    the script as a weighted percentage of the number of characters matching all scripts.

    Args:
        string_to_check (str): The unicode string to check
        threshhold (float, optional): Minimum threshhold to include in the results. Defaults to 0.

    Returns:
        dict: Dictionary of the scripts represented in the string with their threshhold values.
    """
    scripts = {}
    total_weighting = 0
    for character in string_to_check:
        if character.isalpha():
            script_id = ud.name(character).split(' ')[0]
            weighting_factor = SCRIPT_WEIGHTING_FACTORS[script_id] if script_id in SCRIPT_WEIGHTING_FACTORS else 1
            scripts[script_id] = (scripts[script_id] if script_id in scripts else 0) + weighting_factor
            total_weighting += weighting_factor
    # Normalize weightings to a float between 0 and 1 inclusive.
    for key in scripts:
        scripts[key] /= total_weighting
    return dict(filter(lambda item: item[1] >= threshhold, scripts.items()))


def list_script_weighted(string_to_check, threshhold=0.0):
    """Provide a list of the unicode scripts found in the supplied string that meet
    or exceed the specified weighting threshhold based on the number of characters
    matching the script as a weighted percentage of the number of characters matching
    all scripts.  The list is sorted in descending order of weighted values.

    Args:
        string_to_check (str): The unicode string to check
        threshhold (float, optional): Minimum threshhold to include in the results. Defaults to 0.

    Returns:
        list: List of the scripts represented in the string sorted in descending order of weighted values.
    """
    weighted_dict = detect_script_weighted(string_to_check, threshhold)
    return sorted(weighted_dict, key=weighted_dict.get, reverse=True)
