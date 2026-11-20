# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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


from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import gettext as _


class PluginNotesDialog:
    def __init__(self, parent):
        dialog_text = _(
            "<p>"
            "Picard's functionality can be extended through the use of plugins. "
            "Plugins can be installed/uninstalled and enabled/disabled from the "
            "Options menu. Installed plugins are loaded during the startup of "
            "Picard, and are made available to the program."
            "</p><p>"
            "The Plugins page under the Options menu differs from all other option "
            "settings pages in that any changes made or actions taken on this page "
            "are processed immediately and are not reverted if the user clicks "
            "\"Cancel\"."
            "</p><p>"
            "<strong>Be aware that installing plugins from unknown sources may pose "
            "security risks. Only install plugins from sources you trust!</strong>"
            "</p>"
        )

        self.show_again = True
        show_again_text = _("Show this message again when displaying Plugin options.")

        self.msg = QtWidgets.QMessageBox(parent)
        self.msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        self.msg.setText(dialog_text)
        self.msg.setWindowTitle(_("Plugin Options Notes"))
        self.msg.setWindowModality(QtCore.Qt.WindowModality.WindowModal)

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
