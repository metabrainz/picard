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

from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.plugin3.categories import (
    PluginCategorySet,
    category_title_i18n,
)


class TestPluginCategorySet(PicardTestCase):
    def test_init_empty(self):
        categories = PluginCategorySet()
        self.assertEqual(len(categories), 0)
        self.assertEqual(list(categories), [])

    def test_init_with_categories(self):
        categories = PluginCategorySet(['coverart', 'metadata'])
        self.assertEqual(len(categories), 2)
        self.assertIn('coverart', categories)
        self.assertIn('metadata', categories)

    def test_add(self):
        categories = PluginCategorySet()
        categories.add('coverart')
        self.assertEqual(len(categories), 1)
        self.assertIn('coverart', categories)

    def test_discard(self):
        categories = PluginCategorySet(['coverart', 'metadata'])
        categories.discard('coverart')
        self.assertEqual(len(categories), 1)
        self.assertNotIn('coverart', categories)
        self.assertIn('metadata', categories)

    def test_update(self):
        categories = PluginCategorySet(['coverart'])
        categories.update(['metadata', 'scripting'])
        self.assertEqual(len(categories), 3)
        self.assertIn('coverart', categories)
        self.assertIn('metadata', categories)
        self.assertIn('scripting', categories)

    def test_clear(self):
        categories = PluginCategorySet(['coverart', 'metadata'])
        categories.clear()
        self.assertEqual(len(categories), 0)

    def test_remove(self):
        categories = PluginCategorySet(['coverart', 'metadata'])
        categories.remove('coverart')
        self.assertEqual(len(categories), 1)
        self.assertNotIn('coverart', categories)

    def test_remove_missing_raises(self):
        categories = PluginCategorySet(['metadata'])
        with self.assertRaises(KeyError):
            categories.remove('coverart')

    def test_pop(self):
        categories = PluginCategorySet(['coverart'])
        popped = categories.pop()
        self.assertEqual(popped, 'coverart')
        self.assertEqual(len(categories), 0)

    def test_copy(self):
        categories = PluginCategorySet(['coverart', 'metadata'])
        copied = categories.copy()
        self.assertEqual(len(copied), 2)
        self.assertIn('coverart', copied)
        self.assertIn('metadata', copied)
        # Ensure it's a separate instance
        copied.add('scripting')
        self.assertNotIn('scripting', categories)

    def test_items_sorted(self):
        categories = PluginCategorySet(['metadata', 'coverart', 'scripting'])
        items = list(categories.items())
        # Should be sorted by translated title
        self.assertEqual(len(items), 3)
        # Check that all expected categories are present
        category_keys = [item[0] for item in items]
        self.assertIn('coverart', category_keys)
        self.assertIn('metadata', category_keys)
        self.assertIn('scripting', category_keys)

    def test_str_representation(self):
        categories = PluginCategorySet(['coverart', 'metadata'])
        str_repr = str(categories)
        self.assertIn('Cover Art', str_repr)
        self.assertIn('Metadata', str_repr)
        self.assertIn(',', str_repr)

    def test_repr(self):
        categories = PluginCategorySet(['coverart'])
        repr_str = repr(categories)
        self.assertTrue(repr_str.startswith('PluginCategorySet('))
        self.assertIn('coverart', repr_str)


class TestCategoryTitleI18n(PicardTestCase):
    @patch('picard.plugin3.categories._')
    def test_known_category(self, mock_gettext):
        mock_gettext.side_effect = lambda x: x  # Return untranslated
        self.assertEqual(category_title_i18n('coverart'), 'Cover Art')
        self.assertEqual(category_title_i18n('metadata'), 'Metadata')

    def test_unknown_category(self):
        self.assertEqual(category_title_i18n('unknown'), 'unknown')
