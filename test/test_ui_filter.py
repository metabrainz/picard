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

from collections import namedtuple
from unittest.mock import patch

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.file import File
from picard.metadata import (
    Metadata,
    MultiMetadataProxy,
)
from picard.tags.tagvar import (
    TagVar,
    TagVars,
)

from picard.ui.filter import Filter
from picard.ui.itemviews.basetreeview import BaseTreeView


TEST_TAGS = TagVars(
    TagVar(
        'album',
        shortdesc='Album',
        is_filterable=True,
    ),
    TagVar(
        'artist',
        shortdesc='Artist',
        is_filterable=True,
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
        is_filterable=True,
    ),
)


class FilterTestTags(PicardTestCase):
    """Test the Filter widget tags processing"""

    @patch('picard.tags.ALL_TAGS', TEST_TAGS)
    def test_filterable_tags(self):
        """Test generation of valid tags"""
        Filter.load_filterable_tags(force=True)
        filterable_tags = set(str(x) for x in Filter.filterable_tags)
        self.assertEqual(len(filterable_tags), 3)

        tag_names = ['album', 'artist', 'title']
        for name in tag_names:
            self.assertTrue(name in filterable_tags)

        tag_names = ['bitrate', 'filename', 'filepath', 'invalid_tag']
        for name in tag_names:
            self.assertFalse(name in filterable_tags)

    @patch('picard.ui.filter.ALL_TAGS', TEST_TAGS)
    def test_filter_button_text_logic(self):
        """Test the logic for updating filter button text from Filter._show_filter_dialog"""
        test_cases = [
            ([], None),
            (["~filename"], "File Name"),
            (["artist"], "Artist"),
            (["invalid_tag"], "invalid_tag"),
            (["~filename", "artist"], "2 filters"),
            (["~filename", "artist", "album", "title"], "4 filters"),
        ]

        for selected_filters, expected_text in test_cases:
            button_text = Filter.make_button_text(selected_filters)
            self.assertEqual(
                button_text, expected_text, f"Filter list {selected_filters} should produce '{expected_text}'"
            )


class FilterTestFiltering(PicardTestCase):
    """Test filtering of basetreeview items"""

    TestConditions = namedtuple('TestConditions', 'text filters has_tags matches')

    def test_filter_file_1(self):
        """Test with file-related filters"""

        test_file = get_test_data_path('test.flac')
        test_object = File(test_file)

        tests = [
            self.TestConditions(
                text='',
                filters={'~filename'},
                has_tags=True,
                matches={'~filename'},
            ),
            self.TestConditions(
                text='test',
                filters={'~filename'},
                has_tags=True,
                matches={'~filename'},
            ),
            self.TestConditions(
                text='not_in_path',
                filters={'~filename'},
                has_tags=True,
                matches=set(),
            ),
            self.TestConditions(
                text='',
                filters={'~filepath'},
                has_tags=True,
                matches={'~filepath'},
            ),
            self.TestConditions(
                text='test',
                filters={'~filepath'},
                has_tags=True,
                matches={'~filepath'},
            ),
            self.TestConditions(
                text='not_in_path',
                filters={'~filepath'},
                has_tags=True,
                matches=set(),
            ),
            self.TestConditions(
                text='',
                filters={'~filename', '~filepath'},
                has_tags=True,
                matches={'~filename', '~filepath'},
            ),
            self.TestConditions(
                text='test',
                filters={'~filename', '~filepath'},
                has_tags=True,
                matches={'~filename', '~filepath'},
            ),
            self.TestConditions(
                text='not_in_path',
                filters={'~filename', '~filepath'},
                has_tags=True,
                matches=set(),
            ),
            self.TestConditions(
                text='',
                filters={'~filename', '~filepath', 'invalid_filter'},
                has_tags=True,
                matches={'~filename', '~filepath'},
            ),
            self.TestConditions(
                text='test',
                filters={'~filename', '~filepath', 'invalid_filter'},
                has_tags=True,
                matches={'~filename', '~filepath'},
            ),
            self.TestConditions(
                text='not_in_path',
                filters={'~filename', '~filepath', 'invalid_filter'},
                has_tags=True,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_file_properties(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)

    def test_filter_file_2(self):
        """Test with no filter provided"""

        test_file = get_test_data_path('test.flac')
        test_object = File(test_file)

        tests = [
            self.TestConditions(
                text='',
                filters=set(),
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters=set(),
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='not_in_path',
                filters=set(),
                has_tags=False,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_file_properties(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)

    def test_filter_file_3(self):
        """Test with non-file-related filter provided"""

        test_file = get_test_data_path('test.flac')
        test_object = File(test_file)

        tests = [
            self.TestConditions(
                text='test',
                filters={'title'},
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters={'title', 'artist'},
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters={'title', 'artist', 'invalid_filter'},
                has_tags=False,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_file_properties(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)

    def test_filter_metadata_1(self):
        """Test with metadata-related filters"""

        test_metadata = {
            'title': 'test_title',
            'artist': 'test_artist',
        }
        test_object = MultiMetadataProxy(Metadata(test_metadata))

        tests = [
            self.TestConditions(
                text='',
                filters={'title'},
                has_tags=True,
                matches={'title'},
            ),
            self.TestConditions(
                text='',
                filters={'artist'},
                has_tags=True,
                matches={'artist'},
            ),
            self.TestConditions(
                text='',
                filters={'title', 'artist'},
                has_tags=True,
                matches={'title', 'artist'},
            ),
            self.TestConditions(
                text='test',
                filters={'title'},
                has_tags=True,
                matches={'title'},
            ),
            self.TestConditions(
                text='test',
                filters={'artist'},
                has_tags=True,
                matches={'artist'},
            ),
            self.TestConditions(
                text='test',
                filters={'title', 'artist'},
                has_tags=True,
                matches={'title', 'artist'},
            ),
            self.TestConditions(
                text='not_in_metadata',
                filters={'title'},
                has_tags=True,
                matches=set(),
            ),
            self.TestConditions(
                text='not_in_metadata',
                filters={'artist'},
                has_tags=True,
                matches=set(),
            ),
            self.TestConditions(
                text='not_in_metadata',
                filters={'title', 'artist'},
                has_tags=True,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_metadata(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)

    def test_filter_metadata_2(self):
        """Test with no filter provided"""

        test_metadata = {
            'title': 'test_title',
            'artist': 'test_artist',
        }
        test_object = MultiMetadataProxy(Metadata(test_metadata))

        tests = [
            self.TestConditions(
                text='',
                filters=set(),
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters=set(),
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='not_in_metadata',
                filters=set(),
                has_tags=False,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_metadata(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)

    def test_filter_metadata_3(self):
        """Test with non-metadata-related filters"""

        test_metadata = {
            'title': 'test_title',
            'artist': 'test_artist',
        }
        test_object = MultiMetadataProxy(Metadata(test_metadata))

        tests = [
            self.TestConditions(
                text='test',
                filters={'~filename'},
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters={'~filepath'},
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters={'~filename', '~filepath'},
                has_tags=False,
                matches=set(),
            ),
            self.TestConditions(
                text='test',
                filters={'~filename', '~filepath', 'invalid_filter'},
                has_tags=False,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_metadata(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)

    def test_filter_metadata_4(self):
        """Miscellaneous specific tests"""

        test_metadata = {
            'title': 'test_title',
            'artist': 'test_artist',
        }
        test_object = MultiMetadataProxy(Metadata(test_metadata))

        tests = [
            self.TestConditions(
                text='_artist',
                filters={'artist'},
                has_tags=True,
                matches={'artist'},
            ),
            self.TestConditions(
                text='_artist',
                filters={'title'},
                has_tags=True,
                matches=set(),
            ),
            self.TestConditions(
                text='_title',
                filters={'title'},
                has_tags=True,
                matches={'title'},
            ),
            self.TestConditions(
                text='_title',
                filters={'artist'},
                has_tags=True,
                matches=set(),
            ),
        ]

        for test in tests:
            text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
            has_tags, matches = BaseTreeView._matches_metadata(test_object, test.text, test.filters)
            self.assertEqual(has_tags, test.has_tags, text)
            self.assertEqual(matches, test.matches, text)
