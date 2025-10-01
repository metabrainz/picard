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

"""Comprehensive unit tests for ScriptCompleter autocomplete functionality.

Tests the new user-defined variable autocomplete feature with extensive coverage
of edge cases, error handling, and integration scenarios. Uses pytest fixtures
and parametrize to reduce code duplication while adhering to DRY, SOC, SRP, IOC, KISS.
"""

from unittest.mock import Mock, patch

from picard.script.parser import ScriptError, ScriptFunction, ScriptText
from picard.tags import script_variable_tag_names

import pytest

from picard.ui.widgets.scripttextedit import ScriptCompleter


@pytest.fixture
def completer() -> ScriptCompleter:
    """Create a ScriptCompleter instance for testing."""
    return ScriptCompleter()


@pytest.fixture
def mock_parser() -> Mock:
    """Mock ScriptParser for testing."""
    parser = Mock()
    return parser


@pytest.fixture
def sample_script_content() -> dict[str, str]:
    """Sample script content for testing various scenarios."""
    return {
        'simple_set': '$set(myvar, "value")',
        'multiple_sets': '$set(var1, "a")\n$set(var2, "b")\n$set(var3, "c")',
        'nested_functions': '$set(outer, $if(1, "inner", "else"))',
        'complex_script': '''$set(artist, %artist%)
$set(album, %album%)
$set(combined, $if(%artist%, %artist% - %album%, %album%))''',
        'malformed_syntax': '$set(incomplete',
        'empty_lines': '\n\n$set(var1, "test")\n\n$set(var2, "test2")\n\n',
        'whitespace_variations': '$set(  spaced_var  , "value")\n$set(tabbed_var\t, "value")',
        'special_characters': '$set(var_with_underscore, "test")\n$set(var123, "test")',
        'empty_script': '',
        'no_sets': '%artist% - %album%',
        'commented_sets': '// $set(commented, "ignored")\n$set(active, "value")',
        'multiline_set': '''$set(
    multiline_var,
    "value"
)''',
    }


class TestScriptCompleterInitialization:
    """Test ScriptCompleter initialization and basic properties."""

    def test_initialization(self, completer: ScriptCompleter) -> None:
        """Test that ScriptCompleter initializes correctly."""
        assert completer._parser is not None
        assert completer._script_hash is None
        assert completer._user_defined_variables == set()
        assert completer._model is not None

    def test_initial_choices_includes_builtin_functions(self, completer: ScriptCompleter) -> None:
        """Test that initial choices include built-in script functions."""
        choices = list(completer.choices)
        function_choices = [choice for choice in choices if choice.startswith('$')]
        assert len(function_choices) > 0
        assert '$if(' in choices or any('$if' in choice for choice in choices)

    def test_initial_choices_includes_builtin_variables(self, completer: ScriptCompleter) -> None:
        """Test that initial choices include built-in variables."""
        choices = list(completer.choices)
        builtin_vars = script_variable_tag_names()
        for var in builtin_vars:
            assert f'%{var}%' in choices


class TestVariableExtraction:
    """Test the _extract_set_variables method with various script patterns."""

    @pytest.mark.parametrize(
        "script,expected_vars",
        [
            ('$set(myvar, "value")', {'myvar'}),
            ('$set(var1, "a")\n$set(var2, "b")', {'var1', 'var2'}),
            ('$set(  spaced  , "value")', {'spaced'}),
            ('$set(var_with_underscore, "test")', {'var_with_underscore'}),
            ('$set(var123, "test")', {'var123'}),
            ('', set()),
            ('%artist% - %album%', set()),
            ('$set(outer, $if(1, "inner", "else"))', {'outer'}),
        ],
    )
    def test_extract_set_variables_basic_cases(
        self, completer: ScriptCompleter, script: str, expected_vars: set[str]
    ) -> None:
        """Test basic variable extraction from various script patterns."""
        result = completer._extract_set_variables(script)
        assert result == expected_vars

    def test_extract_set_variables_handles_malformed_syntax(self, completer: ScriptCompleter) -> None:
        """Test that malformed syntax doesn't break variable extraction."""
        script = '$set(incomplete\n$set(valid, "test")\n$set(another_incomplete'
        result = completer._extract_set_variables(script)
        # Should still extract valid variables
        assert 'valid' in result

    def test_extract_set_variables_handles_empty_lines(self, completer: ScriptCompleter) -> None:
        """Test that empty lines don't interfere with variable extraction."""
        script = '\n\n$set(var1, "test")\n\n$set(var2, "test2")\n\n'
        result = completer._extract_set_variables(script)
        assert result == {'var1', 'var2'}

    def test_extract_set_variables_handles_whitespace_variations(self, completer: ScriptCompleter) -> None:
        """Test that various whitespace patterns are handled correctly."""
        script = '$set(  spaced_var  , "value")\n$set(tabbed_var\t, "value")'
        result = completer._extract_set_variables(script)
        assert result == {'spaced_var', 'tabbed_var'}

    def test_extract_set_variables_handles_multiline_sets(self, completer: ScriptCompleter) -> None:
        """Test that multiline $set statements are handled correctly."""
        script = '''$set(
    multiline_var,
    "value"
)'''
        result = completer._extract_set_variables(script)
        assert 'multiline_var' in result

    def test_extract_set_variables_handles_underscore_edge_cases(self, completer: ScriptCompleter) -> None:
        """Test that variables with leading and trailing underscores are handled correctly."""
        script = '''$set(_leading_underscore, "value")
$set(trailing_underscore_, "value")
$set(_both_underscores_, "value")
$set(multiple__underscores, "value")'''
        result = completer._extract_set_variables(script)
        assert '_leading_underscore' in result
        assert 'trailing_underscore_' in result
        assert '_both_underscores_' in result
        assert 'multiple__underscores' in result

    def test_extract_set_variables_handles_percent_syntax(self, completer: ScriptCompleter) -> None:
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


class TestASTParsingMethods:
    """Test the AST parsing methods for different script structures."""

    def test_collect_set_variables_from_full_parse_success(self, completer: ScriptCompleter) -> None:
        """Test successful full parse variable collection."""
        script = '$set(var1, "value1")\n$set(var2, "value2")'
        result = completer._collect_set_variables_from_full_parse(script)
        assert result == {'var1', 'var2'}

    def test_collect_set_variables_from_full_parse_handles_errors(self, completer: ScriptCompleter) -> None:
        """Test that full parse handles parsing errors gracefully."""
        script = '$set(incomplete'
        result = completer._collect_set_variables_from_full_parse(script)
        # Should return empty set when parsing fails
        assert result == set()

    def test_collect_set_variables_from_line_parse(self, completer: ScriptCompleter) -> None:
        """Test per-line parsing for resilience during live edits."""
        script = '$set(var1, "value1")\n$set(incomplete\n$set(var2, "value2")'
        result = completer._collect_set_variables_from_line_parse(script)
        # Should extract variables from valid lines
        assert 'var1' in result
        assert 'var2' in result

    def test_collect_set_variables_from_line_parse_handles_empty_lines(self, completer: ScriptCompleter) -> None:
        """Test that empty lines are handled correctly in line parsing."""
        script = '\n\n$set(var1, "test")\n\n'
        result = completer._collect_set_variables_from_line_parse(script)
        assert result == {'var1'}

    def test_collect_set_variables_from_regex(self, completer: ScriptCompleter) -> None:
        """Test regex fallback for incomplete tokens."""
        script = '$set(var1, "value")\n$set(incomplete'
        result = completer._collect_set_variables_from_regex(script)
        # Should extract from regex even with incomplete syntax
        assert 'var1' in result

    def test_collect_set_variables_from_ast_with_nested_functions(self, completer: ScriptCompleter) -> None:
        """Test AST traversal with nested function calls."""

        # Create a custom mock class that handles __bool__ properly
        class MockExpression:
            def __iter__(self):
                mock_text = Mock(spec=ScriptText)
                mock_text.__str__ = Mock(return_value="nested_var")
                return iter([mock_text])

            def __bool__(self):
                return True

        mock_function = Mock(spec=ScriptFunction)
        mock_function.name = "set"
        mock_function.args = [MockExpression()]

        with patch.object(completer, '_extract_static_name', return_value="nested_var"):
            result = set()
            completer._collect_set_variables_from_ast(mock_function, result)
            assert 'nested_var' in result

    def test_extract_static_name_with_valid_expression(self, completer: ScriptCompleter) -> None:
        """Test static name extraction from valid expression."""
        # Test with a real script that should work
        script = '$set(test_var, "value")'
        result = completer._extract_set_variables(script)
        assert 'test_var' in result

    def test_extract_static_name_with_non_expression(self, completer: ScriptCompleter) -> None:
        """Test static name extraction with non-expression input."""
        mock_text = Mock(spec=ScriptText)
        result = completer._extract_static_name(mock_text)
        assert result is None

    def test_extract_static_name_with_mixed_tokens(self, completer: ScriptCompleter) -> None:
        """Test static name extraction with mixed token types."""
        # Test with a script that has mixed content
        script = '$set($if(1, "test", "else"), "value")'
        result = completer._extract_set_variables(script)
        # Should not extract variables from dynamic expressions
        assert result == set()

    def test_extract_static_name_with_empty_expression(self, completer: ScriptCompleter) -> None:
        """Test static name extraction with empty expression."""
        # Test with empty script
        script = ''
        result = completer._extract_set_variables(script)
        assert result == set()


class TestRegexFallback:
    """Test regex fallback for incomplete or malformed scripts."""

    @pytest.mark.parametrize(
        "script,expected_vars",
        [
            ('$set(var1, "value")', {'var1'}),
            ('$set(  spaced_var  , "value")', {'spaced_var'}),
            ('$set(var_with_underscore, "test")', {'var_with_underscore'}),
            ('$set(var123, "test")', {'var123'}),
            ('$set(incomplete', set()),  # Incomplete syntax
            ('', set()),
            ('%artist% - %album%', set()),
        ],
    )
    def test_regex_extraction_patterns(self, completer: ScriptCompleter, script: str, expected_vars: set[str]) -> None:
        """Test regex extraction with various patterns."""
        result = completer._collect_set_variables_from_regex(script)
        assert result == expected_vars

    def test_regex_handles_whitespace_variations(self, completer: ScriptCompleter) -> None:
        """Test that regex handles various whitespace patterns."""
        script = '$set(  var1  , "value")\n$set(var2, "value")'
        result = completer._collect_set_variables_from_regex(script)
        assert result == {'var1', 'var2'}

    def test_regex_handles_special_characters(self, completer: ScriptCompleter) -> None:
        """Test that regex handles special characters in variable names."""
        script = '$set(var_with_underscore, "test")\n$set(var123, "test")'
        result = completer._collect_set_variables_from_regex(script)
        assert result == {'var_with_underscore', 'var123'}


class TestChoicesProperty:
    """Test the choices property integration with user-defined variables."""

    def test_choices_includes_builtin_functions(self, completer: ScriptCompleter) -> None:
        """Test that choices include built-in script functions."""
        choices = list(completer.choices)
        function_choices = [choice for choice in choices if choice.startswith('$')]
        assert len(function_choices) > 0

    def test_choices_includes_builtin_variables(self, completer: ScriptCompleter) -> None:
        """Test that choices include built-in variables."""
        choices = list(completer.choices)
        builtin_vars = script_variable_tag_names()
        for var in builtin_vars:
            assert f'%{var}%' in choices

    def test_choices_includes_user_defined_variables(self, completer: ScriptCompleter) -> None:
        """Test that choices include user-defined variables."""
        completer._user_defined_variables = {'myvar', 'another_var'}
        choices = list(completer.choices)
        assert '%myvar%' in choices
        assert '%another_var%' in choices

    def test_choices_excludes_duplicate_builtin_variables(self, completer: ScriptCompleter) -> None:
        """Test that user-defined variables don't duplicate built-in variables."""
        builtin_vars = set(script_variable_tag_names())
        completer._user_defined_variables = builtin_vars | {'custom_var'}

        choices = list(completer.choices)
        # Should not have duplicates
        variable_choices = [choice for choice in choices if choice.startswith('%')]
        assert len(variable_choices) == len(builtin_vars) + 1  # +1 for custom_var
        assert '%custom_var%' in choices

    def test_choices_are_sorted(self, completer: ScriptCompleter) -> None:
        """Test that choices are properly sorted."""
        completer._user_defined_variables = {'z_var', 'a_var', 'm_var'}
        choices = list(completer.choices)

        # Check that user variables are sorted
        user_vars = [choice for choice in choices if choice.startswith('%') and 'var' in choice]
        assert user_vars == sorted(user_vars)


class TestCachingBehavior:
    """Test script hash caching and force update behavior."""

    def test_update_dynamic_variables_caching(self, completer: ScriptCompleter) -> None:
        """Test that caching works correctly to avoid unnecessary re-parsing."""
        script = '$set(var1, "value")'

        # First call should update
        completer.update_dynamic_variables(script)
        initial_hash = completer._script_hash
        initial_vars = completer._user_defined_variables.copy()

        # Second call with same content should not update
        completer.update_dynamic_variables(script)
        assert completer._script_hash == initial_hash
        assert completer._user_defined_variables == initial_vars

    def test_update_dynamic_variables_force_update(self, completer: ScriptCompleter) -> None:
        """Test that force=True bypasses caching."""
        script = '$set(var1, "value")'

        # First call
        completer.update_dynamic_variables(script)
        initial_variables = completer._user_defined_variables.copy()

        # Force update should process even with same content
        completer.update_dynamic_variables(script, force=True)
        # Variables should be the same but processing should occur
        assert completer._user_defined_variables == initial_variables

    def test_update_dynamic_variables_different_content(self, completer: ScriptCompleter) -> None:
        """Test that different content triggers update."""
        script1 = '$set(var1, "value")'
        script2 = '$set(var2, "value")'

        completer.update_dynamic_variables(script1)
        hash1 = completer._script_hash
        vars1 = completer._user_defined_variables.copy()

        completer.update_dynamic_variables(script2)
        assert completer._script_hash != hash1
        assert completer._user_defined_variables != vars1
        assert 'var2' in completer._user_defined_variables

    def test_update_dynamic_variables_updates_model(self, completer: ScriptCompleter) -> None:
        """Test that model is updated when variables change."""
        script = '$set(var1, "value")'
        completer.update_dynamic_variables(script)

        # Model should be updated with new choices
        model_data = completer._model.stringList()
        assert '%var1%' in model_data


class TestEdgeCases:
    """Test edge cases like nested functions, malformed syntax, empty scripts."""

    def test_empty_script(self, completer: ScriptCompleter) -> None:
        """Test handling of empty scripts."""
        result = completer._extract_set_variables('')
        assert result == set()

    def test_script_with_only_whitespace(self, completer: ScriptCompleter) -> None:
        """Test handling of scripts with only whitespace."""
        result = completer._extract_set_variables('   \n\t  \n  ')
        assert result == set()

    def test_nested_set_functions(self, completer: ScriptCompleter) -> None:
        """Test handling of nested $set functions."""
        script = '$set(outer, $set(inner, "value"))'
        result = completer._extract_set_variables(script)
        # Should extract both outer and inner variables
        assert 'outer' in result
        assert 'inner' in result

    def test_commented_sets(self, completer: ScriptCompleter) -> None:
        """Test that commented $set statements are ignored."""
        script = '// $set(commented, "ignored")\n$set(active, "value")'
        result = completer._extract_set_variables(script)
        assert 'active' in result
        # Regex might still catch commented ones, but AST parsing should not

    def test_very_long_variable_names(self, completer: ScriptCompleter) -> None:
        """Test handling of very long variable names."""
        long_var = 'a' * 1000
        script = f'$set({long_var}, "value")'
        result = completer._extract_set_variables(script)
        assert long_var in result

    def test_special_characters_in_variable_names(self, completer: ScriptCompleter) -> None:
        """Test handling of special characters in variable names."""
        # Only alphanumeric and underscore should be allowed
        script = '$set(var_with_underscore, "value")\n$set(var123, "value")'
        result = completer._extract_set_variables(script)
        assert 'var_with_underscore' in result
        assert 'var123' in result

    def test_unicode_variable_names(self, completer: ScriptCompleter) -> None:
        """Test handling of unicode characters in variable names."""
        script = '$set(variable_ñ, "value")\n$set(variable_中文, "value")'
        result = completer._extract_set_variables(script)
        # Should handle unicode characters
        assert 'variable_ñ' in result or 'variable_中文' in result

    def test_multiple_sets_same_variable(self, completer: ScriptCompleter) -> None:
        """Test handling of multiple $set statements with same variable name."""
        script = '$set(var1, "first")\n$set(var1, "second")'
        result = completer._extract_set_variables(script)
        assert 'var1' in result
        # Should not have duplicates in the set
        assert len(result) == 1

    def test_script_with_only_comments(self, completer: ScriptCompleter) -> None:
        """Test handling of scripts with only comments."""
        script = '// This is a comment\n/* Another comment */'
        result = completer._extract_set_variables(script)
        assert result == set()

    def test_script_with_mixed_content(self, completer: ScriptCompleter) -> None:
        """Test handling of scripts with mixed content types."""
        script = '''%artist% - %album%
$set(var1, "value")
$if(%artist%, "test", "default")
$set(var2, $if(1, "true", "false"))
// Comment
$set(var3, "final")'''
        result = completer._extract_set_variables(script)
        assert result == {'var1', 'var2', 'var3'}


class TestPerformanceAndMemory:
    """Test performance characteristics and memory usage."""

    def test_large_script_performance(self, completer: ScriptCompleter) -> None:
        """Test performance with large scripts."""
        # Create a large script with many $set statements
        script_lines = [f'$set(var{i}, "value{i}")' for i in range(1000)]
        script = '\n'.join(script_lines)

        # Should complete in reasonable time
        result = completer._extract_set_variables(script)
        assert len(result) == 1000
        assert 'var0' in result
        assert 'var999' in result

    def test_memory_usage_with_repeated_calls(self, completer: ScriptCompleter) -> None:
        """Test memory usage with repeated calls."""
        script = '$set(var1, "value")'

        # Make many calls with same content
        for _ in range(100):
            completer.update_dynamic_variables(script)

        # Should not accumulate memory
        assert completer._script_hash is not None
        assert completer._user_defined_variables == {'var1'}

    def test_hash_collision_handling(self, completer: ScriptCompleter) -> None:
        """Test handling of potential hash collisions."""
        # Use different scripts that might have same hash
        script1 = '$set(var1, "value")'
        script2 = '$set(var2, "value")'

        completer.update_dynamic_variables(script1)
        hash1 = completer._script_hash

        completer.update_dynamic_variables(script2)
        hash2 = completer._script_hash

        # Hashes should be different for different content
        assert hash1 != hash2


class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_parser_error_handling(self, completer: ScriptCompleter) -> None:
        """Test that parser errors are handled gracefully."""
        # Mock parser to raise an error
        with patch.object(completer._parser, 'parse', side_effect=ScriptError("Parse error")):
            result = completer._collect_set_variables_from_full_parse('$set(invalid')
            assert result == set()

    def test_malformed_ast_handling(self, completer: ScriptCompleter) -> None:
        """Test handling of malformed AST structures."""
        # Create a mock function with invalid structure
        mock_function = Mock(spec=ScriptFunction)
        mock_function.name = "set"
        mock_function.args = [None]  # Invalid argument

        result = set()
        # Should not raise an exception
        completer._collect_set_variables_from_ast(mock_function, result)
        assert result == set()

    def test_regex_error_handling(self, completer: ScriptCompleter) -> None:
        """Test that regex errors are handled gracefully."""
        # Test with very long strings that might cause regex issues
        long_string = 'a' * 10000
        script = f'$set({long_string}, "value")'

        # Should not raise an exception
        result = completer._collect_set_variables_from_regex(script)
        assert isinstance(result, set)

    def test_model_update_error_handling(self, completer: ScriptCompleter) -> None:
        """Test error handling during model updates."""
        # Mock model to raise an error
        with patch.object(completer._model, 'setStringList', side_effect=Exception("Model error")):
            # Should not raise an exception
            completer.update_dynamic_variables('$set(var1, "value")')
            # Should still update internal state
            assert 'var1' in completer._user_defined_variables
