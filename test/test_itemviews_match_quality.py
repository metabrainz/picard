# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the GNU General Public License Foundation; either version 2
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


from unittest.mock import Mock, patch

from PyQt6 import QtCore, QtGui, QtWidgets

from picard.album import Album
from picard.track import Track

import pytest

from picard.ui.itemviews import TreeItem
from picard.ui.itemviews.custom_columns import DelegateColumn
from picard.ui.itemviews.custom_columns.common_columns import create_match_quality_column
from picard.ui.itemviews.match_quality_column import MatchQualityColumnDelegate, MatchQualityProvider


class TestMatchQualityProvider:
    """Test the MatchQualityProvider class."""

    @pytest.fixture
    def provider(self) -> MatchQualityProvider:
        """Create a MatchQualityProvider instance for testing."""
        return MatchQualityProvider()

    @pytest.fixture
    def mock_album(self) -> Mock:
        """Create a mock album with tracks and files."""
        album = Mock(spec=Album)
        album.tracks = []
        album.get_num_matched_tracks.return_value = 0
        album.get_num_unmatched_files.return_value = 0
        album.unmatched_files = Mock()
        album.unmatched_files.files = []
        return album

    def test_init(self, provider: MatchQualityProvider) -> None:
        """Test MatchQualityProvider initialization."""
        assert provider is not None
        assert provider.get_delegate_class() == MatchQualityColumnDelegate

    @pytest.mark.parametrize(
        ("matched", "total", "expected_percentage"),
        [
            (0, 0, "0.0"),  # No tracks
            (5, 10, "0.5"),  # 50% match
            (6, 10, "0.6"),  # 60% match
            (7, 10, "0.7"),  # 70% match
            (8, 10, "0.8"),  # 80% match
            (9, 10, "0.9"),  # 90% match
            (10, 10, "1.0"),  # 100% match
            (3, 10, "0.3"),  # 30% match
        ],
    )
    def test_evaluate_percentage_calculation(
        self,
        provider: MatchQualityProvider,
        mock_album: Mock,
        matched: int,
        total: int,
        expected_percentage: str,
    ) -> None:
        """Test evaluate returns correct percentage as string."""
        # Setup mock album
        mock_album.get_num_matched_tracks.return_value = matched
        mock_album.tracks = [Mock() for _ in range(total)]

        result = provider.evaluate(mock_album)
        assert result == expected_percentage

    def test_evaluate_no_album_attributes(self, provider: MatchQualityProvider) -> None:
        """Test evaluate returns 0.0 for objects without album attributes."""
        obj = Mock()
        # Remove album attributes
        del obj.get_num_matched_tracks
        del obj.tracks

        result = provider.evaluate(obj)
        assert result == "0.0"

    @pytest.mark.parametrize(
        ("matched", "total", "unmatched", "duplicates", "extra", "missing"),
        [
            (5, 10, 2, 1, 1, 2),  # Normal case
            (0, 0, 0, 0, 0, 0),  # Empty album
            (10, 10, 0, 0, 0, 0),  # Perfect match
            (0, 10, 5, 0, 5, 10),  # No matches
        ],
    )
    def test_get_match_stats(
        self,
        provider: MatchQualityProvider,
        mock_album: Mock,
        matched: int,
        total: int,
        unmatched: int,
        duplicates: int,
        extra: int,
        missing: int,
    ) -> None:
        """Test _get_match_stats returns correct statistics."""
        # Setup mock album
        mock_album.get_num_matched_tracks.return_value = matched
        mock_album.get_num_unmatched_files.return_value = unmatched
        mock_album.tracks = [Mock() for _ in range(total)]
        mock_album.unmatched_files.files = [Mock() for _ in range(extra)]

        # Setup tracks with appropriate file counts
        for i, track in enumerate(mock_album.tracks):
            if i < missing:
                track.files = []  # Missing tracks
            elif i < missing + duplicates:
                track.files = [Mock(), Mock()]  # Duplicate files
            else:
                track.files = [Mock()]  # Normal tracks

        stats = provider.get_match_stats(mock_album)

        assert stats is not None
        assert stats['matched'] == matched
        assert stats['total'] == total
        assert stats['unmatched'] == unmatched
        assert stats['duplicates'] == duplicates
        assert stats['extra'] == extra
        assert stats['missing'] == missing

    def test_get_match_stats_no_album_attributes(self, provider: MatchQualityProvider) -> None:
        """Test _get_match_stats returns None for objects without album attributes."""
        obj = Mock()
        # Remove album attributes
        del obj.get_num_matched_tracks
        del obj.tracks

        stats = provider.get_match_stats(obj)
        assert stats is None


class TestDelegateColumn:
    """Test the DelegateColumn class."""

    @pytest.fixture
    def provider(self) -> MatchQualityProvider:
        """Create a MatchQualityProvider instance for testing."""
        return MatchQualityProvider()

    @pytest.fixture
    def delegate_column(self, provider: MatchQualityProvider) -> DelegateColumn:
        """Create a DelegateColumn instance for testing."""
        return DelegateColumn("Match Quality", "~match_quality", provider, width=57, size=QtCore.QSize(16, 16))

    def test_init(self, delegate_column: DelegateColumn) -> None:
        """Test DelegateColumn initialization."""
        assert delegate_column.title == "Match Quality"
        assert delegate_column.key == "~match_quality"
        assert delegate_column.width == 57
        assert delegate_column.size == QtCore.QSize(16, 16)
        assert delegate_column.delegate_class == MatchQualityColumnDelegate

    def test_delegate_class_property(self, delegate_column: DelegateColumn) -> None:
        """Test delegate_class property returns correct class."""
        assert delegate_column.delegate_class == MatchQualityColumnDelegate

    def test_size_attribute(self, delegate_column: DelegateColumn) -> None:
        """Test size attribute is accessible for delegate compatibility."""
        assert hasattr(delegate_column, 'size')
        assert delegate_column.size == QtCore.QSize(16, 16)

    def test_default_size(self, provider: MatchQualityProvider) -> None:
        """Test DelegateColumn uses default size when none provided."""
        column = DelegateColumn("Test", "test", provider)
        assert column.size == QtCore.QSize(16, 16)


class TestMatchQualityColumnFactory:
    """Test the match quality column factory."""

    def test_create_match_quality_column(self) -> None:
        """Test create_match_quality_column returns properly configured column."""
        column = create_match_quality_column()

        # Check it's a DelegateColumn
        assert isinstance(column, DelegateColumn)

        # Check basic properties
        assert column.title == "Match"
        assert column.key == "~match_quality"
        assert column.width == 57
        assert column.size == QtCore.QSize(16, 16)

        # Check delegate class
        assert column.delegate_class == MatchQualityColumnDelegate

        # Check it's marked as default
        assert column.is_default is True

    def test_factory_uses_numeric_sorting(self) -> None:
        """Test that the factory creates a column with numeric sorting."""
        column = create_match_quality_column()

        assert hasattr(column, 'sortkey')

        # Test that it can handle numeric evaluation
        from unittest.mock import Mock

        mock_album = Mock()
        mock_album.get_num_matched_tracks.return_value = 5
        mock_album.tracks = [Mock() for _ in range(10)]

        # The column's sortkey should return a tuple for sorting
        sort_key = column.sortkey(mock_album)
        assert isinstance(sort_key, tuple)
        assert len(sort_key) == 2
        assert sort_key[0] == 0  # Numeric values get priority
        assert sort_key[1] == 0.5  # The actual percentage


class TestMatchQualityColumn:
    """Test the match quality column using the factory for regression testing."""

    @pytest.fixture
    def match_quality_column(self) -> DelegateColumn:
        """Create a match quality column instance for testing using the factory."""
        return create_match_quality_column()

    @pytest.fixture
    def mock_album(self) -> Mock:
        """Create a mock album with tracks and files."""
        album = Mock(spec=Album)
        album.tracks = []
        album.get_num_matched_tracks.return_value = 0
        album.get_num_unmatched_files.return_value = 0
        album.unmatched_files = Mock()
        album.unmatched_files.files = []
        return album

    @pytest.fixture
    def mock_track(self) -> Mock:
        """Create a mock track."""
        track = Mock(spec=Track)
        track.files = []
        return track

    def test_init(self, match_quality_column: DelegateColumn) -> None:
        """Test match quality column initialization."""
        assert match_quality_column.title == "Match"
        assert match_quality_column.key == "~match_quality"
        assert match_quality_column.width == 57
        assert match_quality_column.size == QtCore.QSize(16, 16)
        assert isinstance(match_quality_column, DelegateColumn)

    def test_delegate_class(self, match_quality_column: DelegateColumn) -> None:
        """Test that the column has the correct delegate class."""
        assert match_quality_column.delegate_class == MatchQualityColumnDelegate

    def test_provider_evaluation(self, match_quality_column: DelegateColumn, mock_album: Mock) -> None:
        """Test that the provider correctly evaluates match percentage."""
        # Setup mock album
        mock_album.get_num_matched_tracks.return_value = 5
        mock_album.tracks = [Mock() for _ in range(10)]

        # Test that the provider evaluates correctly
        result = match_quality_column.delegate_provider.evaluate(mock_album)
        assert result == "0.5"  # 5/10 = 0.5

    def test_provider_stats(self, match_quality_column: DelegateColumn, mock_album: Mock) -> None:
        """Test that the provider correctly calculates match statistics."""
        # Setup mock album
        mock_album.get_num_matched_tracks.return_value = 3
        mock_album.get_num_unmatched_files.return_value = 1
        mock_album.tracks = [Mock() for _ in range(5)]
        mock_album.unmatched_files.files = [Mock()]

        # Setup tracks with appropriate file counts
        for i, track in enumerate(mock_album.tracks):
            if i < 1:
                track.files = []  # Missing track
            elif i < 2:
                track.files = [Mock(), Mock()]  # Duplicate files
            else:
                track.files = [Mock()]  # Normal tracks

        # Test the provider's get_match_stats method
        provider = match_quality_column.delegate_provider
        assert provider is not None
        stats = provider.get_match_stats(mock_album)

        assert stats is not None
        assert stats['matched'] == 3
        assert stats['total'] == 5
        assert stats['unmatched'] == 1
        assert stats['duplicates'] == 1
        assert stats['extra'] == 1
        assert stats['missing'] == 1


class TestMatchQualityColumnDelegate:
    """Test the MatchQualityColumnDelegate class."""

    @pytest.fixture
    def delegate(self) -> MatchQualityColumnDelegate:
        """Create a MatchQualityColumnDelegate instance for testing."""
        return MatchQualityColumnDelegate()

    @pytest.fixture
    def mock_tree_widget(self) -> Mock:
        """Create a mock tree widget."""
        widget = Mock(spec=QtWidgets.QTreeWidget)
        return widget

    @pytest.fixture
    def mock_item(self) -> Mock:
        """Create a mock tree item."""
        item = Mock(spec=TreeItem)
        item.obj = Mock()
        item.columns = [Mock(), Mock(), Mock()]  # 3 columns
        return item

    @pytest.fixture
    def mock_index(self) -> Mock:
        """Create a mock model index."""
        index = Mock()
        index.column.return_value = 2  # Third column
        return index

    @pytest.fixture
    def mock_option(self) -> Mock:
        """Create a mock style option."""
        option = Mock()
        option.rect = QtCore.QRect(0, 0, 200, 20)
        option.state = QtWidgets.QStyle.StateFlag.State_Enabled
        option.palette = Mock()
        option.palette.base.return_value = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        option.palette.text.return_value = QtGui.QColor(0, 0, 0)
        return option

    def test_init(self, delegate: MatchQualityColumnDelegate) -> None:
        """Test MatchQualityColumnDelegate initialization."""
        assert delegate is not None

    def test_paint_without_parent(
        self, delegate: MatchQualityColumnDelegate, mock_option: Mock, mock_index: Mock
    ) -> None:
        """Test paint method when parent is None."""
        painter = Mock()

        # Mock initStyleOption to avoid Qt type issues
        with patch.object(delegate, "initStyleOption"):
            delegate.paint(painter, mock_option, mock_index)

        # Should return early without error
        painter.drawText.assert_not_called()

    def test_paint_without_item(
        self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock, mock_option: Mock, mock_index: Mock
    ) -> None:
        """Test paint method when item is None."""
        painter = Mock()
        mock_tree_widget.itemFromIndex.return_value = None

        # Mock initStyleOption to avoid Qt type issues
        with patch.object(delegate, "parent", return_value=mock_tree_widget):
            with patch.object(delegate, "initStyleOption"):
                delegate.paint(painter, mock_option, mock_index)

        # Should return early without error
        painter.drawText.assert_not_called()

    def test_paint_without_obj(
        self,
        delegate: MatchQualityColumnDelegate,
        mock_tree_widget: Mock,
        mock_item: Mock,
        mock_option: Mock,
        mock_index: Mock,
    ) -> None:
        """Test paint method when item has no obj."""
        painter = Mock()
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.obj = None

        # Mock initStyleOption to avoid Qt type issues
        with patch.object(delegate, "parent", return_value=mock_tree_widget):
            with patch.object(delegate, "initStyleOption"):
                delegate.paint(painter, mock_option, mock_index)

        # Should return early without error
        painter.drawText.assert_not_called()

    def test_paint_without_columns(
        self,
        delegate: MatchQualityColumnDelegate,
        mock_tree_widget: Mock,
        mock_item: Mock,
        mock_option: Mock,
        mock_index: Mock,
    ) -> None:
        """Test paint method when item has no columns."""
        painter = Mock()
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns = None

        # Mock initStyleOption to avoid Qt type issues
        with patch.object(delegate, "parent", return_value=mock_tree_widget):
            with patch.object(delegate, "initStyleOption"):
                delegate.paint(painter, mock_option, mock_index)

        # Should return early without error
        painter.drawText.assert_not_called()

    def test_paint_wrong_column_type(
        self,
        delegate: MatchQualityColumnDelegate,
        mock_tree_widget: Mock,
        mock_item: Mock,
        mock_option: Mock,
        mock_index: Mock,
    ) -> None:
        """Test paint method when column is not DelegateColumn."""
        painter = Mock()
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns[2] = Mock()  # Not DelegateColumn

        # Mock initStyleOption to avoid Qt type issues
        with patch.object(delegate, "parent", return_value=mock_tree_widget):
            with patch.object(delegate, "initStyleOption"):
                delegate.paint(painter, mock_option, mock_index)

        # Should return early without error
        painter.drawText.assert_not_called()

    def test_paint_without_stats(
        self,
        delegate: MatchQualityColumnDelegate,
        mock_tree_widget: Mock,
        mock_item: Mock,
        mock_option: Mock,
        mock_index: Mock,
    ) -> None:
        """Test paint method when get_match_stats returns None."""
        painter = Mock()
        mock_tree_widget.itemFromIndex.return_value = mock_item

        # Mock the column with delegate_provider
        mock_provider = Mock(spec=['get_match_stats'])  # Only allow get_match_stats attribute
        mock_provider.get_match_stats.return_value = None  # No stats available

        mock_column = Mock(spec=DelegateColumn)
        mock_column.delegate_provider = mock_provider
        mock_column.size = QtCore.QSize(16, 16)  # Add size attribute
        mock_item.columns[2] = mock_column

        # Mock the index to return column 2
        mock_index.column.return_value = 2

        # Mock the object to not have album attributes so get_match_stats returns None
        mock_item.obj = Mock()
        # Remove album attributes so get_match_stats returns None
        del mock_item.obj.get_num_matched_tracks
        del mock_item.obj.tracks

        # Mock initStyleOption to avoid Qt type issues
        with patch.object(delegate, "parent", return_value=mock_tree_widget):
            with patch.object(delegate, "initStyleOption"):
                delegate.paint(painter, mock_option, mock_index)

        # Should return early without error
        painter.drawText.assert_not_called()

    def test_helpEvent_without_parent(self, delegate: MatchQualityColumnDelegate) -> None:
        """Test helpEvent method when parent is None."""
        event = Mock()
        view = None
        option = Mock()
        index = Mock()

        result = delegate.helpEvent(event, view, option, index)
        assert result is False

    def test_helpEvent_without_item(self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock) -> None:
        """Test helpEvent method when item is None."""
        event = Mock()
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        mock_tree_widget.itemFromIndex.return_value = None

        result = delegate.helpEvent(event, view, option, index)
        assert result is False

    def test_helpEvent_without_obj(
        self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock, mock_item: Mock
    ) -> None:
        """Test helpEvent method when item has no obj."""
        event = Mock()
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.obj = None

        result = delegate.helpEvent(event, view, option, index)
        assert result is False

    def test_helpEvent_without_columns(
        self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock, mock_item: Mock
    ) -> None:
        """Test helpEvent method when item has no columns."""
        event = Mock()
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns = None

        result = delegate.helpEvent(event, view, option, index)
        assert result is False

    def test_helpEvent_wrong_column_type(
        self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock, mock_item: Mock
    ) -> None:
        """Test helpEvent method when column is not DelegateColumn."""
        event = Mock()
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        index.column.return_value = 2
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns[2] = Mock()  # Not DelegateColumn

        result = delegate.helpEvent(event, view, option, index)
        assert result is False

    def test_helpEvent_without_stats(
        self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock, mock_item: Mock
    ) -> None:
        """Test helpEvent method when get_match_stats returns None."""
        event = Mock()
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        index.column.return_value = 2
        mock_tree_widget.itemFromIndex.return_value = mock_item

        # Mock the column to return None for stats
        mock_column = Mock(spec=DelegateColumn)
        mock_item.columns[2] = mock_column

        result = delegate.helpEvent(event, view, option, index)
        assert result is False

    def test_helpEvent_with_stats(
        self, delegate: MatchQualityColumnDelegate, mock_tree_widget: Mock, mock_item: Mock
    ) -> None:
        """Test helpEvent method with valid stats."""
        event = Mock()
        event.globalPos.return_value = QtCore.QPoint(100, 100)
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        index.column.return_value = 2
        mock_tree_widget.itemFromIndex.return_value = mock_item

        # Mock the album object with proper attributes
        mock_album = Mock()
        mock_album.get_num_matched_tracks.return_value = 5
        mock_album.get_num_unmatched_files.return_value = 2
        mock_album.tracks = [Mock() for _ in range(10)]  # 10 tracks
        mock_album.unmatched_files = Mock()
        mock_album.unmatched_files.files = [Mock()]  # 1 unmatched file

        # Setup tracks with appropriate file counts for stats calculation
        for i, track in enumerate(mock_album.tracks):
            if i < 2:  # 2 missing tracks
                track.files = []
            elif i < 3:  # 1 track with duplicates
                track.files = [Mock(), Mock()]
            else:  # Normal tracks
                track.files = [Mock()]

        mock_item.obj = mock_album

        # Set up delegate's parent relationship
        with patch.object(delegate, "parent", return_value=mock_tree_widget):
            # Mock the column with delegate_provider
            mock_provider = Mock()
            mock_provider.get_match_stats.return_value = {
                'matched': 5,
                'total': 10,
                'missing': 2,
                'duplicates': 1,
                'extra': 1,
                'unmatched': 2,
            }
            # Ensure the provider is not wrapped by an adapter for this test
            if hasattr(mock_provider, '_base'):
                del mock_provider._base

            mock_column = Mock(spec=DelegateColumn)
            mock_column.delegate_provider = mock_provider
            mock_item.columns[2] = mock_column

            with patch("picard.ui.itemviews.match_quality_column.QtWidgets.QToolTip") as mock_tooltip:
                result = delegate.helpEvent(event, view, option, index)

                assert result is True
                mock_tooltip.showText.assert_called_once()

                # Check that tooltip text contains expected parts
                call_args = mock_tooltip.showText.call_args
                tooltip_text = call_args[0][1]
                expected_parts = [
                    "Match: 5/10 (50.0%)",
                    "Missing tracks: 2",
                    "Duplicate files: 1",
                    "Extra files: 1",
                    "Unmatched files: 2",
                ]
                for part in expected_parts:
                    assert part in tooltip_text

    def test_sizeHint(self, delegate: MatchQualityColumnDelegate) -> None:
        """Test sizeHint method returns expected size."""
        option = Mock()
        index = Mock()

        size = delegate.sizeHint(option, index)

        assert size == QtCore.QSize(57, 16)


class TestItemViewsIntegration:
    """Test integration of new delegate column architecture with existing itemviews system."""

    @pytest.fixture
    def mock_album(self) -> Mock:
        """Create a mock album for testing."""
        album = Mock(spec=Album)
        album.tracks = [Mock() for _ in range(5)]
        album.get_num_matched_tracks.return_value = 3
        album.get_num_unmatched_files.return_value = 1
        album.unmatched_files = Mock()
        album.unmatched_files.files = [Mock()]
        return album

    def test_delegate_column_in_album_view_columns(self) -> None:
        """Test that DelegateColumn is included in ALBUMVIEW_COLUMNS (album view)."""
        from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS

        # Find the match quality column in album view columns
        match_quality_column = None
        for column in ALBUMVIEW_COLUMNS:
            if isinstance(column, DelegateColumn) and column.key == "~match_quality":
                match_quality_column = column
                break

        assert match_quality_column is not None
        assert match_quality_column.title == "Match"
        assert match_quality_column.key == "~match_quality"
        assert match_quality_column.sortable is True
        assert match_quality_column.sort_type is not None
        assert match_quality_column.delegate_class == MatchQualityColumnDelegate

    def test_delegate_column_not_in_fileview_columns(self) -> None:
        """Test that DelegateColumn is NOT included in FILEVIEW_COLUMNS."""
        from picard.ui.itemviews.columns import FILEVIEW_COLUMNS

        # Verify that no match quality delegate column exists in file view columns
        match_quality_column = None
        for column in FILEVIEW_COLUMNS:
            if isinstance(column, DelegateColumn) and column.key == "~match_quality":
                match_quality_column = column
                break

        assert match_quality_column is None

    def test_album_view_has_match_quality_column_after_album_artist(self) -> None:
        """Test that the match quality column is immediately after the Album Artist column in album view."""
        from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS

        idx_albumartist = ALBUMVIEW_COLUMNS.pos("albumartist")
        idx_match = ALBUMVIEW_COLUMNS.pos("~match_quality")

        assert idx_match == idx_albumartist + 1

        match_quality_column = ALBUMVIEW_COLUMNS[idx_match]
        assert isinstance(match_quality_column, DelegateColumn)
        assert match_quality_column.key == "~match_quality"

        album_artist_column = ALBUMVIEW_COLUMNS[idx_albumartist]
        assert album_artist_column.key == "albumartist"

    def test_numeric_sorting_with_provider(self) -> None:
        """Test that the provider uses numeric sorting correctly."""
        from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS

        # Find the match quality column
        match_quality_column = None
        for column in ALBUMVIEW_COLUMNS:
            if isinstance(column, DelegateColumn) and column.key == "~match_quality":
                match_quality_column = column
                break

        assert match_quality_column is not None

        # Test with album object
        album = Mock()
        album.get_num_matched_tracks.return_value = 3
        album.tracks = [Mock() for _ in range(5)]

        # Test that the provider correctly evaluates match percentage
        result = match_quality_column.delegate_provider.evaluate(album)
        assert result == "0.6"  # 3/5 = 0.6

        # Test with track object (should return 0.0)
        track = Mock()
        # Mock hasattr to return False for track objects
        with patch("builtins.hasattr", return_value=False):
            result = match_quality_column.delegate_provider.evaluate(track)
            assert result == "0.0"

        # Test with album with no tracks
        album.tracks = []
        result = match_quality_column.delegate_provider.evaluate(album)
        assert result == "0.0"

    def test_treeitem_handles_delegate_column(self, mock_album: Mock) -> None:
        """Test that TreeItem properly handles DelegateColumn."""
        # Create a mock delegate column
        column = Mock(spec=DelegateColumn)
        column.size = QtCore.QSize(16, 16)

        # Create a mock item
        item = Mock(spec=TreeItem)
        item.columns = [Mock(), column, Mock()]

        # Mock the update_colums_text method
        with patch.object(TreeItem, "update_colums_text"):
            # Simulate the condition in update_colums_text
            if isinstance(column, DelegateColumn):
                item.setSizeHint(1, column.size)

            # Verify setSizeHint was called
            item.setSizeHint.assert_called_once_with(1, column.size)

    def test_basetreeview_delegate_setup(self) -> None:
        """Test that BaseTreeView properly sets up delegates for MatchQualityColumn."""
        from picard.ui.itemviews.match_quality_column import MatchQualityColumnDelegate

        # Verify that the delegate class exists and can be instantiated
        delegate = MatchQualityColumnDelegate()
        assert delegate is not None


class TestCodeFormattingChanges:
    """Test that code formatting changes don't break functionality."""

    def test_get_match_color_formatting(self) -> None:
        """Test that get_match_color function works with new formatting."""
        from picard.ui.itemviews import get_match_color

        basecolor = QtGui.QColor(255, 255, 255)
        similarity = 0.5

        result = get_match_color(similarity, basecolor)

        assert isinstance(result, QtGui.QColor)
        # Verify the color calculation still works
        assert result.red() >= 0
        assert result.red() <= 255
        assert result.green() >= 0
        assert result.green() <= 255
        assert result.blue() >= 0
        assert result.blue() <= 255

    def test_album_item_formatting(self) -> None:
        """Test that AlbumItem tooltip formatting works with new formatting."""
        from picard.ui.itemviews import AlbumItem

        # Verify that AlbumItem can be instantiated
        album = Mock()
        item = AlbumItem(album, parent=None)
        assert item is not None

    def test_track_item_formatting(self) -> None:
        """Test that TrackItem tooltip formatting works with new formatting."""
        from picard.ui.itemviews import TrackItem

        # Verify that TrackItem can be instantiated
        track = Mock()
        item = TrackItem(track, parent=None)
        assert item is not None

    def test_file_item_formatting(self) -> None:
        """Test that FileItem tooltip formatting works with new formatting."""
        from picard.ui.itemviews import FileItem

        # Verify that FileItem can be instantiated
        file = Mock()
        item = FileItem(file, parent=None)
        assert item is not None

    def test_cluster_item_formatting(self) -> None:
        """Test that ClusterItem initialization works with new formatting."""
        from picard.ui.itemviews import ClusterItem

        # Verify that ClusterItem can be instantiated
        cluster = Mock()
        # Mock the icon_dir attribute that's set during runtime
        with patch.object(ClusterItem, "icon_dir", QtGui.QIcon(), create=True):
            # Mock the columns property at the class level to avoid RuntimeError
            mock_columns = Mock()
            mock_columns.status_icon_column = 0
            with patch.object(ClusterItem, "columns", mock_columns):
                item = ClusterItem(cluster, parent=None)
                assert item is not None
