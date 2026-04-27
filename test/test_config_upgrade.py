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

from test.picardtestcase import PicardTestCase

from picard.config_upgrade import (
    UpgradeHooksAutodetectError,
    autodetect_upgrade_hooks,
)
from picard.version import Version


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
