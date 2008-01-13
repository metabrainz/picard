# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

import os.path
import sys
from PyQt4 import QtCore, QtGui
from picard.config import BoolOption, TextOption
from picard.file import File
from picard.script import ScriptParser
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_moving import Ui_MovingOptionsPage
from picard.util import decode_filename

class MovingOptionsPage(OptionsPage):

    NAME = "filemoving"
    TITLE = N_("Moving files")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True

    options = [
        BoolOption("setting", "move_files", False),
        TextOption("setting", "move_files_to", ""),
        BoolOption("setting", "move_additional_files", False),
        TextOption("setting", "move_additional_files_pattern", "*.jpg *.png"),
        BoolOption("setting", "delete_empty_dirs", True),
    ]

    def __init__(self, parent=None):
        super(MovingOptionsPage, self).__init__(parent)
        self.ui = Ui_MovingOptionsPage()
        self.ui.setupUi(self)
        self.connect(self.ui.move_files_to_browse, QtCore.SIGNAL("clicked()"), self.move_files_to_browse)
        self.connect(self.ui.move_additional_files, QtCore.SIGNAL("clicked()"), self.update_move_additional_files)

    def load(self):
        self.ui.move_files.setChecked(self.config.setting["move_files"])
        self.ui.move_files_to.setText(self.config.setting["move_files_to"])
        self.ui.move_files_to.setCursorPosition(0)
        self.ui.move_additional_files.setChecked(self.config.setting["move_additional_files"])
        self.ui.move_additional_files_pattern.setText(self.config.setting["move_additional_files_pattern"])
        self.update_move_additional_files()
        self.ui.delete_empty_dirs.setChecked(self.config.setting["delete_empty_dirs"])

    def save(self):
        self.config.setting["move_files"] = self.ui.move_files.isChecked()
        self.config.setting["move_files_to"] = os.path.normpath(unicode(self.ui.move_files_to.text()))
        self.config.setting["move_additional_files"] = self.ui.move_additional_files.isChecked()
        self.config.setting["move_additional_files_pattern"] = unicode(self.ui.move_additional_files_pattern.text())
        self.config.setting["delete_empty_dirs"] = self.ui.delete_empty_dirs.isChecked()
        self.tagger.window.enable_moving_action.setChecked(self.config.setting["move_files"])

    def move_files_to_browse(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "", self.ui.move_files_to.text())
        if path:
            path = os.path.normpath(unicode(path))
            self.ui.move_files_to.setText(path)

    def update_move_additional_files(self):
        self.ui.move_additional_files_pattern.setEnabled(self.ui.move_additional_files.isChecked())

register_options_page(MovingOptionsPage)
