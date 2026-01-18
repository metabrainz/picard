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

from collections.abc import (
    Callable,
    Iterable,
)
from typing import Any

import pytest

from picard.ui.widgets.scripttextedit import ScriptTextEdit


class _FakeSignal:
    def __init__(self) -> None:
        self._slots: list[Callable[..., None]] = []

    def connect(self, slot: Callable[..., None]) -> None:
        self._slots.append(slot)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for slot in list(self._slots):
            slot(*args, **kwargs)


class _FakeIndex:
    def __init__(self, row: int, col: int, model: "_FakeModel") -> None:
        self._row = row
        self._col = col
        self._model = model

    def isValid(self) -> bool:  # noqa: N802 (Qt-style API)
        return 0 <= self._row < self._model.rowCount()

    def row(self) -> int:
        return self._row


class _FakeModel:
    def __init__(self, items: Iterable[str]) -> None:
        self._items: list[str] = list(items)
        # Qt-like signals
        self.modelReset = _FakeSignal()
        self.layoutChanged = _FakeSignal()
        self.rowsInserted = _FakeSignal()
        self.rowsRemoved = _FakeSignal()
        self.dataChanged = _FakeSignal()

    # Minimal QStringListModel-like surface
    def rowCount(self) -> int:  # noqa: N802 (Qt-style API)
        return len(self._items)

    def index(self, row: int, col: int) -> _FakeIndex:
        return _FakeIndex(row, col, self)

    def data(self, index: _FakeIndex, role: Any = None) -> str | None:  # noqa: ANN001
        if 0 <= index._row < len(self._items):
            return self._items[index._row]
        return None

    # Helpers to simulate mutations and emit corresponding signals
    def set_items(self, items: Iterable[str]) -> None:
        self._items = list(items)
        self.modelReset.emit()

    def insert_rows(self, rows: Iterable[str]) -> None:
        start_len = len(self._items)
        self._items.extend(rows)
        # indexes: start, end
        self.rowsInserted.emit(None, start_len, len(self._items) - 1)

    def remove_last_row(self) -> None:
        if self._items:
            self._items.pop()
            last = max(0, len(self._items) - 1)
            self.rowsRemoved.emit(None, last, last)

    def change_first(self, value: str) -> None:
        if not self._items:
            return
        self._items[0] = value
        # topLeft, bottomRight indexes
        self.dataChanged.emit(self.index(0, 0), self.index(0, 0))


class _FakePopup:
    def __init__(self) -> None:
        self._current: _FakeIndex | None = None

    def currentIndex(self) -> _FakeIndex:  # noqa: N802
        return self._current or _FakeIndex(-1, 0, _FakeModel([]))

    def setCurrentIndex(self, index: _FakeIndex) -> None:  # noqa: N802
        self._current = index


class _FakeCompleter:
    def __init__(self, model: _FakeModel) -> None:
        self._model = model
        self._popup = _FakePopup()
        self._current_row: int = -1
        self._prefix: str = ""
        self._last_selected: str = ""

    # Surface used by ScriptTextEdit
    def completionModel(self) -> _FakeModel:  # noqa: N802
        return self._model

    def popup(self) -> _FakePopup:
        return self._popup

    def setCurrentRow(self, row: int) -> None:  # noqa: N802
        self._current_row = row
        self._popup.setCurrentIndex(self._model.index(row, 0))

    def setCompletionPrefix(self, prefix: str) -> None:  # noqa: N802
        self._prefix = prefix

    def completionPrefix(self) -> str:  # noqa: N802
        return self._prefix

    def complete(self, *_: Any, **__: Any) -> None:
        # No-op in fake; ScriptTextEdit defers selection via QTimer
        pass

    def get_selected(self) -> str:
        return self._last_selected

    def set_highlighted(self, text: str) -> None:
        self._last_selected = text


@pytest.fixture()
def patch_qtimer_single_shot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run QTimer.singleShot callbacks immediately for deterministic tests."""
    import picard.ui.widgets.scripttextedit as ste

    def _immediate(ms: int, func: Callable[[], None]) -> None:  # noqa: ARG001
        func()

    monkeypatch.setattr(ste.QtCore.QTimer, "singleShot", _immediate, raising=True)


@pytest.fixture()
def fake_edit(monkeypatch: pytest.MonkeyPatch) -> Callable[[Iterable[str]], ScriptTextEdit]:
    """Factory creating a ScriptTextEdit instance with a mocked completer.

    The instance bypasses the real Qt-heavy constructor by allocating via
    ``__new__`` and wiring only the attributes needed by the methods under test.
    """

    def _factory(items: Iterable[str]) -> ScriptTextEdit:
        # Bypass __init__ to avoid creating real Qt widgets
        edit = ScriptTextEdit.__new__(ScriptTextEdit)  # type: ignore[call-arg]
        model = _FakeModel(items)
        edit.completer = _FakeCompleter(model)  # type: ignore[attr-defined]
        edit._completer_model_signals_connected = False  # type: ignore[attr-defined]
        return edit  # type: ignore[return-value]

    return _factory


@pytest.mark.parametrize(
    "choices",
    [
        ["$set", "$noop", "$copy"],
        ["$copy", "$noop", "$set"],
        ["$noop", "$set", "$copy"],
    ],
)
def test_highlight_first_row_on_show(
    patch_qtimer_single_shot: None, fake_edit: Callable[[Iterable[str]], ScriptTextEdit], choices: list[str]
) -> None:
    edit = fake_edit(choices)

    # Connect model signals once
    edit._connect_completer_model_signals()

    # Trigger highlighting logic
    edit._ensure_first_completion_highlighted()

    current = edit.completer.popup().currentIndex()  # type: ignore[attr-defined]
    assert current.isValid()
    assert current.row() == 0
    assert edit.completer.get_selected() == choices[0]  # type: ignore[attr-defined]


def test_selection_persists_after_model_reset(
    patch_qtimer_single_shot: None, fake_edit: Callable[[Iterable[str]], ScriptTextEdit]
) -> None:
    edit = fake_edit(["$set", "$noop"])  # initial items
    edit._connect_completer_model_signals()
    edit._ensure_first_completion_highlighted()

    # Simulate reset with new items
    model: _FakeModel = edit.completer.completionModel()  # type: ignore[assignment]
    model.set_items(["$set", "$noop", "$copy"])

    current = edit.completer.popup().currentIndex()  # type: ignore[attr-defined]
    assert current.isValid()
    assert current.row() == 0
    assert edit.completer.get_selected() == "$set"  # type: ignore[attr-defined]


def test_selection_persists_after_rows_insert_remove(
    patch_qtimer_single_shot: None, fake_edit: Callable[[Iterable[str]], ScriptTextEdit]
) -> None:
    edit = fake_edit(["$set"])  # start minimal
    edit._connect_completer_model_signals()
    edit._ensure_first_completion_highlighted()

    model: _FakeModel = edit.completer.completionModel()  # type: ignore[assignment]
    model.insert_rows(["$noop", "$copy"])
    current = edit.completer.popup().currentIndex()  # type: ignore[attr-defined]
    assert current.isValid() and current.row() == 0
    assert edit.completer.get_selected() == "$set"  # type: ignore[attr-defined]

    model.remove_last_row()
    current = edit.completer.popup().currentIndex()  # type: ignore[attr-defined]
    assert current.isValid() and current.row() == 0
    assert edit.completer.get_selected() == "$set"  # type: ignore[attr-defined]


def test_selection_updates_on_data_changed(
    patch_qtimer_single_shot: None, fake_edit: Callable[[Iterable[str]], ScriptTextEdit]
) -> None:
    edit = fake_edit(["$noop", "$copy"])  # first item is $noop
    edit._connect_completer_model_signals()
    edit._ensure_first_completion_highlighted()

    model: _FakeModel = edit.completer.completionModel()  # type: ignore[assignment]
    model.change_first("$set")

    current = edit.completer.popup().currentIndex()  # type: ignore[attr-defined]
    assert current.isValid() and current.row() == 0
    # last_selected should reflect updated row 0 value
    assert edit.completer.get_selected() == "$set"  # type: ignore[attr-defined]
