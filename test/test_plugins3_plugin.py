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

from pathlib import Path
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.plugin3.plugin import (
    Plugin,
    PluginSourceSyncError,
)


class TestPluginSync(PicardTestCase):
    def test_plugin_sync_with_source(self):
        """Test Plugin.sync() with a plugin source."""
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        mock_source = Mock()

        plugin.sync(mock_source)

        mock_source.sync.assert_called_once_with(plugin.local_path)

    def test_plugin_sync_error(self):
        """Test Plugin.sync() raises PluginSourceSyncError on failure."""
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        mock_source = Mock()
        mock_source.sync.side_effect = Exception('Sync failed')

        with self.assertRaises(PluginSourceSyncError):
            plugin.sync(mock_source)

    def test_plugin_sync_without_source(self):
        """Test Plugin.sync() without source does nothing."""
        plugin = Plugin(Path('/tmp'), 'test-plugin')

        # Should not raise
        plugin.sync(None)


class TestPluginManifestReading(PicardTestCase):
    def test_read_manifest_invalid(self):
        """Test Plugin.read_manifest() with invalid manifest."""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('picard.plugin3.plugin.PluginManifest') as mock_manifest_class:
                mock_manifest = Mock()
                mock_manifest.validate.return_value = ['Error 1', 'Error 2']
                mock_manifest_class.return_value = mock_manifest

                plugin = Plugin(Path('/tmp'), 'test-plugin')

                with self.assertRaises(ValueError) as context:
                    plugin.read_manifest()

                self.assertIn('Invalid MANIFEST.toml', str(context.exception))
                self.assertIn('Error 1', str(context.exception))
