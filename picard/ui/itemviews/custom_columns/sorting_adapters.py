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

"""Sorting adapters that add `sort_key` support to value providers."""

from __future__ import annotations

from collections.abc import Callable

from picard.i18n import sort_key
from picard.item import Item

from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    SortKeyProvider,
)


def _clean_invisible_and_whitespace(value: str | None) -> str:
    """Remove invisible characters and trim whitespace for emptiness tests.

    Treat the following as invisible: ZERO WIDTH SPACE (\u200b), BYTE ORDER MARK
    (\ufeff), WORD JOINER (\u2060), and NO-BREAK SPACE (\xa0). Also trim
    standard whitespace with ``strip()``.
    """
    if not value:
        return ""
    cleaned: str = (
        value.replace("\u200b", "")  # ZERO WIDTH SPACE
        .replace("\ufeff", "")  # BYTE ORDER MARK (BOM)
        .replace("\u2060", "")  # WORD JOINER
        .replace("\xa0", "")  # NO-BREAK SPACE
        .strip()  # Standard whitespace
    )
    return cleaned


class _AdapterBase(SortKeyProvider):
    """Base adapter that delegates evaluation to a wrapped provider."""

    def __init__(self, base: ColumnValueProvider):
        self._base = base

    def evaluate(self, obj: Item) -> str:
        """Return evaluated text value for item."""
        return self._base.evaluate(obj)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.__class__.__name__}(base={self._base!r})"


class CasefoldSortAdapter(_AdapterBase):
    """Provide case-insensitive sort using `str.casefold()` on evaluated value."""

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return case-insensitive sort key for item."""
        return (self._base.evaluate(obj) or "").casefold()


class DescendingCasefoldSortAdapter(_AdapterBase):
    """Provide descending case-insensitive sort by inverting code points."""

    @staticmethod
    def _invert_string(s: str) -> str:
        # Map code points to inverted order to simulate descending in ascending sort
        # Use BMP range for practicality; characters outside will still order consistently
        return "".join(chr(0x10FFFF - ord(c)) for c in s)

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return descending case-insensitive sort key for item."""
        v = (self._base.evaluate(obj) or "").casefold()
        return self._invert_string(v)


class NumericSortAdapter(_AdapterBase):
    """Provide numeric sort using a parser (default: float) on evaluated value."""

    def __init__(self, base: ColumnValueProvider, parser: Callable[[str], float] | None = None):
        super().__init__(base)
        self._parser = parser or (lambda s: float(s))

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        parser_name = getattr(self._parser, "__name__", repr(self._parser))
        return f"{self.__class__.__name__}(base={self._base!r}, parser={parser_name})"

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return numeric sort key for item."""
        try:
            return self._parser(self._base.evaluate(obj) or "0")
        except (ValueError, TypeError):
            return 0


class DescendingNumericSortAdapter(NumericSortAdapter):
    """Provide descending numeric sort by negating parsed value."""

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return descending numeric sort key for item."""
        try:
            value = self._base.evaluate(obj) or "0"
            parsed = self._parser(value)
            return -parsed
        except (ValueError, TypeError):
            return 0


class LengthSortAdapter(_AdapterBase):
    """Provide sort by string length of evaluated value."""

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return length-based sort key for item."""
        return len(self._base.evaluate(obj) or "")


class ArticleInsensitiveAdapter(_AdapterBase):
    """Provide article-insensitive sort by ignoring leading 'a', 'an', 'the'."""

    def __init__(self, base: ColumnValueProvider, articles: tuple[str, ...] = ("a", "an", "the")):
        """Initialize adapter.

        Parameters
        ----------
        base
            Base provider to evaluate.
        articles
            Tuple of leading articles to ignore (lowercased, no punctuation).
        """
        super().__init__(base)
        self._articles = articles

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.__class__.__name__}(base={self._base!r}, articles={self._articles!r})"

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return article-insensitive sort key for item.

        Returns a tuple (tail, original_lower) so items compare by the tail
        (without article) and tie-break by the original lowercased value.
        """
        v = (self._base.evaluate(obj) or "").strip()
        lv = v.casefold()
        for art in self._articles:
            prefix = f"{art} "
            if lv.startswith(prefix):
                return (lv[len(prefix) :], lv)
        return (lv, lv)


class CompositeSortAdapter(_AdapterBase):
    """Provide composite sort using multiple key functions on item.

    Each key function takes the item and returns a comparable value.
    """

    def __init__(self, base: ColumnValueProvider, key_funcs: list[Callable[[Item], object]]):
        """Initialize adapter.

        Parameters
        ----------
        base
            Base provider to evaluate (unused for key extraction but preserved for evaluation).
        key_funcs
            List of callables to compute primary, secondary, ... keys.
        """
        super().__init__(base)
        self._key_funcs = key_funcs

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        funcs = [getattr(f, "__name__", repr(f)) for f in self._key_funcs]
        return f"{self.__class__.__name__}(base={self._base!r}, key_funcs={funcs})"

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return composite tuple sort key for item."""
        return tuple(func(obj) for func in self._key_funcs)


class NullsLastAdapter(_AdapterBase):
    """Provide sort with empty values ordered last."""

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return sort key that pushes empty values to the end."""
        v = self._base.evaluate(obj)
        cleaned = _clean_invisible_and_whitespace(v)
        is_empty = cleaned == ""
        key = cleaned.casefold()
        return (is_empty, key)


class NullsFirstAdapter(_AdapterBase):
    """Provide sort with empty values ordered first."""

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return sort key that pulls empty values to the front."""
        v = self._base.evaluate(obj)
        cleaned = _clean_invisible_and_whitespace(v)
        is_empty = cleaned == ""
        key = cleaned.casefold()
        return (not is_empty, key)


class CachedSortAdapter(_AdapterBase):
    """Provide cached sort keys for an underlying provider (value or sort_key)."""

    def __init__(
        self, base: ColumnValueProvider, key_func: Callable[[Item, ColumnValueProvider], object] | None = None
    ):
        """Initialize adapter.

        Parameters
        ----------
        base
            Base provider to evaluate.
        key_func
            Optional function to compute sort key from (item, provider). If omitted,
            use provider.sort_key if available, otherwise use casefolded evaluate.
        """
        super().__init__(base)
        from weakref import WeakKeyDictionary

        self._cache: WeakKeyDictionary[Item, object] = WeakKeyDictionary()
        self._key_func = key_func

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return cached sort key for item."""
        try:
            return self._cache[obj]
        except (KeyError, TypeError):
            pass

        if self._key_func is not None:
            key = self._key_func(obj, self._base)
        elif isinstance(self._base, SortKeyProvider):
            key = self._base.sort_key(obj)
        else:
            key = (self._base.evaluate(obj) or "").casefold()

        try:
            self._cache[obj] = key
        except TypeError:
            # Cannot weakref obj; skip caching
            pass
        return key


class ReverseAdapter(_AdapterBase):
    """Provide reversed sorting for string or numeric sort keys."""

    @staticmethod
    def _invert_string(s: str) -> str:
        return "".join(chr(0x10FFFF - ord(c)) for c in s)

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return reversed sort key for item."""
        key: object
        if isinstance(self._base, SortKeyProvider):
            key = self._base.sort_key(obj)
        else:
            key = self._base.evaluate(obj) or ""

        if isinstance(key, (int, float)):
            return -key
        if isinstance(key, str):
            return self._invert_string(key)
        return key


class NaturalSortAdapter(_AdapterBase):
    """Provide natural (alphanumeric) sort using locale-aware natural ordering."""

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return natural sort key for item.

        Uses natural sorting to handle mixed text/numbers intelligently.
        For example: "Track 1", "Track 2", "Track 10" instead of "Track 1", "Track 10", "Track 2".
        """
        return sort_key(self._base.evaluate(obj) or "", numeric=True)


class DescendingNaturalSortAdapter(_AdapterBase):
    """Provide descending natural (alphanumeric) sort using string inversion."""

    @staticmethod
    def _invert_string(s: str) -> str:
        """Invert string for descending order (same as ReverseAdapter)."""
        return "".join(chr(0x10FFFF - ord(c)) for c in s)

    def sort_key(self, obj: Item):  # pragma: no cover - thin wrapper
        """Return descending natural sort key for item.

        Gets the natural sort key, converts to string, then inverts character order.
        """

        # Get the natural sort key and convert to string
        natural_key = sort_key(self._base.evaluate(obj) or "", numeric=True)
        key_str = str(natural_key)

        # Apply string inversion for proper descending order
        return self._invert_string(key_str)
