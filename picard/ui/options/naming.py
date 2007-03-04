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
from picard.ui.ui_options_naming import Ui_NamingOptionsPage
from picard.util import decode_filename

class NamingOptionsPage(OptionsPage):

    NAME = "filenaming"
    TITLE = N_("File Naming")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True

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

    def __init__(self, parent=None):
        super(NamingOptionsPage, self).__init__(parent)
        self.ui = Ui_NamingOptionsPage()
        self.ui.setupUi(self)
        self.connect(self.ui.file_naming_format_default, QtCore.SIGNAL("clicked()"), self.set_file_naming_format_default)
        self.connect(self.ui.va_file_naming_format_default, QtCore.SIGNAL("clicked()"), self.set_va_file_naming_format_default)
        self.connect(self.ui.move_files_to_browse, QtCore.SIGNAL("clicked()"), self.move_files_to_browse)
        self.connect(self.ui.move_additional_files, QtCore.SIGNAL("clicked()"), self.update_move_additional_files)
        self.connect(self.ui.test_button, QtCore.SIGNAL("clicked()"), self.test)

    def load(self):
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

    def save(self):
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
        self.tagger.window.enable_renaming_action.setChecked(self.config.setting["rename_files"])
        self.tagger.window.enable_moving_action.setChecked(self.config.setting["move_files"])

    def set_file_naming_format_default(self):
        self.ui.file_naming_format.setText(self.options[4].default)
        self.ui.file_naming_format.setCursorPosition(0)

    def set_va_file_naming_format_default(self):
        self.ui.va_file_naming_format.setText(self.options[5].default)
        self.ui.va_file_naming_format.setCursorPosition(0)

    def move_files_to_browse(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "", self.ui.move_files_to.text())
        if path:
            path = decode_filename(os.path.normpath(str(path)))
            self.ui.move_files_to.setText(path)

    def update_move_additional_files(self):
        self.ui.move_additional_files_pattern.setEnabled(self.ui.move_additional_files.isChecked())

    def test(self):
        settings = {
            'windows_compatible_filenames': self.ui.windows_compatible_filenames.isChecked(),
            'ascii_filenames': self.ui.ascii_filenames.isChecked(),
            'rename_files': self.ui.rename_files.isChecked(),
            'move_files': self.ui.move_files.isChecked(),
            'file_naming_format': unicode(self.ui.file_naming_format.text()),
            'va_file_naming_format': unicode(self.ui.va_file_naming_format.text()),
            'move_files_to': os.path.normpath(unicode(self.ui.move_files_to.text())),
        }

        file = File("ticket_to_ride.mp3")
        file.metadata['album'] = 'Help!'
        file.metadata['title'] = 'Ticket to Ride'
        file.metadata['artist'] = 'The Beatles'
        file.metadata['albumartist'] = 'The Beatles'
        file.metadata['tracknumber'] = '7'
        file.metadata['totaltracks'] = '14'
        file.metadata['date'] = '1965-08-06'
        file.metadata['~extension'] = 'mp3'
        filename = file.make_filename(settings=settings)
        self.ui.example_filename.setText(filename)

        file = File("track05.mp3")
        file.metadata['album'] = 'Explosive Doowops, Volume 4'
        file.metadata['title'] = 'Why? Oh Why?'
        file.metadata['artist'] = 'The Fantasys'
        file.metadata['albumartist'] = 'Various Artists'
        file.metadata['tracknumber'] = '5'
        file.metadata['totaltracks'] = '26'
        file.metadata['date'] = '1999-02-03'
        file.metadata['compilation'] = '1'
        file.metadata['~extension'] = 'mp3'
        filename = file.make_filename(settings=settings)
        self.ui.example_va_filename.setText(filename)


register_options_page(NamingOptionsPage)
