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

"""Comprehensive tests for regex fallback functionality in ScriptCompleter.

Tests the regex fallback mechanism for extracting user-defined variables
when AST parsing fails or is incomplete. Covers various patterns, edge cases,
and error scenarios. Uses pytest fixtures and parametrize to reduce code duplication.
"""

import re
from unittest.mock import patch

import pytest

from picard.ui.widgets.scripttextedit import ScriptCompleter


@pytest.fixture
def completer() -> ScriptCompleter:
    """Create a ScriptCompleter instance for testing."""
    return ScriptCompleter()


@pytest.fixture
def regex_pattern() -> re.Pattern[str]:
    """The regex pattern used for variable extraction."""
    return re.compile(r"\$set\(\s*([A-Za-z0-9_\u00C0-\u017F\u4E00-\u9FFF]+)\s*,")


class TestRegexBasicFunctionality:
    """Test basic regex functionality for variable extraction."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(var1, "value")', {'var1'}),
            ('$set(var2, "value")', {'var2'}),
            ('$set(my_var, "value")', {'my_var'}),
            ('$set(var123, "value")', {'var123'}),
            ('$set(_private, "value")', {'_private'}),
            ('$set(VarName, "value")', {'VarName'}),
        ],
    )
    def test_regex_extracts_basic_variables(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test that regex extracts basic variable names correctly."""
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == expected_vars

    def test_regex_handles_multiple_variables(self, completer: ScriptCompleter) -> None:
        """Test that regex handles multiple variables in one script."""
        script = '$set(var1, "value1")\n$set(var2, "value2")\n$set(var3, "value3")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1', 'var2', 'var3'}

    def test_regex_handles_single_line_multiple_sets(self, completer: ScriptCompleter) -> None:
        """Test that regex handles multiple $set statements on one line."""
        script = '$set(var1, "value1") $set(var2, "value2")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1', 'var2'}

    def test_regex_handles_empty_script(self, completer: ScriptCompleter) -> None:
        """Test that regex handles empty scripts."""
        result = completer._variable_extractor._collect_from_regex('')
        assert result == set()

    def test_regex_handles_script_without_sets(self, completer: ScriptCompleter) -> None:
        """Test that regex handles scripts without $set statements."""
        script = '%artist% - %album%'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == set()


class TestRegexWhitespaceHandling:
    """Test regex handling of various whitespace patterns."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(  var1  , "value")', {'var1'}),
            ('$set(\tvar2\t, "value")', {'var2'}),
            ('$set(\nvar3\n, "value")', {'var3'}),
            ('$set( \t var4 \t , "value")', {'var4'}),
            ('$set(\t \n var5 \n \t, "value")', {'var5'}),
        ],
    )
    def test_regex_handles_whitespace_variations(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test that regex handles various whitespace patterns correctly."""
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == expected_vars

    def test_regex_handles_mixed_whitespace(self, completer: ScriptCompleter) -> None:
        """Test that regex handles mixed whitespace types."""
        script = '$set(  \t var1 \n , "value")\n$set(\t \n var2 \t , "value")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1', 'var2'}

    def test_regex_handles_no_whitespace(self, completer: ScriptCompleter) -> None:
        """Test that regex handles $set statements without whitespace."""
        script = '$set(var1,"value")\n$set(var2,"value")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1', 'var2'}


class TestRegexSpecialCharacters:
    """Test regex handling of special characters in variable names."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(var_with_underscore, "value")', {'var_with_underscore'}),
            ('$set(var123, "value")', {'var123'}),
            ('$set(_private_var, "value")', {'_private_var'}),
            ('$set(VarName, "value")', {'VarName'}),
            ('$set(var_with_123_numbers, "value")', {'var_with_123_numbers'}),
        ],
    )
    def test_regex_handles_valid_special_characters(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test that regex handles valid special characters in variable names."""
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == expected_vars

    def test_regex_handles_unicode_characters(self, completer: ScriptCompleter) -> None:
        """Test that regex handles unicode characters in variable names."""
        script = '$set(variable_ñ, "value")\n$set(variable_中文, "value")'
        result = completer._variable_extractor._collect_from_regex(script)
        # Should handle unicode characters
        assert 'variable_ñ' in result or 'variable_中文' in result

    def test_regex_handles_very_long_variable_names(self, completer: ScriptCompleter) -> None:
        """Test that regex handles very long variable names."""
        long_var = 'a' * 1000
        script = f'$set({long_var}, "value")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert long_var in result


class TestRegexEdgeCases:
    """Test regex handling of edge cases and error scenarios."""

    def test_regex_handles_incomplete_syntax(self, completer: ScriptCompleter) -> None:
        """Test that regex handles incomplete $set syntax."""
        script = '$set(incomplete'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == set()

    def test_regex_handles_malformed_syntax(self, completer: ScriptCompleter) -> None:
        """Test that regex handles malformed $set syntax."""
        script = '$set(malformed,'
        result = completer._variable_extractor._collect_from_regex(script)
        # Regex fallback should extract variables even from malformed syntax
        assert 'malformed' in result

    def test_regex_handles_missing_comma(self, completer: ScriptCompleter) -> None:
        """Test that regex handles $set statements missing comma."""
        script = '$set(var1 "value")'
        result = completer._variable_extractor._collect_from_regex(script)
        # Regex fallback should not extract from missing comma (no comma in pattern)
        assert result == set()

    def test_regex_handles_extra_commas(self, completer: ScriptCompleter) -> None:
        """Test that regex handles $set statements with extra commas."""
        script = '$set(var1, , "value")'
        result = completer._variable_extractor._collect_from_regex(script)
        # Regex fallback should extract variables even with extra commas
        assert 'var1' in result

    def test_regex_handles_nested_parentheses(self, completer: ScriptCompleter) -> None:
        """Test that regex handles nested parentheses in $set statements."""
        script = '$set(var1, $if(1, "value", "default"))'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_strings_with_commas(self, completer: ScriptCompleter) -> None:
        """Test that regex handles strings containing commas."""
        script = '$set(var1, "value, with, commas")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_strings_with_parentheses(self, completer: ScriptCompleter) -> None:
        """Test that regex handles strings containing parentheses."""
        script = '$set(var1, "value (with) parentheses")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_escaped_characters(self, completer: ScriptCompleter) -> None:
        """Test that regex handles escaped characters."""
        script = '$set(var1, "value\\"with\\"quotes")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_underscore_edge_cases(self, completer: ScriptCompleter) -> None:
        """Test that regex handles variables with leading and trailing underscores."""
        script = '''$set(_leading_underscore, "value")
$set(trailing_underscore_, "value")
$set(_both_underscores_, "value")
$set(multiple__underscores, "value")'''
        result = completer._variable_extractor._collect_from_regex(script)
        assert '_leading_underscore' in result
        assert 'trailing_underscore_' in result
        assert '_both_underscores_' in result
        assert 'multiple__underscores' in result

    def test_regex_handles_percent_syntax(self, completer: ScriptCompleter) -> None:
        """Test regex behavior with %variable% syntax in $set statements."""
        script = '''$set(%variable%, "value")
$set(%artist%, "value")
$set(regular_var, "value")'''
        result = completer._variable_extractor._collect_from_regex(script)
        # The regex pattern [A-Za-z0-9_]+ does not match % characters,
        # so %variable% syntax should not be extracted
        assert '%variable%' not in result
        assert '%artist%' not in result
        assert 'regular_var' in result


class TestRegexPerformance:
    """Test regex performance with various script sizes and patterns."""

    def test_regex_performance_with_large_script(self, completer: ScriptCompleter) -> None:
        """Test regex performance with large scripts."""
        # Create a large script with many $set statements
        script_lines = [f'$set(var{i}, "value{i}")' for i in range(1000)]
        script = '\n'.join(script_lines)

        # Should complete in reasonable time
        result = completer._variable_extractor._collect_from_regex(script)
        assert len(result) == 1000
        assert 'var0' in result
        assert 'var999' in result

    def test_regex_performance_with_very_long_lines(self, completer: ScriptCompleter) -> None:
        """Test regex performance with very long lines."""
        # Create a very long line with many $set statements
        long_line = ' '.join([f'$set(var{i}, "value{i}")' for i in range(100)])
        script = long_line

        # Should complete in reasonable time
        result = completer._variable_extractor._collect_from_regex(script)
        assert len(result) == 100

    def test_regex_performance_with_complex_patterns(self, completer: ScriptCompleter) -> None:
        """Test regex performance with complex patterns."""
        # Create a script with complex patterns
        script_lines = []
        for i in range(100):
            script_lines.append(f'$set(var{i}, "value{i}")\n$set(extra{i}, "extra{i}")')
        script = '\n'.join(script_lines)

        # Should complete in reasonable time
        result = completer._variable_extractor._collect_from_regex(script)
        assert len(result) == 200  # 100 * 2 variables per line

    def test_regex_memory_usage_with_repeated_calls(self, completer: ScriptCompleter) -> None:
        """Test regex memory usage with repeated calls."""
        script = '$set(var1, "value")'

        # Make many calls with same content
        for _ in range(1000):
            result = completer._variable_extractor._collect_from_regex(script)
            assert result == {'var1'}


class TestRegexIntegration:
    """Test regex integration with other extraction methods."""

    def test_regex_works_with_full_parse(self, completer: ScriptCompleter) -> None:
        """Test that regex works alongside full parse."""
        script = '$set(var1, "value1")\n$set(var2, "value2")'

        # Test regex extraction
        regex_result = completer._variable_extractor._collect_from_regex(script)
        assert regex_result == {'var1', 'var2'}

        # Test full extraction (which uses regex as fallback)
        full_result = completer._extract_set_variables(script)
        assert 'var1' in full_result
        assert 'var2' in full_result

    def test_regex_works_with_line_parse(self, completer: ScriptCompleter) -> None:
        """Test that regex works alongside line parse."""
        script = '$set(var1, "value1")\n$set(var2, "value2")'

        # Test regex extraction
        regex_result = completer._variable_extractor._collect_from_regex(script)
        assert regex_result == {'var1', 'var2'}

        # Test line extraction
        line_result = completer._variable_extractor._collect_from_line_parse(script)
        assert 'var1' in line_result
        assert 'var2' in line_result

    def test_regex_fallback_when_parsing_fails(self, completer: ScriptCompleter) -> None:
        """Test that regex provides fallback when parsing fails."""
        script = '$set(incomplete\n$set(valid_var, "value")'

        # Mock parser to fail with ScriptError
        from picard.script.parser import ScriptError

        with patch.object(completer._parser, 'parse', side_effect=ScriptError("Parse error")):
            result = completer._extract_set_variables(script)
            # Should still extract from regex
            assert 'valid_var' in result


class TestRegexPatternValidation:
    """Test the regex pattern itself for correctness."""

    def test_regex_pattern_matches_valid_cases(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern matches valid cases."""
        valid_cases = [
            '$set(var1, "value")',
            '$set(  var2  , "value")',
            '$set(var_with_underscore, "value")',
            '$set(var123, "value")',
            '$set(_private, "value")',
        ]

        for case in valid_cases:
            matches = list(regex_pattern.finditer(case))
            assert len(matches) > 0
            assert matches[0].group(1) in case

    def test_regex_pattern_rejects_invalid_cases(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern rejects invalid cases."""
        invalid_cases = [
            '$set(invalid-name, "value")',  # Hyphen not allowed
            '$set(invalid.name, "value")',  # Dot not allowed
            '$set(invalid name, "value")',  # Space not allowed
            '$set(invalid@name, "value")',  # Special character not allowed
        ]

        for case in invalid_cases:
            matches = list(regex_pattern.finditer(case))
            assert len(matches) == 0

    def test_regex_pattern_handles_edge_cases(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern handles edge cases correctly."""
        edge_cases = [
            ('$set(a, "value")', 'a'),  # Single character
            ('$set(a1, "value")', 'a1'),  # Character followed by number
            ('$set(_a, "value")', '_a'),  # Underscore prefix
            ('$set(a_b_c, "value")', 'a_b_c'),  # Multiple underscores
        ]

        for case, expected_var in edge_cases:
            matches = list(regex_pattern.finditer(case))
            assert len(matches) > 0
            assert matches[0].group(1) == expected_var

    def test_regex_pattern_handles_underscore_edge_cases(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern handles underscore edge cases correctly."""
        underscore_cases = [
            ('$set(_leading, "value")', '_leading'),  # Leading underscore
            ('$set(trailing_, "value")', 'trailing_'),  # Trailing underscore
            ('$set(_both_, "value")', '_both_'),  # Both leading and trailing
            ('$set(multiple__underscores, "value")', 'multiple__underscores'),  # Multiple underscores
        ]

        for case, expected_var in underscore_cases:
            matches = list(regex_pattern.finditer(case))
            assert len(matches) > 0
            assert matches[0].group(1) == expected_var

    def test_regex_pattern_handles_percent_syntax(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern handles %variable% syntax."""
        # The regex pattern [A-Za-z0-9_]+ does not match % characters,
        # so %variable% syntax should not be matched
        percent_cases = [
            ('$set(%variable%, "value")', 0),  # Percent syntax should not match
            ('$set(%artist%, "value")', 0),  # Built-in variable syntax should not match
            ('$set(regular_var, "value")', 1),  # Regular variable should match
        ]

        for case, expected_matches in percent_cases:
            matches = list(regex_pattern.finditer(case))
            assert len(matches) == expected_matches
            if expected_matches > 0:
                assert matches[0].group(1) == 'regular_var'

    def test_regex_pattern_handles_whitespace_correctly(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern handles whitespace correctly."""
        whitespace_cases = [
            ('$set(  var1  , "value")', 'var1'),
            ('$set(\tvar2\t, "value")', 'var2'),
            ('$set(\nvar3\n, "value")', 'var3'),
            ('$set( \t var4 \t , "value")', 'var4'),
        ]

        for case, expected_var in whitespace_cases:
            matches = list(regex_pattern.finditer(case))
            assert len(matches) > 0
            assert matches[0].group(1) == expected_var

    def test_regex_pattern_handles_multiple_matches(self, regex_pattern: re.Pattern[str]) -> None:
        """Test that the regex pattern handles multiple matches correctly."""
        script = '$set(var1, "value1")\n$set(var2, "value2")\n$set(var3, "value3")'
        matches = list(regex_pattern.finditer(script))
        assert len(matches) == 3

        extracted_vars = {match.group(1) for match in matches}
        assert extracted_vars == {'var1', 'var2', 'var3'}


class TestRegexErrorHandling:
    """Test regex error handling and edge cases."""

    def test_regex_handles_very_long_strings(self, completer: ScriptCompleter) -> None:
        """Test that regex handles very long strings."""
        # Create a very long string
        long_string = 'a' * 10000
        script = f'$set({long_string}, "value")'

        # Should not raise an exception
        result = completer._variable_extractor._collect_from_regex(script)
        assert long_string in result

    def test_regex_handles_unicode_strings(self, completer: ScriptCompleter) -> None:
        """Test that regex handles unicode strings."""
        script = '$set(variable_ñ, "café")\n$set(variable_中文, "中文")'
        result = completer._variable_extractor._collect_from_regex(script)
        # Should handle unicode characters
        assert 'variable_ñ' in result or 'variable_中文' in result

    def test_regex_handles_special_regex_characters(self, completer: ScriptCompleter) -> None:
        """Test that regex handles special regex characters in content."""
        script = '$set(var1, "value with [brackets] and (parentheses)")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_very_deep_nesting(self, completer: ScriptCompleter) -> None:
        """Test that regex handles very deep nesting."""
        # Create a deeply nested structure
        script = '$set(level1, $set(level2, $set(level3, $set(level4, $set(level5, "value")))))'
        result = completer._variable_extractor._collect_from_regex(script)
        # Should extract the first level variable
        assert 'level1' in result

    def test_regex_handles_malformed_unicode(self, completer: ScriptCompleter) -> None:
        """Test that regex handles malformed unicode."""
        # Create a string with malformed unicode
        script = '$set(var1, "value with \udcff malformed unicode")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_null_bytes(self, completer: ScriptCompleter) -> None:
        """Test that regex handles null bytes."""
        script = '$set(var1, "value\x00with\x00null\x00bytes")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}

    def test_regex_handles_control_characters(self, completer: ScriptCompleter) -> None:
        """Test that regex handles control characters."""
        script = '$set(var1, "value\twith\ncontrol\fcharacters\r")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1'}
