# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024, 2026 Laurent Monin
# Copyright (C) 2019-2024 Philipp Wolfer
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Gabriel Ferreira
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
import os

import PyQt6.QtCore
from PyQt6.QtCore import QByteArray

from test.test_config import TestPicardConfigCommon

from picard.config import (
    BoolOption,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    TextOption,
)
import picard.config_upgrade_hooks as hooks
from picard.const.cover_processing import ImageFormat
from picard.const.defaults import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_REPLACEMENT,
    DEFAULT_SCRIPT_NAME,
    DEFAULT_THEME_NAME,
)
from picard.options import StandardizeArtistNames
from picard.util import unique_numbered_title

from picard.ui.theme import UiTheme


class TestPicardConfigUpgrades(TestPicardConfigCommon):
    def test_all_hooks_have_tests(self):
        """Ensure every upgrade hook has at least one corresponding test method."""
        from picard.config_upgrade import (
            _UPGRADES_REGISTRY,
            UPGRADE_FUNCTION_PREFIX,
            autodetect_upgrade_hooks,
        )

        # Old-style hooks (upgrade_to_v* functions)
        hooks = autodetect_upgrade_hooks()
        test_prefix = 'test_' + UPGRADE_FUNCTION_PREFIX
        test_methods = {m for m in dir(self) if m.startswith(test_prefix)}
        for version, hook in hooks.items():
            prefix = 'test_' + hook.__name__
            matching = {m for m in test_methods if m.startswith(prefix)}
            self.assertTrue(matching, f"No test found for {hook.__name__} (version {version})")

        # New-style hooks (both @upgrade_settings and @upgrade_config)
        all_test_methods = {m for m in dir(self) if m.startswith('test_')}
        for version, _utype, func in _UPGRADES_REGISTRY:
            prefix = 'test_' + func.__name__
            matching = {m for m in all_test_methods if m.startswith(prefix)}
            self.assertTrue(matching, f"No test found for {func.__name__} (version {version})")

    def test_upgrade_to_v1_0_0final0_A(self):
        TextOption('setting', 'file_naming_format', '')

        self.config.setting['va_file_naming_format'] = 'abc'
        self.config.setting['use_va_format'] = True

        self.assertIn('va_file_naming_format', self.config.setting)
        self.assertIn('use_va_format', self.config.setting)

        hooks.upgrade_to_v1_0_0final0(self.config, interactive=False, merge=True)
        self.assertNotIn('va_file_naming_format', self.config.setting)
        self.assertNotIn('use_va_format', self.config.setting)
        self.assertIn('file_naming_format', self.config.setting)

    def test_upgrade_to_v1_0_0final0_B(self):
        TextOption('setting', 'file_naming_format', '')

        self.config.setting['va_file_naming_format'] = 'abc'
        self.config.setting['use_va_format'] = ""

        self.assertIn('va_file_naming_format', self.config.setting)
        self.assertIn('use_va_format', self.config.setting)

        hooks.upgrade_to_v1_0_0final0(self.config, interactive=False, merge=False)
        self.assertNotIn('va_file_naming_format', self.config.setting)
        self.assertNotIn('use_va_format', self.config.setting)
        self.assertNotIn('file_naming_format', self.config.setting)

    def test_upgrade_to_v1_3_0dev1(self):
        BoolOption('setting', 'windows_compatibility', False)

        self.config.setting['windows_compatible_filenames'] = True
        hooks.upgrade_to_v1_3_0dev1(self.config)
        self.assertNotIn('windows_compatible_filenames', self.config.setting)
        self.assertTrue(self.config.setting['windows_compatibility'])

    def test_upgrade_to_v1_3_0dev2(self):
        TextOption('setting', 'preserved_tags', '')
        self.config.setting['preserved_tags'] = "a b  c  "
        hooks.upgrade_to_v1_3_0dev2(self.config)
        self.assertEqual("a,b,c", self.config.setting['preserved_tags'])

    def test_upgrade_to_v1_3_0dev2_skip_list(self):
        ListOption('setting', 'preserved_tags', [])
        self.config.setting['preserved_tags'] = ['foo']
        hooks.upgrade_to_v1_3_0dev2(self.config)
        self.assertEqual(['foo'], self.config.setting['preserved_tags'])

    def test_upgrade_to_v1_3_0dev3(self):
        ListOption("setting", "preferred_release_countries", [])
        ListOption("setting", "preferred_release_formats", [])
        ListOption("setting", "enabled_plugins", [])
        ListOption("setting", "caa_image_types", [])
        ListOption("setting", "metadata_box_sizes", [])

        self.config.setting['preferred_release_countries'] = "a  b  c"
        self.config.setting['preferred_release_formats'] = "a  b  c"
        self.config.setting['enabled_plugins'] = 'a b c'
        self.config.setting['caa_image_types'] = 'a b c'
        self.config.setting['metadata_box_sizes'] = 'a b c'

        hooks.upgrade_to_v1_3_0dev3(self.config)
        self.assertEqual(["a", "b", "c"], self.config.setting['preferred_release_countries'])
        self.assertEqual(["a", "b", "c"], self.config.setting['preferred_release_formats'])
        self.assertEqual(["a", "b", "c"], self.config.setting['enabled_plugins'])
        self.assertEqual(["a", "b", "c"], self.config.setting['caa_image_types'])
        self.assertEqual(["a", "b", "c"], self.config.setting['metadata_box_sizes'])

    def test_upgrade_to_v1_3_0dev4(self):
        ListOption("setting", "release_type_scores", [])

        self.config.setting['release_type_scores'] = "a 0.1 b 0.2 c 1"
        hooks.upgrade_to_v1_3_0dev4(self.config)

        self.assertEqual([('a', 0.1), ('b', 0.2), ('c', 1.0)], self.config.setting['release_type_scores'])

    def test_upgrade_to_v1_4_0dev2(self):
        self.config.setting['username'] = 'abc'
        self.config.setting['password'] = 'abc'  # nosec

        hooks.upgrade_to_v1_4_0dev2(self.config)
        self.assertNotIn('username', self.config.setting)
        self.assertNotIn('password', self.config.setting)

    def test_upgrade_to_v1_4_0dev3(self):
        ListOption("setting", "ca_providers", [])

        self.config.setting['ca_provider_use_amazon'] = True
        self.config.setting['ca_provider_use_caa'] = True
        self.config.setting['ca_provider_use_whitelist'] = False
        self.config.setting['ca_provider_use_caa_release_group_fallback'] = True

        hooks.upgrade_to_v1_4_0dev3(self.config)
        self.assertIn('ca_providers', self.config.setting)
        self.assertIn(('Amazon', True), self.config.setting['ca_providers'])
        self.assertIn(('Cover Art Archive', True), self.config.setting['ca_providers'])
        self.assertIn(('Whitelist', False), self.config.setting['ca_providers'])
        self.assertIn(('CaaReleaseGroup', True), self.config.setting['ca_providers'])
        self.assertEqual(len(self.config.setting['ca_providers']), 4)

    def test_upgrade_to_v1_4_0dev4(self):
        TextOption("setting", "file_naming_format", "")

        self.config.setting['file_naming_format'] = 'xxx'
        hooks.upgrade_to_v1_4_0dev4(self.config)
        self.assertEqual('xxx', self.config.setting['file_naming_format'])

        self.config.setting['file_naming_format'] = hooks.OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3
        hooks.upgrade_to_v1_4_0dev4(self.config)
        self.assertEqual(DEFAULT_FILE_NAMING_FORMAT, self.config.setting['file_naming_format'])

    def test_upgrade_to_v1_4_0dev5(self):
        hooks.upgrade_to_v1_4_0dev5(self.config)

    def test_upgrade_to_v1_4_0dev6(self):
        BoolOption('setting', 'enable_tagger_scripts', False)
        ListOption('setting', 'list_of_scripts', [])

        self.config.setting['enable_tagger_script'] = True
        self.config.setting['tagger_script'] = "abc"
        hooks.upgrade_to_v1_4_0dev6(self.config)

        self.assertNotIn('enable_tagger_script', self.config.setting)
        self.assertNotIn('tagger_script', self.config.setting)

        self.assertTrue(self.config.setting['enable_tagger_scripts'])
        self.assertEqual(
            [(0, unique_numbered_title(DEFAULT_SCRIPT_NAME, []), True, 'abc')],
            self.config.setting['list_of_scripts'],
        )

    def test_upgrade_to_v1_4_0dev7(self):
        BoolOption('setting', 'embed_only_one_front_image', False)

        self.config.setting['save_only_front_images_to_tags'] = True
        hooks.upgrade_to_v1_4_0dev7(self.config)
        self.assertNotIn('save_only_front_images_to_tags', self.config.setting)
        self.assertTrue(self.config.setting['embed_only_one_front_image'])

    def test_upgrade_to_v2_0_0dev3(self):
        IntOption("setting", "caa_image_size", 500)

        self.config.setting['caa_image_size'] = 0
        hooks.upgrade_to_v2_0_0dev3(self.config)
        self.assertEqual(250, self.config.setting['caa_image_size'])

        self.config.setting['caa_image_size'] = 501
        hooks.upgrade_to_v2_0_0dev3(self.config)
        self.assertEqual(501, self.config.setting['caa_image_size'])

    def test_upgrade_to_v2_1_0dev1(self):
        BoolOption("setting", "use_genres", False)
        IntOption("setting", "max_genres", 5)
        IntOption("setting", "min_genre_usage", 90)
        TextOption("setting", "ignore_genres", "seen live, favorites, fixme, owned")
        TextOption("setting", "join_genres", "")
        BoolOption("setting", "only_my_genres", False)
        BoolOption("setting", "artists_genres", False)
        BoolOption("setting", "folksonomy_tags", False)

        self.config.setting['folksonomy_tags'] = True
        self.config.setting['max_tags'] = 6
        self.config.setting['min_tag_usage'] = 85
        self.config.setting['ignore_tags'] = "abc"
        self.config.setting['join_tags'] = "abc"
        self.config.setting['only_my_tags'] = True
        self.config.setting['artists_tags'] = True

        hooks.upgrade_to_v2_1_0dev1(self.config)
        self.assertEqual(self.config.setting['use_genres'], True)
        self.assertEqual(self.config.setting['max_genres'], 6)
        self.assertEqual(self.config.setting['min_genre_usage'], 85)
        self.assertEqual(self.config.setting['ignore_genres'], "abc")
        self.assertEqual(self.config.setting['join_genres'], "abc")
        self.assertEqual(self.config.setting['only_my_genres'], True)
        self.assertEqual(self.config.setting['artists_genres'], True)

        self.assertIn('folksonomy_tags', self.config.setting)

        self.assertNotIn('max_tags', self.config.setting)
        self.assertNotIn('min_tag_usage', self.config.setting)
        self.assertNotIn('ignore_tags', self.config.setting)
        self.assertNotIn('join_tags', self.config.setting)
        self.assertNotIn('only_my_tags', self.config.setting)
        self.assertNotIn('artists_tags', self.config.setting)

    def test_upgrade_to_v2_2_0dev3(self):
        TextOption("setting", "ignore_genres", "")
        TextOption("setting", "genres_filter", "")

        self.config.setting['ignore_genres'] = "a, b,c"
        hooks.upgrade_to_v2_2_0dev3(self.config)
        self.assertNotIn('ignore_genres', self.config.setting)
        self.assertEqual(self.config.setting['genres_filter'], "-a\n-b\n-c")

    def test_upgrade_to_v2_2_0dev4(self):
        TextOption("setting", "file_naming_format", "")

        self.config.setting['file_naming_format'] = 'xxx'
        hooks.upgrade_to_v2_2_0dev4(self.config)
        self.assertEqual('xxx', self.config.setting['file_naming_format'])

        self.config.setting['file_naming_format'] = hooks.OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1
        hooks.upgrade_to_v2_2_0dev4(self.config)
        self.assertEqual(DEFAULT_FILE_NAMING_FORMAT, self.config.setting['file_naming_format'])

    def test_upgrade_to_v2_4_0beta3(self):
        ListOption("setting", "preserved_tags", [])
        self.config.setting['preserved_tags'] = 'foo,bar'
        hooks.upgrade_to_v2_4_0beta3(self.config)
        self.assertEqual(['foo', 'bar'], self.config.setting['preserved_tags'])

    def test_upgrade_to_v2_4_0beta3_already_done(self):
        ListOption("setting", "preserved_tags", [])
        self.config.setting['preserved_tags'] = ['foo', 'bar']
        hooks.upgrade_to_v2_4_0beta3(self.config)
        self.assertEqual(['foo', 'bar'], self.config.setting['preserved_tags'])

    def test_upgrade_to_v2_5_0dev1(self):
        ListOption("setting", "ca_providers", [])

        self.config.setting['ca_providers'] = [
            ('Cover Art Archive', True),
            ('Whitelist', True),
            ('Local', False),
        ]
        expected = [
            ('Cover Art Archive', True),
            ('UrlRelationships', True),
            ('Local', False),
        ]
        hooks.upgrade_to_v2_5_0dev1(self.config)
        self.assertEqual(expected, self.config.setting['ca_providers'])

    def test_upgrade_to_v2_5_0dev1_profiles(self):
        ListOption('setting', 'ca_providers', [], in_profile=True)
        ListOption.add_if_missing('profiles', 'user_profiles', [])
        Option.add_if_missing('profiles', 'user_profile_settings', {})

        self.config.setting['ca_providers'] = [
            ('Cover Art Archive', True),
            ('Whitelist', True),
        ]
        self.config.profiles['user_profiles'] = [
            {'id': 'p1', 'enabled': True, 'position': 0, 'title': 'Test'},
        ]
        self.config.profiles['user_profile_settings'] = {
            'p1': {
                'ca_providers': [
                    ('Cover Art Archive', False),
                    ('Whitelist', False),
                    ('Local', True),
                ],
            },
        }

        hooks.upgrade_to_v2_5_0dev1(self.config)

        # Base config updated
        with self.config.setting.no_profile():
            self.assertEqual(
                [('Cover Art Archive', True), ('UrlRelationships', True)],
                self.config.setting['ca_providers'],
            )
        # Profile updated
        profile_settings = self.config.profiles['user_profile_settings']['p1']
        self.assertEqual(
            [('Cover Art Archive', False), ('UrlRelationships', False), ('Local', True)],
            profile_settings['ca_providers'],
        )

    def test_upgrade_to_v2_5_0dev2(self):
        Option("persist", "splitter_state", QByteArray())
        Option("persist", "bottom_splitter_state", QByteArray())
        self.config.persist["splitter_state"] = b'foo'
        self.config.persist["bottom_splitter_state"] = b'bar'
        hooks.upgrade_to_v2_5_0dev2(self.config)
        self.assertEqual(b'', self.config.persist['splitter_state'])
        self.assertEqual(b'', self.config.persist['bottom_splitter_state'])

    def test_upgrade_to_v2_6_0dev1(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = "/usr/bin/fpcalc"
        hooks.upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("/usr/bin/fpcalc", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0dev1_empty(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = None
        hooks.upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0dev1_snap(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = "/snap/picard/221/usr/bin/fpcalc"
        hooks.upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0dev1_frozen(self):
        from unittest.mock import patch

        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = r"C:\Program Files\MusicBrainz Picard\fpcalc.exe"
        with patch.object(hooks, 'IS_FROZEN', True):
            hooks.upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0beta2(self):
        BoolOption('setting', 'image_type_as_filename', False)
        BoolOption('setting', 'save_only_one_front_image', False)

        self.config.setting['caa_image_type_as_filename'] = True
        self.config.setting['caa_save_single_front_image'] = True
        hooks.upgrade_to_v2_6_0beta2(self.config)
        self.assertNotIn('caa_image_type_as_filename', self.config.setting)
        self.assertTrue(self.config.setting['image_type_as_filename'])
        self.assertNotIn('caa_save_single_front_image', self.config.setting)
        self.assertTrue(self.config.setting['save_only_one_front_image'])

    def test_upgrade_to_v2_6_0beta3(self):
        # Legacy setting
        BoolOption('setting', 'use_system_theme', False)
        self.config.setting['use_system_theme'] = True
        del Option.registry['setting', 'use_system_theme']
        # New setting
        TextOption('setting', 'ui_theme', str(UiTheme.DEFAULT))
        hooks.upgrade_to_v2_6_0beta3(self.config)
        self.assertNotIn('use_system_theme', self.config.setting)
        self.assertIn('ui_theme', self.config.setting)
        self.assertEqual('system', self.config.setting['ui_theme'])

    def test_upgrade_to_v2_7_0dev2(self):
        Option('persist', 'bottom_splitter_state', b'')
        Option('persist', 'splitter_state', b'')
        Option('persist', 'splitters_MainWindow', {})
        self.config.persist['bottom_splitter_state'] = b'bottom'
        self.config.persist['splitter_state'] = b'main'
        hooks.upgrade_to_v2_7_0dev2(self.config)
        self.assertNotIn('bottom_splitter_state', self.config.persist)
        self.assertNotIn('splitter_state', self.config.persist)
        splitters = self.config.persist['splitters_MainWindow']
        self.assertEqual(b'bottom', splitters['main_window_bottom_splitter'])
        self.assertEqual(b'main', splitters['main_panel_splitter'])

    def test_upgrade_to_v2_7_0dev3(self):
        # Legacy settings
        ListOption('setting', 'file_naming_scripts', [])
        self.config.setting['file_naming_scripts'] = [
            '{"id": "766bb2ce-5170-45f1-900c-02e7f9bd41cb", "title": "Script 1", "script": "$noop(1)"}',
            '{"id": "ab0abb63-797c-4a20-95a8-df1b9109f883", "title": "Script 2", "script": "$noop(2)"}',
        ]
        TextOption('setting', 'file_naming_format', DEFAULT_FILE_NAMING_FORMAT)
        self.config.setting['file_naming_format'] = "%title%"
        del Option.registry[('setting', 'file_naming_scripts')]
        del Option.registry[('setting', 'file_naming_format')]
        # New settings
        Option('setting', 'file_renaming_scripts', {})
        TextOption('setting', 'selected_file_naming_script_id', '')
        hooks.upgrade_to_v2_7_0dev3(self.config)
        new_scripts = self.config.setting['file_renaming_scripts']
        selected_script_id = self.config.setting['selected_file_naming_script_id']
        self.assertEqual(3, len(new_scripts))
        self.assertIn(selected_script_id, new_scripts)
        script1 = new_scripts['766bb2ce-5170-45f1-900c-02e7f9bd41cb']
        self.assertEqual('Script 1', script1['title'])
        self.assertEqual('$noop(1)', script1['script'])
        script2 = new_scripts['ab0abb63-797c-4a20-95a8-df1b9109f883']
        self.assertEqual('Script 2', script2['title'])
        self.assertEqual('$noop(2)', script2['script'])
        default_script = new_scripts[selected_script_id]
        self.assertEqual('Primary file naming script', default_script['title'])
        self.assertEqual('%title%', default_script['script'])

    def test_upgrade_to_v2_7_0dev4(self):
        # Legacy settings
        TextOption('setting', 'artist_script_exception', '')
        TextOption('setting', 'artist_locale', '')
        self.config.setting['artist_script_exception'] = 'LATIN'
        self.config.setting['artist_locale'] = 'en'
        del Option.registry[('setting', 'artist_script_exception')]
        del Option.registry[('setting', 'artist_locale')]
        # New settings
        ListOption('setting', 'artist_script_exceptions', [])
        ListOption('setting', 'artist_locales', ['en'])
        hooks.upgrade_to_v2_7_0dev4(self.config)
        self.assertEqual(['LATIN'], self.config.setting['artist_script_exceptions'])
        self.assertEqual(['en'], self.config.setting['artist_locales'])

    def test_upgrade_to_v2_7_0dev5(self):
        # Legacy settings
        ListOption('setting', 'artist_script_exceptions', [])
        IntOption('setting', 'artist_script_exception_weighting', 0)
        self.config.setting['artist_script_exceptions'] = ['LATIN', 'HEBREW']
        self.config.setting['artist_script_exception_weighting'] = 20
        del Option.registry[('setting', 'artist_script_exceptions')]
        del Option.registry[('setting', 'artist_script_exception_weighting')]
        # New settings
        ListOption('setting', 'script_exceptions', [])
        hooks.upgrade_to_v2_7_0dev5(self.config)
        self.assertEqual(
            self.config.setting['script_exceptions'],
            [
                ('LATIN', 20),
                ('HEBREW', 20),
            ],
        )

    def test_upgrade_to_v2_8_0dev2(self):
        ListOption('setting', 'toolbar_layout', [])
        self.config.setting['toolbar_layout'] = [
            'add_directory_action',
            'extract_and_submit_acousticbrainz_features_action',
            'save_action',
        ]
        expected = ['add_directory_action', 'save_action']
        hooks.upgrade_to_v2_8_0dev2(self.config)
        self.assertEqual(expected, self.config.setting['toolbar_layout'])
        hooks.upgrade_to_v2_8_0dev2(self.config)
        self.assertEqual(expected, self.config.setting['toolbar_layout'])

    def test_upgrade_to_v2_9_0alpha2(self):
        from picard.script import get_file_naming_script_presets

        Option('setting', 'file_renaming_scripts', {})
        self.config.setting['file_renaming_scripts'] = {}
        hooks.upgrade_to_v2_9_0alpha2(self.config)
        scripts = self.config.setting['file_renaming_scripts']
        preset_ids = {item['id'] for item in get_file_naming_script_presets()}
        for preset_id in preset_ids:
            self.assertIn(preset_id, scripts)

    def test_upgrade_to_v3_0_0dev1(self):
        Option('persist', 'current_directory', '')
        Option('persist', 'obsolete_qt5_state', b'')
        self.config.persist['current_directory'] = '/home/test'
        self.config.persist['obsolete_qt5_state'] = b'data'
        # Write directly to simulate Qt5 persisted keys
        self.config.setValue('persist/some_unknown_key', b'old')
        hooks.upgrade_to_v3_0_0dev1(self.config)
        self.assertEqual('/home/test', self.config.persist['current_directory'])
        self.assertNotIn('persist/some_unknown_key', self.config.allKeys())

    def test_upgrade_to_v3_0_0dev2(self):
        Option('persist', 'splitters_OptionsDialog', b'')
        self.config.persist['splitters_OptionsDialog'] = b'state'
        hooks.upgrade_to_v3_0_0dev2(self.config)
        self.assertEqual(b'', self.config.persist['splitters_OptionsDialog'])

    def test_rename_toolbar_multiselect(self):
        """Test new-style @upgrade_settings hook on ConfigSection."""
        BoolOption('setting', 'allow_multi_dirs_selection', False)

        self.config.setting['toolbar_multiselect'] = True
        hooks.rename_toolbar_multiselect(self.config.setting)
        self.assertNotIn('toolbar_multiselect', self.config.setting)
        self.assertTrue(self.config.setting['allow_multi_dirs_selection'])

    def test_rename_toolbar_multiselect_dict(self):
        """Test new-style @upgrade_settings hook on plain dict."""
        settings = {'toolbar_multiselect': True}
        hooks.rename_toolbar_multiselect(settings)
        self.assertNotIn('toolbar_multiselect', settings)
        self.assertTrue(settings['allow_multi_dirs_selection'])

    def test_upgrade_to_v3_0_0dev4(self):
        Option('persist', 'album_view_header_state', QByteArray())
        Option('persist', 'file_view_header_state', QByteArray())
        BoolOption('persist', 'album_view_header_locked', False)
        BoolOption('persist', 'file_view_header_locked', False)

        self.config.persist['album_view_header_state'] = b'foo'
        self.config.persist['file_view_header_state'] = b'bar'

        # test not locked, states shouldn't be modified
        hooks.upgrade_to_v3_0_0dev4(self.config)
        self.assertEqual(b'foo', self.config.persist['album_view_header_state'])
        self.assertEqual(b'bar', self.config.persist['file_view_header_state'])

        # test locked, states should be removed
        self.config.persist['album_view_header_locked'] = True
        self.config.persist['file_view_header_locked'] = True
        hooks.upgrade_to_v3_0_0dev4(self.config)
        self.assertEqual(b'', self.config.persist['album_view_header_state'])
        self.assertEqual(b'', self.config.persist['file_view_header_state'])

    def test_upgrade_to_v3_0_0dev5(self):
        TextOption('setting', 'replace_dir_separator', DEFAULT_REPLACEMENT)
        self.config.setting['replace_dir_separator'] = os.sep
        hooks.upgrade_to_v3_0_0dev5(self.config)
        self.assertEqual(DEFAULT_REPLACEMENT, self.config.setting['replace_dir_separator'])

        if os.altsep:
            self.config.setting['replace_dir_separator'] = os.altsep
            hooks.upgrade_to_v3_0_0dev5(self.config)
            self.assertEqual(DEFAULT_REPLACEMENT, self.config.setting['replace_dir_separator'])

    def test_upgrade_to_v3_0_0dev6(self):
        BoolOption('setting', 'standardize_instruments', False)
        BoolOption('setting', 'standardize_vocals', False)
        self.config.setting['standardize_instruments'] = True
        hooks.upgrade_to_v3_0_0dev6(self.config)
        self.assertTrue(self.config.setting['standardize_vocals'])

    def test_upgrade_to_v3_0_0dev7(self):
        TextOption('setting', 'ui_theme', DEFAULT_THEME_NAME)
        self.config.setting['ui_theme'] = 'system'
        hooks.upgrade_to_v3_0_0dev7(self.config)
        self.assertEqual(DEFAULT_THEME_NAME, self.config.setting['ui_theme'])

    def test_rename_dont_write_tags(self):
        BoolOption('setting', 'enable_tag_saving', True)
        self.config.setting['dont_write_tags'] = True
        hooks.rename_dont_write_tags(self.config.setting)
        self.assertNotIn('dont_write_tags', self.config.setting)
        self.assertFalse(self.config.setting['enable_tag_saving'])

    def test_rename_dont_write_tags_dict(self):
        settings = {'dont_write_tags': True}
        hooks.rename_dont_write_tags(settings)
        self.assertNotIn('dont_write_tags', settings)
        self.assertFalse(settings['enable_tag_saving'])

    def test_remove_old_plugin_options(self):
        from PyQt6 import QtCore

        # Add old plugin options that should be removed
        Option('persist', 'plugins_list_sort_order', QtCore.Qt.SortOrder.AscendingOrder)
        Option('persist', 'plugins_list_sort_section', 0)
        Option('persist', 'plugins_list_state', QtCore.QByteArray())
        ListOption('setting', 'enabled_plugins', [])

        # Set some values
        self.config.persist['plugins_list_sort_order'] = QtCore.Qt.SortOrder.DescendingOrder
        self.config.persist['plugins_list_sort_section'] = 1
        self.config.persist['plugins_list_state'] = QtCore.QByteArray(b'test')
        self.config.setting['enabled_plugins'] = ['plugin1', 'plugin2']

        hooks.remove_old_plugin_options(self.config)

        # Verify options were removed
        self.assertNotIn('plugins_list_sort_order', self.config.persist)
        self.assertNotIn('plugins_list_sort_section', self.config.persist)
        self.assertNotIn('plugins_list_state', self.config.persist)
        self.assertNotIn('enabled_plugins', self.config.setting)

    def test_lowercase_cover_art_formats(self):
        Option('setting', 'cover_tags_convert_to_format', ImageFormat.JPEG)
        Option('setting', 'cover_file_convert_to_format', ImageFormat.JPEG)

        self.config.setting['cover_tags_convert_to_format'] = 'WebP'
        self.config.setting['cover_file_convert_to_format'] = 'PNG'

        hooks.lowercase_cover_art_formats(self.config.setting)

        self.assertEqual(ImageFormat.WEBP, self.config.setting['cover_tags_convert_to_format'])
        self.assertEqual(ImageFormat.PNG, self.config.setting['cover_file_convert_to_format'])

    def test_lowercase_cover_art_formats_dict(self):
        settings = {
            'cover_tags_convert_to_format': 'TIFF',
            'cover_file_convert_to_format': 'JPEG',
        }
        hooks.lowercase_cover_art_formats(settings)
        self.assertEqual('tiff', settings['cover_tags_convert_to_format'])
        self.assertEqual('jpeg', settings['cover_file_convert_to_format'])

    def test_upgrade_to_v3_0_0a2(self):
        Option('setting', 'file_renaming_scripts', {})
        ListOption('setting', 'list_of_scripts', [])

        test_script = (
            r'$set(foo,$matchedtracks(baz)-$matchedtracks()-$matchedtracks(%album%)-$matchedtracks(foo$get(bar)))'
        )
        expected_script = '$set(foo,$matchedtracks()-$matchedtracks()-$matchedtracks()-$matchedtracks(foo$get(bar)))'

        self.config.setting['file_renaming_scripts'] = {
            '766bb2ce-5170-45f1-900c-02e7f9bd41cb': {
                "id": "766bb2ce-5170-45f1-900c-02e7f9bd41cb",
                "title": "Script 1",
                "script": test_script,
            },
        }
        self.config.setting['list_of_scripts'] = [
            (0, 'Script 1', True, test_script),
        ]

        hooks.upgrade_to_v3_0_0a2(self.config)

        result_naming_script = self.config.setting['file_renaming_scripts']['766bb2ce-5170-45f1-900c-02e7f9bd41cb']
        self.assertEqual(
            expected_script,
            result_naming_script['script'],
        )
        result_tagger_script = self.config.setting['list_of_scripts'][0]
        self.assertEqual(
            expected_script,
            result_tagger_script[3],
        )

    def test_upgrade_to_v3_0_0a2_profiles(self):
        Option('setting', 'file_renaming_scripts', {})
        ListOption('setting', 'list_of_scripts', [], in_profile=True)
        ListOption.add_if_missing('profiles', 'user_profiles', [])
        Option.add_if_missing('profiles', 'user_profile_settings', {})

        test_script = r'$set(foo,$matchedtracks(baz))'
        expected_script = '$set(foo,$matchedtracks())'

        self.config.setting['file_renaming_scripts'] = {
            'test-id': {'id': 'test-id', 'title': 'Test', 'script': test_script},
        }
        self.config.setting['list_of_scripts'] = [
            (0, 'Base Script', True, test_script),
        ]
        self.config.profiles['user_profiles'] = [
            {'id': 'p1', 'enabled': True, 'position': 0, 'title': 'Test'},
        ]
        self.config.profiles['user_profile_settings'] = {
            'p1': {
                'list_of_scripts': [
                    (0, 'Profile Script', True, test_script),
                ],
            },
        }

        hooks.upgrade_to_v3_0_0a2(self.config)

        # Base config updated
        self.assertEqual(expected_script, self.config.setting['list_of_scripts'][0][3])
        self.assertEqual(
            expected_script,
            self.config.setting['file_renaming_scripts']['test-id']['script'],
        )
        # Profile updated
        profile_settings = self.config.profiles['user_profile_settings']['p1']
        self.assertEqual(expected_script, profile_settings['list_of_scripts'][0][3])

    def test_upgrade_to_v3_0_0a3(self):
        Option('persist', 'album_view_header_state', PyQt6.QtCore.QByteArray())
        Option('persist', 'file_view_header_state', PyQt6.QtCore.QByteArray())
        self.config.persist['album_view_header_state'] = b'a'
        self.config.persist['file_view_header_state'] = b'a'

        hooks.upgrade_to_v3_0_0a3(self.config)

        self.assertNotIn('album_view_header_state', self.config.persist)
        self.assertNotIn('file_view_header_state', self.config.persist)

    def test_rename_artist_locales(self):
        ListOption('setting', 'translation_locales', ['en'])

        self.config.setting['artist_locales'] = ['fr', 'de']
        hooks.rename_artist_locales(self.config.setting)
        self.assertNotIn('artist_locales', self.config.setting)
        self.assertEqual(self.config.setting['translation_locales'], ['fr', 'de'])

    def test_rename_artist_locales_dict(self):
        settings = {'artist_locales': ['fr', 'de']}
        hooks.rename_artist_locales(settings)
        self.assertNotIn('artist_locales', settings)
        self.assertEqual(settings['translation_locales'], ['fr', 'de'])

    def test_upgrade_to_v3_0_0b3(self):
        FloatOption('setting', 'file_lookup_threshold', 0.7)
        FloatOption('setting', 'cluster_lookup_threshold', 0.7)

        self.config.setting['file_lookup_threshold'] = 0.8
        self.config.setting['cluster_lookup_threshold'] = 0.6
        hooks.upgrade_to_v3_0_0b3(self.config)
        self.assertNotIn('file_lookup_threshold', self.config.setting)
        self.assertNotIn('cluster_lookup_threshold', self.config.setting)

    def test_rename_selected_file_naming_script_id(self):
        TextOption('setting', 'active_file_naming_script_id', '')
        self.config.setting['selected_file_naming_script_id'] = 'test-script-id'
        hooks.rename_selected_file_naming_script_id(self.config.setting)
        self.assertEqual(self.config.setting['active_file_naming_script_id'], 'test-script-id')
        self.assertNotIn('selected_file_naming_script_id', self.config.setting)

    def test_rename_selected_file_naming_script_id_dict(self):
        settings = {'selected_file_naming_script_id': 'test-script-id'}
        hooks.rename_selected_file_naming_script_id(settings)
        self.assertEqual(settings['active_file_naming_script_id'], 'test-script-id')
        self.assertNotIn('selected_file_naming_script_id', settings)

    def test_add_quick_menu_items(self):
        ListOption('setting', 'quick_menu_items', [])
        self.config.setting['quick_menu_items'] = ['save_images_to_tags', 'save_images_to_files']
        hooks.add_quick_menu_items(self.config.setting)
        items = self.config.setting['quick_menu_items']
        self.assertEqual(items[:3], ['rename_files', 'move_files', 'enable_tag_saving'])
        self.assertIn('save_images_to_tags', items)
        self.assertIn('save_images_to_files', items)

    def test_add_quick_menu_items_dict(self):
        settings = {'quick_menu_items': ['save_images_to_tags', 'save_images_to_files']}
        hooks.add_quick_menu_items(settings)
        items = settings['quick_menu_items']
        self.assertEqual(items[:3], ['rename_files', 'move_files', 'enable_tag_saving'])
        self.assertIn('save_images_to_tags', items)
        self.assertIn('save_images_to_files', items)

    def test_convert_standardize_artists(self):
        BoolOption('setting', 'standardize_artists', False)
        Option('setting', 'standardize_artist_names', StandardizeArtistNames.VARIATIONS)

        self.config.setting['standardize_artists'] = True
        hooks.convert_standardize_artists(self.config.setting)
        self.assertNotIn('standardize_artists', self.config.setting)
        self.assertEqual(self.config.setting['standardize_artist_names'], StandardizeArtistNames.ALL)

        self.config.setting['standardize_artists'] = False
        hooks.convert_standardize_artists(self.config.setting)
        self.assertNotIn('standardize_artists', self.config.setting)
        self.assertEqual(self.config.setting['standardize_artist_names'], StandardizeArtistNames.NONE)

    def test_convert_standardize_artists_dict(self):
        settings = {'standardize_artists': True}
        hooks.convert_standardize_artists(settings)
        self.assertNotIn('standardize_artists', settings)
        self.assertEqual(settings['standardize_artist_names'], StandardizeArtistNames.ALL.value)

        settings = {'standardize_artists': False}
        hooks.convert_standardize_artists(settings)
        self.assertNotIn('standardize_artists', settings)
        self.assertEqual(settings['standardize_artist_names'], StandardizeArtistNames.NONE.value)

    def test_convert_standardize_artists_missing(self):
        settings = {'other_option': 'value'}
        hooks.convert_standardize_artists(settings)
        # Should not create standardize_artist_names if old option wasn't present
        self.assertNotIn('standardize_artist_names', settings)

    def test_upgrade_to_v3_0_0b7(self):
        BoolOption('setting', 'rtd_updates_ask', True)
        self.config.persist['rtd_updates_ask'] = True

        hooks.upgrade_to_v3_0_0b7(self.config)

        self.assertNotIn('rtd_updates_ask', self.config.setting)
