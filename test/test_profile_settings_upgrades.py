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

from test.picardtestcase import PicardTestCase

from picard.profile_settings_upgrades import (
    _SETTINGS_UPGRADES,
    _register,
    upgrade_settings_for_import,
)


class TestProfileSettingsUpgrades(PicardTestCase):
    def setUp(self):
        super().setUp()
        # Save original registry and restore after test
        self._original_upgrades = _SETTINGS_UPGRADES.copy()

    def tearDown(self):
        _SETTINGS_UPGRADES.clear()
        _SETTINGS_UPGRADES.extend(self._original_upgrades)
        super().tearDown()

    def test_no_upgrades_for_current_version(self):
        """No upgrades applied when version is higher than all registered."""
        settings = {'rename_files': True}
        applied = upgrade_settings_for_import(settings, '99.0.0')
        self.assertEqual(applied, [])
        self.assertEqual(settings, {'rename_files': True})

    def test_invalid_version_string(self):
        """Invalid version string should not crash, returns empty list."""
        settings = {'rename_files': True}
        applied = upgrade_settings_for_import(settings, 'not-a-version')
        self.assertEqual(applied, [])

    def test_register_and_apply(self):
        """Test that @_register decorator works and upgrades are applied."""

        @_register('4.0.0')
        def _upgrade_4_0_0(settings: dict) -> None:
            """Rename foo to bar."""
            if 'foo' in settings:
                settings['bar'] = settings.pop('foo')

        settings = {'foo': 'value'}
        applied = upgrade_settings_for_import(settings, '3.0.0')

        self.assertNotIn('foo', settings)
        self.assertEqual(settings['bar'], 'value')
        self.assertEqual(applied, ['Rename foo to bar.'])

    def test_upgrade_not_applied_for_newer_version(self):
        """Upgrade should not apply if profile version is newer."""

        @_register('4.0.0')
        def _upgrade_4_0_0(settings: dict) -> None:
            """Rename foo to bar."""
            if 'foo' in settings:
                settings['bar'] = settings.pop('foo')

        settings = {'foo': 'value'}
        applied = upgrade_settings_for_import(settings, '5.0.0')

        self.assertIn('foo', settings)
        self.assertNotIn('bar', settings)
        self.assertEqual(applied, [])

    def test_multiple_upgrades_applied_in_order(self):
        """Multiple upgrades should apply in version order."""

        @_register('4.0.0')
        def _upgrade_4_0_0(settings: dict) -> None:
            """Step 1."""
            settings['step1'] = True

        @_register('4.1.0')
        def _upgrade_4_1_0(settings: dict) -> None:
            """Step 2."""
            settings['step2'] = True

        settings = {}
        applied = upgrade_settings_for_import(settings, '3.0.0')

        self.assertTrue(settings['step1'])
        self.assertTrue(settings['step2'])
        self.assertEqual(applied, ['Step 1.', 'Step 2.'])

    def test_registry_sorted_regardless_of_registration_order(self):
        """Upgrades registered out of order should still apply in version order."""

        @_register('5.0.0')
        def _upgrade_5(settings: dict) -> None:
            """Second."""
            settings['order'] = settings.get('order', []) + ['5.0.0']

        @_register('4.0.0')
        def _upgrade_4(settings: dict) -> None:
            """First."""
            settings['order'] = settings.get('order', []) + ['4.0.0']

        settings = {}
        upgrade_settings_for_import(settings, '3.0.0')

        self.assertEqual(settings['order'], ['4.0.0', '5.0.0'])
