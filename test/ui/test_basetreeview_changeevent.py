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


def _run_change_event(qapp, event_type, with_panel=True):
    """Invoke BaseTreeView.changeEvent with a crafted event, no real widget.

    A real BaseTreeView needs columns/window/tagger; we only exercise the
    changeEvent override, so build a bare instance, mock the viewport/window
    and stub the base-class handler (calling it on a non-initialised C++ object
    would crash).

    Returns (viewport, panel) so tests can assert which path ran. When
    ``with_panel`` is False, ``window.panel`` is missing to exercise the
    early-init fallback.
    """
    view = BaseTreeView.__new__(BaseTreeView)
    viewport = Mock()
    view.viewport = Mock(return_value=viewport)

    if with_panel:
        panel = Mock()
        view.window = Mock(panel=panel)
    else:
        panel = None
        view.window = Mock(spec=[])  # no 'panel' attribute

    with patch.object(QtWidgets.QTreeWidget, 'changeEvent', Mock()):
        view.changeEvent(_make_event(event_type))
    return viewport, panel


def test_enabled_change_recomputes_colors(qapp):
    """Re-enabling the window (options dialog closing) re-tints and repaints.

    Regression test for the "great match" banding: baked match-similarity tints
    are frozen against the palette group current when they were computed, so a
    plain repaint is not enough — they must be recomputed against the new group
    or they band against the automatic (perfect-match / normal-text) cells that
    do follow the group. The changeEvent override now re-runs the panel colour
    refresh, which recomputes base_color for the current group, re-applies every
    item's tint and repaints.
    """
    viewport, panel = _run_change_event(qapp, QtCore.QEvent.Type.EnabledChange)
    panel._refresh_colors.assert_called_once_with()
    # The refresh handles repainting; changeEvent must not repaint separately.
    viewport.update.assert_not_called()


def test_activation_change_recomputes_colors(qapp):
    """Window (de)activation must re-tint so all cells follow the new group."""
    viewport, panel = _run_change_event(qapp, QtCore.QEvent.Type.ActivationChange)
    panel._refresh_colors.assert_called_once_with()


def test_palette_change_recomputes_colors(qapp):
    """A palette change must re-tint so all cells pick up the new colors."""
    viewport, panel = _run_change_event(qapp, QtCore.QEvent.Type.PaletteChange)
    panel._refresh_colors.assert_called_once_with()


def test_change_before_panel_ready_falls_back_to_repaint(qapp):
    """During early init the panel may be missing; fall back to a plain repaint."""
    viewport, _ = _run_change_event(qapp, QtCore.QEvent.Type.EnabledChange, with_panel=False)
    viewport.update.assert_called_once_with()


def test_unrelated_change_does_not_recompute(qapp):
    """Unrelated change events must not trigger a colour refresh or repaint."""
    viewport, panel = _run_change_event(qapp, QtCore.QEvent.Type.FontChange)
    panel._refresh_colors.assert_not_called()
    viewport.update.assert_not_called()
