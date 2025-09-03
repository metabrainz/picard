"""Column controller facade for custom column management dialogs.

Thin facade layer that reduces complexity in dialog components by
encapsulating validation and specification management logic.

Classes
-------
ColumnController
    Facade class that simplifies custom column operations for dialogs.
"""

from typing import Any, Iterable

from picard.ui.itemviews.custom_columns.column_spec_service import (
    ColumnSpecService,
)
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnSpec,
)
from picard.ui.itemviews.custom_columns.validation import (
    ColumnSpecValidator,
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

    def apply_all(self, model: Any) -> None:
        """Apply all specifications from a model.

        Deduplicates and persists specifications.
        """
        self._spec_service.deduplicate_model_by_keys(model)
        self._spec_service.persist_and_register(model.specs())
