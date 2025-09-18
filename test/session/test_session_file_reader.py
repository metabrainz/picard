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

"""Tests for SessionFileReader."""

from pathlib import Path

import yaml

from picard.session.session_loader import SessionFileReader

import pytest


def test_session_file_reader_read(tmp_path: Path) -> None:
    """Read a valid YAML session file."""
    session_data = {'version': 1, 'items': []}
    session_file = tmp_path / "test.mbps"
    session_file.write_text(yaml.dump(session_data, default_flow_style=False), encoding="utf-8")

    reader = SessionFileReader()
    data = reader.read(session_file)

    assert data == session_data


def test_session_file_reader_invalid_yaml(tmp_path: Path) -> None:
    """Raise YAMLError on invalid YAML."""
    session_file = tmp_path / "test.mbps"
    session_file.write_text("invalid yaml: [", encoding="utf-8")

    reader = SessionFileReader()
    with pytest.raises(yaml.YAMLError):
        reader.read(session_file)


def test_session_file_reader_not_found() -> None:
    """Raise FileNotFoundError for nonexistent path."""
    reader = SessionFileReader()
    with pytest.raises(FileNotFoundError):
        reader.read(Path("/nonexistent/file.mbps"))


def test_session_file_reader_gzip(tmp_path: Path) -> None:
    """Read a gzipped YAML session file."""
    session_data = {'version': 1, 'items': []}
    text = yaml.dump(session_data, default_flow_style=False)

    import gzip as _gzip

    gz_path = tmp_path / "test.mbps.gz"
    gz_path.write_bytes(_gzip.compress(text.encode("utf-8")))

    reader = SessionFileReader()
    data = reader.read(gz_path)

    assert data == session_data
