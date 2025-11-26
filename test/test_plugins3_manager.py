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

from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.plugin3.manager import PluginManager


class TestPluginManagerHelpers(PicardTestCase):
    def test_validate_manifest_valid(self):
        """Test _validate_manifest with valid manifest."""
        manager = PluginManager(None)
        mock_manifest = Mock()
        mock_manifest.validate.return_value = []

        # Should not raise
        manager._validate_manifest(mock_manifest)

    def test_validate_manifest_invalid(self):
        """Test _validate_manifest with invalid manifest."""
        manager = PluginManager(None)
        mock_manifest = Mock()
        mock_manifest.validate.return_value = ['Error 1', 'Error 2']

        with self.assertRaises(ValueError) as context:
            manager._validate_manifest(mock_manifest)

        self.assertIn('Invalid MANIFEST.toml', str(context.exception))

    def test_get_plugin_uuid_missing(self):
        """Test _get_plugin_uuid when UUID is missing."""
        manager = PluginManager(None)
        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_plugin.manifest = None

        with self.assertRaises(ValueError) as context:
            manager._get_plugin_uuid(mock_plugin)

        self.assertIn('has no UUID', str(context.exception))

    def test_get_plugin_uuid_success(self):
        """Test _get_plugin_uuid with valid UUID."""
        manager = PluginManager(None)
        mock_plugin = Mock()
        mock_plugin.manifest.uuid = 'test-uuid-123'

        result = manager._get_plugin_uuid(mock_plugin)

        self.assertEqual(result, 'test-uuid-123')

    def test_get_config_value(self):
        """Test _get_config_value helper."""
        with patch('picard.config.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.setting = {'plugins3': {'enabled': ['plugin1']}}
            mock_get_config.return_value = mock_config

            manager = PluginManager(None)
            result = manager._get_config_value('plugins3', 'enabled', default=[])

            self.assertEqual(result, ['plugin1'])

    def test_get_config_value_default(self):
        """Test _get_config_value returns default when key missing."""
        with patch('picard.config.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.setting = {}
            mock_get_config.return_value = mock_config

            manager = PluginManager(None)
            result = manager._get_config_value('missing', 'key', default='default_value')

            self.assertEqual(result, 'default_value')
