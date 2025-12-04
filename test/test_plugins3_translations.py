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

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import load_plugin_manifest

from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest


class TestPluginManifestSourceLocale(PicardTestCase):
    def test_source_locale_defaults_to_en(self):
        """Test source_locale defaults to 'en' when not specified."""
        manifest = load_plugin_manifest('example')
        self.assertEqual(manifest.source_locale, 'en')

    def test_source_locale_from_manifest(self):
        """Test source_locale reads from MANIFEST.toml."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            temp_path = Path(f.name)
            f.write(b'name = "Test"\nsource_locale = "de_DE"\n')
            f.flush()

        try:
            with open(temp_path, 'rb') as manifest_fp:
                manifest = PluginManifest('test', manifest_fp)
                self.assertEqual(manifest.source_locale, 'de_DE')
        finally:
            temp_path.unlink(missing_ok=True)


class TestPluginApiLocale(PicardTestCase):
    def test_get_locale_returns_current_locale(self):
        """Test get_locale() returns current QLocale."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        locale = api.get_locale()
        # Should return a locale string like 'en_US', 'de_DE', etc.
        self.assertIsInstance(locale, str)
        self.assertGreater(len(locale), 0)


class TestPluginTranslations(PicardTestCase):
    def test_tr_with_text(self):
        """Test basic translation with text parameter."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        result = api.tr('submit_listens', 'Submit listens')
        self.assertEqual(result, 'Submit listens')

    def test_tr_without_text(self):
        """Test translation without text parameter returns key."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        result = api.tr('submit_listens')
        self.assertEqual(result, 'submit_listens')

    def test_tr_with_placeholders(self):
        """Test translation with placeholder substitution."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        result = api.tr('greeting', 'Hello {name}', name='World')
        self.assertEqual(result, 'Hello World')

    def test_tr_with_multiple_placeholders(self):
        """Test translation with multiple placeholders."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        result = api.tr('user_info', '{name} has {count} items', name='Alice', count=5)
        self.assertEqual(result, 'Alice has 5 items')


class TestPluginTranslationLoading(PicardTestCase):
    def test_load_translations_from_json(self):
        """Test loading translations from JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            # Create translation files
            (locale_dir / 'en.json').write_text(json.dumps({'greeting': 'Hello', 'farewell': 'Goodbye'}))
            (locale_dir / 'de.json').write_text(json.dumps({'greeting': 'Hallo', 'farewell': 'Auf Wiedersehen'}))

            # Create manifest
            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api._load_translations()

                self.assertIn('en', api._translations)
                self.assertIn('de', api._translations)
                self.assertEqual(api._translations['en']['greeting'], 'Hello')
                self.assertEqual(api._translations['de']['greeting'], 'Hallo')


class TestPluginTranslationLookup(PicardTestCase):
    def test_tr_uses_current_locale(self):
        """Test tr() uses translations from current locale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({'greeting': 'Hello', 'farewell': 'Goodbye'}))
            (locale_dir / 'de.json').write_text(json.dumps({'greeting': 'Hallo', 'farewell': 'Auf Wiedersehen'}))
            (locale_dir / 'de_DE.json').write_text(json.dumps({'greeting': 'Guten Tag'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='de')
                api._load_translations()

                result = api.tr('greeting', 'Hello')
                self.assertEqual(result, 'Hallo')

    def test_tr_falls_back_to_language(self):
        """Test tr() falls back to language without region."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'de.json').write_text(json.dumps({'farewell': 'Auf Wiedersehen'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='de_AT')
                api._load_translations()

                result = api.tr('farewell', 'Goodbye')
                self.assertEqual(result, 'Auf Wiedersehen')

    def test_tr_falls_back_to_text(self):
        """Test tr() falls back to text parameter when key not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'de.json').write_text(json.dumps({'greeting': 'Hallo'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='de')
                api._load_translations()

                result = api.tr('unknown_key', 'Fallback text')
                self.assertEqual(result, 'Fallback text')

    def test_tr_returns_key_when_no_text(self):
        """Test tr() returns key when translation and text missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'de.json').write_text(json.dumps({'greeting': 'Hallo'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='de')
                api._load_translations()

                result = api.tr('unknown_key')
                self.assertEqual(result, 'unknown_key')


class TestPluginPluralTranslations(PicardTestCase):
    def test_trn_english_singular(self):
        """Test trn() with English singular form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({'files': {'one': '{n} file', 'other': '{n} files'}}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='en')
                api._load_translations()

                result = api.trn('files', '{n} file', '{n} files', n=1)
                self.assertEqual(result, '1 file')

    def test_trn_english_plural(self):
        """Test trn() with English plural form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({'files': {'one': '{n} file', 'other': '{n} files'}}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='en')
                api._load_translations()

                result = api.trn('files', '{n} file', '{n} files', n=5)
                self.assertEqual(result, '5 files')

    def test_trn_polish_one(self):
        """Test trn() with Polish 'one' form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'pl.json').write_text(
                json.dumps({'files': {'one': '{n} plik', 'few': '{n} pliki', 'many': '{n} plików'}})
            )

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='pl')
                api._load_translations()

                result = api.trn('files', '{n} file', '{n} files', n=1)
                self.assertEqual(result, '1 plik')

    def test_trn_polish_few(self):
        """Test trn() with Polish 'few' form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'pl.json').write_text(
                json.dumps({'files': {'one': '{n} plik', 'few': '{n} pliki', 'many': '{n} plików'}})
            )

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='pl')
                api._load_translations()

                result = api.trn('files', '{n} file', '{n} files', n=3)
                self.assertEqual(result, '3 pliki')

    def test_trn_polish_many(self):
        """Test trn() with Polish 'many' form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'pl.json').write_text(
                json.dumps({'files': {'one': '{n} plik', 'few': '{n} pliki', 'many': '{n} plików'}})
            )

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='pl')
                api._load_translations()

                result = api.trn('files', '{n} file', '{n} files', n=5)
                self.assertEqual(result, '5 plików')

    def test_trn_fallback_to_singular(self):
        """Test trn() falls back to singular parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='en')
                api._load_translations()

                result = api.trn('unknown', '{n} item', '{n} items', n=1)
                self.assertEqual(result, '1 item')

    def test_trn_fallback_to_plural(self):
        """Test trn() falls back to plural parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'en.json').write_text(json.dumps({}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock())
                api._plugin_dir = plugin_dir
                api.get_locale = Mock(return_value='en')
                api._load_translations()

                result = api.trn('unknown', '{n} item', '{n} items', n=5)
                self.assertEqual(result, '5 items')
