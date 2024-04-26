# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2022 Philipp Wolfer
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
from picard.profile import UserProfileGroups


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
        logging.disable(logging.ERROR)
        Option.registry = {}

        ListOption('profiles', self.PROFILES_KEY, [])
        Option('profiles', self.SETTINGS_KEY, {})

        # Get valid profile option settings for testing
        UserProfileGroups.reset()
        for n in range(0, 4):
            group = 'group%d' % (n % 2)
            title = 'title_' + group
            name = 'opt%d' % n
            highlights = ('obj%d' % i for i in range(0, n))
            UserProfileGroups.append_to_group(group, name, highlights, title=title)
        option_settings = list(UserProfileGroups.all_settings())
        self.test_setting_0 = option_settings[0]
        self.test_setting_1 = option_settings[1]
        self.test_setting_2 = option_settings[2]
        self.test_setting_3 = option_settings[3]

        TextOption("setting", self.test_setting_0, "abc")
        BoolOption("setting", self.test_setting_1, True)
        IntOption("setting", self.test_setting_2, 42)
        TextOption("setting", self.test_setting_3, "xyz")

    def cleanup_config_obj(self):
        # Ensure QSettings do not recreate the file on exit
        self.config.sync()
        del self.config
        self.config = None

    def get_profiles(self, enabled=True):
        profiles = []
        for i in range(3):
            profiles.append(
                {
                    "position": i,
                    "title": "Test Profile {0}".format(i),
                    "enabled": enabled,
                    "id": "test_key_{0}".format(i),
                }
            )
        return profiles


class TestUserProfileGroups(TestPicardProfilesCommon):

    def test_has_groups(self):
        groups = list(UserProfileGroups.keys())
        self.assertEqual(groups, ['group0', 'group1'])

    def test_groups_have_items(self):
        for group in UserProfileGroups.keys():
            settings = UserProfileGroups.settings(group)
            self.assertNotEqual(settings, {})

    def test_no_duplicate_settings(self):
        count1 = 0
        for group in UserProfileGroups.keys():
            settings = UserProfileGroups.settings(group)
            count1 += len(list(settings))
        count2 = len(list(UserProfileGroups.all_settings()))
        self.assertEqual(count1, count2)

    def test_settings_have_no_blank_keys(self):
        for group in UserProfileGroups.keys():
            settings = UserProfileGroups.settings(group)
            for name, highlights in settings:
                self.assertNotEqual(name.strip(), "")

    def test_groups_have_title(self):
        for value in UserProfileGroups.values():
            self.assertTrue(value['title'].startswith('title_'))

    def test_groups_have_highlights(self):
        for group in UserProfileGroups.keys():
            for setting in UserProfileGroups.settings(group):
                self.assertIsNotNone(setting.highlights)

    def test_order(self):
        result_before = [value['title'] for value in UserProfileGroups.values()]
        self.assertEqual(
            result_before,
            ['title_group0', 'title_group1']
        )

        UserProfileGroups.order('group1')
        UserProfileGroups.order('group0')

        result_after = [value['title'] for value in UserProfileGroups.values()]
        self.assertEqual(
            result_after,
            ['title_group1', 'title_group0']
        )


class TestUserProfiles(TestPicardProfilesCommon):

    def test_settings(self):
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

        # Test retrieval with profiles disabled
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=False)
        self.assertEqual(self.config.setting[self.test_setting_0], "abc")
        self.assertEqual(self.config.setting[self.test_setting_1], True)
        self.assertEqual(self.config.setting[self.test_setting_2], 42)

        # Test setting new values with profiles disabled
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

        # Re-enable profiles and check that the saved settings still exist
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=True)
        self.assertEqual(self.config.setting[self.test_setting_0], "def")
        self.assertEqual(self.config.setting[self.test_setting_1], False)
        self.assertEqual(self.config.setting[self.test_setting_2], 99)

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
        from picard.config_upgrade import rename_option
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
        rename_option(self.config, self.test_setting_0, self.test_setting_3, TextOption, "")
        self.assertEqual(self.config.setting[self.test_setting_3], "def")
        self.config.profiles[self.PROFILES_KEY] = self.get_profiles(enabled=False)
        self.assertEqual(self.config.setting[self.test_setting_3], "abc")
