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


import io
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)
from test.plugins3.helpers import (
    create_test_plugin_api,
    load_plugin_manifest,
)

from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest
from picard.plugin3.plugin import (
    Plugin,
    PluginState,
)


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


class TestPluginManifestMalformedI18n(PicardTestCase):
    """Regression tests for malformed *_i18n sections in a plugin MANIFEST.toml.

    The i18n accessors (name/description/long_description) previously indexed
    into whatever value the TOML declared for the section. The manifest
    validator only rejects *empty* i18n sections, so a section declared with
    the wrong type still counted as valid. For example ``name_i18n = "enabled"``
    made ``name('en')`` evaluate ``'en' in "enabled"`` (a substring match) and
    then ``"enabled"['en']``, raising ``TypeError: string indices must be
    integers``. Non-string dict values likewise leaked through, breaking the
    documented ``-> str`` return type.

    The accessors must always return a string, falling back to the plain field.
    """

    BASE = (
        b'uuid = "3f9a1b2c-4d5e-4f6a-8b9c-0d1e2f3a4b5c"\n'
        b'name = "Test Plugin"\n'
        b'description = "A test plugin for demonstration"\n'
        b'api = ["3.0"]\n'
    )

    def _manifest(self, extra: bytes) -> PluginManifest:
        return PluginManifest('test', io.BytesIO(self.BASE + extra))

    def test_name_i18n_as_string_does_not_crash(self):
        # 'en' is a substring of 'enabled': the old code indexed into the string.
        manifest = self._manifest(b'name_i18n = "enabled"\n')
        self.assertEqual(manifest.name('en'), 'Test Plugin')

    def test_name_i18n_non_string_value_returns_plain_field(self):
        manifest = self._manifest(b'[name_i18n]\nen = 123\n')
        self.assertEqual(manifest.name('en'), 'Test Plugin')

    def test_name_i18n_array_value_returns_plain_field(self):
        manifest = self._manifest(b'[name_i18n]\nen = ["x"]\n')
        self.assertEqual(manifest.name('en'), 'Test Plugin')

    def test_description_i18n_as_string_does_not_crash(self):
        manifest = self._manifest(b'description_i18n = "enclosure"\n')
        self.assertEqual(manifest.description('en'), 'A test plugin for demonstration')

    def test_long_description_i18n_non_string_value_returns_plain_field(self):
        manifest = self._manifest(b'long_description = "Long desc"\n[long_description_i18n]\nen = 42\n')
        self.assertEqual(manifest.long_description('en'), 'Long desc')

    def test_valid_i18n_still_translates(self):
        # Ensure the guard does not break the normal, well-formed case.
        manifest = self._manifest(b'[name_i18n]\nde = "Test-Erweiterung"\n')
        self.assertEqual(manifest.name('de'), 'Test-Erweiterung')
        self.assertEqual(manifest.name('en'), 'Test Plugin')


class TestPluginApiLocale(PicardTestCase):
    def test_get_locale_returns_current_locale(self):
        """Test get_locale() returns current QLocale."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        locale = api.get_locale()
        # Should return a locale string like 'en_US', 'de_DE', etc.
        self.assertIsInstance(locale, str)
        self.assertGreater(len(locale), 0)


class TestPluginTranslations(PicardTestCase):
    def test_tr_with_text(self):
        """Test basic translation with text parameter."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        result = api.tr('submit_listens', 'Submit listens')
        self.assertEqual(result, 'Submit listens')

    def test_tr_without_text(self):
        """Test translation without text parameter returns key."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        result = api.tr('submit_listens')
        self.assertEqual(result, 'submit_listens')

    def test_tr_with_placeholders(self):
        """Test translation with placeholder substitution."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        result = api.tr('greeting', 'Hello {name}', name='World')
        self.assertEqual(result, 'Hello World')

    def test_tr_with_multiple_placeholders(self):
        """Test translation with multiple placeholders."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        result = api.tr('user_info', '{name} has {count} items', name='Alice', count=5)
        self.assertEqual(result, 'Alice has 5 items')

    @subtest_cases(
        "text,expected",
        {
            'missing placeholder kwarg': ('Hello {missing}', 'Hello {missing}'),
            'malformed opening brace': ('Hello {', 'Hello {'),
            'malformed closing brace': ('Hello }', 'Hello }'),
        },
    )
    def test_tr_bad_format_falls_back_to_unformatted(self, text, expected):
        """tr() must not crash on bad format strings from plugins/translations.

        Regression test: a badly written plugin or incorrect translation may
        reference an unsupplied placeholder ('{missing}') or use malformed
        format syntax (a stray brace). str.format() raised KeyError/ValueError,
        which propagated out of the translation call. tr() now logs a warning
        and falls back to the unformatted string.
        """
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        result = api.tr('greeting', text, name='World')
        self.assertEqual(result, expected)

    @subtest_cases(
        "singular,plural,expected",
        {
            'missing placeholder kwarg': ('{missing} file', '{missing} files', '{missing} files'),
            'malformed opening brace': ('{ file', '{ files', '{ files'),
            'malformed closing brace': ('} file', '} files', '} files'),
        },
    )
    def test_trn_bad_format_falls_back_to_unformatted(self, singular, plural, expected):
        """trn() must not crash on bad format strings from plugins/translations."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock(), Mock(), Path(''))

        result = api.trn('files', singular, plural, n=5)
        self.assertEqual(result, expected)


def _create_locale_dir(tmpdir):
    """Create a plugin directory with a locale subdirectory."""
    plugin_dir = Path(tmpdir)
    (plugin_dir / 'locale').mkdir()
    return plugin_dir


class TestPluginTranslationLoading(PicardTestCase):
    def test_load_translations_from_json(self):
        """Test loading translations from JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(json.dumps({'greeting': 'Hello', 'farewell': 'Goodbye'}))
            (plugin_dir / 'locale' / 'de.json').write_text(
                json.dumps({'greeting': 'Hallo', 'farewell': 'Auf Wiedersehen'})
            )

            api = create_test_plugin_api(plugin_dir)

            self.assertIn('en', api._translations)
            self.assertEqual(api._translations['en']['greeting'], 'Hello')

    def test_load_translations_from_toml(self):
        """Test loading translations from TOML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.toml').write_text('"greeting" = "Hello"\n"farewell" = "Goodbye"\n')
            (plugin_dir / 'locale' / 'de.toml').write_text('"greeting" = "Hallo"\n"farewell" = "Auf Wiedersehen"\n')

            api = create_test_plugin_api(plugin_dir)

            self.assertIn('en', api._translations)
            self.assertEqual(api._translations['en']['greeting'], 'Hello')

    def test_load_translations_toml_with_dotted_keys(self):
        """Test loading TOML with dotted keys (quoted)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.toml').write_text(
                '"message.greeting" = "Hello"\n["message.plurals"]\none = "{n} item"\nother = "{n} items"\n'
            )

            api = create_test_plugin_api(plugin_dir)

            self.assertEqual(api._translations['en']['message.greeting'], 'Hello')
            self.assertEqual(api._translations['en']['message.plurals']['one'], '{n} item')

    def test_load_translations_toml_warns_on_nested_structure(self):
        """Test that loading TOML with unquoted nested keys produces warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.toml').write_text('[message]\ngreeting = "Hello"\n')

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')

            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('test', f)
                api = PluginApi(manifest, Mock(), Mock(), plugin_dir)
                api.get_locale = Mock(return_value='en')

                with self.assertLogs('main.plugin.test', level='WARNING') as cm:
                    api._load_translations()

                self.assertTrue(any('nested structure' in msg.lower() for msg in cm.output))
                self.assertTrue(any('quoted' in msg.lower() for msg in cm.output))

    def test_load_translations_mixed_formats(self):
        """Test loading translations with mixed JSON and TOML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(json.dumps({'greeting': 'Hello'}))
            (plugin_dir / 'locale' / 'fr.toml').write_text('"greeting" = "Bonjour"\n')

            api = create_test_plugin_api(plugin_dir)
            self.assertIn('en', api._translations)
            self.assertEqual(api._translations['en']['greeting'], 'Hello')

            # Reset and test loading French
            api._translations = {}
            api.get_locale = Mock(return_value='fr')
            api._load_translations()
            self.assertIn('fr', api._translations)
            self.assertEqual(api._translations['fr']['greeting'], 'Bonjour')

    def test_translations_loaded_on_plugin_enable(self):
        """Test that translations are loaded when plugin is enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / 'test_plugin'
            plugin_dir.mkdir()
            locale_dir = plugin_dir / 'locale'
            locale_dir.mkdir()

            (locale_dir / 'fr.json').write_text(json.dumps({'greeting': 'Bonjour'}))

            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_path.write_text(
                'uuid = "12345678-1234-4234-8234-123456789012"\n'
                'name = "Test"\n'
                'description = "Test plugin"\n'
                'api = ["3.0"]\n'
            )

            init_file = plugin_dir / '__init__.py'
            init_file.write_text('def enable(api): pass\n')

            plugin = Plugin(Path(tmpdir), 'test_plugin')
            plugin.read_manifest()
            plugin.load_module()

            mock_tagger = Mock()
            plugin.enable(mock_tagger)

            self.assertEqual(plugin.state, PluginState.ENABLED)


class TestPluginTranslationLookup(PicardTestCase):
    def test_tr_uses_current_locale(self):
        """Test tr() uses translations from current locale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(json.dumps({'greeting': 'Hello', 'farewell': 'Goodbye'}))
            (plugin_dir / 'locale' / 'de.json').write_text(
                json.dumps({'greeting': 'Hallo', 'farewell': 'Auf Wiedersehen'})
            )
            (plugin_dir / 'locale' / 'de_DE.json').write_text(json.dumps({'greeting': 'Guten Tag'}))

            api = create_test_plugin_api(plugin_dir, locale='de')

            result = api.tr('greeting', 'Hello')
            self.assertEqual(result, 'Hallo')

    def test_tr_falls_back_to_language(self):
        """Test tr() falls back to language without region."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'de.json').write_text(json.dumps({'farewell': 'Auf Wiedersehen'}))

            api = create_test_plugin_api(plugin_dir, locale='de_AT')

            result = api.tr('farewell', 'Goodbye')
            self.assertEqual(result, 'Auf Wiedersehen')

    def test_tr_falls_back_to_text(self):
        """Test tr() falls back to text parameter when key not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'de.json').write_text(json.dumps({'greeting': 'Hallo'}))

            api = create_test_plugin_api(plugin_dir, locale='de')

            result = api.tr('unknown_key', 'Fallback text')
            self.assertEqual(result, 'Fallback text')

    def test_tr_returns_key_when_no_text(self):
        """Test tr() returns key when translation and text missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'de.json').write_text(json.dumps({'greeting': 'Hallo'}))

            api = create_test_plugin_api(plugin_dir, locale='de')

            result = api.tr('unknown_key')
            self.assertEqual(result, 'unknown_key')


class TestPluginPluralTranslations(PicardTestCase):
    def test_trn_english_singular(self):
        """Test trn() with English singular form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(
                json.dumps({'files': {'one': '{n} file', 'other': '{n} files'}})
            )

            api = create_test_plugin_api(plugin_dir)

            result = api.trn('files', '{n} file', '{n} files', n=1)
            self.assertEqual(result, '1 file')

    def test_trn_english_plural(self):
        """Test trn() with English plural form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(
                json.dumps({'files': {'one': '{n} file', 'other': '{n} files'}})
            )

            api = create_test_plugin_api(plugin_dir)

            result = api.trn('files', '{n} file', '{n} files', n=5)
            self.assertEqual(result, '5 files')

    def test_trn_polish_one(self):
        """Test trn() with Polish 'one' form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'pl.json').write_text(
                json.dumps({'files': {'one': '{n} plik', 'few': '{n} pliki', 'many': '{n} plików'}})
            )

            api = create_test_plugin_api(plugin_dir, locale='pl')

            result = api.trn('files', '{n} file', '{n} files', n=1)
            self.assertEqual(result, '1 plik')

    def test_trn_polish_few(self):
        """Test trn() with Polish 'few' form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'pl.json').write_text(
                json.dumps({'files': {'one': '{n} plik', 'few': '{n} pliki', 'many': '{n} plików'}})
            )

            api = create_test_plugin_api(plugin_dir, locale='pl')

            result = api.trn('files', '{n} file', '{n} files', n=3)
            self.assertEqual(result, '3 pliki')

    def test_trn_polish_many(self):
        """Test trn() with Polish 'many' form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'pl.json').write_text(
                json.dumps({'files': {'one': '{n} plik', 'few': '{n} pliki', 'many': '{n} plików'}})
            )

            api = create_test_plugin_api(plugin_dir, locale='pl')

            result = api.trn('files', '{n} file', '{n} files', n=5)
            self.assertEqual(result, '5 plików')

    def test_trn_fallback_to_singular(self):
        """Test trn() falls back to singular parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(json.dumps({}))

            api = create_test_plugin_api(plugin_dir)

            result = api.trn('unknown', '{n} item', '{n} items', n=1)
            self.assertEqual(result, '1 item')

    def test_trn_fallback_to_plural(self):
        """Test trn() falls back to plural parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = _create_locale_dir(tmpdir)

            (plugin_dir / 'locale' / 'en.json').write_text(json.dumps({}))

            api = create_test_plugin_api(plugin_dir)

            result = api.trn('unknown', '{n} item', '{n} items', n=5)
            self.assertEqual(result, '5 items')
