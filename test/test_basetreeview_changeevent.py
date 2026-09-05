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


from unittest.mock import (
    Mock,
    patch,
)

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.ui.itemviews.basetreeview import BaseTreeView


def _make_event(event_type):
    event = Mock()
    event.type = Mock(return_value=event_type)
    return event


def _run_change_event(qapp, event_type):
    """Invoke BaseTreeView.changeEvent with a crafted event, no real widget.

    A real BaseTreeView needs columns/window/tagger; we only exercise the
    changeEvent override, so build a bare instance, mock the viewport and stub
    the base-class handler (calling it on a non-initialised C++ object would
    crash).
    """
    view = BaseTreeView.__new__(BaseTreeView)
    viewport = Mock()
    view.viewport = Mock(return_value=viewport)

    with patch.object(QtWidgets.QTreeWidget, 'changeEvent', Mock()):
        view.changeEvent(_make_event(event_type))
    return viewport


def test_enabled_change_repaints_viewport(qapp):
    """Re-enabling the window (options dialog closing) repaints automatic rows.

    Regression test: automatic (palette-driven) item colors follow the widget's
    palette color group at paint time. When the window is disabled while the
    options dialog is open and enabled again on "Make It So", the greyed
    disabled color could linger because Qt did not repaint the viewport. The
    changeEvent override now forces a repaint.
    """
    viewport = _run_change_event(qapp, QtCore.QEvent.Type.EnabledChange)
    viewport.update.assert_called_once_with()


def test_activation_change_repaints_viewport(qapp):
    """Window (de)activation must repaint so automatic rows follow the group."""
    viewport = _run_change_event(qapp, QtCore.QEvent.Type.ActivationChange)
    viewport.update.assert_called_once_with()


def test_palette_change_repaints_viewport(qapp):
    """A palette change must repaint so automatic rows pick up the new colors."""
    viewport = _run_change_event(qapp, QtCore.QEvent.Type.PaletteChange)
    viewport.update.assert_called_once_with()


def test_unrelated_change_does_not_repaint(qapp):
    """Unrelated change events must not trigger an extra repaint."""
    viewport = _run_change_event(qapp, QtCore.QEvent.Type.FontChange)
    viewport.update.assert_not_called()
