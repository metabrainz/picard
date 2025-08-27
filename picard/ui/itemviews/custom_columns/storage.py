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

"""Persistence and application of user-defined custom columns.

This module handles serialization of custom column specifications to and from
the application configuration and registering those columns into the UI using
the public custom columns API.

All functions and classes are fully type-annotated and include NumPy-style
docstrings.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable

from picard import log
from picard.config import get_config

from picard.ui.columns import ColumnAlign
from picard.ui.itemviews.custom_columns import (
    CustomColumn,
    make_field_column,
    make_script_column,
    make_transformed_column,
    registry,
)
from picard.ui.itemviews.custom_columns.providers import FieldReferenceProvider


class CustomColumnKind(str, Enum):
    """Kinds of user-defined custom columns.

    Values
    ------
    FIELD
        A simple field reference (e.g. ``title`` or ``~bitrate``).
    SCRIPT
        A Picard scripting expression (e.g. ``$if(%artist%,%artist%,Unknown)``).
    TRANSFORM
        Apply a predefined transform function to a base provider (initially
        limited to simple transforms for safety and portability).
    """

    FIELD = "field"
    SCRIPT = "script"
    TRANSFORM = "transform"


class TransformName(str, Enum):
    """Supported transform functions for UI-defined transformed columns.

    Notes
    -----
    These are intentionally limited to safe, deterministic string functions.
    """

    UPPER = "upper"
    LOWER = "lower"
    TITLE = "title"
    STRIP = "strip"
    BRACKETS = "brackets"  # surround value with square brackets


@dataclass(slots=True)
class CustomColumnSpec:
    """Serializable specification for a custom column.

    Parameters
    ----------
    title
        Display title of the column.
    key
        Internal unique key for the column. Used for registration and lookup.
    kind
        Kind of column: field, script or transform.
    expression
        For ``FIELD``: the field key. For ``SCRIPT``: the script text. For
        ``TRANSFORM``: the base field key (initial support).
    width
        Optional width in pixels. ``None`` to use defaults.
    align
        Text alignment as ``LEFT`` or ``RIGHT``.
    always_visible
        If ``True``, the column is not toggleable in the header menu.
    add_to_file_view
        Whether to add this column to the File view.
    add_to_album_view
        Whether to add this column to the Album view.
    insert_after_key
        Insert new column after this existing key if present, else append.
    transform
        Optional transform name when ``kind == TRANSFORM``.
    """

    title: str
    key: str
    kind: CustomColumnKind
    expression: str
    width: int | None = None
    align: str = "LEFT"
    always_visible: bool = False
    add_to_file_view: bool = True
    add_to_album_view: bool = True
    insert_after_key: str | None = None
    transform: TransformName | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return CustomColumnSpecSerializer.to_dict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CustomColumnSpec:
        """Create a spec from a mapping."""
        return CustomColumnSpecSerializer.from_dict(data)


def _safe_convert(data: dict[str, Any], key: str, converter: Callable[[Any], Any], default: Any) -> Any:
    """Safely convert a dictionary value with fallback.

    Converter is applied if value is present and not None; otherwise default
    is returned. Conversion errors fall back to default.
    """

    try:
        if key not in data:
            return default
        value = data.get(key)
        if value is None:
            return default
        return converter(value)
    except (TypeError, ValueError):
        return default


class CustomColumnSpecSerializer:
    """Serialization / deserialization for CustomColumnSpec."""

    @staticmethod
    def to_dict(spec: CustomColumnSpec) -> dict[str, Any]:
        data = asdict(spec)
        data['kind'] = spec.kind.value
        if spec.transform is not None:
            data['transform'] = spec.transform.value
        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CustomColumnSpec:
        kind_name = _safe_convert(data, "kind", str, CustomColumnKind.FIELD.value)
        kind = CustomColumnKind(kind_name)
        transform_value = data.get('transform')
        transform = TransformName(str(transform_value)) if transform_value is not None else None
        return CustomColumnSpec(
            title=_safe_convert(data, "title", str, ""),
            key=_safe_convert(data, "key", str, ""),
            kind=kind,
            expression=_safe_convert(data, "expression", str, ""),
            width=_safe_convert(data, "width", int, None),
            align=_safe_convert(data, "align", str, "LEFT"),
            always_visible=_safe_convert(data, "always_visible", bool, False),
            add_to_file_view=_safe_convert(data, "add_to_file_view", bool, True),
            add_to_album_view=_safe_convert(data, "add_to_album_view", bool, True),
            insert_after_key=_safe_convert(data, "insert_after_key", str, None),
            transform=transform,
        )


def _align_from_name(name: str) -> ColumnAlign:
    """Map alignment name to :class:`~picard.ui.columns.ColumnAlign`.

    Parameters
    ----------
    name
        Alignment name, case-insensitive. Supported: ``LEFT``, ``RIGHT``.

    Returns
    -------
    ColumnAlign
        Corresponding alignment enum (defaults to LEFT on unknown).
    """

    upper = name.upper().strip()
    if upper == "RIGHT":
        return ColumnAlign.RIGHT
    return ColumnAlign.LEFT


def _make_transform_callable(name: TransformName) -> Callable[[str], str]:
    """Return a safe transform callable for the given name.

    Parameters
    ----------
    name
        Transform name.

    Returns
    -------
    callable
        A function that takes and returns ``str``.
    """

    if name == TransformName.UPPER:
        return lambda s: (s or "").upper()
    if name == TransformName.LOWER:
        return lambda s: (s or "").lower()
    if name == TransformName.TITLE:
        return lambda s: (s or "").title()
    if name == TransformName.STRIP:
        return lambda s: (s or "").strip()
    if name == TransformName.BRACKETS:
        return lambda s: f"[{s}]" if s else ""
    # Fallback no-op
    return lambda s: s or ""


def build_column_from_spec(spec: CustomColumnSpec) -> CustomColumn:
    """Build a :class:`CustomColumn` instance from a specification.

    Parameters
    ----------
    spec
        The column specification to convert.

    Returns
    -------
    CustomColumn
        The constructed custom column ready for registration.
    """

    align = _align_from_name(spec.align)
    if spec.kind == CustomColumnKind.FIELD:
        return make_field_column(
            spec.title, spec.key, width=spec.width, align=align, always_visible=spec.always_visible
        )
    if spec.kind == CustomColumnKind.SCRIPT:
        return make_script_column(
            spec.title,
            spec.key,
            spec.expression,
            width=spec.width,
            align=align,
            always_visible=spec.always_visible,
        )
    # TRANSFORM: apply transform to a base provider derived from expression
    transform_fn = _make_transform_callable(spec.transform or TransformName.STRIP)
    base_provider = FieldReferenceProvider(spec.expression)
    return make_transformed_column(
        spec.title,
        spec.key,
        base=base_provider,
        transform=transform_fn,
        width=spec.width,
        align=align,
        always_visible=spec.always_visible,
    )


class CustomColumnConfigManager:
    """Handles all configuration persistence operations."""

    def __init__(self) -> None:
        self._config_key = "custom_columns"

    def _config_list(self) -> list[dict[str, Any]]:
        cfg = get_config()
        settings = cfg.setting
        # Read the raw value directly; Option may not be registered for this key
        lst = settings.raw_value(self._config_key)
        if isinstance(lst, list):
            return lst
        # If not set or wrong type, treat as empty without mutating config here
        if lst is not None:
            log.debug(
                "Custom columns config '%s' has unexpected type %s; treating as empty",
                self._config_key,
                type(lst).__name__,
            )
        return []

    def load_specs(self) -> list[CustomColumnSpec]:
        raw_list = self._config_list()
        if not isinstance(raw_list, list):  # Defensive: normalize unexpected values
            return []
        specs: list[CustomColumnSpec] = []
        for entry in raw_list:
            try:
                if not isinstance(entry, dict):
                    continue
                # Skip entries missing essential fields
                key_val = entry.get('key')
                expr_val = entry.get('expression')
                if not isinstance(key_val, str) or not key_val.strip():
                    continue
                if not isinstance(expr_val, str) or not expr_val.strip():
                    continue
                specs.append(CustomColumnSpecSerializer.from_dict(entry))
            except (ValueError, KeyError, TypeError):
                continue
        return specs

    def save_specs(self, specs: list[CustomColumnSpec]) -> None:
        cfg = get_config()
        # Use QSettings API to write a JSON-like list under 'setting/<key>'
        data_list = [CustomColumnSpecSerializer.to_dict(spec) for spec in specs]
        cfg.setting[self._config_key] = data_list
        cfg.sync()

    def add_or_update(self, spec: CustomColumnSpec) -> None:
        specs = self.load_specs()
        by_key = {s.key: s for s in specs}
        by_key[spec.key] = spec
        self.save_specs(list(by_key.values()))

    def delete_by_key(self, key: str) -> bool:
        specs = self.load_specs()
        new_specs = [s for s in specs if s.key != key]
        changed = len(new_specs) != len(specs)
        if changed:
            self.save_specs(new_specs)
        return changed

    def get_by_key(self, key: str) -> CustomColumnSpec | None:
        for spec in self.load_specs():
            if spec.key == key:
                return spec
        return None


def load_specs_from_config() -> list[CustomColumnSpec]:
    """Load custom column specs from configuration."""
    return CustomColumnConfigManager().load_specs()


def save_specs_to_config(specs: list[CustomColumnSpec]) -> None:
    """Save the provided specs list to configuration."""
    CustomColumnConfigManager().save_specs(specs)


def add_or_update_spec(spec: CustomColumnSpec) -> None:
    """Add a new spec or update an existing one by key, then persist."""
    CustomColumnConfigManager().add_or_update(spec)


def delete_spec_by_key(key: str) -> bool:
    """Delete a spec by key and persist changes."""
    return CustomColumnConfigManager().delete_by_key(key)


def get_spec_by_key(key: str) -> CustomColumnSpec | None:
    """Return the stored spec for a given key, if any."""
    return CustomColumnConfigManager().get_by_key(key)


class CustomColumnRegistrar:
    """Handles UI column registration and management."""

    def register_column(self, spec: CustomColumnSpec) -> None:
        column = build_column_from_spec(spec)
        registry.register(
            column,
            add_to_file_view=spec.add_to_file_view,
            add_to_album_view=spec.add_to_album_view,
            insert_after_key=spec.insert_after_key,
        )

    def unregister_column(self, key: str) -> None:
        registry.unregister(key)


class CustomColumnManager:
    """High-level interface for custom column operations."""

    def __init__(self) -> None:
        self.config_manager = CustomColumnConfigManager()
        self.registrar = CustomColumnRegistrar()

    def add_column(self, spec: CustomColumnSpec) -> None:
        self.config_manager.add_or_update(spec)
        self.registrar.register_column(spec)

    def remove_column(self, key: str) -> bool:
        self.registrar.unregister_column(key)
        return self.config_manager.delete_by_key(key)


_loaded_once: bool = False


def load_persisted_columns_once() -> None:
    """Load stored specs and register corresponding columns exactly once.

    Notes
    -----
    This function is idempotent and safe to call multiple times. Only the
    first invocation performs registration.
    """

    global _loaded_once
    if _loaded_once:
        return
    for spec in load_specs_from_config():
        try:
            CustomColumnRegistrar().register_column(spec)
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
    _loaded_once = True


def register_and_persist(spec: CustomColumnSpec) -> None:
    """Persist a spec and register the corresponding UI column."""
    CustomColumnManager().add_column(spec)


def unregister_and_delete(key: str) -> None:
    """Unregister a column and delete its spec from persistence."""
    CustomColumnManager().remove_column(key)
