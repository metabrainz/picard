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

from test.picardtestcase import PicardTestCase

from picard.plugin3.i18n import get_plural_form


class TestPluralRules(PicardTestCase):
    def test_english_plural_rules(self):
        """Test English plural rules (one/other)."""
        self.assertEqual(get_plural_form('en', 0), 'other')
        self.assertEqual(get_plural_form('en', 1), 'one')
        self.assertEqual(get_plural_form('en', 2), 'other')
        self.assertEqual(get_plural_form('en', 5), 'other')

    def test_german_plural_rules(self):
        """Test German plural rules (same as English)."""
        self.assertEqual(get_plural_form('de', 0), 'other')
        self.assertEqual(get_plural_form('de', 1), 'one')
        self.assertEqual(get_plural_form('de', 2), 'other')

    def test_polish_plural_rules(self):
        """Test Polish plural rules (one/few/many/other)."""
        self.assertEqual(get_plural_form('pl', 1), 'one')
        self.assertEqual(get_plural_form('pl', 2), 'few')
        self.assertEqual(get_plural_form('pl', 3), 'few')
        self.assertEqual(get_plural_form('pl', 4), 'few')
        self.assertEqual(get_plural_form('pl', 5), 'many')
        self.assertEqual(get_plural_form('pl', 10), 'many')
        self.assertEqual(get_plural_form('pl', 22), 'few')

    def test_russian_plural_rules(self):
        """Test Russian plural rules (one/few/many/other)."""
        self.assertEqual(get_plural_form('ru', 1), 'one')
        self.assertEqual(get_plural_form('ru', 2), 'few')
        self.assertEqual(get_plural_form('ru', 5), 'many')
        self.assertEqual(get_plural_form('ru', 21), 'one')
        self.assertEqual(get_plural_form('ru', 22), 'few')

    def test_french_plural_rules(self):
        """Test French plural rules (one/other, 0 and 1 are 'one')."""
        self.assertEqual(get_plural_form('fr', 0), 'one')
        self.assertEqual(get_plural_form('fr', 1), 'one')
        self.assertEqual(get_plural_form('fr', 2), 'other')

    def test_punjabi_plural_rules(self):
        """Test Punjabi plural rules (same as French: 0 and 1 are 'one')."""
        self.assertEqual(get_plural_form('pa', 0), 'one')
        self.assertEqual(get_plural_form('pa', 1), 'one')
        self.assertEqual(get_plural_form('pa', 2), 'other')

    def test_arabic_plural_rules(self):
        """Test Arabic plural rules (zero/one/two/few/many/other)."""
        self.assertEqual(get_plural_form('ar', 0), 'zero')
        self.assertEqual(get_plural_form('ar', 1), 'one')
        self.assertEqual(get_plural_form('ar', 2), 'two')
        self.assertEqual(get_plural_form('ar', 3), 'few')
        self.assertEqual(get_plural_form('ar', 11), 'many')
        self.assertEqual(get_plural_form('ar', 100), 'other')

    def test_czech_plural_rules(self):
        """Test Czech plural rules (one/few/other)."""
        self.assertEqual(get_plural_form('cs', 0), 'other')
        self.assertEqual(get_plural_form('cs', 1), 'one')
        self.assertEqual(get_plural_form('cs', 2), 'few')
        self.assertEqual(get_plural_form('cs', 4), 'few')
        self.assertEqual(get_plural_form('cs', 5), 'other')
        self.assertEqual(get_plural_form('cs', 100), 'other')

    def test_hebrew_plural_rules(self):
        """Test Hebrew plural rules (one/two/other)."""
        self.assertEqual(get_plural_form('he', 0), 'other')
        self.assertEqual(get_plural_form('he', 1), 'one')
        self.assertEqual(get_plural_form('he', 2), 'two')
        self.assertEqual(get_plural_form('he', 5), 'other')
        self.assertEqual(get_plural_form('he', 100), 'other')

    def test_lithuanian_plural_rules(self):
        """Test Lithuanian plural rules (one/few/other)."""
        self.assertEqual(get_plural_form('lt', 0), 'other')
        self.assertEqual(get_plural_form('lt', 1), 'one')
        self.assertEqual(get_plural_form('lt', 2), 'few')
        self.assertEqual(get_plural_form('lt', 9), 'few')
        self.assertEqual(get_plural_form('lt', 10), 'other')
        self.assertEqual(get_plural_form('lt', 11), 'other')
        self.assertEqual(get_plural_form('lt', 19), 'other')
        self.assertEqual(get_plural_form('lt', 21), 'one')
        self.assertEqual(get_plural_form('lt', 22), 'few')
        self.assertEqual(get_plural_form('lt', 29), 'few')
        self.assertEqual(get_plural_form('lt', 100), 'other')
        self.assertEqual(get_plural_form('lt', 101), 'one')

    def test_japanese_plural_rules(self):
        """Test Japanese plural rules (other)."""
        self.assertEqual(get_plural_form('ja', 0), 'other')
        self.assertEqual(get_plural_form('ja', 1), 'other')
        self.assertEqual(get_plural_form('ja', 5), 'other')
        self.assertEqual(get_plural_form('ja', 100), 'other')

    def test_icelandic_plural_rules(self):
        """Test Icelandic plural rules (one/other)."""
        self.assertEqual(get_plural_form('is', 0), 'other')
        self.assertEqual(get_plural_form('is', 1), 'one')
        self.assertEqual(get_plural_form('is', 2), 'other')
        self.assertEqual(get_plural_form('is', 10), 'other')
        self.assertEqual(get_plural_form('is', 11), 'other')
        self.assertEqual(get_plural_form('is', 21), 'one')
        self.assertEqual(get_plural_form('is', 101), 'one')
        self.assertEqual(get_plural_form('is', 111), 'other')
        self.assertEqual(get_plural_form('is', 131), 'one')

    def test_irish_plural_rules(self):
        """Test Irish plural rules (one/two/few/many/other)."""
        self.assertEqual(get_plural_form('ga', 0), 'other')
        self.assertEqual(get_plural_form('ga', 1), 'one')
        self.assertEqual(get_plural_form('ga', 2), 'two')
        self.assertEqual(get_plural_form('ga', 3), 'few')
        self.assertEqual(get_plural_form('ga', 6), 'few')
        self.assertEqual(get_plural_form('ga', 7), 'many')
        self.assertEqual(get_plural_form('ga', 10), 'many')
        self.assertEqual(get_plural_form('ga', 11), 'other')
        self.assertEqual(get_plural_form('ga', 100), 'other')

    def test_welsh_plural_rules(self):
        """Test Welsh plural rules (zero/one/two/few/many/other)."""
        self.assertEqual(get_plural_form('cy', 0), 'zero')
        self.assertEqual(get_plural_form('cy', 1), 'one')
        self.assertEqual(get_plural_form('cy', 2), 'two')
        self.assertEqual(get_plural_form('cy', 3), 'few')
        self.assertEqual(get_plural_form('cy', 4), 'other')
        self.assertEqual(get_plural_form('cy', 5), 'other')
        self.assertEqual(get_plural_form('cy', 6), 'many')
        self.assertEqual(get_plural_form('cy', 7), 'other')
        self.assertEqual(get_plural_form('cy', 10), 'other')
        self.assertEqual(get_plural_form('cy', 11), 'other')
        self.assertEqual(get_plural_form('cy', 100), 'other')

    def test_unknown_locale_defaults_to_english(self):
        """Test unknown locale falls back to English rules."""
        self.assertEqual(get_plural_form('xx', 1), 'one')
        self.assertEqual(get_plural_form('xx', 2), 'other')
