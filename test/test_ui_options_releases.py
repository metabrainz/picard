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

from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.ui.options.releases import ReleasesOptionsPage


def _noop(s):
    return s


class TestLoadListItems(PicardTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch('picard.ui.options.releases.sort_key', side_effect=str.casefold)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.available = []
        self.preferred = []

    def _add_item(self, name, data, is_preferred):
        if is_preferred:
            self.preferred.append((data, name))
        else:
            self.available.append((data, name))

    def _load(self, preferred, source):
        ReleasesOptionsPage._load_list_items(preferred, _noop, source, self._add_item)

    def test_no_saved_preferences(self):
        """All items go to available, none to preferred."""
        self._load([], {'US': 'United States', 'DE': 'Germany', 'JP': 'Japan'})

        self.assertEqual(len(self.available), 3)
        self.assertEqual(len(self.preferred), 0)
        self.assertEqual({d for d, n in self.available}, {'US', 'DE', 'JP'})

    def test_all_items_preferred(self):
        """All items go to preferred, none to available."""
        self._load(['DE', 'US'], {'US': 'United States', 'DE': 'Germany'})

        self.assertEqual(len(self.available), 0)
        self.assertEqual(len(self.preferred), 2)

    def test_preferred_items_preserve_saved_order(self):
        """Preferred items appear in the order they were saved, not source order."""
        self._load(['JP', 'US'], {'US': 'United States', 'DE': 'Germany', 'JP': 'Japan'})

        self.assertEqual([d for d, n in self.preferred], ['JP', 'US'])

    def test_available_items_sorted_by_name(self):
        """Non-preferred items are sorted alphabetically by translated name."""
        self._load([], {'US': 'United States', 'DE': 'Germany', 'JP': 'Japan'})

        names = [name for d, name in self.available]
        self.assertEqual(names, sorted(names))

    def test_split_between_lists(self):
        """Items split correctly between available and preferred."""
        source = {
            'US': 'United States',
            'DE': 'Germany',
            'JP': 'Japan',
            'GB': 'United Kingdom',
        }

        self._load(['GB', 'DE'], source)

        self.assertEqual({d for d, n in self.available}, {'US', 'JP'})
        self.assertEqual([d for d, n in self.preferred], ['GB', 'DE'])

    def test_saved_items_not_in_source_are_ignored(self):
        """Saved preferences referencing removed items don't cause errors."""
        self._load(['XX', 'US'], {'US': 'United States', 'DE': 'Germany'})

        self.assertEqual(self.available, [('DE', 'Germany')])
        self.assertEqual(self.preferred, [('US', 'United States')])

    def test_translate_func_applied(self):
        """The translate_func is applied to source values."""
        ReleasesOptionsPage._load_list_items([], str.upper, {'a': 'alpha', 'b': 'bravo'}, self._add_item)

        names = [name for d, name in self.available]
        self.assertEqual(names, ['ALPHA', 'BRAVO'])
