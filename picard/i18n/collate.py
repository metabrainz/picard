# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024, 2026 Philipp Wolfer
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


from collections.abc import Callable
import locale
import os
import re
from typing import Protocol

from PyQt6.QtCore import (
    QCollator,
    QCollatorSortKey,
)

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)


_qcollator = QCollator()
_qcollator_numeric = QCollator()
_qcollator_numeric.setNumericMode(True)


class _QtSortKey:
    """Comparable wrapper around :class:`QCollatorSortKey`.

    ``QCollatorSortKey`` only provides ``compare()`` and, via PyQt, a ``<``
    operator; it does **not** implement a meaningful ``==``. That makes it
    unsafe to use as a non-final element of a composite (tuple) sort key:
    Python tuple comparison tests ``==`` on each element to decide whether to
    advance to the next one, and two keys built from equal strings compare as
    "not equal" (identity fallback), so later tie-break elements are never
    considered. Defining ``__eq__``/``__lt__`` in terms of ``compare()``
    restores correct, backend-independent tuple ordering.

    The comparison methods are deliberately kept minimal: they sit on the hot
    path of every Qt-collated sort, including the main item view. ``__lt__``
    (by far the most-called during sorting) skips the ``isinstance`` guard
    since it is only ever called with another ``_QtSortKey``; ``__eq__`` keeps
    the guard so equality against unrelated objects stays well-defined.
    ``>``/``>=``/``<=`` work through Python's reflected-operator fallback onto
    ``__lt__``/``__eq__``.
    """

    __slots__ = ("_key",)

    def __init__(self, key: QCollatorSortKey):
        self._key = key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _QtSortKey):
            return NotImplemented
        return self._key.compare(other._key) == 0

    def __lt__(self, other: "_QtSortKey") -> bool:
        return self._key.compare(other._key) < 0

    def __hash__(self) -> int:  # pragma: no cover - not used for sorting
        # Sort keys are not hashable in a content-meaningful way; fall back to
        # identity. Provided only so the type is not unhashable.
        return id(self)


def setup_collator(logger: Callable):
    global _qcollator, _qcollator_numeric

    logger("Collator: %s", ACTIVE_COLLATOR)
    if ACTIVE_COLLATOR == 'qt':
        _qcollator = QCollator()
        _qcollator_numeric = QCollator()
        _qcollator_numeric.setNumericMode(True)


class Comparable(Protocol):
    """Protocol for annotating comparable types."""

    def __lt__(self, other, /) -> bool: ...


RE_NUMBER = re.compile(r'(\d+)')


def _digits_replace(matchobj):
    s = matchobj.group(0)
    return str(int(s)) if s.isdecimal() else s


def _sort_key_qt(string: str, numeric: bool = False) -> Comparable:
    """Transforms a string to one that can be used in locale-aware comparisons.

    Args:
        string: The string to convert
        numeric: Boolean indicating whether to use number aware sorting (natural sorting)

    Returns: An object that can be compared locale-aware
    """
    collator = _qcollator_numeric if numeric else _qcollator

    # Null bytes can cause crashes in OS collation functions.
    string = string.replace('\0', '')

    # On macOS / Windows the numeric sorting does not work reliable with non-latin
    # scripts. Replace numbers in the sort string with their latin equivalent.
    if numeric and (IS_MACOS or IS_WIN):
        string = RE_NUMBER.sub(_digits_replace, string)

    if IS_MACOS:
        # macOS does not sort the empty string before other values correctly
        if not string:
            string = ' '
        # On macOS numeric sorting of strings entirely consisting of numeric
        # characters fails and always sorts alphabetically (002 < 1). Always
        # prefix with an alphabetic character to work around that.
        string = 'a' + string

    return _QtSortKey(collator.sortKey(string))


def _sort_key_strxfrm(string: str, numeric: bool = False) -> Comparable:
    """Transforms a string to one that can be used in locale-aware comparisons.

    Args:
        string: The string to convert
        numeric: Boolean indicating whether to use number aware sorting (natural sorting)

    Returns: An object that can be compared locale-aware
    """
    if numeric:
        return [int(s) if s.isdecimal() else _strxfrm(s) for s in RE_NUMBER.split(str(string).replace('\0', ''))]
    else:
        return _strxfrm(string)


def _strxfrm(string: str) -> str:
    try:
        return locale.strxfrm(string)
    except (OSError, ValueError):
        return string.lower()


def _sort_key_string(string: str, numeric: bool = False) -> Comparable:
    return string


AVAILABLE_COLLATORS = {
    'strxfrm': _sort_key_strxfrm,
    'qt': _sort_key_qt,
    'string': _sort_key_string,
}

# QCollator.sortKey is broken on Windows in some Qt builds,
# see https://qt-project.atlassian.net/browse/QTBUG-88704
DEFAULT_COLLATOR = 'strxfrm' if IS_WIN else 'qt'
ACTIVE_COLLATOR = os.environ.get('PICARD_COLLATOR', DEFAULT_COLLATOR)
if ACTIVE_COLLATOR not in AVAILABLE_COLLATORS:
    ACTIVE_COLLATOR = DEFAULT_COLLATOR

sort_key = AVAILABLE_COLLATORS[ACTIVE_COLLATOR]
