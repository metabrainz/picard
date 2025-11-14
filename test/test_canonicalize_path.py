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
Tests for picard.util.canonicalize_path
"""

from __future__ import annotations

import os
from pathlib import Path
import unicodedata

from picard.const.sys import IS_MACOS
from picard.util import (
    WIN_LONGPATH_PREFIX,
    WIN_MAX_FILEPATH_LEN,
    canonicalize_path,
    win_prefix_longpath,
)

import pytest


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/tmp/foo\0\0", "/tmp/foo"),
        ("./a/../b\0", str(Path("b"))),
    ],
)
def test_canonicalize_path_trims_nulls_and_normalizes(raw: str, expected: str) -> None:
    out: str = canonicalize_path(raw)
    # Only compare tail to avoid host-specific absolute prefixes
    assert out.endswith(os.path.normpath(expected))


def test_canonicalize_path_returns_non_string_unchanged() -> None:
    # Provide arbitrary bytes; function should pass through unchanged
    path_b: bytes = b"/invalid/bytes/\xff\xfe.bin"
    out = canonicalize_path(path_b)  # type: ignore[arg-type]
    assert isinstance(out, (bytes, bytearray))
    assert out == path_b


def test_canonicalize_path_resolves_existing_paths(tmp_path: os.PathLike[str]) -> None:
    nested: Path = Path(tmp_path) / "x" / "y"
    nested.mkdir(parents=True, exist_ok=True)
    fpath: Path = nested / "file.txt"
    fpath.write_bytes(b"ok")

    out: str = canonicalize_path(str(fpath))
    # Should resolve to an absolute path that exists
    assert Path(out).is_absolute()
    assert Path(out).exists()


def test_canonicalize_path_preserves_relative_form(tmp_path: os.PathLike[str], monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure cwd is tmp_path so relative resolution is predictable
    monkeypatch.chdir(tmp_path)
    rel: str = "a/../b/c.txt\0"
    # Create parent only; file may not exist, but normalization should still run
    Path("b").mkdir(parents=True, exist_ok=True)
    out: str = canonicalize_path(rel)
    # Non-strict resolve keeps path normalized; we check it endswith normalized relative
    assert out.endswith(str(Path("b") / "c.txt"))


def test_win_prefix_longpath_drive_path() -> None:
    # Long path over the limit should get the standard long-path prefix
    long_tail: str = "a" * (WIN_MAX_FILEPATH_LEN + 5)
    p: str = "C:\\" + long_tail
    out: str = win_prefix_longpath(p)
    assert out.startswith(WIN_LONGPATH_PREFIX)
    assert out[len(WIN_LONGPATH_PREFIX) :].startswith("C:\\")


def test_win_prefix_longpath_unc_path() -> None:
    # UNC path should translate to \\?\UNC + path[1:]
    long_tail: str = "share\\" + ("a" * (WIN_MAX_FILEPATH_LEN + 5))
    p: str = "\\\\server\\" + long_tail
    out: str = win_prefix_longpath(p)
    assert out.startswith(WIN_LONGPATH_PREFIX + 'UNC')
    assert out.endswith(long_tail)


def test_canonicalize_path_applies_windows_longpath(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force Windows branch and ensure prefixing is applied via the helper
    monkeypatch.setattr("picard.util.IS_WIN", True, raising=False)
    monkeypatch.setattr("picard.util.system_supports_long_paths", lambda: False, raising=False)

    calls: list[str] = []

    def _spy_prefix(path: str) -> str:
        calls.append(path)
        return "PREFIXED:" + path

    monkeypatch.setattr("picard.util.win_prefix_longpath", _spy_prefix, raising=False)

    # Any input path is fine; the spy will be invoked unconditionally under IS_WIN and no long paths
    raw: str = "C:/dummy"
    out: str = canonicalize_path(raw)
    assert calls, "win_prefix_longpath was not called"
    assert out.startswith("PREFIXED:")


@pytest.mark.skipif(not IS_MACOS, reason="macOS-only normalization behavior")
@pytest.mark.parametrize(
    ("name"),
    [
        "Caf\u00e9",  # café
        "Mon C\u0153ur",  # cœur with ligature
        "S’ouvre \u00c0 Ta Voix",  # curly apostrophe and À
    ],
)
def test_canonicalize_path_componentwise_nfc_nfd(tmp_path: os.PathLike[str], name: str) -> None:
    base = Path(tmp_path)
    name_nfc = unicodedata.normalize("NFC", name)
    name_nfd = unicodedata.normalize("NFD", name)

    # Create using one form, then address using the other
    created_dir = base / name_nfd
    created_dir.mkdir()
    # Determine actual on-disk entry spelling (APFS/HFS+ may adjust)
    actual_entry = next(p.name for p in base.iterdir())

    # Address path using the alternate form
    alt_path = str(base / name_nfc / "test.txt")
    out: str = canonicalize_path(alt_path)

    # Parent should resolve to the actual entry; file may not exist yet
    parent = Path(out).parent
    assert parent.exists()
    assert parent.name == actual_entry
