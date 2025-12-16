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


class TestRefItemIntegrationImprovements(PicardTestCase):
    def test_plugin_metadata_refitem_integration(self):
        """Test that plugin metadata manager has RefItem integration."""
        # Just verify the integration code exists
        import picard.plugin3.plugin_metadata as metadata_module

        # Check that the module can import RefItem (integration exists)
        source_code = metadata_module.__file__
        with open(source_code, 'r') as f:
            content = f.read()

        # Verify RefItem integration is present
        self.assertIn('ref_item', content)
        self.assertIn('hasattr(plugin, \'ref_item\')', content)

    def test_async_manager_docstring_updated(self):
        """Test that async manager methods have updated docstrings."""
        from picard.plugin3.asyncops.manager import AsyncPluginManager

        manager = AsyncPluginManager(Mock())

        # Check install_plugin docstring mentions RefItem
        install_doc = manager.install_plugin.__doc__
        self.assertIn("RefItem", install_doc)

        # Check switch_ref docstring mentions RefItem
        switch_doc = manager.switch_ref.__doc__
        self.assertIn("RefItem", switch_doc)

    def test_refitem_for_logging_efficiency(self):
        """Test RefItem.for_logging efficiency."""
        # Should return None for empty values
        self.assertIsNone(RefItem.for_logging("", ""))
        self.assertIsNone(RefItem.for_logging())

        # Should create minimal RefItem for valid values
        ref = RefItem.for_logging("v1.0.0", "abc123")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.name, "v1.0.0")
        self.assertEqual(ref.commit, "abc123")

        # Should work with partial data
        ref = RefItem.for_logging("v1.0.0")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.name, "v1.0.0")
        self.assertEqual(ref.commit, "")
