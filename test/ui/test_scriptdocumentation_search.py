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

from unittest.mock import MagicMock

from PyQt6 import (
    QtCore,
    QtGui,
)

import pytest

from picard.ui.widgets import scriptdocumentation
from picard.ui.widgets.scriptdocumentation import (
    ScriptingDocumentationWidget,
    SearchLineEdit,
)


@pytest.fixture
def widget(qapp, monkeypatch):
    # Avoid building the (heavy) real documentation pages; the search
    # navigation logic under test does not depend on their content.
    monkeypatch.setattr(
        scriptdocumentation.FunctionsDocumentationPage,
        'generate_html',
        lambda self: '',
    )
    monkeypatch.setattr(
        scriptdocumentation.TagsDocumentationPage,
        'generate_html',
        lambda self: '',
    )
    return ScriptingDocumentationWidget(include_link=False)


def _press(line_edit, key, shift=False):
    """Deliver a key press directly to the line edit's handler."""
    modifiers = QtCore.Qt.KeyboardModifier.ShiftModifier if shift else QtCore.Qt.KeyboardModifier.NoModifier
    event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, key, modifiers)
    line_edit.keyPressEvent(event)
    return event


# --- SearchLineEdit: Enter/Shift+Enter emit navigation signals -------------


def test_enter_emits_find_next_signal(qapp):
    # Regression test for PICARD-3507: Enter in the search field must emit a
    # "find next" request instead of doing nothing. Using keyPressEvent (not an
    # event filter) guarantees it also works inside a QDialog such as the
    # file naming script editor.
    line_edit = SearchLineEdit()
    next_cb = MagicMock()
    prev_cb = MagicMock()
    line_edit.find_next_requested.connect(next_cb)
    line_edit.find_prev_requested.connect(prev_cb)

    event = _press(line_edit, QtCore.Qt.Key.Key_Return)

    next_cb.assert_called_once()
    prev_cb.assert_not_called()
    assert event.isAccepted()


def test_keypad_enter_emits_find_next_signal(qapp):
    line_edit = SearchLineEdit()
    next_cb = MagicMock()
    line_edit.find_next_requested.connect(next_cb)

    _press(line_edit, QtCore.Qt.Key.Key_Enter)

    next_cb.assert_called_once()


def test_shift_enter_emits_find_prev_signal(qapp):
    line_edit = SearchLineEdit()
    next_cb = MagicMock()
    prev_cb = MagicMock()
    line_edit.find_next_requested.connect(next_cb)
    line_edit.find_prev_requested.connect(prev_cb)

    event = _press(line_edit, QtCore.Qt.Key.Key_Return, shift=True)

    prev_cb.assert_called_once()
    next_cb.assert_not_called()
    assert event.isAccepted()


def test_other_keys_do_not_emit_signals(qapp):
    line_edit = SearchLineEdit()
    next_cb = MagicMock()
    prev_cb = MagicMock()
    line_edit.find_next_requested.connect(next_cb)
    line_edit.find_prev_requested.connect(prev_cb)

    _press(line_edit, QtCore.Qt.Key.Key_A)

    next_cb.assert_not_called()
    prev_cb.assert_not_called()


# --- Widget: signals are wired to bounds-respecting navigation -------------


def test_enter_advances_to_next_match(widget):
    widget._find_next = MagicMock()
    widget._find_prev = MagicMock()
    widget.found_item = 1
    widget.found_items = 3

    widget.searchText.find_next_requested.emit()

    widget._find_next.assert_called_once()
    widget._find_prev.assert_not_called()


def test_shift_enter_goes_to_previous_match(widget):
    widget._find_next = MagicMock()
    widget._find_prev = MagicMock()
    widget.found_item = 2
    widget.found_items = 3

    widget.searchText.find_prev_requested.emit()

    widget._find_prev.assert_called_once()
    widget._find_next.assert_not_called()


def test_enter_at_last_match_is_noop(widget):
    widget._find_next = MagicMock()
    widget._find_prev = MagicMock()
    widget.found_item = 3
    widget.found_items = 3

    widget.searchText.find_next_requested.emit()

    widget._find_next.assert_not_called()


def test_shift_enter_at_first_match_is_noop(widget):
    widget._find_next = MagicMock()
    widget._find_prev = MagicMock()
    widget.found_item = 1
    widget.found_items = 3

    widget.searchText.find_prev_requested.emit()

    widget._find_prev.assert_not_called()


def test_enter_in_widget_search_field_navigates_end_to_end(widget):
    # Pressing Enter on the actual search line edit should drive navigation
    # through the connected signal, confirming the wiring is intact.
    widget._find_next = MagicMock()
    widget.found_item = 1
    widget.found_items = 3

    _press(widget.searchText, QtCore.Qt.Key.Key_Return)

    widget._find_next.assert_called_once()
