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

from pathlib import Path

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import create_test_plugin_api

from picard.plugin3.manifest import PluginManifest


TRANSLATED_PLUGIN_DIR = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'


class TestPluginTranslationsIntegration(PicardTestCase):
    def test_load_translated_plugin(self):
        """Test loading a plugin with translation files."""
        with open(TRANSLATED_PLUGIN_DIR / 'MANIFEST.toml', 'rb') as f:
            manifest = PluginManifest('translated', f)
            self.assertEqual(manifest.source_locale, 'en')

    def test_plugin_translations_english(self):
        """Test plugin translations work in English."""
        api = create_test_plugin_api(TRANSLATED_PLUGIN_DIR, locale='en', module_name='translated')

        self.assertEqual(api.tr('greeting', 'Hello'), 'Hello')
        self.assertEqual(api.tr('farewell', 'Goodbye'), 'Goodbye')

    def test_plugin_translations_german(self):
        """Test plugin translations work in German."""
        api = create_test_plugin_api(TRANSLATED_PLUGIN_DIR, locale='de', module_name='translated')

        self.assertEqual(api.tr('greeting', 'Hello'), 'Hallo')
        self.assertEqual(api.tr('farewell', 'Goodbye'), 'Auf Wiedersehen')

    def test_plugin_translations_french(self):
        """Test plugin translations work in French."""
        api = create_test_plugin_api(TRANSLATED_PLUGIN_DIR, locale='fr', module_name='translated')

        self.assertEqual(api.tr('greeting', 'Hello'), 'Bonjour')
        self.assertEqual(api.tr('farewell', 'Goodbye'), 'Au revoir')

    def test_plugin_plural_translations_english(self):
        """Test plugin plural translations in English."""
        api = create_test_plugin_api(TRANSLATED_PLUGIN_DIR, locale='en', module_name='translated')

        self.assertEqual(api.trn('files', '{n} file', '{n} files', n=1), '1 file')
        self.assertEqual(api.trn('files', '{n} file', '{n} files', n=5), '5 files')

    def test_plugin_plural_translations_german(self):
        """Test plugin plural translations in German."""
        api = create_test_plugin_api(TRANSLATED_PLUGIN_DIR, locale='de', module_name='translated')

        self.assertEqual(api.trn('files', '{n} file', '{n} files', n=1), '1 Datei')
        self.assertEqual(api.trn('files', '{n} file', '{n} files', n=5), '5 Dateien')

    def test_plugin_qt_translations(self):
        """Test Qt UI translations are available."""
        api = create_test_plugin_api(TRANSLATED_PLUGIN_DIR, locale='de', module_name='translated')

        self.assertIn('qt.SettingsDialog.Apply', api._translations['de'])
        self.assertEqual(api._translations['de']['qt.SettingsDialog.Apply'], 'Anwenden')
