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
import re

from picard.script import ScriptError, ScriptParser

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
            return "Valid"
        parts: list[str] = []
        if error_count:
            parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
        if warning_count:
            parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")
        return ", ".join(parts)


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
                    "title", ValidationSeverity.ERROR, "Title is required and cannot be empty", "TITLE_REQUIRED"
                )
            )
        if not spec.key or spec.key.isspace():
            results.append(
                ValidationResult("key", ValidationSeverity.ERROR, "Key is required and cannot be empty", "KEY_REQUIRED")
            )
        if not spec.expression or spec.expression.isspace():
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.ERROR,
                    "Expression is required and cannot be empty",
                    "EXPRESSION_REQUIRED",
                )
            )
        return results


class KeyFormatRule(ValidationRule):
    KEY_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")

    def validate(self, spec: CustomColumnSpec, context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        # Key is optional; when present, enforce format/length/uniqueness
        if not spec.key:
            return results
        if not self.KEY_PATTERN.match(spec.key):
            results.append(
                ValidationResult(
                    "key",
                    ValidationSeverity.ERROR,
                    "Key must start with a letter and contain only letters, numbers, underscores, and hyphens",
                    "KEY_INVALID_FORMAT",
                )
            )
        if len(spec.key) > MAX_KEY_LENGTH:
            results.append(
                ValidationResult(
                    "key",
                    ValidationSeverity.ERROR,
                    f"Key must be {MAX_KEY_LENGTH} characters or less",
                    "KEY_TOO_LONG",
                )
            )
        if spec.key in context.existing_keys:
            results.append(
                ValidationResult("key", ValidationSeverity.ERROR, f"Key '{spec.key}' already exists", "KEY_DUPLICATE")
            )
        if spec.key.startswith("_") or spec.key in {"title", "artist", "album"}:
            results.append(
                ValidationResult(
                    "key",
                    ValidationSeverity.WARNING,
                    f"Key '{spec.key}' may conflict with built-in columns",
                    "KEY_POTENTIALLY_RESERVED",
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
                    "expression", ValidationSeverity.ERROR, f"Invalid field key: '{spec.expression}'", "FIELD_INVALID"
                )
            )
        if spec.expression.startswith("$"):
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.WARNING,
                    "Field expressions should not start with '$' - use SCRIPT type for scripting",
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
                    "expression", ValidationSeverity.ERROR, f"Invalid script syntax: {e}", "SCRIPT_SYNTAX_ERROR"
                )
            )
        if len(spec.expression) > MAX_EXPRESSION_LENGTH:
            results.append(
                ValidationResult(
                    "expression",
                    ValidationSeverity.WARNING,
                    "Very long scripts may impact performance",
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
                    f"Invalid base field for transform: '{spec.expression}'",
                    "TRANSFORM_BASE_INVALID",
                )
            )
        if not getattr(spec, 'transform', None):
            results.append(
                ValidationResult(
                    "transform",
                    ValidationSeverity.ERROR,
                    "Transform type is required when kind is TRANSFORM",
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
                    "Transform specified but kind is not TRANSFORM",
                    "TRANSFORM_INCONSISTENT",
                )
            )
        if spec.width is not None:
            if spec.width <= 0:
                results.append(
                    ValidationResult("width", ValidationSeverity.ERROR, "Width must be positive", "WIDTH_INVALID")
                )
            elif spec.width > MAX_WIDTH:
                results.append(
                    ValidationResult(
                        "width", ValidationSeverity.WARNING, "Very wide columns may impact UI layout", "WIDTH_TOO_LARGE"
                    )
                )
        if not spec.add_to_file_view and not spec.add_to_album_view:
            results.append(
                ValidationResult(
                    "add_to_file_view",
                    ValidationSeverity.WARNING,
                    "Column will not be visible in any view",
                    "NO_VIEWS_SELECTED",
                )
            )
        return results


class CustomColumnSpecValidator:
    """Main validator for CustomColumnSpec objects."""

    def __init__(self) -> None:
        self.rules: list[ValidationRule] = [
            RequiredFieldRule(),
            KeyFormatRule(),
            ExpressionRule(),
            ConsistencyRule(),
        ]

    def validate(self, spec: CustomColumnSpec, context: ValidationContext | None = None) -> ValidationReport:
        if context is None:
            context = ValidationContext()
        all_results: list[ValidationResult] = []
        for rule in self.rules:
            all_results.extend(rule.validate(spec, context))
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
    validator = CustomColumnSpecValidator()
    return validator.validate(spec, ValidationContext(existing_keys))


def is_spec_valid(spec: CustomColumnSpec, existing_keys: set[str] | None = None) -> bool:
    return validate_spec(spec, existing_keys).is_valid
