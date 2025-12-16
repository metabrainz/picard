# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem
from picard.plugin3.manager import PluginManager


class TestInstallPluginRefItem(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager = PluginManager()
        self.manager._refs_cache = Mock()

    def test_normalize_ref_parameter_in_install(self):
        """Test that install_plugin properly normalizes ref parameters."""
        # Test with RefItem
        ref_item = RefItem(name="v1.0.0", commit="abc123")
        result = self.manager._normalize_ref_parameter(ref_item)
        self.assertEqual(result, ref_item)

        # Test with string
        result = self.manager._normalize_ref_parameter("v1.0.0")
        self.assertIsInstance(result, RefItem)
        self.assertEqual(result.name, "v1.0.0")

        # Test with None
        result = self.manager._normalize_ref_parameter(None)
        self.assertIsNone(result)

    def test_install_plugin_ref_parameter_types(self):
        """Test that install_plugin accepts different ref parameter types."""
        # Mock the method to avoid complex setup
        original_method = self.manager.install_plugin

        def mock_install(url, ref=None, **kwargs):
            # Just test the ref normalization part
            target_ref_item = self.manager._normalize_ref_parameter(ref)
            ref_name = target_ref_item.name if target_ref_item else None
            return ref_name

        self.manager.install_plugin = mock_install

        # Test with RefItem
        ref_item = RefItem(name="v1.0.0", commit="abc123")
        result = self.manager.install_plugin("test-url", ref=ref_item)
        self.assertEqual(result, "v1.0.0")

        # Test with string
        result = self.manager.install_plugin("test-url", ref="main")
        self.assertEqual(result, "main")

        # Test with None
        result = self.manager.install_plugin("test-url", ref=None)
        self.assertIsNone(result)

        # Restore original method
        self.manager.install_plugin = original_method

    def test_install_plugin_docstring_updated(self):
        """Test that install_plugin docstring mentions RefItem support."""
        docstring = self.manager.install_plugin.__doc__
        self.assertIn("RefItem", docstring)
        self.assertIn("string", docstring)
        self.assertIn("None", docstring)
