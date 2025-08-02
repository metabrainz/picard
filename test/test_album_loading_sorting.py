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

from unittest.mock import Mock

from picard.album import AlbumStatus

import pytest

from picard.ui.itemviews.columns import _sortkey_match_quality


class TestAlbumLoadingSorting:
    """Test that sorting works correctly during album loading."""

    def test_sortkey_during_loading_returns_zero(self):
        """Test that sort key returns 0.0 when album is still loading."""
        album = Mock()
        album.status = AlbumStatus.LOADING
        album.get_num_matched_tracks.return_value = 3
        album.tracks = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 tracks

        result = _sortkey_match_quality(album)
        assert result == 0.0

    def test_sortkey_after_loading_returns_correct_percentage(self):
        """Test that sort key returns correct percentage after album is loaded."""
        album = Mock()
        album.status = AlbumStatus.LOADED
        album.get_num_matched_tracks.return_value = 3
        album.tracks = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 tracks

        result = _sortkey_match_quality(album)
        assert result == -0.6  # 3/5 = 0.6, but returned as negative for proper sorting

    def test_sortkey_no_status_attribute_works_normally(self):
        """Test that objects without status attribute work normally."""
        album = Mock()
        # No status attribute
        album.get_num_matched_tracks.return_value = 2
        album.tracks = [Mock(), Mock(), Mock()]  # 3 tracks

        result = _sortkey_match_quality(album)
        assert result == pytest.approx(-0.6666666666666666, rel=1e-10)  # 2/3 ≈ 0.666, but returned as negative

    def test_sortkey_error_status_works_normally(self):
        """Test that albums with error status work normally."""
        album = Mock()
        album.status = AlbumStatus.ERROR
        album.get_num_matched_tracks.return_value = 1
        album.tracks = [Mock(), Mock()]  # 2 tracks

        result = _sortkey_match_quality(album)
        assert result == -0.5  # 1/2 = 0.5, but returned as negative

    def test_sortkey_none_status_works_normally(self):
        """Test that albums with None status work normally."""
        album = Mock()
        album.status = None
        album.get_num_matched_tracks.return_value = 4
        album.tracks = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 tracks

        result = _sortkey_match_quality(album)
        assert result == -0.8  # 4/5 = 0.8, but returned as negative
