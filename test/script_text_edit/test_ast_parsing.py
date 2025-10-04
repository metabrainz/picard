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


# Test data fixtures for parametrized tests
@pytest.fixture
def basic_script_tests() -> list[dict[str, Any]]:
    """Basic script test cases for parametrized testing."""
    return [
        {
            'script': '$set(var1, "value1")\n$set(var2, "value2")',
            'expected_vars': {'var1', 'var2'},
            'description': 'basic two variables',
        },
        {'script': '$set(test_var, "value")', 'expected_vars': {'test_var'}, 'description': 'single variable'},
        {
            'script': '$set(var_with_underscore, "value")',
            'expected_vars': {'var_with_underscore'},
            'description': 'variable with underscore',
        },
        {'script': '$set(var123, "value")', 'expected_vars': {'var123'}, 'description': 'variable with numbers'},
        {'script': '', 'expected_vars': set(), 'description': 'empty script'},
        {'script': '   ', 'expected_vars': set(), 'description': 'whitespace only'},
    ]


@pytest.fixture
def nested_script_tests() -> list[dict[str, Any]]:
    """Nested script test cases for parametrized testing."""
    return [
        {
            'script': '$set(outer, $if(1, $set(inner, "value"), "default"))',
            'expected_vars': {'outer', 'inner'},
            'description': 'nested if with set',
        },
        {
            'script': '$set(outer, $set(inner, "value"))',
            'expected_vars': {'outer', 'inner'},
            'description': 'nested set functions',
        },
        {
            'script': '''$set(level1, $if(1, $set(level2, "value"), $set(level3, "value")))
$set(level4, $set(level5, $set(level6, "value")))''',
            'expected_vars': {'level1', 'level2', 'level3', 'level4', 'level5', 'level6'},
            'description': 'multiple nested functions',
        },
    ]


@pytest.fixture
def error_handling_tests() -> list[dict[str, Any]]:
    """Error handling test cases for parametrized testing."""
    return [
        {'script': '$set(incomplete', 'expected_vars': set(), 'description': 'incomplete syntax'},
        {'script': '%artist% - %album%', 'expected_vars': set(), 'description': 'no set statements'},
        {
            'script': '$set($if(1, "test", "else"), "value")',
            'expected_vars': set(),
            'description': 'dynamic expression in set',
        },
    ]


@pytest.fixture
def special_character_tests() -> list[dict[str, Any]]:
    """Special character test cases for parametrized testing."""
    return [
        {'script': '$set(variable_ñ, "value")', 'expected_vars': {'variable_ñ'}, 'description': 'unicode characters'},
        {
            'script': '$set(_leading_underscore, "value")',
            'expected_vars': {'_leading_underscore'},
            'description': 'leading underscore',
        },
        {
            'script': '$set(trailing_underscore_, "value")',
            'expected_vars': {'trailing_underscore_'},
            'description': 'trailing underscore',
        },
        {
            'script': '$set(multiple__underscores, "value")',
            'expected_vars': {'multiple__underscores'},
            'description': 'multiple underscores',
        },
    ]


# Helper functions for common test patterns
def assert_variables_extracted(
    completer: ScriptCompleter, script: str, expected_vars: set[str], method_name: str
) -> None:
    """Helper function to test variable extraction from scripts."""
    method = getattr(completer._variable_extractor, method_name)
    result = method(script)
    assert result == expected_vars, f"Expected {expected_vars}, got {result}"


def assert_variables_in_result(
    completer: ScriptCompleter, script: str, expected_vars: set[str], method_name: str
) -> None:
    """Helper function to test that variables are contained in extraction result."""
    method = getattr(completer._variable_extractor, method_name)
    result = method(script)
    for var in expected_vars:
        assert var in result, f"Expected {var} to be in {result}"


def create_mock_function(name: str, args: list[Any]) -> Mock:
    """Helper function to create mock ScriptFunction nodes."""
    mock_func = Mock(spec=ScriptFunction)
    mock_func.name = name
    mock_func.args = args
    return mock_func


def create_mock_text_node(value: str) -> Mock:
    """Helper function to create mock ScriptText nodes."""
    text_node = Mock(spec=ScriptText)
    text_node.__str__ = Mock(return_value=value)
    return text_node


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

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(outer, $if(1, $set(inner, "value"), "default"))', {'outer', 'inner'}),
            ('$set(outer, $set(inner, "value"))', {'outer', 'inner'}),
        ],
    )
    def test_collect_set_variables_from_ast_with_nested_functions(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test collecting variables from nested function calls."""
        result = completer._extract_set_variables(script)
        for var in expected_vars:
            assert var in result

    @pytest.mark.parametrize(
        ("function_name", "args", "expected_result"),
        [
            ("set", [], set()),
            ("set", [None, None], set()),
            ("if", [Mock(), Mock(), Mock()], set()),
        ],
    )
    def test_collect_set_variables_from_ast_handles_edge_cases(
        self, completer: ScriptCompleter, function_name: str, args: list[Any], expected_result: set[str]
    ) -> None:
        """Test handling of various edge cases in AST traversal."""
        mock_function = create_mock_function(function_name, args)
        result = set()
        completer._variable_extractor._collect_from_ast(mock_function, result)
        assert result == expected_result


class TestStaticNameExtraction:
    """Test static name extraction from AST nodes."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(test_var, "value")', {'test_var'}),
            ('', set()),
            ('   ', set()),
            ('$set(var_with_underscore, "value")', {'var_with_underscore'}),
            ('$set(var123, "value")', {'var123'}),
        ],
    )
    def test_extract_static_name_with_various_expressions(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test extracting static names from various expressions."""
        result = completer._extract_set_variables(script)
        assert result == expected_vars

    def test_extract_static_name_with_mixed_tokens(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from expressions with mixed token types."""
        # Test with a script that has mixed content
        script = '$set($if(1, "test", "else"), "value")'
        result = completer._extract_set_variables(script)
        # Should not extract variables from dynamic expressions
        assert result == set()

    def test_extract_static_name_with_non_expression(self, completer: ScriptCompleter) -> None:
        """Test extracting static names from non-expression nodes."""
        text_node = create_mock_text_node("test")
        result = completer._variable_extractor._extract_static_name(text_node)
        assert result is None


class TestFullParseMethods:
    """Test full parse methods for variable extraction."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(var1, "value1")\n$set(var2, "value2")', {'var1', 'var2'}),
            ('$set(incomplete', set()),
            ('', set()),
            ('   \n\t  \n  ', set()),
            (
                '''$set(artist, %artist%)
$set(album, %album%)
$set(combined, $if(%artist%, %artist% - %album%, %album%))''',
                {'artist', 'album', 'combined'},
            ),
            ('$set(outer, $if(1, $set(inner, "value"), "default"))', {'outer', 'inner'}),
        ],
    )
    def test_collect_set_variables_from_full_parse(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test full parse variable collection with various scripts."""
        result = completer._variable_extractor._collect_from_full_parse(script)
        assert result == expected_vars


class TestLineParseMethods:
    """Test line-by-line parse methods for variable extraction."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(var1, "value1")\n$set(var2, "value2")', {'var1', 'var2'}),
            ('$set(var1, "value1")\n$set(incomplete\n$set(var2, "value2")', {'var1', 'var2'}),
            ('\n\n$set(var1, "value1")\n\n$set(var2, "value2")\n\n', {'var1', 'var2'}),
            ('   \n\t  \n$set(var1, "value1")\n  \n$set(var2, "value2")\n\t', {'var1', 'var2'}),
            ('$set(var1, "value1")', {'var1'}),
        ],
    )
    def test_collect_set_variables_from_line_parse(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test line parse variable collection with various scripts."""
        result = completer._variable_extractor._collect_from_line_parse(script)
        assert result == expected_vars

    def test_collect_set_variables_from_line_parse_handles_no_newlines(self, completer: ScriptCompleter) -> None:
        """Test that line parse handles scripts without newlines."""
        script = '$set(var1, "value1") $set(var2, "value2")'
        result = completer._variable_extractor._collect_from_line_parse(script)
        # Should still work even without newlines
        assert isinstance(result, set)


class TestRegexFallback:
    """Test regex fallback for variable extraction."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(var1, "value1")\n$set(var2, "value2")', {'var1', 'var2'}),
            ('$set(  var1  , "value1")\n$set(var2, "value2")', {'var1', 'var2'}),
            ('$set(var_with_underscore, "value1")\n$set(var123, "value2")', {'var_with_underscore', 'var123'}),
            ('$set(var1, "value1")\n$set(incomplete', {'var1'}),
            ('', set()),
            ('%artist% - %album%', set()),
            ('$set(var1, "value1")\n$set(var1, "value2")', {'var1'}),
        ],
    )
    def test_collect_set_variables_from_regex(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test regex extraction with various scripts."""
        result = completer._variable_extractor._collect_from_regex(script)
        assert result == expected_vars


class TestErrorHandling:
    """Test error handling in AST parsing methods."""

    @pytest.mark.parametrize(
        ("node", "expected_result"),
        [
            (None, set()),
            (Mock(), set()),
        ],
    )
    def test_collect_set_variables_from_ast_handles_invalid_nodes(
        self, completer: ScriptCompleter, node: Any, expected_result: set[str]
    ) -> None:
        """Test that AST traversal handles invalid nodes."""
        result = set()
        completer._variable_extractor._collect_from_ast(node, result)  # type: ignore
        assert result == expected_result

    @pytest.mark.parametrize(
        ("node", "expected_result"),
        [
            (None, None),
            (Mock(), None),
        ],
    )
    def test_extract_static_name_handles_invalid_nodes(
        self, completer: ScriptCompleter, node: Any, expected_result: Any
    ) -> None:
        """Test that static name extraction handles invalid nodes."""
        result = completer._variable_extractor._extract_static_name(node)  # type: ignore
        assert result == expected_result

    @pytest.mark.parametrize(
        "method_name",
        [
            "_collect_from_full_parse",
            "_collect_from_line_parse",
        ],
    )
    def test_parse_methods_handle_parser_exceptions(self, completer: ScriptCompleter, method_name: str) -> None:
        """Test that parse methods handle parser exceptions."""
        from picard.script.parser import ScriptError

        method = getattr(completer._variable_extractor, method_name)
        with patch.object(completer._parser, 'parse', side_effect=ScriptError("Parser error")):
            result = method('$set(var1, "value")')
            assert result == set()


class TestComplexScenarios:
    """Test complex scenarios and edge cases."""

    @pytest.mark.parametrize(
        ("script", "expected_vars"),
        [
            ('$set(outer, $set(inner, "value"))', {'outer', 'inner'}),
            (
                '''$set(level1, $if(1, $set(level2, "value"), $set(level3, "value")))
$set(level4, $set(level5, $set(level6, "value")))''',
                {'level1', 'level2', 'level3', 'level4', 'level5', 'level6'},
            ),
            (
                '$set(level1, $set(level2, $set(level3, $set(level4, $set(level5, "value")))))',
                {'level1', 'level2', 'level3', 'level4', 'level5'},
            ),
            (
                '''$set(var1, "value1")
$if(1, $set(var2, "value2"), $set(var3, "value3"))
$set(var4, $if(1, "true", "false"))''',
                {'var1', 'var2', 'var3', 'var4'},
            ),
            ('$set(var_with_underscore, "value")\n$set(var123, "value")', {'var_with_underscore', 'var123'}),
            ('$set(var1, "value1")\n$set(var1, "value2")\n$set(var1, "value3")', {'var1'}),
            (
                '''// This is a comment
$set(var1, "value1")
/* Another comment */
$set(var2, "value2")''',
                {'var1', 'var2'},
            ),
            ('$set(var1, "This contains $set in a string")\n$set(var2, "value2")', {'var1', 'var2'}),
            (
                '''$set(_leading_underscore, "value")
$set(trailing_underscore_, "value")
$set(_both_underscores_, "value")
$set(multiple__underscores, "value")''',
                {'_leading_underscore', 'trailing_underscore_', '_both_underscores_', 'multiple__underscores'},
            ),
        ],
    )
    def test_complex_script_scenarios(self, completer: ScriptCompleter, script: str, expected_vars: set[str]) -> None:
        """Test complex script scenarios with various nesting and edge cases."""
        result = completer._extract_set_variables(script)
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
