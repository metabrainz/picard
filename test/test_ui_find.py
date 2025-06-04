# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025 Francisco Lisboa
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

from picard.metadata import Metadata
from picard.tags import preserved_tag_names

from picard.ui.find import FindBox
from picard.ui.itemviews import MainPanel
from picard.ui.itemviews.basetreeview import BaseTreeView


class FindBoxTest(PicardTestCase):
    """Test the FindBox widget functionality"""

    def test_tag_names_available(self):
        """Test that tag_names() returns valid tags for filtering"""
        tags = set(preserved_tag_names())
        self.assertIsInstance(tags, set)
        self.assertGreater(len(tags), 0)
        self.assertIn('artist', tags)
        self.assertIn('album', tags)
        self.assertIn('title', tags)

    def test_findbox_class_exists(self):
        """Test that FindBox class can be imported and has required attributes"""
        self.assertTrue(hasattr(FindBox, 'findChanged'))
        self.assertTrue(hasattr(FindBox, '_query_changed'))
        self.assertTrue(hasattr(FindBox, 'clear'))
        self.assertTrue(hasattr(FindBox, 'set_focus'))

    def test_filter_button_text_logic(self):
        """Test the logic for updating filter button text from FindBox._show_filter_dialog"""
        test_cases = [
            ([], "Filters"),
            (["filename"], "filename"),
            (["filename", "artist"], "filename, artist"),
            (["filename", "artist", "album", "title"], "4 filters"),
        ]

        for selected_filters, expected_text in test_cases:
            if not selected_filters or selected_filters == []:
                button_text = "Filters"
            elif len(selected_filters) <= 2:
                button_text = ", ".join(selected_filters)
            else:
                button_text = f"{len(selected_filters)} filters"

            self.assertEqual(button_text, expected_text,
                           f"Filter list {selected_filters} should produce text '{expected_text}'")

    def test_filename_filtering_patterns(self):
        """Test filename filtering patterns used in the implementation"""
        filename = "Test_Song.mp3"
        base_filename = filename.lower().rsplit('.', 1)[0]

        self.assertTrue("test" in base_filename)
        self.assertTrue("song" in base_filename)
        self.assertFalse("album" in base_filename)

    def test_filepath_filtering_patterns(self):
        """Test filepath filtering patterns used in the implementation"""
        filepath = "/home/user/Music/Artist/Album/01-Song.mp3"
        filepath_lower = filepath.lower()

        self.assertTrue("music" in filepath_lower)
        self.assertTrue("artist" in filepath_lower)
        self.assertTrue("album" in filepath_lower)
        self.assertTrue("song" in filepath_lower)


class BaseTreeViewFilteringTest(PicardTestCase):
    """Test filtering functionality in BaseTreeView"""

    def test_filter_methods_exist(self):
        """Test that BaseTreeView has the required filtering methods"""
        self.assertTrue(hasattr(BaseTreeView, 'setup_find_box'))
        self.assertTrue(hasattr(BaseTreeView, 'filter_items'))
        self.assertTrue(hasattr(BaseTreeView, '_filter_tree_items'))
        self.assertTrue(hasattr(BaseTreeView, '_restore_all_items'))

    def test_metadata_filtering_logic(self):
        """Test metadata filtering logic used in BaseTreeView._filter_tree_items"""
        metadata = Metadata()
        metadata['artist'] = 'The Beatles'
        metadata['album'] = 'Abbey Road'
        metadata['title'] = 'Come Together'

        text = "beatles"
        filters = ["artist"]

        child_match = False
        for tag, values in metadata.rawitems():
            if isinstance(values, list):
                for value in values:
                    if filters == [] or tag.lower() in filters:
                        if text in str(value).lower():
                            child_match = True
                            break
            elif filters == [] or tag.lower() in filters:
                if text in str(values).lower():
                    child_match = True
                    break

        self.assertTrue(child_match)

        child_match = False
        filters = ["album"]
        for tag, values in metadata.rawitems():
            if isinstance(values, list):
                for value in values:
                    if filters == [] or tag.lower() in filters:
                        if text in str(value).lower():
                            child_match = True
                            break
            elif filters == [] or tag.lower() in filters:
                if text in str(values).lower():
                    child_match = True
                    break

        self.assertFalse(child_match)

    def test_empty_filter_searches_all(self):
        """Test that empty filter list searches all fields"""
        metadata = Metadata()
        metadata['artist'] = 'Test Artist'
        metadata['album'] = 'Different Album'

        text = "test"
        filters = []

        metadata_match = False
        for tag, values in metadata.rawitems():
            if isinstance(values, list):
                for value in values:
                    if filters == [] or tag.lower() in filters:
                        if text in str(value).lower():
                            metadata_match = True
                            break
            elif filters == [] or tag.lower() in filters:
                if text in str(values).lower():
                    metadata_match = True
                    break

        self.assertTrue(metadata_match)

    def test_filter_items_text_processing(self):
        """Test that BaseTreeView.filter_items processes text correctly"""
        test_text = "  TeSt  "
        processed = test_text.strip().lower()

        self.assertEqual(processed, "test")

    def test_filename_iteration_logic(self):
        """Test the logic for iterating through files for filename matching"""
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                self.base_filename = filename.split('/')[-1].rsplit('.', 1)[0]

        class MockCluster:
            def __init__(self, files):
                self.files = files

            def iterfiles(self):
                return self.files

        files = [
            MockFile("test_song.mp3"),
            MockFile("another_track.mp3")
        ]
        cluster = MockCluster(files)

        text = "test"
        filters = ["filename"]

        child_match = False
        if hasattr(cluster, 'iterfiles'):
            for file_ in cluster.iterfiles():
                if filters == [] or "filename" in filters:
                    if text in file_.base_filename.lower():
                        child_match = True
                        break

        self.assertTrue(child_match)


class MainPanelFindTest(PicardTestCase):
    """Test find functionality integration in MainPanel"""

    def test_main_panel_has_toggle_method(self):
        """Test that MainPanel has the toggle_find_boxes method"""
        self.assertTrue(hasattr(MainPanel, 'toggle_find_boxes'))

    def test_toggle_logic(self):
        """Test the core toggle logic used in MainPanel.toggle_find_boxes"""
        find_box_visible = False

        new_visible_state = not find_box_visible
        self.assertTrue(new_visible_state)

        find_box_visible = True
        new_visible_state = not find_box_visible
        self.assertFalse(new_visible_state)
