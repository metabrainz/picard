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

import json
from pathlib import Path
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.plugin3.api import PluginApi
from picard.plugin3.i18n import PluginTranslator
from picard.plugin3.manifest import PluginManifest


class TestPluginTranslator(PicardTestCase):
    def test_translate_generates_correct_key(self):
        """Test that translate() generates qt.context.text key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'de.json').write_text(
                json.dumps({'qt.MyDialog.Submit': 'Absenden', 'qt.MyDialog.Cancel': 'Abbrechen'})
            )

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                translations = {}
                for json_file in locale_dir.glob('*.json'):
                    with open(json_file, encoding='utf-8') as jf:
                        translations[json_file.stem] = json.load(jf)

                translator = PluginTranslator(translations, manifest.source_locale)
                translator._current_locale = 'de'

                result = translator.translate('MyDialog', 'Submit')
                self.assertEqual(result, 'Absenden')

    def test_translate_fallback_to_source_text(self):
        """Test translate() falls back to source text when key not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({'qt.MyDialog.submit': 'Submit'}))
            (locale_dir / 'de.json').write_text(json.dumps({}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                translations = {}
                for json_file in locale_dir.glob('*.json'):
                    with open(json_file, encoding='utf-8') as jf:
                        translations[json_file.stem] = json.load(jf)

                translator = PluginTranslator(translations, manifest.source_locale)
                translator._current_locale = 'de'

                result = translator.translate('MyDialog', 'submit')
                self.assertEqual(result, 'Submit')

    def test_translate_with_disambiguation(self):
        """Test translate() handles disambiguation parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({'qt.MyDialog.Submit': 'Submit'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                translations = {}
                for json_file in locale_dir.glob('*.json'):
                    with open(json_file, encoding='utf-8') as jf:
                        translations[json_file.stem] = json.load(jf)

                translator = PluginTranslator(translations, manifest.source_locale)
                translator._current_locale = 'en'

                result = translator.translate('MyDialog', 'Submit', 'button')
                self.assertEqual(result, 'Submit')

    def test_translate_empty_context(self):
        """Test translate() with empty context."""
        translations = {}
        translator = PluginTranslator(translations, 'en')
        translator._current_locale = 'en'
        result = translator.translate('', 'Text')
        self.assertEqual(result, 'Text')


class TestPluginApiQtTranslator(PicardTestCase):
    def test_qt_translator_installed_after_load(self):
        """Test that Qt translator is installed when translations are loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({'qt.Dialog.OK': 'OK'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='en')

                with patch('PyQt6.QtCore.QCoreApplication.installTranslator') as mock_install:
                    api._load_translations()
                    api._install_qt_translator()

                    mock_install.assert_called_once()
                    self.assertIsInstance(api._qt_translator, PluginTranslator)

    def test_qt_translator_not_installed_without_translations(self):
        """Test that Qt translator is not installed when no translations exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())

                with patch('PyQt6.QtCore.QCoreApplication.installTranslator') as mock_install:
                    api._install_qt_translator()
                    mock_install.assert_not_called()
                    self.assertIsNone(api._qt_translator)
