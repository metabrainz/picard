# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
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

import sys


if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from test.test_config import TestPicardConfigCommon

from picard.config import (
    BoolOption,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    TextOption,
)
from picard.const.cover_processing import ImageFormat
from picard.profiles.exporter import export_profile


class TestProfileExport(TestPicardConfigCommon):
    def setUp(self):
        super().setUp()
        ListOption.add_if_missing('profiles', 'user_profiles', [])
        Option.add_if_missing('profiles', 'user_profile_settings', {})
        Option('setting', 'file_renaming_scripts', {})

    def _setup_profile(self, profile_id, settings):
        self.config.profiles['user_profiles'] = [
            {'id': profile_id, 'enabled': True, 'position': 0, 'title': 'Test'},
        ]
        self.config.profiles['user_profile_settings'] = {
            profile_id: settings,
        }

    def test_export_basic_settings(self):
        BoolOption('setting', 'standardize_artists', False, title="Standardize", in_profile=True)
        BoolOption('setting', 'write_id3v23', True, title="Write ID3v2.3", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'standardize_artists': True,
                'write_id3v23': False,
            },
        )

        result = export_profile(self.config, 'p1', title='Test Profile')
        parsed = tomllib.loads(result)

        self.assertEqual(parsed['profile']['title'], 'Test Profile')
        self.assertIn('picard_version', parsed['profile'])
        self.assertEqual(parsed['profile']['format_version'], 1)
        self.assertIn('created', parsed['profile'])
        self.assertTrue(parsed['settings']['standardize_artists'])
        self.assertFalse(parsed['settings']['write_id3v23'])

    def test_export_share_mode_excludes_non_shareable(self):
        TextOption('setting', 'proxy_password', '', title="Proxy password", in_profile=True, shareable=False)
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'proxy_password': 'secret123',
                'rename_files': True,
            },
        )

        result = export_profile(self.config, 'p1', title='Test', mode='share')
        parsed = tomllib.loads(result)

        self.assertNotIn('proxy_password', parsed.get('settings', {}))
        self.assertTrue(parsed['settings']['rename_files'])

    def test_export_backup_mode_includes_non_shareable(self):
        TextOption('setting', 'proxy_password', '', title="Proxy password", in_profile=True, shareable=False)
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'proxy_password': 'secret123',
                'rename_files': True,
            },
        )

        result = export_profile(self.config, 'p1', title='Test', mode='backup')
        parsed = tomllib.loads(result)

        self.assertEqual(parsed['settings']['proxy_password'], 'secret123')
        self.assertTrue(parsed['settings']['rename_files'])

    def test_export_skips_none_values(self):
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)
        BoolOption('setting', 'move_files', False, title="Move", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'rename_files': True,
                'move_files': None,  # tracked but not overridden
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        self.assertTrue(parsed['settings']['rename_files'])
        self.assertNotIn('move_files', parsed.get('settings', {}))

    def test_export_tagger_scripts_share_mode(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'list_of_scripts': [
                    (0, 'Enabled Script', True, '$set(foo,bar)'),
                    (1, 'Disabled Script', False, '$noop()'),
                ],
            },
        )

        result = export_profile(self.config, 'p1', title='Test', mode='share')
        parsed = tomllib.loads(result)

        # Share mode: only enabled scripts
        scripts = parsed['scripts']['tagging']
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0]['title'], 'Enabled Script')
        self.assertEqual(scripts[0]['script'], '$set(foo,bar)')
        self.assertNotIn('enabled', scripts[0])

    def test_export_tagger_scripts_backup_mode(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'list_of_scripts': [
                    (0, 'Enabled Script', True, '$set(foo,bar)'),
                    (1, 'Disabled Script', False, '$noop()'),
                ],
            },
        )

        result = export_profile(self.config, 'p1', title='Test', mode='backup')
        parsed = tomllib.loads(result)

        # Backup mode: all scripts with enabled field
        scripts = parsed['scripts']['tagging']
        self.assertEqual(len(scripts), 2)
        self.assertTrue(scripts[0]['enabled'])
        self.assertFalse(scripts[1]['enabled'])

    def test_export_naming_script(self):
        TextOption('setting', 'active_file_naming_script_id', '', title="Active script", in_profile=True)

        self.config.setting['file_renaming_scripts'] = {
            'test-uuid': {
                'id': 'test-uuid',
                'title': 'My Script',
                'script': '$if2(%albumartist%,%artist%)/%album%',
                'author': 'Test Author',
                'description': 'A test naming script',
                'license': 'GPL-2.0',
                'version': '1.2',
                'last_updated': '2026-06-21 12:00:00 UTC',
                'script_language_version': '1.1',
            },
        }

        self._setup_profile(
            'p1',
            {
                'active_file_naming_script_id': 'test-uuid',
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        naming = parsed['scripts']['naming']
        self.assertEqual(naming['id'], 'test-uuid')
        self.assertEqual(naming['title'], 'My Script')
        self.assertIn('%albumartist%', naming['script'])
        self.assertNotIn('preset', naming)
        # Metadata fields
        self.assertEqual(naming['author'], 'Test Author')
        self.assertEqual(naming['description'], 'A test naming script')
        self.assertEqual(naming['license'], 'GPL-2.0')
        self.assertEqual(naming['version'], '1.2')
        self.assertEqual(naming['last_updated'], '2026-06-21 12:00:00 UTC')
        self.assertEqual(naming['script_language_version'], '1.1')

    def test_export_preset_naming_script(self):
        TextOption('setting', 'active_file_naming_script_id', '', title="Active script", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'active_file_naming_script_id': 'Preset 1',
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        naming = parsed['scripts']['naming']
        self.assertEqual(naming['id'], 'Preset 1')
        self.assertTrue(naming['preset'])

    def test_export_excludes_plugin_settings(self):
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'rename_files': True,
                'plugin.abc123/some_option': 'value',
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        self.assertNotIn('plugins', parsed)
        self.assertNotIn('plugin.abc123/some_option', parsed.get('settings', {}))

    def test_export_partial_profile_no_settings(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'list_of_scripts': [
                    (0, 'My Script', True, '$set(date,%date%)'),
                ],
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        self.assertNotIn('settings', parsed)
        self.assertEqual(len(parsed['scripts']['tagging']), 1)

    def test_export_empty_profile(self):
        self._setup_profile('p1', {})

        result = export_profile(self.config, 'p1', title='Empty')
        parsed = tomllib.loads(result)

        self.assertEqual(parsed['profile']['title'], 'Empty')
        self.assertNotIn('settings', parsed)
        self.assertNotIn('scripts', parsed)

    def test_export_description_and_author(self):
        self._setup_profile('p1', {})

        result = export_profile(
            self.config,
            'p1',
            title='My Profile',
            description='A test profile',
            author='Test Author',
        )
        parsed = tomllib.loads(result)

        self.assertEqual(parsed['profile']['description'], 'A test profile')
        self.assertEqual(parsed['profile']['author'], 'Test Author')

    def test_export_list_of_tuples(self):
        ListOption('setting', 'ca_providers', [], title="Providers", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'ca_providers': [
                    ('Cover Art Archive', True),
                    ('UrlRelationships', False),
                ],
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        expected = [['Cover Art Archive', True], ['UrlRelationships', False]]
        self.assertEqual(parsed['settings']['ca_providers'], expected)

    def test_export_script_not_in_settings(self):
        """active_file_naming_script_id and list_of_scripts should not appear in [settings]."""
        TextOption('setting', 'active_file_naming_script_id', '', title="Active script", in_profile=True)
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)

        self.config.setting['file_renaming_scripts'] = {
            'test-uuid': {'id': 'test-uuid', 'title': 'Script', 'script': 'test'},
        }

        self._setup_profile(
            'p1',
            {
                'active_file_naming_script_id': 'test-uuid',
                'list_of_scripts': [(0, 'Script', True, '$noop()')],
                'rename_files': True,
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        # These should be in [scripts], not [settings]
        settings = parsed.get('settings', {})
        self.assertNotIn('active_file_naming_script_id', settings)
        self.assertNotIn('list_of_scripts', settings)
        self.assertNotIn('enable_tagger_scripts', settings)
        self.assertTrue(settings['rename_files'])

    def test_export_dict_option(self):
        Option('setting', 'win_compat_replacements', {}, title="Replacements", in_profile=True)

        self._setup_profile(
            'p1',
            {
                'win_compat_replacements': {
                    '*': '_',
                    ':': '-',
                    '?': '',
                },
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        expected = {'*': '_', ':': '-', '?': ''}
        self.assertEqual(parsed['settings']['win_compat_replacements'], expected)

    def test_export_int_option(self):
        IntOption('setting', 'caa_image_size', 500, title="Image size", in_profile=True)

        self._setup_profile('p1', {'caa_image_size': 1000})

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        self.assertEqual(parsed['settings']['caa_image_size'], 1000)

    def test_export_float_option(self):
        FloatOption('setting', 'match_min_similarity', 0.5, title="Similarity", in_profile=True)

        self._setup_profile('p1', {'match_min_similarity': 0.75})

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        self.assertAlmostEqual(parsed['settings']['match_min_similarity'], 0.75)

    def test_export_enum_option(self):
        Option('setting', 'cover_format', ImageFormat.JPEG, title="Format", in_profile=True)

        self._setup_profile('p1', {'cover_format': ImageFormat.PNG})

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        # Enum should be exported as its value string
        self.assertEqual(parsed['settings']['cover_format'], 'png')

    def test_export_naming_script_empty_metadata_omitted(self):
        TextOption('setting', 'active_file_naming_script_id', '', title="Active script", in_profile=True)

        self.config.setting['file_renaming_scripts'] = {
            'test-uuid': {
                'id': 'test-uuid',
                'title': 'Minimal Script',
                'script': '%artist%/%album%/%title%',
                'author': '',
                'description': '',
                'license': '',
                'version': '',
                'last_updated': '',
                'script_language_version': '',
            },
        }

        self._setup_profile(
            'p1',
            {
                'active_file_naming_script_id': 'test-uuid',
            },
        )

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        naming = parsed['scripts']['naming']
        self.assertEqual(naming['id'], 'test-uuid')
        self.assertEqual(naming['title'], 'Minimal Script')
        self.assertIn('%artist%', naming['script'])
        # Empty metadata fields should NOT be present
        self.assertNotIn('author', naming)
        self.assertNotIn('description', naming)
        self.assertNotIn('license', naming)
        self.assertNotIn('version', naming)
        self.assertNotIn('last_updated', naming)
        self.assertNotIn('script_language_version', naming)

    def test_export_tuple_option_transforms_elements(self):
        """Tuples should be recursively transformed, same as lists."""
        Option('setting', 'tuple_opt', (), title="Tuple option", in_profile=True)

        self._setup_profile('p1', {'tuple_opt': (ImageFormat.JPEG, ImageFormat.PNG)})

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        # Enum values inside the tuple should be exported as their .value
        self.assertEqual(parsed['settings']['tuple_opt'], ['jpeg', 'png'])

    def test_export_list_with_enum_elements(self):
        """List elements that are Enums should be converted to their values."""
        Option('setting', 'format_list', [], title="Format list", in_profile=True)

        self._setup_profile('p1', {'format_list': [ImageFormat.JPEG, ImageFormat.PNG]})

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        self.assertEqual(parsed['settings']['format_list'], ['jpeg', 'png'])

    def test_export_dict_with_complex_values(self):
        """Dict values should be recursively transformed."""
        Option('setting', 'complex_dict', {}, title="Complex dict", in_profile=True)

        self._setup_profile('p1', {'complex_dict': {'format': ImageFormat.PNG, 'count': 5}})

        result = export_profile(self.config, 'p1', title='Test')
        parsed = tomllib.loads(result)

        expected = {'format': 'png', 'count': 5}
        self.assertEqual(parsed['settings']['complex_dict'], expected)
