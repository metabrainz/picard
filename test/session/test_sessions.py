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

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import picard.config as picard_config
from picard.const.appdirs import config_folder, sessions_folder
from picard.metadata import Metadata
from picard.session.session_manager import export_session

# Import stub classes from conftest.py
from .conftest import _StubAlbum, _StubFile, _StubTagger, _StubTrack
import pytest


def test_export_session_empty(tmp_path: Path, cfg_options) -> None:
    data = export_session(_StubTagger(files=[], albums={}))
    assert isinstance(data, dict)
    assert data['version'] == 1
    assert set(data['options'].keys()) == {"rename_files", "move_files", "enable_tag_saving"}
    assert data['options']['enable_tag_saving'] is False
    assert data['items'] == []


@pytest.mark.parametrize("saved", [True, False])
def test_export_session_includes_items_and_metadata_tags(cfg_options: None, tmp_path: Path, saved: bool) -> None:
    m = Metadata()
    m['title'] = "Song"
    m['artist'] = "Artist"
    m['~internal'] = "x"
    m['length'] = "123456"
    f = _StubFile(filename=str(tmp_path / "a.flac"), metadata=m, saved=saved, parent_item=None)
    # Provide baseline so deltas can be computed
    f.orig_metadata = Metadata()
    tagger = _StubTagger(files=[f])

    data = export_session(tagger)

    assert isinstance(data['items'], list) and len(data['items']) == 1
    item = data['items'][0]
    assert Path(item['file_path']).name == "a.flac"

    loc = item['location']
    assert loc['type'] == "unclustered"
    assert "album_id" not in loc and "recording_id" not in loc

    if saved:
        assert "metadata" not in item
    else:
        # Only user-visible tags; internal and length excluded; values are lists
        tags = item['metadata']['tags']
        assert set(tags.keys()) == {"title", "artist"}
        assert isinstance(tags['title'], list) and tags['title'] == ["Song"]


def test_export_session_options_reflect_config_flags(cfg_options: None) -> None:
    cfg = picard_config.get_config()
    cfg.setting['rename_files'] = True
    cfg.setting['move_files'] = True
    cfg.setting['enable_tag_saving'] = True

    tagger = _StubTagger(files=[])
    data = export_session(tagger)
    assert data['options'] == {
        'rename_files': True,
        'move_files': True,
        'enable_tag_saving': True,
    }


def test_export_session_captures_album_and_track_overrides(cfg_options: None, tmp_path: Path) -> None:
    # File present to ensure items list not empty, but focus is on overrides capture
    fm = Metadata()
    fm['title'] = "Song"
    f = _StubFile(filename=str(tmp_path / "b.mp3"), metadata=fm, saved=True, parent_item=None)

    # Album-level override (albumartist changed)
    album_orig = Metadata()
    album_orig['albumartist'] = "Orig Artist"
    album_cur = Metadata()
    album_cur['albumartist'] = "New Artist"

    # Track-level override vs scripted_metadata; exclude length
    scripted = Metadata()
    scripted['title'] = "Old Title"
    scripted['length'] = "1000"
    track_cur = Metadata()
    track_cur['title'] = "New Title"
    track_cur['length'] = "2000"  # must be excluded

    tr = _StubTrack("track-1", scripted=scripted, current=track_cur)
    alb = _StubAlbum("album-1", orig=album_orig, current=album_cur, tracks=[tr])
    tagger = _StubTagger(files=[f], albums={'album-1': alb})

    data = export_session(tagger)

    # Track-level overrides captured and listified
    atr = data['album_track_overrides']
    assert "album-1" in atr and "track-1" in atr['album-1']
    assert atr['album-1']['track-1'] == {'title': ["New Title"]}

    # Album-level overrides captured and listified
    aor = data['album_overrides']
    assert aor == {'album-1': {'albumartist': ["New Artist"]}}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Rock", ["Rock"]),
        (["Rock", "Pop"], ["Rock", "Pop"]),
    ],
)
def test_export_session_listifies_override_values(cfg_options: None, value: Any, expected: list[str]) -> None:
    # Construct album with scalar/list diffs
    album_orig = Metadata()
    album_orig['genre'] = ""
    album_cur = Metadata()
    album_cur['genre'] = value
    alb = _StubAlbum("album-X", orig=album_orig, current=album_cur, tracks=[])

    tagger = _StubTagger(files=[], albums={'album-X': alb})
    data = export_session(tagger)
    assert data['album_overrides'] == {'album-X': {'genre': expected}}


def test_export_session_includes_unmatched_albums(cfg_options: None) -> None:
    """Test that albums with no files matched are included in unmatched_albums."""
    # Create an album with no files matched to it
    album_orig = Metadata()
    album_cur = Metadata()
    alb = _StubAlbum("album-unmatched", orig=album_orig, current=album_cur, tracks=[])

    # Tagger with no files but has the album loaded
    tagger = _StubTagger(files=[], albums={'album-unmatched': alb})

    data = export_session(tagger)

    # Should include the unmatched album
    assert "unmatched_albums" in data
    assert data['unmatched_albums'] == ["album-unmatched"]


def test_export_session_excludes_albums_with_files_from_unmatched(cfg_options: None, tmp_path: Path) -> None:
    """Test that albums with files matched are not included in unmatched_albums."""

    # Create a mock parent item that represents a track in an album
    class _StubParentItem:
        def __init__(self, album_id: str) -> None:
            self.album = SimpleNamespace(id=album_id)

    # Create an album
    album_orig = Metadata()
    album_cur = Metadata()
    alb = _StubAlbum("album-with-files", orig=album_orig, current=album_cur, tracks=[])

    # Create a file that's matched to the album
    fm = Metadata()
    fm['title'] = "Song"
    parent_item = _StubParentItem("album-with-files")
    f = _StubFile(filename=str(tmp_path / "song.mp3"), metadata=fm, saved=True, parent_item=parent_item)

    # Tagger with the file and album
    tagger = _StubTagger(files=[f], albums={'album-with-files': alb})

    data = export_session(tagger)

    # Should not include the album in unmatched_albums since it has files
    assert "unmatched_albums" in data
    assert data['unmatched_albums'] == []


def test_sessions_folder_default_path(cfg_options: None) -> None:
    """Test that sessions_folder returns the default path when no custom path is set."""
    config = picard_config.get_config()
    config.setting['session_folder_path'] = ''

    expected_path = Path(config_folder()) / 'sessions'
    result = sessions_folder()
    assert result.lower().endswith(str(expected_path).lower())


def test_sessions_folder_custom_path(cfg_options: None, tmp_path: Path) -> None:
    """Test that sessions_folder returns the custom path when configured."""
    config = picard_config.get_config()
    custom_path = str(tmp_path / 'custom_sessions')
    config.setting['session_folder_path'] = custom_path

    # sessions_folder resolves custom paths; compare using endswith on strings
    expected = Path(custom_path).resolve()
    result = sessions_folder()
    assert result.lower().endswith(str(expected).lower())


@pytest.mark.parametrize("custom_path", ["", "/some/custom/path", "relative/path"])
def test_sessions_folder_path_normalization(cfg_options: None, custom_path: str) -> None:
    """Test that sessions_folder normalizes paths correctly."""
    config = picard_config.get_config()
    config.setting['session_folder_path'] = custom_path

    result = sessions_folder()
    assert isinstance(result, str)
    if custom_path:
        expected = Path(custom_path).resolve()
    else:
        expected = Path(config_folder()) / 'sessions'
    assert result.lower().endswith(str(expected).lower())
