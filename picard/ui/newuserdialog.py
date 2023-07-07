# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023 Bob Swift
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


from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.const import PICARD_URLS


class NewUserDialog():

    def __init__(self, parent):

        dialog_text = _(
            "<h2 align=center>READ THIS BEFORE USING PICARD</h2>"
            "<p>"
            "Picard is a very flexible music tagging tool which uses metadata from MusicBrainz for tags and file naming. "
            "However, if you do not understand how it works, its limitations, or how to configure the program, "
            "you can easily make undesired changes to your music files."
            "</p><p>"
            "We therefore <strong>STRONGLY</strong> recommend that you:"
            "</p><ol>"
            "<li>Read the Picard <a href='{documentation_url}'>documentation</a> "
            'before you use this tool on your music collection. This link is also accessible from the "Help" menu.<br /></li>'
            "<li>Start with copies of your music, and in small batches until you are fully confident that your music files "
            "will be handled as intended. It is important to note that <strong>once Picard changes/updates a file, "
            "there is no way to undo any of the changes</strong>.</li>"
            "</ol><p>"
            "Picard is open source software written by volunteers. It is provided as-is and with no warranty. "
            "<strong>You use Picard at your own risk.</strong>"
            "</p>"
        ).format(documentation_url=PICARD_URLS['documentation_server'])

        self.show_again = True
        show_again_text = _("Show this message again the next time you start Picard.")

        self.msg = QtWidgets.QMessageBox(parent)
        self.msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        self.msg.setText(dialog_text)
        self.msg.setWindowTitle(_("New User Information"))
        self.msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self.cb = QtWidgets.QCheckBox(show_again_text)
        self.cb.setChecked(self.show_again)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)

    def _set_state(self):
        self.show_again = not self.show_again

    def show(self):
        self.msg.exec_()
        return self.show_again
