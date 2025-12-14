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

"""Tests for metadata handler."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from picard.file import File
from picard.metadata import Metadata
from picard.session.metadata_handler import MetadataHandler

import pytest


@pytest.fixture
def mock_file_with_metadata() -> Mock:
    """Provide a mock file with metadata."""
    file_mock = Mock(spec=File)
    metadata = Metadata()
    metadata['title'] = "Test Song"
    metadata['artist'] = "Test Artist"
    metadata['~internal'] = "internal_value"
    metadata['length'] = "123456"
    file_mock.metadata = metadata
    return file_mock


def test_serialize_metadata_for_file(mock_file_with_metadata: Mock) -> None:
    """Test metadata serialization excluding internal tags."""
    tags = MetadataHandler.serialize_metadata_for_file(mock_file_with_metadata)

    assert "title" in tags
    assert "artist" in tags
    assert "~internal" not in tags
    assert "length" not in tags
    assert tags['title'] == ["Test Song"]
    assert tags['artist'] == ["Test Artist"]


def test_serialize_metadata_empty_file() -> None:
    """Test metadata serialization for file with no metadata."""
    file_mock = Mock(spec=File)
    metadata = Mock(spec=Metadata)
    metadata.rawitems.return_value = []
    file_mock.metadata = metadata

    tags = MetadataHandler.serialize_metadata_for_file(file_mock)

    assert tags == {}


def test_serialize_metadata_with_multiple_values() -> None:
    """Test metadata serialization with multiple values per tag."""
    file_mock = Mock(spec=File)
    metadata = Mock(spec=Metadata)
    metadata.rawitems.return_value = [
        ("genre", ["Rock", "Pop"]),
        ("artist", ["Single Artist"]),
    ]
    file_mock.metadata = metadata

    tags = MetadataHandler.serialize_metadata_for_file(file_mock)

    assert tags['genre'] == ["Rock", "Pop"]
    assert tags['artist'] == ["Single Artist"]


def test_deserialize_metadata() -> None:
    """Test metadata deserialization."""
    tags = {'title': ["Test Song"], 'artist': ["Test Artist"]}

    metadata = MetadataHandler.deserialize_metadata(tags)

    assert metadata['title'] == "Test Song"
    assert metadata['artist'] == "Test Artist"


def test_deserialize_metadata_empty() -> None:
    """Test metadata deserialization with empty tags."""
    metadata = MetadataHandler.deserialize_metadata({})

    assert len(metadata) == 0


def test_deserialize_metadata_with_multiple_values() -> None:
    """Test metadata deserialization with multiple values per tag."""
    tags = {'genre': ["Rock", "Pop"], 'artist': ["Artist 1", "Artist 2"]}

    metadata = MetadataHandler.deserialize_metadata(tags)

    assert metadata['genre'] == "Rock; Pop"
    assert metadata['artist'] == "Artist 1; Artist 2"


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ("single_value", ["single_value"]),
        (["list", "values"], ["list", "values"]),
        (("tuple", "values"), ["tuple", "values"]),
        (123, [123]),
        (None, [None]),
        ([], []),
        ((), []),
    ],
)
def test_as_list(values: Any, expected: list[Any]) -> None:
    """Test as_list conversion with various input types."""
    result = MetadataHandler.as_list(values)
    assert result == expected


def test_safe_apply_metadata_success() -> None:
    """Test successful metadata application."""
    file_mock = Mock(spec=File)
    file_mock.metadata = Mock()
    file_mock.metadata.length = 123456
    file_mock.orig_metadata = Mock()
    file_mock.orig_metadata.length = 789012

    metadata = Metadata()
    metadata['title'] = "New Title"

    result = MetadataHandler.safe_apply_metadata(file_mock, metadata)

    assert result is True
    file_mock.copy_metadata.assert_called_once_with(metadata)
    file_mock.update.assert_called_once()
    assert metadata.length == 123456


def test_safe_apply_metadata_success_with_none_length() -> None:
    """Test successful metadata application with None length."""
    file_mock = Mock(spec=File)
    file_mock.metadata = Mock()
    file_mock.metadata.length = None
    file_mock.orig_metadata = Mock()
    file_mock.orig_metadata.length = 789012

    metadata = Metadata()
    metadata['title'] = "New Title"

    result = MetadataHandler.safe_apply_metadata(file_mock, metadata)

    assert result is True
    file_mock.copy_metadata.assert_called_once_with(metadata)
    file_mock.update.assert_called_once()
    assert metadata.length == 789012


@patch("picard.session.metadata_handler.log")
def test_safe_apply_metadata_attribute_error(mock_log: Mock) -> None:
    """Test metadata application with AttributeError."""
    file_mock = Mock(spec=File)
    file_mock.filename = str(Path("/test/file.mp3"))
    file_mock.metadata = Mock()
    file_mock.metadata.length = None
    file_mock.orig_metadata = Mock()
    file_mock.orig_metadata.length = 789012
    file_mock.copy_metadata.side_effect = AttributeError("Test error")

    metadata = Metadata()

    result = MetadataHandler.safe_apply_metadata(file_mock, metadata)

    assert result is False
    mock_log.warning.assert_called_once()
    assert "Test error" in str(mock_log.warning.call_args)


@patch("picard.session.metadata_handler.log")
def test_safe_apply_metadata_key_error(mock_log: Mock) -> None:
    """Test metadata application with KeyError."""
    file_mock = Mock(spec=File)
    file_mock.filename = str(Path("/test/file.mp3"))
    file_mock.metadata = Mock()
    file_mock.metadata.length = None
    file_mock.orig_metadata = Mock()
    file_mock.orig_metadata.length = 789012
    file_mock.copy_metadata.side_effect = KeyError("Test error")

    metadata = Metadata()

    result = MetadataHandler.safe_apply_metadata(file_mock, metadata)

    assert result is False
    mock_log.warning.assert_called_once()
    assert "Test error" in str(mock_log.warning.call_args)


@patch("picard.session.metadata_handler.log")
def test_safe_apply_metadata_unexpected_error(mock_log: Mock) -> None:
    """Test metadata application with unexpected error."""
    file_mock = Mock(spec=File)
    file_mock.filename = str(Path("test_file.mp3"))
    file_mock.metadata = Mock()
    file_mock.metadata.length = None
    file_mock.orig_metadata = Mock()
    file_mock.orig_metadata.length = 789012
    file_mock.copy_metadata.side_effect = OSError("File system error")

    metadata = Metadata()

    result = MetadataHandler.safe_apply_metadata(file_mock, metadata)

    assert result is False
    mock_log.error.assert_called_once()
    assert "File system error" in str(mock_log.error.call_args)


@patch("picard.session.retry_helper.RetryHelper")
def test_apply_saved_metadata_if_any_file_pending(mock_retry_helper: Mock) -> None:
    """Test applying saved metadata with file in PENDING state."""
    tagger_mock = Mock()
    file_mock = Mock(spec=File)
    file_mock.state = File.State.PENDING

    tagger_mock.files.get.return_value = file_mock

    metadata_map = {Path("/test/file.mp3"): Metadata()}

    MetadataHandler.apply_saved_metadata_if_any(tagger_mock, metadata_map)

    mock_retry_helper.retry_until.assert_called_once()


@patch("picard.session.retry_helper.RetryHelper")
def test_apply_saved_metadata_if_any_file_not_found(mock_retry_helper: Mock) -> None:
    """Test applying saved metadata when file is not found."""
    tagger_mock = Mock()
    tagger_mock.files.get.return_value = None

    metadata_map = {Path("/test/file.mp3"): Metadata()}

    MetadataHandler.apply_saved_metadata_if_any(tagger_mock, metadata_map)

    mock_retry_helper.retry_until.assert_called_once()


@patch("picard.session.retry_helper.RetryHelper")
def test_apply_saved_metadata_if_any_file_ready_success(mock_retry_helper: Mock) -> None:
    """Test applying saved metadata when file is ready and application succeeds."""
    tagger_mock = Mock()
    file_mock = Mock(spec=File)
    file_mock.state = 1  # Not PENDING (PENDING = 0)

    tagger_mock.files.get.return_value = file_mock

    metadata = Metadata()
    metadata_map = {Path("/test/file.mp3"): metadata}

    with patch.object(MetadataHandler, "safe_apply_metadata", return_value=True):
        MetadataHandler.apply_saved_metadata_if_any(tagger_mock, metadata_map)

    # Should not retry if file is ready and metadata applied successfully
    mock_retry_helper.retry_until.assert_not_called()


@patch("picard.session.retry_helper.RetryHelper")
def test_apply_saved_metadata_if_any_file_ready_failure(mock_retry_helper: Mock) -> None:
    """Test applying saved metadata when file is ready but application fails."""
    tagger_mock = Mock()
    file_mock = Mock(spec=File)
    file_mock.state = 1  # Not PENDING (PENDING = 0)

    tagger_mock.files.get.return_value = file_mock

    metadata = Metadata()
    metadata_map = {Path("/test/file.mp3"): metadata}

    with patch.object(MetadataHandler, "safe_apply_metadata", return_value=False):
        MetadataHandler.apply_saved_metadata_if_any(tagger_mock, metadata_map)

    # Should retry if metadata application failed
    mock_retry_helper.retry_until.assert_called_once()


@patch("picard.session.retry_helper.RetryHelper")
def test_apply_saved_metadata_if_any_mixed_states(mock_retry_helper: Mock) -> None:
    """Test applying saved metadata with files in different states."""
    tagger_mock = Mock()

    # File 1: ready and successful
    file1_mock = Mock(spec=File)
    file1_mock.state = 1  # Not PENDING (PENDING = 0)

    # File 2: pending
    file2_mock = Mock(spec=File)
    file2_mock.state = File.State.PENDING

    # File 3: ready but failed
    file3_mock = Mock(spec=File)
    file3_mock.state = 1  # Not PENDING (PENDING = 0)

    def files_getter(path):
        if str(path) == "/test/file1.mp3":
            return file1_mock
        elif str(path) == "/test/file2.mp3":
            return file2_mock
        elif str(path) == "/test/file3.mp3":
            return file3_mock
        return None

    tagger_mock.files.get.side_effect = files_getter

    metadata_map = {
        Path("/test/file1.mp3"): Metadata(),
        Path("/test/file2.mp3"): Metadata(),
        Path("/test/file3.mp3"): Metadata(),
    }

    with patch.object(MetadataHandler, "safe_apply_metadata", side_effect=[True, False]):
        MetadataHandler.apply_saved_metadata_if_any(tagger_mock, metadata_map)

    # Should retry for file2 (pending) and file3 (failed)
    mock_retry_helper.retry_until.assert_called_once()
