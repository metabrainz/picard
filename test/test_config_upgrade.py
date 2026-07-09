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


class TestRenameOptionInSettingsPolymorphic(PicardTestCase):
    """Tests for the new polymorphic rename_option (dict path)."""

    def test_rename_existing_key(self):
        from picard.config_upgrade import rename_option

        settings = {'old_name': 'value', 'other': 42}
        rename_option(settings, 'old_name', 'new_name')
        self.assertEqual({'new_name': 'value', 'other': 42}, settings)

    def test_rename_with_reverse(self):
        from picard.config_upgrade import rename_option

        settings = {'old_name': True}
        rename_option(settings, 'old_name', 'new_name', reverse=True)
        self.assertEqual({'new_name': False}, settings)

    def test_rename_missing_key(self):
        from picard.config_upgrade import rename_option

        settings = {'other': 'value'}
        rename_option(settings, 'old_name', 'new_name')
        self.assertEqual({'other': 'value'}, settings)

    def test_rename_none_value(self):
        from picard.config_upgrade import rename_option

        settings = {'old_name': None}
        rename_option(settings, 'old_name', 'new_name')
        self.assertEqual({'new_name': None}, settings)

    def test_rename_none_value_reverse(self):
        from picard.config_upgrade import rename_option

        settings = {'old_name': None}
        rename_option(settings, 'old_name', 'new_name', reverse=True)
        self.assertEqual({'new_name': None}, settings)


class TestUpgradeOptionValueInSettingsPolymorphic(PicardTestCase):
    """Tests for the new polymorphic upgrade_option_value (dict path)."""

    def test_transform_existing_key(self):
        from picard.config_upgrade import upgrade_option_value

        settings = {'my_opt': 'HELLO', 'other': 42}
        upgrade_option_value(settings, 'my_opt', str.lower)
        self.assertEqual({'my_opt': 'hello', 'other': 42}, settings)

    def test_transform_missing_key(self):
        from picard.config_upgrade import upgrade_option_value

        settings = {'other': 42}
        upgrade_option_value(settings, 'my_opt', str.lower)
        self.assertEqual({'other': 42}, settings)

    def test_transform_none_value_unchanged(self):
        from picard.config_upgrade import upgrade_option_value

        settings = {'my_opt': None}
        upgrade_option_value(settings, 'my_opt', str.lower)
        self.assertEqual({'my_opt': None}, settings)

    def test_transform_list(self):
        from picard.config_upgrade import upgrade_option_value

        settings = {'items': [('Whitelist', True), ('Other', False)]}
        upgrade_option_value(
            settings,
            'items',
            lambda providers: [('UrlRelationships' if n == 'Whitelist' else n, s) for n, s in providers],
        )
        self.assertEqual({'items': [('UrlRelationships', True), ('Other', False)]}, settings)


class TestUpgradeSettingsDecorator(PicardTestCase):
    """Tests for the @upgrade_settings decorator and registry."""

    def test_decorator_registers_function(self):
        from picard.config_upgrade import (
            _UPGRADES_REGISTRY,
            _UpgradeType,
            upgrade_settings,
        )
        from picard.version import Version

        original_len = len(_UPGRADES_REGISTRY)

        @upgrade_settings('99.0.0dev1')
        def _test_upgrade(settings):
            """Test upgrade."""
            pass

        self.assertEqual(len(_UPGRADES_REGISTRY), original_len + 1)
        version, utype, func = _UPGRADES_REGISTRY[-1]
        self.assertEqual(version, Version(99, 0, 0, 'dev', 1))
        self.assertEqual(utype, _UpgradeType.SETTINGS)
        self.assertEqual(func, _test_upgrade)

        # Clean up
        _UPGRADES_REGISTRY.pop()

    def test_multiple_decorators_same_version(self):
        from picard.config_upgrade import (
            _UPGRADES_REGISTRY,
            upgrade_settings,
        )

        original_len = len(_UPGRADES_REGISTRY)

        @upgrade_settings('99.0.0dev2')
        def _test_upgrade_a(settings):
            pass

        @upgrade_settings('99.0.0dev2')
        def _test_upgrade_b(settings):
            pass

        self.assertEqual(len(_UPGRADES_REGISTRY), original_len + 2)

        # Clean up
        _UPGRADES_REGISTRY.pop()
        _UPGRADES_REGISTRY.pop()


class TestUpgradeConfigDecorator(PicardTestCase):
    """Tests for the @upgrade_config decorator and registry."""

    def test_decorator_registers_function(self):
        from picard.config_upgrade import (
            _UPGRADES_REGISTRY,
            _UpgradeType,
            upgrade_config,
        )
        from picard.version import Version

        original_len = len(_UPGRADES_REGISTRY)

        @upgrade_config('99.0.0dev1')
        def _test_config_hook(config):
            """Test config hook."""
            pass

        self.assertEqual(len(_UPGRADES_REGISTRY), original_len + 1)
        version, utype, func = _UPGRADES_REGISTRY[-1]
        self.assertEqual(version, Version(99, 0, 0, 'dev', 1))
        self.assertEqual(utype, _UpgradeType.CONFIG)
        self.assertEqual(func, _test_config_hook)

        # Clean up
        _UPGRADES_REGISTRY.pop()


class TestApplySettingsUpgradesForImport(PicardTestCase):
    """Tests for apply_settings_upgrades_for_import."""

    def test_applies_upgrades_after_version(self):
        from picard.config_upgrade import apply_settings_upgrades_for_import

        # toolbar_multiselect was renamed at 3.0.0dev3
        settings = {'toolbar_multiselect': True}
        descriptions = apply_settings_upgrades_for_import(settings, '3.0.0dev2')
        self.assertNotIn('toolbar_multiselect', settings)
        self.assertTrue(settings['allow_multi_dirs_selection'])
        self.assertTrue(len(descriptions) > 0)

    def test_skips_upgrades_at_or_before_version(self):
        from picard.config_upgrade import apply_settings_upgrades_for_import

        # If from_version >= the upgrade version, it should not apply
        settings = {'toolbar_multiselect': True}
        apply_settings_upgrades_for_import(settings, '3.0.0dev3')
        # Should NOT be renamed — upgrade is for versions < 3.0.0dev3
        self.assertIn('toolbar_multiselect', settings)
        self.assertNotIn('allow_multi_dirs_selection', settings)

    def test_invalid_version_returns_empty(self):
        from picard.config_upgrade import apply_settings_upgrades_for_import

        settings = {'toolbar_multiselect': True}
        descriptions = apply_settings_upgrades_for_import(settings, 'not_a_version')
        self.assertEqual(descriptions, [])
        # Settings unchanged
        self.assertIn('toolbar_multiselect', settings)

    def test_no_matching_keys_is_noop(self):
        from picard.config_upgrade import apply_settings_upgrades_for_import

        settings = {'some_other_option': 'value'}
        apply_settings_upgrades_for_import(settings, '3.0.0dev2')
        self.assertEqual(settings, {'some_other_option': 'value'})


class TestGetSortedUpgrades(PicardTestCase):
    """Tests for _get_sorted_upgrades."""

    def test_sorts_by_version(self):
        from picard.config_upgrade import (
            _get_sorted_upgrades,
            _UpgradeEntry,
            _UpgradeType,
        )
        from picard.version import Version

        v1 = Version(3, 0, 0, 'dev', 3)
        v2 = Version(2, 0, 0, 'final', 0)
        v3 = Version(3, 0, 0, 'dev', 1)
        S = _UpgradeType.SETTINGS

        def f1(s):
            pass

        def f2(s):
            pass

        def f3(s):
            pass

        registry = [_UpgradeEntry(v1, S, f1), _UpgradeEntry(v2, S, f2), _UpgradeEntry(v3, S, f3)]
        result = _get_sorted_upgrades(registry)
        self.assertEqual(result[0], _UpgradeEntry(v2, S, f2))
        self.assertEqual(result[1], _UpgradeEntry(v3, S, f3))
        self.assertEqual(result[2], _UpgradeEntry(v1, S, f1))

    def test_preserves_order_within_same_version(self):
        from picard.config_upgrade import (
            _get_sorted_upgrades,
            _UpgradeEntry,
            _UpgradeType,
        )
        from picard.version import Version

        v = Version(3, 0, 0, 'dev', 3)
        S = _UpgradeType.SETTINGS
        C = _UpgradeType.CONFIG

        def f1(s):
            pass

        def f2(s):
            pass

        registry = [_UpgradeEntry(v, S, f1), _UpgradeEntry(v, C, f2)]
        result = _get_sorted_upgrades(registry)
        self.assertEqual(result[0], _UpgradeEntry(v, S, f1))
        self.assertEqual(result[1], _UpgradeEntry(v, C, f2))


class TestGetOption(PicardTestCase):
    """Tests for the polymorphic get_option (dict path)."""

    def test_read_existing_key(self):
        from picard.config_upgrade import get_option

        settings = {'old_key': 'value', 'other': 42}
        result = get_option(settings, 'old_key')
        self.assertEqual(result, 'value')
        # Key is NOT removed
        self.assertIn('old_key', settings)

    def test_read_missing_key_returns_default(self):
        from picard.config_upgrade import get_option

        settings = {'other': 42}
        result = get_option(settings, 'old_key', default='fallback')
        self.assertEqual(result, 'fallback')
        self.assertEqual(settings, {'other': 42})

    def test_read_missing_key_no_default_returns_none(self):
        from picard.config_upgrade import get_option

        settings = {'other': 42}
        result = get_option(settings, 'old_key')
        self.assertIsNone(result)

    def test_read_bool_value(self):
        from picard.config_upgrade import get_option

        settings = {'flag': True}
        result = get_option(settings, 'flag')
        self.assertTrue(result)
        self.assertIn('flag', settings)

    def test_read_none_value(self):
        from picard.config_upgrade import get_option

        settings = {'tracked': None}
        result = get_option(settings, 'tracked', default=False)
        self.assertIsNone(result)


class TestRemoveOption(PicardTestCase):
    """Tests for the polymorphic remove_option (dict path)."""

    def test_remove_existing_key(self):
        from picard.config_upgrade import remove_option

        settings = {'old_key': 'value', 'other': 42}
        remove_option(settings, 'old_key')
        self.assertNotIn('old_key', settings)
        self.assertIn('other', settings)

    def test_remove_missing_key_is_noop(self):
        from picard.config_upgrade import remove_option

        settings = {'other': 42}
        remove_option(settings, 'old_key')
        self.assertEqual(settings, {'other': 42})


class TestWriteOption(PicardTestCase):
    """Tests for the polymorphic write_option (dict path)."""

    def test_write_string(self):
        from picard.config_upgrade import write_option

        settings = {}
        write_option(settings, 'key', 'value')
        self.assertEqual(settings, {'key': 'value'})

    def test_write_bool(self):
        from picard.config_upgrade import write_option

        settings = {}
        write_option(settings, 'flag', True)
        self.assertEqual(settings, {'flag': True})

    def test_write_int(self):
        from picard.config_upgrade import write_option

        settings = {}
        write_option(settings, 'count', 42)
        self.assertEqual(settings, {'count': 42})

    def test_write_enum_stores_value(self):
        from enum import Enum

        from picard.config_upgrade import write_option

        class MyEnum(Enum):
            FOO = 'foo'
            BAR = 'bar'

        settings = {}
        write_option(settings, 'choice', MyEnum.FOO)
        self.assertEqual(settings, {'choice': 'foo'})

    def test_write_int_enum_stores_value(self):
        from enum import IntEnum

        from picard.config_upgrade import write_option

        class Priority(IntEnum):
            LOW = 1
            HIGH = 2

        settings = {}
        write_option(settings, 'priority', Priority.HIGH)
        self.assertEqual(settings, {'priority': 2})

    def test_write_overwrites_existing(self):
        from picard.config_upgrade import write_option

        settings = {'key': 'old'}
        write_option(settings, 'key', 'new')
        self.assertEqual(settings, {'key': 'new'})
