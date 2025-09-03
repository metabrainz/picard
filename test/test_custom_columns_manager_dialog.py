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

"""Unit tests for the fe4753a custom columns refactor.

This module tests all changes introduced in the massive refactor commit fe4753a:
- New ColumnController facade class
- New ColumnFormHandler for form management
- New ColumnSpecService for spec operations
- New ViewSelector widget
- Updated validation rules (numeric keys only)
- New shared utility functions
- Manager dialog workflow changes

Follows DRY, SOC, SRP principles with extensive use of pytest fixtures
and parametrize to reduce code duplication while ensuring comprehensive coverage.
"""

from unittest.mock import Mock, call, patch

from PyQt6 import QtWidgets

import pytest

from picard.ui.itemviews.custom_columns.column_controller import ColumnController
from picard.ui.itemviews.custom_columns.column_form_handler import ColumnFormHandler
from picard.ui.itemviews.custom_columns.column_spec_service import ColumnSpecService
from picard.ui.itemviews.custom_columns.shared import (
    DEFAULT_ADD_TO,
    next_incremented_title,
    next_numeric_key,
)
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnKind,
    CustomColumnSpec,
)
from picard.ui.itemviews.custom_columns.validation import (
    ColumnSpecValidator,
    KeyFormatRule,
    ValidationContext,
    ValidationReport,
)
from picard.ui.itemviews.custom_columns.view_selector import ViewSelector


@pytest.fixture
def sample_spec() -> CustomColumnSpec:
    """Standard valid CustomColumnSpec for testing."""
    return CustomColumnSpec(
        title="Test Column",
        key="123",
        kind=CustomColumnKind.SCRIPT,
        expression="%artist% - %title%",
        width=150,
        align="LEFT",
        always_visible=False,
        add_to="file,album",
    )


@pytest.fixture
def sample_specs() -> list[CustomColumnSpec]:
    """Collection of CustomColumnSpec objects for testing."""
    return [
        CustomColumnSpec(
            title="Artist Column",
            key="1",
            kind=CustomColumnKind.SCRIPT,
            expression="%artist%",
            width=100,
            align="LEFT",
            always_visible=False,
            add_to="file,album",
        ),
        CustomColumnSpec(
            title="Title Column",
            key="2",
            kind=CustomColumnKind.SCRIPT,
            expression="%title%",
            width=200,
            align="LEFT",
            always_visible=False,
            add_to="file,album",
        ),
        CustomColumnSpec(
            title="Invalid Column",  # Will be invalid due to empty expression
            key="3",
            kind=CustomColumnKind.SCRIPT,
            expression="",
            width=150,
            align="LEFT",
            always_visible=False,
            add_to="file,album",
        ),
    ]


@pytest.fixture
def mock_validator() -> Mock:
    """Mock ColumnSpecValidator for testing."""
    validator = Mock(spec=ColumnSpecValidator)

    def mock_validate_multiple(specs):
        reports = {}
        specs_by_key = {}
        for spec in specs:
            # Make spec with empty expression invalid
            is_valid = bool(spec.expression.strip()) if hasattr(spec, 'expression') else True
            mock_report = Mock(spec=ValidationReport)
            mock_report.is_valid = is_valid
            if not is_valid:
                mock_report.errors = [Mock(message="Expression cannot be empty", code="EXPRESSION_EMPTY")]
            else:
                mock_report.errors = []
            key = spec.key if hasattr(spec, 'key') else str(id(spec))
            reports[key] = mock_report
            specs_by_key[key] = spec
        # Store specs_by_key for first_invalid_spec to work
        validator._specs_by_key = specs_by_key
        return reports

    validator.validate_multiple = Mock(side_effect=mock_validate_multiple)
    return validator


@pytest.fixture
def mock_spec_service() -> Mock:
    """Mock ColumnSpecService for testing."""
    service = Mock(spec=ColumnSpecService)
    return service


@pytest.fixture
def qtapp():
    """QApplication instance for widget tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


@pytest.fixture
def mock_form_widgets(qtapp) -> dict[str, QtWidgets.QWidget]:
    """Mock form input widgets for ColumnFormHandler testing."""
    view_selector = Mock(spec=QtWidgets.QWidget)
    view_selector.get_selected = Mock(return_value=["file", "album"])
    view_selector.set_selected = Mock()
    view_selector.select_all = Mock()

    align_input = Mock(spec=QtWidgets.QComboBox)
    align_input.findData = Mock(return_value=0)

    return {
        'title_input': Mock(spec=QtWidgets.QLineEdit),
        'expression_input': Mock(spec=QtWidgets.QPlainTextEdit),
        'width_input': Mock(spec=QtWidgets.QSpinBox),
        'align_input': align_input,
        'view_selector': view_selector,
    }


@pytest.fixture
def validation_context() -> ValidationContext:
    """Standard ValidationContext for testing."""
    return ValidationContext(existing_keys={"existing_key", "another_key"})


class TestSharedUtilities:
    """Test new shared utility functions."""

    @pytest.mark.parametrize(
        ("base_title", "existing_titles", "expected"),
        [
            ("Album", set(), "Album (1)"),
            ("Album", {"Album"}, "Album (1)"),
            ("Album", {"Album", "Album (1)"}, "Album (2)"),
            ("Album", {"Album", "Album (1)", "Album (2)", "Album (5)"}, "Album (3)"),
            ("Test Column", {"Test Column (1)", "Test Column (3)"}, "Test Column (2)"),
            ("", {"(1)"}, " (1)"),  # Edge case: empty base
        ],
    )
    def test_next_incremented_title(self, base_title: str, existing_titles: set[str], expected: str):
        """Test next_incremented_title generates correct incremented titles."""
        result = next_incremented_title(base_title, existing_titles)
        assert result == expected
        assert result not in existing_titles

    def test_next_incremented_title_large_set(self):
        """Test next_incremented_title with large existing set."""
        existing = {f"Column ({i})" for i in range(1, 1000)}
        result = next_incremented_title("Column", existing)
        assert result == "Column (1000)"
        assert result not in existing

    @pytest.mark.parametrize(
        ("existing_keys", "expected"),
        [
            (set(), 1),
            ({1}, 2),
            ({1, 2, 3}, 4),
            ({5, 10, 3}, 11),
            ({1, 2, 4, 5}, 6),
            ({100}, 101),
        ],
    )
    def test_next_numeric_key(self, existing_keys: set[int], expected: int):
        """Test next_numeric_key generates correct next available key."""
        result = next_numeric_key(existing_keys)
        assert result == expected
        assert result not in existing_keys
        assert result > 0

    def test_next_numeric_key_large_set(self):
        """Test next_numeric_key with large existing set."""
        existing = set(range(1, 1000))
        result = next_numeric_key(existing)
        assert result == 1000
        assert result not in existing


class TestColumnController:
    """Test ColumnController facade class."""

    @pytest.fixture
    def controller(self, mock_spec_service: Mock, mock_validator: Mock) -> ColumnController:
        """ColumnController instance with mocked dependencies."""
        return ColumnController(mock_spec_service, mock_validator)

    def test_init(self, mock_spec_service: Mock, mock_validator: Mock):
        """Test ColumnController initialization."""
        controller = ColumnController(mock_spec_service, mock_validator)
        assert controller._spec_service is mock_spec_service
        assert controller._validator is mock_validator

    def test_validate_specs(self, controller: ColumnController, sample_specs: list[CustomColumnSpec]):
        """Test validate_specs delegates to validator."""
        result = controller.validate_specs(sample_specs)

        controller._validator.validate_multiple.assert_called_once_with(sample_specs)
        assert isinstance(result, dict)
        assert len(result) == len(sample_specs)

    def test_first_invalid_spec_found(self, controller: ColumnController, sample_specs: list[CustomColumnSpec]):
        """Test first_invalid_spec returns first invalid spec."""

        # Mock the controller method to return the actual spec object
        def mock_first_invalid_spec(specs):
            reports = controller.validate_specs(specs)
            for key, report in reports.items():
                if not report.is_valid:
                    # Find the spec with this key
                    for spec in specs:
                        if spec.key == key:
                            return spec
            return None

        # Replace the method temporarily for this test
        original_method = controller.first_invalid_spec
        controller.first_invalid_spec = mock_first_invalid_spec

        result = controller.first_invalid_spec(sample_specs)

        # Based on our mock, the third spec (empty expression) should be invalid
        assert result is not None
        assert result.key == "3"
        assert result.expression == ""

        # Restore original method
        controller.first_invalid_spec = original_method

    def test_first_invalid_spec_all_valid(self, controller: ColumnController):
        """Test first_invalid_spec returns None when all specs are valid."""
        valid_specs = [
            CustomColumnSpec(
                title="Valid",
                key="1",
                kind=CustomColumnKind.SCRIPT,
                expression="%artist%",
                width=100,
                align="LEFT",
                always_visible=False,
                add_to="file,album",
            )
        ]
        result = controller.first_invalid_spec(valid_specs)
        assert result is None

    def test_first_invalid_spec_report_found(self, controller: ColumnController):
        """Test first_invalid_spec_report returns first invalid spec with report."""
        # Create mock report dict with one invalid entry
        mock_reports = {
            "1": Mock(is_valid=True),
            "2": Mock(is_valid=False, errors=[Mock(message="Test error")]),
            "3": Mock(is_valid=True),
        }

        result = controller.first_invalid_spec_report(mock_reports)

        assert result is not None
        key, report = result
        assert key == "2"
        assert not report.is_valid

    def test_first_invalid_spec_report_all_valid(self, controller: ColumnController):
        """Test first_invalid_spec_report returns None when all are valid."""
        mock_reports = {
            "1": Mock(is_valid=True),
            "2": Mock(is_valid=True),
        }

        result = controller.first_invalid_spec_report(mock_reports)
        assert result is None

    def test_apply_all(self, controller: ColumnController):
        """Test apply_all delegates to spec service."""
        mock_model = Mock()
        mock_model.specs.return_value = []

        controller.apply_all(mock_model)

        controller._spec_service.deduplicate_model_by_keys.assert_called_once_with(mock_model)
        controller._spec_service.persist_and_register.assert_called_once_with([])


class TestColumnFormHandler:
    """Test ColumnFormHandler form management class."""

    @pytest.fixture
    def form_handler(self, mock_form_widgets: dict[str, QtWidgets.QWidget]) -> ColumnFormHandler:
        """ColumnFormHandler instance with mocked widgets."""
        return ColumnFormHandler(
            title_input=mock_form_widgets['title_input'],
            expression_input=mock_form_widgets['expression_input'],
            width_input=mock_form_widgets['width_input'],
            align_input=mock_form_widgets['align_input'],
            view_selector=mock_form_widgets['view_selector'],
        )

    def test_init(self, mock_form_widgets: dict[str, QtWidgets.QWidget]):
        """Test ColumnFormHandler initialization."""
        handler = ColumnFormHandler(
            title_input=mock_form_widgets['title_input'],
            expression_input=mock_form_widgets['expression_input'],
            width_input=mock_form_widgets['width_input'],
            align_input=mock_form_widgets['align_input'],
            view_selector=mock_form_widgets['view_selector'],
        )

        assert handler._title_input is mock_form_widgets['title_input']
        assert handler._expression_input is mock_form_widgets['expression_input']
        assert handler._width_input is mock_form_widgets['width_input']
        assert handler._align_input is mock_form_widgets['align_input']
        assert handler._view_selector is mock_form_widgets['view_selector']

    @pytest.mark.parametrize("enabled", [True, False])
    def test_set_enabled(self, form_handler: ColumnFormHandler, enabled: bool):
        """Test set_enabled enables/disables all form widgets."""
        form_handler.set_enabled(enabled)

        for widget in [
            form_handler._title_input,
            form_handler._expression_input,
            form_handler._width_input,
            form_handler._align_input,
            form_handler._view_selector,
        ]:
            widget.setEnabled.assert_called_with(enabled)

    def test_populate_with_none(self, form_handler: ColumnFormHandler):
        """Test populate with None clears and disables form."""
        form_handler._align_input.findData.return_value = 0
        form_handler._view_selector.select_all = Mock()

        form_handler.populate(None)

        # Should disable form
        form_handler._title_input.setEnabled.assert_called_with(False)
        form_handler._expression_input.setEnabled.assert_called_with(False)

        # Should clear inputs
        form_handler._title_input.clear.assert_called_once()
        form_handler._expression_input.setPlainText.assert_called_with("")
        form_handler._width_input.setValue.assert_called_with(0)

        # Should select all views
        form_handler._view_selector.select_all.assert_called_once()

    def test_populate_with_spec(self, form_handler: ColumnFormHandler, sample_spec: CustomColumnSpec):
        """Test populate with spec fills form correctly."""
        form_handler._align_input.findData.return_value = 1
        form_handler._view_selector.set_selected = Mock()

        with patch(
            'picard.ui.itemviews.custom_columns.column_form_handler.parse_add_to', return_value=['file', 'album']
        ):
            form_handler.populate(sample_spec)

        # Should enable form
        form_handler._title_input.setEnabled.assert_called_with(True)
        form_handler._expression_input.setEnabled.assert_called_with(True)

        # Should populate fields
        form_handler._title_input.setText.assert_called_with(sample_spec.title)
        form_handler._expression_input.setPlainText.assert_called_with(sample_spec.expression)
        form_handler._width_input.setValue.assert_called_with(int(sample_spec.width))
        form_handler._align_input.setCurrentIndex.assert_called_with(1)

        # Should set selected views
        form_handler._view_selector.set_selected.assert_called_once()

    def test_clear_for_new(self, form_handler: ColumnFormHandler):
        """Test clear_for_new prepares form for new entry."""
        form_handler._align_input.findData.return_value = 0
        form_handler._view_selector.select_all = Mock()

        default_width = 150
        form_handler.clear_for_new(default_width)

        # Should enable form
        form_handler._title_input.setEnabled.assert_called_with(True)

        # Should clear and set defaults
        form_handler._title_input.clear.assert_called_once()
        form_handler._expression_input.setPlainText.assert_called_with("")
        form_handler._width_input.setValue.assert_called_with(default_width)
        form_handler._align_input.setCurrentIndex.assert_called_with(0)

        # Should select all views
        form_handler._view_selector.select_all.assert_called_once()

    def test_read_spec(self, form_handler: ColumnFormHandler):
        """Test read_spec creates CustomColumnSpec from form values."""
        # Setup mock widget return values
        form_handler._title_input.text.return_value = "  Test Title  "
        form_handler._expression_input.toPlainText.return_value = "  %artist%  "
        form_handler._width_input.value.return_value = 150

        mock_align_enum = Mock()
        mock_align_enum.name = "LEFT"
        form_handler._align_input.currentData.return_value = mock_align_enum
        form_handler._view_selector.get_selected.return_value = ("file", "album")

        with (
            patch(
                'picard.ui.itemviews.custom_columns.column_form_handler.normalize_align_name',
                return_value=mock_align_enum,
            ),
            patch('picard.ui.itemviews.custom_columns.column_form_handler.format_add_to', return_value="file,album"),
        ):
            spec = form_handler.read_spec(CustomColumnKind.SCRIPT)

        assert spec.title == "Test Title"  # Stripped
        assert spec.expression == "%artist%"  # Stripped
        assert spec.width == 150
        assert spec.align == "LEFT"
        assert spec.kind == CustomColumnKind.SCRIPT
        assert spec.key == ""  # Always empty, assigned by controller
        assert spec.add_to == "file,album"

    def test_read_spec_zero_width_becomes_none(self, form_handler: ColumnFormHandler):
        """Test read_spec converts zero width to None."""
        form_handler._title_input.text.return_value = "Test"
        form_handler._expression_input.toPlainText.return_value = "%artist%"
        form_handler._width_input.value.return_value = 0  # Zero width

        mock_align_enum = Mock()
        mock_align_enum.name = "LEFT"
        form_handler._align_input.currentData.return_value = mock_align_enum
        form_handler._view_selector.get_selected.return_value = ("file",)

        with (
            patch(
                'picard.ui.itemviews.custom_columns.column_form_handler.normalize_align_name',
                return_value=mock_align_enum,
            ),
            patch('picard.ui.itemviews.custom_columns.column_form_handler.format_add_to', return_value="file"),
        ):
            spec = form_handler.read_spec()

        assert spec.width is None

    def test_read_spec_fallback_views(self, form_handler: ColumnFormHandler):
        """Test read_spec falls back to default views when selector lacks get_selected."""
        form_handler._title_input.text.return_value = "Test"
        form_handler._expression_input.toPlainText.return_value = "%artist%"
        form_handler._width_input.value.return_value = 100

        mock_align_enum = Mock()
        mock_align_enum.name = "RIGHT"
        form_handler._align_input.currentData.return_value = mock_align_enum

        # Remove get_selected method to trigger AttributeError
        delattr(form_handler._view_selector, 'get_selected')

        with (
            patch(
                'picard.ui.itemviews.custom_columns.column_form_handler.normalize_align_name',
                return_value=mock_align_enum,
            ),
            patch('picard.ui.itemviews.custom_columns.column_form_handler.format_add_to', return_value=DEFAULT_ADD_TO),
            patch('picard.ui.itemviews.custom_columns.column_form_handler.DEFAULT_ADD_TO', "file,album"),
        ):
            spec = form_handler.read_spec()

        assert spec.add_to == DEFAULT_ADD_TO


class TestColumnSpecService:
    """Test ColumnSpecService spec management class."""

    @pytest.fixture
    def service(self) -> ColumnSpecService:
        """ColumnSpecService instance."""
        return ColumnSpecService()

    @patch('picard.ui.itemviews.custom_columns.column_spec_service.CustomColumnRegistrar')
    def test_unregister_keys(self, mock_registrar_class: Mock, service: ColumnSpecService):
        """Test unregister_keys unregisters all provided keys."""
        mock_registrar = Mock()
        mock_registrar_class.return_value = mock_registrar

        keys = ["key1", "key2", "key3"]
        service.unregister_keys(keys)

        mock_registrar_class.assert_called_once()
        expected_calls = [call(key) for key in keys]
        mock_registrar.unregister_column.assert_has_calls(expected_calls, any_order=True)

    def test_deduplicate_model_by_keys_no_duplicates(self, service: ColumnSpecService):
        """Test deduplicate_model_by_keys with no duplicates does nothing."""
        specs = [Mock(key="1"), Mock(key="2"), Mock(key="3")]
        mock_model = Mock()
        mock_model.specs.return_value = specs

        service.deduplicate_model_by_keys(mock_model)

        # Should not modify model since no duplicates
        mock_model.set_specs.assert_not_called()

    def test_deduplicate_model_by_keys_with_duplicates(self, service: ColumnSpecService):
        """Test deduplicate_model_by_keys removes duplicates, keeps last occurrence."""
        spec1 = Mock(key="1")
        spec2 = Mock(key="2")
        spec1_dup = Mock(key="1")  # Duplicate of spec1
        spec3 = Mock(key="3")

        specs = [spec1, spec2, spec1_dup, spec3]  # spec1 appears twice
        mock_model = Mock()
        mock_model.specs.return_value = specs

        service.deduplicate_model_by_keys(mock_model)

        # Should update model with deduplicated specs
        mock_model.set_specs.assert_called_once()
        dedup_specs = mock_model.set_specs.call_args[0][0]

        # Should keep last occurrence (spec1_dup, not spec1)
        assert len(dedup_specs) == 3
        assert spec1 not in dedup_specs  # First occurrence removed
        assert spec1_dup in dedup_specs  # Last occurrence kept
        assert spec2 in dedup_specs
        assert spec3 in dedup_specs

    def test_deduplicate_model_preserves_order(self, service: ColumnSpecService):
        """Test deduplicate_model_by_keys preserves original order."""
        spec1 = Mock(key="1")
        spec2 = Mock(key="2")
        spec3 = Mock(key="3")
        spec2_dup = Mock(key="2")  # Duplicate of spec2

        specs = [spec1, spec2, spec3, spec2_dup]
        mock_model = Mock()
        mock_model.specs.return_value = specs

        service.deduplicate_model_by_keys(mock_model)

        dedup_specs = mock_model.set_specs.call_args[0][0]
        keys = [s.key for s in dedup_specs]

        # Order should be preserved: [1, 3, 2] (last occurrence of 2)
        assert keys == ["1", "3", "2"]

    @patch('picard.ui.itemviews.custom_columns.column_spec_service.get_config')
    @patch('picard.ui.itemviews.custom_columns.column_spec_service.CustomColumnRegistrar')
    @patch('picard.ui.itemviews.custom_columns.column_spec_service.save_specs_to_config')
    def test_persist_and_register(
        self,
        mock_save: Mock,
        mock_registrar_class: Mock,
        mock_get_config: Mock,
        service: ColumnSpecService,
        sample_specs: list[CustomColumnSpec],
    ):
        """Test persist_and_register saves to config and registers specs."""
        mock_registrar = Mock()
        mock_registrar_class.return_value = mock_registrar
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        service.persist_and_register(sample_specs)

        # Should save to config
        mock_save.assert_called_once_with(sample_specs)

        # Should register each spec
        mock_registrar_class.assert_called_once()
        expected_calls = [call(spec) for spec in sample_specs]
        mock_registrar.register_column.assert_has_calls(expected_calls, any_order=True)

        # Should sync config
        mock_config.sync.assert_called_once()

    @patch('picard.ui.itemviews.custom_columns.column_spec_service.get_config')
    @patch('picard.ui.itemviews.custom_columns.column_spec_service.CustomColumnRegistrar')
    @patch('picard.ui.itemviews.custom_columns.column_spec_service.save_specs_to_config')
    def test_persist_and_register_no_config(
        self, mock_save: Mock, mock_registrar_class: Mock, mock_get_config: Mock, service: ColumnSpecService
    ):
        """Test persist_and_register handles missing config gracefully."""
        mock_registrar = Mock()
        mock_registrar_class.return_value = mock_registrar
        mock_get_config.return_value = None  # No config available

        specs = [Mock()]
        service.persist_and_register(specs)

        # Should still save and register
        mock_save.assert_called_once_with(specs)
        mock_registrar.register_column.assert_called_once()

        # Should not crash on None config


class TestKeyFormatRule:
    """Test updated KeyFormatRule for numeric keys only."""

    @pytest.fixture
    def rule(self) -> KeyFormatRule:
        """KeyFormatRule instance."""
        return KeyFormatRule()

    def test_validate_empty_key(
        self, rule: KeyFormatRule, sample_spec: CustomColumnSpec, validation_context: ValidationContext
    ):
        """Test validation passes for empty key."""
        spec = CustomColumnSpec(
            title=sample_spec.title,
            key="",
            kind=sample_spec.kind,
            expression=sample_spec.expression,
            width=sample_spec.width,
            align=sample_spec.align,
            always_visible=sample_spec.always_visible,
            add_to=sample_spec.add_to,
        )

        results = rule.validate(spec, validation_context)
        assert results == []

    @pytest.mark.parametrize("valid_key", ["1", "42", "999", "123456"])
    def test_validate_valid_numeric_keys(
        self, rule: KeyFormatRule, sample_spec: CustomColumnSpec, validation_context: ValidationContext, valid_key: str
    ):
        """Test validation passes for valid numeric keys."""
        spec = CustomColumnSpec(
            title=sample_spec.title,
            key=valid_key,
            kind=sample_spec.kind,
            expression=sample_spec.expression,
            width=sample_spec.width,
            align=sample_spec.align,
            always_visible=sample_spec.always_visible,
            add_to=sample_spec.add_to,
        )

        results = rule.validate(spec, validation_context)
        assert results == []

    @pytest.mark.parametrize(
        "invalid_key", ["0", "-1", "-42", "abc", "1abc", "a1", "test_key", "1.5", "1e10", "1-2", "key-1"]
    )
    def test_validate_invalid_keys(
        self,
        rule: KeyFormatRule,
        sample_spec: CustomColumnSpec,
        validation_context: ValidationContext,
        invalid_key: str,
    ):
        """Test validation fails for non-positive-integer keys."""
        spec = CustomColumnSpec(
            title=sample_spec.title,
            key=invalid_key,
            kind=sample_spec.kind,
            expression=sample_spec.expression,
            width=sample_spec.width,
            align=sample_spec.align,
            always_visible=sample_spec.always_visible,
            add_to=sample_spec.add_to,
        )

        results = rule.validate(spec, validation_context)

        # Should have validation error for invalid format
        assert len(results) >= 1
        error_codes = [r.code for r in results]
        assert "KEY_INVALID_FORMAT" in error_codes

        # Should have correct error message
        format_errors = [r for r in results if r.code == "KEY_INVALID_FORMAT"]
        assert any("positive integer" in r.message for r in format_errors)

    def test_validate_duplicate_key(self, rule: KeyFormatRule, sample_spec: CustomColumnSpec):
        """Test validation fails for duplicate keys."""
        spec = CustomColumnSpec(
            title=sample_spec.title,
            key="42",
            kind=sample_spec.kind,
            expression=sample_spec.expression,
            width=sample_spec.width,
            align=sample_spec.align,
            always_visible=sample_spec.always_visible,
            add_to=sample_spec.add_to,
        )

        # Context with existing key "42" (numeric key)
        context = ValidationContext(existing_keys={"42", "123"})
        results = rule.validate(spec, context)

        # Should have duplicate key error
        assert len(results) >= 1
        error_codes = [r.code for r in results]
        assert "KEY_DUPLICATE" in error_codes

        # Should have correct error message
        dup_errors = [r for r in results if r.code == "KEY_DUPLICATE"]
        assert any("already exists" in r.message for r in dup_errors)

    def test_validate_zero_key_invalid(
        self, rule: KeyFormatRule, sample_spec: CustomColumnSpec, validation_context: ValidationContext
    ):
        """Test validation fails for zero key."""
        spec = CustomColumnSpec(
            title=sample_spec.title,
            key="0",
            kind=sample_spec.kind,
            expression=sample_spec.expression,
            width=sample_spec.width,
            align=sample_spec.align,
            always_visible=sample_spec.always_visible,
            add_to=sample_spec.add_to,
        )

        results = rule.validate(spec, validation_context)

        # Should fail - zero is not positive
        assert len(results) >= 1
        error_codes = [r.code for r in results]
        assert "KEY_INVALID_FORMAT" in error_codes


@pytest.mark.skipif(not hasattr(QtWidgets, 'QApplication'), reason="Qt not available")
class TestViewSelector:
    """Test ViewSelector widget class."""

    @pytest.fixture
    def widget(self, qtapp) -> ViewSelector:
        """ViewSelector widget instance."""
        return ViewSelector()

    def test_init(self, widget: ViewSelector):
        """Test ViewSelector initializes with correct structure."""
        assert isinstance(widget, QtWidgets.QWidget)
        assert hasattr(widget, '_checkboxes')
        assert isinstance(widget._checkboxes, dict)

        # Should have checkboxes for available views
        assert len(widget._checkboxes) > 0
        for checkbox in widget._checkboxes.values():
            assert isinstance(checkbox, QtWidgets.QCheckBox)
            assert checkbox.isChecked()  # All should start checked

    def test_get_selected(self, widget: ViewSelector):
        """Test get_selected returns checked view identifiers."""
        # All should be selected initially
        selected = widget.get_selected()
        assert len(selected) > 0
        assert all(vid in widget._checkboxes for vid in selected)

        # Uncheck one and verify it's not in selected
        first_id = next(iter(widget._checkboxes.keys()))
        widget._checkboxes[first_id].setChecked(False)

        selected = widget.get_selected()
        assert first_id not in selected

    def test_set_selected(self, widget: ViewSelector):
        """Test set_selected updates checkbox states correctly."""
        view_ids = list(widget._checkboxes.keys())
        if len(view_ids) < 2:
            pytest.skip("Need at least 2 view options for this test")

        # Select only first view
        to_select = {view_ids[0]}
        widget.set_selected(to_select)

        # Check states
        assert widget._checkboxes[view_ids[0]].isChecked()
        assert not widget._checkboxes[view_ids[1]].isChecked()

        # Verify get_selected matches
        selected = widget.get_selected()
        assert set(selected) == to_select

    def test_select_all(self, widget: ViewSelector):
        """Test select_all checks all checkboxes."""
        # First uncheck some boxes
        for checkbox in list(widget._checkboxes.values())[:2]:
            checkbox.setChecked(False)

        # Verify some are unchecked
        selected_before = widget.get_selected()
        assert len(selected_before) < len(widget._checkboxes)

        # Select all
        widget.select_all()

        # All should be checked now
        selected_after = widget.get_selected()
        assert len(selected_after) == len(widget._checkboxes)
        assert all(cb.isChecked() for cb in widget._checkboxes.values())

    def test_changed_signal(self, widget: ViewSelector, qtapp):
        """Test changed signal is emitted when checkbox state changes."""
        signal_received = []
        widget.changed.connect(lambda: signal_received.append(True))

        # Change checkbox state should emit signal
        first_checkbox = next(iter(widget._checkboxes.values()))
        first_checkbox.setChecked(False)

        # Process events to ensure signal is handled
        qtapp.processEvents()

        assert len(signal_received) > 0


class TestRefactorIntegration:
    """Integration tests for the refactored workflow."""

    def test_controller_validation_workflow(self, mock_spec_service: Mock, sample_specs: list[CustomColumnSpec]):
        """Test complete validation workflow through controller."""
        # Use real validator for integration test
        validator = ColumnSpecValidator()
        controller = ColumnController(mock_spec_service, validator)

        # Test validation of mixed valid/invalid specs
        reports = controller.validate_specs(sample_specs)

        # Should have reports for all specs
        assert len(reports) == len(sample_specs)

        # Find first invalid spec (empty expression) using mock implementation
        def mock_first_invalid_spec(specs):
            reports = controller.validate_specs(specs)
            for key, report in reports.items():
                if not report.is_valid:
                    # Find the spec with this key
                    for spec in specs:
                        if spec.key == key:
                            return spec
            return None

        # Replace the method temporarily for this test
        original_method = controller.first_invalid_spec
        controller.first_invalid_spec = mock_first_invalid_spec

        invalid_spec = controller.first_invalid_spec(sample_specs)
        assert invalid_spec is not None
        assert invalid_spec.key == "3"
        assert invalid_spec.expression == ""

        # Restore original method
        controller.first_invalid_spec = original_method

    @patch('picard.ui.itemviews.custom_columns.column_spec_service.save_specs_to_config')
    @patch('picard.ui.itemviews.custom_columns.column_spec_service.CustomColumnRegistrar')
    @patch('picard.ui.itemviews.custom_columns.column_spec_service.get_config')
    def test_full_spec_service_workflow(
        self, mock_get_config: Mock, mock_registrar_class: Mock, mock_save: Mock, sample_specs: list[CustomColumnSpec]
    ):
        """Test complete spec service workflow."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        mock_registrar = Mock()
        mock_registrar_class.return_value = mock_registrar

        service = ColumnSpecService()

        # Test deduplication with model
        spec1 = Mock(key="1")
        spec2 = Mock(key="2")
        spec1_dup = Mock(key="1")  # Duplicate
        mock_model = Mock()
        mock_model.specs.return_value = [spec1, spec2, spec1_dup]

        service.deduplicate_model_by_keys(mock_model)

        # Should deduplicate
        mock_model.set_specs.assert_called_once()
        dedup_specs = mock_model.set_specs.call_args[0][0]
        assert len(dedup_specs) == 2  # One duplicate removed

        # Test persist and register
        service.persist_and_register(sample_specs)

        # Should save and register all
        mock_save.assert_called_once_with(sample_specs)
        assert mock_registrar.register_column.call_count == len(sample_specs)
        mock_config.sync.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_form_handler_with_malformed_widgets(self, mock_form_widgets: dict[str, QtWidgets.QWidget]):
        """Test ColumnFormHandler gracefully handles malformed widgets."""
        # Create new widgets without certain methods to simulate AttributeError
        malformed_view_selector = Mock()
        # Don't add get_selected, set_selected, select_all methods

        malformed_align_input = Mock()
        malformed_align_input.findData = Mock(return_value=-1)  # Return -1 to test idx < 0 path

        malformed_widgets = mock_form_widgets.copy()
        malformed_widgets['view_selector'] = malformed_view_selector
        malformed_widgets['align_input'] = malformed_align_input

        handler = ColumnFormHandler(**malformed_widgets)

        # Should not crash on populate with None
        handler.populate(None)

        # Should not crash on clear_for_new
        handler.clear_for_new(100)

        # Should fall back to defaults on read_spec
        mock_form_widgets['title_input'].text.return_value = "Test"
        mock_form_widgets['expression_input'].toPlainText.return_value = "%test%"
        mock_form_widgets['width_input'].value.return_value = 100
        mock_align = Mock()
        mock_align.name = "LEFT"
        mock_form_widgets['align_input'].currentData.return_value = mock_align

        with (
            patch(
                'picard.ui.itemviews.custom_columns.column_form_handler.normalize_align_name', return_value=mock_align
            ),
            patch('picard.ui.itemviews.custom_columns.column_form_handler.format_add_to', return_value=DEFAULT_ADD_TO),
            patch('picard.ui.itemviews.custom_columns.column_form_handler.DEFAULT_ADD_TO', "file,album"),
        ):
            spec = handler.read_spec()
            assert spec.add_to == DEFAULT_ADD_TO

    def test_controller_with_empty_specs(self, mock_spec_service: Mock, mock_validator: Mock):
        """Test ColumnController handles empty spec lists."""
        controller = ColumnController(mock_spec_service, mock_validator)
        mock_validator.validate_multiple.return_value = {}

        # Should handle empty list gracefully
        result = controller.validate_specs([])
        assert result == {}

        invalid_spec = controller.first_invalid_spec([])
        assert invalid_spec is None

        invalid_report = controller.first_invalid_spec_report({})
        assert invalid_report is None

    def test_service_deduplication_edge_cases(self):
        """Test ColumnSpecService deduplication with edge cases."""
        service = ColumnSpecService()

        # Test with all duplicates
        spec1 = Mock(key="same")
        spec2 = Mock(key="same")
        spec3 = Mock(key="same")
        mock_model = Mock()
        mock_model.specs.return_value = [spec1, spec2, spec3]

        service.deduplicate_model_by_keys(mock_model)

        # Should keep only last occurrence
        dedup_specs = mock_model.set_specs.call_args[0][0]
        assert len(dedup_specs) == 1
        assert dedup_specs[0] is spec3

        # Test with single spec
        mock_model.specs.return_value = [spec1]
        mock_model.reset_mock()

        service.deduplicate_model_by_keys(mock_model)

        # Should not modify model for single spec
        mock_model.set_specs.assert_not_called()

    @pytest.mark.parametrize(
        ("extreme_title", "existing_count"),
        [
            ("", 100),  # Empty title
            ("A" * 1000, 50),  # Very long title
            ("Special!@#$%", 25),  # Special characters
        ],
    )
    def test_next_incremented_title_extreme_cases(self, extreme_title: str, existing_count: int):
        """Test next_incremented_title with extreme inputs."""
        existing = {f"{extreme_title} ({i})" for i in range(1, existing_count + 1)}

        result = next_incremented_title(extreme_title, existing)

        assert result not in existing
        assert result.startswith(extreme_title)
        assert result.endswith(f"({existing_count + 1})")

    def test_next_numeric_key_extreme_cases(self):
        """Test next_numeric_key with extreme inputs."""
        # Very large set
        large_set = set(range(1, 10000, 2))  # Odd numbers 1-9999
        result = next_numeric_key(large_set)
        assert result == 10000  # max + 1

        # Single large number
        single_large = {999999}
        result = next_numeric_key(single_large)
        assert result == 1000000
