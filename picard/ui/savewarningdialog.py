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

from picard.config import get_config

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)


class SaveWarningDialog(PicardDialog, SingletonDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        actions = []
        config = get_config()
        if not config.setting["dont_write_tags"]:
            actions.append(_("overwrite existing metadata in the files"))
        if config.setting["rename_files"] and config.setting["move_files"]:
            actions.append(_("rename and move the files"))
        elif config.setting["rename_files"]:
            actions.append(_("rename the files"))
        elif config.setting["move_files"]:
            actions.append(_("move the files"))
        if actions:
            self.WARNING_TEXT = _("This will ") + ' and '.join(actions) + '.  This action cannot be undone.  Do you want to continue?'
        else:
            self.WARNING_TEXT = -("There are no actions selected.  No changes will be saved.")
        self.DISABLE_TEXT = _("Don't show this warning again.")

        self.disable = False
        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Warning)
        self.msg.setText(self.WARNING_TEXT)
        self.msg.setWindowTitle(_("File Save Warning"))

        self.cb = QtWidgets.QCheckBox(self.DISABLE_TEXT)
        self.cb.setChecked(False)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

    def _set_state(self):
        self.disable = not self.disable

    def show(self):
        return self.msg.exec_() == QtWidgets.QMessageBox.Ok, self.disable
