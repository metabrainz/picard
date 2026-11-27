# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022-2023 Philipp Wolfer
# Copyright (C) 2023 Bob Swift
# Copyright (C) 2024-2026 Laurent Monin
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

from picard.i18n import (
    N_,
    gettext as _,
    ngettext,
)

from picard.ui.dialogs.donotshowagainmessagebox import DoNotShowAgainMessageBox


class QuitConfirmationDialog(DoNotShowAgainMessageBox):
    KEY = 'quit_confirmation'
    TITLE = N_("Unsaved Changes")

    def __init__(self, parent, unsaved_files):
        super().__init__(
            parent,
            text=_("Are you sure you want to quit Picard?"),
            icon=QtWidgets.QMessageBox.Icon.Question,
            buttons=QtWidgets.QMessageBox.StandardButton.Cancel,
            default_button=QtWidgets.QMessageBox.StandardButton.Cancel,
        )
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setInformativeText(
            ngettext(
                "There is %d unsaved file. Closing Picard will lose all unsaved changes.",
                "There are %d unsaved files. Closing Picard will lose all unsaved changes.",
                unsaved_files,
            )
            % unsaved_files
        )
        self.addButton(_("&Quit Picard"), QtWidgets.QMessageBox.ButtonRole.YesRole)
