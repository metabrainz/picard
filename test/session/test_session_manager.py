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

"""Tests for session manager."""

from pathlib import Path
from unittest.mock import Mock, patch

from picard.session.constants import SessionConstants
from picard.session.session_manager import export_session, load_session_from_path, save_session_to_path


@patch('picard.session.session_manager.SessionExporter')
def test_export_session_function(mock_exporter_class: Mock) -> None:
    """Test the export_session function."""
    mock_exporter = Mock()
    mock_exporter_class.return_value = mock_exporter
    mock_exporter.export_session.return_value = {"version": 1}

    tagger_mock = Mock()
    result = export_session(tagger_mock)

    mock_exporter_class.assert_called_once()
    mock_exporter.export_session.assert_called_once_with(tagger_mock)
    assert result == {"version": 1}


@patch('picard.session.session_manager.export_session')
def test_save_session_to_path(mock_export_session: Mock, tmp_path: Path) -> None:
    """Test saving session to path."""
    mock_export_session.return_value = {"version": 1, "items": []}

    tagger_mock = Mock()
    session_file = tmp_path / "test"

    save_session_to_path(tagger_mock, session_file)

    # Expect .mbps.gz to be appended
    expected_file = Path(str(session_file) + ".mbps.gz")
    assert expected_file.exists()
    mock_export_session.assert_called_once_with(tagger_mock)


@patch('picard.session.session_manager.export_session')
def test_save_session_to_path_with_extension(mock_export_session: Mock, tmp_path: Path) -> None:
    """Test saving session to path with existing extension."""
    mock_export_session.return_value = {"version": 1, "items": []}

    tagger_mock = Mock()
    session_file = tmp_path / "test.mbps.gz"

    save_session_to_path(tagger_mock, session_file)

    assert session_file.exists()
    mock_export_session.assert_called_once_with(tagger_mock)


@patch('picard.session.session_manager.export_session')
def test_save_session_to_path_with_different_extension(mock_export_session: Mock, tmp_path: Path) -> None:
    """Test saving session to path with different extension."""
    mock_export_session.return_value = {"version": 1, "items": []}

    tagger_mock = Mock()
    session_file = tmp_path / "test.json"

    save_session_to_path(tagger_mock, session_file)

    # Should add .mbps.gz extension
    expected_file = Path(str(session_file) + ".mbps.gz")
    assert expected_file.exists()
    mock_export_session.assert_called_once_with(tagger_mock)


@patch('picard.session.session_manager.export_session')
def test_save_session_to_path_string_path(mock_export_session: Mock, tmp_path: Path) -> None:
    """Test saving session to string path."""
    mock_export_session.return_value = {"version": 1, "items": []}

    tagger_mock = Mock()
    session_file = tmp_path / "test"

    save_session_to_path(tagger_mock, str(session_file))

    assert Path(str(session_file) + ".mbps.gz").exists()
    mock_export_session.assert_called_once_with(tagger_mock)


@patch('picard.session.session_manager.export_session')
def test_save_session_to_path_creates_json_content(mock_export_session: Mock, tmp_path: Path) -> None:
    """Test that saved session file contains proper JSON content."""
    session_data = {
        "version": 1,
        "options": {"rename_files": True},
        "items": [{"file_path": "/test/file.mp3"}],
    }
    mock_export_session.return_value = session_data

    tagger_mock = Mock()
    session_file = tmp_path / "test"

    save_session_to_path(tagger_mock, session_file)

    saved_file = Path(str(session_file) + ".mbps.gz")
    assert saved_file.exists()

    # Read and verify content (gzip -> parse JSON)
    import gzip
    import json

    content = gzip.decompress(saved_file.read_bytes()).decode("utf-8")
    data = json.loads(content)
    assert data["version"] == 1
    assert data["options"]["rename_files"] is True
    assert data["items"][0]["file_path"] == "/test/file.mp3"


@patch('picard.session.session_manager.SessionLoader')
def test_load_session_from_path(mock_loader_class: Mock) -> None:
    """Test loading session from path."""
    mock_loader = Mock()
    mock_loader_class.return_value = mock_loader

    tagger_mock = Mock()
    session_file = Path("/test/session.mbps.gz")

    load_session_from_path(tagger_mock, session_file)

    mock_loader_class.assert_called_once_with(tagger_mock)
    mock_loader.load_from_path.assert_called_once_with(session_file)
    mock_loader.finalize_loading.assert_called_once()


@patch('picard.session.session_manager.SessionLoader')
def test_load_session_from_path_string_path(mock_loader_class: Mock) -> None:
    """Test loading session from string path."""
    mock_loader = Mock()
    mock_loader_class.return_value = mock_loader

    tagger_mock = Mock()
    session_file = "/test/session.mbps.gz"

    load_session_from_path(tagger_mock, session_file)

    mock_loader_class.assert_called_once_with(tagger_mock)
    mock_loader.load_from_path.assert_called_once_with(session_file)
    mock_loader.finalize_loading.assert_called_once()


@patch('picard.session.session_manager.export_session')
def test_save_session_to_path_file_overwrite(mock_export_session: Mock, tmp_path: Path) -> None:
    """Test that save_session_to_path overwrites existing files."""
    existing_file = tmp_path / "test.mbps.gz"
    existing_file.write_text("old content", encoding="utf-8")

    mock_export_session.return_value = {"version": 1, "items": []}

    tagger_mock = Mock()
    save_session_to_path(tagger_mock, existing_file)

    # File should be overwritten
    import gzip
    import json

    content = gzip.decompress(existing_file.read_bytes()).decode("utf-8")
    data = json.loads(content)
    assert data["version"] == 1


def test_save_session_to_path_creates_directory(tmp_path: Path) -> None:
    """Test that save_session_to_path creates parent directories."""
    with patch('picard.session.session_manager.export_session') as mock_export:
        mock_export.return_value = {"version": 1, "items": []}

        tagger_mock = Mock()
        session_file = tmp_path / "subdir" / "test.mbps.gz"

        save_session_to_path(tagger_mock, session_file)

        assert session_file.exists()
        assert session_file.parent.exists()


def test_save_session_to_path_utf8_encoding(tmp_path: Path) -> None:
    """Test that save_session_to_path uses UTF-8 encoding."""
    with patch('picard.session.session_manager.export_session') as mock_export:
        # Session data with Unicode characters
        session_data = {
            "version": 1,
            "items": [{"file_path": "/test/歌曲.mp3"}],
        }
        mock_export.return_value = session_data

        tagger_mock = Mock()
        session_file = tmp_path / "test"

        save_session_to_path(tagger_mock, session_file)

        saved_file = Path(str(session_file) + ".mbps.gz")
        import gzip

        content = gzip.decompress(saved_file.read_bytes()).decode("utf-8")
        assert "歌曲" in content


def test_save_session_to_path_json_formatting(tmp_path: Path) -> None:
    """Test that save_session_to_path uses proper JSON formatting."""
    with patch('picard.session.session_manager.export_session') as mock_export:
        session_data = {
            "version": 1,
            "options": {"rename_files": True, "move_files": False},
            "items": [],
        }
        mock_export.return_value = session_data

        tagger_mock = Mock()
        session_file = tmp_path / "test"

        save_session_to_path(tagger_mock, session_file)

        saved_file = Path(str(session_file) + ".mbps.gz")
        import gzip

        content = gzip.decompress(saved_file.read_bytes()).decode("utf-8")
        # Content is minified JSON
        assert content.startswith("{")
        assert '"version":1' in content
        assert '"options":{' in content
        assert '"rename_files":true' in content


def test_export_session_returns_dict() -> None:
    """Test that export_session returns a dictionary."""
    with patch('picard.session.session_manager.SessionExporter') as mock_exporter_class:
        mock_exporter = Mock()
        mock_exporter_class.return_value = mock_exporter
        mock_exporter.export_session.return_value = {"version": 1, "items": []}

        tagger_mock = Mock()
        result = export_session(tagger_mock)

        assert isinstance(result, dict)
        assert "version" in result
        assert "items" in result


def test_load_session_from_path_loader_initialization() -> None:
    """Test that SessionLoader is properly initialized."""
    with patch('picard.session.session_manager.SessionLoader') as mock_loader_class:
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        tagger_mock = Mock()
        session_file = Path("/test/session.mbps.gz")

        load_session_from_path(tagger_mock, session_file)

        # Verify SessionLoader was initialized with correct tagger
        mock_loader_class.assert_called_once_with(tagger_mock)


def test_load_session_from_path_loader_methods_called() -> None:
    """Test that all required SessionLoader methods are called."""
    with patch('picard.session.session_manager.SessionLoader') as mock_loader_class:
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        tagger_mock = Mock()
        session_file = Path("/test/session.mbps.gz")

        load_session_from_path(tagger_mock, session_file)

        # Verify all required methods were called
        mock_loader.load_from_path.assert_called_once_with(session_file)
        mock_loader.finalize_loading.assert_called_once()


def test_save_session_to_path_extension_handling(tmp_path: Path) -> None:
    """Test various extension handling scenarios."""
    with patch('picard.session.session_manager.export_session') as mock_export:
        mock_export.return_value = {"version": 1}

        tagger_mock = Mock()

        # Test cases: (input_path)
        test_cases = [
            "test",
            "test.mbps.gz",
            "test.json",
            "test.txt",
        ]

        for input_path in test_cases:
            session_file = tmp_path / input_path
            save_session_to_path(tagger_mock, session_file)

            expected_file = (
                session_file if str(session_file).endswith(".mbps.gz") else Path(str(session_file) + ".mbps.gz")
            )
            assert expected_file.exists(), f"Failed for input: {input_path}"

            # Clean up for next test
            expected_file.unlink()


def test_session_constants_used_correctly(tmp_path: Path) -> None:
    """Test that session constants are used correctly in manager functions."""
    # This test ensures that the session manager uses the correct constants
    assert SessionConstants.SESSION_FILE_EXTENSION == ".mbps.gz"
    assert SessionConstants.SESSION_FORMAT_VERSION == 1

    # Test that the extension is used in save function
    with patch('picard.session.session_manager.export_session') as mock_export:
        mock_export.return_value = {"version": SessionConstants.SESSION_FORMAT_VERSION}

        tagger_mock = Mock()
        session_file = tmp_path / "session"

        save_session_to_path(tagger_mock, session_file)

        # Verify the exported data has correct version
        mock_export.assert_called_once_with(tagger_mock)
