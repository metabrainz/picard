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

from picard.config import get_config


class SaveWarningDialog():

    def __init__(self, parent, file_count=None):

        actions = []
        config = get_config()

        if not config.setting['dont_write_tags']:
            actions.append(_("overwrite existing metadata (tags) within the files"))
        if config.setting['rename_files']:
            actions.append(_("rename the files"))
        if config.setting['move_files']:
            actions.append(_("move the files to a different location"))

        if actions:
            header = _("This action will:")
            footer = _("<strong>This action cannot be undone.</strong> Do you want to continue?")
            list_of_actions = ''
            for action in actions:
                list_of_actions += _('<li>{action}</li>').format(action=action)
            if file_count:
                count_text = _("The number of files to be processed is {file_count:,d}.").format(file_count=file_count)
                warning_text = _('<p>{header}</p><ul>{list_of_actions}</ul><p>{count_text}</p><p>{footer}</p>').format(
                    header=header, list_of_actions=list_of_actions, footer=footer, count_text=count_text)
            else:
                warning_text = _('<p>{header}</p><ul>{list_of_actions}</ul><p>{footer}</p>').format(header=header, list_of_actions=list_of_actions, footer=footer)
        else:
            warning_text = _("There are no actions selected. No changes will be saved.")

        disable_text = _("Don't show this warning again.")

        self.disable = False
        self.msg = QtWidgets.QMessageBox(parent)
        self.msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        self.msg.setText(warning_text)
        self.msg.setWindowTitle(_("File Save Warning"))
        self.msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self.cb = QtWidgets.QCheckBox(disable_text)
        self.cb.setChecked(False)
        self.cb.toggled.connect(self._set_state)

        self.msg.setCheckBox(self.cb)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)

    def _set_state(self):
        self.disable = not self.disable

    def show(self):
        return self.msg.exec_() == QtWidgets.QMessageBox.StandardButton.Ok, self.disable
