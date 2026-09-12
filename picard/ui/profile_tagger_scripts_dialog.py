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


"""Dialog asking the user whether to enable tagger scripts on profile import.

Shown when a shared profile is imported that carries one or more enabled
tagger scripts. Importing must not silently turn on tagger scripting, so the
user is warned and given a per-script choice. Accepting with at least one
script checked enables tagger scripting for the profile and applies the
per-script selection; rejecting (or unchecking everything) imports the
scripts but leaves tagger scripting disabled.
"""

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import gettext as _


class ProfileTaggerScriptsDialog(QtWidgets.QDialog):
    """Ask whether to enable tagger scripting for an imported profile.

    Args:
        profile_title: Title of the imported profile (for the message).
        scripts: List of (position, title, enabled, content) tuples for the
            profile's tagger scripts. All are shown, pre-checked according to
            their ``enabled`` flag.
        parent: Parent widget.
    """

    def __init__(self, profile_title, scripts, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Enable Tagger Scripts?"))
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)

        message = QtWidgets.QLabel(
            _(
                "The imported profile \"%s\" contains tagger scripts. Tagger "
                "scripting is currently disabled for this profile.\n\n"
                "Enabling it will run the checked scripts when this profile is "
                "active. Uncheck any script you do not want to run, or cancel "
                "to import the scripts without enabling tagger scripting."
            )
            % profile_title
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        self._list = QtWidgets.QListWidget(self)
        for pos, title, enabled, _content in scripts:
            item = QtWidgets.QListWidgetItem(title, self._list)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Checked if enabled else QtCore.Qt.CheckState.Unchecked)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, pos)
        layout.addWidget(self._list)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        ok_button = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setText(_("Enable tagger scripts"))
        cancel_button = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setText(_("Import without enabling"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_positions(self) -> set:
        """Return the set of script positions the user left checked."""
        selected = set()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is not None and item.checkState() == QtCore.Qt.CheckState.Checked:
                selected.add(item.data(QtCore.Qt.ItemDataRole.UserRole))
        return selected
