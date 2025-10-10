# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 2
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

"""Comprehensive unit tests for variable_pattern module.

Tests all pattern functions in the variable_pattern module to verify
they work correctly with various input formats and edge cases.
"""

import re

from picard.script.variable_pattern import (
    GET_VARIABLE_RE,
    PERCENT_VARIABLE_RE,
    SET_VARIABLE_RE,
    VARIABLE_NAME_FULLMATCH_RE,
)

import pytest


@pytest.fixture(scope="module")
def percent_pattern() -> re.Pattern:
    return PERCENT_VARIABLE_RE


@pytest.fixture(scope="module")
def get_pattern() -> re.Pattern:
    return GET_VARIABLE_RE


@pytest.fixture(scope="module")
def set_pattern() -> re.Pattern:
    return SET_VARIABLE_RE


@pytest.fixture(scope="module")
def variable_fullmatch() -> re.Pattern:
    return VARIABLE_NAME_FULLMATCH_RE


def test_compiled_patterns(
    percent_pattern: re.Pattern, get_pattern: re.Pattern, set_pattern: re.Pattern, variable_fullmatch: re.Pattern
) -> None:
    assert isinstance(percent_pattern, re.Pattern)
    assert isinstance(get_pattern, re.Pattern)
    assert isinstance(set_pattern, re.Pattern)
    assert isinstance(variable_fullmatch, re.Pattern)


# %variable% matching and capture
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("%artist%", "artist"),
        ("%album%", "album"),
        ("%title%", "title"),
        ("%var_ñ%", "var_ñ"),
        ("%var_中文%", "var_中文"),
        ("%var_α%", "var_α"),
        ("%tag:artist%", "tag:artist"),
        ("%tag:album%", "tag:album"),
        ("%namespace:key%", "namespace:key"),
        ("%var1%", "var1"),
        ("%var123%", "var123"),
        ("%var_123%", "var_123"),
        ("%var_name%", "var_name"),
        ("%_private_var%", "_private_var"),
        ("%var_with_underscores%", "var_with_underscores"),
        ("%a%", "a"),
        (f"%{'a' * 1000}%", "a" * 1000),
        ("artist", None),
        ("%artist", None),
        ("artist%", None),
        ("%var-name%", None),
        ("%var.name%", None),
        ("%var name%", None),
        ("%%", None),
    ],
)
def test_percent_variable_match(percent_pattern: re.Pattern, text: str, expected: str | None) -> None:
    m = percent_pattern.match(text)
    assert (m.group(1) if m else None) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("This is %artist% and %album%", ["artist", "album"])],
)
def test_percent_variable_finditer(percent_pattern: re.Pattern, text: str, expected: list[str]) -> None:
    names = [m.group(1) for m in percent_pattern.finditer(text)]
    assert names == expected


# $get(variable) matching and capture
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$get(artist)", "artist"),
        ("$get(album)", "album"),
        ("$get(title)", "title"),
        ("$get( artist )", "artist"),
        ("$get(  artist  )", "artist"),
        ("$get(artist )", "artist"),
        ("$get( artist)", "artist"),
        ("$get(var_ñ)", "var_ñ"),
        ("$get(var_中文)", "var_中文"),
        ("$get(var_α)", "var_α"),
        ("$get(tag:artist)", "tag:artist"),
        ("$get(tag:album)", "tag:album"),
        ("$get(namespace:key)", "namespace:key"),
        ("$get artist", None),
        ("$get(artist", None),
        ("$get artist)", None),
        ("$get(var-name)", None),
        ("$get(var.name)", None),
        ("$get(var name)", None),
        ("$get()", None),
        ("$get(a)", "a"),
        (f"$get({'a' * 1000})", "a" * 1000),
    ],
)
def test_get_variable_match(get_pattern: re.Pattern, text: str, expected: str | None) -> None:
    m = get_pattern.match(text)
    assert (m.group(1) if m else None) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("This is $get(artist) and $get(album)", ["artist", "album"])],
)
def test_get_variable_finditer(get_pattern: re.Pattern, text: str, expected: list[str]) -> None:
    names = [m.group(1) for m in get_pattern.finditer(text)]
    assert names == expected


# $set(variable, ...) matching and capture
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$set(artist, value)", "artist"),
        ("$set(album, value)", "album"),
        ("$set(title, value)", "title"),
        ("$set( artist , value)", "artist"),
        ("$set(  artist  , value)", "artist"),
        ("$set(artist , value)", "artist"),
        ("$set( artist, value)", "artist"),
        ("$set(var_ñ, value)", "var_ñ"),
        ("$set(var_中文, value)", "var_中文"),
        ("$set(var_α, value)", "var_α"),
        ("$set(tag:artist, value)", "tag:artist"),
        ("$set(tag:album, value)", "tag:album"),
        ("$set(namespace:key, value)", "namespace:key"),
        ("$set(artist value)", None),
        ("$set(artist)", None),
        ("$set artist, value", None),
        # Matches without closing parenthesis
        ("$set(artist, value", "artist"),
        ("$set(var-name, value)", None),
        ("$set(var.name, value)", None),
        ("$set(var name, value)", None),
        ("$set(a, value)", "a"),
        (f"$set({'a' * 1000}, value)", "a" * 1000),
    ],
)
def test_set_variable_match(set_pattern: re.Pattern, text: str, expected: str | None) -> None:
    m = set_pattern.match(text)
    assert (m.group(1) if m else None) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("This is $set(artist, value) and $set(album, value)", ["artist", "album"])],
)
def test_set_variable_finditer(set_pattern: re.Pattern, text: str, expected: list[str]) -> None:
    names = [m.group(1) for m in set_pattern.finditer(text)]
    assert names == expected


# Full-match variable name pattern
@pytest.mark.parametrize(
    ("name", "should_match"),
    [
        # Basics
        ("artist", True),
        ("album", True),
        ("title", True),
        # Unicode and colons
        ("var_ñ", True),
        ("var_中文", True),
        ("var_α", True),
        ("tag:artist", True),
        ("tag:album", True),
        ("namespace:key", True),
        # Numbers and underscores
        ("var1", True),
        ("var123", True),
        ("var_123", True),
        ("var_name", True),
        ("_private_var", True),
        ("var_with_underscores", True),
        # Compound and edge
        ("artist_extra", True),
        ("extra_artist", True),
        ("artist extra", False),
        ("a", True),
        ("1", True),
        ("_", True),
        (":", True),
        ("var-name", False),
        ("var.name", False),
        ("var name", False),
        ("var@name", False),
        ("", False),
        ("var123_abc:def", True),
        ("_private:key_123", True),
        ("namespace:sub:key", True),
        ("a" * 1000, True),
    ],
)
def test_variable_fullmatch(variable_fullmatch: re.Pattern, name: str, should_match: bool) -> None:
    assert bool(variable_fullmatch.match(name)) is should_match


@pytest.mark.parametrize(
    ("text", "expected_percent", "expected_get", "expected_set"),
    [
        (
            "This is %artist% and $get(album) and $set(title, value)",
            ["artist"],
            ["album"],
            ["title"],
        ),
        (
            "$set(%artist%, $get(album)) and %title%",
            ["artist", "title"],
            ["album"],
            [],  # $set does not match complex first arg
        ),
        (
            "This is %var_ñ% and $get(var_中文) and $set(var_α, value)",
            ["var_ñ"],
            ["var_中文"],
            ["var_α"],
        ),
    ],
)
def test_integration(
    percent_pattern: re.Pattern,
    get_pattern: re.Pattern,
    set_pattern: re.Pattern,
    text: str,
    expected_percent: list[str],
    expected_get: list[str],
    expected_set: list[str],
) -> None:
    percent_names = [m.group(1) for m in percent_pattern.finditer(text)]
    get_names = [m.group(1) for m in get_pattern.finditer(text)]
    set_names = [m.group(1) for m in set_pattern.finditer(text)]

    assert percent_names == expected_percent
    assert get_names == expected_get
    assert set_names == expected_set
