# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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


def get_plural_form(locale: str, n: int) -> str:
    """Get CLDR plural form for a number in a given locale.

    Args:
        locale: Locale code (e.g., 'en', 'de', 'pl', 'ru', 'ar')
        n: Number to get plural form for

    Returns:
        One of: 'zero', 'one', 'two', 'few', 'many', 'other'
    """
    lang = locale.split('_')[0]

    # English, German, Spanish, Italian, Portuguese, etc.
    if lang in ('en', 'de', 'es', 'it', 'pt', 'nl', 'sv', 'da', 'no', 'fi'):
        return 'one' if n == 1 else 'other'

    # French (0 and 1 are singular)
    if lang == 'fr':
        return 'one' if n in (0, 1) else 'other'

    # Polish
    if lang == 'pl':
        if n == 1:
            return 'one'
        if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            return 'few'
        return 'many'

    # Russian, Ukrainian
    if lang in ('ru', 'uk'):
        if n % 10 == 1 and n % 100 != 11:
            return 'one'
        if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            return 'few'
        return 'many'

    # Arabic
    if lang == 'ar':
        if n == 0:
            return 'zero'
        if n == 1:
            return 'one'
        if n == 2:
            return 'two'
        if 3 <= n % 100 <= 10:
            return 'few'
        if 11 <= n % 100 <= 99:
            return 'many'
        return 'other'

    # Czech, Slovak
    if lang in ('cs', 'sk'):
        if n == 1:
            return 'one'
        if 2 <= n <= 4:
            return 'few'
        return 'other'

    # Default to English rules
    return 'one' if n == 1 else 'other'
