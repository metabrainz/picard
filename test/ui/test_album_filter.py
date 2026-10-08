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

from picard.ui.filter import AlbumStatusState
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
    StatusConditions = namedtuple('TestConditions', ['test_item', 'status_tuple', 'applies', 'filter_passes'])

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
        for filter_func_combo in [
            (AlbumStatusState.NOT_APPLICABLE, 'is_modified'),
            (AlbumStatusState.NOT_APPLICABLE, 'is_complete'),
            (AlbumStatusState.TRUE, 'is_modified'),
            (AlbumStatusState.TRUE, 'is_complete'),
            (AlbumStatusState.FALSE, 'is_modified'),
            (AlbumStatusState.FALSE, 'is_complete'),
        ]:
            for modified_state, complete_state in [(False, False), (False, True), (True, False), (True, True)]:
                filter_passes = False
                if filter_func_combo[0] == AlbumStatusState.NOT_APPLICABLE:
                    filter_passes = False
                elif filter_func_combo[1] == 'is_modified' and (
                    modified_state
                    and filter_func_combo[0] == AlbumStatusState.TRUE
                    or not modified_state
                    and filter_func_combo[0] == AlbumStatusState.FALSE
                ):
                    filter_passes = True
                elif filter_func_combo[1] == 'is_complete' and (
                    complete_state
                    and filter_func_combo[0] == AlbumStatusState.TRUE
                    or not complete_state
                    and filter_func_combo[0] == AlbumStatusState.FALSE
                ):
                    filter_passes = True

                status_test = AlbumFilterTestFiltering.StatusConditions(
                    test_item=create_fake_album(modified_state, complete_state),
                    status_tuple=filter_func_combo,
                    applies=bool(filter_func_combo[0] != AlbumStatusState.NOT_APPLICABLE),
                    filter_passes=filter_passes,
                )
                test_combo_list.append(status_test)

        for test in test_combo_list:
            with self.subTest(
                f"Item={vars(test.test_item)}",
                item=vars(test.test_item),
            ):
                (status_filter, status_func) = test.status_tuple
                with self.subTest(
                    f"Result of function {status_func} is being checked against filter {status_filter.name}",
                    filter=status_filter.name,
                    func=status_func,
                ):
                    text = f"Error testing: item={vars(test.test_item)}, filter={test.status_tuple}"
                    applies, filter_matches = BaseTreeView._matches_album_state(
                        test.test_item, status_filter, status_func
                    )
                    self.assertEqual(applies, test.applies, text)
                    self.assertEqual(filter_matches, test.filter_passes, text)

    def test_album_filter_with_item_without_status_func_is_not_applicable(self):
        """Test that items that don't have a is_modified / is_complete func are not applicable"""

        tests = [
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.NOT_APPLICABLE, 'is_modified')],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.NOT_APPLICABLE, 'is_complete')],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[
                    (AlbumStatusState.NOT_APPLICABLE, 'is_modified'),
                    (AlbumStatusState.NOT_APPLICABLE, 'is_complete'),
                ],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.TRUE, 'is_modified')],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.TRUE, 'is_complete')],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.TRUE, 'is_modified'), (AlbumStatusState.TRUE, 'is_complete')],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[
                    (AlbumStatusState.FALSE, 'is_modified'),
                ],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.FALSE, 'is_complete')],
                applies=False,
                filter_passes=False,
            ),
            self.StatusConditions(
                test_item=MultiMetadataProxy(Metadata()),
                status_tuple=[(AlbumStatusState.FALSE, 'is_modified'), (AlbumStatusState.FALSE, 'is_complete')],
                applies=False,
                filter_passes=False,
            ),
        ]

        for test in tests:
            with self.subTest(
                item=vars(test.test_item),
            ):
                for status_filter, status_func in test.status_tuple:
                    with self.subTest(
                        f"Result of function {status_func} is being checked against filter {status_filter}",
                        filter=status_filter.name,
                        func=status_func,
                    ):
                        text = f"Error testing: item={vars(test.test_item)}, filter={test.status_tuple}"
                        applies, filter_matches = BaseTreeView._matches_album_state(
                            test.test_item, status_filter, status_func
                        )
                        self.assertEqual(applies, test.applies, text)
                        self.assertEqual(filter_matches, test.filter_passes, text)

    def test_album_filter_with_both_status_and_text_filters__text_empty(self):
        """Test the status filters (modified / complete) alongside the test filters
        to validate they work in concert without issue

        Test with an empty text field and no text filters
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

        # Modified/Complete filter = N/A, Text filter = empty, text=""
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = N/A, Complete filter = TRUE, Text filter = empty, text=""
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = N/A, Complete filter = FALSE, Text filter = empty, text=""
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = N/A, Text filter = empty, text=""
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = TRUE, Complete filter = FALSE, Text filter = empty, text=""
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = TRUE, Text filter = empty, text=""
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = N/A, Text filter = empty, text=""
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = FALSE, Complete filter = TRUE, Text filter = empty, text=""
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = FALSE, Text filter = empty, text=""
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "",
                filters=set(),
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )

    def test_album_filter_with_both_status_and_text_filters___text_not_empty(self):
        """Test the status filters (modified / complete) alongside the test filters
        to validate they work in concert without issue

        Test a filled text field, but no text filters
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

        # Modified/Complete filter = N/A, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = N/A, Complete filter = TRUE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = N/A, Complete filter = FALSE, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = N/A, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = TRUE, Complete filter = FALSE, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = TRUE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = N/A, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = FALSE, Complete filter = TRUE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = FALSE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters=set(),
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )

    def test_album_filter_with_both_status_and_text_filters___text_filters_exist_match(self):
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

        # Modified/Complete filter = N/A, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = N/A, Complete filter = TRUE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = N/A, Complete filter = FALSE, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = N/A, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = TRUE, Complete filter = FALSE, Text filter = empty, text="test"
        self.assertTrue(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = TRUE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = N/A, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = FALSE, Complete filter = TRUE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = FALSE, Text filter = empty, text="test"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "test",
                filters={'title'},
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )

    def test_album_filter_with_both_status_and_text_filters___text_filters_exist_no_match(self):
        """Test the status filters (modified / complete) alongside the test filters
        to validate they work in concert without issue

        Test a populated text field that fails the text filters
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

        # Modified/Complete filter = N/A, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = N/A, Complete filter = TRUE, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = N/A, Complete filter = FALSE, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.NOT_APPLICABLE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = N/A, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = TRUE, Complete filter = FALSE, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
        # Modified filter = TRUE, Complete filter = TRUE, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.TRUE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = N/A, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.NOT_APPLICABLE,
            )
        )
        # Modified filter = FALSE, Complete filter = TRUE, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.TRUE,
            )
        )
        # Modified filter = FALSE, Complete filter = FALSE, Text filter = empty, text="not_match"
        self.assertFalse(
            BaseTreeView._filter_tree_items(
                mock_parent,
                "not_match",
                filters={'title'},
                modified_state_filter=AlbumStatusState.FALSE,
                complete_state_filter=AlbumStatusState.FALSE,
            )
        )
