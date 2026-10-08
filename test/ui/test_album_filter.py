# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
# Copyright (C) 2025 Francisco Lisboa
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025-2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections import namedtuple
from unittest.mock import MagicMock

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.album import Album
from picard.file import File
from picard.metadata import (
    Metadata,
    MultiMetadataProxy,
)
from picard.tags.tagvar import (
    TagVar,
    TagVars,
)

from picard.ui.filter import StatusFilters
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


def create_fake_album(modified: bool = False, complete: bool = False):
    """Album-like object exposing the boolean predicates used by the columns."""
    fake_album_class = MagicMock(spec=Album)

    def is_modified() -> bool:
        return modified

    def is_complete() -> bool:
        return complete

    fake_album_class.is_modified.side_effect = is_modified
    fake_album_class.is_complete.side_effect = is_complete

    return fake_album_class


class AlbumFilterTestFiltering(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    """Test filtering of AlbumTreeView items"""

    TestConditions = namedtuple('TestConditions', ['text', 'filters', 'has_tags', 'matches'])
    StatusConditions = namedtuple('TestConditions', ['test_item', 'status_filter', 'filter_passes'])

    def test_album_filter_with_file_filters(self):
        """Verify the base class file-related filters still work"""

        test_file = get_test_data_path('test.flac')
        test_object = File(str(test_file))

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
            with self.subTest(f"Text={test.text}, filters={test.filters}", text=test.text, filters=test.filters):
                text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
                has_tags, matches = BaseTreeView._matches_file_properties(test_object, test.text, test.filters)
                self.assertEqual(has_tags, test.has_tags, text)
                self.assertEqual(matches, test.matches, text)

    def test_album_filter_with_no_file_filters(self):
        """Verify the base class file-related filters still work when not used"""

        test_file = get_test_data_path('test.flac')
        test_object = File(str(test_file))

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
            with self.subTest(f"Text={test.text}, filters={test.filters}", text=test.text, filters=test.filters):
                text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
                has_tags, matches = BaseTreeView._matches_file_properties(test_object, test.text, test.filters)
                self.assertEqual(has_tags, test.has_tags, text)
                self.assertEqual(matches, test.matches, text)

    def test_album_filter_with_metadata_filters(self):
        """Verify the base class metadata-related filters still work"""

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
            with self.subTest(f"Text={test.text}, filters={test.filters}", text=test.text, filters=test.filters):
                text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
                has_tags, matches = BaseTreeView._matches_metadata(test_object, test.text, test.filters)
                self.assertEqual(has_tags, test.has_tags, text)
                self.assertEqual(matches, test.matches, text)

    def test_album_filter_with_no_metadata_filters(self):
        """Verify the base class metadata-related filters still work when not used"""

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
            with self.subTest(f"Text={test.text}, filters={test.filters}", text=test.text, filters=test.filters):
                text = f"Error testing: filters={test.filters}  text={repr(test.text)}"
                has_tags, matches = BaseTreeView._matches_metadata(test_object, test.text, test.filters)
                self.assertEqual(has_tags, test.has_tags, text)
                self.assertEqual(matches, test.matches, text)

    def test_album_filter_with_status_filters(self):
        """Test the status filters (modified / complete)"""

        # Now add the combinations of album status
        test_combo_list: list[AlbumFilterTestFiltering.StatusConditions] = []
        for status_filter in [
            StatusFilters(False, False, False, False),
            StatusFilters(False, False, False, True),
            StatusFilters(False, False, True, False),
            StatusFilters(False, False, True, True),
            StatusFilters(False, True, False, False),
            StatusFilters(False, True, False, True),
            StatusFilters(False, True, True, False),
            StatusFilters(False, True, True, True),
            StatusFilters(True, False, False, False),
            StatusFilters(True, False, False, True),
            StatusFilters(True, False, True, False),
            StatusFilters(True, False, True, True),
            StatusFilters(True, True, False, False),
            StatusFilters(True, True, False, True),
            StatusFilters(True, True, True, False),
            StatusFilters(True, True, True, True),
        ]:
            for modified_state, complete_state in [(False, False), (False, True), (True, False), (True, True)]:
                filter_fails = False
                if not status_filter.modified:
                    filter_fails = modified_state
                if not filter_fails and not status_filter.unmodified:
                    filter_fails = not modified_state
                if not filter_fails and not status_filter.complete:
                    filter_fails = complete_state
                if not filter_fails and not status_filter.incomplete:
                    filter_fails = not complete_state

                status_test = AlbumFilterTestFiltering.StatusConditions(
                    test_item=create_fake_album(modified_state, complete_state),
                    status_filter=status_filter,
                    filter_passes=not filter_fails,
                )
                test_combo_list.append(status_test)

        for test in test_combo_list:
            with self.subTest(item=vars(test.test_item), filter=test.status_filter):
                text = f"Error testing: item={vars(test.test_item)}, filter={test.status_filter}"
                filter_matches = BaseTreeView._matches_status_filters(test.test_item, test.status_filter)
                self.assertEqual(filter_matches, test.filter_passes, text)

    def test_album_filter_with_non_album_item_passes(self):
        """Test that items that don't have a is_modified / is_complete func are not applicable"""

        status_test = AlbumFilterTestFiltering.StatusConditions(
            test_item=MultiMetadataProxy(Metadata()),
            status_filter=StatusFilters(False, False, False, False),
            filter_passes=True,
        )

        filter_matches = BaseTreeView._matches_status_filters(status_test.test_item, status_test.status_filter)
        self.assertEqual(filter_matches, status_test.filter_passes)

    def test_album_filter_with_both_status_and_text_filters(self):
        """Test the status filters (modified / complete) alongside the test filters
        to validate they work in concert without issue

        Test a populated text field that matches matches the filters
        """

        test_metadata = {
            'title': 'test_title',
            'artist': 'test_artist',
        }
        test_album = create_fake_album(True, False)
        test_album.metadata = MultiMetadataProxy(Metadata(test_metadata))

        mock_album_item = MagicMock()
        mock_album_item.obj = test_album
        mock_album_item.childCount.return_value = 0
        mock_parent = MagicMock()
        mock_parent.childCount.return_value = 1
        mock_parent.child.return_value = mock_album_item

        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent, "test", filters={'title'}, status_filters=StatusFilters(True, True, True, True)
            )
        )
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent, "test", filters={'title'}, status_filters=StatusFilters(False, True, True, True)
            )
        )
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent, "test", filters={'title'}, status_filters=StatusFilters(True, True, True, False)
            )
        )
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent, "not matched", filters={'title'}, status_filters=StatusFilters(True, True, True, True)
            )
        )
