# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024, 2026 Philipp Wolfer
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from typing import ClassVar

from test.picardtestcase import PicardTestCase

from picard.plugin3.i18n import (
    Plural,
    get_plural_form,
)


class TestPluralRules(PicardTestCase):
    """Test CLDR plural rules for get_plural_form().

    Each entry in PLURAL_RULES_TEST_DATA maps a locale to a list of
    (n, expected_form) pairs covering the rule boundaries.
    """

    PLURAL_RULES_TEST_DATA: ClassVar[dict] = {
        # English (also: de, es, it, pt, nl, sv, da, no, fi) — one/other
        'en': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.OTHER),
            (5, Plural.OTHER),
        ],
        # French (also: pa) — one/other, 0 and 1 are Plural.ONE
        'fr': [
            (0, Plural.ONE),
            (1, Plural.ONE),
            (2, Plural.OTHER),
        ],
        # Polish — one/few/many
        'pl': [
            (1, Plural.ONE),
            (2, Plural.FEW),
            (3, Plural.FEW),
            (4, Plural.FEW),
            (5, Plural.MANY),
            (10, Plural.MANY),
            (22, Plural.FEW),
        ],
        # Russian (also: uk) — one/few/many
        'ru': [
            (1, Plural.ONE),
            (2, Plural.FEW),
            (5, Plural.MANY),
            (21, Plural.ONE),
            (22, Plural.FEW),
        ],
        # Arabic — zero/one/two/few/many/other
        'ar': [
            (0, Plural.ZERO),
            (1, Plural.ONE),
            (2, Plural.TWO),
            (3, Plural.FEW),
            (11, Plural.MANY),
            (100, Plural.OTHER),
        ],
        # Czech (also: sk) — one/few/other
        'cs': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.FEW),
            (4, Plural.FEW),
            (5, Plural.OTHER),
            (100, Plural.OTHER),
        ],
        # Romanian — one/few/other
        'ro': [
            (0, Plural.FEW),
            (1, Plural.ONE),
            (2, Plural.FEW),
            (12, Plural.FEW),
            (19, Plural.FEW),
            (20, Plural.OTHER),
            (100, Plural.OTHER),
            (101, Plural.FEW),
            (119, Plural.FEW),
            (120, Plural.OTHER),
        ],
        # Croatian (also: bs, sr) — one/few/other
        'hr': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.FEW),
            (4, Plural.FEW),
            (5, Plural.OTHER),
            (11, Plural.OTHER),
            (12, Plural.OTHER),
            (21, Plural.ONE),
            (22, Plural.FEW),
            (25, Plural.OTHER),
        ],
        # Catalan — one/many/other
        'ca': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.OTHER),
            (5, Plural.OTHER),
            (1_000_000, Plural.MANY),
            (2_000_000, Plural.MANY),
            (1_000, Plural.OTHER),
        ],
        # Hebrew — one/two/other
        'he': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.TWO),
            (5, Plural.OTHER),
            (100, Plural.OTHER),
        ],
        # Lithuanian — one/few/other
        'lt': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.FEW),
            (9, Plural.FEW),
            (10, Plural.OTHER),
            (11, Plural.OTHER),
            (19, Plural.OTHER),
            (21, Plural.ONE),
            (22, Plural.FEW),
            (29, Plural.FEW),
            (100, Plural.OTHER),
            (101, Plural.ONE),
        ],
        # Japanese (also: ko, ms, vi, zh) — other only
        'ja': [
            (0, Plural.OTHER),
            (1, Plural.OTHER),
            (5, Plural.OTHER),
            (100, Plural.OTHER),
        ],
        # Icelandic — one/other
        'is': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.OTHER),
            (10, Plural.OTHER),
            (11, Plural.OTHER),
            (21, Plural.ONE),
            (101, Plural.ONE),
            (111, Plural.OTHER),
            (131, Plural.ONE),
        ],
        # Irish — one/two/few/many/other
        'ga': [
            (0, Plural.OTHER),
            (1, Plural.ONE),
            (2, Plural.TWO),
            (3, Plural.FEW),
            (6, Plural.FEW),
            (7, Plural.MANY),
            (10, Plural.MANY),
            (11, Plural.OTHER),
            (100, Plural.OTHER),
        ],
        # Welsh — zero/one/two/few/many/other
        'cy': [
            (0, Plural.ZERO),
            (1, Plural.ONE),
            (2, Plural.TWO),
            (3, Plural.FEW),
            (4, Plural.OTHER),
            (5, Plural.OTHER),
            (6, Plural.MANY),
            (7, Plural.OTHER),
            (10, Plural.OTHER),
            (11, Plural.OTHER),
            (100, Plural.OTHER),
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
        self.assertEqual(get_plural_form('xx', 1), Plural.ONE)
        self.assertEqual(get_plural_form('xx', 2), Plural.OTHER)

    def test_locale_with_region(self):
        """Test that region suffix is stripped correctly."""
        self.assertEqual(get_plural_form('en_US', 1), Plural.ONE)
        self.assertEqual(get_plural_form('fr_CA', 0), Plural.ONE)
        self.assertEqual(get_plural_form('zh_TW', 5), Plural.OTHER)
