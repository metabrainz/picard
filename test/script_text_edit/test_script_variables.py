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

"""Unit tests for script variables functionality."""

from picard.extension_points.script_variables import _is_valid_plugin_variable_name

import pytest


class TestIsValidPluginVariableName:
    """Test the _is_valid_plugin_variable_name function."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            # Basic valid names
            "artist",
            "album",
            "title",
            "year",
            "tracknumber",
            # Names with underscores
            "artist_name",
            "album_artist",
            "track_number",
            "release_date",
            # Names with digits
            "track1",
            "album2",
            "year2023",
            "test123",
            # Mixed case
            "Artist",
            "AlbumTitle",
            "TrackNumber",
            # Names with colons (allowed by pattern)
            "artist:name",
            "album:title",
            "track:number",
            # Unicode characters
            "artista",
            "álbum",
            "título",
            "год",
            "アーティスト",
            # Long names
            "very_long_variable_name_with_underscores",
            "VeryLongVariableNameWithMixedCase",
            # Single character
            "a",
            "A",
            "1",
            "_",
            ":",
            # Names starting with underscore
            "_private",
            "_internal",
            # Names starting with colon
            ":namespace",
            ":global",
        ],
    )
    def test_valid_variable_names(self, valid_name: str) -> None:
        """Test that valid variable names return True."""
        assert _is_valid_plugin_variable_name(valid_name) is True

    @pytest.mark.parametrize(
        "invalid_name",
        [
            # Empty string
            "",
            # Names with spaces
            "artist name",
            "album title",
            "track number",
            # Names with special characters (not in \w or :)
            "artist-name",
            "album.title",
            "track@number",
            "artist#name",
            "album$title",
            "track%number",
            "artist&name",
            "album*title",
            "track+number",
            "artist=name",
            "album<title",
            "track>number",
            "artist!name",
            "album?title",
            "track^number",
            "artist|name",
            "album\\title",
            "track/number",
            "artist(name",
            "album)title",
            "track{number",
            "artist}name",
            "album[title",
            "track]number",
            "artist;name",
            "album'title",
            "track\"number",
            "artist,name",
            "track~number",
            "artist`name",
            # Names with newlines or tabs
            "artist\nname",
            "album\ttitle",
            "track\rnumber",
            # Names with control characters
            "artist\x00name",
            "album\x01title",
            # Names with only special characters
            "---",
            "...",
            "###",
            "$$$",
            "%%%",
            "&&&",
            "***",
            "+++",
            "===",
            "<<<",
            ">>>",
            "!!!",
            "???",
            "^^^",
            "|||",
            "\\\\\\",
            "///",
            "(((",
            ")))",
            "{{{",
            "}}}",
            "[[[",
            "]]]",
            ";;;",
            "'''",
            '"""',
            ",,,",
            "~~~",
            "```",
        ],
    )
    def test_invalid_variable_names(self, invalid_name: str) -> None:
        """Test that invalid variable names return False."""
        assert _is_valid_plugin_variable_name(invalid_name) is False

    @pytest.mark.parametrize(
        "non_string_input",
        [
            None,
            123,
            456.789,
            True,
            False,
            [],
            {},
            set(),
            tuple(),
            object(),
            lambda: None,
        ],
    )
    def test_non_string_inputs(self, non_string_input) -> None:
        """Test that non-string inputs return False."""
        assert _is_valid_plugin_variable_name(non_string_input) is False

    def test_empty_string(self) -> None:
        """Test that empty string returns False."""
        assert _is_valid_plugin_variable_name("") is False

    def test_whitespace_only_strings(self) -> None:
        """Test that whitespace-only strings return False."""
        assert _is_valid_plugin_variable_name(" ") is False
        assert _is_valid_plugin_variable_name("  ") is False
        assert _is_valid_plugin_variable_name("\t") is False
        assert _is_valid_plugin_variable_name("\n") is False
        assert _is_valid_plugin_variable_name("\r") is False
        assert _is_valid_plugin_variable_name(" \t\n\r ") is False

    def test_unicode_edge_cases(self) -> None:
        """Test Unicode edge cases."""
        # Valid Unicode letters
        assert _is_valid_plugin_variable_name("café") is True
        assert _is_valid_plugin_variable_name("naïve") is True
        assert _is_valid_plugin_variable_name("résumé") is True
        assert _is_valid_plugin_variable_name("Москва") is True
        assert _is_valid_plugin_variable_name("北京") is True
        assert _is_valid_plugin_variable_name("東京") is True

        # Invalid Unicode characters
        assert _is_valid_plugin_variable_name("café-") is False
        assert _is_valid_plugin_variable_name("naïve ") is False
        assert _is_valid_plugin_variable_name("résumé.") is False

    def test_colon_usage(self) -> None:
        """Test colon usage in variable names."""
        # Valid colon usage
        assert _is_valid_plugin_variable_name("artist:name") is True
        assert _is_valid_plugin_variable_name("album:title") is True
        assert _is_valid_plugin_variable_name("track:number") is True
        assert _is_valid_plugin_variable_name(":global") is True
        assert _is_valid_plugin_variable_name(":namespace:variable") is True
        assert _is_valid_plugin_variable_name("artist:") is True  # Ends with colon (allowed)
        assert _is_valid_plugin_variable_name(":") is True  # Only colon (allowed)
        assert _is_valid_plugin_variable_name("::") is True  # Multiple colons (allowed)

    def test_underscore_usage(self) -> None:
        """Test underscore usage in variable names."""
        # Valid underscore usage
        assert _is_valid_plugin_variable_name("_private") is True
        assert _is_valid_plugin_variable_name("__internal") is True
        assert _is_valid_plugin_variable_name("artist_name") is True
        assert _is_valid_plugin_variable_name("album_artist") is True
        assert _is_valid_plugin_variable_name("_") is True

        # Edge cases with underscores
        assert _is_valid_plugin_variable_name("_a") is True
        assert _is_valid_plugin_variable_name("a_") is True
        assert _is_valid_plugin_variable_name("__") is True

    def test_digit_usage(self) -> None:
        """Test digit usage in variable names."""
        # Valid digit usage
        assert _is_valid_plugin_variable_name("track1") is True
        assert _is_valid_plugin_variable_name("album2") is True
        assert _is_valid_plugin_variable_name("year2023") is True
        assert _is_valid_plugin_variable_name("test123") is True
        assert _is_valid_plugin_variable_name("1") is True
        assert _is_valid_plugin_variable_name("123") is True

        # Names starting with digits (should be valid)
        assert _is_valid_plugin_variable_name("1track") is True
        assert _is_valid_plugin_variable_name("2album") is True
        assert _is_valid_plugin_variable_name("2023year") is True

    def test_mixed_valid_characters(self) -> None:
        """Test combinations of valid characters."""
        # Letters, digits, underscores, and colons
        assert _is_valid_plugin_variable_name("artist_name_2023") is True
        assert _is_valid_plugin_variable_name("album:title_2023") is True
        assert _is_valid_plugin_variable_name("track:number_1") is True
        assert _is_valid_plugin_variable_name("_private:variable_123") is True
        assert _is_valid_plugin_variable_name("a1b2c3:d4e5f6") is True

    def test_case_sensitivity(self) -> None:
        """Test that variable names are case sensitive."""
        # Different cases should be treated as different names
        assert _is_valid_plugin_variable_name("artist") is True
        assert _is_valid_plugin_variable_name("Artist") is True
        assert _is_valid_plugin_variable_name("ARTIST") is True
        assert _is_valid_plugin_variable_name("ArTiSt") is True

    def test_very_long_names(self) -> None:
        """Test very long variable names."""
        # Very long valid name
        long_name = "a" * 1000
        assert _is_valid_plugin_variable_name(long_name) is True

        # Very long name with mixed characters
        long_mixed_name = "a1b2c3d4e5f6g7h8i9j0" * 50
        assert _is_valid_plugin_variable_name(long_mixed_name) is True

    def test_boundary_conditions(self) -> None:
        """Test boundary conditions."""
        # Single character tests
        assert _is_valid_plugin_variable_name("a") is True
        assert _is_valid_plugin_variable_name("A") is True
        assert _is_valid_plugin_variable_name("1") is True
        assert _is_valid_plugin_variable_name("_") is True
        assert _is_valid_plugin_variable_name(":") is True

        # Two character tests
        assert _is_valid_plugin_variable_name("ab") is True
        assert _is_valid_plugin_variable_name("a1") is True
        assert _is_valid_plugin_variable_name("a_") is True
        assert _is_valid_plugin_variable_name("a:") is True
        assert _is_valid_plugin_variable_name("_a") is True
        assert _is_valid_plugin_variable_name(":a") is True
