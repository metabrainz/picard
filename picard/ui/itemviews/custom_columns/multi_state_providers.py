# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


"""Providers for multi-state album columns with decoupled state, display and sort.

The design keeps three concerns independent so the presentation can change
later without touching sorting or the data source:

- **state**  : the semantic state which supports 2 or more states (`MultiColumnState`) — the single source
  of truth. Everything else is derived from it.
- **display**: a translated ``Yes``/``No`` label, derived from the state.
- **sort**   : a stable, language-independent integer, derived from the state.

A future renderer (e.g. icons or a read-only checkbox) only needs the *state*;
it can call `MultiStateAlbumColumnProvider.state()` and map the enum as needed,
without depending on the displayed text or the numeric sort key. The module has
no Qt dependency, so it stays usable without a running ``QApplication`` (and
therefore unit-testable in isolation).
"""

from collections.abc import Callable

from picard.item import Item

from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    SortKeyProvider,
)


class MultiColumnStateBase:
    """Multi-state used by album columns.

    The integer values define the sort order (ascending):
    The amount of values that are sortable can be chosen by the implementerrows that are not
    applicable (e.g. non-album rows) sort before ``NO`` which sorts before
    ``YES``. Values are intentionally stable and independent of any displayed,
    translatable text.
    """

    NOT_APPLICABLE: int = -1
    _current_value: int

    def __init__(self, value: int = NOT_APPLICABLE):
        self._current_value = value

    def value(
        self,
    ) -> int:
        """Return the current value represented by the cell."""
        return self._current_value

    def display(self) -> str:
        """Return the translated label for display in a cell.

        Plain ``_()`` both marks the msgid for extraction and translates at
        call time, so the label follows the current UI language.
        """
        return ""


class MultiStateAlbumColumnProvider(ColumnValueProvider, SortKeyProvider):
    """Provide state, display and sort for an album-level multi-state predicate.

    The provider exposes the semantic `state` so alternative renderers (icons,
    a tri-state checkbox, etc..) can be added later by reading the value directly,
    without depending on the displayed text or the numeric sort key.

    Parameters
    ----------
    predicate
        Callable returning the multi state of an album-like item. It is only
        invoked for items for which ``applies`` returns ``True``.
    applies
        Callable deciding whether ``predicate`` is meaningful for the item.
        Items that do not apply resolve to ``NOT_APPLICABLE`` (empty display,
        sorted apart).
    """

    def __init__(self, predicate: Callable[[Item], MultiColumnStateBase], applies: Callable[[Item], bool]):
        self._predicate = predicate
        self._applies = applies

    def state(self, obj: Item) -> MultiColumnStateBase:
        """Return the semantic tri-state for the item.

        This is the single source of truth; `evaluate` and `sort_key` (and any
        future icon/checkbox renderer) derive their result from it.
        """
        if not self._applies(obj):
            return MultiColumnStateBase()
        return self._predicate(obj)

    def evaluate(self, obj: Item) -> str:
        """Return the translated display label for the item."""
        return self.state(obj).display()

    def sort_key(self, obj: Item) -> int:
        """Return a stable, language-independent integer sort key."""
        return self.state(obj).value()
