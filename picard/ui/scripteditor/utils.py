# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2023 Bob Swift
# Copyright (C) 2021-2025 Laurent Monin
# Copyright (C) 2021-2024 Philipp Wolfer
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

from functools import partial

from PyQt6 import QtWidgets
from PyQt6.QtGui import QPalette

from picard.i18n import gettext as _


def confirmation_dialog(parent, message):
    """Displays a confirmation dialog.

    Args:
        parent (object): Parent object / window making the call to set modality
        message (str): Message to be displayed

    Returns:
        bool: True if accepted, otherwise False.
    """
    dialog = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Warning,
        _("Confirm"),
        message,
        QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
        parent,
    )
    return dialog.exec() == QtWidgets.QMessageBox.StandardButton.Ok


def synchronize_vertical_scrollbars(widgets):
    """Synchronize position of vertical scrollbars and selections for listed widgets.

    Args:
        widgets (list): List of QListView widgets to synchronize
    """
    # Set highlight colors for selected list items
    example_style = widgets[0].palette()
    highlight_bg = example_style.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
    highlight_fg = example_style.color(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText)
    stylesheet = (
        "QListView::item:selected { color: "
        + highlight_fg.name()
        + "; background-color: "
        + highlight_bg.name()
        + "; }"
    )

    def _sync_scrollbar_vert(widget, value):
        widget.blockSignals(True)
        widget.verticalScrollBar().setValue(value)
        widget.blockSignals(False)

    widgets = set(widgets)
    for widget in widgets:
        for other in widgets - {widget}:
            widget.verticalScrollBar().valueChanged.connect(partial(_sync_scrollbar_vert, other))
        widget.setStyleSheet(stylesheet)


def populate_script_selection_combo_box(naming_scripts, selected_script_id, combo_box):
    """Populate the specified script selection combo box and identify the selected script.

    Args:
        naming_scripts (dict): Dictionary of available user-defined naming scripts as script dictionaries as produced by FileNamingScriptInfo().to_dict()
        selected_script_id (str): ID code for the currently selected script
        combo_box (QComboBox): Combo box object to populate

    Returns:
        int: The index of the currently selected script
    """
    combo_box.blockSignals(True)
    combo_box.clear()

    def _add_and_check(idx, count, title, item):
        combo_box.addItem(title, item)
        if item['id'] == selected_script_id:
            idx = count
        return idx

    idx = 0
    count = -1
    for count, (_id, naming_script) in enumerate(sorted(naming_scripts.items(), key=lambda item: item[1]['title'])):
        idx = _add_and_check(idx, count, naming_script['title'], naming_script)

    combo_box.setCurrentIndex(idx)
    combo_box.blockSignals(False)
    return idx
