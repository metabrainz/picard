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
    QtWidgets,
)

from picard.i18n import gettext as _
from picard.util.isrc import format_isrc

from picard.ui import PicardDialog


class ISRCSubmitDialog(PicardDialog):
    """Confirmation dialog showing ISRCs to be submitted to MusicBrainz."""

    def __init__(self, details, parent=None):
        """
        Args:
            details: dict keyed by (album, albumartist) with values being
                lists of (track_number, title, existing_isrcs, new_isrcs).
        """
        super().__init__(parent=parent)
        self.setWindowTitle(_("Submit ISRCs"))
        self.resize(700, 450)
        self._details = details
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(_("The following ISRCs will be submitted to MusicBrainz:"), self)
        layout.addWidget(label)

        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setHeaderLabels([_("Track"), _("Title"), _("Existing ISRCs"), _("New ISRC")])
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)

        self._track_items = []
        for (album, albumartist), tracks in details.items():
            release_label = f"{albumartist} - {album}" if albumartist else album
            release_item = QtWidgets.QTreeWidgetItem(self._tree)
            release_item.setText(0, release_label)
            release_item.setFirstColumnSpanned(True)
            release_item.setExpanded(True)
            for detail in tracks:
                track_item = QtWidgets.QTreeWidgetItem(release_item)
                track_item.setFlags(track_item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                if detail.submittable:
                    track_item.setCheckState(0, QtCore.Qt.CheckState.Checked)
                else:
                    track_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                    track_item.setDisabled(True)
                    if detail.disabled_reason:
                        reason_text = _(detail.disabled_reason)
                        for col in range(self._tree.columnCount()):
                            track_item.setToolTip(col, reason_text)
                track_item.setText(0, detail.track_number)
                track_item.setText(1, detail.title)
                track_item.setText(
                    2,
                    ', '.join(format_isrc(isrc) for isrc in detail.existing_isrcs) if detail.existing_isrcs else '',
                )
                track_item.setText(
                    3,
                    ', '.join(format_isrc(isrc) for isrc in detail.new_isrcs) if detail.new_isrcs else '',
                )
                if detail.submittable:
                    self._track_items.append((track_item, detail.new_isrcs))

        for i in range(self._tree.columnCount()):
            self._tree.resizeColumnToContents(i)
        layout.addWidget(self._tree)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self._submit_button = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self._submit_button.setText(_("&Submit"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._tree.itemChanged.connect(self._update_submit_button)
        self._update_submit_button()

    def _update_submit_button(self):
        """Enable Submit button only when at least one track is checked."""
        has_checked = any(item.checkState(0) == QtCore.Qt.CheckState.Checked for item, _ in self._track_items)
        self._submit_button.setEnabled(has_checked)

    def get_submitted_isrcs(self) -> set[str]:
        """Return the set of ISRCs checked for submission."""
        included = set()
        for track_item, new_isrcs in self._track_items:
            if track_item.checkState(0) == QtCore.Qt.CheckState.Checked:
                included.update(new_isrcs)
        return included
