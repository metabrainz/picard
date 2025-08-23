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

"""
Pytest-based tests for filename/path handling across locales and drag-and-drop.

Covers regressions referenced by:
 - PICARD-167: Handle non-UTF-8 locales better
 - PICARD-233: Charset of file different than application

Some scenarios are marked xfail to document and reproduce current bugs.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import os.path as osp
from typing import Any, Iterable
import unicodedata

from PyQt6 import QtCore

from picard.const.sys import IS_MACOS
from picard.tagger import Tagger
from picard.util import decode_filename, encode_filename

import pytest

from picard.ui.itemviews.basetreeview import BaseTreeView


@dataclass
class _Captured:
    paths: list[str] | None = None
    add_paths_target: Any | None = None
    moved_files: list[Any] | None = None
    move_to_multi_tracks: bool | None = None
    move_files_target: Any | None = None
    mbid_lookups: list[tuple[str, bool]] | None = None


@dataclass
class _FakeLookup:
    captured: _Captured

    def mbid_lookup(self, url_path: str, browser_fallback: bool = False) -> None:
        if self.captured.mbid_lookups is None:
            self.captured.mbid_lookups = []
        self.captured.mbid_lookups.append((url_path, browser_fallback))


@dataclass
class _FakeTagger:
    files: dict[str, Any]
    captured: _Captured

    def add_paths(self, paths: Iterable[str], target: Any | None = None) -> None:
        if isinstance(paths, list):
            self.captured.paths = paths
        else:
            self.captured.paths = list(paths)
        self.captured.add_paths_target = target

    def get_file_lookup(self) -> _FakeLookup:
        return _FakeLookup(self.captured)

    def move_files(self, files: list[Any], target: Any | None, move_to_multi_tracks: bool) -> None:
        self.captured.moved_files = list(files)
        self.captured.move_files_target = target
        self.captured.move_to_multi_tracks = move_to_multi_tracks


@pytest.fixture
def fake_tagger(monkeypatch: pytest.MonkeyPatch) -> tuple[_FakeTagger, _Captured]:
    """Provide a minimal fake tagger returned by QCoreApplication.instance()."""
    captured = _Captured()
    fake = _FakeTagger(files={}, captured=captured)
    monkeypatch.setattr(QtCore.QCoreApplication, "instance", lambda: fake)
    return fake, captured


@pytest.mark.parametrize(
    "name",
    [
        "Café.txt",
        "Mon Cœur.txt",
        "S’ouvre.txt",
        "I Belong To You _ Mon Cœur S’ouvre À Ta Voix.txt",
        "日本語 🐍.txt",
        "emoji_🚀_é_œ_’.txt",
    ],
)
@pytest.mark.parametrize("scheme_kind", ["file", "noscheme"], ids=["file", "noscheme"])
@pytest.mark.skipif(
    not osp.supports_unicode_filenames and not IS_MACOS, reason="Unicode filenames not supported on this FS"
)
def test_drop_urls_preserves_unicode_paths(
    tmp_path: os.PathLike[str], fake_tagger: tuple[_FakeTagger, _Captured], name: str, scheme_kind: str
) -> None:
    fake, captured = fake_tagger
    path: str = osp.normpath(osp.join(str(tmp_path), name))
    with open(path, "wb") as f:
        f.write(b"test")

    if scheme_kind == "file":
        url: QtCore.QUrl = QtCore.QUrl.fromLocalFile(path)
    else:
        # Construct URL without explicit scheme; BaseTreeView accepts both
        url = QtCore.QUrl(path)

    BaseTreeView.drop_urls([url], target=None, move_to_multi_tracks=True)

    assert captured.paths is not None
    assert len(captured.paths) == 1
    assert isinstance(captured.paths[0], str)
    assert captured.paths[0] == osp.normpath(path)


@pytest.mark.parametrize(
    "http_url",
    [
        "https://musicbrainz.org/recording/1234",
        "http://example.com/not-mbid",
    ],
)
def test_drop_urls_http_invokes_mbid_lookup(fake_tagger: tuple[_FakeTagger, _Captured], http_url: str) -> None:
    _fake, captured = fake_tagger
    url: QtCore.QUrl = QtCore.QUrl(http_url)

    BaseTreeView.drop_urls([url], target=None, move_to_multi_tracks=True)

    # For HTTP/HTTPS we must not call add_paths
    assert captured.paths is None
    # We should have attempted an MBID lookup with the URL path
    assert captured.mbid_lookups is not None
    assert (url.path(), False) in captured.mbid_lookups


def test_drop_urls_moves_existing_files_and_adds_new_paths(
    tmp_path: os.PathLike[str], fake_tagger: tuple[_FakeTagger, _Captured]
) -> None:
    fake, captured = fake_tagger
    # Prepare two paths: one already tracked (should be moved), one new (should be added)
    existing_path = osp.join(str(tmp_path), "existing.flac")
    new_path = osp.join(str(tmp_path), "new.ogg")
    for p in (existing_path, new_path):
        with open(p, "wb") as f:
            f.write(b"x")

    existing_file_obj = object()
    fake.files[osp.normpath(existing_path)] = existing_file_obj

    urls = [
        QtCore.QUrl.fromLocalFile(existing_path),
        QtCore.QUrl(new_path),  # scheme-less
    ]

    BaseTreeView.drop_urls(urls, target="TGT", move_to_multi_tracks=False)

    # move_files called with the existing file object
    assert captured.moved_files == [existing_file_obj]
    assert captured.move_files_target == "TGT"
    assert captured.move_to_multi_tracks is False

    # add_paths called with the new normalized path
    assert captured.paths == [osp.normpath(new_path)]
    assert captured.add_paths_target == "TGT"


def test_drop_urls_trims_trailing_null_and_normalizes(
    tmp_path: os.PathLike[str], fake_tagger: tuple[_FakeTagger, _Captured]
) -> None:
    # Build a stub mimicking QUrl that returns a path with a trailing NUL
    norm_base = osp.normpath(str(tmp_path))
    raw_path = osp.join(norm_base, "dir", "..", "file.txt")
    os.makedirs(osp.dirname(osp.normpath(raw_path)), exist_ok=True)
    with open(osp.normpath(raw_path), "wb") as f:
        f.write(b"ok")

    class _StubUrl:
        def __init__(self, p: str) -> None:
            self._p = p

        def scheme(self) -> str:
            return "file"

        def toLocalFile(self) -> str:
            return self._p + "\0"

        def path(self) -> str:
            return self._p

        def toString(self, *_args: Any, **_kwargs: Any) -> str:
            return self._p

    url = _StubUrl(raw_path)
    _fake, captured = fake_tagger
    BaseTreeView.drop_urls([url], target=None, move_to_multi_tracks=True)

    # Expect trimmed and normalized path
    assert captured.paths is not None
    assert len(captured.paths) == 1
    assert captured.paths[0] == osp.normpath(raw_path)


def test_drop_urls_ignores_unknown_schemes(fake_tagger: tuple[_FakeTagger, _Captured]) -> None:
    _fake, captured = fake_tagger
    url = QtCore.QUrl("ftp://example.com/foo.mp3")
    BaseTreeView.drop_urls([url], target=None, move_to_multi_tracks=True)
    assert captured.paths is None
    assert captured.moved_files is None
    assert captured.mbid_lookups is None


@pytest.mark.parametrize(
    ("bad_encoding", "filename"),
    [
        ("ISO-8859-1", "Café _ Mon Cœur.txt"),
        ("ASCII", "S’ouvre.txt"),
        ("euc_jp", "波形 ~ テスト.txt"),
    ],
)
@pytest.mark.xfail(reason="encode_filename currently performs lossy replacement under non-UTF-8 locales")
@pytest.mark.skipif(IS_MACOS, reason="macOS path handling will be addressed separately")
def test_encode_filename_should_not_lossily_replace_on_posix(
    monkeypatch: pytest.MonkeyPatch, bad_encoding: str, filename: str
) -> None:
    """Simulate non-UTF-8 locale and assert we do not corrupt Unicode paths."""
    # Use a POSIX-like absolute path for consistency
    unicode_path: str = f"/tmp/{filename}"

    # Force Picard's view of the filesystem encoding
    monkeypatch.setattr("picard.util._io_encoding", bad_encoding, raising=False)

    result = encode_filename(unicode_path)
    # Desired: keep str unchanged; current behavior often returns bytes or lossy content
    assert isinstance(result, str)
    assert result == unicode_path


@pytest.mark.skipif(not IS_MACOS, reason="macOS-specific normalization behavior")
def test_component_wise_resolution_between_nfc_and_nfd(tmp_path: os.PathLike[str]) -> None:
    """Create path using NFD but address it using NFC, expecting resolution.

    This documents the normalization mismatch seen with FUSE/sshfs and Finder.
    """
    base: str = str(tmp_path)
    name_nfc: str = "Caf\u00e9"
    name_nfd: str = unicodedata.normalize("NFD", name_nfc)
    assert name_nfc != name_nfd

    nfd_dir: str = osp.join(base, name_nfd)
    os.makedirs(nfd_dir, exist_ok=True)

    file_name_nfc: str = "T\u00c0.txt"  # "TÀ.txt"
    file_path_nfd: str = osp.join(nfd_dir, file_name_nfc)
    with open(file_path_nfd, "wb") as f:
        f.write(b"ok")

    # Address using NFC form
    nfc_dir: str = osp.join(base, name_nfc)
    nfc_path: str = osp.join(nfc_dir, file_name_nfc)

    # Future resolver should make this True even if the underlying FS exposes different normalization
    assert os.path.exists(nfc_path)


# ------------------------
# POSIX bytes-path testing
# ------------------------


@pytest.mark.skipif(os.name != "posix" or IS_MACOS, reason="bytes-path tests are POSIX-only and skipped on macOS")
def test_bytes_filename_ascii_locale(monkeypatch: pytest.MonkeyPatch, tmp_path: os.PathLike[str]) -> None:
    """Create a file using raw bytes in the name and verify behavior under ASCII locale."""
    base_b: bytes = os.fsencode(str(tmp_path))
    # Name includes bytes not representable in ASCII/UTF-8 (0xE9, 0xFF)
    name_b: bytes = b"Cafe\xe9_\xff.bin"
    path_b: bytes = base_b + b"/" + name_b

    fd: int = os.open(path_b, os.O_CREAT | os.O_WRONLY, 0o644)
    os.close(fd)
    assert osp.exists(path_b)

    # Simulate ASCII locale in Picard
    monkeypatch.setattr("picard.util._io_encoding", "ASCII", raising=False)

    # decode_filename should fail on undecodable bytes
    with pytest.raises(UnicodeDecodeError):
        decode_filename(name_b)

    # encode_filename should return bytes unchanged if bytes were provided
    assert encode_filename(path_b) == path_b

    # os APIs still function with bytes paths
    st = os.stat(path_b)
    assert st.st_size == 0


@pytest.mark.skipif(os.name != "posix" or IS_MACOS, reason="POSIX-only and skipped on macOS")
def test_scan_recursive_accepts_bytes(tmp_path: os.PathLike[str]) -> None:
    """Ensure Tagger._scan_paths_recursive yields bytes paths if provided bytes input."""
    base_b: bytes = os.fsencode(str(tmp_path))
    name_b: bytes = b"\xff\xfe.bad"
    path_b: bytes = base_b + b"/" + name_b
    fd: int = os.open(path_b, os.O_CREAT | os.O_WRONLY, 0o644)
    os.close(fd)

    out = list(Tagger._scan_paths_recursive([path_b], recursive=False, ignore_hidden=False))
    assert path_b in out
