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

"""Test sanitize_date function."""

from collections.abc import Callable

from picard.util import sanitize_date

import pytest


@pytest.fixture
def norm() -> Callable[[str], str]:
    return sanitize_date


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("", ""),
        ("0", ""),
        ("0000", ""),
        ("2006", "2006"),
        ("2006--", "2006"),
        ("2006-00-02", "2006-00-02"),
        ("2006   ", "2006"),
        ("2006 02", ""),
        ("2006.02", ""),
        ("2006-02", "2006-02"),
        ("2006-02-00", "2006-02"),
        ("2006-00-00", "2006"),
        ("2006-02-23", "2006-02-23"),
        ("2006-00-23", "2006-00-23"),
        ("0000-00-23", "0000-00-23"),
        ("0000-02", "0000-02"),
        ("--23", "0000-00-23"),
    ],
)
def test_sanitize_date_basic(norm: Callable, src: str, expected: str) -> None:
    assert norm(src) == expected


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("2005-12-00", "2005-12"),
        ("2005-00-12", "2005-00-12"),  # bugfix: don't shift 00 month
        ("0000-00-12", "0000-00-12"),  # bugfix: don't become 0012
        ("0000-00-00", ""),
    ],
)
def test_sanitize_date_bug_cases(norm: Callable, src: str, expected: str) -> None:
    assert norm(src) == expected


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("31/12/2005", "2005-12-31"),
        ("12/31/2005", "2005-12-31"),
        ("20051231", "2005-12-31"),
        ("20053112", "2005-12-31"),
    ],
)
def test_sanitize_date_other_formats(norm: Callable, src: str, expected: str) -> None:
    assert norm(src) == expected


@pytest.mark.parametrize(
    "src",
    [
        ("nonsense",),
        ("2006/13/01",),
        ("2006-13-01",),
    ],
)
def test_sanitize_date_invalid(norm: Callable, src: str) -> None:
    assert norm(src) == ""


@pytest.mark.parametrize(
    "src",
    [
        "0000-00-00",
        "2005-00-12",
        "2005-12-00",
    ],
)
def test_disable_sanitization_returns_input(src: str) -> None:
    assert sanitize_date(src, disable_sanitization=True) == src
