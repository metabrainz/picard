# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Tests for mainwindow session filename functionality."""

from typing import Any
from unittest.mock import Mock

from picard.metadata import Metadata

import pytest

from picard.ui.mainwindow import MainWindow


@pytest.fixture
def mock_tagger() -> Mock:
    """Provide a mock tagger instance."""
    tagger = Mock()
    tagger.iter_all_files.return_value = []
    return tagger


@pytest.fixture
def mock_mainwindow(mock_tagger: Mock) -> Mock:
    """Provide a mock MainWindow instance with tagger."""
    mainwindow = Mock(spec=MainWindow)
    mainwindow.tagger = mock_tagger
    # Bind the actual method to the mock
    mainwindow._get_default_session_filename_from_metadata = (
        MainWindow._get_default_session_filename_from_metadata.__get__(mainwindow, MainWindow)
    )
    return mainwindow


@pytest.fixture
def mock_file_with_metadata() -> Mock:
    """Provide a mock file with metadata."""
    file_mock = Mock()
    file_mock.metadata = Metadata()
    return file_mock


@pytest.fixture
def artist_metadata_cases() -> list[dict[str, Any]]:
    """Provide test cases for different artist metadata scenarios."""
    return [
        # Case: artist tag present
        {'metadata': {'artist': 'The Beatles'}, 'expected': 'The Beatles', 'description': 'artist tag present'},
        # Case: albumartist tag present (should be used when artist is empty)
        {'metadata': {'albumartist': 'Pink Floyd'}, 'expected': 'Pink Floyd', 'description': 'albumartist tag present'},
        # Case: artists tag present (should be used when artist and albumartist are empty)
        {'metadata': {'artists': 'Led Zeppelin'}, 'expected': 'Led Zeppelin', 'description': 'artists tag present'},
        # Case: albumartists tag present (should be used when others are empty)
        {'metadata': {'albumartists': 'Queen'}, 'expected': 'Queen', 'description': 'albumartists tag present'},
        # Case: multiple artists with comma (should take first)
        {
            'metadata': {'artist': 'Artist1, Artist2, Artist3'},
            'expected': 'Artist1',
            'description': 'multiple artists with comma',
        },
        # Case: artist with path separators (should be replaced)
        {'metadata': {'artist': 'AC/DC'}, 'expected': 'AC_DC', 'description': 'artist with path separators'},
        # Case: artist with spaces (should remain unchanged)
        {
            'metadata': {'artist': 'The Rolling Stones'},
            'expected': 'The Rolling Stones',
            'description': 'artist with spaces',
        },
        # Case: artist with unicode characters
        {'metadata': {'artist': 'Björk'}, 'expected': 'Björk', 'description': 'artist with unicode characters'},
    ]


@pytest.fixture
def empty_metadata_cases() -> list[dict[str, Any]]:
    """Provide test cases for empty or invalid metadata scenarios."""
    return [
        # Case: empty metadata
        {'metadata': {}, 'expected': None, 'description': 'empty metadata'},
        # Case: empty string values
        {'metadata': {'artist': '', 'albumartist': ''}, 'expected': None, 'description': 'empty string values'},
        # Case: whitespace-only values
        {
            'metadata': {'artist': '   ', 'albumartist': '\t\n'},
            'expected': None,
            'description': 'whitespace-only values',
        },
        # Case: None values
        {'metadata': {'artist': None, 'albumartist': None}, 'expected': None, 'description': 'None values'},
    ]


@pytest.fixture
def priority_test_cases() -> list[dict[str, Any]]:
    """Provide test cases for tag priority (artist > albumartist > artists > albumartists)."""
    return [
        # Case: artist should take priority over albumartist
        {
            'metadata': {'artist': 'Artist1', 'albumartist': 'AlbumArtist1'},
            'expected': 'Artist1',
            'description': 'artist takes priority over albumartist',
        },
        # Case: albumartist should take priority over artists
        {
            'metadata': {'albumartist': 'AlbumArtist1', 'artists': 'Artists1'},
            'expected': 'AlbumArtist1',
            'description': 'albumartist takes priority over artists',
        },
        # Case: artists should take priority over albumartists
        {
            'metadata': {'artists': 'Artists1', 'albumartists': 'AlbumArtists1'},
            'expected': 'Artists1',
            'description': 'artists takes priority over albumartists',
        },
    ]


def test_get_default_session_filename_with_artist_metadata(
    mock_mainwindow: Mock, mock_file_with_metadata: Mock, artist_metadata_cases: list[dict[str, Any]]
) -> None:
    """Test session filename generation with various artist metadata scenarios."""
    for case in artist_metadata_cases:
        # Set up metadata
        metadata = Metadata()
        for tag, value in case['metadata'].items():
            metadata[tag] = value

        mock_file_with_metadata.metadata = metadata
        mock_mainwindow.tagger.iter_all_files.return_value = [mock_file_with_metadata]

        # Test the method
        result = mock_mainwindow._get_default_session_filename_from_metadata()

        assert result == case['expected'], f"Failed for case: {case['description']}"


def test_get_default_session_filename_with_empty_metadata(
    mock_mainwindow: Mock, mock_file_with_metadata: Mock, empty_metadata_cases: list[dict[str, Any]]
) -> None:
    """Test session filename generation with empty or invalid metadata."""
    for case in empty_metadata_cases:
        # Set up metadata
        metadata = Metadata()
        for tag, value in case['metadata'].items():
            if value is not None:
                metadata[tag] = value

        mock_file_with_metadata.metadata = metadata
        mock_mainwindow.tagger.iter_all_files.return_value = [mock_file_with_metadata]

        # Test the method
        result = mock_mainwindow._get_default_session_filename_from_metadata()

        assert result == case['expected'], f"Failed for case: {case['description']}"


def test_get_default_session_filename_tag_priority(
    mock_mainwindow: Mock, mock_file_with_metadata: Mock, priority_test_cases: list[dict[str, Any]]
) -> None:
    """Test that artist tags are checked in the correct priority order."""
    for case in priority_test_cases:
        # Set up metadata
        metadata = Metadata()
        for tag, value in case['metadata'].items():
            metadata[tag] = value

        mock_file_with_metadata.metadata = metadata
        mock_mainwindow.tagger.iter_all_files.return_value = [mock_file_with_metadata]

        # Test the method
        result = mock_mainwindow._get_default_session_filename_from_metadata()

        assert result == case['expected'], f"Failed for case: {case['description']}"


def test_get_default_session_filename_no_files(mock_mainwindow: Mock) -> None:
    """Test session filename generation when no files are present."""
    mock_mainwindow.tagger.iter_all_files.return_value = []

    result = mock_mainwindow._get_default_session_filename_from_metadata()

    assert result is None


def test_get_default_session_filename_multiple_files_uses_first(
    mock_mainwindow: Mock, mock_file_with_metadata: Mock
) -> None:
    """Test that the method returns the first valid artist found across multiple files."""
    # Create multiple files with different artists
    file1 = Mock()
    file1.metadata = Metadata()
    file1.metadata['artist'] = 'First Artist'

    file2 = Mock()
    file2.metadata = Metadata()
    file2.metadata['artist'] = 'Second Artist'

    mock_mainwindow.tagger.iter_all_files.return_value = [file1, file2]

    result = mock_mainwindow._get_default_session_filename_from_metadata()

    assert result == 'First Artist'


@pytest.mark.parametrize(
    "artist_value,expected",
    [
        ("Artist Name", "Artist Name"),  # Spaces are not sanitized
        ("Artist/Name", "Artist_Name"),  # Forward slash is sanitized
        ("Artist\\Name", "Artist_Name"),  # Backslash is sanitized
        ("Artist:Name", "Artist:Name"),  # Colon is not sanitized
        ("Artist*Name", "Artist*Name"),  # Asterisk is not sanitized
        ("Artist?Name", "Artist?Name"),  # Question mark is not sanitized
        ("Artist<Name", "Artist<Name"),  # Less than is not sanitized
        ("Artist>Name", "Artist>Name"),  # Greater than is not sanitized
        ("Artist|Name", "Artist|Name"),  # Pipe is not sanitized
        ("Artist\"Name", "Artist\"Name"),  # Quote is not sanitized
    ],
)
def test_get_default_session_filename_sanitization(
    mock_mainwindow: Mock, mock_file_with_metadata: Mock, artist_value: str, expected: str
) -> None:
    """Test that artist names are properly sanitized for filename use."""
    mock_file_with_metadata.metadata = Metadata()
    mock_file_with_metadata.metadata['artist'] = artist_value
    mock_mainwindow.tagger.iter_all_files.return_value = [mock_file_with_metadata]

    result = mock_mainwindow._get_default_session_filename_from_metadata()

    assert result == expected


def test_get_default_session_filename_whitespace_handling(mock_mainwindow: Mock, mock_file_with_metadata: Mock) -> None:
    """Test that whitespace is properly handled in artist names."""
    test_cases = [
        ("  Artist Name  ", "Artist Name"),  # Spaces are preserved
        ("Artist\tName", "Artist\tName"),  # Tabs are preserved
        ("Artist\nName", "Artist\nName"),  # Newlines are preserved
        ("Artist\rName", "Artist\rName"),  # Carriage returns are preserved
    ]

    for artist_value, expected in test_cases:
        mock_file_with_metadata.metadata = Metadata()
        mock_file_with_metadata.metadata['artist'] = artist_value
        mock_mainwindow.tagger.iter_all_files.return_value = [mock_file_with_metadata]

        result = mock_mainwindow._get_default_session_filename_from_metadata()

        assert result == expected, f"Failed for artist value: {repr(artist_value)}"
