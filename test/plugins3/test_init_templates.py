# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

try:
    import tomllib  # type: ignore[unresolved-import]
except (ImportError, ModuleNotFoundError):
    import tomli as tomllib  # type: ignore[no-redef]

from test.picardtestcase import PicardTestCase

from picard.plugin3.init_templates import (
    generate_gitignore,
    generate_manifest,
    generate_plugin_init_py,
    generate_readme,
    slugify_name,
)


class TestSlugifyName(PicardTestCase):
    def test_basic(self):
        self.assertEqual(slugify_name('My Cool Plugin'), 'my-cool-plugin')

    def test_special_characters(self):
        self.assertEqual(slugify_name('Hello, World!'), 'hello-world')

    def test_multiple_spaces(self):
        self.assertEqual(slugify_name('  too   many  spaces  '), 'too-many-spaces')

    def test_already_slugified(self):
        self.assertEqual(slugify_name('my-plugin'), 'my-plugin')

    def test_uppercase(self):
        self.assertEqual(slugify_name('ALL CAPS'), 'all-caps')

    def test_numbers(self):
        self.assertEqual(slugify_name('Plugin 2 Test'), 'plugin-2-test')

    def test_unicode_accents(self):
        self.assertEqual(slugify_name('Ünïcödé Plügin'), 'unicode-plugin')

    def test_unicode_french(self):
        self.assertEqual(slugify_name("Plugin d'Étiquetage"), 'plugin-d-etiquetage')

    def test_unicode_cjk(self):
        self.assertEqual(slugify_name('中文插件'), '中文插件')

    def test_unicode_mixed(self):
        self.assertEqual(slugify_name('My 中文 Plugin'), 'my-中文-plugin')

    def test_empty_string(self):
        self.assertEqual(slugify_name(''), '')

    def test_only_special_chars(self):
        self.assertEqual(slugify_name('!!!'), '')


class TestGenerateManifest(PicardTestCase):
    def test_minimal(self):
        result = generate_manifest('My Plugin')
        self.assertIn('name = "My Plugin"', result)
        self.assertIn('api = ["3.0"]', result)
        self.assertIn('uuid = "', result)
        self.assertIn('description = "A Picard plugin"', result)

    def test_with_description(self):
        result = generate_manifest('Test', description='Does things')
        self.assertIn('description = "Does things"', result)

    def test_with_authors(self):
        result = generate_manifest('Test', authors=['Alice', 'Bob'])
        self.assertIn('authors = ["Alice", "Bob"]', result)

    def test_with_license(self):
        result = generate_manifest(
            'Test', license_id='GPL-2.0-or-later', license_url='https://www.gnu.org/licenses/gpl-2.0.html'
        )
        self.assertIn('license = "GPL-2.0-or-later"', result)
        self.assertIn('license_url = "https://www.gnu.org/licenses/gpl-2.0.html"', result)

    def test_with_categories(self):
        result = generate_manifest('Test', categories=['metadata', 'ui'])
        self.assertIn('categories = ["metadata", "ui"]', result)

    def test_with_report_bugs_to(self):
        result = generate_manifest('Test', report_bugs_to='mailto:dev@example.com')
        self.assertIn('report_bugs_to = "mailto:dev@example.com"', result)

    def test_without_report_bugs_to_has_comment(self):
        result = generate_manifest('Test')
        self.assertIn('# report_bugs_to =', result)

    def test_report_bugs_to_url(self):
        result = generate_manifest('Test', report_bugs_to='https://github.com/user/repo/issues')
        data = tomllib.loads(result)
        self.assertEqual(data['report_bugs_to'], 'https://github.com/user/repo/issues')

    def test_uuid_is_valid(self):
        """Generated manifest should contain a valid UUID."""
        result = generate_manifest('Test')
        # Extract UUID from the output
        for line in result.splitlines():
            if line.startswith('uuid = "'):
                uuid_str = line.split('"')[1]
                self.assertRegex(uuid_str, r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
                return
        self.fail('No uuid line found in generated manifest')

    def test_parseable_toml(self):
        """Generated manifest should be valid TOML."""
        result = generate_manifest('Test', description='Desc', authors=['Me'], categories=['metadata'])
        data = tomllib.loads(result)
        self.assertEqual(data['name'], 'Test')
        self.assertEqual(data['description'], 'Desc')
        self.assertEqual(data['authors'], ['Me'])
        self.assertEqual(data['categories'], ['metadata'])
        self.assertEqual(data['api'], ['3.0'])

    def test_special_characters_in_name(self):
        """Names with quotes and backslashes produce valid TOML."""
        result = generate_manifest('Plugin "Foo" \\Bar', description='A "test" plugin')
        data = tomllib.loads(result)
        self.assertEqual(data['name'], 'Plugin "Foo" \\Bar')
        self.assertEqual(data['description'], 'A "test" plugin')

    def test_unicode_name(self):
        """Unicode names produce valid TOML."""
        result = generate_manifest("Plugin d'Étiquetage")
        data = tomllib.loads(result)
        self.assertEqual(data['name'], "Plugin d'Étiquetage")

    def test_with_source_locale(self):
        """Custom source_locale is included when i18n is enabled."""
        result = generate_manifest('Test', with_i18n=True, source_locale='fr')
        data = tomllib.loads(result)
        self.assertEqual(data['source_locale'], 'fr')

    def test_source_locale_default(self):
        """Default source_locale is 'en'."""
        result = generate_manifest('Test', with_i18n=True)
        data = tomllib.loads(result)
        self.assertEqual(data['source_locale'], 'en')

    def test_source_locale_whitespace_fallback(self):
        """Whitespace-only source_locale falls back to 'en'."""
        result = generate_manifest('Test', with_i18n=True, source_locale='  ')
        data = tomllib.loads(result)
        self.assertEqual(data['source_locale'], 'en')

    def test_other_locale_differs_from_source(self):
        """i18n example locale differs from source_locale."""
        result = generate_manifest('Test', with_i18n=True, source_locale='de')
        self.assertIn('# en = ""', result)

    def test_other_locale_default_is_de(self):
        """When source_locale is not 'de', example locale is 'de'."""
        result = generate_manifest('Test', with_i18n=True, source_locale='en')
        self.assertIn('# de = ""', result)

    def test_with_long_description(self):
        """long_description produces valid TOML."""
        result = generate_manifest('Test', long_description='A longer description')
        data = tomllib.loads(result)
        self.assertEqual(data['long_description'], 'A longer description')

    def test_long_description_i18n_section(self):
        """long_description with i18n includes long_description_i18n comment."""
        result = generate_manifest('Test', long_description='Long desc', with_i18n=True)
        self.assertIn('# [long_description_i18n]', result)

    def test_no_long_description_i18n_without_long_description(self):
        """Without long_description, no long_description_i18n section."""
        result = generate_manifest('Test', with_i18n=True)
        self.assertNotIn('long_description_i18n', result)


class TestGeneratePluginInitPy(PicardTestCase):
    def test_contains_enable(self):
        result = generate_plugin_init_py()
        self.assertIn('def enable(api: PluginApi)', result)

    def test_contains_disable(self):
        result = generate_plugin_init_py()
        self.assertIn('def disable()', result)

    def test_contains_import(self):
        result = generate_plugin_init_py()
        self.assertIn('from picard.plugin3.api import PluginApi', result)


class TestGenerateReadme(PicardTestCase):
    def test_contains_plugin_name(self):
        result = generate_readme('My Cool Plugin')
        self.assertIn('# My Cool Plugin', result)

    def test_contains_install_path(self):
        result = generate_readme('My Cool Plugin')
        self.assertIn('my-cool-plugin', result)

    def test_contains_picard_link(self):
        result = generate_readme('Test')
        self.assertIn('picard.musicbrainz.org', result)

    def test_escapes_markdown_special_chars(self):
        result = generate_readme('Plugin #1 *bold*')
        self.assertIn(r'# Plugin \#1 \*bold\*', result)


class TestGenerateGitignore(PicardTestCase):
    def test_returns_content(self):
        result = generate_gitignore()
        self.assertTrue(result.strip())
