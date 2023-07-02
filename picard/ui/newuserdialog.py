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


from PyQt5 import QtWidgets

from picard.const import PICARD_URLS


class NewUserDialog():

    def __init__(self):

        dialog_text = _(
            "<h2 align=center>READ THIS BEFORE USING PICARD</h2>"
            "<p>"
            "Picard is a very flexible music tagging tool, using MusicBrainz metadata for tags and file naming, "
            "but if you don't understand how it works, what its limitations are, and how to configure it, "
            "you can easily mess up your music library."
            "</p><p>"
            "We therefore <strong>STRONGLY</strong> recommend that you:"
            "</p><ol>"
            "<li>Read the Picard <a href='{documentation_url}'>documentation</a> "
            "before you use this tool on your music collection. The link is also available from the Help menu.<br /></li>"
            "<li>Work on copies of your music files and in small batches until you are fully confident that your music files will be handled the way "
            "you want them to be. <strong>Once Picard has updated a file, there is no way to undo the changes</strong>.</li>"
            "</ol><p>"
            "Picard is open source software written by volunteers. It is provided as-is and with no warranty. "
            "<strong>You use Picard at your own risk.</strong>"
            "</p>"
        ).format(documentation_url=PICARD_URLS['documentation_server'])

        self.show_again = True
        show_again_text = _("Show this message again the next time you start Picard.")

        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Warning)
        self.msg.setText(dialog_text)
        self.msg.setWindowTitle(_("New User Information"))

        self.cb = QtWidgets.QCheckBox(show_again_text)
        self.cb.setChecked(self.show_again)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

    def _set_state(self):
        self.show_again = not self.show_again

    def show(self):
        self.msg.exec_()
        return self.show_again
