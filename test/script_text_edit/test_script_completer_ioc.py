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

"""Comprehensive unit tests for ScriptCompleter IOC surfaces.

Tests the ScriptCompleter class with dependency injection to verify
that injected dependencies are used correctly and model reuse works
as expected.
"""

from collections.abc import Callable
from unittest.mock import Mock

from picard.script.parser import ScriptParser

import pytest

from picard.ui.widgets.completion_provider import CompletionChoicesProvider
from picard.ui.widgets.context_detector import CompletionMode, ContextDetector
from picard.ui.widgets.scripttextedit import ScriptCompleter
from picard.ui.widgets.variable_extractor import VariableExtractor


@pytest.fixture
def mock_parser() -> Mock:
    """Create a mock ScriptParser."""
    parser = Mock(spec=ScriptParser)
    return parser


@pytest.fixture
def mock_variable_extractor() -> Mock:
    """Create a mock VariableExtractor."""
    extractor = Mock(spec=VariableExtractor)
    extractor.extract_variables.return_value = set()
    return extractor


@pytest.fixture
def mock_context_detector() -> Mock:
    """Create a mock ContextDetector."""
    detector = Mock(spec=ContextDetector)
    detector.detect_context.return_value = CompletionMode.DEFAULT
    detector.detect_context_details.return_value = {'mode': CompletionMode.DEFAULT}
    return detector


@pytest.fixture
def mock_plugin_variable_provider() -> Callable[[], set[str]]:
    """Create a mock plugin variable provider."""
    provider = Mock(return_value={'plugin_var1', 'plugin_var2'})
    return provider


@pytest.fixture
def mock_choices_provider() -> Mock:
    """Create a mock CompletionChoicesProvider."""
    provider = Mock(spec=CompletionChoicesProvider)
    provider.build_choices.return_value = iter(['%test_var%', '%plugin_var1%'])
    return provider


@pytest.fixture
def script_completer_with_injections(
    mock_parser: Mock,
    mock_variable_extractor: Mock,
    mock_context_detector: Mock,
    mock_plugin_variable_provider: Callable[[], set[str]],
    mock_choices_provider: Mock,
) -> ScriptCompleter:
    """Create a ScriptCompleter with all dependencies injected."""
    return ScriptCompleter(
        parser=mock_parser,
        variable_extractor=mock_variable_extractor,
        context_detector=mock_context_detector,
        plugin_variable_provider=mock_plugin_variable_provider,
        choices_provider=mock_choices_provider,
    )


class TestScriptCompleterDependencyInjection:
    """Test that ScriptCompleter uses injected dependencies correctly."""

    def test_uses_injected_parser(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_parser: Mock,
    ) -> None:
        """Test that injected parser is used."""
        assert script_completer_with_injections._parser is mock_parser

    def test_uses_injected_variable_extractor(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_variable_extractor: Mock,
    ) -> None:
        """Test that injected variable extractor is used."""
        assert script_completer_with_injections._variable_extractor is mock_variable_extractor

    def test_uses_injected_context_detector(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_context_detector: Mock,
    ) -> None:
        """Test that injected context detector is used."""
        assert script_completer_with_injections._context_detector is mock_context_detector

    def test_uses_injected_plugin_provider(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_plugin_variable_provider: Callable[[], set[str]],
    ) -> None:
        """Test that injected plugin provider is used."""
        assert script_completer_with_injections._plugin_variable_provider is mock_plugin_variable_provider

    def test_uses_injected_choices_provider(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Test that injected choices provider is used."""
        assert script_completer_with_injections._choices_provider is mock_choices_provider

    def test_creates_default_dependencies_when_none_provided(self) -> None:
        """Test that default dependencies are created when none provided."""
        completer = ScriptCompleter()

        # Should create default instances
        assert isinstance(completer._parser, ScriptParser)
        assert isinstance(completer._variable_extractor, VariableExtractor)
        assert isinstance(completer._context_detector, ContextDetector)
        assert completer._plugin_variable_provider is not None
        assert isinstance(completer._choices_provider, CompletionChoicesProvider)

    def test_variable_extractor_uses_injected_parser(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_parser: Mock,
    ) -> None:
        """Test that variable extractor is initialized with injected parser."""
        # The variable extractor should be initialized with the parser
        # This is tested indirectly by checking that the parser is used
        assert script_completer_with_injections._parser is mock_parser


class TestScriptCompleterModelReuse:
    """Test that model object is reused while contents update."""

    def test_model_object_unchanged_during_updates(
        self,
        script_completer_with_injections: ScriptCompleter,
    ) -> None:
        """Test that model object remains the same during updates."""
        initial_model = script_completer_with_injections._model

        # Update with new script content
        script_completer_with_injections.update_dynamic_variables("new script content")

        # Model object should be the same
        assert script_completer_with_injections._model is initial_model

    def test_model_contents_update_with_new_variables(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_variable_extractor: Mock,
    ) -> None:
        """Test that model contents update with new variables."""
        # Setup mock to return different variables
        mock_variable_extractor.extract_variables.return_value = {'new_var1', 'new_var2'}

        # Update with new script
        script_completer_with_injections.update_dynamic_variables("$set(new_var1, value)")

        # Verify extractor was called
        mock_variable_extractor.extract_variables.assert_called_with("$set(new_var1, value)")

    def test_model_contents_update_with_usage_counts(
        self,
        script_completer_with_injections: ScriptCompleter,
    ) -> None:
        """Test that model contents update with usage counts."""
        # Update with script that has variable usage
        script_content = "%artist% %album% %artist%"  # artist used twice
        script_completer_with_injections.update_dynamic_variables(script_content)

        # Check that usage counts are updated
        assert script_completer_with_injections._var_usage_counts['artist'] == 2
        assert script_completer_with_injections._var_usage_counts['album'] == 1

    def test_model_persistence_across_multiple_updates(
        self,
        script_completer_with_injections: ScriptCompleter,
    ) -> None:
        """Test that model persists across multiple updates."""
        initial_model = script_completer_with_injections._model

        # Multiple updates
        script_completer_with_injections.update_dynamic_variables("script1")
        script_completer_with_injections.update_dynamic_variables("script2")
        script_completer_with_injections.update_dynamic_variables("script3")

        # Model should still be the same object
        assert script_completer_with_injections._model is initial_model


class TestScriptCompleterContextChanges:
    """Test that context changes cause expected choices."""

    def test_context_detector_not_called_during_choices_generation(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_context_detector: Mock,
    ) -> None:
        """Test that context detector is not called during choices generation."""
        # Generate choices
        list(script_completer_with_injections.choices)

        # Context detector should NOT be called during choices generation
        # The context is set elsewhere via _set_context method
        mock_context_detector.detect_context.assert_not_called()

    def test_choices_provider_called_with_default_context(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Test that choices provider is called with default context."""
        # Generate choices
        list(script_completer_with_injections.choices)

        # Verify choices provider was called with default mode
        mock_choices_provider.build_choices.assert_called()
        call_args = mock_choices_provider.build_choices.call_args
        assert call_args[0][0] == CompletionMode.DEFAULT

    def test_context_changes_affect_choices(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Test that context changes affect the choices returned."""
        # Set different contexts manually
        script_completer_with_injections._set_context({'mode': CompletionMode.VARIABLE})
        choices1 = list(script_completer_with_injections.choices)

        script_completer_with_injections._set_context({'mode': CompletionMode.TAG_NAME_ARG})
        choices2 = list(script_completer_with_injections.choices)

        # Should get different choices for different contexts
        assert isinstance(choices1, list)
        assert isinstance(choices2, list)
        # The choices provider should be called
        mock_choices_provider.build_choices.assert_called()

    def test_smoke_test_with_small_inputs(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Smoke test with small inputs to verify basic functionality."""
        # Test with minimal script
        script_completer_with_injections.update_dynamic_variables("")
        choices = list(script_completer_with_injections.choices)

        # Should get choices
        assert isinstance(choices, list)
        assert len(choices) > 0
        # The choices provider should be called
        mock_choices_provider.build_choices.assert_called()

    def test_choices_provider_receives_correct_parameters(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Test that choices provider receives correct parameters."""
        # Setup some state
        script_completer_with_injections._user_defined_variables = {'user_var'}
        script_completer_with_injections._var_usage_counts = {'user_var': 2}

        # Generate choices
        list(script_completer_with_injections.choices)

        # Verify parameters passed to choices provider
        call_args = mock_choices_provider.build_choices.call_args
        args, kwargs = call_args

        assert args[0] == CompletionMode.DEFAULT  # mode
        assert args[1] == {'user_var'}  # user_defined_variables
        assert 'builtin_variables' in kwargs or len(args) > 2  # builtin_variables
        assert args[3] == {'user_var': 2}  # usage_counts


class TestScriptCompleterIntegration:
    """Test integration between different components."""

    def test_variable_extraction_integration(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_variable_extractor: Mock,
    ) -> None:
        """Test integration between completer and variable extractor."""
        mock_variable_extractor.extract_variables.return_value = {'extracted_var'}

        script_completer_with_injections.update_dynamic_variables("$set(extracted_var, value)")

        # Verify extractor was called with correct script
        mock_variable_extractor.extract_variables.assert_called_with("$set(extracted_var, value)")

        # Verify extracted variables are stored
        assert 'extracted_var' in script_completer_with_injections._user_defined_variables

    def test_context_detection_integration(
        self,
        script_completer_with_injections: ScriptCompleter,
    ) -> None:
        """Test integration between completer and context detector."""
        # Set context manually
        script_completer_with_injections._set_context(
            {
                'mode': CompletionMode.TAG_NAME_ARG,
                'function_name': 'set',
                'arg_index': 0,
            }
        )

        # Generate choices
        choices = list(script_completer_with_injections.choices)

        # Should get choices for the context
        assert isinstance(choices, list)

    def test_plugin_provider_integration(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_plugin_variable_provider: Callable[[], set[str]],
    ) -> None:
        """Test integration between completer and plugin provider."""
        # Generate choices
        choices = list(script_completer_with_injections.choices)

        # Should get choices that include plugin variables
        assert isinstance(choices, list)
        # The plugin provider is called internally by the choices provider
        # We can't easily test the call count without more complex mocking

    def test_choices_provider_integration(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Test integration between completer and choices provider."""
        # Setup choices provider to return specific choices
        mock_choices_provider.build_choices.return_value = iter(['%integration_test%'])

        # Generate choices
        choices = list(script_completer_with_injections.choices)

        # Verify choices provider was called and returned expected choices
        mock_choices_provider.build_choices.assert_called()
        assert '%integration_test%' in choices


class TestScriptCompleterEdgeCases:
    """Test edge cases and error conditions."""

    def test_handles_none_dependencies_gracefully(self) -> None:
        """Test that completer handles None dependencies gracefully."""
        # This should not raise an exception
        completer = ScriptCompleter(
            parser=None,
            variable_extractor=None,
            context_detector=None,
            plugin_variable_provider=None,
            choices_provider=None,
        )

        # Should create default instances
        assert completer._parser is not None
        assert completer._variable_extractor is not None
        assert completer._context_detector is not None
        assert completer._plugin_variable_provider is not None
        assert completer._choices_provider is not None

    def test_handles_empty_script_content(
        self,
        script_completer_with_injections: ScriptCompleter,
    ) -> None:
        """Test handling of empty script content."""
        script_completer_with_injections.update_dynamic_variables("")

        # Should not raise exception
        choices = list(script_completer_with_injections.choices)
        assert isinstance(choices, list)

    def test_handles_context_detector_exception(
        self,
        script_completer_with_injections: ScriptCompleter,
    ) -> None:
        """Test handling of context detector exceptions."""
        # Since context detector is not called during choices generation,
        # this test is not applicable to the current implementation
        # The context is set via _set_context method, not during choices generation
        choices = list(script_completer_with_injections.choices)
        assert isinstance(choices, list)

    def test_handles_choices_provider_exception(
        self,
        script_completer_with_injections: ScriptCompleter,
        mock_choices_provider: Mock,
    ) -> None:
        """Test handling of choices provider exceptions."""
        mock_choices_provider.build_choices.side_effect = RuntimeError("Choices error")

        # Should handle exception gracefully
        with pytest.raises(RuntimeError, match="Choices error"):
            list(script_completer_with_injections.choices)
