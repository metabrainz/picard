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

"""View selector (for `add_to`) for custom columns."""

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import gettext as _

from picard.ui.itemviews.custom_columns.shared import get_ordered_view_presentations


class ViewSelector(QtWidgets.QWidget):
    """Widget for selecting which views to add the column to."""

    changed = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the view selector.

        Parameters
        ----------
        parent : QtWidgets.QWidget | None, optional
            Parent widget, by default None.
        """
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._checkboxes: dict[str, QtWidgets.QCheckBox] = {}
        for vp in get_ordered_view_presentations():
            cb = QtWidgets.QCheckBox(_(vp.title), self)
            cb.setChecked(True)
            if vp.tooltip:
                cb.setToolTip(_(vp.tooltip))
            cb.stateChanged.connect(self.changed.emit)
            self._checkboxes[vp.id] = cb
            layout.addWidget(cb)

    def get_selected(self) -> list[str]:
        """Return the list of selected view identifiers.

        Returns
        -------
        list[str]
            Selected view identifiers.
        """
        return [vid for vid, cb in self._checkboxes.items() if cb.isChecked()]

    def set_selected(self, view_ids: set[str]) -> None:
        """Set the selection state of views by identifiers.

        Parameters
        ----------
        view_ids : set[str]
            Identifiers of views to mark as selected; others will be unselected.
        """
        for vid, cb in self._checkboxes.items():
            cb.setChecked(vid in view_ids)

    def select_all(self) -> None:
        """Select all available views."""
        for cb in self._checkboxes.values():
            cb.setChecked(True)
