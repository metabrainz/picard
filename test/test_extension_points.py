# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
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

from pathlib import Path
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.extension_points import (
    ExtensionPoint,
    set_plugin_uuid,
    unset_plugin_uuid,
)
from picard.extension_points.script_variables import (
    get_plugin_variable_documentation,
    get_plugin_variable_names,
    register_script_variable,
    unregister_all_script_variables,
    unregister_script_variable,
)
from picard.plugin3.manager import PluginManager
from picard.plugin3.plugin import Plugin


def create_mock_plugin(uuid, plugin_id='testplugin') -> Plugin:
    mock_plugin = Plugin(Path(), plugin_id)
    mock_plugin.name = plugin_id
    mock_plugin.manifest = Mock()
    mock_plugin.manifest.uuid = uuid
    mock_plugin.uuid = uuid
    mock_plugin.state = Mock()
    mock_plugin.state.value = 'enabled'
    mock_plugin.load_module = Mock()
    mock_plugin.enable = Mock()
    mock_plugin.disable = Mock()
    return mock_plugin


class TestExtensionPoints(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.ep = ExtensionPoint(label='test')
        self.mock_tagger = Mock()
        self.manager = PluginManager(self.mock_tagger)

    def tearDown(self):
        # Clean up registered UUIDs
        from picard.extension_points import _plugin_uuid_to_module

        _plugin_uuid_to_module.clear()
        super().tearDown()

    def test_plugin_not_enabled(self):
        """Plugin extensions should not be yielded if plugin not enabled"""
        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        self.ep.register('picard.plugins.testplugin', 'plugin_item')

        # Plugin not in enabled list
        items = list(self.ep)
        self.assertEqual(items, [])

    def test_plugin_enabled(self):
        """Plugin extensions should be yielded if plugin is enabled"""
        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        self.ep.register('picard.plugins.testplugin', 'plugin_item')

        # Enable plugin via manager (which handles config properly)
        mock_plugin = create_mock_plugin(uuid)
        self.manager.enable_plugin(mock_plugin)

        items = list(self.ep)
        self.assertEqual(items, ['plugin_item'])

    def test_multiple_plugins(self):
        """Multiple plugins with different enabled states"""
        uuid1 = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        uuid2 = 'b2c3d4e5-f6a7-4b5c-9d0e-1f2a3b4c5d6e'

        set_plugin_uuid(uuid1, 'plugin1')
        set_plugin_uuid(uuid2, 'plugin2')

        self.ep.register('picard.plugins.plugin1', 'item1')
        self.ep.register('picard.plugins.plugin2', 'item2')

        # Only enable plugin1
        mock_plugin = create_mock_plugin(uuid1, 'plugin1')
        self.manager.enable_plugin(mock_plugin)

        items = list(self.ep)
        self.assertEqual(items, ['item1'])

    def test_unregister_uuid(self):
        """Unregistering UUID should prevent plugin from being yielded"""
        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        self.ep.register('picard.plugins.testplugin', 'plugin_item')

        mock_plugin = create_mock_plugin(uuid)
        self.manager.enable_plugin(mock_plugin)

        # Should be yielded
        items = list(self.ep)
        self.assertEqual(items, ['plugin_item'])

        # Unregister UUID
        unset_plugin_uuid(uuid)

        # Should not be yielded anymore
        items = list(self.ep)
        self.assertEqual(items, [])

    def test_unregister_nonexistent_uuid(self):
        """Unregistering non-existent UUID should not raise error"""
        # Should not raise
        unset_plugin_uuid('nonexistent-uuid')

    def test_extension_point_without_label(self):
        """ExtensionPoint without label should generate UUID label"""
        ep = ExtensionPoint()
        # Label should be a UUID
        self.assertIsNotNone(ep.label)
        self.assertNotEqual(ep.label, '')

    def test_extension_point_repr(self):
        """ExtensionPoint repr should show label"""
        ep = ExtensionPoint(label='test_label')
        self.assertEqual(repr(ep), "ExtensionPoint(label='test_label')")

    def test_unregister_module(self):
        """Unregistering module should remove all its extensions"""
        self.ep.register('picard.plugins.testplugin', 'item1')
        self.ep.register('picard.plugins.testplugin', 'item2')

        # Register UUID and enable
        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        mock_plugin = create_mock_plugin(uuid)
        self.manager.enable_plugin(mock_plugin)

        # Should yield both items
        items = list(self.ep)
        self.assertEqual(len(items), 2)

        # Unregister module
        self.ep.unregister_module('testplugin')

        # Should yield nothing
        items = list(self.ep)
        self.assertEqual(items, [])

    def test_unregister_module_nonexistent(self):
        """Unregistering non-existent module should not raise error"""
        # Should not raise
        self.ep.unregister_module('nonexistent')

    def test_no_config_yields_all(self):
        """When config is None, all extensions should be yielded"""
        from unittest.mock import patch

        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        self.ep.register('picard.plugins.testplugin', 'plugin_item')

        # Mock get_config to return None
        with patch('picard.extension_points.get_config', return_value=None):
            items = list(self.ep)
            self.assertEqual(items, ['plugin_item'])

    def test_unregister_module_extensions(self):
        """unregister_module_extensions should unregister from all extension points"""
        from picard.extension_points import unregister_module_extensions

        ep1 = ExtensionPoint(label='ep1')
        ep2 = ExtensionPoint(label='ep2')

        ep1.register('picard.plugins.testplugin', 'item1')
        ep2.register('picard.plugins.testplugin', 'item2')

        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        mock_plugin = create_mock_plugin(uuid)
        self.manager.enable_plugin(mock_plugin)

        # Both should yield items
        self.assertEqual(len(list(ep1)), 1)
        self.assertEqual(len(list(ep2)), 1)

        # Unregister from all extension points
        unregister_module_extensions('testplugin')

        # Neither should yield items
        self.assertEqual(list(ep1), [])
        self.assertEqual(list(ep2), [])


class TestExtensionPointsScriptVariable(PicardTestCase):
    def setUp(self):
        super().setUp()
        patcher_ep = patch(
            'picard.extension_points.script_variables.ext_point_script_variables',
            ExtensionPoint(label='test_variables'),
        )
        patcher_config = patch('picard.extension_points.get_config', return_value=None)
        self.ext_point = patcher_ep.start()
        patcher_config.start()
        self.addCleanup(patcher_ep.stop)
        self.addCleanup(patcher_config.stop)

    def _make_api(self, module='picard.plugins.testplugin', name='Test Plugin'):
        api = MagicMock()
        api._plugin_module.__name__ = module
        api.module_path = module
        api.plugin_id = module.split('.')[-1]
        api.manifest.name_i18n.return_value = name
        return api

    def test_register_script_variable(self):
        register_script_variable('my_var1', 'some docs')
        register_script_variable('my_var2', 'other docs')
        self.assertEqual({'my_var1', 'my_var2'}, get_plugin_variable_names())
        self.assertEqual('some docs', get_plugin_variable_documentation('my_var1'))

    def test_register_script_variable_no_docs(self):
        register_script_variable('my_var1')
        self.assertEqual({'my_var1'}, get_plugin_variable_names())
        self.assertIsNone(get_plugin_variable_documentation('my_var1'))

    def test_register_script_variable_with_api(self):
        api = self._make_api()
        register_script_variable('my_var1', 'Some docs', api)
        register_script_variable('my_var2', api=api)
        self.assertEqual({'my_var1', 'my_var2'}, get_plugin_variable_names())
        self.assertEqual('Some docs', get_plugin_variable_documentation('my_var1'))
        self.assertIsNone(get_plugin_variable_documentation('my_var2'))

    def test_register_script_variable_invalid_name(self):
        with self.assertRaises(ValueError):
            register_script_variable('my-var1')

    def test_register_script_variable_plugin_id(self):
        """Registered TagVar should carry the plugin_id from the API."""
        api = self._make_api()
        register_script_variable('my_var', 'docs', api)
        for var in self.ext_point:
            if var.name == 'my_var':
                self.assertEqual('testplugin', var.plugin_id)
                break
        else:
            self.fail("Variable not found in extension point")

    def test_register_script_variable_is_hidden(self):
        """is_hidden parameter should be passed through to the TagVar."""
        register_script_variable('hidden_var', 'docs', is_hidden=True)
        for var in self.ext_point:
            if var.name == 'hidden_var':
                self.assertTrue(var.is_hidden)
                self.assertEqual('~hidden_var', str(var))
                self.assertEqual('_hidden_var', var.script_name())
                break
        else:
            self.fail("Variable not found in extension point")

    def test_register_script_variable_is_multi_value(self):
        """is_multi_value parameter should be passed through to the TagVar."""
        register_script_variable('multi_var', 'docs', is_multi_value=True)
        for var in self.ext_point:
            if var.name == 'multi_var':
                self.assertTrue(var.is_multi_value)
                break
        else:
            self.fail("Variable not found in extension point")

    def test_register_script_variable_underscore_prefix_normalized(self):
        """Names starting with _ should be normalized to is_hidden=True with stripped name."""
        register_script_variable('_hidden_by_prefix', 'docs')
        self.assertIn('hidden_by_prefix', get_plugin_variable_names())
        self.assertNotIn('_hidden_by_prefix', get_plugin_variable_names())
        for var in self.ext_point:
            if var.name == 'hidden_by_prefix':
                self.assertTrue(var.is_hidden)
                self.assertEqual('_hidden_by_prefix', var.script_name())
                break
        else:
            self.fail("Variable not found in extension point")

    def test_register_script_variable_deduplication(self):
        """Registering the same variable twice from the same plugin should update, not duplicate."""
        api = self._make_api()
        register_script_variable('my_var', 'First docs', api)
        register_script_variable('my_var', 'Updated docs', api)
        self.assertEqual({'my_var'}, get_plugin_variable_names())
        self.assertEqual('Updated docs', get_plugin_variable_documentation('my_var'))

    def test_register_same_variable_different_plugins(self):
        """Same variable name from different plugins should both be kept."""
        api1 = self._make_api('picard.plugins.plugin1', 'Plugin One')
        api2 = self._make_api('picard.plugins.plugin2', 'Plugin Two')
        register_script_variable('shared_var', 'Docs from plugin1', api1)
        register_script_variable('shared_var', 'Docs from plugin2', api2)
        self.assertEqual({'shared_var'}, get_plugin_variable_names())
        self.assertEqual('Docs from plugin1', get_plugin_variable_documentation('shared_var'))

    def test_unregister_script_variable(self):
        """Unregistering a single variable should remove only that variable."""
        api = self._make_api()
        register_script_variable('var1', 'Docs 1', api)
        register_script_variable('var2', 'Docs 2', api)
        self.assertEqual({'var1', 'var2'}, get_plugin_variable_names())
        unregister_script_variable('var1', api)
        self.assertEqual({'var2'}, get_plugin_variable_names())

    def test_unregister_script_variable_nonexistent(self):
        """Unregistering a variable that doesn't exist should not raise."""
        api = self._make_api()
        unregister_script_variable('nonexistent', api)

    def test_unregister_all_script_variables(self):
        """Unregistering all variables should remove all variables from a plugin."""
        api = self._make_api()
        register_script_variable('var1', 'Docs 1', api)
        register_script_variable('var2', 'Docs 2', api)
        register_script_variable('var3', 'Docs 3', api)
        self.assertEqual({'var1', 'var2', 'var3'}, get_plugin_variable_names())
        unregister_all_script_variables(api)
        self.assertEqual(set(), get_plugin_variable_names())

    def test_unregister_all_does_not_affect_other_plugins(self):
        """Unregistering all variables from one plugin should not affect another."""
        api1 = self._make_api('picard.plugins.plugin1', 'Plugin One')
        api2 = self._make_api('picard.plugins.plugin2', 'Plugin Two')
        register_script_variable('var_from_p1', 'Docs', api1)
        register_script_variable('var_from_p2', 'Docs', api2)
        unregister_all_script_variables(api1)
        self.assertEqual({'var_from_p2'}, get_plugin_variable_names())

    def test_unregister_does_not_affect_other_plugins(self):
        """Unregistering a variable name should only remove it from the calling plugin."""
        api1 = self._make_api('picard.plugins.plugin1', 'Plugin One')
        api2 = self._make_api('picard.plugins.plugin2', 'Plugin Two')
        register_script_variable('shared_var', 'Docs from p1', api1)
        register_script_variable('shared_var', 'Docs from p2', api2)
        unregister_script_variable('shared_var', api1)
        self.assertEqual({'shared_var'}, get_plugin_variable_names())
        self.assertEqual('Docs from p2', get_plugin_variable_documentation('shared_var'))

    def test_extension_point_unregister_with_match(self):
        """ExtensionPoint.unregister should remove only items matching the callable."""
        ep = ExtensionPoint(label='test_unregister')
        ep.register('picard.plugins.testplugin', ('a', 'data_a'))
        ep.register('picard.plugins.testplugin', ('b', 'data_b'))
        ep.register('picard.plugins.testplugin', ('c', 'data_c'))

        uuid = 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'
        set_plugin_uuid(uuid, 'testplugin')
        mock_plugin = create_mock_plugin(uuid)
        PluginManager(Mock()).enable_plugin(mock_plugin)

        ep.unregister('picard.plugins.testplugin', lambda item: item[0] == 'b')
        self.assertEqual([('a', 'data_a'), ('c', 'data_c')], list(ep))
