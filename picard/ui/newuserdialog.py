# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022-2023 Philipp Wolfer
# Copyright (C) 2023 Bob Swift
# Copyright (C) 2024 Laurent Monin
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

from picard.const import PICARD_URLS


class NewUserDialog():

    def __init__(self, parent):

        dialog_text = _(
            "<p>"
            "<strong>Changes made by Picard are not reversible.</strong>"
            "</p><p>"
            "Picard is a very flexible music tagging tool which can rename your files and overwrite the tags. "
            "We <strong>strongly recommend</strong> that you:"
            "</p><ul>"
            "<li>read the <a href='{documentation_url}'>User Guide</a> (also available from the Help menu)</li>"
            "<li>test with copies of your music and work in small batches</li>"
            "</ul><p>"
            "Picard is open source software written by volunteers. It is provided as-is and with no warranty."
            "</p>"
        ).format(documentation_url=PICARD_URLS['documentation_server'])

        self.show_again = True
        show_again_text = _("Show this message again the next time you start Picard.")

        self.msg = QtWidgets.QMessageBox(parent)
        self.msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        self.msg.setText(dialog_text)
        self.msg.setWindowTitle(_("New User Warning"))
        self.msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self.cb = QtWidgets.QCheckBox(show_again_text)
        self.cb.setChecked(self.show_again)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)

    def _set_state(self):
        self.show_again = not self.show_again

    def show(self):
        self.msg.exec()
        return self.show_again
