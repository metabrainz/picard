# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2014-2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2011-2013 Wieland Hoffmann
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2015, 2018-2019, 2021 Laurent Monin
# Copyright (C) 2015 Alex Berman
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Bob Swift
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


from functools import partial
import os.path

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.config import (
    TextOption,
    get_config,
)
from picard.const import DEFAULT_FILE_NAMING_FORMAT
from picard.file import File
from picard.script import (
    ScriptError,
    ScriptParser,
)
from picard.util.settingsoverride import SettingsOverride

from picard.ui import PicardDialog
from picard.ui.options import OptionsPage
from picard.ui.options.scripting import (
    ScriptCheckError,
    ScriptingDocumentationDialog,
)
from picard.ui.ui_scripteditor import Ui_ScriptEditor


PRESET_SCRIPTS = [
    {
        "title": N_("- please select an item -"),
        "script": ""
    },
    {
        "title": N_("album artist / album / track #. title"),
        "script": """\
%albumartist%/
%album%/
%tracknumber%. %title%"""
    },
    {
        "title": N_("album / track #. artist - title"),
        "script": """\
$if2(%albumartist%,%artist%)/
$if(%albumartist%,%album%/,)
$if($gt(%totaldiscs%,1),%discnumber%-,)
$if($and(%albumartist%,%tracknumber%),$num(%tracknumber%,2) ,)
$if(%_multiartist%,%artist% - ,)
%title%"""
    },
]

class ScriptEditorPage(PicardDialog):

    NAME = "scripteditor"
    TITLE = N_("File naming script editor")
    PARENT = None
    HELP_URL = '/config/options_filerenaming.html'
    STYLESHEET_ERROR = OptionsPage.STYLESHEET_ERROR

    options = [
        TextOption(
            "setting",
            "file_naming_format",
            DEFAULT_FILE_NAMING_FORMAT,
        ),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.PARENT = parent
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.ui = Ui_ScriptEditor()
        self.ui.setupUi(self)

        self.installEventFilter(self)

        self.ui.file_naming_editor_save.clicked.connect(self.save_script)

        self.ui.file_naming_format.setEnabled(True)
        self.ui.file_naming_format_reload.setEnabled(True)

        self.ui.file_naming_format.textChanged.connect(self.check_formats)
        self.ui.file_naming_format_reload.clicked.connect(self.load)
        self.ui.file_naming_word_wrap.stateChanged.connect(self.toggle_wordwrap)

        self.ui.scripting_documentation_button.clicked.connect(self.show_scripting_documentation)
        self.ui.example_filename_sample_files_button.clicked.connect(self._sample_example_files)
        self._sampled_example_files = []

        self.ui.example_filename_after.itemSelectionChanged.connect(self.match_before_to_after)
        self.ui.example_filename_before.itemSelectionChanged.connect(self.match_after_to_before)

        self.ui.preset_naming_scripts.clear()
        for item in PRESET_SCRIPTS:
            self.ui.preset_naming_scripts.addItem(item["title"])
        self.ui.preset_naming_script_select.clicked.connect(self.select_preset_script)

        # Sync example lists vertical scrolling
        def sync_vertical_scrollbars(widgets):
            """Sync position of vertical scrollbars for listed widgets"""
            def _sync_scrollbar_vert(widget, value):
                widget.blockSignals(True)
                widget.verticalScrollBar().setValue(value)
                widget.blockSignals(False)

            widgets = set(widgets)
            for widget in widgets:
                for other in widgets - {widget}:
                    widget.verticalScrollBar().valueChanged.connect(
                        partial(_sync_scrollbar_vert, other))

        # Sync example lists vertical scrolling
        sync_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

        self.wordwrap = QtWidgets.QTextEdit.NoWrap
        self.current_row = -1

        self.load()

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.WindowActivate or event.type() == QtCore.QEvent.FocusIn:
            self._sample_example_files()
            self.load()
        return False

    def select_preset_script(self):
        selected_script = self.ui.preset_naming_scripts.currentIndex()
        if selected_script > 0:
            self.ui.file_naming_format.setPlainText(PRESET_SCRIPTS[selected_script]['script'])
            self.update_examples()

    def match_after_to_before(self):
        if self.ui.example_filename_before.currentRow() != self.current_row:
            self.current_row = self.ui.example_filename_before.currentRow()
            self.ui.example_filename_after.setCurrentRow(self.current_row)

    def match_before_to_after(self):
        if self.ui.example_filename_after.currentRow() != self.current_row:
            self.current_row = self.ui.example_filename_after.currentRow()
            self.ui.example_filename_before.setCurrentRow(self.current_row)

    def save_script(self):
        config = get_config()
        config.setting["file_naming_format"] = self.ui.file_naming_format.toPlainText()

    def show_scripting_documentation(self):
        ScriptingDocumentationDialog.show_instance(parent=self)

    def check_formats(self):
        self.test()
        self.update_examples()

    def _example_to_filename(self, file):
        config = get_config()
        settings = SettingsOverride(config.setting, {
            'file_naming_format': self.ui.file_naming_format.toPlainText(),
        })

        try:
            if config.setting["enable_tagger_scripts"]:
                for s_pos, s_name, s_enabled, s_text in config.setting["list_of_scripts"]:
                    if s_enabled and s_text:
                        parser = ScriptParser()
                        parser.eval(s_text, file.metadata)
            filename_before = file.filename
            filename_after = file.make_filename(filename_before, file.metadata, settings)
            if not settings["move_files"]:
                return os.path.basename(filename_before), os.path.basename(filename_after)
            return filename_before, filename_after
        except ScriptError:
            return "", ""
        except TypeError:
            return "", ""

    def _sample_example_files(self):
        # Get a new sample of randomly selected /loaded files to use as renaming examples
        import random
        max_samples = 10  # pick up to 10 samples
        if self.PARENT.selected_objects:
            # If files/albums/tracks are selected, sample example files from them
            files = self.PARENT.tagger.get_files_from_objects(self.PARENT.selected_objects)
            length = min(max_samples, len(files))
            files = [file for file in random.sample(files, k=length)]
        else:
            # If files/albums/tracks are not selected, sample example files from the pool of loaded files
            files = self.PARENT.tagger.files
            length = min(max_samples, len(files))
            files = [files[key] for key in random.sample(files.keys(), k=length)]

        if not files:
            # If no file has been loaded, use generic examples
            files = [self.example_1(), self.example_2()]
        self._sampled_example_files = files
        self.update_examples()

    def update_examples(self):
        config = get_config()
        self.ui.example_filename_before.clear()
        self.ui.example_filename_after.clear()
        self.current_row = -1

        if config.setting["move_files"] or config.setting["rename_files"]:
            if not self._sampled_example_files:
                self._sample_example_files()
            example_files = self._sampled_example_files

            examples = [self._example_to_filename(example) for example in example_files]
            for before, after in sorted(examples, key=lambda x: x[1]):
                self.ui.example_filename_before.addItem(before)
                self.ui.example_filename_after.addItem(after)
        else:
            err_text = N_("Renaming options are disabled")
            self.ui.example_filename_before.addItem(err_text)
            self.ui.example_filename_after.addItem(err_text)

    def toggle_wordwrap(self):
        if self.ui.file_naming_word_wrap.isChecked():
            self.wordwrap = QtWidgets.QTextEdit.WidgetWidth
        else:
            self.wordwrap = QtWidgets.QTextEdit.NoWrap
        self.ui.file_naming_format.setLineWrapMode(self.wordwrap)

    def load(self):
        config = get_config()
        self.toggle_wordwrap()
        self.ui.file_naming_format.setPlainText(config.setting["file_naming_format"])
        self.update_examples()

    def check(self):
        self.check_format()

    def check_format(self):
        config = get_config()
        parser = ScriptParser()
        try:
            parser.eval(self.ui.file_naming_format.toPlainText())
        except Exception as e:
            raise ScriptCheckError("", str(e))
        if config.setting["rename_files"]:
            if not self.ui.file_naming_format.toPlainText().strip():
                raise ScriptCheckError("", _("The file naming format must not be empty."))

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)

    def test(self):
        self.ui.renaming_error.setStyleSheet("")
        self.ui.renaming_error.setText("")
        try:
            self.check_format()
        except ScriptCheckError as e:
            self.ui.renaming_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.renaming_error.setText(e.info)
            return

    @staticmethod
    def example_1():
        file = File("ticket_to_ride.mp3")
        file.state = File.NORMAL
        file.metadata['album'] = 'Help!'
        file.metadata['title'] = 'Ticket to Ride'
        file.metadata['~releasecomment'] = '2014 mono remaster'
        file.metadata['artist'] = 'The Beatles'
        file.metadata['artistsort'] = 'Beatles, The'
        file.metadata['albumartist'] = 'The Beatles'
        file.metadata['albumartistsort'] = 'Beatles, The'
        file.metadata['tracknumber'] = '7'
        file.metadata['totaltracks'] = '14'
        file.metadata['discnumber'] = '1'
        file.metadata['totaldiscs'] = '1'
        file.metadata['originaldate'] = '1965-08-06'
        file.metadata['originalyear'] = '1965'
        file.metadata['date'] = '2014-09-08'
        file.metadata['releasetype'] = ['album', 'soundtrack']
        file.metadata['~primaryreleasetype'] = ['album']
        file.metadata['~secondaryreleasetype'] = ['soundtrack']
        file.metadata['releasestatus'] = 'official'
        file.metadata['releasecountry'] = 'US'
        file.metadata['~extension'] = 'mp3'
        file.metadata['musicbrainz_albumid'] = 'd7fbbb0a-1348-40ad-8eef-cd438d4cd203'
        file.metadata['musicbrainz_albumartistid'] = 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d'
        file.metadata['musicbrainz_artistid'] = 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d'
        file.metadata['musicbrainz_recordingid'] = 'ed052ae1-c950-47f2-8d2b-46e1b58ab76c'
        file.metadata['musicbrainz_releasetrackid'] = '392639f5-5629-477e-b04b-93bffa703405'
        return file

    @staticmethod
    def example_2():
        config = get_config()
        file = File("track05.mp3")
        file.state = File.NORMAL
        file.metadata['album'] = "Coup d'État, Volume 1: Ku De Ta / Prologue"
        file.metadata['title'] = "I've Got to Learn the Mambo"
        file.metadata['artist'] = "Snowboy feat. James Hunter"
        file.metadata['artistsort'] = "Snowboy feat. Hunter, James"
        file.metadata['albumartist'] = config.setting['va_name']
        file.metadata['albumartistsort'] = config.setting['va_name']
        file.metadata['tracknumber'] = '5'
        file.metadata['totaltracks'] = '13'
        file.metadata['discnumber'] = '2'
        file.metadata['totaldiscs'] = '2'
        file.metadata['discsubtitle'] = "Beat Up"
        file.metadata['originaldate'] = '2005-07-04'
        file.metadata['originalyear'] = '2005'
        file.metadata['date'] = '2005-07-04'
        file.metadata['releasetype'] = ['album', 'compilation']
        file.metadata['~primaryreleasetype'] = 'album'
        file.metadata['~secondaryreleasetype'] = 'compilation'
        file.metadata['releasestatus'] = 'official'
        file.metadata['releasecountry'] = 'AU'
        file.metadata['compilation'] = '1'
        file.metadata['~multiartist'] = '1'
        file.metadata['~extension'] = 'mp3'
        file.metadata['musicbrainz_albumid'] = '4b50c71e-0a07-46ac-82e4-cb85dc0c9bdd'
        file.metadata['musicbrainz_recordingid'] = 'b3c487cb-0e55-477d-8df3-01ec6590f099'
        file.metadata['musicbrainz_releasetrackid'] = 'f8649a05-da39-39ba-957c-7abf8f9012be'
        file.metadata['musicbrainz_albumartistid'] = '89ad4ac3-39f7-470e-963a-56509c546377'
        file.metadata['musicbrainz_artistid'] = ['7b593455-d207-482c-8c6f-19ce22c94679',
                                                    '9e082466-2390-40d1-891e-4803531f43fd']
        return file
