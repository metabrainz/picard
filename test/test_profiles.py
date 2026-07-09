# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021, 2023, 2025 Bob Swift
# Copyright (C) 2022 Philipp Wolfer
# Copyright (C) 2024 Laurent Monin
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


from enum import Enum
import logging
import os
import shutil

from test.picardtestcase import PicardTestCase

from picard.config import (
    BoolOption,
    Config,
    IntOption,
    ListOption,
    Option,
    SettingConfigSection,
    TextOption,
)
from picard.profile import (
    profile_groups_add_setting,
    profile_groups_all_settings,
    profile_groups_keys,
    profile_groups_order,
    profile_groups_remove_group,
    profile_groups_reset,
    profile_groups_settings,
    profile_groups_update_highlights,
    profile_groups_values,
)


class DummyEnum(Enum):
    A = "a"
    B = "b"
    C = "c"


class TestPicardProfilesCommon(PicardTestCase):
    PROFILES_KEY = SettingConfigSection.PROFILES_KEY
    SETTINGS_KEY = SettingConfigSection.SETTINGS_KEY

    def setUp(self):
        super().setUp()

        self.tmp_directory = self.mktmpdir()

        self.configpath = os.path.join(self.tmp_directory, 'test.ini')
        shutil.copy(os.path.join('test', 'data', 'test.ini'), self.configpath)
        self.addCleanup(os.remove, self.configpath)

        self.config = Config.from_file(None, self.configpath)
        self.addCleanup(self.cleanup_config_obj)

        self.config.application["version"] = "testing"
        self.original_logging_disable = logging.root.manager.disable
        logging.disable(logging.ERROR)
        self.old_registry = dict(Option.registry)
        Option.registry = {}

        ListOption('profiles', self.PROFILES_KEY, [])
        Option('profiles', self.SETTINGS_KEY, {})

        # Get valid profile option settings for testing
        profile_groups_reset()
        for n in range(0, 5):
            group = 'group%d' % (n % 2)
            title = 'title_' + group
            name = 'opt%d' % n
            highlights = tuple('obj%d' % i for i in range(0, n))
            profile_groups_add_setting(group, name, highlights, title=title)
        option_settings = list(profile_groups_all_settings())
        self.test_setting_0 = option_settings[0]
        self.test_setting_1 = option_settings[1]
        self.test_setting_2 = option_settings[2]
        self.test_setting_3 = option_settings[3]
        self.test_setting_4 = option_settings[4]

        TextOption("setting", self.test_setting_0, "abc", in_profile=True)
        BoolOption("setting", self.test_setting_1, True, in_profile=True)
        IntOption("setting", self.test_setting_2, 42, in_profile=True)
        TextOption("setting", self.test_setting_3, "xyz", in_profile=True)
        Option("setting", self.test_setting_4, DummyEnum.B, in_profile=True)

    def tearDown(self):
        Option.registry = self.old_registry
        logging.disable(self.original_logging_disable)

    def cleanup_config_obj(self):
        # Ensure QSettings do not recreate the file on exit
        self.config.sync()
        del self.config
        self.config = None

    def get_profiles(self, enabled=True):
        profiles = []
        for i in range(4):
            profiles.append(
                {
                    "position": i,
                    "title": "Test Profile {}".format(i),
                    "enabled": enabled,
                    "id": "test_key_{}".format(i),
                }
            )
        return profiles


class TestUserProfileGroups(TestPicardProfilesCommon):
    def test_has_groups(self):
        groups = list(profile_groups_keys())
        self.assertEqual(groups, ['group0', 'group1'])

    def test_groups_have_items(self):
        for group in profile_groups_keys():
            settings = profile_groups_settings(group)
            self.assertNotEqual(settings, {})

    def test_no_duplicate_settings(self):
        count1 = 0
        for group in profile_groups_keys():
            settings = profile_groups_settings(group)
            count1 += len(list(settings))
        count2 = len(list(profile_groups_all_settings()))
        self.assertEqual(count1, count2)

    def test_settings_have_no_blank_keys(self):
        for group in profile_groups_keys():
            settings = profile_groups_settings(group)
            for setting in settings:
                self.assertNotEqual(setting.name.strip(), "")

    def test_groups_have_title(self):
        for value in profile_groups_values():
            self.assertTrue(value['title'].startswith('title_'))

    def test_groups_have_highlights(self):
        for group in profile_groups_keys():
            for setting in profile_groups_settings(group):
                self.assertIsNotNone(setting.highlights)

    def test_order(self):
        result_before = [value['title'] for value in profile_groups_values()]
        self.assertEqual(result_before, ['title_group0', 'title_group1'])

        profile_groups_order('group1')
        profile_groups_order('group0')

        result_after = [value['title'] for value in profile_groups_values()]
        self.assertEqual(result_after, ['title_group1', 'title_group0'])

    def test_remove_group(self):
        self.assertIn('opt0', profile_groups_all_settings())
        profile_groups_remove_group('group0')
        # opt0 and opt2 were in group0
        self.assertNotIn('opt0', profile_groups_all_settings())
        self.assertNotIn('opt2', profile_groups_all_settings())
        # opt1 and opt3 should remain (they're in group1)
        self.assertIn('opt1', profile_groups_all_settings())
        self.assertIn('opt3', profile_groups_all_settings())

    def test_remove_group_preserves_shared_names(self):
        # Add same option name to two groups
        profile_groups_add_setting('extra_group', 'opt0', (), title='Extra')
        profile_groups_remove_group('extra_group')
        # opt0 should still be in _known_settings because group0 still has it
        self.assertIn('opt0', profile_groups_all_settings())

    def test_update_highlights(self):
        profile_groups_add_setting('group1', 'opt1', ('old_widget',), section='section2')
        # Update highlights for opt1 in section 'section2'
        profile_groups_update_highlights('section2', 'opt1', ('new_widget',))
        settings = list(profile_groups_settings('group1'))
        opt1_updated = next(s for s in settings if s.name == 'opt1' and s.section == 'section2')
        self.assertEqual(opt1_updated.highlights, ('new_widget',))
        opt1_unchanged = next(s for s in settings if s.name == 'opt1' and s.section == 'setting')
        self.assertEqual(opt1_unchanged.highlights, ('obj0',))


class TestUserProfiles(TestPicardProfilesCommon):
    def test_settings(self):
        self.config.setting[self.test_setting_0] = "abc"
        self.config.setting[self.test_setting_1] = True
        self.config.setting[self.test_setting_2] = 42
        self.config.setting[self.test_setting_4] = DummyEnum.A
        settings = {
            "test_key_0": {self.test_setting_0: None},
            "test_key_1": {self.test_setting_1: None},
            "test_key_2": {self.test_setting_2: None},
            "test_key_3": {self.test_setting_4: None},
        }
        self.config.profiles[self.SETTINGS_KEY] = settings
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=True)

        # Stack:
        #                   setting_0  setting_1  setting_2  setting_4
        #                   ---------  ---------  ---------  ---------
        # test_key_0:       None       n/a        n/a        n/a
        # test_key_1:       n/a        None       n/a        n/a
        # test_key_2:       n/a        n/a        None       n/a
        # test_key_2:       n/a        n/a        n/a        None
        # user_settings:    abc        True       42         A

        # Test retrieval with overrides at None
        self.assertEqual(self.config.setting[self.test_setting_0], "abc")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 42)
        self.assertEqual(self.config.setting[self.test_setting_4], DummyEnum.A)

        # Test setting new values
        self.config.setting[self.test_setting_0] = "def"
        self.config.setting[self.test_setting_1] = False
        self.config.setting[self.test_setting_2] = 99
        self.config.setting[self.test_setting_4] = DummyEnum.B

        # Stack:
        #                   setting_0  setting_1  setting_2  setting_4
        #                   ---------  ---------  ---------  ---------
        # test_key_0:       def        n/a        n/a        n/a
        # test_key_1:       n/a        False      n/a        n/a
        # test_key_2:       n/a        n/a        99         n/a
        # test_key_2:       n/a        n/a        n/a        B
        # user_settings:    abc        True       42         A

        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)
        self.assertEqual(self.config.setting[self.test_setting_4], DummyEnum.B)

        # Test retrieval with profiles disabled
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=False)
        self.assertEqual(self.config.setting[self.test_setting_0], "abc")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 42)
        self.assertEqual(self.config.setting[self.test_setting_4], DummyEnum.A)

        # Test setting new values with profiles disabled
        self.config.setting[self.test_setting_0] = "ghi"
        self.config.setting[self.test_setting_1] = True
        self.config.setting[self.test_setting_2] = 86
        self.config.setting[self.test_setting_4] = DummyEnum.C

        # Stack:
        #                   setting_0  setting_1  setting_2  setting_4
        #                   ---------  ---------  ---------  ---------
        # test_key_0:       def        n/a        n/a        n/a
        # test_key_1:       n/a        False      n/a        n/a
        # test_key_2:       n/a        n/a        99         n/a
        # test_key_2:       n/a        n/a        n/a        B
        # user_settings:    ghi        True       86         C

        self.assertEqual(self.config.setting[self.test_setting_0], "ghi")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 86)
        self.assertEqual(self.config.setting[self.test_setting_4], DummyEnum.C)

        # Re-enable profiles and check that the saved settings still exist
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=True)
        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)
        self.assertEqual(self.config.setting[self.test_setting_4], DummyEnum.B)

    def test_settings_with_overrides(self):
        self.config.setting[self.test_setting_0] = "abc"
        self.config.setting[self.test_setting_1] = True
        self.config.setting[self.test_setting_2] = 42
        settings = {
            "test_key_0": {self.test_setting_0: None},
            "test_key_1": {self.test_setting_1: None},
            "test_key_2": {self.test_setting_2: None},
        }
        self.config.profiles[self.SETTINGS_KEY] = settings
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=False)
        self.config.setting.set_profiles_override(self.get_profiles(enabled=True))

        # Stack:
        #                   setting_0   setting_1   setting_2
        #                   ---------   ---------   ---------
        # test_key_0:       None        n/a         n/a
        # test_key_1:       n/a         None        n/a
        # test_key_2:       n/a         n/a         None
        # user_settings:    abc         True        42

        # Test retrieval with overrides at None
        self.assertEqual(self.config.setting[self.test_setting_0], "abc")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 42)

        # Test setting new values
        self.config.setting[self.test_setting_0] = "def"
        self.config.setting[self.test_setting_1] = False
        self.config.setting[self.test_setting_2] = 99

        # Stack:
        #                   setting_0   setting_1   setting_2
        #                   ---------   ---------   ---------
        # test_key_0:       def         n/a         n/a
        # test_key_1:       n/a         False       n/a
        # test_key_2:       n/a         n/a         99
        # user_settings:    abc         True        42

        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)

        # Test retrieval with profile overrides disabled
        self.config.setting.set_profiles_override()
        self.assertEqual(self.config.setting[self.test_setting_0], "abc")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 42)

        # Test retrieval with empty settings overrides
        self.config.setting.set_profiles_override(self.get_profiles(enabled=True))
        empty_settings = {
            "test_key_0": {},
            "test_key_1": {},
            "test_key_2": {},
        }
        self.config.setting.set_settings_override(empty_settings)
        self.assertEqual(self.config.setting[self.test_setting_0], "abc")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 42)

        # Test retrieval with settings overrides disabled
        self.config.setting.set_settings_override()
        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)

        # Test setting new values with profiles override disabled
        self.config.setting.set_profiles_override()
        self.config.setting[self.test_setting_0] = "ghi"
        self.config.setting[self.test_setting_1] = True
        self.config.setting[self.test_setting_2] = 86

        # Stack:
        #                   setting_0   setting_1   setting_2
        #                   ---------   ---------   ---------
        # test_key_0:       def         n/a         n/a
        # test_key_1:       n/a         False       n/a
        # test_key_2:       n/a         n/a         99
        # user_settings:    ghi         True        86

        self.assertEqual(self.config.setting[self.test_setting_0], "ghi")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 86)

        # Re-enable profile overrides and check that the saved settings still exist
        self.config.setting.set_profiles_override(self.get_profiles(enabled=True))
        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)

        # Re-enable profile overrides and check that the saved settings still exist
        # with invalid profile id in profile list
        profiles = [
            {
                "position": 4,
                "title": "Test Profile 4",
                "enabled": True,
                "id": "test_key_4",
            }
        ]
        profiles.extend(self.get_profiles(enabled=True))
        self.config.setting.set_profiles_override(profiles)
        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)

    def test_config_option_rename(self):
        from picard.config_upgrade import rename_option_in_settings

        self.config.setting[self.test_setting_0] = "abc"
        self.config.setting[self.test_setting_1] = True
        self.config.setting[self.test_setting_2] = 42
        settings = {
            "test_key_0": {self.test_setting_0: None},
            "test_key_1": {self.test_setting_1: None},
            "test_key_2": {self.test_setting_2: None},
        }
        self.config.profiles[self.SETTINGS_KEY] = settings
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=True)
        self.config.setting[self.test_setting_0] = "def"

        # Rename in base config
        rename_option_in_settings(self.config.setting, self.test_setting_0, self.test_setting_3, TextOption, "")
        # Rename in all profile override dicts
        for profile_settings in self.config.profiles[self.SETTINGS_KEY].values():
            rename_option_in_settings(profile_settings, self.test_setting_0, self.test_setting_3)

        self.assertEqual(self.config.setting[self.test_setting_3], "def")
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=False)
        self.assertEqual(self.config.setting[self.test_setting_3], "abc")

    def test_no_profile_context_manager(self):
        self.config.setting[self.test_setting_0] = "abc"
        settings = {
            "test_key_0": {self.test_setting_0: "profile_value"},
            "test_key_1": {},
            "test_key_2": {},
        }
        self.config.profiles[self.SETTINGS_KEY] = settings
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=True)

        # With profiles active, profile value is returned
        self.assertEqual(self.config.setting[self.test_setting_0], "profile_value")

        # Inside no_profile(), base setting is returned
        with self.config.setting.no_profile():
            self.assertEqual(self.config.setting[self.test_setting_0], "abc")

        # After exiting, profile value is returned again
        self.assertEqual(self.config.setting[self.test_setting_0], "profile_value")

    def test_no_profile_restores_existing_overrides(self):
        self.config.setting[self.test_setting_0] = "abc"
        settings = {
            "test_key_0": {self.test_setting_0: "profile_value"},
            "test_key_1": {},
            "test_key_2": {},
        }
        self.config.profiles[self.SETTINGS_KEY] = settings
        override_profiles = self.get_profiles(enabled=True)
        override_settings = {
            "test_key_0": {self.test_setting_0: "override_value"},
            "test_key_1": {},
            "test_key_2": {},
        }
        self.config.setting.set_profiles_override(override_profiles)
        self.config.setting.set_settings_override(override_settings)

        # With overrides active
        self.assertEqual(self.config.setting[self.test_setting_0], "override_value")

        with self.config.setting.no_profile():
            self.assertEqual(self.config.setting[self.test_setting_0], "abc")

        # Overrides restored after context manager exits
        self.assertEqual(self.config.setting[self.test_setting_0], "override_value")
        self.assertIs(self.config.setting.profiles_override, override_profiles)
        self.assertIs(self.config.setting.settings_override, override_settings)

    def test_no_profile_restores_on_exception(self):
        override_profiles = self.get_profiles(enabled=True)
        self.config.setting.set_profiles_override(override_profiles)

        with self.assertRaises(ValueError):
            with self.config.setting.no_profile():
                raise ValueError("test error")

        # Overrides restored even after exception
        self.assertIs(self.config.setting.profiles_override, override_profiles)

    def test_clean_profile_settings(self):
        from picard.ui.options.profiles import ProfilesOptionsPage

        # test_setting_0 has in_profile=True (from setUp)
        # Create an option without in_profile
        TextOption('setting', 'stale_option', 'default')

        # Simulate profile_settings with valid, stale, and plugin keys
        page = ProfilesOptionsPage.__new__(ProfilesOptionsPage)
        page.profile_settings = {
            'p1': {
                self.test_setting_0: 'value1',  # valid (in_profile=True)
                'stale_option': 'stale_value',  # invalid (in_profile=False)
                'nonexistent_option': 'gone',  # option doesn't exist
                'plugin.some-uuid/greeting': 'hello',  # plugin key — always kept
            }
        }

        cleaned = page._clean_profile_settings()
        self.assertIn(self.test_setting_0, cleaned['p1'])
        self.assertNotIn('stale_option', cleaned['p1'])
        self.assertNotIn('nonexistent_option', cleaned['p1'])
        self.assertIn('plugin.some-uuid/greeting', cleaned['p1'])

    def test_clean_plugin_profile_settings(self):
        from picard.plugin3.manager.clean import PluginCleanupManager

        # Set up profile settings with plugin and core keys
        self.config.profiles[self.SETTINGS_KEY] = {
            'p1': {
                'move_files': True,
                'plugin.test-uuid/greeting': 'hello',
                'plugin.test-uuid/other': 'world',
                'plugin.other-uuid/opt': 'keep',
            }
        }

        cleanup = PluginCleanupManager(None)
        cleanup._clean_plugin_profile_settings(self.config, 'test-uuid')

        settings = self.config.profiles[self.SETTINGS_KEY]
        # Core keys and other plugin keys preserved
        self.assertIn('move_files', settings['p1'])
        self.assertIn('plugin.other-uuid/opt', settings['p1'])
        # Target plugin keys removed
        self.assertNotIn('plugin.test-uuid/greeting', settings['p1'])
        self.assertNotIn('plugin.test-uuid/other', settings['p1'])
