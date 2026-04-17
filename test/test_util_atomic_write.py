# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from pathlib import Path
from unittest.mock import patch

from picard.util import atomic_write

import pytest


def test_atomic_write_creates_file(tmp_path):
    """Test that atomic_write creates a new file."""
    target = tmp_path / "test.toml"
    data = b"key = 'value'"

    atomic_write(target, data)

    assert target.exists()
    assert target.read_bytes() == data


def test_atomic_write_overwrites_existing(tmp_path):
    """Test that atomic_write replaces existing file content."""
    target = tmp_path / "test.toml"
    target.write_bytes(b"old content")

    atomic_write(target, b"new content")

    assert target.read_bytes() == b"new content"


def test_atomic_write_creates_parent_dirs(tmp_path):
    """Test that atomic_write creates missing parent directories."""
    target = tmp_path / "sub" / "dir" / "test.toml"

    atomic_write(target, b"data")

    assert target.exists()
    assert target.read_bytes() == b"data"


def test_atomic_write_no_temp_files_on_success(tmp_path):
    """Test that no temporary files remain after successful write."""
    target = tmp_path / "test.toml"

    atomic_write(target, b"data")

    files = list(tmp_path.iterdir())
    assert files == [target]


def test_atomic_write_cleanup_on_rename_failure(tmp_path):
    """Test that temporary files are cleaned up when rename fails."""
    target = tmp_path / "test.toml"

    with patch("pathlib.Path.replace", side_effect=OSError("Rename failed")):
        with pytest.raises(OSError, match="Rename failed"):
            atomic_write(target, b"data")

    # No temp files left behind
    temp_files = list(tmp_path.glob("test_*"))
    assert len(temp_files) == 0

    # Target not created
    assert not target.exists()


def test_atomic_write_preserves_old_file_on_failure(tmp_path):
    """Test that the original file is preserved when write fails."""
    target = tmp_path / "test.toml"
    target.write_bytes(b"original")

    with patch("pathlib.Path.replace", side_effect=OSError("Rename failed")):
        with pytest.raises(OSError):
            atomic_write(target, b"new data")

    assert target.read_bytes() == b"original"


def test_atomic_write_accepts_str_path(tmp_path):
    """Test that atomic_write accepts string paths."""
    target = str(tmp_path / "test.toml")

    atomic_write(target, b"data")

    assert Path(target).read_bytes() == b"data"


def test_atomic_write_cleanup_on_write_failure(tmp_path):
    """Test that temporary files are cleaned up when write fails (e.g. disk full)."""
    target = tmp_path / "test.toml"
    target.write_bytes(b"original")

    with patch("tempfile.NamedTemporaryFile") as mock_ntf:
        mock_file = mock_ntf.return_value.__enter__.return_value
        mock_file.name = str(tmp_path / "test_tmp.toml")
        mock_file.write.side_effect = OSError("No space left on device")
        Path(mock_file.name).write_bytes(b"")  # create the temp file

        with pytest.raises(OSError, match="No space left on device"):
            atomic_write(target, b"new data")

    # Original file preserved
    assert target.read_bytes() == b"original"
    # Temp file cleaned up
    assert not Path(mock_file.name).exists()
