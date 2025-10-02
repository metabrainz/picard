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

"""Comprehensive tests for AST parsing methods in ScriptCompleter.

Tests the AST parsing functionality for extracting user-defined variables
from script content, including edge cases, error handling, and complex
script structures. Uses pytest fixtures and parametrize to reduce code duplication.
"""

from typing import Any
from unittest.mock import Mock, patch

from picard.script.parser import ScriptFunction, ScriptText

import pytest

from picard.ui.widgets.scripttextedit import ScriptCompleter


@pytest.fixture
def completer() -> ScriptCompleter:
    """Create a ScriptCompleter instance for testing."""
    return ScriptCompleter()


@pytest.fixture
def mock_ast_nodes() -> dict[str, Any]:
    """Mock AST nodes for testing."""
    # Create mock ScriptText nodes
    text_node1 = Mock(spec=ScriptText)
    text_node1.__str__ = Mock(return_value="variable1")

    text_node2 = Mock(spec=ScriptText)
    text_node2.__str__ = Mock(return_value="variable2")

    # Create custom mock expression classes that handle __bool__ properly
    class MockExpression1:
        def __iter__(self):
            return iter([text_node1])

        def __bool__(self):
            return True

    class MockExpression2:
        def __iter__(self):
            return iter([text_node2])

        def __bool__(self):
            return True

    expression_node1 = MockExpression1()
    expression_node2 = MockExpression2()

    # Create mock ScriptFunction nodes
    set_function = Mock(spec=ScriptFunction)
    set_function.name = "set"
    set_function.args = [expression_node1, Mock()]

    if_function = Mock(spec=ScriptFunction)
    if_function.name = "if"
    if_function.args = [Mock(), Mock(), Mock()]

    nested_set_function = Mock(spec=ScriptFunction)
    nested_set_function.name = "set"
    nested_set_function.args = [expression_node2, Mock()]

    return {
        'text_node1': text_node1,
        'text_node2': text_node2,
        'expression_node1': expression_node1,
        'expression_node2': expression_node2,
        'set_function': set_function,
        'if_function': if_function,
        'nested_set_function': nested_set_function,
    }


class TestASTTraversal:
    """Test AST traversal and variable extraction."""

    def test_collect_set_variables_from_ast_with_set_function(
        self, completer: ScriptCompleter, mock_ast_nodes: dict[str, Any]
    ) -> None:
        """Test collecting variables from $set function calls."""
        result = set()
        # Mock the _extract_static_name method to return the expected value
        with patch.object(completer._variable_extractor, '_extract_static_name', return_value="variable1"):
            completer._variable_extractor._collect_from_ast(mock_ast_nodes['set_function'], result)
            assert 'variable1' in result

    def test_collect_set_variables_from_ast_with_non_set_function(
        self, completer: ScriptCompleter, mock_ast_nodes: dict[str, Any]
    ) -> None:
        """Test that non-$set functions don't add variables."""
        result = set()
        completer._variable_extractor._collect_from_ast(mock_ast_nodes['if_function'], result)
        assert result == set()

    def test_collect_set_variables_from_ast_with_expression(
        self, completer: ScriptCompleter, mock_ast_nodes: dict[str, Any]
    ) -> None:
        """Test collecting variables from expression nodes."""
        result = set()
        completer._variable_extractor._collect_from_ast(mock_ast_nodes['expression_node1'], result)
        # Expressions themselves don't contain variables, but their children might
        assert result == set()

    def test_collect_set_variables_from_ast_with_nested_functions(self, completer: ScriptCompleter) -> None:
        """Test collecting variables from nested function calls."""
        # Test with a real script that has nested functions
        script = '$set(outer, $if(1, $set(inner, "value"), "default"))'
        result = completer._extract_set_variables(script)
        assert 'outer' in result
        assert 'inner' in result

    def test_collect_set_variables_from_ast_handles_empty_args(self, completer: ScriptCompleter) -> None:
        """Test handling of functions with empty arguments."""
        empty_function = Mock(spec=ScriptFunction)
        empty_function.name = "set"
        empty_function.args = []

        result = set()
        # Should not raise an exception even with empty args
        completer._variable_extractor._collect_from_ast(empty_function, result)
        assert result == set()

    def test_collect_set_variables_from_ast_handles_none_args(self, completer: ScriptCompleter) -> None:
        """Test handling of functions with None arguments."""
        none_function = Mock(spec=ScriptFunction)
        none_function.name = "set"
        none_function.args = [None, None]

        result = set()
        # Should not raise an exception
        completer._variable_extractor._collect_from_ast(none_function, result)
        assert result == set()


class TestStaticNameExtraction:
    """Test static name extraction from AST nodes."""

    def test_extract_static_name_with_valid_expression(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from valid expressions."""
        # Test with a real script that should work
        script = '$set(test_var, "value")'
        result = completer._extract_set_variables(script)
        assert 'test_var' in result

    def test_extract_static_name_with_empty_expression(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from empty expressions."""
        # Test with empty script
        script = ''
        result = completer._extract_set_variables(script)
        assert result == set()

    def test_extract_static_name_with_mixed_tokens(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from expressions with mixed token types."""
        # Test with a script that has mixed content
        script = '$set($if(1, "test", "else"), "value")'
        result = completer._extract_set_variables(script)
        # Should not extract variables from dynamic expressions
        assert result == set()

    def test_extract_static_name_with_non_expression(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from non-expression nodes."""
        text_node = Mock(spec=ScriptText)
        result = completer._variable_extractor._extract_static_name(text_node)
        assert result is None

    def test_extract_static_name_with_whitespace_only(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from expressions with whitespace-only content."""
        # Test with a script that has only whitespace
        script = '   '
        result = completer._extract_set_variables(script)
        assert result == set()

    def test_extract_static_name_with_special_characters(self, completer: ScriptCompleter) -> None:
        """Test extracting static names with special characters."""
        # Test with a script that has special characters
        script = '$set(var_with_underscore, "value")'
        result = completer._extract_set_variables(script)
        assert 'var_with_underscore' in result

    def test_extract_static_name_with_numeric_characters(self, completer: ScriptCompleter) -> None:
        """Test extracting static names with numeric characters."""
        # Test with a script that has numeric characters
        script = '$set(var123, "value")'
        result = completer._extract_set_variables(script)
        assert 'var123' in result


class TestFullParseMethods:
    """Test full parse methods for variable extraction."""

    def test_collect_set_variables_from_full_parse_success(self, completer: ScriptCompleter) -> None:
        """Test successful full parse variable collection."""
        script = '$set(var1, "value1")\n$set(var2, "value2")'
        result = completer._variable_extractor._collect_from_full_parse(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_full_parse_handles_errors(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles parsing errors gracefully."""
        script = '$set(incomplete'
        result = completer._variable_extractor._collect_from_full_parse(script)
        assert result == set()

    def test_collect_set_variables_from_full_parse_handles_empty_script(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles empty scripts."""
        result = completer._variable_extractor._collect_from_full_parse('')
        assert result == set()

    def test_collect_set_variables_from_full_parse_handles_whitespace_only(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles whitespace-only scripts."""
        result = completer._variable_extractor._collect_from_full_parse('   \n\t  \n  ')
        assert result == set()

    def test_collect_set_variables_from_full_parse_handles_complex_script(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles complex scripts."""
        script = '''$set(artist, %artist%)
$set(album, %album%)
$set(combined, $if(%artist%, %artist% - %album%, %album%))'''
        result = completer._variable_extractor._collect_from_full_parse(script)
        assert result == {'artist', 'album', 'combined'}

    def test_collect_set_variables_from_full_parse_handles_nested_functions(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles nested functions."""
        script = '$set(outer, $if(1, $set(inner, "value"), "default"))'
        result = completer._variable_extractor._collect_from_full_parse(script)
        assert 'outer' in result
        assert 'inner' in result


class TestLineParseMethods:
    """Test line-by-line parse methods for variable extraction."""

    def test_collect_set_variables_from_line_parse_success(self, completer: ScriptCompleter) -> None:
        """Test successful line parse variable collection."""
        script = '$set(var1, "value1")\n$set(var2, "value2")'
        result = completer._variable_extractor._collect_from_line_parse(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_line_parse_handles_mixed_valid_invalid(
        self, completer: ScriptCompleter
    ) -> None:
        """Test that line parse handles mixed valid and invalid lines."""
        script = '$set(var1, "value1")\n$set(incomplete\n$set(var2, "value2")'
        result = completer._variable_extractor._collect_from_line_parse(script)
        assert 'var1' in result
        assert 'var2' in result

    def test_collect_set_variables_from_line_parse_handles_empty_lines(self, completer: ScriptCompleter) -> None:
        """Test that line parse handles empty lines."""
        script = '\n\n$set(var1, "value1")\n\n$set(var2, "value2")\n\n'
        result = completer._variable_extractor._collect_from_line_parse(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_line_parse_handles_whitespace_lines(self, completer: ScriptCompleter) -> None:
        """Test that line parse handles whitespace-only lines."""
        script = '   \n\t  \n$set(var1, "value1")\n  \n$set(var2, "value2")\n\t'
        result = completer._variable_extractor._collect_from_line_parse(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_line_parse_handles_single_line(self, completer: ScriptCompleter) -> None:
        """Test that line parse handles single line scripts."""
        script = '$set(var1, "value1")'
        result = completer._variable_extractor._collect_from_line_parse(script)
        assert result == {'var1'}

    def test_collect_set_variables_from_line_parse_handles_no_newlines(self, completer: ScriptCompleter) -> None:
        """Test that line parse handles scripts without newlines."""
        script = '$set(var1, "value1") $set(var2, "value2")'
        result = completer._variable_extractor._collect_from_line_parse(script)
        # Should still work even without newlines
        assert isinstance(result, set)


class TestRegexFallback:
    """Test regex fallback for variable extraction."""

    def test_collect_set_variables_from_regex_basic(self, completer: ScriptCompleter) -> None:
        """Test basic regex extraction."""
        script = '$set(var1, "value1")\n$set(var2, "value2")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_regex_handles_whitespace(self, completer: ScriptCompleter) -> None:
        """Test that regex handles whitespace variations."""
        script = '$set(  var1  , "value1")\n$set(var2, "value2")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_regex_handles_special_characters(self, completer: ScriptCompleter) -> None:
        """Test that regex handles special characters in variable names."""
        script = '$set(var_with_underscore, "value1")\n$set(var123, "value2")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == {'var_with_underscore', 'var123'}

    def test_collect_set_variables_from_regex_handles_incomplete_syntax(self, completer: ScriptCompleter) -> None:
        """Test that regex handles incomplete syntax."""
        script = '$set(var1, "value1")\n$set(incomplete'
        result = completer._variable_extractor._collect_from_regex(script)
        assert 'var1' in result

    def test_collect_set_variables_from_regex_handles_empty_script(self, completer: ScriptCompleter) -> None:
        """Test that regex handles empty scripts."""
        result = completer._variable_extractor._collect_from_regex('')
        assert result == set()

    def test_collect_set_variables_from_regex_handles_no_sets(self, completer: ScriptCompleter) -> None:
        """Test that regex handles scripts without $set statements."""
        script = '%artist% - %album%'
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == set()

    def test_collect_set_variables_from_regex_handles_multiple_same_variable(self, completer: ScriptCompleter) -> None:
        """Test that regex handles multiple $set statements with same variable."""
        script = '$set(var1, "value1")\n$set(var1, "value2")'
        result = completer._variable_extractor._collect_from_regex(script)
        assert 'var1' in result
        assert len(result) == 1


class TestErrorHandling:
    """Test error handling in AST parsing methods."""

    def test_collect_set_variables_from_ast_handles_none_node(self, completer: ScriptCompleter) -> None:
        """Test that AST traversal handles None nodes."""
        result = set()
        # Should not raise an exception
        completer._variable_extractor._collect_from_ast(None, result)
        assert result == set()

    def test_collect_set_variables_from_ast_handles_invalid_node_type(self, completer: ScriptCompleter) -> None:
        """Test that AST traversal handles invalid node types."""
        invalid_node = Mock()
        result = set()
        # Should not raise an exception
        completer._variable_extractor._collect_from_ast(invalid_node, result)
        assert result == set()

    def test_extract_static_name_handles_none_node(self, completer: ScriptCompleter) -> None:
        """Test that static name extraction handles None nodes."""
        result = completer._variable_extractor._extract_static_name(None)
        assert result is None

    def test_extract_static_name_handles_invalid_node_type(self, completer: ScriptCompleter) -> None:
        """Test that static name extraction handles invalid node types."""
        invalid_node = Mock()
        result = completer._variable_extractor._extract_static_name(invalid_node)
        assert result is None

    def test_collect_set_variables_from_full_parse_handles_parser_exception(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles parser exceptions."""
        from picard.script.parser import ScriptError

        with patch.object(completer._parser, 'parse', side_effect=ScriptError("Parser error")):
            result = completer._variable_extractor._collect_from_full_parse('$set(var1, "value")')
            assert result == set()

    def test_collect_set_variables_from_line_parse_handles_parser_exception(self, completer: ScriptCompleter) -> None:
        """Test that line parse handles parser exceptions."""
        from picard.script.parser import ScriptError

        with patch.object(completer._parser, 'parse', side_effect=ScriptError("Parser error")):
            result = completer._variable_extractor._collect_from_line_parse('$set(var1, "value")')
            assert result == set()


class TestComplexScenarios:
    """Test complex scenarios and edge cases."""

    def test_nested_set_functions(self, completer: ScriptCompleter) -> None:
        """Test handling of nested $set functions."""
        script = '$set(outer, $set(inner, "value"))'
        result = completer._extract_set_variables(script)
        assert 'outer' in result
        assert 'inner' in result

    def test_multiple_nested_functions(self, completer: ScriptCompleter) -> None:
        """Test handling of multiple nested functions."""
        script = '''$set(level1, $if(1, $set(level2, "value"), $set(level3, "value")))
$set(level4, $set(level5, $set(level6, "value")))'''
        result = completer._extract_set_variables(script)
        expected_vars = {'level1', 'level2', 'level3', 'level4', 'level5', 'level6'}
        assert result == expected_vars

    def test_very_deep_nesting(self, completer: ScriptCompleter) -> None:
        """Test handling of very deep nesting."""
        # Create a deeply nested structure
        script = '$set(level1, $set(level2, $set(level3, $set(level4, $set(level5, "value")))))'
        result = completer._extract_set_variables(script)
        expected_vars = {'level1', 'level2', 'level3', 'level4', 'level5'}
        assert result == expected_vars

    def test_mixed_function_types(self, completer: ScriptCompleter) -> None:
        """Test handling of mixed function types."""
        script = '''$set(var1, "value1")
$if(1, $set(var2, "value2"), $set(var3, "value3"))
$set(var4, $if(1, "true", "false"))'''
        result = completer._extract_set_variables(script)
        expected_vars = {'var1', 'var2', 'var3', 'var4'}
        assert result == expected_vars

    def test_unicode_variable_names(self, completer: ScriptCompleter) -> None:
        """Test handling of unicode variable names."""
        script = '$set(variable_ñ, "value")\n$set(variable_中文, "value")'
        result = completer._extract_set_variables(script)
        # Should handle unicode characters
        assert 'variable_ñ' in result or 'variable_中文' in result

    def test_very_long_variable_names(self, completer: ScriptCompleter) -> None:
        """Test handling of very long variable names."""
        long_var = 'a' * 1000
        script = f'$set({long_var}, "value")'
        result = completer._extract_set_variables(script)
        assert long_var in result

    def test_special_characters_in_variable_names(self, completer: ScriptCompleter) -> None:
        """Test handling of special characters in variable names."""
        script = '$set(var_with_underscore, "value")\n$set(var123, "value")'
        result = completer._extract_set_variables(script)
        assert 'var_with_underscore' in result
        assert 'var123' in result

    def test_multiple_same_variable_different_cases(self, completer: ScriptCompleter) -> None:
        """Test handling of multiple $set statements with same variable name."""
        script = '$set(var1, "value1")\n$set(var1, "value2")\n$set(var1, "value3")'
        result = completer._extract_set_variables(script)
        assert 'var1' in result
        assert len(result) == 1

    def test_script_with_comments(self, completer: ScriptCompleter) -> None:
        """Test handling of scripts with comments."""
        script = '''// This is a comment
$set(var1, "value1")
/* Another comment */
$set(var2, "value2")'''
        result = completer._extract_set_variables(script)
        assert 'var1' in result
        assert 'var2' in result

    def test_script_with_strings_containing_set(self, completer: ScriptCompleter) -> None:
        """Test handling of strings containing 'set'."""
        script = '$set(var1, "This contains $set in a string")\n$set(var2, "value2")'
        result = completer._extract_set_variables(script)
        assert 'var1' in result
        assert 'var2' in result

    def test_script_with_underscore_edge_cases(self, completer: ScriptCompleter) -> None:
        """Test handling of variables with leading and trailing underscores."""
        script = '''$set(_leading_underscore, "value")
$set(trailing_underscore_, "value")
$set(_both_underscores_, "value")
$set(multiple__underscores, "value")'''
        result = completer._extract_set_variables(script)
        assert '_leading_underscore' in result
        assert 'trailing_underscore_' in result
        assert '_both_underscores_' in result
        assert 'multiple__underscores' in result

    def test_script_with_percent_syntax(self, completer: ScriptCompleter) -> None:
        """Test behavior with %variable% syntax in $set statements."""
        script = '''$set(%variable%, "value")
$set(%artist%, "value")
$set(regular_var, "value")'''
        result = completer._extract_set_variables(script)
        # The regex pattern [A-Za-z0-9_]+ does not match % characters,
        # so %variable% syntax should not be extracted
        assert '%variable%' not in result
        assert '%artist%' not in result
        assert 'regular_var' in result
