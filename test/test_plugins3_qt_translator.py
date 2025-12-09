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
from unittest.mock import Mock

from PyQt6 import QtCore

from test.picardtestcase import PicardTestCase

from picard.plugin3.api import PluginApi
from picard.plugin3.i18n import PluginTranslator
from picard.plugin3.manifest import PluginManifest
from picard.tagger import Translators


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
    def _create_mock_tagger(self):
        """Create a mock tagger with proper Qt signal."""

        class MockTagger(QtCore.QObject):
            _qt_translators_updated = QtCore.pyqtSignal()

            def __init__(self):
                super().__init__()
                self.installTranslator = Mock(return_value=True)
                self.removeTranslator = Mock()

        return MockTagger()

    def _setup_plugin_api(self, tmpdir, translations=None):
        """Setup PluginApi with optional translations."""
        plugin_dir = Path(tmpdir)

        if translations:
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()
            (locale_dir / 'en.json').write_text(json.dumps(translations))

        manifest_path = plugin_dir / 'MANIFEST.toml'
        manifest_path.write_text('name = "Test"\n')

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('test', f)
            tagger = self._create_mock_tagger()
            tagger._qt_translators = Translators(tagger)

            api = PluginApi(manifest, tagger)
            if translations:
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='en')

            return api, tagger

    def test_qt_translator_installed_after_load(self):
        """Test that Qt translator is installed when translations are loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            api, tagger = self._setup_plugin_api(tmpdir, {'qt.Dialog.OK': 'OK'})
            initial_count = len(tagger._qt_translators._translators)

            api._load_translations()
            api._install_qt_translator()

            self.assertIsInstance(api._qt_translator, PluginTranslator)
            self.assertEqual(len(tagger._qt_translators._translators), initial_count + 1)

    def test_qt_translator_not_installed_without_translations(self):
        """Test that Qt translator is not installed when no translations exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            api, tagger = self._setup_plugin_api(tmpdir)
            initial_count = len(tagger._qt_translators._translators)

            api._install_qt_translator()

            self.assertIsNone(api._qt_translator)
            self.assertEqual(len(tagger._qt_translators._translators), initial_count)

    def test_qt_translator_not_installed_without_qt_keys(self):
        """Test that Qt translator is not installed when translations have no qt. keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            api, tagger = self._setup_plugin_api(tmpdir, {'regular.key': 'Value'})
            initial_count = len(tagger._qt_translators._translators)

            api._load_translations()
            api._install_qt_translator()

            self.assertIsNone(api._qt_translator)
            self.assertEqual(len(tagger._qt_translators._translators), initial_count)

    def test_qt_translator_installed_on_reinstall(self):
        """Test that installTranslator is called when reinstall() is triggered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            api, tagger = self._setup_plugin_api(tmpdir, {'qt.Dialog.OK': 'OK'})

            api._load_translations()
            api._install_qt_translator()
            tagger._qt_translators.reinstall()

            tagger.installTranslator.assert_called()
            self.assertIsInstance(api._qt_translator, PluginTranslator)
