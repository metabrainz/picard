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

"""Validation for CustomColumnSpec objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from picard.i18n import (
    N_,
    gettext as _,
    ngettext,
)
from picard.script import ScriptError, ScriptParser

from picard.ui.itemviews.custom_columns.shared import RECOGNIZED_VIEWS, parse_add_to
from picard.ui.itemviews.custom_columns.storage import CustomColumnKind, CustomColumnSpec


MAX_EXPRESSION_LENGTH = 500
MAX_KEY_LENGTH = 50
MAX_WIDTH = 1000


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(slots=True, frozen=True)
class ValidationResult:
    """Result of a validation check."""

    field: str
    severity: ValidationSeverity
    message: str
    code: str

    @property
    def is_error(self) -> bool:
        return self.severity == ValidationSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == ValidationSeverity.WARNING


@dataclass(slots=True, frozen=True)
class ValidationReport:
    """Complete validation report for a spec."""

    results: list[ValidationResult]

    @property
    def is_valid(self) -> bool:
        return not any(r.is_error for r in self.results)

    @property
    def errors(self) -> list[ValidationResult]:
        return [r for r in self.results if r.is_error]

    @property
    def warnings(self) -> list[ValidationResult]:
        return [r for r in self.results if r.is_warning]

    def summary(self) -> str:
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        if error_count == 0 and warning_count == 0:
            return _("Valid")
        parts: list[str] = []
        if error_count:
            parts.append(ngettext("%d error", "%d errors", error_count) % error_count)
        if warning_count:
            parts.append(ngettext("%d warning", "%d warnings", warning_count) % warning_count)
        return _(", ").join(parts)


class ValidationRule(ABC):
    """Base class for validation rules."""

    @abstractmethod
    def validate(self, spec: CustomColumnSpec, context: "ValidationContext") -> list[ValidationResult]:  # noqa: D401
        """Validate a spec and return any issues found."""
        raise NotImplementedError


class ValidationContext:
    """Context information for validation."""

    def __init__(self, existing_keys: set[str] | None = None):
        self.existing_keys = existing_keys or set()
        self._field_cache: dict[str, bool] = {}

    def is_field_valid(self, field_key: str) -> bool:
        if field_key not in self._field_cache:
            # Basic validation: non-empty and not whitespace; allow tilde-prefixed keys
            self._field_cache[field_key] = bool(field_key and not field_key.isspace())
        return self._field_cache[field_key]


class RequiredFieldRule(ValidationRule):
    def validate(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        if not spec.title or spec.title.isspace():
            results.append(
                ValidationResult(
                    "title", ValidationSeverity.ERROR, N_("Title is required and cannot be empty"), "TITLE_REQUIRED"
                )
            )
        if not spec.key or spec.key.isspace():
            results.append(
                ValidationResult(
                    "key", ValidationSeverity.ERROR, N_("Key is required and cannot be empty"), "KEY_REQUIRED"
                )
            )
        if not spec.expression or spec.expression.isspace():
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.WARNING,
                    N_("Expression is blank; the column will display nothing"),
                    "EXPRESSION_EMPTY",
                )
            )
        return results


class KeyFormatRule(ValidationRule):
    def validate(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        # Key is optional; when present, enforce format/length/uniqueness
        if not spec.key:
            return results

        def _normalize_key(value: UUID | str | None) -> str | None:
            if isinstance(value, UUID):
                return str(value)
            value_str = str(value or "").strip()
            if not value_str:
                return None

            # Attempt to parse the string as UUID
            try:
                uuid_obj = UUID(value_str)
            except ValueError:
                return None
            else:
                return str(uuid_obj)

        normalized_current = _normalize_key(spec.key)
        if not normalized_current:
            results.append(
                ValidationResult("key", ValidationSeverity.ERROR, N_("Key must be a valid UUID"), "KEY_INVALID_FORMAT")
            )
            return results

        normalized_existing = {n for n in (_normalize_key(k) for k in context.existing_keys) if n}
        if normalized_current in normalized_existing:
            results.append(
                ValidationResult(
                    "key", ValidationSeverity.ERROR, N_("Key '%s' already exists") % spec.key, "KEY_DUPLICATE"
                )
            )
        return results


class KeyRequiredRule(ValidationRule):
    def validate(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []

        # Key is required - check for None or blank
        if spec.key is None or spec.key == "":
            results.append(ValidationResult("key", ValidationSeverity.ERROR, N_("Key is required"), "KEY_REQUIRED"))
            return results

        # Check if key already exists in context
        if spec.key in context.existing_keys:
            results.append(
                ValidationResult(
                    "key", ValidationSeverity.ERROR, N_("Key '%s' already exists") % spec.key, "KEY_DUPLICATE"
                )
            )

        return results


class ExpressionRule(ValidationRule):
    def validate(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        if not spec.expression:
            return results
        if spec.kind == CustomColumnKind.FIELD:
            results.extend(self._validate_field_expression(spec, context))
        elif spec.kind == CustomColumnKind.SCRIPT:
            results.extend(self._validate_script_expression(spec))
        elif spec.kind == CustomColumnKind.TRANSFORM:
            results.extend(self._validate_transform_expression(spec, context))
        return results

    def _validate_field_expression(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        if not context.is_field_valid(spec.expression):
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.ERROR,
                    N_("Invalid field key: '%s'") % spec.expression,
                    "FIELD_INVALID",
                )
            )
        if spec.expression.startswith("$"):
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.WARNING,
                    N_("Field expressions should not start with '$' - use SCRIPT type for scripting"),
                    "FIELD_SCRIPT_SYNTAX",
                )
            )
        return results

    def _validate_script_expression(self, spec: CustomColumnSpec) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        parser = ScriptParser()
        try:
            parser.parse(spec.expression)
        except ScriptError as e:
            results.append(
                ValidationResult(
                    "expression", ValidationSeverity.ERROR, N_("Invalid script syntax: %s") % e, "SCRIPT_SYNTAX_ERROR"
                )
            )
        if len(spec.expression) > MAX_EXPRESSION_LENGTH:
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.WARNING,
                    N_("Very long scripts may impact performance"),
                    "SCRIPT_PERFORMANCE_WARNING",
                )
            )
        return results

    def _validate_transform_expression(
        self, spec: CustomColumnSpec, context: ValidationContext
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        if not context.is_field_valid(spec.expression):
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.ERROR,
                    N_("Invalid base field for transform: '%s'") % spec.expression,
                    "TRANSFORM_BASE_INVALID",
                )
            )
        if not getattr(spec, 'transform', None):
            results.append(
                ValidationResult(
                    "transform",
                    ValidationSeverity.ERROR,
                    N_("Transform type is required when kind is TRANSFORM"),
                    "TRANSFORM_TYPE_REQUIRED",
                )
            )
        return results


class ConsistencyRule(ValidationRule):
    def validate(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        if spec.kind != CustomColumnKind.TRANSFORM and getattr(spec, 'transform', None) is not None:
            results.append(
                ValidationResult(
                    "transform",
                    ValidationSeverity.WARNING,
                    N_("Transform specified but kind is not TRANSFORM"),
                    "TRANSFORM_INCONSISTENT",
                )
            )
        if spec.width is not None:
            if spec.width <= 0:
                results.append(
                    ValidationResult("width", ValidationSeverity.ERROR, N_("Width must be positive"), "WIDTH_INVALID")
                )
            elif spec.width > MAX_WIDTH:
                results.append(
                    ValidationResult(
                        "width",
                        ValidationSeverity.WARNING,
                        N_("Very wide columns may impact UI layout"),
                        "WIDTH_TOO_LARGE",
                    )
                )
        # Validate add_to views
        views = parse_add_to(getattr(spec, 'add_to', None))
        if not views:
            results.append(
                ValidationResult(
                    "add_to",
                    ValidationSeverity.WARNING,
                    N_("Column will not be visible in any view"),
                    "NO_VIEWS_SELECTED",
                )
            )
        # Warn about unknown tokens in add_to
        raw = getattr(spec, 'add_to', "") or ""
        unknown = {t.strip().upper() for t in raw.split(",") if t.strip()} - (views or set()) - RECOGNIZED_VIEWS
        if unknown:
            results.append(
                ValidationResult(
                    "add_to",
                    ValidationSeverity.WARNING,
                    N_("Unknown views in add_to: %s") % ', '.join(sorted(unknown)),
                    "UNKNOWN_VIEWS",
                )
            )
        return results


class ColumnSpecValidator:
    """Main validator for CustomColumnSpec objects."""

    def __init__(self) -> None:
        self.rules: list[ValidationRule] = [
            RequiredFieldRule(),
            KeyRequiredRule(),
            ExpressionRule(),
            ConsistencyRule(),
        ]

    def validate(self, spec: CustomColumnSpec, context: ValidationContext | None = None) -> ValidationReport:
        if context is None:
            context = ValidationContext()
        all_results = [result for rule in self.rules for result in rule.validate(spec, context)]
        return ValidationReport(all_results)

    def validate_multiple(self, specs: list[CustomColumnSpec]) -> dict[str, ValidationReport]:
        existing_keys = {spec.key for spec in specs if spec.key}
        reports: dict[str, ValidationReport] = {}
        for spec in specs:
            key = spec.key or f"<unnamed:{id(spec)}>"
            context = ValidationContext(existing_keys - ({spec.key} if spec.key else set()))
            reports[key] = self.validate(spec, context)
        return reports

    def add_rule(self, rule: ValidationRule) -> None:
        self.rules.append(rule)


def validate_spec(spec: CustomColumnSpec, existing_keys: set[str] | None = None) -> ValidationReport:
    validator = ColumnSpecValidator()
    return validator.validate(spec, ValidationContext(existing_keys))


def is_spec_valid(spec: CustomColumnSpec, existing_keys: set[str] | None = None) -> bool:
    return validate_spec(spec, existing_keys).is_valid
