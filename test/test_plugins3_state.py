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
