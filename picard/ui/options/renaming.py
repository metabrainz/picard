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
from picard.ui.ui_options_renaming import Ui_RenamingOptionsPage
from picard.util import decode_filename
from picard.ui.options.scripting import TaggerScriptSyntaxHighlighter

class RenamingOptionsPage(OptionsPage):

    NAME = "filerenaming"
    TITLE = N_("File Renaming")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True

    options = [
        BoolOption("setting", "windows_compatible_filenames", True),
        BoolOption("setting", "ascii_filenames", False),
        BoolOption("setting", "rename_files", False),
        TextOption("setting", "file_naming_format", "$if2(%albumartist%,%artist%)/%album%/$num(%tracknumber%,2) %title%"),
        TextOption("setting", "va_file_naming_format", "$if2(%albumartist%,%artist%)/%album%/$num(%tracknumber%,2) %artist% - %title%"),
        BoolOption("setting", "use_va_format", False)
    ]

    def __init__(self, parent=None):
        super(RenamingOptionsPage, self).__init__(parent)
        self.ui = Ui_RenamingOptionsPage()
        self.ui.setupUi(self)
        self.connect(self.ui.file_naming_format_default, QtCore.SIGNAL("clicked()"), self.set_file_naming_format_default)
        self.connect(self.ui.va_file_naming_format_default, QtCore.SIGNAL("clicked()"), self.set_va_file_naming_format_default)
        self.connect(self.ui.va_copy_from_above, QtCore.SIGNAL("clicked()"), self.copy_format_to_va)
        self.connect(self.ui.file_naming_format, QtCore.SIGNAL("textChanged()"), self.test)
        self.connect(self.ui.va_file_naming_format, QtCore.SIGNAL("textChanged()"), self.va_test)
        self.highlighter = TaggerScriptSyntaxHighlighter(self.ui.file_naming_format.document())
        self.highlighter_va = TaggerScriptSyntaxHighlighter(self.ui.va_file_naming_format.document())
        
    def load(self):
        if sys.platform == "win32":
            self.ui.windows_compatible_filenames.setChecked(True)
            self.ui.windows_compatible_filenames.setEnabled(False)
        else:
            self.ui.windows_compatible_filenames.setChecked(self.config.setting["windows_compatible_filenames"])
        self.ui.use_va_format.setChecked(self.config.setting["use_va_format"])
        self.ui.ascii_filenames.setChecked(self.config.setting["ascii_filenames"])
        self.ui.rename_files.setChecked(self.config.setting["rename_files"])
        self.ui.file_naming_format.setPlainText(self.config.setting["file_naming_format"])
        self.ui.va_file_naming_format.setPlainText(self.config.setting["va_file_naming_format"])

    def check(self):
        parser = ScriptParser()
        try:
            parser.parse(unicode(self.ui.file_naming_format.toPlainText()))
        except Exception, e:
            raise OptionsCheckError(_("Script Error"), _("File naming format:") + " " + str(e))
        try:
            parser.parse(unicode(self.ui.va_file_naming_format.toPlainText()))
        except Exception, e:
            raise OptionsCheckError(_("Script Error"), _("Multiple artist file naming format:") + " " + str(e))
        if self.ui.rename_files.isChecked():
           if not unicode(self.ui.file_naming_format.toPlainText()).strip():
                raise OptionsCheckError(_("Script Error"), _("The file naming format must not be empty."))
           if self.ui.use_va_format.isChecked() and not unicode(self.ui.va_file_naming_format.toPlainText()).strip():
                raise OptionsCheckError(_("Script Error"), _("The multiple artist file naming format must not be empty."))

    def save(self):
        self.config.setting["use_va_format"] = self.ui.use_va_format.isChecked()
        self.config.setting["windows_compatible_filenames"] = self.ui.windows_compatible_filenames.isChecked()
        self.config.setting["ascii_filenames"] = self.ui.ascii_filenames.isChecked()
        self.config.setting["rename_files"] = self.ui.rename_files.isChecked()
        self.config.setting["file_naming_format"] = unicode(self.ui.file_naming_format.toPlainText())
        self.config.setting["va_file_naming_format"] = unicode(self.ui.va_file_naming_format.toPlainText())
        self.tagger.window.enable_renaming_action.setChecked(self.config.setting["rename_files"])

    def set_file_naming_format_default(self):
        self.ui.file_naming_format.setText(self.options[3].default)
#        self.ui.file_naming_format.setCursorPosition(0)

    def set_va_file_naming_format_default(self):
        self.ui.va_file_naming_format.setText(self.options[4].default)
#        self.ui.va_file_naming_format.setCursorPosition(0)

    def copy_format_to_va(self):
        self.ui.va_file_naming_format.setText(self.ui.file_naming_format.toPlainText())

    def test(self):
        try:
            self.check()
        except OptionsCheckError, e:
            dialog = QtGui.QMessageBox(QtGui.QMessageBox.Warning, e.title, e.message, QtGui.QMessageBox.Ok, self)
            dialog.exec_()
            return
        
        settings = {
            'windows_compatible_filenames': self.ui.windows_compatible_filenames.isChecked(),
            'ascii_filenames': self.ui.ascii_filenames.isChecked(),
            'rename_files': self.ui.rename_files.isChecked(),
            'move_files': self.config.setting["move_files"],
            'use_va_format': self.ui.use_va_format.isChecked(),
            'file_naming_format': unicode(self.ui.file_naming_format.toPlainText()),
            'va_file_naming_format': unicode(self.ui.va_file_naming_format.toPlainText()),
            'move_files_to': os.path.normpath(unicode(self.config.setting["move_files_to"])),
        }
        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            parser = ScriptParser()
        else:
            script = None

        file = File("ticket_to_ride.mp3")
        file.metadata['album'] = 'Help!'
        file.metadata['title'] = 'Ticket to Ride'
        file.metadata['artist'] = 'The Beatles'
        file.metadata['artistsort'] = 'Beatles, The'
        file.metadata['albumartist'] = 'The Beatles'
        file.metadata['albumartistsort'] = 'Beatles, The'
        file.metadata['tracknumber'] = '7'
        file.metadata['totaltracks'] = '14'
        file.metadata['date'] = '1965-08-06'
        file.metadata['releasetype'] = 'album'
        file.metadata['releasestatus'] = 'official'
        file.metadata['releasecountry'] = 'US'
        file.metadata['~extension'] = 'mp3'
        file.metadata['musicbrainz_albumid'] = '2c053984-4645-4699-9474-d2c35c227028'
        file.metadata['musicbrainz_albumartistid'] = 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d'
        file.metadata['musicbrainz_artistid'] = 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d'
        file.metadata['musicbrainz_trackid'] = '898a2916-f64d-48d3-ab1a-3446fb450448'
        if script:
            parser.eval(script, file.metadata)
        filename = file._make_filename(file.filename, file.metadata, settings)
        self.ui.example_filename.setText(filename)

    def va_test(self):

        try:
            self.check()
        except OptionsCheckError, e:
            dialog = QtGui.QMessageBox(QtGui.QMessageBox.Warning, e.title, e.message, QtGui.QMessageBox.Ok, self)
            dialog.exec_()
            return
        
        settings = {
            'windows_compatible_filenames': self.ui.windows_compatible_filenames.isChecked(),
            'ascii_filenames': self.ui.ascii_filenames.isChecked(),
            'rename_files': self.ui.rename_files.isChecked(),
            'move_files': self.config.setting["move_files"],
            'use_va_format': self.ui.use_va_format.isChecked(),
            'file_naming_format': unicode(self.ui.file_naming_format.toPlainText()),
            'va_file_naming_format': unicode(self.ui.va_file_naming_format.toPlainText()),
            'move_files_to': os.path.normpath(unicode(self.config.setting["move_files_to"])),
        }

        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            parser = ScriptParser()
        else:
            script = None
            
        file = File("track05.mp3")
        file.metadata['album'] = 'Explosive Doowops, Volume 4'
        file.metadata['title'] = 'Why? Oh Why?'
        file.metadata['artist'] = 'The Fantasys'
        file.metadata['artistsort'] = 'Fantasys, The'
        file.metadata['albumartist'] = self.config.setting['va_name']
        file.metadata['albumartistsort'] = self.config.setting['va_name']
        file.metadata['tracknumber'] = '5'
        file.metadata['totaltracks'] = '26'
        file.metadata['date'] = '1999-02-03'
        file.metadata['releasetype'] = 'compilation'
        file.metadata['releasestatus'] = 'official'
        file.metadata['releasecountry'] = 'US'
        file.metadata['compilation'] = '1'
        file.metadata['~extension'] = 'mp3'
        file.metadata['musicbrainz_albumid'] = 'bcc97e8a-2055-400b-a6ed-83288285c6fc'
        file.metadata['musicbrainz_albumartistid'] = '89ad4ac3-39f7-470e-963a-56509c546377'
        file.metadata['musicbrainz_artistid'] = '06704773-aafe-4aca-8833-b449e0a6467f'
        file.metadata['musicbrainz_trackid'] = 'd92837ee-b1e4-4649-935f-e433c3e5e429'
        if script:
            parser.eval(script, file.metadata)
        filename = file._make_filename(file.filename, file.metadata, settings)
        self.ui.example_va_filename.setText(filename)

register_options_page(RenamingOptionsPage)
