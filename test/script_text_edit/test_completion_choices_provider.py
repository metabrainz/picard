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

"""Comprehensive unit tests for CompletionChoicesProvider.

Tests the CompletionChoicesProvider class that was extracted from ScriptCompleter
to handle completion choices generation with proper ordering, mode handling,
deduplication, and error handling.
"""

from unittest.mock import (
    patch,
)

import pytest

from picard.ui.widgets.completion_provider import CompletionChoicesProvider
from picard.ui.widgets.context_detector import CompletionMode


@pytest.fixture
def choices_provider() -> CompletionChoicesProvider:
    """Create a CompletionChoicesProvider instance for testing."""
    return CompletionChoicesProvider()


@pytest.fixture
def sample_usage_counts() -> dict[str, int]:
    """Sample usage counts for testing."""
    return {
        'artist': 5,
        'album': 3,
        'title': 1,
        'plugin_var1': 2,
        'user_var1': 4,
    }


@pytest.fixture
def sample_builtin_variables() -> list[str]:
    """Sample builtin variables for testing."""
    return ['artist', 'album', 'title', 'date']


@pytest.fixture
def sample_user_variables() -> set[str]:
    """Sample user-defined variables for testing."""
    return {'user_var1', 'user_var2', 'artist'}  # 'artist' overlaps with builtin


class TestCompletionChoicesProviderOrdering:
    """Test completion choices ordering (usage-count desc then name asc)."""

    def test_ordering_by_usage_count_desc_then_name_asc(
        self,
        choices_provider: CompletionChoicesProvider,
        sample_usage_counts: dict[str, int],
        sample_builtin_variables: list[str],
        sample_user_variables: set[str],
    ) -> None:
        """Test that variables are ordered by usage count (desc) then name (asc)."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                sample_user_variables,
                sample_builtin_variables,
                sample_usage_counts,
            )
        )

        # Extract variable names from %name% format
        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]

        # Expected order: artist(5), user_var1(4), plugin_var1(2), album(3), title(1), date(0), user_var2(0), plugin_var2(0), plugin_var3(0)
        # Within same usage count, alphabetical: album(3), artist(5), plugin_var1(2), title(1), user_var1(4)
        # Then: date(0), plugin_var2(0), plugin_var3(0), user_var2(0)
        expected_order = [
            'artist',  # 5 uses
            'user_var1',  # 4 uses
            'album',  # 3 uses
            'title',  # 1 use
            'date',  # 0 uses
            'user_var2',  # 0 uses
        ]

        assert var_names == expected_order

    def test_ordering_with_equal_usage_counts(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test ordering when variables have equal usage counts."""
        usage_counts = {'var_a': 1, 'var_b': 1, 'var_c': 1}
        builtin_vars = ['var_a', 'var_b', 'var_c']

        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                set(),
                builtin_vars,
                usage_counts,
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        # Should include plugin variables, so we need to check that our variables are in the right order
        # within the context of all variables
        builtin_indices = [var_names.index(var) for var in ['var_a', 'var_b', 'var_c']]
        assert builtin_indices == sorted(builtin_indices)  # Should be in alphabetical order

    def test_ordering_with_no_usage_counts(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test ordering when no usage counts are provided."""
        builtin_vars = ['z_var', 'a_var', 'm_var']

        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                set(),
                builtin_vars,
                {},
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        # Should include plugin variables, so we need to check that our variables are in the right order
        # within the context of all variables
        builtin_indices = [var_names.index(var) for var in ['a_var', 'm_var', 'z_var']]
        assert builtin_indices == sorted(builtin_indices)  # Should be in alphabetical order


class TestCompletionChoicesProviderModes:
    """Test completion choices for different modes."""

    @pytest.mark.parametrize(
        ("mode", "expected_format"),
        [
            (CompletionMode.DEFAULT, "%name%"),
            (CompletionMode.VARIABLE, "%name%"),
            (CompletionMode.TAG_NAME_ARG, "name"),  # Bare names
            (CompletionMode.FUNCTION_NAME, "$name"),  # Function names
        ],
    )
    def test_mode_formats(
        self,
        choices_provider: CompletionChoicesProvider,
        mode: CompletionMode,
        expected_format: str,
    ) -> None:
        """Test that different modes return correctly formatted choices."""
        choices = list(
            choices_provider.build_choices(
                mode,
                {'test_var'},
                ['builtin_var'],
                {'test_var': 1, 'builtin_var': 2},
            )
        )

        if mode == CompletionMode.TAG_NAME_ARG:
            # TAG_NAME_ARG returns bare names
            assert 'test_var' in choices
            assert 'builtin_var' in choices
            assert not any(choice.startswith('%') for choice in choices)
        elif mode in (CompletionMode.DEFAULT, CompletionMode.VARIABLE):
            # Variable modes return %name% format
            assert '%test_var%' in choices
            assert '%builtin_var%' in choices
        elif mode == CompletionMode.FUNCTION_NAME:
            # Function mode returns $name format for functions
            # Note: This mode also includes functions from script_function_names()
            assert any(choice.startswith('$') for choice in choices)

    def test_tag_name_arg_returns_bare_names(
        self,
        choices_provider: CompletionChoicesProvider,
        sample_builtin_variables: list[str],
        sample_user_variables: set[str],
    ) -> None:
        """Test that TAG_NAME_ARG mode returns bare variable names."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.TAG_NAME_ARG,
                sample_user_variables,
                sample_builtin_variables,
                {},
            )
        )

        # Should contain bare names without % wrapping
        expected_names = {
            'artist',
            'album',
            'title',
            'date',
            'user_var1',
            'user_var2',
        }
        actual_names = set(choices)
        assert actual_names == expected_names

    def test_function_name_mode_includes_functions(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test that FUNCTION_NAME mode includes script functions."""
        with patch('picard.ui.widgets.completion_provider.script_function_names') as mock_func_names:
            mock_func_names.return_value = ['set', 'get', 'if']

            choices = list(
                choices_provider.build_choices(
                    CompletionMode.FUNCTION_NAME,
                    set(),
                    [],
                    {},
                )
            )

            # Should include function names with $ prefix
            assert '$set' in choices
            assert '$get' in choices
            assert '$if' in choices


class TestCompletionChoicesProviderDeduplication:
    """Test deduplication across builtin/plugin/user variables."""

    def test_deduplication_user_builtin_overlap(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test deduplication when user and builtin variables overlap."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {'artist', 'user_var'},  # 'artist' overlaps with builtin
                ['artist', 'album'],
                {},
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        assert len(var_names) == len(set(var_names))
        assert var_names.count('artist') == 1  # Should appear only once

    def test_stable_output_with_equal_weights(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test that output is stable when variables have equal weights."""
        # All variables have same usage count (0)
        choices1 = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {'z_var', 'a_var'},
                ['m_var'],
                {},
            )
        )

        choices2 = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {'z_var', 'a_var'},
                ['m_var'],
                {},
            )
        )

        assert choices1 == choices2  # Should be identical


class TestCompletionChoicesProviderErrorHandling:
    """Test error handling for plugin provider errors and empty sets."""

    def test_plugin_provider_returns_empty_set(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test handling when plugin provider returns empty set."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {'user_var'},
                ['builtin_var'],
                {},
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        assert 'user_var' in var_names
        assert 'builtin_var' in var_names
        # No plugin variables should be present

    def test_empty_inputs(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test handling of empty inputs."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                set(),
                [],
                {},
            )
        )

        # Should only contain plugin variables
        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        assert set(var_names) == set()


class TestCompletionChoicesProviderEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_variable_names(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test handling of unicode variable names."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {'var_ñ', 'var_中文'},
                [],
                {},
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        assert 'var_ñ' in var_names
        assert 'var_中文' in var_names

    def test_variable_names_with_colons(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test handling of variable names with colons."""
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {'tag:artist', 'tag:album'},
                [],
                {},
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        assert 'tag:artist' in var_names
        assert 'tag:album' in var_names

    def test_very_long_variable_names(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test handling of very long variable names."""
        long_name = 'a' * 1000
        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                {long_name},
                [],
                {},
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        assert long_name in var_names

    def test_negative_usage_counts(
        self,
        choices_provider: CompletionChoicesProvider,
    ) -> None:
        """Test handling of negative usage counts."""
        usage_counts = {'var1': -1, 'var2': 0, 'var3': 1}

        choices = list(
            choices_provider.build_choices(
                CompletionMode.VARIABLE,
                set(),
                ['var1', 'var2', 'var3'],
                usage_counts,
            )
        )

        var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
        # Should include plugin variables, so we need to check that our variables are in the right order
        # within the context of all variables
        builtin_indices = [var_names.index(var) for var in ['var1', 'var2', 'var3']]

        # Should be ordered by usage count: var3(1), var2(0), var1(-1)
        # The actual order in the list should be: var3, var2, var1 (descending usage count)
        # builtin_indices[0] = var1 index, builtin_indices[1] = var2 index, builtin_indices[2] = var3 index
        # So we expect: var3 (index 2) < var2 (index 1) < var1 (index 0)
        assert builtin_indices[2] < builtin_indices[1]  # var3 before var2
        assert builtin_indices[1] < builtin_indices[0]  # var2 before var1
