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

from PyQt6 import QtWidgets

from picard.i18n import gettext as _
from picard.util.isrc import format_isrc


class ISRCSubmitDialog(QtWidgets.QDialog):
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
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(_("The following ISRCs will be submitted to MusicBrainz:"), self)
        layout.addWidget(label)

        tree = QtWidgets.QTreeWidget(self)
        tree.setHeaderLabels([_("Track"), _("Title"), _("Existing ISRCs"), _("New ISRC")])
        tree.setRootIsDecorated(True)
        tree.setAlternatingRowColors(True)

        for (album, albumartist), tracks in details.items():
            release_label = f"{albumartist} - {album}" if albumartist else album
            release_item = QtWidgets.QTreeWidgetItem(tree)
            release_item.setText(0, release_label)
            release_item.setFirstColumnSpanned(True)
            release_item.setExpanded(True)
            for track_number, title, existing_isrcs, new_isrcs in tracks:
                track_item = QtWidgets.QTreeWidgetItem(release_item)
                track_item.setText(0, str(track_number))
                track_item.setText(1, title)
                track_item.setText(
                    2,
                    ', '.join(format_isrc(isrc) for isrc in existing_isrcs) if existing_isrcs else '',
                )
                track_item.setText(3, ', '.join(format_isrc(isrc) for isrc in new_isrcs))

        for i in range(tree.columnCount()):
            tree.resizeColumnToContents(i)
        layout.addWidget(tree)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(_("&Submit"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
