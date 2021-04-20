# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
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
from PyQt5.QtGui import QPalette

from picard import log
from picard.config import (
    TextOption,
    get_config,
)
from picard.const import (
    DEFAULT_FILE_NAMING_FORMAT,
    PICARD_URLS,
)
from picard.file import File
from picard.script import (
    ScriptError,
    ScriptParser,
    script_function_documentation_all,
)
from picard.util.settingsoverride import SettingsOverride

from picard.ui import (
    FONT_FAMILY_MONOSPACE,
    PicardDialog,
    SingletonDialog,
)
from picard.ui.options import OptionsPage
from picard.ui.options.scripting import (
    DOCUMENTATION_HTML_TEMPLATE,
    ScriptCheckError,
)
from picard.ui.theme import theme
from picard.ui.ui_scripteditor import Ui_ScriptEditor


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
    def __init__(self, parent=None, tagger=None):
        """File naming script examples.

        Args:
            parent (QMainWindow or OptionsPage, optional): Parent object. Defaults to None.
            tagger (object, optional): Object containing the main window tagger object. Defaults to None.
        """
        self.parent = parent
        self.tagger = tagger
        self._sampled_example_files = []
        config = get_config()
        self.settings = config.setting
        self.example_list = []

    def update_sample_example_files(self):
        """Get a new sample of randomly selected / loaded files to use as renaming examples.
        """
        import random
        max_samples = 10  # pick up to 10 samples
        if self.tagger.tagger.window.selected_objects:
            # If files/albums/tracks are selected, sample example files from them
            files = self.tagger.tagger.get_files_from_objects(self.tagger.tagger.window.selected_objects)
            length = min(max_samples, len(files))
            files = [file for file in random.sample(files, k=length)]
        else:
            # If files/albums/tracks are not selected, sample example files from the pool of loaded files
            files = self.tagger.tagger.files
            length = min(max_samples, len(files))
            files = [files[key] for key in random.sample(files.keys(), k=length)]

        if not files:
            # If no file has been loaded, use generic examples
            files = [self.example_1(), self.example_2()]
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
    def example_1():
        """First default example file.

        Returns:
            File: Default example file.
        """
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
        """Second default example file.

        Returns:
            File: Default example file.
        """
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


class ScriptEditorPage(PicardDialog, SingletonDialog):
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

    EMPTY_SCRIPT = '$noop( ' + N_('The script text is empty.') + ' )'

    def __init__(self, parent=None, examples=None):
        """Stand-alone file naming script editor.

        Args:
            parent (QMainWindow or OptionsPage, optional): Parent object. Defaults to None.
            examples (ScriptEditorExamples, required): Object containing examples to display. Defaults to None.
        """
        super().__init__(parent)
        self.PARENT = parent
        self.examples = examples
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.ui = Ui_ScriptEditor()
        self.ui.setupUi(self)

        self.installEventFilter(self)

        self.ui.file_naming_editor_save.clicked.connect(self.save_script)

        self.ui.file_naming_format.setEnabled(True)

        text = '<a href="' + PICARD_URLS['doc_scripting'] + '">' + N_('Open Scripting Documentation in your browser') + '</a>'
        self.ui.scripting_doc_link.setText(text)

        def process_html(html, function):
            if not html:
                html = ''
            template = '<dt>%s%s</dt><dd>%s</dd>'
            if function.module is not None and function.module != 'picard.script.functions':
                module = ' [' + function.module + ']'
            else:
                module = ''
            try:
                firstline, remaining = html.split("\n", 1)
                return template % (firstline, module, remaining)
            except ValueError:
                return template % ("<code>$%s()</code>" % function.name, module, html)

        funcdoc = script_function_documentation_all(
            fmt='html',
            postprocessor=process_html,
        )

        if self.ui.textBrowser.layoutDirection() == QtCore.Qt.RightToLeft:
            text_direction = 'rtl'
        else:
            text_direction = 'ltr'

        html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % funcdoc,
            'script_function_fg': theme.syntax_theme.func.name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }
        # Scripting code is always left-to-right. Qt does not support the dir
        # attribute on inline tags, insert explicit left-right-marks instead.
        html = html.replace('<code>', '<code>&#8206;')
        self.ui.textBrowser.setHtml(html)

        self.ui.textBrowser.show()
        self.ui.scripting_doc_link.show()
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

        def sync_vertical_scrollbars(widgets):
            """Sync position of vertical scrollbars for listed widgets.
            """
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

        # Set highlight colors for selected list items
        example_style = self.ui.example_filename_before.palette()
        highlight_bg = example_style.color(QPalette.Active, QPalette.Highlight)
        highlight_fg = example_style.color(QPalette.Active, QPalette.HighlightedText)
        stylesheet = "QListView::item:selected { color: " + highlight_fg.name() + "; background-color: " + highlight_bg.name() + "; }"
        self.ui.example_filename_after.setStyleSheet(stylesheet)
        self.ui.example_filename_before.setStyleSheet(stylesheet)

        self.wordwrap = QtWidgets.QTextEdit.NoWrap
        self.override = {}
        self.current_row = -1

        self.load()

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
        selected_script = self.ui.preset_naming_scripts.currentIndex()
        if PRESET_SCRIPTS[selected_script]['script'] is None:
            config = get_config()
            self.set_script(config.setting['file_naming_format'])
        else:
            self.set_script(PRESET_SCRIPTS[selected_script]['script'])
        self.update_examples()

    def synchronize_selected_example_lines(self, source, target):
        """Matches selected item in target to source"""
        if source.currentRow() != self.current_row:
            self.current_row = source.currentRow()
            target.blockSignals(True)
            target.setCurrentRow(self.current_row)
            target.blockSignals(False)

    def match_after_to_before(self):
        """Sets the selected item in the 'after' list to the corresponding item in the 'before' list.
        """
        self.synchronize_selected_example_lines(self.ui.example_filename_before, self.ui.example_filename_after)

    def match_before_to_after(self):
        """Sets the selected item in the 'before' list to the corresponding item in the 'after' list.
        """
        self.synchronize_selected_example_lines(self.ui.example_filename_after, self.ui.example_filename_before)

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

    def set_script(self, script_text=None):
        """Sets the text of the file naming script into the editor.  Sets default text if `script_text` is empty or missing.

        Args:
            script_text (str, optional): File naming script text to set in the editor. Defaults to None.
        """
        self.ui.file_naming_format.setPlainText(self.EMPTY_SCRIPT if not script_text else str(script_text).strip())

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

    def display_examples(self, send_signal=True):
        """Update the display of the before and after file naming examples.  Optionally emits an `update` signal.

        Args:
            send_signal (bool, optional): Determines if an `update` signal is emitted. Defaults to True.
        """
        self.ui.example_filename_before.clear()
        self.ui.example_filename_after.clear()
        self.current_row = -1

        examples = self.examples.get_examples()
        for before, after in sorted(examples, key=lambda x: x[1]):
            self.ui.example_filename_before.addItem(before)
            self.ui.example_filename_after.addItem(after)

        if send_signal:
            self.signal_update.emit()

    def toggle_wordwrap(self):
        """Toggles wordwrap in the script editing textbox.
        """
        if self.ui.file_naming_word_wrap.isChecked():
            self.wordwrap = QtWidgets.QTextEdit.WidgetWidth
        else:
            self.wordwrap = QtWidgets.QTextEdit.NoWrap
        self.ui.file_naming_format.setLineWrapMode(self.wordwrap)

    def import_script(self):
        """Import the current script from an external text file.
        """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Script File", "", "All Files (*);;Picard Script Files (*.pts)", options=options)
        if filename:
            log.debug('Importing naming script file: %s' % filename)
            file_text = ""
            try:
                with open(filename, 'r', encoding='utf8') as i_file:
                    file_text = i_file.read().strip()
            except OSError as error:
                self.display_error(error)
                return
            if not file_text:
                file_text = None
            self.set_script(file_text)

    def export_script(self):
        """Export the current script to an external text file.
        """
        script_text = self.get_script()
        if script_text:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Script File", "picard_naming_script.pts", "All Files (*);;Picard Script Files (*.pts)", options=options)
            if filename:
                log.debug('Exporting naming script file: %s' % filename)
                try:
                    with open(filename, 'w', encoding='utf8') as o_file:
                        o_file.write(self.get_script() + '\n')
                except OSError as error:
                    self.display_error(error)
                    return

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
            super().display_error(error)

    def test(self):
        """Parse the script and display any errors.
        """
        self.ui.renaming_error.setStyleSheet("")
        self.ui.renaming_error.setText("")
        try:
            self.check_format()
        except ScriptCheckError as e:
            self.ui.renaming_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.renaming_error.setText(e.info)
            return
