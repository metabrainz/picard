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

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem


class TestRefSelectorIntegration(PicardTestCase):
    def test_refitem_import_in_refselector(self):
        """Test that RefItem is properly imported in refselector module."""
        # This verifies the integration exists without creating Qt widgets
        import picard.ui.widgets.refselector as refselector_module

        # Check that RefItem is imported
        self.assertTrue(hasattr(refselector_module, 'RefItem'))
        self.assertEqual(refselector_module.RefItem, RefItem)

    def test_refitem_creation_logic(self):
        """Test RefItem creation logic used in refselector."""
        # Test the same logic used in load_refs method
        ref_data = {'name': 'v1.0.0', 'commit': 'abc123'}
        current_ref = 'v1.0.0'

        # Simulate tag RefItem creation
        ref_item = RefItem(
            name=ref_data['name'],
            commit=ref_data.get('commit'),
            is_current=(current_ref and ref_data['name'] == current_ref),
            is_tag=True,
        )

        self.assertEqual(ref_item.name, 'v1.0.0')
        self.assertEqual(ref_item.commit, 'abc123')
        self.assertTrue(ref_item.is_tag)
        self.assertTrue(ref_item.is_current)
        self.assertFalse(ref_item.is_branch)

        # Test formatting (used for display)
        formatted = ref_item.format()
        self.assertIn('v1.0.0', formatted)
        self.assertIn('current', formatted.lower())

    def test_custom_refitem_creation(self):
        """Test custom RefItem creation logic."""
        # Simulate custom ref input
        custom_text = "feature-branch"

        ref_item = RefItem(name=custom_text)

        self.assertEqual(ref_item.name, "feature-branch")
        self.assertIsNone(ref_item.commit)
        self.assertFalse(ref_item.is_tag)
        self.assertFalse(ref_item.is_branch)
        self.assertFalse(ref_item.is_current)

    def test_refitem_validation_in_selector_context(self):
        """Test RefItem validation in selector context."""
        # Test valid RefItem
        valid_ref = RefItem(name="v1.0.0", commit="abc123")
        self.assertTrue(valid_ref.is_valid())

        # Test empty RefItem (should be invalid)
        empty_ref = RefItem(name="", commit="")
        self.assertFalse(empty_ref.is_valid())

        # Test RefItem with only name (valid for custom input)
        name_only_ref = RefItem(name="custom-ref")
        self.assertTrue(name_only_ref.is_valid())
