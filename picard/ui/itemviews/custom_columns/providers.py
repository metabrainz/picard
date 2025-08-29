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

"""Provider implementations for field lookup, transforms and callables."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from picard import log
from picard.item import Item

from picard.ui.itemviews.custom_columns.protocols import ColumnValueProvider


@dataclass(frozen=True)
class FieldReferenceProvider:
    key: str

    def evaluate(self, obj: Item) -> str:
        try:
            return obj.column(self.key)  # type: ignore[attr-defined]
        except (AttributeError, KeyError, TypeError) as e:
            log.debug("%s failure for key %r: %r", self.__class__.__name__, self.key, e)
            return ""

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"FieldReferenceProvider(key={self.key!r})"


class TransformProvider:
    def __init__(self, base: ColumnValueProvider, transform: Callable[[str], str]):
        self._base = base
        self._transform = transform

    def evaluate(self, obj: Item) -> str:
        try:
            return self._transform(self._base.evaluate(obj) or "")
        except (TypeError, ValueError) as e:
            log.debug(
                "%s failure using %r: %r",
                self.__class__.__name__,
                getattr(self._transform, "__name__", self._transform),
                e,
            )
            return ""

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        transform_name = getattr(self._transform, "__name__", repr(self._transform))
        return f"TransformProvider(base={self._base!r}, transform={transform_name})"


class CallableProvider:
    def __init__(self, func: Callable[[Item], str]):
        self._func = func

    def evaluate(self, obj: Item) -> str:
        try:
            return str(self._func(obj))
        except (TypeError, ValueError, AttributeError) as e:
            log.debug("%s failure for %r: %r", self.__class__.__name__, getattr(self._func, "__name__", self._func), e)
            return ""

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        func_name = getattr(self._func, "__name__", repr(self._func))
        return f"CallableProvider(func={func_name})"
