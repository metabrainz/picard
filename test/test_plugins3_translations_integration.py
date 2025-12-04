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
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest


class TestPluginTranslationsIntegration(PicardTestCase):
    def test_load_translated_plugin(self):
        """Test loading a plugin with translation files."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            self.assertEqual(manifest.source_locale, 'en')

    def test_plugin_translations_english(self):
        """Test plugin translations work in English."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            api = PluginApi(manifest, Mock())
            api._plugin_dir = plugin_dir
            api._current_locale = 'en'
            api._load_translations()

            result = api.tr('greeting', 'Hello')
            self.assertEqual(result, 'Hello')

            result = api.tr('farewell', 'Goodbye')
            self.assertEqual(result, 'Goodbye')

    def test_plugin_translations_german(self):
        """Test plugin translations work in German."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            api = PluginApi(manifest, Mock())
            api._plugin_dir = plugin_dir
            api._current_locale = 'de'
            api._load_translations()

            result = api.tr('greeting', 'Hello')
            self.assertEqual(result, 'Hallo')

            result = api.tr('farewell', 'Goodbye')
            self.assertEqual(result, 'Auf Wiedersehen')

    def test_plugin_translations_french(self):
        """Test plugin translations work in French."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            api = PluginApi(manifest, Mock())
            api._plugin_dir = plugin_dir
            api._current_locale = 'fr'
            api._load_translations()

            result = api.tr('greeting', 'Hello')
            self.assertEqual(result, 'Bonjour')

            result = api.tr('farewell', 'Goodbye')
            self.assertEqual(result, 'Au revoir')

    def test_plugin_plural_translations_english(self):
        """Test plugin plural translations in English."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            api = PluginApi(manifest, Mock())
            api._plugin_dir = plugin_dir
            api._current_locale = 'en'
            api._load_translations()

            result = api.trn('files', '{n} file', '{n} files', n=1)
            self.assertEqual(result, '1 file')

            result = api.trn('files', '{n} file', '{n} files', n=5)
            self.assertEqual(result, '5 files')

    def test_plugin_plural_translations_german(self):
        """Test plugin plural translations in German."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            api = PluginApi(manifest, Mock())
            api._plugin_dir = plugin_dir
            api._current_locale = 'de'
            api._load_translations()

            result = api.trn('files', '{n} file', '{n} files', n=1)
            self.assertEqual(result, '1 Datei')

            result = api.trn('files', '{n} file', '{n} files', n=5)
            self.assertEqual(result, '5 Dateien')

    def test_plugin_qt_translations(self):
        """Test Qt UI translations are available."""
        plugin_dir = Path(__file__).parent / 'data' / 'testplugins3' / 'translated'
        manifest_path = plugin_dir / 'MANIFEST.toml'

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('translated', f)
            api = PluginApi(manifest, Mock())
            api._plugin_dir = plugin_dir
            api._current_locale = 'de'
            api._load_translations()

            # Check Qt translation key exists
            self.assertIn('qt.SettingsDialog.Apply', api._translations['de'])
            self.assertEqual(api._translations['de']['qt.SettingsDialog.Apply'], 'Anwenden')
