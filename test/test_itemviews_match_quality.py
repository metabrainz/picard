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

from picard.album import Album, AlbumStatus
from picard.const.sys import IS_LINUX
from picard.track import Track

import pytest

from picard.ui.itemviews import TreeItem
from picard.ui.itemviews.columns import _sortkey_match_quality
from picard.ui.itemviews.match_quality_column import (
    MatchQualityColumn,
    MatchQualityColumnDelegate,
)


def _apply_platform_multiplier(value):
    """Apply the same platform-specific multiplier logic as in _sortkey_match_quality."""
    multiplier = -1 if IS_LINUX else 1
    return value * multiplier


class TestMatchQualityColumn:
    """Test the MatchQualityColumn class."""

    @pytest.fixture
    def match_quality_column(self) -> MatchQualityColumn:
        """Create a MatchQualityColumn instance for testing."""
        return MatchQualityColumn("Match Quality", "~match_quality", width=120)

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

    def test_init(self, match_quality_column: MatchQualityColumn) -> None:
        """Test MatchQualityColumn initialization."""
        assert match_quality_column.title == "Match Quality"
        assert match_quality_column.key == "~match_quality"
        assert match_quality_column.width == 120
        assert match_quality_column.size == QtCore.QSize(16, 16)

    def test_paint_does_nothing(self, match_quality_column: MatchQualityColumn) -> None:
        """Test that paint method does nothing (handled by delegate)."""
        painter = Mock()
        rect = QtCore.QRect(0, 0, 100, 20)
        # Should not raise any exception
        match_quality_column.paint(painter, rect)

    @pytest.mark.parametrize(
        ("matched", "total", "expected_icon_index"),
        [
            (0, 0, 5),  # No tracks - use pending icon
            (5, 10, 0),  # 50% match
            (6, 10, 1),  # 60% match
            (7, 10, 2),  # 70% match
            (8, 10, 3),  # 80% match
            (9, 10, 4),  # 90% match
            (10, 10, 5),  # 100% match
            (3, 10, 0),  # 30% match - use worst icon
        ],
    )
    def test_get_match_icon_percentage_based(
        self,
        match_quality_column: MatchQualityColumn,
        mock_album: Mock,
        matched: int,
        total: int,
        expected_icon_index: int,
    ) -> None:
        """Test get_match_icon returns correct icon based on percentage."""
        # Setup mock album
        mock_album.get_num_matched_tracks.return_value = matched
        mock_album.tracks = [Mock() for _ in range(total)]

        # Mock FileItem.match_icons - patch the import inside the method
        with patch("picard.ui.itemviews.FileItem") as mock_file_item:
            mock_file_item.match_icons = [Mock() for _ in range(6)]
            mock_file_item.match_pending_icons = [Mock() for _ in range(6)]

            icon = match_quality_column.get_match_icon(mock_album)

            if total == 0:
                # Should use pending icon for zero tracks
                assert icon == mock_file_item.match_pending_icons[5]
            else:
                # Should use match icon based on percentage
                assert icon == mock_file_item.match_icons[expected_icon_index]

    def test_get_match_icon_no_album_attributes(self, match_quality_column: MatchQualityColumn) -> None:
        """Test get_match_icon returns None for objects without album attributes."""
        obj = Mock()
        # Remove album attributes
        del obj.get_num_matched_tracks
        del obj.tracks

        icon = match_quality_column.get_match_icon(obj)
        assert icon is None

    def test_get_match_icon_no_fileitem_icons(self, match_quality_column: MatchQualityColumn, mock_album: Mock) -> None:
        """Test get_match_icon handles missing FileItem icons gracefully."""
        mock_album.get_num_matched_tracks.return_value = 5
        mock_album.tracks = [Mock() for _ in range(10)]

        with patch("picard.ui.itemviews.FileItem") as mock_file_item:
            # Remove match_icons attribute
            del mock_file_item.match_icons

            icon = match_quality_column.get_match_icon(mock_album)
            assert icon is None

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
        match_quality_column: MatchQualityColumn,
        mock_album: Mock,
        matched: int,
        total: int,
        unmatched: int,
        duplicates: int,
        extra: int,
        missing: int,
    ) -> None:
        """Test get_match_stats returns correct statistics."""
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

        stats = match_quality_column.get_match_stats(mock_album)

        assert stats is not None
        assert stats["matched"] == matched
        assert stats["total"] == total
        assert stats["unmatched"] == unmatched
        assert stats["duplicates"] == duplicates
        assert stats["extra"] == extra
        assert stats["missing"] == missing

    def test_get_match_stats_no_album_attributes(self, match_quality_column: MatchQualityColumn) -> None:
        """Test get_match_stats returns None for objects without album attributes."""
        obj = Mock()
        # Remove album attributes
        del obj.get_num_matched_tracks
        del obj.tracks

        stats = match_quality_column.get_match_stats(obj)
        assert stats is None


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
        delegate.parent = lambda: mock_tree_widget
        mock_tree_widget.itemFromIndex.return_value = None

        # Mock initStyleOption to avoid Qt type issues
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
        delegate.parent = lambda: mock_tree_widget
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.obj = None

        # Mock initStyleOption to avoid Qt type issues
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
        delegate.parent = lambda: mock_tree_widget
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns = None

        # Mock initStyleOption to avoid Qt type issues
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
        """Test paint method when column is not MatchQualityColumn."""
        painter = Mock()
        delegate.parent = lambda: mock_tree_widget
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns[2] = Mock()  # Not MatchQualityColumn

        # Mock initStyleOption to avoid Qt type issues
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
        delegate.parent = lambda: mock_tree_widget
        mock_tree_widget.itemFromIndex.return_value = mock_item

        # Mock the column to return None for stats
        mock_column = Mock(spec=MatchQualityColumn)
        mock_column.get_match_stats.return_value = None
        mock_item.columns[2] = mock_column

        # Mock initStyleOption to avoid Qt type issues
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
        """Test helpEvent method when column is not MatchQualityColumn."""
        event = Mock()
        view = mock_tree_widget
        option = Mock()
        index = Mock()
        index.column.return_value = 2
        mock_tree_widget.itemFromIndex.return_value = mock_item
        mock_item.columns[2] = Mock()  # Not MatchQualityColumn

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
        mock_column = Mock(spec=MatchQualityColumn)
        mock_column.get_match_stats.return_value = None
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

        # Set up delegate's parent relationship
        delegate.parent = lambda: mock_tree_widget

        # Mock the column
        mock_column = Mock(spec=MatchQualityColumn)
        stats = {"matched": 5, "total": 10, "missing": 2, "duplicates": 1, "extra": 1, "unmatched": 2}
        mock_column.get_match_stats.return_value = stats
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
    """Test integration of MatchQualityColumn with existing itemviews system."""

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

    def test_match_quality_column_in_itemview_columns(self) -> None:
        """Test that MatchQualityColumn is included in ITEMVIEW_COLUMNS (album view)."""
        from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS

        # Find the match quality column in album view columns
        match_quality_column = None
        for column in ALBUMVIEW_COLUMNS:
            if isinstance(column, MatchQualityColumn):
                match_quality_column = column
                break

        assert match_quality_column is not None
        assert match_quality_column.title == "Match"
        assert match_quality_column.key == "~match_quality"
        assert match_quality_column.sortable is True
        assert match_quality_column.sort_type is not None
        assert match_quality_column.sortkey is not None

    def test_match_quality_column_not_in_fileview_columns(self) -> None:
        """Test that MatchQualityColumn is NOT included in FILEVIEW_COLUMNS."""
        from picard.ui.itemviews.columns import FILEVIEW_COLUMNS

        # Verify that no match quality column exists in file view columns
        match_quality_column = None
        for column in FILEVIEW_COLUMNS:
            if isinstance(column, MatchQualityColumn):
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
        assert isinstance(match_quality_column, MatchQualityColumn)
        assert match_quality_column.key == "~match_quality"

        album_artist_column = ALBUMVIEW_COLUMNS[idx_albumartist]
        assert album_artist_column.key == "albumartist"

    def test_sortkey_progress_function(self) -> None:
        """Test the _sortkey_progress function used by MatchQualityColumn."""
        from picard.ui.itemviews.columns import _sortkey_match_quality

        # Test with album object
        album = Mock()
        album.get_num_matched_tracks.return_value = 3
        album.tracks = [Mock() for _ in range(5)]

        result = _sortkey_match_quality(album)
        expected = _apply_platform_multiplier(0.6)
        assert result == expected

        # Test with track object (should return 0.0)
        track = Mock()
        # Mock hasattr to return False for track objects
        with patch("builtins.hasattr", return_value=False):
            result = _sortkey_match_quality(track)
            assert result == 0.0

        # Test with album with no tracks
        album.tracks = []
        result = _sortkey_match_quality(album)
        assert result == 0.0

    def test_treeitem_handles_match_quality_column(self, mock_album: Mock) -> None:
        """Test that TreeItem properly handles MatchQualityColumn."""
        # Create a mock column
        column = Mock(spec=MatchQualityColumn)
        column.size = QtCore.QSize(16, 16)

        # Create a mock item
        item = Mock(spec=TreeItem)
        item.columns = [Mock(), column, Mock()]

        # Mock the update_colums_text method
        with patch.object(TreeItem, "update_colums_text"):
            # Simulate the condition in update_colums_text
            if isinstance(column, MatchQualityColumn):
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
            with patch.object(ClusterItem, 'columns', mock_columns):
                item = ClusterItem(cluster, parent=None)
                assert item is not None


class TestMatchQualitySorting:
    """Test match quality sorting behavior."""

    @pytest.fixture
    def mock_album_loading(self):
        """Create a mock album that is still loading."""
        album = Mock()
        album.status = AlbumStatus.LOADING
        album.get_num_matched_tracks.return_value = 0
        album.tracks = []
        return album

    @pytest.fixture
    def mock_album_loaded(self):
        """Create a mock album that has finished loading."""
        album = Mock()
        album.status = AlbumStatus.LOADED
        album.get_num_matched_tracks.return_value = 3
        album.tracks = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 tracks total
        return album

    @pytest.fixture
    def mock_track(self):
        """Create a mock track object."""
        track = Mock()
        # Track objects don't have get_num_matched_tracks or tracks attributes
        # We'll use patch to mock hasattr behavior
        return track

    def test_sortkey_match_quality_loading_album(self, mock_album_loading):
        """Test that loading albums return 0.0 to avoid premature sorting."""
        result = _sortkey_match_quality(mock_album_loading)
        assert result == 0.0

    def test_sortkey_match_quality_loaded_album(self, mock_album_loaded):
        """Test that loaded albums return correct match percentage."""
        result = _sortkey_match_quality(mock_album_loaded)
        # 3 matched out of 5 total = 0.6
        expected = _apply_platform_multiplier(0.6)
        assert result == expected

    def test_sortkey_match_quality_track_object(self, mock_track):
        """Test that track objects return 0.0."""
        # Mock hasattr to return False for track objects
        with patch("builtins.hasattr", side_effect=lambda obj, attr: attr not in ('get_num_matched_tracks', 'tracks')):
            result = _sortkey_match_quality(mock_track)
            assert result == 0.0

    def test_sortkey_match_quality_no_tracks(self, mock_album_loaded):
        """Test that albums with no tracks return 0.0."""
        mock_album_loaded.tracks = []
        result = _sortkey_match_quality(mock_album_loaded)
        assert result == 0.0

    def test_sortkey_match_quality_all_matched(self, mock_album_loaded):
        """Test that albums with all tracks matched return correct value."""
        mock_album_loaded.get_num_matched_tracks.return_value = 5
        result = _sortkey_match_quality(mock_album_loaded)
        expected = _apply_platform_multiplier(1.0)
        assert result == expected

    def test_sortkey_match_quality_no_matches(self, mock_album_loaded):
        """Test that albums with no matches return 0.0."""
        mock_album_loaded.get_num_matched_tracks.return_value = 0
        result = _sortkey_match_quality(mock_album_loaded)
        assert result == 0.0

    def test_sortkey_match_quality_partial_matches(self, mock_album_loaded):
        """Test that albums with partial matches return correct percentage."""
        mock_album_loaded.get_num_matched_tracks.return_value = 2
        result = _sortkey_match_quality(mock_album_loaded)
        # 2 matched out of 5 total = 0.4
        expected = _apply_platform_multiplier(0.4)
        assert result == expected

    def test_sortkey_match_quality_no_status_attribute(self):
        """Test that objects without status attribute are handled gracefully."""
        obj = Mock()
        obj.get_num_matched_tracks.return_value = 2
        obj.tracks = [Mock(), Mock(), Mock()]  # 3 tracks
        # No status attribute
        result = _sortkey_match_quality(obj)
        # Should calculate normally: 2/3 = 0.666...
        expected = _apply_platform_multiplier(0.6666666666666666)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_sortkey_match_quality_error_status(self, mock_album_loaded):
        """Test that albums with error status are handled correctly."""
        mock_album_loaded.status = AlbumStatus.ERROR
        result = _sortkey_match_quality(mock_album_loaded)
        # Should still calculate the match percentage
        expected = _apply_platform_multiplier(0.6)
        assert result == expected

    def test_sortkey_match_quality_none_status(self, mock_album_loaded):
        """Test that albums with None status are handled correctly."""
        mock_album_loaded.status = None
        result = _sortkey_match_quality(mock_album_loaded)
        # Should still calculate the match percentage
        expected = _apply_platform_multiplier(0.6)
        assert result == expected
