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

from PyQt6 import (
    QtWidgets,
    sip,
)

from picard.ui.scripteditor.utils import synchronize_vertical_scrollbars
from picard.ui.theme import theme


def _make_widgets():
    return [QtWidgets.QListWidget(), QtWidgets.QListWidget()]


def test_theme_change_after_widgets_deleted_does_not_crash(qapp):
    # Regression test for PICARD-3509: synchronize_vertical_scrollbars connects a
    # highlight-stylesheet slot to the long-lived theme.theme_changed signal.
    # When the widgets are destroyed (e.g. the script editor dialog closes) and
    # the user later switches themes, the slot was invoked on deleted C++ objects
    # and crashed with "wrapped C/C++ object of type QListWidget has been
    # deleted".
    widgets = _make_widgets()
    synchronize_vertical_scrollbars(widgets)

    # Simulate the owning dialog being destroyed.
    for w in widgets:
        sip.delete(w)

    # A later theme switch must not raise.
    theme.theme_changed.emit()


def test_connection_is_removed_when_widgets_destroyed(qapp):
    # The stale connection must not accumulate across dialog open/close.
    before = theme.receivers(theme.theme_changed)
    widgets = _make_widgets()
    synchronize_vertical_scrollbars(widgets)
    assert theme.receivers(theme.theme_changed) == before + 1

    for w in widgets:
        sip.delete(w)
    # Destroying the widgets fires destroyed, which disconnects the slot.
    assert theme.receivers(theme.theme_changed) == before


def test_highlight_stylesheet_applied_to_live_widgets(qapp):
    # Sanity: with live widgets a theme change still applies a stylesheet.
    widgets = _make_widgets()
    synchronize_vertical_scrollbars(widgets)
    theme.theme_changed.emit()
    for w in widgets:
        assert 'QListView::item:selected' in w.styleSheet()
