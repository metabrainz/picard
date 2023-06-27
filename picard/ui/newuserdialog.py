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

        self.DIALOG_TEXT = _(
            (
                "<p>"
                "MusicBrainz Picard is an extremely powerful cross-platform music file tagger.  "
                "In addition to downloading metadata from the MusicBrainz database and updating the tags in your music files, "
                "it can also automatically rename your files and move them into directories based on a file renaming script."
                "</p><p>"
                "Because of Picard's power and flexibility, it has a great number of option settings that can be configured.  "
                "We encourage all new users to review all of the option settings along with the <a href='%s'>on-line documentation</a> found under "
                "the 'Help' menu (or by pressing the F1 key) to see what each option does, and to ensure that they are set to your preference.  "
                "The documentation also includes explanations of all the screens and icons displayed by the program, "
                "as well as recommended work flows and tutorials to help you get started."
                "</p><p>"
                "We strongly encourage you to work with a copy of your music files and to work on small batches of files (ideally one album at a time).  "
                "Once Picard has updated a file, there is no simple way to undo the changes."
                "</p><p>"
                "Picard is provided free of charge, as-is with no warranty, under the GNU General Public License <a href='%s'>GPL 2.0</a> or later.  "
                "You use it at your own risk."
                "</p>"
            )
        ) % (PICARD_URLS['documentation'], PICARD_URLS['license'])

        self.show_again = True
        self.SHOW_AGAIN_TEXT = _("Show this message again on next program start.")

        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Information)
        self.msg.setText(self.DIALOG_TEXT)
        self.msg.setWindowTitle(_("New User Information"))

        self.cb = QtWidgets.QCheckBox(self.SHOW_AGAIN_TEXT)
        self.cb.setChecked(self.show_again)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

    def _set_state(self):
        self.show_again = not self.show_again

    def show(self):
        self.msg.exec_()
        return self.show_again
