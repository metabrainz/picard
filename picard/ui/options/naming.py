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
from picard.api import IOptionsPage, OptionsCheckError
from picard.component import Component, implements
from picard.config import BoolOption, TextOption
from picard.script import ScriptParser
from picard.util import decode_filename

class FileNamingOptionsPage(Component):

    implements(IOptionsPage)

    options = [
        BoolOption("setting", "windows_compatible_filenames", True),
        BoolOption("setting", "ascii_filenames", False),
        BoolOption("setting", "rename_files", False),
        BoolOption("setting", "move_files", False),
        TextOption("setting", "file_naming_format", "$if2(%albumartist%,%artist%)/%album%/$num(%tracknumber%,2) %title%"),
        TextOption("setting", "va_file_naming_format", "$if2(%albumartist%,%artist%)/%album%/$num(%tracknumber%,2) %artist% - %title%"),
        TextOption("setting", "move_files_to", ""),
        BoolOption("setting", "move_additional_files", False),
        TextOption("setting", "move_additional_files_pattern", "*.jpg *.png"),
        BoolOption("setting", "delete_empty_dirs", True),
    ]

    def get_page_info(self):
        return (_(u"File Naming"), "filenaming", None, 40)

    def get_page_widget(self, parent=None):
        from picard.ui.ui_options_naming import Ui_Form
        self.widget = QtGui.QWidget(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self.widget)
        self.connect(self.ui.file_naming_format_default, QtCore.SIGNAL("clicked()"),
                     self.set_file_naming_format_default)
        self.connect(self.ui.va_file_naming_format_default, QtCore.SIGNAL("clicked()"),
                     self.set_va_file_naming_format_default)
        self.connect(self.ui.move_files_to_browse, QtCore.SIGNAL("clicked()"),
                     self.move_files_to_browse)
        self.connect(self.ui.move_additional_files, QtCore.SIGNAL("clicked()"),
                     self.update_move_additional_files)
        return self.widget

    def load_options(self):
        if sys.platform == "win32":
            self.ui.windows_compatible_filenames.setChecked(True)
            self.ui.windows_compatible_filenames.setEnabled(False)
        else:
            self.ui.windows_compatible_filenames.setChecked(self.config.setting["windows_compatible_filenames"])
        self.ui.ascii_filenames.setChecked(self.config.setting["ascii_filenames"])
        self.ui.rename_files.setChecked(self.config.setting["rename_files"])
        self.ui.move_files.setChecked(self.config.setting["move_files"])
        self.ui.file_naming_format.setText(self.config.setting["file_naming_format"])
        self.ui.file_naming_format.setCursorPosition(0)
        self.ui.va_file_naming_format.setText(self.config.setting["va_file_naming_format"])
        self.ui.va_file_naming_format.setCursorPosition(0)
        self.ui.move_files_to.setText(self.config.setting["move_files_to"])
        self.ui.move_files_to.setCursorPosition(0)
        self.ui.move_additional_files.setChecked(self.config.setting["move_additional_files"])
        self.ui.move_additional_files_pattern.setText(self.config.setting["move_additional_files_pattern"])
        self.update_move_additional_files()
        self.ui.delete_empty_dirs.setChecked(self.config.setting["delete_empty_dirs"])

    def check(self):
        parser = ScriptParser()
        try:
            parser.parse(unicode(self.ui.file_naming_format.text()))
        except Exception, e:
            raise OptionsCheckError(_("Script Error"), _("File naming format:") + " " + str(e))
        try:
            parser.parse(unicode(self.ui.va_file_naming_format.text()))
        except Exception, e:
            raise OptionsCheckError(_("Script Error"), _("Multiple artist file naming format:") + " " + str(e))

    def save_options(self):
        self.config.setting["windows_compatible_filenames"] = self.ui.windows_compatible_filenames.isChecked()
        self.config.setting["ascii_filenames"] = self.ui.ascii_filenames.isChecked()
        self.config.setting["rename_files"] = self.ui.rename_files.isChecked()
        self.config.setting["move_files"] = self.ui.move_files.isChecked()
        self.config.setting["file_naming_format"] = unicode(self.ui.file_naming_format.text())
        self.config.setting["va_file_naming_format"] = unicode(self.ui.va_file_naming_format.text())
        self.config.setting["move_files_to"] = os.path.normpath(unicode(self.ui.move_files_to.text()))
        self.config.setting["move_additional_files"] = self.ui.move_additional_files.isChecked()
        self.config.setting["move_additional_files_pattern"] = unicode(self.ui.move_additional_files_pattern.text())
        self.config.setting["delete_empty_dirs"] = self.ui.delete_empty_dirs.isChecked()

    def set_file_naming_format_default(self):
        self.ui.file_naming_format.setText(self.options[4].default)
        self.ui.file_naming_format.setCursorPosition(0)

    def set_va_file_naming_format_default(self):
        self.ui.va_file_naming_format.setText(self.options[5].default)
        self.ui.va_file_naming_format.setCursorPosition(0)

    def move_files_to_browse(self):
        path = QtGui.QFileDialog.getExistingDirectory(
            self.widget, "", self.ui.move_files_to.text())
        if path:
            path = decode_filename(os.path.normpath(str(path)))
            self.ui.move_files_to.setText(path)

    def update_move_additional_files(self):
        self.ui.move_additional_files_pattern.setEnabled(
            self.ui.move_additional_files.isChecked())
