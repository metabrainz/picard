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

- **state**  : a semantic ``IntEnum`` member (``MultiColumnState`` subclass) —
  the single source of truth.  Everything else is derived from it.
- **display**: a human-readable, translatable label, derived from the state
  via ``state.display()``.
- **sort**   : a stable, language-independent integer, derived from the state
  via ``int(state)``.

A future renderer (e.g. icons or a read-only checkbox) only needs the *state*;
it can call ``MultiStateAlbumColumnProvider.state()`` and map the enum as
needed, without depending on the displayed text or the numeric sort key.

The module has no Qt dependency, so it stays usable without a running
``QApplication`` (and therefore unit-testable in isolation).
"""

from collections.abc import Callable
from enum import IntEnum

from picard.item import Item

from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    SortKeyProvider,
)


class MultiColumnState(IntEnum):
    """Abstract ``IntEnum`` base for multi-state column values.

    Subclasses define the concrete members (including a ``NOT_APPLICABLE``
    sentinel) and override :meth:`display` to return a translated label.

    The integer values define the sort order (ascending): rows that are not
    applicable (e.g. non-album rows) should sort before every meaningful
    state.  Values are intentionally stable and independent of any displayed,
    translatable text.
    """

    def display(self) -> str:
        """Return the translated label for display in a cell.

        The default implementation returns an empty string, which is
        appropriate for the ``NOT_APPLICABLE`` sentinel and for columns
        that render an icon instead of text.

        Subclasses should override this method to provide translated
        labels for their meaningful states.
        """
        return ""


class MultiStateAlbumColumnProvider(ColumnValueProvider, SortKeyProvider):
    """Provide state, display and sort for an album-level multi-state predicate.

    The provider exposes the semantic ``state()`` so alternative renderers
    (icons, a tri-state checkbox, etc.) can be added later by reading the
    enum value directly, without depending on the displayed text or the
    numeric sort key.

    Parameters
    ----------
    predicate
        Callable that receives an album-like item and returns a concrete
        ``MultiColumnState`` enum member.  It is only invoked for items
        for which *applies* returns ``True``.
    applies
        Callable deciding whether *predicate* is meaningful for the item.
        Items that do not apply resolve to *not_applicable* (empty display,
        sorted apart).
    not_applicable
        The ``NOT_APPLICABLE`` enum member of the concrete state class.
        Returned for items where *applies* is ``False``.
    """

    def __init__(
        self,
        predicate: Callable[[Item], MultiColumnState],
        applies: Callable[[Item], bool],
        not_applicable: MultiColumnState,
    ):
        self._predicate = predicate
        self._applies = applies
        self._not_applicable = not_applicable

    def state(self, obj: Item) -> MultiColumnState:
        """Return the semantic state for the item.

        This is the single source of truth; ``evaluate`` and ``sort_key``
        (and any future icon/checkbox renderer) derive their result from it.
        """
        if not self._applies(obj):
            return self._not_applicable
        return self._predicate(obj)

    def evaluate(self, obj: Item) -> str:
        """Return the translated display label for the item."""
        return self.state(obj).display()

    def sort_key(self, obj: Item) -> int:
        """Return a stable, language-independent integer sort key."""
        return int(self.state(obj))
