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
# along with this program; if not, write to the
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Custom column specification service for Picard's item views.

Service class for managing custom column specifications including
registration, deduplication, and persistence.

Classes
-------
ColumnSpecService
    Service class for managing custom column specifications.
"""

from dataclasses import replace
from typing import Iterable

from picard.config import get_config

from picard.ui.itemviews.custom_columns.shared import (
    ALIGN_LEFT_NAME,
    DEFAULT_ADD_TO,
    DEFAULT_NEW_COLUMN_NAME,
    generate_new_key,
    next_incremented_title,
)
from picard.ui.itemviews.custom_columns.spec_list_model import SpecListModel
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnKind,
    CustomColumnRegistrar,
    CustomColumnSpec,
    save_specs_to_config,
)


class ColumnSpecService:
    """Service for managing custom column specifications.

    Handles registration, deduplication, and persistence operations.
    """

    @staticmethod
    def unregister_keys(keys: Iterable[str]) -> None:
        """Unregister custom columns by their keys."""
        registrar = CustomColumnRegistrar()
        for key in keys:
            registrar.unregister_column(key)

    def deduplicate_model_by_keys(self, model: SpecListModel) -> None:
        """Remove duplicate column specifications from a model.

        Preserves order while removing duplicates based on key.
        """
        specs = model.specs()
        seen: set[str] = set()
        dedup_reversed: list[CustomColumnSpec] = []
        for s in reversed(specs):
            if s.key in seen:
                continue
            seen.add(s.key)
            dedup_reversed.append(s)
        dedup_specs = list(reversed(dedup_reversed))
        if len(dedup_specs) != len(specs):
            model.set_specs(dedup_specs)

    def persist_and_register(self, specs: Iterable[CustomColumnSpec]) -> None:
        """Save specifications to config and register them.

        Saves to config, registers with registrar, and syncs.
        """
        save_specs_to_config(specs)
        registrar = CustomColumnRegistrar()
        for spec in specs:
            registrar.register_column(spec)
        cfg = get_config()
        if cfg is not None:
            cfg.sync()

    @staticmethod
    def allocate_new_key() -> str:
        """Allocate a new unique key for a custom column.

        Returns
        -------
        str
            New unique key.
        """
        return generate_new_key()

    def ensure_unique_nonempty_keys_in_model(self, model: SpecListModel) -> None:
        """Ensure all specs in the model have non-empty and unique keys.

        Assigns new keys for missing/blank keys or duplicates while preserving
        order and other fields.
        """
        specs = model.specs()
        seen: set[str] = set()
        for index, spec in enumerate(specs):
            key = spec.key or ""
            if not key.strip() or key in seen:
                new_key = self.allocate_new_key()
                seen.add(new_key)
                model.update_spec(index, replace(spec, key=new_key))
            else:
                seen.add(key)

    @staticmethod
    def create_placeholder_spec(
        default_width: int,
        current_specs: Iterable[CustomColumnSpec] | None = None,
    ) -> CustomColumnSpec:
        """Create a placeholder specification with blank expression.

        Creates a specification with the same default values as the form handler's
        clear_for_new method to ensure consistency between placeholder creation
        and form initialization. The title will be unique based on existing specs.

        Parameters
        ----------
        default_width : int
            Default width for the column.
        current_specs : Iterable[CustomColumnSpec] | None, optional
            Current specifications to check for title conflicts, by default None.

        Returns
        -------
        CustomColumnSpec
            New placeholder specification with blank expression and form-aligned defaults.
        """
        # Generate unique title based on existing specs
        existing_titles: set[str] = set()
        if current_specs:
            existing_titles = {spec.title for spec in current_specs if spec.title}

        # Use base title if it doesn't exist, otherwise generate incremented title
        if DEFAULT_NEW_COLUMN_NAME not in existing_titles:
            unique_title = DEFAULT_NEW_COLUMN_NAME
        else:
            unique_title = next_incremented_title(DEFAULT_NEW_COLUMN_NAME, existing_titles)
        return CustomColumnSpec(
            title=unique_title,
            key=ColumnSpecService.allocate_new_key(),
            kind=CustomColumnKind.SCRIPT,
            expression="",
            width=default_width,
            align=ALIGN_LEFT_NAME,  # Align with form handler default
            always_visible=False,
            add_to=DEFAULT_ADD_TO,  # Align with form handler default (select all views)
            sorting_adapter="",  # Align with form handler default (first item)
        )

    def duplicate_with_new_title_and_key(
        self, spec: CustomColumnSpec, specs: Iterable[CustomColumnSpec]
    ) -> CustomColumnSpec:
        """Create a duplicate of a specification with a new title and key.

        Parameters
        ----------
        spec : CustomColumnSpec
            Original specification to duplicate.
        new_title : str
            New title for the duplicated specification.

        Returns
        -------
        CustomColumnSpec
            New specification with updated title and unique key.
        """
        existing_titles = {s.title for s in specs}
        new_title = next_incremented_title(spec.title, existing_titles)
        new_key = self.allocate_new_key()
        return CustomColumnSpec(
            key=new_key,
            title=new_title,
            kind=spec.kind,
            expression=spec.expression,
            align=spec.align,
            width=spec.width,
            always_visible=spec.always_visible,
            add_to=spec.add_to,
        )
