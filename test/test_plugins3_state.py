# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

from unittest.mock import Mock

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.plugin3.manifest import PluginManifest


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


class TestPluginState(PicardTestCase):
    def test_plugin_state_transitions(self):
        """Test that plugin state transitions work correctly."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        mock_tagger = Mock()
        plugin = Plugin(Path('/tmp'), 'test-plugin')

        # Initial state should be DISCOVERED
        self.assertEqual(plugin.state, PluginState.DISCOVERED)

        # Mock the module loading
        plugin._module = Mock()
        plugin._module.enable = Mock()
        plugin._module.disable = Mock()

        # Load module should transition to LOADED
        plugin.state = PluginState.DISCOVERED
        plugin.load_module = Mock(side_effect=lambda: setattr(plugin, 'state', PluginState.LOADED))
        plugin.load_module()
        self.assertEqual(plugin.state, PluginState.LOADED)

        # Enable should transition to ENABLED
        plugin.manifest = Mock()
        plugin.enable(mock_tagger)
        self.assertEqual(plugin.state, PluginState.ENABLED)

        # Disable should transition to DISABLED
        plugin.disable()
        self.assertEqual(plugin.state, PluginState.DISABLED)

    def test_plugin_double_enable_error(self):
        """Test that enabling an already enabled plugin raises error."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        mock_tagger = Mock()
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.ENABLED
        plugin._module = Mock()
        plugin.manifest = Mock()

        with self.assertRaises(ValueError) as context:
            plugin.enable(mock_tagger)

        self.assertIn('already enabled', str(context.exception))

    def test_plugin_double_disable_error(self):
        """Test that disabling an already disabled plugin raises error."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.DISABLED
        plugin._module = Mock()

        with self.assertRaises(ValueError) as context:
            plugin.disable()

        self.assertIn('already disabled', str(context.exception))

    def test_plugin_load_manifest(self):
        """Test Plugin.read_manifest() method."""
        from pathlib import Path

        from test.picardtestcase import get_test_data_path

        from picard.plugin3.plugin import Plugin

        plugins_dir = Path(get_test_data_path('testplugins3'))
        plugin = Plugin(plugins_dir, 'example')

        plugin.read_manifest()

        self.assertIsNotNone(plugin.manifest)
        self.assertEqual(plugin.manifest.name(), 'Example plugin')

    def test_plugin_initial_state(self):
        """Test that new Plugin starts in DISCOVERED state."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')

        self.assertEqual(plugin.state, PluginState.DISCOVERED)
        self.assertEqual(plugin.name, 'test-plugin')
        self.assertEqual(plugin.module_name, 'picard.plugins.test-plugin')

    def test_plugin_disable_with_disable_method(self):
        """Test Plugin.disable() when plugin has disable method."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.ENABLED

        # Mock module with disable method
        mock_module = Mock()
        mock_module.disable = Mock()
        plugin._module = mock_module

        plugin.disable()

        # Should call plugin's disable method
        mock_module.disable.assert_called_once()
        self.assertEqual(plugin.state, PluginState.DISABLED)

    def test_plugin_disable_without_disable_method(self):
        """Test Plugin.disable() when plugin has no disable method."""
        from pathlib import Path
        from unittest.mock import patch

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.ENABLED

        # Mock module without disable method
        mock_module = Mock(spec=[])  # Empty spec = no methods
        plugin._module = mock_module

        with patch('picard.plugin3.plugin.unregister_module_extensions'):
            plugin.disable()

        # Should not raise, just change state
        self.assertEqual(plugin.state, PluginState.DISABLED)

    def test_plugin_load_module_already_loaded(self):
        """Test Plugin.load_module() when already loaded."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.LOADED
        mock_module = Mock()
        plugin._module = mock_module

        # Should return existing module
        result = plugin.load_module()

        self.assertEqual(result, mock_module)
        self.assertEqual(plugin.state, PluginState.LOADED)

    def test_plugin_load_module_when_enabled(self):
        """Test Plugin.load_module() raises when already enabled."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.ENABLED

        with self.assertRaises(ValueError) as context:
            plugin.load_module()

        self.assertIn('already enabled', str(context.exception))

    def test_plugin_enable_already_enabled(self):
        """Test Plugin.enable() raises when already enabled."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        mock_tagger = Mock()
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.ENABLED
        plugin._module = Mock()
        plugin.manifest = Mock()

        with self.assertRaises(ValueError) as context:
            plugin.enable(mock_tagger)

        self.assertIn('already enabled', str(context.exception))
