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


from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import (
    N_,
    gettext as _,
    sort_key,
)


_PLACEHOLDER_TEXT = N_("Add…")


class PreferenceListWidget(QtWidgets.QWidget):
    """Widget for selecting and ordering items from a predefined set.

    Displays a priority-ordered list of selected items with controls to
    add (via combobox), remove, and reorder.  Items higher in the list
    have higher priority.
    """

    changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, ordered=True):
        """Initialize the preference list widget.

        Args:
            parent: Parent widget.
            ordered: If True (default), items can be reordered via up/down
                buttons and drag-and-drop.  If False, items are always
                displayed in alphabetical order and reorder controls are
                hidden.
        """
        super().__init__(parent=parent)
        self._ordered = ordered
        self._available_items: dict[str, str] = {}
        self._excluded_keys: set[str] = set()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._list_widget = QtWidgets.QListWidget(self)
        if self._ordered:
            self._list_widget.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
            self._list_widget.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        else:
            self._list_widget.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop)
        self._list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self._list_widget)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self._add_combo = QtWidgets.QComboBox(self)
        self._add_combo.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        buttons_layout.addWidget(self._add_combo)

        buttons_layout.addStretch()
        if self._ordered:
            self._up_btn = self._make_button(buttons_layout, ":/images/16x16/go-up.png", _("Move up"))
            self._down_btn = self._make_button(buttons_layout, ":/images/16x16/go-down.png", _("Move down"))
        self._remove_btn = self._make_button(buttons_layout, ":/images/16x16/list-remove.png", _("Remove"))

        layout.addLayout(buttons_layout)

    def _make_button(self, layout, icon_path, tooltip) -> QtWidgets.QToolButton:
        btn = QtWidgets.QToolButton(self)
        btn.setIcon(QtGui.QIcon(icon_path))
        btn.setToolTip(tooltip)
        layout.addWidget(btn)
        return btn

    def _connect_signals(self) -> None:
        self._add_combo.activated.connect(self._on_combo_activated)
        self._remove_btn.clicked.connect(self._remove_selected)
        if self._ordered:
            self._up_btn.clicked.connect(self._move_up)
            self._down_btn.clicked.connect(self._move_down)
            model = self._list_widget.model()
            if model:
                model.rowsMoved.connect(self._on_order_changed)
        self._list_widget.itemSelectionChanged.connect(self._update_buttons)
        self._update_buttons()

    # --- Public API ---

    def set_available_items(self, items: dict[str, str]) -> None:
        """Set the full mapping of key → display name for all possible items."""
        self._available_items = dict(items)
        self._refresh_combo()

    def set_selected_keys(self, keys: list[str]) -> None:
        """Set the ordered list of currently selected keys."""
        self._list_widget.clear()
        if self._ordered:
            for key in keys:
                if key in self._available_items:
                    self._append_item(key)
        else:
            sorted_keys = sorted(
                (k for k in keys if k in self._available_items),
                key=lambda k: sort_key(self._available_items.get(k, k)),
            )
            for key in sorted_keys:
                self._append_item(key)
        self._refresh_combo()
        self._update_buttons()

    def selected_keys(self) -> list[str]:
        """Return the ordered list of selected item keys."""
        keys = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item:
                keys.append(item.data(QtCore.Qt.ItemDataRole.UserRole))
        return keys

    def set_excluded_keys(self, keys: set[str]) -> None:
        """Exclude keys from the combobox (used by a sibling widget)."""
        self._excluded_keys = keys
        self._refresh_combo()

    # --- Private ---

    def _append_item(self, key: str) -> None:
        self._list_widget.addItem(self._create_item(key))

    def _create_item(self, key: str) -> QtWidgets.QListWidgetItem:
        """Create a list item for the given key."""
        display = self._available_items.get(key, key)
        item = QtWidgets.QListWidgetItem(display)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, key)
        return item

    def _insert_item_sorted(self, key: str) -> None:
        """Insert item in alphabetically sorted position."""
        display = self._available_items.get(key, key)
        new_sort_key = sort_key(display)
        insert_row = self._list_widget.count()
        for row in range(self._list_widget.count()):
            existing_item = self._list_widget.item(row)
            if existing_item and sort_key(existing_item.text()) > new_sort_key:
                insert_row = row
                break
        self._list_widget.insertItem(insert_row, self._create_item(key))

    def _find_item_row(self, key: str) -> int:
        """Find the row index of an item by its key."""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item and item.data(QtCore.Qt.ItemDataRole.UserRole) == key:
                return i
        return -1

    def _on_combo_activated(self, index: int) -> None:
        """Handle combobox activation — skip placeholder at index 0."""
        if index <= 0:
            return
        key = self._add_combo.itemData(index, QtCore.Qt.ItemDataRole.UserRole)
        if key is None:
            return
        if self._ordered:
            self._append_item(key)
        else:
            self._insert_item_sorted(key)
        # Clear existing selection and select only the newly added item
        self._list_widget.clearSelection()
        new_row = self._find_item_row(key)
        if new_row >= 0:
            self._list_widget.setCurrentRow(new_row)
        self._refresh_combo()
        self._update_buttons()
        self.changed.emit()

    def _remove_selected(self) -> None:
        for item in self._list_widget.selectedItems():
            self._list_widget.takeItem(self._list_widget.row(item))
        self._refresh_combo()
        self._update_buttons()
        self.changed.emit()

    def _move_up(self) -> None:
        self._move_selection(-1)

    def _move_down(self) -> None:
        self._move_selection(1)

    def _move_selection(self, direction: int) -> None:
        rows = sorted(index.row() for index in self._list_widget.selectedIndexes())
        if not rows:
            return
        if direction < 0 and rows[0] == 0:
            return
        if direction > 0 and rows[-1] >= self._list_widget.count() - 1:
            return
        iterate = rows if direction < 0 else reversed(rows)
        for row in iterate:
            item = self._list_widget.takeItem(row)
            if item:
                self._list_widget.insertItem(row + direction, item)
                item.setSelected(True)
        self._list_widget.setCurrentRow(rows[0] + direction)
        self._update_buttons()
        self.changed.emit()

    def _on_order_changed(self) -> None:
        self._update_buttons()
        self.changed.emit()

    def _update_buttons(self) -> None:
        rows = sorted(index.row() for index in self._list_widget.selectedIndexes())
        has_sel = len(rows) > 0
        self._remove_btn.setEnabled(has_sel)
        if self._ordered:
            self._up_btn.setEnabled(has_sel and rows[0] > 0)
            self._down_btn.setEnabled(has_sel and rows[-1] < self._list_widget.count() - 1)

    def _refresh_combo(self) -> None:
        current_keys = set(self.selected_keys())
        hidden = current_keys | self._excluded_keys
        self._add_combo.clear()
        # Placeholder as first item (disabled in dropdown so it can't be picked)
        self._add_combo.addItem(_(_PLACEHOLDER_TEXT), None)
        model = self._add_combo.model()
        if isinstance(model, QtGui.QStandardItemModel):
            first_item = model.item(0)
            if first_item:
                first_item.setEnabled(False)
        for key, name in sorted(self._available_items.items(), key=lambda x: sort_key(x[1])):
            if key not in hidden:
                self._add_combo.addItem(name, key)
        self._add_combo.setCurrentIndex(0)
        self._add_combo.setEnabled(self._add_combo.count() > 1)
