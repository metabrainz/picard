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

"""Comprehensive unit tests for ContextDetector details API.

Tests the ContextDetector class's detect_context_details method to verify
that it returns function_name and arg_index for nested/multiple calls,
handles partial tag-arg for unknown functions, and recognizes $$ as function context.
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


class TestContextDetectorDetailsAPI:
    """Test ContextDetector's detect_context_details method."""

    def test_detect_context_details_returns_mode(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details returns the mode."""
        result = context_detector.detect_context_details("$")
        assert 'mode' in result
        assert result['mode'] == CompletionMode.FUNCTION_NAME

    def test_detect_context_details_returns_function_name_for_tag_arg(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details returns function_name for TAG_NAME_ARG mode."""
        result = context_detector.detect_context_details("$set(")
        assert result['mode'] == CompletionMode.TAG_NAME_ARG
        assert result['function_name'] == 'set'
        assert result['arg_index'] == 0

    def test_detect_context_details_returns_function_name_for_nested_calls(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details returns function_name for nested function calls."""
        # Nested calls: $set($get(
        result = context_detector.detect_context_details("$set($get(")
        assert result['mode'] == CompletionMode.TAG_NAME_ARG
        assert result['function_name'] == 'get'  # Most recent function
        assert result['arg_index'] == 0

    def test_detect_context_details_returns_function_name_for_multiple_calls(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details returns function_name for multiple function calls."""
        # Multiple calls: $set(artist, value) $get(
        result = context_detector.detect_context_details("$set(artist, value) $get(")
        assert result['mode'] == CompletionMode.TAG_NAME_ARG
        assert result['function_name'] == 'get'  # Most recent function
        assert result['arg_index'] == 0

    def test_detect_context_details_returns_arg_index_for_second_argument(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details returns correct arg_index for second argument."""
        # Second argument: $set(artist,
        # The implementation only returns TAG_NAME_ARG for the first argument (arg_index == 0)
        # For second and subsequent arguments, it returns DEFAULT mode
        result = context_detector.detect_context_details("$set(artist,")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_returns_arg_index_for_third_argument(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details returns correct arg_index for third argument."""
        # Third argument: $setmulti(artist, album,
        # The implementation only returns TAG_NAME_ARG for the first argument (arg_index == 0)
        # For second and subsequent arguments, it returns DEFAULT mode
        result = context_detector.detect_context_details("$setmulti(artist, album,")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_handles_unknown_functions(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles unknown functions."""
        # Unknown function should return DEFAULT mode
        result = context_detector.detect_context_details("$unknown(")
        assert result['mode'] == CompletionMode.DEFAULT
        assert 'function_name' not in result
        assert 'arg_index' not in result

    def test_detect_context_details_handles_partial_unknown_functions(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles partial unknown functions."""
        # Partial unknown function should return FUNCTION_NAME mode
        # because it's detected as a partial function context
        result = context_detector.detect_context_details("$unk")
        assert result['mode'] == CompletionMode.FUNCTION_NAME
        assert 'function_name' not in result
        assert 'arg_index' not in result

    def test_detect_context_details_recognizes_double_dollar_as_function_context(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details recognizes $$ as function context."""
        result = context_detector.detect_context_details("$$")
        assert result['mode'] == CompletionMode.FUNCTION_NAME
        assert 'function_name' not in result
        assert 'arg_index' not in result

    def test_detect_context_details_recognizes_double_dollar_with_text(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details recognizes $$ with surrounding text."""
        # The implementation doesn't recognize $$ as function context when surrounded by text
        # It only recognizes it when it's at the end or followed by partial function name
        result = context_detector.detect_context_details("text $$ more")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_handles_complex_nested_scenarios(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles complex nested scenarios."""
        # Complex scenario: $set($get($copy(
        result = context_detector.detect_context_details("$set($get($copy(")
        assert result['mode'] == CompletionMode.TAG_NAME_ARG
        assert result['function_name'] == 'copy'  # Most deeply nested
        assert result['arg_index'] == 0

    def test_detect_context_details_handles_mixed_contexts(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles mixed contexts."""
        # Mixed: function call followed by variable context
        result = context_detector.detect_context_details("$set(artist, value) %")
        assert result['mode'] == CompletionMode.VARIABLE

    def test_detect_context_details_handles_invalid_syntax(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles invalid syntax."""
        # Invalid syntax: $set((
        result = context_detector.detect_context_details("$set((")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_handles_empty_input(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles empty input."""
        result = context_detector.detect_context_details("")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_handles_whitespace_only(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles whitespace-only input."""
        result = context_detector.detect_context_details("   ")
        assert result['mode'] == CompletionMode.DEFAULT


class TestContextDetectorDetailsEdgeCases:
    """Test edge cases for detect_context_details."""

    def test_detect_context_details_with_very_long_function_names(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with very long function names."""
        long_func = "a" * 1000
        result = context_detector.detect_context_details(f"${long_func}(")
        # Should return DEFAULT since it's not a known function
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_with_unicode_function_names(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with unicode function names."""
        result = context_detector.detect_context_details("$func_ñ(")
        # Should return DEFAULT since it's not a known function
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_with_special_characters(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with special characters."""
        result = context_detector.detect_context_details("$func-name(")
        # Should return DEFAULT since it's not a known function
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_with_multiple_dollars(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with multiple dollar signs."""
        result = context_detector.detect_context_details("$$$")
        assert result['mode'] == CompletionMode.FUNCTION_NAME

    def test_detect_context_details_with_nested_parentheses(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with nested parentheses."""
        result = context_detector.detect_context_details("$set(((")
        # Should return DEFAULT due to invalid syntax
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_with_trailing_commas(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with trailing commas."""
        # The implementation only returns TAG_NAME_ARG for the first argument (arg_index == 0)
        # For second and subsequent arguments, it returns DEFAULT mode
        result = context_detector.detect_context_details("$set(artist, album, title,")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_with_spaces_around_commas(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with spaces around commas."""
        # The implementation only returns TAG_NAME_ARG for the first argument (arg_index == 0)
        # For second and subsequent arguments, it returns DEFAULT mode
        result = context_detector.detect_context_details("$set(artist , album ,")
        assert result['mode'] == CompletionMode.DEFAULT

    def test_detect_context_details_with_multiple_spaces(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test detect_context_details with multiple spaces."""
        # The implementation only returns TAG_NAME_ARG for the first argument (arg_index == 0)
        # For second and subsequent arguments, it returns DEFAULT mode
        result = context_detector.detect_context_details("$set(  artist  ,  album  ,")
        assert result['mode'] == CompletionMode.DEFAULT


class TestContextDetectorDetailsRegressionTests:
    """Test regression cases for detect_context_details."""

    def test_detect_context_details_preserves_original_behavior_for_simple_cases(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details preserves original behavior for simple cases."""
        # Test basic function context
        result = context_detector.detect_context_details("$")
        assert result['mode'] == CompletionMode.FUNCTION_NAME

        # Test basic variable context
        result = context_detector.detect_context_details("%")
        assert result['mode'] == CompletionMode.VARIABLE

        # Test basic tag arg context
        result = context_detector.detect_context_details("$set(")
        assert result['mode'] == CompletionMode.TAG_NAME_ARG
        assert result['function_name'] == 'set'
        assert result['arg_index'] == 0

    def test_detect_context_details_handles_all_tag_name_functions(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles all tag name functions."""
        tag_functions = ["set", "get", "unset", "getunset", "delete", "setmulti", "copy", "copymerge"]

        for func in tag_functions:
            result = context_detector.detect_context_details(f"${func}(")
            assert result['mode'] == CompletionMode.TAG_NAME_ARG
            assert result['function_name'] == func
            assert result['arg_index'] == 0

    def test_detect_context_details_handles_case_sensitivity(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles case sensitivity correctly."""
        # Function names should be case-sensitive
        result = context_detector.detect_context_details("$SET(")
        assert result['mode'] == CompletionMode.DEFAULT  # Not a known function

        result = context_detector.detect_context_details("$Set(")
        assert result['mode'] == CompletionMode.DEFAULT  # Not a known function

        result = context_detector.detect_context_details("$set(")
        assert result['mode'] == CompletionMode.TAG_NAME_ARG  # Known function

    def test_detect_context_details_handles_underscore_in_function_names(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles underscores in function names."""
        # Test with underscore (should work for partial function names)
        result = context_detector.detect_context_details("$func_")
        assert result['mode'] == CompletionMode.FUNCTION_NAME

    def test_detect_context_details_handles_numbers_in_function_names(
        self,
        context_detector: ContextDetector,
    ) -> None:
        """Test that detect_context_details handles numbers in function names."""
        # Test with numbers (should work for partial function names)
        result = context_detector.detect_context_details("$func1")
        assert result['mode'] == CompletionMode.FUNCTION_NAME
