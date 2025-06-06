# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025 Francisco Lisboa
# Copyright (C) 2025 Bob Swift
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

from picard.tags.tagvar import (
    TagVar,
    TagVars,
)

from picard.ui.filter import Filter
from picard.ui.itemviews import MainPanel
from picard.ui.itemviews.basetreeview import BaseTreeView


TEST_TAGS = TagVars(
    TagVar(
        'album',
        shortdesc='Album',
    ),
    TagVar(
        'artist',
        shortdesc='Artist',
    ),
    TagVar(
        'bitrate',
        shortdesc='Bitrate',
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filename',
        shortdesc='File Name',
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filepath',
        shortdesc='File Path',
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'title',
        shortdesc='Title',
    ),
)


class FilterxTest(PicardTestCase):
    """Test the Filter widget functionality"""

    def test_filter_class_exists(self):
        """Test that Filter class can be imported and has required attributes"""
        self.assertTrue(hasattr(Filter, 'filterChanged'))
        self.assertTrue(hasattr(Filter, '_query_changed'))
        self.assertTrue(hasattr(Filter, 'clear'))
        self.assertTrue(hasattr(Filter, 'set_focus'))

    # @patch('picard.const.tags.ALL_TAGS', TEST_TAGS)
    def test_filter_button_text_logic(self):
        """Test the logic for updating filter button text from Filter._show_filter_dialog"""
        test_cases = [
            ([], None),
            (["filename"], "Filename"),
            (["artist"], "Artist"),
            (["invalid_tag"], "invalid_tag"),
            (["filename", "artist"], "2 filters"),
            (["filename", "artist", "album", "title"], "4 filters"),
        ]

        for selected_filters, expected_text in test_cases:
            button_text = Filter.make_button_text(selected_filters)
            self.assertEqual(button_text, expected_text,
                           f"Filter list {selected_filters} should produce '{expected_text}'")

    @patch('picard.ui.filter.ALL_TAGS', TEST_TAGS)
    def test_filterable_tags(self):
        """Test generation of valid tags"""
        filterable_tags = set(str(x) for x in Filter.get_filterable_tags())
        self.assertEqual(len(filterable_tags), 35)

        tag_names = ['album', 'artist', 'title']
        for name in tag_names:
            self.assertTrue(name in filterable_tags)

        tag_names = ['bitrate', 'filename', 'filepath', 'invalid_tag']
        for name in tag_names:
            self.assertFalse(name in filterable_tags)


class BaseTreeViewFilteringTest(PicardTestCase):
    """Test filtering functionality in BaseTreeView"""

    def test_filter_methods_exist(self):
        """Test that BaseTreeView has the required filtering methods"""
        self.assertTrue(hasattr(BaseTreeView, 'setup_filter_box'))
        self.assertTrue(hasattr(BaseTreeView, 'filter_items'))
        self.assertTrue(hasattr(BaseTreeView, '_filter_tree_items'))
        self.assertTrue(hasattr(BaseTreeView, '_restore_all_items'))


class MainPanelFilterTest(PicardTestCase):
    """Test filter functionality integration in MainPanel"""

    def test_main_panel_has_toggle_method(self):
        """Test that MainPanel has the toggle_filter_boxes method"""
        self.assertTrue(hasattr(MainPanel, 'toggle_filter_boxes'))
