# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2025 The MusicBrainz Team
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


"""Unit tests for the ContextDetector details API.

Tests `ContextDetector.detect_context_details()`: the completion mode it reports,
the `function_name` and `arg_index` it returns for nested and repeated calls, and
the cases where it deliberately reports no function details.
"""

import pytest

from picard.ui.widgets.context_detector import (
    CompletionMode,
    ContextDetector,
)


@pytest.fixture
def context_detector() -> ContextDetector:
    """Create a ContextDetector instance for testing."""
    return ContextDetector()


class TestContextDetectorDetails:
    """Test ContextDetector's detect_context_details method."""

    @pytest.mark.parametrize(
        ("script", "expected_mode"),
        [
            # Simple contexts
            ("$", CompletionMode.FUNCTION_NAME),
            ("%", CompletionMode.VARIABLE),
            ("$$$", CompletionMode.FUNCTION_NAME),
            ("", CompletionMode.DEFAULT),
            ("   ", CompletionMode.DEFAULT),
            # Only the first argument completes a tag name; later arguments fall back
            # to DEFAULT, whatever the spacing
            ("$set(artist,", CompletionMode.DEFAULT),
            ("$setmulti(artist, album,", CompletionMode.DEFAULT),
            ("$set(artist, album, title,", CompletionMode.DEFAULT),
            ("$set(artist , album ,", CompletionMode.DEFAULT),
            ("$set(  artist  ,  album  ,", CompletionMode.DEFAULT),
            # $$ is a function context only at the end or before a partial name
            ("text $$ more", CompletionMode.DEFAULT),
            # A variable context after a completed call takes precedence
            ("$set(artist, value) %", CompletionMode.VARIABLE),
            # Invalid syntax
            ("$set((", CompletionMode.DEFAULT),
            ("$set(((", CompletionMode.DEFAULT),
            # Names that are not known functions
            ("$func_ñ(", CompletionMode.DEFAULT),
            ("$func-name(", CompletionMode.DEFAULT),
            pytest.param("$" + "a" * 1000 + "(", CompletionMode.DEFAULT, id="very-long-function-name"),
            # Function names are case sensitive
            ("$SET(", CompletionMode.DEFAULT),
            ("$Set(", CompletionMode.DEFAULT),
            # A partial name is still a function context
            ("$func_", CompletionMode.FUNCTION_NAME),
            ("$func1", CompletionMode.FUNCTION_NAME),
        ],
    )
    def test_detect_context_details_mode(
        self,
        context_detector: ContextDetector,
        script: str,
        expected_mode: CompletionMode,
    ) -> None:
        """Test the completion mode reported for a script."""
        assert context_detector.detect_context_details(script)['mode'] == expected_mode

    @pytest.mark.parametrize(
        ("script", "expected_function"),
        [
            # Every function whose first argument is a tag name
            ("$set(", 'set'),
            ("$get(", 'get'),
            ("$unset(", 'unset'),
            ("$getunset(", 'getunset'),
            ("$delete(", 'delete'),
            ("$setmulti(", 'setmulti'),
            ("$copy(", 'copy'),
            ("$copymerge(", 'copymerge'),
            # The most recent, most deeply nested call is the one reported
            ("$set($get(", 'get'),
            ("$set(artist, value) $get(", 'get'),
            ("$set($get($copy(", 'copy'),
        ],
    )
    def test_detect_context_details_tag_name_arg(
        self,
        context_detector: ContextDetector,
        script: str,
        expected_function: str,
    ) -> None:
        """Test that a tag-name argument reports its function name and index."""
        result = context_detector.detect_context_details(script)
        assert result['mode'] == CompletionMode.TAG_NAME_ARG
        assert result['function_name'] == expected_function
        assert result['arg_index'] == 0

    @pytest.mark.parametrize(
        ("script", "expected_mode"),
        [
            ("$unknown(", CompletionMode.DEFAULT),
            ("$unk", CompletionMode.FUNCTION_NAME),
            ("$$", CompletionMode.FUNCTION_NAME),
        ],
    )
    def test_detect_context_details_without_function_details(
        self,
        context_detector: ContextDetector,
        script: str,
        expected_mode: CompletionMode,
    ) -> None:
        """Test that an unresolved function reports no function_name or arg_index."""
        result = context_detector.detect_context_details(script)
        assert result['mode'] == expected_mode
        assert 'function_name' not in result
        assert 'arg_index' not in result
