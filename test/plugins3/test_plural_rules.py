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

from typing import ClassVar

from test.picardtestcase import PicardTestCase

from picard.plugin3.i18n import get_plural_form


class TestPluralRules(PicardTestCase):
    """Test CLDR plural rules for get_plural_form().

    Each entry in PLURAL_RULES_TEST_DATA maps a locale to a list of
    (n, expected_form) pairs covering the rule boundaries.
    """

    PLURAL_RULES_TEST_DATA: ClassVar[dict] = {
        # English (also: de, es, it, pt, nl, sv, da, no, fi) — one/other
        'en': [
            (0, 'other'),
            (1, 'one'),
            (2, 'other'),
            (5, 'other'),
        ],
        # French (also: pa) — one/other, 0 and 1 are 'one'
        'fr': [
            (0, 'one'),
            (1, 'one'),
            (2, 'other'),
        ],
        # Polish — one/few/many
        'pl': [
            (1, 'one'),
            (2, 'few'),
            (3, 'few'),
            (4, 'few'),
            (5, 'many'),
            (10, 'many'),
            (22, 'few'),
        ],
        # Russian (also: uk) — one/few/many
        'ru': [
            (1, 'one'),
            (2, 'few'),
            (5, 'many'),
            (21, 'one'),
            (22, 'few'),
        ],
        # Arabic — zero/one/two/few/many/other
        'ar': [
            (0, 'zero'),
            (1, 'one'),
            (2, 'two'),
            (3, 'few'),
            (11, 'many'),
            (100, 'other'),
        ],
        # Czech (also: sk) — one/few/other
        'cs': [
            (0, 'other'),
            (1, 'one'),
            (2, 'few'),
            (4, 'few'),
            (5, 'other'),
            (100, 'other'),
        ],
        # Hebrew — one/two/other
        'he': [
            (0, 'other'),
            (1, 'one'),
            (2, 'two'),
            (5, 'other'),
            (100, 'other'),
        ],
        # Lithuanian — one/few/other
        'lt': [
            (0, 'other'),
            (1, 'one'),
            (2, 'few'),
            (9, 'few'),
            (10, 'other'),
            (11, 'other'),
            (19, 'other'),
            (21, 'one'),
            (22, 'few'),
            (29, 'few'),
            (100, 'other'),
            (101, 'one'),
        ],
        # Japanese (also: ko, ms, vi, zh) — other only
        'ja': [
            (0, 'other'),
            (1, 'other'),
            (5, 'other'),
            (100, 'other'),
        ],
        # Icelandic — one/other
        'is': [
            (0, 'other'),
            (1, 'one'),
            (2, 'other'),
            (10, 'other'),
            (11, 'other'),
            (21, 'one'),
            (101, 'one'),
            (111, 'other'),
            (131, 'one'),
        ],
        # Irish — one/two/few/many/other
        'ga': [
            (0, 'other'),
            (1, 'one'),
            (2, 'two'),
            (3, 'few'),
            (6, 'few'),
            (7, 'many'),
            (10, 'many'),
            (11, 'other'),
            (100, 'other'),
        ],
        # Welsh — zero/one/two/few/many/other
        'cy': [
            (0, 'zero'),
            (1, 'one'),
            (2, 'two'),
            (3, 'few'),
            (4, 'other'),
            (5, 'other'),
            (6, 'many'),
            (7, 'other'),
            (10, 'other'),
            (11, 'other'),
            (100, 'other'),
        ],
    }

    def test_plural_rules(self):
        """Test plural form rules for all supported locales."""
        for locale, cases in self.PLURAL_RULES_TEST_DATA.items():
            for n, expected in cases:
                with self.subTest(locale=locale, n=n):
                    self.assertEqual(get_plural_form(locale, n), expected)

    def test_unknown_locale_defaults_to_english(self):
        """Test unknown locale falls back to English rules."""
        self.assertEqual(get_plural_form('xx', 1), 'one')
        self.assertEqual(get_plural_form('xx', 2), 'other')

    def test_locale_with_region(self):
        """Test that region suffix is stripped correctly."""
        self.assertEqual(get_plural_form('en_US', 1), 'one')
        self.assertEqual(get_plural_form('fr_CA', 0), 'one')
        self.assertEqual(get_plural_form('zh_TW', 5), 'other')
