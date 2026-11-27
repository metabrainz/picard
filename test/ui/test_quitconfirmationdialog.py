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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6 import QtWidgets

from picard.ui.quitconfirmationdialog import QuitConfirmationDialog


def test_quit_confirmation_dialog(qapp):
    dialog = QuitConfirmationDialog(None, 2)
    assert QuitConfirmationDialog.KEY == 'quit_confirmation'
    assert '2 unsaved files' in dialog.informativeText()
    assert dialog.checkBox().text() == "Do not show this message again."
    assert dialog.defaultButton() is dialog.button(QtWidgets.QMessageBox.StandardButton.Cancel)
    assert len(dialog.buttons()) == 2


def test_quit_confirmation_dialog_singular(qapp):
    dialog = QuitConfirmationDialog(None, 1)
    assert 'is 1 unsaved file' in dialog.informativeText()
