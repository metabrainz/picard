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

"""Column controller facade for custom column management dialogs.

Thin facade layer that reduces complexity in dialog components by
encapsulating validation and specification management logic.

Classes
-------
ColumnController
    Facade class that simplifies custom column operations for dialogs.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from picard.ui.itemviews.custom_columns.column_spec_service import ColumnSpecService
from picard.ui.itemviews.custom_columns.spec_list_model import SpecListModel
from picard.ui.itemviews.custom_columns.storage import CustomColumnSpec
from picard.ui.itemviews.custom_columns.validation import (
    ColumnSpecValidator,
    ValidationContext,
    ValidationReport,
)


class ColumnController:
    """Facade for custom column operations in dialog components.

    Provides simplified interface for common custom column operations,
    delegating to specialized services.

    Parameters
    ----------
    spec_service : ColumnSpecService
        Service for managing column specifications.
    validator : ColumnSpecValidator
        Validator for checking specification validity.
    """

    def __init__(self, spec_service: ColumnSpecService, validator: ColumnSpecValidator) -> None:
        """Initialize the column controller with required services."""
        self._spec_service = spec_service
        self._validator = validator

    def validate_specs(self, specs: Iterable[CustomColumnSpec]) -> dict[str, ValidationReport]:
        """Validate multiple column specifications.

        Returns
        -------
        dict[str, ValidationReport]
            Dictionary mapping specification keys to validation reports.
        """
        return self._validator.validate_multiple(specs)

    def first_invalid_spec(self, specs: Iterable[CustomColumnSpec]) -> CustomColumnSpec | None:
        """Find the first invalid specification in a collection.

        Returns
        -------
        CustomColumnSpec | None
            First invalid specification found, or None if all valid.
        """
        reports = self.validate_specs(specs)
        for spec, report in reports.items():
            if not report.is_valid:
                return spec
        return None

    def first_invalid_spec_report(self, report: dict[str, ValidationReport]) -> tuple[str, ValidationReport] | None:
        """Get first invalid specification with its validation report.

        Returns
        -------
        tuple[str, ValidationReport] | None
            (key, validation_report) for first invalid spec, or None.
        """
        for key, validation_report in report.items():
            if not validation_report.is_valid:
                return key, validation_report
        return None

    def validate_single(self, spec: CustomColumnSpec, existing_keys: set[str]) -> ValidationReport:
        """Validate a single column specification.

        Returns
        -------
        ValidationReport
            Report detailing the validation result.
        """
        context = ValidationContext(existing_keys=existing_keys)
        return self._validator.validate(spec, context)

    def apply_all(self, model: SpecListModel) -> None:
        """Apply all specifications from a model.

        Deduplicates and persists specifications.
        """
        self._spec_service.deduplicate_model_by_keys(model)
        self._spec_service.persist_and_register(model.specs())


@dataclass(frozen=True)
class InvalidSpecAnalysis:
    """Summary of the first invalid specification in a validation result set."""

    key: str
    error_messages: tuple[str, ...]
    warning_messages: tuple[str, ...]
    has_title_error: bool
    has_expression_error: bool
    has_only_blank_expression_warning: bool


def analyze_first_invalid(reports: dict[str, ValidationReport]) -> InvalidSpecAnalysis | None:
    """Analyze validation reports for the first blocking issue or blank-expression warning.

    Parameters
    ----------
    reports : dict[str, ValidationReport]
        Mapping of spec key to its validation report.

    Returns
    -------
    InvalidSpecAnalysis | None
        Summary for the first invalid spec, or None if all are valid.
    """
    for key, report in reports.items():
        errors = report.errors
        warnings = report.warnings
        # Determine if this report requires user attention
        has_only_blank_expression_warning = (
            len(errors) == 0
            and len(warnings) >= 1
            and all(getattr(w, "code", None) == "EXPRESSION_EMPTY" for w in warnings)
        )

        if not report.is_valid or has_only_blank_expression_warning:
            error_messages = tuple(r.message for r in errors)
            warning_messages = tuple(r.message for r in warnings)
            has_title_error = any(r.field == "title" for r in errors)
            has_expression_error = any(r.field == "expression" for r in errors)
            return InvalidSpecAnalysis(
                key=key,
                error_messages=error_messages,
                warning_messages=warning_messages,
                has_title_error=has_title_error,
                has_expression_error=has_expression_error,
                has_only_blank_expression_warning=has_only_blank_expression_warning,
            )
    return None
