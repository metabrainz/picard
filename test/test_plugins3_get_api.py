# -*- coding: utf-8 -*-

import sys
import types
import unittest

from picard.plugin3.api import PluginApi


class TestPluginApiGetApi(unittest.TestCase):
    def setUp(self):
        """Clear registries before each test."""
        PluginApi._instances.clear()
        PluginApi._module_cache.clear()
        # Clean up test modules
        for name in list(sys.modules.keys()):
            if name.startswith('test_plugin_'):
                del sys.modules[name]

    def tearDown(self):
        """Clean up after each test."""
        PluginApi._instances.clear()
        PluginApi._module_cache.clear()
        for name in list(sys.modules.keys()):
            if name.startswith('test_plugin_'):
                del sys.modules[name]

    def _create_api(self, module_name):
        """Helper to create and register a fake API instance."""

        class FakeManifest:
            pass

        manifest = FakeManifest()
        manifest.uuid = f'{module_name}-uuid'
        manifest.module_name = module_name
        manifest.source_locale = 'en'

        api = PluginApi(manifest, None)

        # Create fake module
        module = types.ModuleType(module_name)
        sys.modules[module_name] = module

        api._plugin_module = module
        PluginApi._instances[module_name] = api

        return api, module

    def test_get_api_from_main_module(self):
        """Test getting API from main plugin module."""
        api, module = self._create_api('test_plugin_main')

        # Execute in module context
        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            module.__dict__,
        )

        self.assertIs(module.__dict__['retrieved_api'], api)

    def test_get_api_from_submodule(self):
        """Test getting API from plugin submodule."""
        api, main_module = self._create_api('test_plugin_sub')

        # Create submodule
        submodule = types.ModuleType('test_plugin_sub.widgets')
        sys.modules['test_plugin_sub.widgets'] = submodule

        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            submodule.__dict__,
        )

        self.assertIs(submodule.__dict__['retrieved_api'], api)

    def test_get_api_from_nested_submodule(self):
        """Test getting API from deeply nested submodule."""
        api, main_module = self._create_api('test_plugin_nested')

        # Create nested submodule
        submodule = types.ModuleType('test_plugin_nested.ui.dialogs')
        sys.modules['test_plugin_nested.ui.dialogs'] = submodule

        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            submodule.__dict__,
        )

        self.assertIs(submodule.__dict__['retrieved_api'], api)

    def test_get_api_caching(self):
        """Test that get_api() caches results."""
        api, module = self._create_api('test_plugin_cache')

        # First call should populate cache
        self.assertEqual(len(PluginApi._module_cache), 0)

        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            module.__dict__,
        )

        self.assertEqual(len(PluginApi._module_cache), 1)
        self.assertIn('test_plugin_cache', PluginApi._module_cache)
        self.assertIs(PluginApi._module_cache['test_plugin_cache'], api)

    def test_get_api_cache_hit(self):
        """Test that subsequent calls use cache."""
        api, module = self._create_api('test_plugin_cache_hit')

        # Populate cache
        PluginApi._module_cache['test_plugin_cache_hit'] = api

        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            module.__dict__,
        )

        # Should return cached instance
        self.assertIs(module.__dict__['retrieved_api'], api)

    def test_get_api_unknown_module(self):
        """Test that get_api() raises error for unknown module."""
        unknown_module = types.ModuleType('unknown_plugin')
        sys.modules['unknown_plugin'] = unknown_module

        with self.assertRaises(RuntimeError) as cm:
            exec(
                """
from picard.plugin3.api import PluginApi
PluginApi.get_api()
""",
                unknown_module.__dict__,
            )

        self.assertIn('No PluginApi instance found', str(cm.exception))
        self.assertIn('unknown_plugin', str(cm.exception))

    def test_get_api_multiple_plugins(self):
        """Test get_api() with multiple plugins registered."""
        api1, module1 = self._create_api('test_plugin_one')
        api2, module2 = self._create_api('test_plugin_two')

        # Each should get its own API
        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            module1.__dict__,
        )

        exec(
            """
from picard.plugin3.api import PluginApi
retrieved_api = PluginApi.get_api()
""",
            module2.__dict__,
        )

        self.assertIs(module1.__dict__['retrieved_api'], api1)
        self.assertIs(module2.__dict__['retrieved_api'], api2)
        self.assertIsNot(api1, api2)

    def test_get_api_submodule_caching(self):
        """Test that submodules are cached separately."""
        api, main_module = self._create_api('test_plugin_subcache')

        submodule = types.ModuleType('test_plugin_subcache.widgets')
        sys.modules['test_plugin_subcache.widgets'] = submodule

        # Call from main module
        exec("from picard.plugin3.api import PluginApi; PluginApi.get_api()", main_module.__dict__)

        # Call from submodule
        exec("from picard.plugin3.api import PluginApi; PluginApi.get_api()", submodule.__dict__)

        # Both should be cached
        self.assertIn('test_plugin_subcache', PluginApi._module_cache)
        self.assertIn('test_plugin_subcache.widgets', PluginApi._module_cache)
        self.assertIs(PluginApi._module_cache['test_plugin_subcache'], api)
        self.assertIs(PluginApi._module_cache['test_plugin_subcache.widgets'], api)

    def test_get_api_for_module_direct(self):
        """Test _get_api_for_module() with direct module name."""
        api, module = self._create_api('test_plugin_direct')

        retrieved_api = PluginApi._get_api_for_module('test_plugin_direct')
        self.assertIs(retrieved_api, api)

    def test_get_api_for_module_submodule(self):
        """Test _get_api_for_module() with submodule name."""
        api, module = self._create_api('test_plugin_parent')

        retrieved_api = PluginApi._get_api_for_module('test_plugin_parent.submodule')
        self.assertIs(retrieved_api, api)

    def test_get_api_for_module_unknown(self):
        """Test _get_api_for_module() with unknown module."""
        retrieved_api = PluginApi._get_api_for_module('unknown_module')
        self.assertIsNone(retrieved_api)

    def test_get_api_for_module_caching(self):
        """Test _get_api_for_module() caches results."""
        api, module = self._create_api('test_plugin_cache_direct')

        # First call should populate cache
        self.assertEqual(len(PluginApi._module_cache), 0)
        retrieved_api = PluginApi._get_api_for_module('test_plugin_cache_direct')

        self.assertIs(retrieved_api, api)
        self.assertEqual(len(PluginApi._module_cache), 1)
        self.assertIn('test_plugin_cache_direct', PluginApi._module_cache)
