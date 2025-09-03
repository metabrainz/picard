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

from typing import Any, Iterable

from picard.config import get_config

from picard.ui.itemviews.custom_columns.storage import (
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

    def deduplicate_model_by_keys(self, model: Any) -> None:
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
