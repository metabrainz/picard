# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021 Laurent Monin
# Copyright (C) 2020 Philipp Wolfer
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


from test.picardtestcase import PicardTestCase

from picard import config
from picard.util.settingsoverride import SettingsOverride


class SettingsOverrideTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values({'key1': 'origval1', 'key2': 'origval2'})
        self.new_settings = {'key1': 'newval2'}

    def test_read_orig_settings(self):
        override = SettingsOverride(config.setting, self.new_settings)
        self.assertEqual(override['key1'], 'newval2')
        self.assertEqual(override['key2'], 'origval2')
        with self.assertRaises(KeyError):
            x = override['key3']  # noqa: F841

    def test_read_orig_settings_kw(self):
        override = SettingsOverride(config.setting, key1='newval2')
        self.assertEqual(override['key1'], 'newval2')
        self.assertEqual(override['key2'], 'origval2')

    def test_write_orig_settings(self):
        override = SettingsOverride(config.setting, self.new_settings)
        override['key1'] = 'newval3'
        self.assertEqual(override['key1'], 'newval3')
        self.assertEqual(config.setting['key1'], 'origval1')

        override['key2'] = 'newval4'
        self.assertEqual(override['key2'], 'newval4')
        self.assertEqual(config.setting['key2'], 'origval2')

        override['key3'] = 'newval5'
        self.assertEqual(override['key3'], 'newval5')
        with self.assertRaises(KeyError):
            x = config.setting['key3']  # noqa: F841

    def test_del_orig_settings(self):
        override = SettingsOverride(config.setting, self.new_settings)

        override['key1'] = 'newval3'
        self.assertEqual(override['key1'], 'newval3')
        del override['key1']
        self.assertEqual(override['key1'], 'origval1')

        self.assertEqual(override['key2'], 'origval2')
        del override['key2']
        self.assertEqual(override['key2'], 'origval2')
