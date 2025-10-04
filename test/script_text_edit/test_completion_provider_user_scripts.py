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

"""Unit tests for CompletionChoicesProvider with user script integration.

Tests the CompletionChoicesProvider class with user script scanner
integration to ensure user script variables are included in completion choices.
"""

from unittest.mock import Mock

import pytest

from picard.ui.widgets.completion_provider import CompletionChoicesProvider
from picard.ui.widgets.context_detector import CompletionMode
from picard.ui.widgets.user_script_scanner import UserScriptScanner


@pytest.fixture
def mock_plugin_provider():
    """Create a mock plugin variable provider."""
    return Mock(return_value={'plugin_var1', 'plugin_var2'})


@pytest.fixture
def mock_user_script_scanner():
    """Create a mock user script scanner."""
    scanner = Mock(spec=UserScriptScanner)
    scanner.get_cached_variables.return_value = {'user_script_var1', 'user_script_var2'}
    return scanner


@pytest.fixture
def choices_provider_with_scanner(mock_plugin_provider, mock_user_script_scanner):
    """Create a CompletionChoicesProvider with user script scanner."""
    return CompletionChoicesProvider(mock_plugin_provider, mock_user_script_scanner)


@pytest.fixture
def choices_provider_without_scanner(mock_plugin_provider):
    """Create a CompletionChoicesProvider without user script scanner."""
    return CompletionChoicesProvider(mock_plugin_provider)


def test_initialization_with_user_script_scanner(mock_plugin_provider, mock_user_script_scanner):
    """Test initialization with user script scanner."""
    provider = CompletionChoicesProvider(mock_plugin_provider, mock_user_script_scanner)
    assert provider._get_plugin_variable_names is mock_plugin_provider
    assert provider._user_script_scanner is mock_user_script_scanner


def test_initialization_without_user_script_scanner(mock_plugin_provider):
    """Test initialization without user script scanner."""
    provider = CompletionChoicesProvider(mock_plugin_provider)
    assert provider._get_plugin_variable_names is mock_plugin_provider
    assert provider._user_script_scanner is None


def test_build_choices_includes_user_script_variables(choices_provider_with_scanner):
    """Test that build_choices includes user script variables."""
    choices = list(
        choices_provider_with_scanner.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should include user script variables
    assert '%user_script_var1%' in choices
    assert '%user_script_var2%' in choices
    assert '%user_defined_var%' in choices
    assert '%builtin_var%' in choices
    assert '%plugin_var1%' in choices
    assert '%plugin_var2%' in choices


def test_build_choices_without_user_script_scanner(choices_provider_without_scanner):
    """Test that build_choices works without user script scanner."""
    choices = list(
        choices_provider_without_scanner.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should not include user script variables
    assert '%user_script_var1%' not in choices
    assert '%user_script_var2%' not in choices
    assert '%user_defined_var%' in choices
    assert '%builtin_var%' in choices
    assert '%plugin_var1%' in choices
    assert '%plugin_var2%' in choices


def test_build_choices_deduplication_with_user_scripts(choices_provider_with_scanner):
    """Test deduplication when user script variables overlap with others."""
    # Mock scanner to return overlapping variables
    choices_provider_with_scanner._user_script_scanner.get_cached_variables.return_value = {
        'builtin_var',  # Overlaps with builtin
        'user_script_unique',
    }

    choices = list(
        choices_provider_with_scanner.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should not have duplicates
    var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]
    assert len(var_names) == len(set(var_names))
    assert var_names.count('builtin_var') == 1  # Should appear only once


def test_build_choices_ordering_with_user_scripts(choices_provider_with_scanner):
    """Test ordering when user script variables are included."""
    usage_counts = {
        'user_script_var1': 3,
        'builtin_var': 2,
        'user_defined_var': 1,
        'plugin_var1': 0,
    }

    choices = list(
        choices_provider_with_scanner.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            usage_counts,
        )
    )

    # Extract variable names and check ordering
    var_names = [choice[1:-1] for choice in choices if choice.startswith('%') and choice.endswith('%')]

    # Should be ordered by usage count: user_script_var1(3), builtin_var(2), user_defined_var(1), others(0)
    user_script_idx = var_names.index('user_script_var1')
    builtin_idx = var_names.index('builtin_var')
    user_defined_idx = var_names.index('user_defined_var')

    assert user_script_idx < builtin_idx  # user_script_var1 before builtin_var
    assert builtin_idx < user_defined_idx  # builtin_var before user_defined_var


def test_build_choices_tag_name_arg_mode_with_user_scripts(choices_provider_with_scanner):
    """Test TAG_NAME_ARG mode includes user script variables as bare names."""
    choices = list(
        choices_provider_with_scanner.build_choices(
            CompletionMode.TAG_NAME_ARG,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should contain bare names without % wrapping
    expected_names = {
        'user_script_var1',
        'user_script_var2',
        'user_defined_var',
        'builtin_var',
        'plugin_var1',
        'plugin_var2',
    }
    actual_names = set(choices)
    assert actual_names == expected_names


def test_build_choices_user_script_scanner_exception(mock_plugin_provider):
    """Test handling when user script scanner raises exception."""
    mock_scanner = Mock(spec=UserScriptScanner)
    mock_scanner.get_cached_variables.side_effect = AttributeError("Scanner error")
    provider = CompletionChoicesProvider(mock_plugin_provider, mock_scanner)

    # Should not raise exception
    choices = list(
        provider.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should still include other variables
    assert '%user_defined_var%' in choices
    assert '%builtin_var%' in choices
    assert '%plugin_var1%' in choices


def test_build_choices_user_script_scanner_returns_none(mock_plugin_provider):
    """Test handling when user script scanner returns None."""
    mock_scanner = Mock(spec=UserScriptScanner)
    mock_scanner.get_cached_variables.return_value = None
    provider = CompletionChoicesProvider(mock_plugin_provider, mock_scanner)

    # Should not raise exception
    choices = list(
        provider.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should still include other variables
    assert '%user_defined_var%' in choices
    assert '%builtin_var%' in choices
    assert '%plugin_var1%' in choices


def test_build_choices_empty_user_script_variables(mock_plugin_provider):
    """Test handling when user script scanner returns empty set."""
    mock_scanner = Mock(spec=UserScriptScanner)
    mock_scanner.get_cached_variables.return_value = set()
    provider = CompletionChoicesProvider(mock_plugin_provider, mock_scanner)

    choices = list(
        provider.build_choices(
            CompletionMode.VARIABLE,
            {'user_defined_var'},
            ['builtin_var'],
            {},
        )
    )

    # Should include other variables but not user script variables
    assert '%user_defined_var%' in choices
    assert '%builtin_var%' in choices
    assert '%plugin_var1%' in choices
    assert '%user_script_var1%' not in choices


def test_build_choices_unicode_user_script_variables(mock_plugin_provider):
    """Test handling of unicode user script variable names."""
    mock_scanner = Mock(spec=UserScriptScanner)
    mock_scanner.get_cached_variables.return_value = {'var_ñ', 'var_中文'}
    provider = CompletionChoicesProvider(mock_plugin_provider, mock_scanner)

    choices = list(
        provider.build_choices(
            CompletionMode.VARIABLE,
            set(),
            [],
            {},
        )
    )

    assert '%var_ñ%' in choices
    assert '%var_中文%' in choices


def test_build_choices_very_long_user_script_variables(mock_plugin_provider):
    """Test handling of very long user script variable names."""
    long_name = 'a' * 1000
    mock_scanner = Mock(spec=UserScriptScanner)
    mock_scanner.get_cached_variables.return_value = {long_name}
    provider = CompletionChoicesProvider(mock_plugin_provider, mock_scanner)

    choices = list(
        provider.build_choices(
            CompletionMode.VARIABLE,
            set(),
            [],
            {},
        )
    )

    assert f'%{long_name}%' in choices
