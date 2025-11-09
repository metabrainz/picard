# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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


class AllowRtdUpdatesDialog:
    def __init__(self, parent):
        dialog_text = _(
            "<p>"
            "The current settings do <strong>not</strong> allow Picard to check ReadTheDocs for the available "
            "languages and versions of the documentation. This means that Picard will display the 'latest' version "
            "of the documentation in English when opened in your browser."
            "</p><p>"
            "When this setting is enabled, Picard will display the current version of the documentation in the "
            "best available language based on the currently selected user interface language."
            "</p><p>"
            "Do you want to allow Picard to check the available languages and versions for the documentation on "
            "ReadTheDocs?"
            "</p>"
        )

        self.show_again = True
        show_again_text = _("Show this message again the next time you use Picard.")

        self.msg = QtWidgets.QMessageBox(parent)
        self.msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        self.msg.setText(dialog_text)
        self.msg.setWindowTitle(_("ReadTheDocs Updates"))
        self.msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self.cb = QtWidgets.QCheckBox(show_again_text)
        self.cb.setChecked(self.show_again)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        self.msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)

    def _set_state(self):
        self.show_again = not self.show_again

    def show(self):
        accepted = self.msg.exec() == QtWidgets.QMessageBox.StandardButton.Yes
        return (accepted, self.show_again)
