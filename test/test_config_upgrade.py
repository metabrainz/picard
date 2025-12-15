# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024 Laurent Monin
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

from PyQt6.QtCore import QByteArray

from test.picardtestcase import PicardTestCase
from test.test_config import TestPicardConfigCommon

from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    Option,
    TextOption,
)
import picard.config_upgrade
from picard.config_upgrade import (
    OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3,
    OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1,
    UpgradeHooksAutodetectError,
    autodetect_upgrade_hooks,
    upgrade_to_v1_0_0final0,
    upgrade_to_v1_3_0dev1,
    upgrade_to_v1_3_0dev2,
    upgrade_to_v1_3_0dev3,
    upgrade_to_v1_3_0dev4,
    upgrade_to_v1_4_0dev2,
    upgrade_to_v1_4_0dev3,
    upgrade_to_v1_4_0dev4,
    upgrade_to_v1_4_0dev6,
    upgrade_to_v1_4_0dev7,
    upgrade_to_v2_0_0dev3,
    upgrade_to_v2_1_0dev1,
    upgrade_to_v2_2_0dev3,
    upgrade_to_v2_2_0dev4,
    upgrade_to_v2_4_0beta3,
    upgrade_to_v2_5_0dev1,
    upgrade_to_v2_5_0dev2,
    upgrade_to_v2_6_0beta2,
    upgrade_to_v2_6_0beta3,
    upgrade_to_v2_6_0dev1,
    upgrade_to_v2_7_0dev3,
    upgrade_to_v2_7_0dev4,
    upgrade_to_v2_7_0dev5,
    upgrade_to_v2_8_0dev2,
    upgrade_to_v3_0_0dev3,
    upgrade_to_v3_0_0dev4,
    upgrade_to_v3_0_0dev5,
    upgrade_to_v3_0_0dev7,
    upgrade_to_v3_0_0dev8,
)
from picard.const.defaults import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_REPLACEMENT,
    DEFAULT_SCRIPT_NAME,
    DEFAULT_THEME_NAME,
)
from picard.util import unique_numbered_title
from picard.version import Version

from picard.ui.theme import UiTheme


def _upgrade_hook_ok_1_2_3_dev_1(config):
    pass


def _upgrade_hook_not_ok_xxx(config):
    pass


def _upgrade_hook_tricky_1_2_3_alpha_1(config):
    pass


def _upgrade_hook_tricky_1_2_3_alpha1(config):
    pass


def _upgrade_hook_future_9999(config):
    pass


# WARNING: order of _upgrade_hook_sort_*() functions is important for tests


def _upgrade_hook_sort_2(config):
    pass


def _upgrade_hook_sort_1(config):
    pass


def _upgrade_hook_sort_2_0_0dev1(config):
    pass


class TestPicardConfigUpgradesAutodetect(PicardTestCase):
    def test_upgrade_hook_autodetect_ok(self):
        hooks = autodetect_upgrade_hooks(module_name=__name__, prefix='_upgrade_hook_ok_')
        expected_version = Version(major=1, minor=2, patch=3, identifier='dev', revision=1)
        self.assertIn(expected_version, hooks)
        self.assertEqual(hooks[expected_version], _upgrade_hook_ok_1_2_3_dev_1)
        self.assertEqual(len(hooks), 1)

    def test_upgrade_hook_autodetect_not_ok(self):
        with self.assertRaisesRegex(
            UpgradeHooksAutodetectError,
            r'^Failed to extract version from _upgrade_hook_not_ok_xxx',
        ):
            autodetect_upgrade_hooks(module_name=__name__, prefix='_upgrade_hook_not_ok_')

    def test_upgrade_hook_autodetect_tricky(self):
        with self.assertRaisesRegex(
            UpgradeHooksAutodetectError,
            r"^Conflicting functions for version 1\.2\.3\.alpha1",
        ):
            autodetect_upgrade_hooks(module_name=__name__, prefix='_upgrade_hook_tricky_')

    def test_upgrade_hook_autodetect_future(self):
        with self.assertRaisesRegex(
            UpgradeHooksAutodetectError,
            r"^Upgrade hook _upgrade_hook_future_9999 has version 9999\.0\.0\.final0 > Picard version",
        ):
            autodetect_upgrade_hooks(module_name=__name__, prefix='_upgrade_hook_future_')

    def test_upgrade_hook_autodetect_sort(self):
        hooks = autodetect_upgrade_hooks(module_name=__name__, prefix='_upgrade_hook_sort_')
        expected_keys = (
            Version(major=1, minor=0, patch=0, identifier='final', revision=0),
            Version(major=2, minor=0, patch=0, identifier='dev', revision=1),
            Version(major=2, minor=0, patch=0, identifier='final', revision=0),
        )
        self.assertEqual(tuple(hooks), expected_keys)


class TestPicardConfigUpgrades(TestPicardConfigCommon):
    def test_upgrade_to_v1_0_0final0_A(self):
        TextOption('setting', 'file_naming_format', '')

        self.config.setting['va_file_naming_format'] = 'abc'
        self.config.setting['use_va_format'] = True

        self.assertIn('va_file_naming_format', self.config.setting)
        self.assertIn('use_va_format', self.config.setting)

        upgrade_to_v1_0_0final0(self.config, interactive=False, merge=True)
        self.assertNotIn('va_file_naming_format', self.config.setting)
        self.assertNotIn('use_va_format', self.config.setting)
        self.assertIn('file_naming_format', self.config.setting)

    def test_upgrade_to_v1_0_0final0_B(self):
        TextOption('setting', 'file_naming_format', '')

        self.config.setting['va_file_naming_format'] = 'abc'
        self.config.setting['use_va_format'] = ""

        self.assertIn('va_file_naming_format', self.config.setting)
        self.assertIn('use_va_format', self.config.setting)

        upgrade_to_v1_0_0final0(self.config, interactive=False, merge=False)
        self.assertNotIn('va_file_naming_format', self.config.setting)
        self.assertNotIn('use_va_format', self.config.setting)
        self.assertNotIn('file_naming_format', self.config.setting)

    def test_upgrade_to_v1_3_0dev1(self):
        BoolOption('setting', 'windows_compatibility', False)

        self.config.setting['windows_compatible_filenames'] = True
        upgrade_to_v1_3_0dev1(self.config)
        self.assertNotIn('windows_compatible_filenames', self.config.setting)
        self.assertTrue(self.config.setting['windows_compatibility'])

    def test_upgrade_to_v1_3_0dev2(self):
        TextOption('setting', 'preserved_tags', '')
        self.config.setting['preserved_tags'] = "a b  c  "
        upgrade_to_v1_3_0dev2(self.config)
        self.assertEqual("a,b,c", self.config.setting['preserved_tags'])

    def test_upgrade_to_v1_3_0dev2_skip_list(self):
        ListOption('setting', 'preserved_tags', [])
        self.config.setting['preserved_tags'] = ['foo']
        upgrade_to_v1_3_0dev2(self.config)
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

        upgrade_to_v1_3_0dev3(self.config)
        self.assertEqual(["a", "b", "c"], self.config.setting['preferred_release_countries'])
        self.assertEqual(["a", "b", "c"], self.config.setting['preferred_release_formats'])
        self.assertEqual(["a", "b", "c"], self.config.setting['enabled_plugins'])
        self.assertEqual(["a", "b", "c"], self.config.setting['caa_image_types'])
        self.assertEqual(["a", "b", "c"], self.config.setting['metadata_box_sizes'])

    def test_upgrade_to_v3_0_0dev9(self):
        from PyQt6 import QtCore

        from picard.config import ListOption, Option
        from picard.config_upgrade import upgrade_to_v3_0_0dev9

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

        upgrade_to_v3_0_0dev9(self.config)

        # Verify options were removed
        self.assertNotIn('plugins_list_sort_order', self.config.persist)
        self.assertNotIn('plugins_list_sort_section', self.config.persist)
        self.assertNotIn('plugins_list_state', self.config.persist)
        self.assertNotIn('enabled_plugins', self.config.setting)

    def test_upgrade_to_v1_3_0dev4(self):
        ListOption("setting", "release_type_scores", [])

        self.config.setting['release_type_scores'] = "a 0.1 b 0.2 c 1"
        upgrade_to_v1_3_0dev4(self.config)

        self.assertEqual([('a', 0.1), ('b', 0.2), ('c', 1.0)], self.config.setting['release_type_scores'])

    def test_upgrade_to_v1_4_0dev2(self):
        self.config.setting['username'] = 'abc'
        self.config.setting['password'] = 'abc'  # nosec

        upgrade_to_v1_4_0dev2(self.config)
        self.assertNotIn('username', self.config.setting)
        self.assertNotIn('password', self.config.setting)

    def test_upgrade_to_v1_4_0dev3(self):
        ListOption("setting", "ca_providers", [])

        self.config.setting['ca_provider_use_amazon'] = True
        self.config.setting['ca_provider_use_caa'] = True
        self.config.setting['ca_provider_use_whitelist'] = False
        self.config.setting['ca_provider_use_caa_release_group_fallback'] = True

        upgrade_to_v1_4_0dev3(self.config)
        self.assertIn('ca_providers', self.config.setting)
        self.assertIn(('Amazon', True), self.config.setting['ca_providers'])
        self.assertIn(('Cover Art Archive', True), self.config.setting['ca_providers'])
        self.assertIn(('Whitelist', False), self.config.setting['ca_providers'])
        self.assertIn(('CaaReleaseGroup', True), self.config.setting['ca_providers'])
        self.assertEqual(len(self.config.setting['ca_providers']), 4)

    def test_upgrade_to_v1_4_0dev4(self):
        TextOption("setting", "file_naming_format", "")

        self.config.setting['file_naming_format'] = 'xxx'
        upgrade_to_v1_4_0dev4(self.config)
        self.assertEqual('xxx', self.config.setting['file_naming_format'])

        self.config.setting['file_naming_format'] = OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3
        upgrade_to_v1_4_0dev4(self.config)
        self.assertEqual(DEFAULT_FILE_NAMING_FORMAT, self.config.setting['file_naming_format'])

    def test_upgrade_to_v1_4_0dev6(self):
        BoolOption('setting', 'enable_tagger_scripts', False)
        ListOption('setting', 'list_of_scripts', [])

        self.config.setting['enable_tagger_script'] = True
        self.config.setting['tagger_script'] = "abc"
        upgrade_to_v1_4_0dev6(self.config)

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
        upgrade_to_v1_4_0dev7(self.config)
        self.assertNotIn('save_only_front_images_to_tags', self.config.setting)
        self.assertTrue(self.config.setting['embed_only_one_front_image'])

    def test_upgrade_to_v2_0_0dev3(self):
        IntOption("setting", "caa_image_size", 500)

        self.config.setting['caa_image_size'] = 0
        upgrade_to_v2_0_0dev3(self.config)
        self.assertEqual(250, self.config.setting['caa_image_size'])

        self.config.setting['caa_image_size'] = 501
        upgrade_to_v2_0_0dev3(self.config)
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

        upgrade_to_v2_1_0dev1(self.config)
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
        upgrade_to_v2_2_0dev3(self.config)
        self.assertNotIn('ignore_genres', self.config.setting)
        self.assertEqual(self.config.setting['genres_filter'], "-a\n-b\n-c")

    def test_upgrade_to_v2_2_0dev4(self):
        TextOption("setting", "file_naming_format", "")

        self.config.setting['file_naming_format'] = 'xxx'
        upgrade_to_v2_2_0dev4(self.config)
        self.assertEqual('xxx', self.config.setting['file_naming_format'])

        self.config.setting['file_naming_format'] = OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1
        upgrade_to_v2_2_0dev4(self.config)
        self.assertEqual(DEFAULT_FILE_NAMING_FORMAT, self.config.setting['file_naming_format'])

    def test_upgrade_to_v2_4_0beta3(self):
        ListOption("setting", "preserved_tags", [])
        self.config.setting['preserved_tags'] = 'foo,bar'
        upgrade_to_v2_4_0beta3(self.config)
        self.assertEqual(['foo', 'bar'], self.config.setting['preserved_tags'])

    def test_upgrade_to_v2_4_0beta3_already_done(self):
        ListOption("setting", "preserved_tags", [])
        self.config.setting['preserved_tags'] = ['foo', 'bar']
        upgrade_to_v2_4_0beta3(self.config)
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
        upgrade_to_v2_5_0dev1(self.config)
        self.assertEqual(expected, self.config.setting['ca_providers'])

    def test_upgrade_to_v2_5_0dev2(self):
        Option("persist", "splitter_state", QByteArray())
        Option("persist", "bottom_splitter_state", QByteArray())
        self.config.persist["splitter_state"] = b'foo'
        self.config.persist["bottom_splitter_state"] = b'bar'
        upgrade_to_v2_5_0dev2(self.config)
        self.assertEqual(b'', self.config.persist['splitter_state'])
        self.assertEqual(b'', self.config.persist['bottom_splitter_state'])

    def test_upgrade_to_v2_6_0dev1(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = "/usr/bin/fpcalc"
        upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("/usr/bin/fpcalc", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0dev1_empty(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = None
        upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0dev1_snap(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = "/snap/picard/221/usr/bin/fpcalc"
        upgrade_to_v2_6_0dev1(self.config)
        self.assertEqual("", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0dev1_frozen(self):
        TextOption("setting", "acoustid_fpcalc", "")
        self.config.setting["acoustid_fpcalc"] = r"C:\Program Files\MusicBrainz Picard\fpcalc.exe"
        picard.config_upgrade.IS_FROZEN = True
        upgrade_to_v2_6_0dev1(self.config)
        picard.config_upgrade.IS_FROZEN = False
        self.assertEqual("", self.config.setting["acoustid_fpcalc"])

    def test_upgrade_to_v2_6_0beta2(self):
        BoolOption('setting', 'image_type_as_filename', False)
        BoolOption('setting', 'save_only_one_front_image', False)

        self.config.setting['caa_image_type_as_filename'] = True
        self.config.setting['caa_save_single_front_image'] = True
        upgrade_to_v2_6_0beta2(self.config)
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
        upgrade_to_v2_6_0beta3(self.config)
        self.assertNotIn('use_system_theme', self.config.setting)
        self.assertIn('ui_theme', self.config.setting)
        self.assertEqual('system', self.config.setting['ui_theme'])

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
        upgrade_to_v2_7_0dev3(self.config)
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
        upgrade_to_v2_7_0dev4(self.config)
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
        upgrade_to_v2_7_0dev5(self.config)
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
        upgrade_to_v2_8_0dev2(self.config)
        self.assertEqual(expected, self.config.setting['toolbar_layout'])
        upgrade_to_v2_8_0dev2(self.config)
        self.assertEqual(expected, self.config.setting['toolbar_layout'])

    def test_upgrade_to_v3_0_0dev3(self):
        BoolOption('setting', 'allow_multi_dirs_selection', False)

        self.config.setting['toolbar_multiselect'] = True
        upgrade_to_v3_0_0dev3(self.config)
        self.assertNotIn('toolbar_multiselect', self.config.setting)
        self.assertTrue(self.config.setting['allow_multi_dirs_selection'])

    def test_upgrade_to_v3_0_0dev4(self):
        Option('persist', 'album_view_header_state', QByteArray())
        Option('persist', 'file_view_header_state', QByteArray())
        BoolOption('persist', 'album_view_header_locked', False)
        BoolOption('persist', 'file_view_header_locked', False)

        self.config.persist['album_view_header_state'] = b'foo'
        self.config.persist['file_view_header_state'] = b'bar'

        # test not locked, states shouldn't be modified
        upgrade_to_v3_0_0dev4(self.config)
        self.assertEqual(b'foo', self.config.persist['album_view_header_state'])
        self.assertEqual(b'bar', self.config.persist['file_view_header_state'])

        # test locked, states should be removed
        self.config.persist['album_view_header_locked'] = True
        self.config.persist['file_view_header_locked'] = True
        upgrade_to_v3_0_0dev4(self.config)
        self.assertEqual(b'', self.config.persist['album_view_header_state'])
        self.assertEqual(b'', self.config.persist['file_view_header_state'])

    def test_upgrade_to_v3_0_0dev5(self):
        TextOption('setting', 'replace_dir_separator', DEFAULT_REPLACEMENT)
        self.config.setting['replace_dir_separator'] = os.sep
        upgrade_to_v3_0_0dev5(self.config)
        self.assertEqual(DEFAULT_REPLACEMENT, self.config.setting['replace_dir_separator'])

        if os.altsep:
            self.config.setting['replace_dir_separator'] = os.altsep
            upgrade_to_v3_0_0dev5(self.config)
            self.assertEqual(DEFAULT_REPLACEMENT, self.config.setting['replace_dir_separator'])

    def test_upgrade_to_v3_0_0dev7(self):
        TextOption('setting', 'ui_theme', DEFAULT_THEME_NAME)
        self.config.setting['ui_theme'] = 'system'
        upgrade_to_v3_0_0dev7(self.config)
        self.assertEqual(DEFAULT_THEME_NAME, self.config.setting['ui_theme'])

    def test_upgrade_to_v3_0_0dev8(self):
        BoolOption('setting', 'enable_tag_saving', True)
        self.config.setting['dont_write_tags'] = True
        upgrade_to_v3_0_0dev8(self.config)
        self.assertNotIn('dont_write_tags', self.config.setting)
        self.assertFalse(self.config.setting['enable_tag_saving'])
