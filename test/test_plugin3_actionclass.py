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
import types
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.plugin3.api import PluginApi


class TestActionInstantiation(PicardTestCase):
    def setUp(self):
        super().setUp()
        """Clear registries before each test."""
        PluginApi._instances.clear()
        PluginApi._module_cache.clear()
        # Clean up test modules
        for name in list(sys.modules.keys()):
            if name.startswith('test_action_'):
                del sys.modules[name]

    def tearDown(self):
        """Clean up after each test."""
        PluginApi._instances.clear()
        PluginApi._module_cache.clear()
        for name in list(sys.modules.keys()):
            if name.startswith('test_action_'):
                del sys.modules[name]
        super().tearDown()

    def _create_api(self, module_name):
        """Helper to create and register a fake API instance."""

        class FakeManifest:
            pass

        manifest = FakeManifest()
        manifest.uuid = f'{module_name}-uuid'
        manifest.module_name = module_name
        manifest.source_locale = 'en'

        api = PluginApi(manifest, None)
        api.tr = Mock(return_value="Translated Text")

        # Create fake module
        module = types.ModuleType(module_name)
        sys.modules[module_name] = module

        api._plugin_module = module
        PluginApi._instances[module_name] = api

        return api, module

    def test_action_instantiation_with_api(self):
        """Test that plugin actions can be instantiated with API."""
        api, module = self._create_api('test_action_plugin')

        class TestAction:
            def __init__(self, api=None):
                self.api = api
                if api:
                    self.text = api.tr("action.name", "Test Action")

        # Set module for the action class
        TestAction.__module__ = 'test_action_plugin'

        # Simulate the fixed code from basetreeview.py
        retrieved_api = PluginApi._get_api_for_module(TestAction.__module__)
        action = TestAction(api=retrieved_api)

        self.assertIs(action.api, api)
        api.tr.assert_called_once_with("action.name", "Test Action")

    def test_action_instantiation_without_api_fallback(self):
        """Test that non-plugin actions work without API."""

        class NonPluginAction:
            def __init__(self, api=None):
                self.api = api

        # Set module that doesn't exist in plugin registry
        NonPluginAction.__module__ = 'non_plugin_module'

        # Simulate the fixed code from basetreeview.py
        retrieved_api = PluginApi._get_api_for_module(NonPluginAction.__module__)
        action = NonPluginAction(api=retrieved_api)

        self.assertIsNone(action.api)

    def test_action_instantiation_submodule(self):
        """Test that actions from plugin submodules get correct API."""
        api, module = self._create_api('test_action_main')

        class SubmoduleAction:
            def __init__(self, api=None):
                self.api = api

        # Set submodule name
        SubmoduleAction.__module__ = 'test_action_main.widgets'

        # Simulate the fixed code from basetreeview.py
        retrieved_api = PluginApi._get_api_for_module(SubmoduleAction.__module__)
        action = SubmoduleAction(api=retrieved_api)

        self.assertIs(action.api, api)

    def test_basetreeview_action_creation_logic(self):
        """Test the actual logic used in basetreeview.py"""
        api, module = self._create_api('test_plugin_module')

        class MockAction:
            __module__ = 'test_plugin_module'

            def __init__(self, api=None):
                self.api = api
                if api is None:
                    raise AttributeError("'NoneType' object has no attribute 'tr'")

        ActionClass = MockAction

        # Simulate the fixed code from basetreeview.py
        try:
            retrieved_api = PluginApi._get_api_for_module(ActionClass.__module__)
            action = ActionClass(api=retrieved_api)
            success = True
        except Exception:
            action = ActionClass()
            success = False

        self.assertTrue(success)
        self.assertIs(action.api, api)

    def test_basetreeview_fallback_logic(self):
        """Test fallback when API lookup fails"""

        class MockAction:
            __module__ = 'non_plugin_module'

            def __init__(self, api=None):
                self.api = api

        ActionClass = MockAction

        # Simulate the fixed code from basetreeview.py
        try:
            retrieved_api = PluginApi._get_api_for_module(ActionClass.__module__)
            action = ActionClass(api=retrieved_api)
        except Exception:
            action = ActionClass()

        self.assertIsNone(action.api)
