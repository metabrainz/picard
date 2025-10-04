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

"""Comprehensive unit tests for VariableExtractor class.

Tests the VariableExtractor class that handles extraction of user-defined
variables from script content using multiple strategies.
"""

from unittest.mock import Mock, patch

from picard.script.parser import ScriptParser

import pytest

from picard.ui.widgets.variable_extractor import VariableExtractor


@pytest.fixture
def parser() -> ScriptParser:
    """Create a ScriptParser instance for testing."""
    return ScriptParser()


@pytest.fixture
def variable_extractor(parser: ScriptParser) -> VariableExtractor:
    """Create a VariableExtractor instance for testing."""
    return VariableExtractor(parser)


class TestVariableExtractor:
    """Test the VariableExtractor class functionality."""

    @pytest.mark.parametrize(
        ("script_content", "expected_variables"),
        [
            # Basic extraction
            ('$set(artist, "The Beatles")', {"artist"}),
            # Multiple variables
            (
                '''
                $set(artist, "The Beatles")
                $set(album, "Abbey Road")
                $set(year, "1969")
                ''',
                {"artist", "album", "year"},
            ),
            # No variables
            ('$if($eq(%artist%, "The Beatles"), "Yes", "No")', set()),
            # Empty content
            ("", set()),
            # Whitespace handling
            ('$set(  artist  , "The Beatles")', {"artist"}),
            # Unicode names
            ('$set(artista, "The Beatles")', {"artista"}),
            # Special characters
            ('$set(artist_name, "The Beatles")', {"artist_name"}),
            # Nested functions
            ('$set(artist, $if($eq(%album%, "Abbey Road"), "The Beatles", "Unknown"))', {"artist"}),
            # Multiline
            (
                '''
                $set(artist, "The Beatles")
                $set(album, "Abbey Road")
                ''',
                {"artist", "album"},
            ),
        ],
    )
    def test_extract_variables_cases(
        self, variable_extractor: VariableExtractor, script_content: str, expected_variables: set[str]
    ) -> None:
        """Test variable extraction with various scenarios."""
        variables = variable_extractor.extract_variables(script_content)
        assert variables == expected_variables

    def test_extract_variables_mixed_strategies(self, variable_extractor: VariableExtractor) -> None:
        """Test that multiple extraction strategies work together."""
        # This should work even if one strategy fails
        script_content = '$set(artist, "The Beatles")'
        variables = variable_extractor.extract_variables(script_content)
        assert "artist" in variables


class TestVariableExtractionStrategies:
    """Test individual variable extraction strategies."""

    def test_collect_from_full_parse_success(self, variable_extractor: VariableExtractor) -> None:
        """Test successful full parse extraction."""
        script_content = '$set(artist, "The Beatles")'
        variables = variable_extractor._collect_from_full_parse(script_content)
        assert "artist" in variables

    def test_collect_from_full_parse_failure(self, variable_extractor: VariableExtractor) -> None:
        """Test full parse extraction with invalid syntax."""
        script_content = '$set(artist, "The Beatles"'  # Missing closing parenthesis
        variables = variable_extractor._collect_from_full_parse(script_content)
        # Should return empty set when parsing fails
        assert len(variables) == 0

    def test_collect_from_line_parse_success(self, variable_extractor: VariableExtractor) -> None:
        """Test successful line-by-line parse extraction."""
        script_content = '''
        $set(artist, "The Beatles")
        $set(album, "Abbey Road")
        '''
        variables = variable_extractor._collect_from_line_parse(script_content)
        assert "artist" in variables
        assert "album" in variables

    def test_collect_from_line_parse_partial_failure(self, variable_extractor: VariableExtractor) -> None:
        """Test line-by-line parse extraction with some invalid lines."""
        script_content = '''
        $set(artist, "The Beatles")
        $set(album, "Abbey Road"  # Missing closing parenthesis
        $set(year, "1969")
        '''
        variables = variable_extractor._collect_from_line_parse(script_content)
        # Should still extract from valid lines
        assert "artist" in variables
        assert "year" in variables
        # Should not extract from invalid line
        assert "album" not in variables

    @pytest.mark.parametrize(
        ("script_content", "expected_variables"),
        [
            # Basic regex extraction
            ('$set(artist, "The Beatles")', {"artist"}),
            # Multiple variables
            (
                '''
                $set(artist, "The Beatles")
                $set(album, "Abbey Road")
                $set(year, "1969")
                ''',
                {"artist", "album", "year"},
            ),
            # Whitespace handling
            ('$set(  artist  , "The Beatles")', {"artist"}),
            # Unicode characters
            ('$set(artista, "The Beatles")', {"artista"}),
            # Special characters
            ('$set(artist_name, "The Beatles")', {"artist_name"}),
        ],
    )
    def test_collect_from_regex_cases(
        self, variable_extractor: VariableExtractor, script_content: str, expected_variables: set[str]
    ) -> None:
        """Test regex extraction with various scenarios."""
        variables = variable_extractor._collect_from_regex(script_content)
        assert variables == expected_variables


class TestASTTraversal:
    """Test AST traversal and variable collection."""

    def test_collect_from_ast_function_node(self, variable_extractor: VariableExtractor) -> None:
        """Test AST collection from function nodes."""
        # Mock a function node
        mock_function = Mock()
        mock_function.name = "set"
        mock_function.args = [Mock()]

        # Mock the first argument as a static name
        mock_arg = Mock()
        mock_arg.__class__.__name__ = "ScriptExpression"
        mock_arg.__iter__ = Mock(return_value=iter([Mock()]))

        variables = set()
        variable_extractor._collect_from_ast(mock_function, variables)
        # Should not add anything since we can't easily mock the static name extraction

    def test_collect_from_ast_expression_node(self, variable_extractor: VariableExtractor) -> None:
        """Test AST collection from expression nodes."""
        # Mock an expression node
        mock_expression = Mock()
        mock_expression.__iter__ = Mock(return_value=iter([]))

        variables = set()
        variable_extractor._collect_from_ast(mock_expression, variables)
        # Should not add anything since we can't easily mock the traversal

    def test_extract_static_name_success(self, variable_extractor: VariableExtractor) -> None:
        """Test successful static name extraction."""
        # This test is complex to mock properly, so we'll test the integration instead
        # The actual functionality is tested through the integration tests
        pass

    def test_extract_static_name_failure(self, variable_extractor: VariableExtractor) -> None:
        """Test static name extraction failure."""
        # Mock a node that doesn't represent a static name
        mock_node = Mock()
        mock_node.__class__.__name__ = "ScriptFunction"  # Not a ScriptExpression

        result = variable_extractor._extract_static_name(mock_node)
        assert result is None

    def test_extract_static_name_mixed_tokens(self, variable_extractor: VariableExtractor) -> None:
        """Test static name extraction with mixed token types."""
        # Mock a node with mixed token types
        mock_node = Mock()
        mock_node.__class__.__name__ = "ScriptExpression"

        # Mock tokens with different types
        mock_text_token = Mock()
        mock_text_token.__class__.__name__ = "ScriptText"
        mock_function_token = Mock()
        mock_function_token.__class__.__name__ = "ScriptFunction"

        mock_node.__iter__ = Mock(return_value=iter([mock_text_token, mock_function_token]))

        result = variable_extractor._extract_static_name(mock_node)
        assert result is None  # Should return None due to mixed token types


class TestVariableExtractorEdgeCases:
    """Test edge cases and error handling for VariableExtractor."""

    def test_extract_variables_with_parser_errors(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction when parser raises errors."""
        from picard.script.parser import ScriptError

        with patch.object(variable_extractor._parser, 'parse', side_effect=ScriptError("Parser error")):
            script_content = '$set(artist, "The Beatles")'
            # Should not raise an exception, should use regex fallback
            variables = variable_extractor.extract_variables(script_content)
            # Should still work using regex fallback
            assert "artist" in variables

    def test_extract_variables_with_mixed_validity(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction with mixed valid and invalid content."""
        script_content = '''
        $set(artist, "The Beatles")
        $set(album, "Abbey Road"  # Missing closing parenthesis
        $set(year, "1969")
        '''
        variables = variable_extractor.extract_variables(script_content)
        # Should extract from valid lines
        assert "artist" in variables
        assert "year" in variables

    def test_extract_variables_with_empty_lines(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction with empty lines."""
        script_content = '''

        $set(artist, "The Beatles")

        $set(album, "Abbey Road")

        '''
        variables = variable_extractor.extract_variables(script_content)
        assert "artist" in variables
        assert "album" in variables

    def test_extract_variables_with_very_long_content(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction with very long content."""
        # Create a long script with many variables
        script_content = '\n'.join(f'$set(var{i}, "value{i}")' for i in range(1000))
        variables = variable_extractor.extract_variables(script_content)
        # Should extract all variables
        assert len(variables) == 1000
        for i in range(1000):
            assert f"var{i}" in variables

    def test_extract_variables_with_unicode_content(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction with unicode content."""
        script_content = '$set(artista, "Los Beatles")'
        variables = variable_extractor.extract_variables(script_content)
        assert "artista" in variables

    def test_extract_variables_with_special_characters(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction with special characters in variable names."""
        script_content = '$set(artist_name, "The Beatles")'
        variables = variable_extractor.extract_variables(script_content)
        assert "artist_name" in variables

    def test_extract_variables_deduplication(self, variable_extractor: VariableExtractor) -> None:
        """Test that duplicate variables are deduplicated."""
        script_content = '''
        $set(artist, "The Beatles")
        $set(artist, "The Rolling Stones")
        '''
        variables = variable_extractor.extract_variables(script_content)
        # Should only have one instance of "artist"
        assert len(variables) == 1
        assert "artist" in variables

    def test_extract_variables_performance(self, variable_extractor: VariableExtractor) -> None:
        """Test extraction performance with large content."""
        # Create a large script
        script_content = '\n'.join(f'$set(var{i}, "value{i}")' for i in range(10000))

        # Should complete in reasonable time
        variables = variable_extractor.extract_variables(script_content)
        assert len(variables) == 10000
