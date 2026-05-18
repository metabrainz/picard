# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
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

from collections.abc import Generator, Iterable

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.coverart.utils import (
    CAA_TYPES,
    translate_caa_type,
)
from picard.i18n import gettext as _

from picard.ui import PicardDialog


class CoverTypesSelectorDialog(PicardDialog):
    defaultsize = QtCore.QSize(400, 460)

    def __init__(self, selected_types: Iterable[str] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Cover art types"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self._layout = QtWidgets.QVBoxLayout(self)

        self._types_list = QtWidgets.QListWidget(self)

        # Ensure selected_types is a set
        selected_types = set(selected_types or ())

        for type in CAA_TYPES:
            name = type['name']
            item = QtWidgets.QListWidgetItem(translate_caa_type(name))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            item.setCheckState(
                QtCore.Qt.CheckState.Checked if name in selected_types else QtCore.Qt.CheckState.Unchecked
            )
            self._types_list.addItem(item)

        self._layout.addWidget(self._types_list)

        buttonbox = QtWidgets.QDialogButtonBox(self)
        buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)
        self._layout.addWidget(buttonbox)

    def selected_types(self) -> Generator[str, None, None]:
        for i in range(self._types_list.count()):
            item = self._types_list.item(i)
            if item and item.checkState() == QtCore.Qt.CheckState.Checked:
                yield item.data(QtCore.Qt.ItemDataRole.UserRole)

    @classmethod
    def display(
        cls,
        selected_types: Iterable[str] | None = None,
        parent=None,
    ) -> tuple[list[str], bool]:
        dialog = cls(
            parent=parent,
            selected_types=selected_types,
        )
        result = dialog.exec()
        return (list(dialog.selected_types()), result == QtWidgets.QDialog.DialogCode.Accepted)
