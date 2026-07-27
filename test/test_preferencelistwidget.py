# -*- coding: utf-8 -*-
#
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Tests for PreferenceListWidget.

Note: Widget instantiation tests are skipped on headless CI (no display).
Run locally with a display or QT_QPA_PLATFORM=offscreen for full coverage.
"""

import os
import sys

import pytest


def _has_display():
    """Check if a display server is likely available."""
    if os.environ.get('CI'):
        # CI environments typically don't have a usable display
        return False
    if sys.platform == 'win32':
        return True
    if sys.platform == 'darwin':
        return True
    # Linux: check DISPLAY or WAYLAND_DISPLAY
    return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))


if not _has_display():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


SAMPLE_ITEMS = {
    'US': 'United States',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    'FR': 'France',
    'JP': 'Japan',
}

needs_display = pytest.mark.skipif(
    not _has_display(),
    reason="Qt widget tests require a display (skipped on headless CI)",
)


@pytest.fixture()
def widget():
    from PyQt6 import QtWidgets

    from picard.ui.widgets.preferencelistwidget import PreferenceListWidget

    # Keep reference to prevent garbage collection
    if not hasattr(widget, '_app'):
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
        widget._app = app
    w = PreferenceListWidget()
    w.set_available_items(SAMPLE_ITEMS)
    # prevent GC during test
    widget._current = w
    return w


@needs_display
class TestPreferenceListWidgetInit:
    def test_starts_empty(self, widget):
        assert widget.selected_keys() == []

    def test_combobox_has_all_items_plus_placeholder(self, widget):
        # +1 for the "Add…" placeholder
        assert widget._add_combo.count() == len(SAMPLE_ITEMS) + 1

    def test_combobox_placeholder_has_no_data(self, widget):
        assert widget._add_combo.itemData(0) is None


@needs_display
class TestSetSelectedKeys:
    def test_set_keys(self, widget):
        widget.set_selected_keys(['US', 'GB'])
        assert widget.selected_keys() == ['US', 'GB']

    def test_order_preserved(self, widget):
        widget.set_selected_keys(['JP', 'FR', 'DE'])
        assert widget.selected_keys() == ['JP', 'FR', 'DE']

    def test_unknown_keys_skipped(self, widget):
        widget.set_selected_keys(['US', 'XX', 'GB'])
        assert widget.selected_keys() == ['US', 'GB']

    def test_combobox_excludes_selected(self, widget):
        widget.set_selected_keys(['US', 'GB'])
        combo_keys = [widget._add_combo.itemData(i) for i in range(widget._add_combo.count())]
        assert 'US' not in combo_keys
        assert 'GB' not in combo_keys
        assert 'DE' in combo_keys


@needs_display
class TestAddItem:
    def test_add_from_combo(self, widget):
        widget._add_combo.setCurrentIndex(1)  # first real item (0 is placeholder)
        widget._on_combo_activated(1)
        assert len(widget.selected_keys()) == 1

    def test_add_removes_from_combo(self, widget):
        initial_count = widget._add_combo.count()
        widget._add_combo.setCurrentIndex(1)
        widget._on_combo_activated(1)
        assert widget._add_combo.count() == initial_count - 1

    def test_add_emits_changed(self, widget):
        signals = []
        widget.changed.connect(lambda: signals.append(True))
        widget._add_combo.setCurrentIndex(1)
        widget._on_combo_activated(1)
        assert len(signals) == 1

    def test_add_skips_placeholder(self, widget):
        widget._on_combo_activated(0)  # placeholder
        assert len(widget.selected_keys()) == 0

    def test_add_selects_only_new_item(self, widget):
        widget.set_selected_keys(['US', 'GB'])
        widget._list_widget.setCurrentRow(0)  # select US
        widget._add_combo.setCurrentIndex(1)  # pick something
        widget._on_combo_activated(1)
        selected = widget._list_widget.selectedIndexes()
        # Only the newly added item should be selected
        assert len(selected) == 1
        assert selected[0].row() == widget._list_widget.count() - 1


@needs_display
class TestRemoveItem:
    def test_remove_selected(self, widget):
        widget.set_selected_keys(['US', 'GB', 'DE'])
        widget._list_widget.setCurrentRow(1)
        widget._remove_selected()
        assert widget.selected_keys() == ['US', 'DE']

    def test_remove_restores_to_combo(self, widget):
        widget.set_selected_keys(['US', 'GB'])
        combo_count = widget._add_combo.count()
        widget._list_widget.setCurrentRow(0)
        widget._remove_selected()
        assert widget._add_combo.count() == combo_count + 1

    def test_remove_emits_changed(self, widget):
        widget.set_selected_keys(['US', 'GB'])
        widget._list_widget.setCurrentRow(0)
        signals = []
        widget.changed.connect(lambda: signals.append(True))
        widget._remove_selected()
        assert len(signals) == 1


@needs_display
class TestMoveItems:
    def test_move_up(self, widget):
        widget.set_selected_keys(['US', 'GB', 'DE'])
        widget._list_widget.setCurrentRow(2)
        widget._move_up()
        assert widget.selected_keys() == ['US', 'DE', 'GB']

    def test_move_down(self, widget):
        widget.set_selected_keys(['US', 'GB', 'DE'])
        widget._list_widget.setCurrentRow(0)
        widget._move_down()
        assert widget.selected_keys() == ['GB', 'US', 'DE']

    def test_move_up_at_top_does_nothing(self, widget):
        widget.set_selected_keys(['US', 'GB', 'DE'])
        widget._list_widget.setCurrentRow(0)
        widget._move_up()
        assert widget.selected_keys() == ['US', 'GB', 'DE']

    def test_move_down_at_bottom_does_nothing(self, widget):
        widget.set_selected_keys(['US', 'GB', 'DE'])
        widget._list_widget.setCurrentRow(2)
        widget._move_down()
        assert widget.selected_keys() == ['US', 'GB', 'DE']

    def test_move_emits_changed(self, widget):
        widget.set_selected_keys(['US', 'GB', 'DE'])
        widget._list_widget.setCurrentRow(1)
        signals = []
        widget.changed.connect(lambda: signals.append(True))
        widget._move_up()
        assert len(signals) == 1


@needs_display
class TestExcludedKeys:
    def test_excluded_keys_hidden_from_combo(self, widget):
        widget.set_excluded_keys({'FR', 'JP'})
        combo_keys = [widget._add_combo.itemData(i) for i in range(widget._add_combo.count())]
        assert 'FR' not in combo_keys
        assert 'JP' not in combo_keys
        assert 'US' in combo_keys

    def test_excluded_plus_selected(self, widget):
        widget.set_excluded_keys({'FR'})
        widget.set_selected_keys(['US'])
        combo_keys = [widget._add_combo.itemData(i) for i in range(widget._add_combo.count())]
        assert 'FR' not in combo_keys
        assert 'US' not in combo_keys
        # Remaining: placeholder(None) + DE, GB, JP
        assert len(combo_keys) == 4


@pytest.fixture()
def unordered_widget():
    from PyQt6 import QtWidgets

    from picard.ui.widgets.preferencelistwidget import PreferenceListWidget

    if not hasattr(unordered_widget, '_app'):
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
        unordered_widget._app = app
    w = PreferenceListWidget(ordered=False)
    w.set_available_items(SAMPLE_ITEMS)
    unordered_widget._current = w
    return w


@needs_display
class TestUnorderedMode:
    def test_no_up_down_buttons(self, unordered_widget):
        assert not hasattr(unordered_widget, '_up_btn')
        assert not hasattr(unordered_widget, '_down_btn')

    def test_drag_drop_disabled(self, unordered_widget):
        from PyQt6 import QtWidgets

        assert unordered_widget._list_widget.dragDropMode() == QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop

    def test_set_selected_keys_sorted_alphabetically(self, unordered_widget):
        # JP=Japan, US=United States, DE=Germany — sorted: France, Germany, Japan, UK, US
        unordered_widget.set_selected_keys(['US', 'JP', 'DE'])
        keys = unordered_widget.selected_keys()
        # Germany < Japan < United States (alphabetical by display name)
        assert keys == ['DE', 'JP', 'US']

    def test_add_inserts_in_sorted_position(self, unordered_widget):
        unordered_widget.set_selected_keys(['DE', 'US'])  # Germany, United States
        # Add France — should go before Germany
        # Find France in the combo
        for i in range(unordered_widget._add_combo.count()):
            if unordered_widget._add_combo.itemData(i) == 'FR':
                unordered_widget._on_combo_activated(i)
                break
        keys = unordered_widget.selected_keys()
        assert keys == ['FR', 'DE', 'US']

    def test_add_selects_new_item(self, unordered_widget):
        unordered_widget.set_selected_keys(['DE', 'US'])
        for i in range(unordered_widget._add_combo.count()):
            if unordered_widget._add_combo.itemData(i) == 'FR':
                unordered_widget._on_combo_activated(i)
                break
        selected = unordered_widget._list_widget.selectedIndexes()
        assert len(selected) == 1
        # France should be at row 0 (first alphabetically)
        assert selected[0].row() == 0

    def test_remove_works(self, unordered_widget):
        unordered_widget.set_selected_keys(['DE', 'JP', 'US'])
        unordered_widget._list_widget.setCurrentRow(1)  # JP
        unordered_widget._remove_selected()
        assert unordered_widget.selected_keys() == ['DE', 'US']
