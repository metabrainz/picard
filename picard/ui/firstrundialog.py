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

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)


class FirstRunDialog(PicardDialog, SingletonDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.DIALOG_TEXT = _(
            (
                "<p>"
                "It appears that this is the first time that Picard has been started on this system, so there are a few things that you should know about its use.  "
                "MusicBrainz Picard is an extremely powerful cross-platform music file tagger.  "
                "In addition to downloading metadata from the MusicBrainz database and updating the tags in your music files, "
                "it can also automatically rename your files and move them into directories based on a file renaming script."
                "</p><p>"
                "Because of Picard's power and flexibility, it has a great number of option settings that can be configured.  "
                "We encourage all new users to review the on-line documentation found under the 'Help' menu (or by pressing the F1 key) to see what "
                "each option does.  There are also explanations of all the screens displayed by the program, as well as suggested work flows and tutorials to "
                "help you get started."
                "</p><p>"
                "Finally, we strongly encourage you to work with a copy of your music files initially, until you are sure that Picard is configured properly and "
                "is producing the results that you expect.  Once Picard has updated a file, there is no simple way to undo the changes."
                "</p>"
            )
        )

        self.show_again = False
        self.SHOW_AGAIN_TEXT = _("Show this message again on next program start.")

        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Information)
        self.msg.setText(self.DIALOG_TEXT)
        self.msg.setWindowTitle(_("First Use Information"))

        self.cb = QtWidgets.QCheckBox(self.SHOW_AGAIN_TEXT)
        self.cb.setChecked(False)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

    def _set_state(self):
        self.show_again = not self.show_again

    def show(self):
        self.msg.exec_()
        return self.show_again
