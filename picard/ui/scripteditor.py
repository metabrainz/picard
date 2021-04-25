# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Laurent Monin
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
from PyQt5.QtGui import QPalette

from picard import log
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
    OptionsCheckError,
    ScriptCheckError,
)
from picard.ui.ui_scripteditor import Ui_ScriptEditor
from picard.ui.widgets.scriptdocumentation import ScriptingDocumentationWidget


PRESET_SCRIPTS = [
    {
        "title": N_("Current file naming script saved in configuration"),
        # Setting the script to None will force the current naming script from the configuration settings to be loaded.
        "script": None
    },
    {
        "title": N_("[Album artist]/[album]/[Track #]. [Title]"),
        "script": """\
%albumartist%/
%album%/
%tracknumber%. %title%"""
    },
    {
        "title": N_("[Album]/[Disc and track #] [Artist] - [Title]"),
        "script": """\
$if2(%albumartist%,%artist%)/
$if(%albumartist%,%album%/,)
$if($gt(%totaldiscs%,1),%discnumber%-,)
$if($and(%albumartist%,%tracknumber%),$num(%tracknumber%,2) ,)
$if(%_multiartist%,%artist% - ,)
%title%"""
    },
]


class ScriptEditorExamples():
    """File naming script examples.
    """
    max_samples = 10  # pick up to 10 samples
    notes_text = N_(
        "If you select files from the Cluster pane or Album pane prior to opening the Options screen, "
        "up to %u files will be randomly chosen from your selection as file naming examples.  If you "
        "have not selected any files, then some default examples will be provided.") % max_samples
    tooltip_text = N_("Reload up to %u items chosen at random from files selected in the main window") % max_samples

    def __init__(self, parent=None, tagger=None):
        """File naming script examples.

        Args:
            parent (QMainWindow or OptionsPage, optional): Parent object. Defaults to None.
            tagger (object, optional): Object containing the main window tagger object. Defaults to None.
        """
        self.tagger = tagger
        self._sampled_example_files = []
        config = get_config()
        self.settings = config.setting
        self.example_list = []

    def update_sample_example_files(self):
        """Get a new sample of randomly selected / loaded files to use as renaming examples.
        """
        import random
        if self.tagger.tagger.window.selected_objects:
            # If files/albums/tracks are selected, sample example files from them
            files = self.tagger.tagger.get_files_from_objects(self.tagger.tagger.window.selected_objects)
            length = min(self.max_samples, len(files))
            files = [file for file in random.sample(files, k=length)]
        else:
            # If files/albums/tracks are not selected, sample example files from the pool of loaded files
            files = self.tagger.tagger.files
            length = min(self.max_samples, len(files))
            files = [files[key] for key in random.sample(files.keys(), k=length)]

        if not files:
            # If no file has been loaded, use generic examples
            files = self.default_examples()
        self._sampled_example_files = files
        self.update_examples()

    def update_examples(self, override=None):
        """Update the before and after file naming examples list.

        Args:
            override (dict, optional): Dictionary of settings overrides to apply. Defaults to None.
        """
        if override and isinstance(override, dict):
            self.settings = SettingsOverride(self.settings, override)

        if self.settings["move_files"] or self.settings["rename_files"]:
            if not self._sampled_example_files:
                self.update_sample_example_files()
            self.example_list = [self._example_to_filename(example) for example in self._sampled_example_files]
        else:
            err_text = N_("Renaming options are disabled")
            self.example_list = [[err_text, err_text]]

    def _example_to_filename(self, file):
        """Produce the before and after file naming example tuple for the specified file.

        Args:
            file (File): File to produce example before and after names

        Returns:
            tuple: Example before and after names for the specified file
        """
        try:
            if self.settings["enable_tagger_scripts"]:
                for s_pos, s_name, s_enabled, s_text in self.settings["list_of_scripts"]:
                    if s_enabled and s_text:
                        parser = ScriptParser()
                        parser.eval(s_text, file.metadata)
            filename_before = file.filename
            filename_after = file.make_filename(filename_before, file.metadata, self.settings)
            if not self.settings["move_files"]:
                return os.path.basename(filename_before), os.path.basename(filename_after)
            return filename_before, filename_after
        except ScriptError:
            return "", ""
        except TypeError:
            return "", ""

    def get_examples(self):
        """Get the list of examples.

        Returns:
            [list]: List of the before and after file name example tuples
        """
        return self.example_list

    @staticmethod
    def default_examples():
        """List default example files.

        Returns:
            [list]: List of example File objects.
        """

        examples = []

        # example 1
        efile = File("ticket_to_ride.mp3")
        efile.state = File.NORMAL
        efile.metadata.update({
            'album': 'Help!',
            'title': 'Ticket to Ride',
            '~releasecomment': '2014 mono remaster',
            'artist': 'The Beatles',
            'artistsort': 'Beatles, The',
            'albumartist': 'The Beatles',
            'albumartistsort': 'Beatles, The',
            'tracknumber': '7',
            'totaltracks': '14',
            'discnumber': '1',
            'totaldiscs': '1',
            'originaldate': '1965-08-06',
            'originalyear': '1965',
            'date': '2014-09-08',
            'releasetype': ['album', 'soundtrack'],
            '~primaryreleasetype': ['album'],
            '~secondaryreleasetype': ['soundtrack'],
            'releasestatus': 'official',
            'releasecountry': 'US',
            '~extension': 'mp3',
            'musicbrainz_albumid': 'd7fbbb0a-1348-40ad-8eef-cd438d4cd203',
            'musicbrainz_albumartistid': 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d',
            'musicbrainz_artistid': 'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d',
            'musicbrainz_recordingid': 'ed052ae1-c950-47f2-8d2b-46e1b58ab76c',
            'musicbrainz_releasetrackid': '392639f5-5629-477e-b04b-93bffa703405',
        })
        examples.append(efile)

        # example 2
        config = get_config()
        efile = File("track05.mp3")
        efile.state = File.NORMAL
        efile.metadata.update({
            'album': "Coup d'État, Volume 1: Ku De Ta / Prologue",
            'title': "I've Got to Learn the Mambo",
            'artist': "Snowboy feat. James Hunter",
            'artistsort': "Snowboy feat. Hunter, James",
            'albumartist': config.setting['va_name'],
            'albumartistsort': config.setting['va_name'],
            'tracknumber': '5',
            'totaltracks': '13',
            'discnumber': '2',
            'totaldiscs': '2',
            'discsubtitle': "Beat Up",
            'originaldate': '2005-07-04',
            'originalyear': '2005',
            'date': '2005-07-04',
            'releasetype': ['album', 'compilation'],
            '~primaryreleasetype': 'album',
            '~secondaryreleasetype': 'compilation',
            'releasestatus': 'official',
            'releasecountry': 'AU',
            'compilation': '1',
            '~multiartist': '1',
            '~extension': 'mp3',
            'musicbrainz_albumid': '4b50c71e-0a07-46ac-82e4-cb85dc0c9bdd',
            'musicbrainz_recordingid': 'b3c487cb-0e55-477d-8df3-01ec6590f099',
            'musicbrainz_releasetrackid': 'f8649a05-da39-39ba-957c-7abf8f9012be',
            'musicbrainz_albumartistid': '89ad4ac3-39f7-470e-963a-56509c546377',
            'musicbrainz_artistid': ['7b593455-d207-482c-8c6f-19ce22c94679', '9e082466-2390-40d1-891e-4803531f43fd'],
        })
        examples.append(efile)

        return examples


class ScriptEditorPage(PicardDialog):
    """File Naming Script Editor Page
    """
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

    signal_save = QtCore.pyqtSignal()
    signal_update = QtCore.pyqtSignal()

    FILE_TYPE_ALL = N_("All Files") + " (*)"
    FILE_TYPE_SCRIPT = N_("Picard Script Files") + " (*.pts)"

    default_script_directory = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation))
    default_script_filename = "picard_naming_script.pts"

    def __init__(self, parent=None, examples=None):
        """Stand-alone file naming script editor.

        Args:
            parent (QMainWindow or OptionsPage, optional): Parent object. Defaults to None.
            examples (ScriptEditorExamples, required): Object containing examples to display. Defaults to None.
        """
        super().__init__(parent)
        self.examples = examples
        # TODO: Make this work properly so that it can be accessed from both the main window and the options window.
        # self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.ui = Ui_ScriptEditor()
        self.ui.setupUi(self)

        self.ui.example_filename_sample_files_button.setToolTip(self.examples.tooltip_text)

        self.installEventFilter(self)

        self.ui.file_naming_editor_save.clicked.connect(self.save_script)

        self.ui.file_naming_format.setEnabled(True)

        # Add scripting documentation to parent frame.
        doc_widget = ScriptingDocumentationWidget(self)
        self.ui.documentation_frame_layout.addWidget(doc_widget)
        self.ui.show_documentation.stateChanged.connect(self.toggle_documentation)

        self.ui.file_naming_format.textChanged.connect(self.check_formats)
        self.ui.file_naming_word_wrap.stateChanged.connect(self.toggle_wordwrap)
        self.ui.import_script.clicked.connect(self.import_script)
        self.ui.export_script.clicked.connect(self.export_script)

        self.ui.example_filename_sample_files_button.clicked.connect(self.update_example_files)
        self._sampled_example_files = []

        self.ui.example_filename_after.itemSelectionChanged.connect(self.match_before_to_after)
        self.ui.example_filename_before.itemSelectionChanged.connect(self.match_after_to_before)

        self.ui.preset_naming_scripts.clear()
        for item in PRESET_SCRIPTS:
            self.ui.preset_naming_scripts.addItem(item["title"])
        self.ui.preset_naming_scripts.setCurrentIndex(0)
        self.ui.preset_naming_scripts.currentIndexChanged.connect(self.select_script)

        self.synchronize_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

        self.current_row = -1

        self.load()

    @staticmethod
    def synchronize_vertical_scrollbars(widgets):
        """Synchronize position of vertical scrollbars and selections for listed widgets.
        """
        # Set highlight colors for selected list items
        example_style = widgets[0].palette()
        highlight_bg = example_style.color(QPalette.Active, QPalette.Highlight)
        highlight_fg = example_style.color(QPalette.Active, QPalette.HighlightedText)
        stylesheet = "QListView::item:selected { color: " + highlight_fg.name() + "; background-color: " + highlight_bg.name() + "; }"

        def _sync_scrollbar_vert(widget, value):
            widget.blockSignals(True)
            widget.verticalScrollBar().setValue(value)
            widget.blockSignals(False)

        widgets = set(widgets)
        for widget in widgets:
            for other in widgets - {widget}:
                widget.verticalScrollBar().valueChanged.connect(
                    partial(_sync_scrollbar_vert, other))

            widget.setStyleSheet(stylesheet)

    def eventFilter(self, object, event):
        """Process selected events.
        """
        if event.type() == QtCore.QEvent.WindowActivate or event.type() == QtCore.QEvent.FocusIn:
            self.update_examples()
        return False

    def toggle_documentation(self):
        """Toggle the display of the scripting documentation sidebar.
        """
        if self.ui.show_documentation.isChecked():
            self.ui.documentation_frame.show()
        else:
            self.ui.documentation_frame.hide()

    def select_script(self):
        """Set the current script from the combo box.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        selected_script = PRESET_SCRIPTS[selected]['script']
        if selected_script is None:
            config = get_config()
            self.set_script(config.setting['file_naming_format'])
        else:
            self.set_script(selected_script)
        self.update_examples()

    @staticmethod
    def synchronize_selected_example_lines(current_row, source, target):
        """Matches selected item in target to source"""
        if source.currentRow() != current_row:
            current_row = source.currentRow()
            target.blockSignals(True)
            target.setCurrentRow(current_row)
            target.blockSignals(False)

    def match_after_to_before(self):
        """Sets the selected item in the 'after' list to the corresponding item in the 'before' list.
        """
        self.synchronize_selected_example_lines(self.current_row, self.ui.example_filename_before, self.ui.example_filename_after)

    def match_before_to_after(self):
        """Sets the selected item in the 'before' list to the corresponding item in the 'after' list.
        """
        self.synchronize_selected_example_lines(self.current_row, self.ui.example_filename_after, self.ui.example_filename_before)

    def save_script(self):
        """Emits a `save` signal to trigger appropriate save action in the parent object.
        """
        self.signal_save.emit()

    def get_script(self):
        """Provides the text of the file naming script currently loaded into the editor.

        Returns:
            str: File naming script
        """
        return str(self.ui.file_naming_format.toPlainText()).strip()

    def set_script(self, script_text):
        """Sets the text of the file naming script into the editor.  Sets default text if `script_text` is empty or missing.

        Args:
            script_text (str): File naming script text to set in the editor.
        """
        self.ui.file_naming_format.setPlainText(str(script_text).strip())

    def update_example_files(self):
        """Update the before and after file naming examples list.
        """
        self.examples.update_sample_example_files()
        self.display_examples()

    def update_examples(self):
        """Update the before and after file naming examples using the current file naming script in the editor.
        """
        override = {'file_naming_format': self.get_script()}
        self.examples.update_examples(override)
        self.display_examples()

    @staticmethod
    def update_example_listboxes(before_listbox, after_listbox, examples):
        before_listbox.clear()
        after_listbox.clear()
        for before, after in sorted(examples, key=lambda x: x[1]):
            before_listbox.addItem(before)
            after_listbox.addItem(after)

    def display_examples(self, send_signal=True):
        """Update the display of the before and after file naming examples.  Optionally emits an `update` signal.

        Args:
            send_signal (bool, optional): Determines if an `update` signal is emitted. Defaults to True.
        """
        self.current_row = -1
        examples = self.examples.get_examples()
        self.update_example_listboxes(self.ui.example_filename_before, self.ui.example_filename_after, examples)

        if send_signal:
            self.signal_update.emit()

    def toggle_wordwrap(self):
        """Toggles wordwrap in the script editing textbox.
        """
        if self.ui.file_naming_word_wrap.isChecked():
            self.ui.file_naming_format.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        else:
            self.ui.file_naming_format.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

    def import_script(self):
        """Import the current script from an external text file.
        """
        dialog_title = N_("Import Script File")
        dialog_file_types = self.FILE_TYPE_SCRIPT + ";;" + self.FILE_TYPE_ALL
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, file_type = QtWidgets.QFileDialog.getOpenFileName(self, dialog_title, self.default_script_directory, dialog_file_types, options=options)
        if filename:
            log.debug('Importing naming script file: %s' % filename)
            try:
                with open(filename, 'r', encoding='utf8') as i_file:
                    self.set_script(i_file.read())
            except OSError as error:
                error_message = 'Error importing file "{0}": {1}'.format(filename, error.strerror)
                log.error(error_message)
                self.display_error(OptionsCheckError(N_("File Error"), error_message))

    def export_script(self):
        """Export the current script to an external text file.
        """
        script_text = self.get_script()
        if script_text:
            default_path = os.path.normpath(os.path.join(self.default_script_directory, self.default_script_filename))
            dialog_title = N_("Export Script File")
            dialog_file_types = self.FILE_TYPE_SCRIPT + ";;" + self.FILE_TYPE_ALL
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            filename, file_type = QtWidgets.QFileDialog.getSaveFileName(self, dialog_title, default_path, dialog_file_types, options=options)
            if filename:
                log.debug('Exporting naming script file: %s' % filename)
                try:
                    with open(filename, 'w', encoding='utf8') as o_file:
                        o_file.write(self.get_script() + '\n')
                except OSError as error:
                    error_message = 'Error exporting file "{0}": {1}'.format(filename, error.strerror)
                    log.error(error_message)
                    self.display_error(OptionsCheckError(N_("File Error"), error_message))

    def load(self):
        """Loads the file naming script from the configuration settings.
        """
        self.toggle_wordwrap()
        self.toggle_documentation()
        self.ui.preset_naming_scripts.blockSignals(True)
        self.ui.preset_naming_scripts.setCurrentIndex(0)
        self.ui.preset_naming_scripts.blockSignals(False)
        self.select_script()

    def check_formats(self):
        """Checks for valid file naming script and settings, and updates the examples.
        """
        self.test()
        self.update_examples()

    def check_format(self):
        """Parse the file naming script and check for errors.
        """
        config = get_config()
        parser = ScriptParser()
        script_text = self.get_script()
        try:
            parser.eval(script_text)
        except Exception as e:
            raise ScriptCheckError("", str(e))
        if config.setting["rename_files"]:
            if not self.get_script():
                raise ScriptCheckError("", _("The file naming format must not be empty."))

    def display_error(self, error):
        """Display an error message for the specified error.

        Args:
            error (Exception): The exception to display.
        """
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, error.title, error.info, QtWidgets.QMessageBox.Ok, self)
            dialog.exec_()

    def test(self):
        """Parse the script and display any errors.
        """
        self.ui.renaming_error.setStyleSheet("")
        self.ui.renaming_error.setText("")
        save_enabled = True
        try:
            self.check_format()
        except ScriptCheckError as e:
            self.ui.renaming_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.renaming_error.setText(e.info)
            save_enabled = False
        self.ui.file_naming_editor_save.setEnabled(save_enabled)
        self.ui.export_script.setEnabled(save_enabled)
