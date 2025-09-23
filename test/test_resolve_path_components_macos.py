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
Tests for picard.util._resolve_path_components_macos
"""

from __future__ import annotations

import os
from pathlib import Path
import unicodedata

from picard.const.sys import IS_MACOS
from picard.util import _resolve_path_components_macos

import pytest


pytestmark = pytest.mark.skipif(not IS_MACOS, reason="macOS-only tests")


@pytest.mark.parametrize(
    ("parts"),
    [
        ("A",),
        ("A", "B"),
        ("Caf\u00e9",),
        ("Mon C\u0153ur",),
    ],
)
def test_resolve_existing_components(tmp_path: os.PathLike[str], parts: tuple[str, ...]) -> None:
    base = Path(tmp_path)
    current = base
    for p in parts:
        current = current / p
    current.mkdir(parents=True, exist_ok=True)

    out: str = _resolve_path_components_macos(str(current))
    assert Path(out).exists()
    assert Path(out).is_dir()


@pytest.mark.parametrize(
    ("name"),
    [
        "Caf\u00e9",
        "Mon C\u0153ur",
        "S’ouvre \u00c0 Ta Voix",
    ],
)
def test_resolve_nfc_nfd_alternates(tmp_path: os.PathLike[str], name: str) -> None:
    base = Path(tmp_path)
    name_nfc = unicodedata.normalize("NFC", name)
    name_nfd = unicodedata.normalize("NFD", name)

    created_dir = base / name_nfd
    created_dir.mkdir(parents=True, exist_ok=True)
    actual_entry = next(p.name for p in base.iterdir())

    # Pass the alternate spelling
    alt_dir = base / name_nfc / "sub"
    out: str = _resolve_path_components_macos(str(alt_dir))
    # Parent should resolve to actual entry, even if final component doesn't exist
    parent = Path(out).parent
    assert parent.exists()
    assert parent.name == actual_entry


def test_resolve_preserves_relative_form(tmp_path: os.PathLike[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("a").mkdir(exist_ok=True)
    rel = Path("a") / ".." / "b" / "c"
    # Only 'a' exists; 'b' should be left as-is but normalized
    out: str = _resolve_path_components_macos(str(rel))
    assert out.endswith(str(Path("b") / "c"))
