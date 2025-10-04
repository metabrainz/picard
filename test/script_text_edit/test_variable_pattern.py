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
    pattern_get_variable,
    pattern_percent_variable,
    pattern_set_variable,
    pattern_variable_fullmatch,
)


class TestPatternPercentVariable:
    """Test pattern_percent_variable function."""

    def test_pattern_percent_variable_returns_compiled_pattern(self) -> None:
        """Test that pattern_percent_variable returns a compiled regex pattern."""
        pattern = pattern_percent_variable()
        assert isinstance(pattern, re.Pattern)

    def test_pattern_percent_variable_matches_basic_variables(self) -> None:
        """Test that pattern matches basic variable syntax."""
        pattern = pattern_percent_variable()

        # Should match basic variables
        assert pattern.match("%artist%") is not None
        assert pattern.match("%album%") is not None
        assert pattern.match("%title%") is not None

    def test_pattern_percent_variable_captures_variable_name(self) -> None:
        """Test that pattern captures the variable name."""
        pattern = pattern_percent_variable()

        match = pattern.match("%artist%")
        assert match is not None
        assert match.group(1) == "artist"

        match = pattern.match("%album%")
        assert match is not None
        assert match.group(1) == "album"

    def test_pattern_percent_variable_matches_unicode_variables(self) -> None:
        """Test that pattern matches unicode variable names."""
        pattern = pattern_percent_variable()

        # Unicode letters
        assert pattern.match("%var_ñ%") is not None
        assert pattern.match("%var_中文%") is not None
        assert pattern.match("%var_α%") is not None

    def test_pattern_percent_variable_matches_variables_with_colons(self) -> None:
        """Test that pattern matches variables with colons."""
        pattern = pattern_percent_variable()

        assert pattern.match("%tag:artist%") is not None
        assert pattern.match("%tag:album%") is not None
        assert pattern.match("%namespace:key%") is not None

    def test_pattern_percent_variable_matches_variables_with_numbers(self) -> None:
        """Test that pattern matches variables with numbers."""
        pattern = pattern_percent_variable()

        assert pattern.match("%var1%") is not None
        assert pattern.match("%var123%") is not None
        assert pattern.match("%var_123%") is not None

    def test_pattern_percent_variable_matches_variables_with_underscores(self) -> None:
        """Test that pattern matches variables with underscores."""
        pattern = pattern_percent_variable()

        assert pattern.match("%var_name%") is not None
        assert pattern.match("%_private_var%") is not None
        assert pattern.match("%var_with_underscores%") is not None

    def test_pattern_percent_variable_does_not_match_invalid_syntax(self) -> None:
        """Test that pattern does not match invalid syntax."""
        pattern = pattern_percent_variable()

        # Missing percent signs
        assert pattern.match("artist") is None
        assert pattern.match("%artist") is None
        assert pattern.match("artist%") is None

        # Invalid characters
        assert pattern.match("%var-name%") is None
        assert pattern.match("%var.name%") is None
        assert pattern.match("%var name%") is None

        # Empty variable name
        assert pattern.match("%%") is None

    def test_pattern_percent_variable_matches_in_text(self) -> None:
        """Test that pattern matches variables within text."""
        pattern = pattern_percent_variable()

        text = "This is %artist% and %album%"
        matches = list(pattern.finditer(text))
        assert len(matches) == 2
        assert matches[0].group(1) == "artist"
        assert matches[1].group(1) == "album"

    def test_pattern_percent_variable_handles_edge_cases(self) -> None:
        """Test that pattern handles edge cases."""
        pattern = pattern_percent_variable()

        # Single character variable
        assert pattern.match("%a%") is not None
        assert pattern.match("%a%").group(1) == "a"

        # Very long variable name
        long_var = "a" * 1000
        assert pattern.match(f"%{long_var}%") is not None
        assert pattern.match(f"%{long_var}%").group(1) == long_var


class TestPatternGetVariable:
    """Test pattern_get_variable function."""

    def test_pattern_get_variable_returns_compiled_pattern(self) -> None:
        """Test that pattern_get_variable returns a compiled regex pattern."""
        pattern = pattern_get_variable()
        assert isinstance(pattern, re.Pattern)

    def test_pattern_get_variable_matches_basic_syntax(self) -> None:
        """Test that pattern matches basic $get(variable) syntax."""
        pattern = pattern_get_variable()

        assert pattern.match("$get(artist)") is not None
        assert pattern.match("$get(album)") is not None
        assert pattern.match("$get(title)") is not None

    def test_pattern_get_variable_captures_variable_name(self) -> None:
        """Test that pattern captures the variable name."""
        pattern = pattern_get_variable()

        match = pattern.match("$get(artist)")
        assert match is not None
        assert match.group(1) == "artist"

        match = pattern.match("$get(album)")
        assert match is not None
        assert match.group(1) == "album"

    def test_pattern_get_variable_handles_spaces(self) -> None:
        """Test that pattern handles spaces around variable name."""
        pattern = pattern_get_variable()

        assert pattern.match("$get( artist )") is not None
        assert pattern.match("$get(  artist  )") is not None
        assert pattern.match("$get(artist )") is not None
        assert pattern.match("$get( artist)") is not None

    def test_pattern_get_variable_matches_unicode_variables(self) -> None:
        """Test that pattern matches unicode variable names."""
        pattern = pattern_get_variable()

        assert pattern.match("$get(var_ñ)") is not None
        assert pattern.match("$get(var_中文)") is not None
        assert pattern.match("$get(var_α)") is not None

    def test_pattern_get_variable_matches_variables_with_colons(self) -> None:
        """Test that pattern matches variables with colons."""
        pattern = pattern_get_variable()

        assert pattern.match("$get(tag:artist)") is not None
        assert pattern.match("$get(tag:album)") is not None
        assert pattern.match("$get(namespace:key)") is not None

    def test_pattern_get_variable_does_not_match_invalid_syntax(self) -> None:
        """Test that pattern does not match invalid syntax."""
        pattern = pattern_get_variable()

        # Missing parentheses
        assert pattern.match("$get artist") is None
        assert pattern.match("$get(artist") is None
        assert pattern.match("$get artist)") is None

        # Invalid characters in variable name
        assert pattern.match("$get(var-name)") is None
        assert pattern.match("$get(var.name)") is None
        assert pattern.match("$get(var name)") is None

        # Empty variable name
        assert pattern.match("$get()") is None

    def test_pattern_get_variable_matches_in_text(self) -> None:
        """Test that pattern matches $get() calls within text."""
        pattern = pattern_get_variable()

        text = "This is $get(artist) and $get(album)"
        matches = list(pattern.finditer(text))
        assert len(matches) == 2
        assert matches[0].group(1) == "artist"
        assert matches[1].group(1) == "album"

    def test_pattern_get_variable_handles_edge_cases(self) -> None:
        """Test that pattern handles edge cases."""
        pattern = pattern_get_variable()

        # Single character variable
        assert pattern.match("$get(a)") is not None
        assert pattern.match("$get(a)").group(1) == "a"

        # Very long variable name
        long_var = "a" * 1000
        assert pattern.match(f"$get({long_var})") is not None
        assert pattern.match(f"$get({long_var})").group(1) == long_var


class TestPatternSetVariable:
    """Test pattern_set_variable function."""

    def test_pattern_set_variable_returns_compiled_pattern(self) -> None:
        """Test that pattern_set_variable returns a compiled regex pattern."""
        pattern = pattern_set_variable()
        assert isinstance(pattern, re.Pattern)

    def test_pattern_set_variable_matches_basic_syntax(self) -> None:
        """Test that pattern matches basic $set(variable, value) syntax."""
        pattern = pattern_set_variable()

        assert pattern.match("$set(artist, value)") is not None
        assert pattern.match("$set(album, value)") is not None
        assert pattern.match("$set(title, value)") is not None

    def test_pattern_set_variable_captures_variable_name(self) -> None:
        """Test that pattern captures the variable name."""
        pattern = pattern_set_variable()

        match = pattern.match("$set(artist, value)")
        assert match is not None
        assert match.group(1) == "artist"

        match = pattern.match("$set(album, value)")
        assert match is not None
        assert match.group(1) == "album"

    def test_pattern_set_variable_handles_spaces(self) -> None:
        """Test that pattern handles spaces around variable name."""
        pattern = pattern_set_variable()

        assert pattern.match("$set( artist , value)") is not None
        assert pattern.match("$set(  artist  , value)") is not None
        assert pattern.match("$set(artist , value)") is not None
        assert pattern.match("$set( artist, value)") is not None

    def test_pattern_set_variable_matches_unicode_variables(self) -> None:
        """Test that pattern matches unicode variable names."""
        pattern = pattern_set_variable()

        assert pattern.match("$set(var_ñ, value)") is not None
        assert pattern.match("$set(var_中文, value)") is not None
        assert pattern.match("$set(var_α, value)") is not None

    def test_pattern_set_variable_matches_variables_with_colons(self) -> None:
        """Test that pattern matches variables with colons."""
        pattern = pattern_set_variable()

        assert pattern.match("$set(tag:artist, value)") is not None
        assert pattern.match("$set(tag:album, value)") is not None
        assert pattern.match("$set(namespace:key, value)") is not None

    def test_pattern_set_variable_does_not_match_invalid_syntax(self) -> None:
        """Test that pattern does not match invalid syntax."""
        pattern = pattern_set_variable()

        # Missing comma
        assert pattern.match("$set(artist value)") is None
        assert pattern.match("$set(artist)") is None

        # Missing parentheses
        assert pattern.match("$set artist, value") is None
        # Note: The pattern matches $set(artist, even without closing parenthesis
        # because it only looks for the comma, not the full syntax
        assert pattern.match("$set(artist, value") is not None

        # Invalid characters in variable name
        assert pattern.match("$set(var-name, value)") is None
        assert pattern.match("$set(var.name, value)") is None
        assert pattern.match("$set(var name, value)") is None

    def test_pattern_set_variable_matches_in_text(self) -> None:
        """Test that pattern matches $set() calls within text."""
        pattern = pattern_set_variable()

        text = "This is $set(artist, value) and $set(album, value)"
        matches = list(pattern.finditer(text))
        assert len(matches) == 2
        assert matches[0].group(1) == "artist"
        assert matches[1].group(1) == "album"

    def test_pattern_set_variable_handles_edge_cases(self) -> None:
        """Test that pattern handles edge cases."""
        pattern = pattern_set_variable()

        # Single character variable
        assert pattern.match("$set(a, value)") is not None
        assert pattern.match("$set(a, value)").group(1) == "a"

        # Very long variable name
        long_var = "a" * 1000
        assert pattern.match(f"$set({long_var}, value)") is not None
        assert pattern.match(f"$set({long_var}, value)").group(1) == long_var


class TestPatternVariableFullmatch:
    """Test pattern_variable_fullmatch function."""

    def test_pattern_variable_fullmatch_returns_compiled_pattern(self) -> None:
        """Test that pattern_variable_fullmatch returns a compiled regex pattern."""
        pattern = pattern_variable_fullmatch()
        assert isinstance(pattern, re.Pattern)

    def test_pattern_variable_fullmatch_matches_basic_variables(self) -> None:
        """Test that pattern matches basic variable names."""
        pattern = pattern_variable_fullmatch()

        assert pattern.match("artist") is not None
        assert pattern.match("album") is not None
        assert pattern.match("title") is not None

    def test_pattern_variable_fullmatch_matches_unicode_variables(self) -> None:
        """Test that pattern matches unicode variable names."""
        pattern = pattern_variable_fullmatch()

        assert pattern.match("var_ñ") is not None
        assert pattern.match("var_中文") is not None
        assert pattern.match("var_α") is not None

    def test_pattern_variable_fullmatch_matches_variables_with_colons(self) -> None:
        """Test that pattern matches variables with colons."""
        pattern = pattern_variable_fullmatch()

        assert pattern.match("tag:artist") is not None
        assert pattern.match("tag:album") is not None
        assert pattern.match("namespace:key") is not None

    def test_pattern_variable_fullmatch_matches_variables_with_numbers(self) -> None:
        """Test that pattern matches variables with numbers."""
        pattern = pattern_variable_fullmatch()

        assert pattern.match("var1") is not None
        assert pattern.match("var123") is not None
        assert pattern.match("var_123") is not None

    def test_pattern_variable_fullmatch_matches_variables_with_underscores(self) -> None:
        """Test that pattern matches variables with underscores."""
        pattern = pattern_variable_fullmatch()

        assert pattern.match("var_name") is not None
        assert pattern.match("_private_var") is not None
        assert pattern.match("var_with_underscores") is not None

    def test_pattern_variable_fullmatch_does_not_match_invalid_syntax(self) -> None:
        """Test that pattern does not match invalid syntax."""
        pattern = pattern_variable_fullmatch()

        # Invalid characters
        assert pattern.match("var-name") is None
        assert pattern.match("var.name") is None
        assert pattern.match("var name") is None
        assert pattern.match("var@name") is None

        # Empty string
        assert pattern.match("") is None

    def test_pattern_variable_fullmatch_requires_full_match(self) -> None:
        """Test that pattern requires full match."""
        pattern = pattern_variable_fullmatch()

        # The pattern uses + which means one or more, so it matches any valid variable name
        # including compound names like "artist_extra"
        assert pattern.match("artist_extra") is not None
        assert pattern.match("extra_artist") is not None
        # Should not match strings with spaces
        assert pattern.match("artist extra") is None

    def test_pattern_variable_fullmatch_handles_edge_cases(self) -> None:
        """Test that pattern handles edge cases."""
        pattern = pattern_variable_fullmatch()

        # Single character
        assert pattern.match("a") is not None
        assert pattern.match("1") is not None
        assert pattern.match("_") is not None
        assert pattern.match(":") is not None

        # Very long variable name
        long_var = "a" * 1000
        assert pattern.match(long_var) is not None

    def test_pattern_variable_fullmatch_matches_mixed_content(self) -> None:
        """Test that pattern matches mixed content."""
        pattern = pattern_variable_fullmatch()

        assert pattern.match("var123_abc:def") is not None
        assert pattern.match("_private:key_123") is not None
        assert pattern.match("namespace:sub:key") is not None


class TestPatternIntegration:
    """Test integration between different patterns."""

    def test_all_patterns_work_together(self) -> None:
        """Test that all patterns work together without conflicts."""
        percent_pattern = pattern_percent_variable()
        get_pattern = pattern_get_variable()
        set_pattern = pattern_set_variable()

        text = "This is %artist% and $get(album) and $set(title, value)"

        # Should find all patterns
        percent_matches = list(percent_pattern.finditer(text))
        get_matches = list(get_pattern.finditer(text))
        set_matches = list(set_pattern.finditer(text))

        assert len(percent_matches) == 1
        assert len(get_matches) == 1
        assert len(set_matches) == 1

        assert percent_matches[0].group(1) == "artist"
        assert get_matches[0].group(1) == "album"
        assert set_matches[0].group(1) == "title"

    def test_patterns_handle_complex_scenarios(self) -> None:
        """Test that patterns handle complex scenarios."""
        percent_pattern = pattern_percent_variable()
        get_pattern = pattern_get_variable()
        set_pattern = pattern_set_variable()

        text = "$set(%artist%, $get(album)) and %title%"

        # Should find all patterns
        percent_matches = list(percent_pattern.finditer(text))
        get_matches = list(get_pattern.finditer(text))
        set_matches = list(set_pattern.finditer(text))

        assert len(percent_matches) == 2  # %artist% and %title%
        assert len(get_matches) == 1  # $get(album)
        # The set pattern doesn't match $set(%artist%, $get(album)) because
        # it expects a simple variable name, not a complex expression like %artist%
        assert len(set_matches) == 0

    def test_patterns_handle_unicode_content(self) -> None:
        """Test that patterns handle unicode content."""
        percent_pattern = pattern_percent_variable()
        get_pattern = pattern_get_variable()
        set_pattern = pattern_set_variable()

        text = "This is %var_ñ% and $get(var_中文) and $set(var_α, value)"

        # Should find all patterns
        percent_matches = list(percent_pattern.finditer(text))
        get_matches = list(get_pattern.finditer(text))
        set_matches = list(set_pattern.finditer(text))

        assert len(percent_matches) == 1
        assert len(get_matches) == 1
        assert len(set_matches) == 1

        assert percent_matches[0].group(1) == "var_ñ"
        assert get_matches[0].group(1) == "var_中文"
        assert set_matches[0].group(1) == "var_α"
