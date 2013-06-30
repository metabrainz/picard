# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2008 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
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
from functools import partial
from PyQt4 import QtCore, QtGui
from picard import config
from picard.file import File
from picard.script import ScriptParser, SyntaxError, UnknownFunction
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_renaming import Ui_RenamingOptionsPage
from picard.ui.options.scripting import TaggerScriptSyntaxHighlighter


class RenamingOptionsPage(OptionsPage):

    NAME = "filerenaming"
    TITLE = N_("File naming")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True

    options = [
        config.BoolOption("setting", "windows_compatible_filenames", True),
        config.BoolOption("setting", "ascii_filenames", False),
        config.BoolOption("setting", "rename_files", False),
        config.TextOption("setting", "file_naming_format", "$if2(%albumartist%,%artist%)/%album%/$if($gt(%totaldiscs%,1),%discnumber%-,)$num(%tracknumber%,2)$if(%compilation%, %artist% -,) %title%"),
        config.BoolOption("setting", "move_files", False),
        config.TextOption("setting", "move_files_to", ""),
        config.BoolOption("setting", "move_additional_files", False),
        config.TextOption("setting", "move_additional_files_pattern", "*.jpg *.png"),
        config.BoolOption("setting", "delete_empty_dirs", True),
    ]

    def __init__(self, parent=None):
        super(RenamingOptionsPage, self).__init__(parent)
        self.ui = Ui_RenamingOptionsPage()
        self.ui.setupUi(self)

        self.ui.ascii_filenames.clicked.connect(self.update_examples)
        self.ui.windows_compatible_filenames.clicked.connect(self.update_examples)
        self.ui.rename_files.clicked.connect(self.update_examples)
        self.ui.move_files.clicked.connect(self.update_examples)
        self.ui.move_files_to.editingFinished.connect(self.update_examples)

        # The following code is there to fix
        # http://tickets.musicbrainz.org/browse/PICARD-417
        # In some older version of PyQt/sip it's impossible to connect a signal
        # emitting an `int` to a slot expecting a `bool`.
        # By using `enabledSlot` instead we can force python to do the
        # conversion from int (`state`) to bool.
        def enabledSlot(func, state):
            """Calls `func` with `state`."""
            func(state)

        if not sys.platform == "win32":
            self.ui.rename_files.stateChanged.connect(partial(
                                                       enabledSlot,
                                                       self.ui.windows_compatible_filenames.setEnabled)
                                                      )

        self.ui.move_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.delete_empty_dirs.setEnabled)
                                               )
        self.ui.move_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.move_files_to.setEnabled)
                                                )
        self.ui.move_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.move_files_to_browse.setEnabled)
                                                )
        self.ui.move_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.move_additional_files.setEnabled)
                                                )
        self.ui.move_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.move_additional_files_pattern.setEnabled)
                                                )
        self.ui.rename_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.ascii_filenames.setEnabled)
                                                )
        self.ui.rename_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.file_naming_format.setEnabled)
                                                )
        self.ui.rename_files.stateChanged.connect(partial(
                                                        enabledSlot,
                                                        self.ui.file_naming_format_default.setEnabled)
                                                )
        self.ui.file_naming_format.textChanged.connect(self.check_formats)
        self.ui.file_naming_format_default.clicked.connect(self.set_file_naming_format_default)
        self.highlighter = TaggerScriptSyntaxHighlighter(self.ui.file_naming_format.document())
        self.ui.move_files_to_browse.clicked.connect(self.move_files_to_browse)

    def check_formats(self):
        self.test()
        self.update_examples()

    def _example_to_filename(self, file):
        settings = {
            'windows_compatible_filenames': self.ui.windows_compatible_filenames.isChecked(),
            'ascii_filenames': self.ui.ascii_filenames.isChecked(),
            'rename_files': self.ui.rename_files.isChecked(),
            'move_files': self.ui.move_files.isChecked(),
            'use_va_format': False, # TODO remove
            'file_naming_format': unicode(self.ui.file_naming_format.toPlainText()),
            'move_files_to': os.path.normpath(unicode(self.ui.move_files_to.text()))
        }
        try:
            if config.setting["enable_tagger_script"]:
                script = config.setting["tagger_script"]
                parser = ScriptParser()
                parser.eval(script, file.metadata)
            filename = file._make_filename(file.filename, file.metadata, settings)
            if not settings["move_files"]:
                return os.path.basename(filename)
            return filename
        except SyntaxError, e: return ""
        except TypeError, e: return ""
        except UnknownFunction, e: return ""

    def update_examples(self):
        # TODO: Here should be more examples etc.
        # TODO: Would be nice to show diffs too....
        example1 = self._example_to_filename(self.example_1())
        example2 = self._example_to_filename(self.example_2())
        self.ui.example_filename.setText(example1)
        self.ui.example_filename_va.setText(example2)

    def load(self):
        if sys.platform == "win32":
            self.ui.windows_compatible_filenames.setChecked(True)
            self.ui.windows_compatible_filenames.setEnabled(False)
        else:
            self.ui.windows_compatible_filenames.setChecked(config.setting["windows_compatible_filenames"])
        self.ui.rename_files.setChecked(config.setting["rename_files"])
        self.ui.move_files.setChecked(config.setting["move_files"])
        self.ui.ascii_filenames.setChecked(config.setting["ascii_filenames"])
        self.ui.file_naming_format.setPlainText(config.setting["file_naming_format"])
        self.ui.move_files_to.setText(config.setting["move_files_to"])
        self.ui.move_files_to.setCursorPosition(0)
        self.ui.move_additional_files.setChecked(config.setting["move_additional_files"])
        self.ui.move_additional_files_pattern.setText(config.setting["move_additional_files_pattern"])
        self.ui.delete_empty_dirs.setChecked(config.setting["delete_empty_dirs"])
        self.update_examples()

    def check(self):
        self.check_format()
        if self.ui.move_files.isChecked() and not unicode(self.ui.move_files_to.text()).strip():
            raise OptionsCheckError(_("Error"), _("The location to move files to must not be empty."))

    def check_format(self):
        parser = ScriptParser()
        try:
            parser.eval(unicode(self.ui.file_naming_format.toPlainText()))
        except Exception, e:
            raise OptionsCheckError("", str(e))
        if self.ui.rename_files.isChecked():
            if not unicode(self.ui.file_naming_format.toPlainText()).strip():
                raise OptionsCheckError("", _("The file naming format must not be empty."))

    def save(self):
        config.setting["windows_compatible_filenames"] = self.ui.windows_compatible_filenames.isChecked()
        config.setting["ascii_filenames"] = self.ui.ascii_filenames.isChecked()
        config.setting["rename_files"] = self.ui.rename_files.isChecked()
        config.setting["file_naming_format"] = unicode(self.ui.file_naming_format.toPlainText())
        self.tagger.window.enable_renaming_action.setChecked(config.setting["rename_files"])
        config.setting["move_files"] = self.ui.move_files.isChecked()
        config.setting["move_files_to"] = os.path.normpath(unicode(self.ui.move_files_to.text()))
        config.setting["move_additional_files"] = self.ui.move_additional_files.isChecked()
        config.setting["move_additional_files_pattern"] = unicode(self.ui.move_additional_files_pattern.text())
        config.setting["delete_empty_dirs"] = self.ui.delete_empty_dirs.isChecked()
        self.tagger.window.enable_moving_action.setChecked(config.setting["move_files"])

    def display_error(self, error):
        pass

    def set_file_naming_format_default(self):
        self.ui.file_naming_format.setText(self.options[3].default)
#        self.ui.file_naming_format.setCursorPosition(0)

    def example_1(self):
        file = File("ticket_to_ride.mp3")
        file.state = File.NORMAL
        file.metadata['album'] = 'Help!'
        file.metadata['title'] = 'Ticket to Ride'
        file.metadata['artist'] = 'The Beatles'
        file.metadata['artistsort'] = 'Beatles, The'
        file.metadata['albumartist'] = 'The Beatles'
        file.metadata['albumartistsort'] = 'Beatles, The'
        file.metadata['tracknumber'] = '7'
        file.metadata['totaltracks'] = '14'
        file.metadata['discnumber'] = '1'
        file.metadata['totaldiscs'] = '1'
        file.metadata['date'] = '1965-08-06'
        file.metadata['releasetype'] = 'album'
        file.metadata['releasestatus'] = 'official'
        file.metadata['releasecountry'] = 'US'
        file.metadata['~extension'] = 'mp3'
        file.metadata['musicbrainz_albumid'] = '2c053984-4645-4699-9474-d2c35c227028'
        file.metadata['musicbrainz_albumartistid'] = 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d'
        file.metadata['musicbrainz_artistid'] = 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d'
        file.metadata['musicbrainz_trackid'] = '898a2916-f64d-48d3-ab1a-3446fb450448'
        return file

    def example_2(self):
        file = File("track05.mp3")
        file.state = File.NORMAL
        file.metadata['album'] = 'Explosive Doowops, Volume 4'
        file.metadata['title'] = 'Why? Oh Why?'
        file.metadata['artist'] = 'The Fantasys'
        file.metadata['artistsort'] = 'Fantasys, The'
        file.metadata['albumartist'] = config.setting['va_name']
        file.metadata['albumartistsort'] = config.setting['va_name']
        file.metadata['tracknumber'] = '5'
        file.metadata['totaltracks'] = '26'
        file.metadata['discnumber'] = '2'
        file.metadata['totaldiscs'] = '2'
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
        return file

    STYLESHEET_ERROR = "QWidget { background-color: #f55; color: white; font-weight:bold }"

    def move_files_to_browse(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, "", self.ui.move_files_to.text())
        if path:
            path = os.path.normpath(unicode(path))
            self.ui.move_files_to.setText(path)

    def test(self):
        self.ui.renaming_error.setStyleSheet("");
        self.ui.renaming_error.setText("")
        try:
            self.check_format()
        except OptionsCheckError, e:
            self.ui.renaming_error.setStyleSheet(self.STYLESHEET_ERROR);
            self.ui.renaming_error.setText(e.info)
            return

register_options_page(RenamingOptionsPage)
