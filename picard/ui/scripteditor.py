# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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
from json.decoder import JSONDecodeError
import os.path

from PyQt5 import (
    QtCore,
    QtWidgets,
)
from PyQt5.QtGui import QPalette

from picard import log
from picard.config import (
    ListOption,
    TextOption,
    get_config,
)
from picard.const import DEFAULT_FILE_NAMING_FORMAT
from picard.file import File
from picard.script import (
    FileNamingScript,
    ScriptError,
    ScriptParser,
    get_file_naming_script_presets,
)
from picard.util.settingsoverride import SettingsOverride

from picard.ui import PicardDialog
from picard.ui.options import OptionsPage
from picard.ui.options.scripting import (
    OptionsCheckError,
    ScriptCheckError,
)
from picard.ui.ui_scripteditor import Ui_ScriptEditor
from picard.ui.ui_scripteditor_details import Ui_ScriptDetails
from picard.ui.widgets.scriptdocumentation import ScriptingDocumentationWidget


class ScriptImportError(OptionsCheckError):
    pass


class ScriptExportError(OptionsCheckError):
    pass


class ScriptEditorExamples():
    """File naming script examples.
    """
    max_samples = 10  # pick up to 10 samples
    notes_text = N_(
        "If you select files from the Cluster pane or Album pane prior to opening the Options screen, "
        "up to %u files will be randomly chosen from your selection as file naming examples.  If you "
        "have not selected any files, then some default examples will be provided.")
    tooltip_text = N_("Reload up to %u items chosen at random from files selected in the main window")

    def __init__(self, tagger):
        """File naming script examples.

        Args:
            tagger (object): The main window tagger object.
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
        if self.tagger.window.selected_objects:
            # If files/albums/tracks are selected, sample example files from them
            files = self.tagger.get_files_from_objects(self.tagger.window.selected_objects)
            length = min(self.max_samples, len(files))
            files = [file for file in random.sample(files, k=length)]
        else:
            # If files/albums/tracks are not selected, sample example files from the pool of loaded files
            files = self.tagger.files
            length = min(self.max_samples, len(files))
            files = [files[key] for key in random.sample(files.keys(), k=length)]

        if not files:
            # If no file has been loaded, use generic examples
            files = list(self.default_examples())
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
            err_text = _("Renaming options are disabled")
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
        """Generator for default example files.

        Yields:
            File: the next example File object
        """
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
        yield efile

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
        yield efile


class ScriptEditorPage(PicardDialog):
    """File Naming Script Editor Page
    """
    TITLE = N_("File naming script editor")
    STYLESHEET_ERROR = OptionsPage.STYLESHEET_ERROR

    options = [
        TextOption(
            "setting",
            "file_naming_format",
            DEFAULT_FILE_NAMING_FORMAT,
        ),
        ListOption(
            "setting",
            "file_naming_scripts",
            [],
        ),
    ]

    FILE_ERROR_IMPORT = N_('Error importing "%s". %s.')
    FILE_ERROR_DECODE = N_('Error decoding "%s". %s.')
    FILE_ERROR_EXPORT = N_('Error exporting file "%s". %s.')

    signal_save = QtCore.pyqtSignal()
    signal_update = QtCore.pyqtSignal()

    default_script_directory = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation))
    default_script_filename = "picard_naming_script.pnsp"

    def __init__(self, parent=None, examples=None):
        """Stand-alone file naming script editor.

        Args:
            parent (QMainWindow or OptionsPage, optional): Parent object. Defaults to None.
            examples (ScriptEditorExamples, required): Object containing examples to display. Defaults to None.
        """
        super().__init__(parent)
        self.examples = examples

        self.FILE_TYPE_ALL = _("All Files") + " (*)"
        self.FILE_TYPE_SCRIPT = _("Picard Script Files") + " (*.pts *.txt)"
        self.FILE_TYPE_PACKAGE = _("Picard Naming Script Package") + " (*.pnsp *.json)"

        self.SCRIPT_TITLE_SYSTEM = _("System: %s")
        self.SCRIPT_TITLE_USER = _("User: %s")

        # TODO: Make this work properly so that it can be accessed from both the main window and the options window.
        # self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.ui = Ui_ScriptEditor()
        self.ui.setupUi(self)

        self.ui.example_filename_sample_files_button.setToolTip(_(self.examples.tooltip_text) % self.examples.max_samples)

        self.installEventFilter(self)

        self.ui.file_naming_editor_new.clicked.connect(self.new_script)
        self.ui.file_naming_editor_save.clicked.connect(self.save_script)
        self.ui.file_naming_editor_copy.clicked.connect(self.copy_script)
        self.ui.file_naming_editor_select.clicked.connect(self.save_selected_script)
        self.ui.file_naming_editor_delete.clicked.connect(self.delete_script)
        self.ui.script_details.clicked.connect(self.view_script_details)

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

        config = get_config()
        self.naming_scripts = config.setting["file_naming_scripts"]
        self.populate_script_selector()
        self.ui.preset_naming_scripts.setCurrentIndex(0)
        self.ui.preset_naming_scripts.currentIndexChanged.connect(self.select_script)
        self.select_script()

        self.synchronize_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

        self.wordwrap = QtWidgets.QTextEdit.NoWrap
        self.examples_current_row = -1

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
        evtype = event.type()
        if evtype in {QtCore.QEvent.WindowActivate, QtCore.QEvent.FocusIn}:
            self.update_examples()
        return False

    def populate_script_selector(self):
        """Populate the script selection combo box.
        """
        self.ui.preset_naming_scripts.blockSignals(True)
        self.ui.preset_naming_scripts.clear()
        script_item = FileNamingScript(
            script=get_config().setting["file_naming_format"],
            title=_("Current file naming script saved in configuration"),
            readonly=False,
            deletable=False,
            id="current"
        )
        self.set_script(script_item.script)
        self.ui.preset_naming_scripts.addItem(self.SCRIPT_TITLE_SYSTEM % script_item.title, script_item)

        for script_json in self.naming_scripts:
            script_item = FileNamingScript().create_from_json(script_json)
            if script_item.get_value('title'):
                self.ui.preset_naming_scripts.addItem(self.SCRIPT_TITLE_USER % script_item.title, script_item)

        for script_item in get_file_naming_script_presets():
            title = script_item.title
            self.ui.preset_naming_scripts.addItem(title, script_item)

        self.ui.preset_naming_scripts.blockSignals(False)

    def toggle_documentation(self):
        """Toggle the display of the scripting documentation sidebar.
        """
        self.ui.documentation_frame.setVisible(self.ui.show_documentation.isChecked())

    def view_script_details(self):
        """View and edit (if not readonly) the metadata associated with the script.
        """
        selected_item = self.get_selected_item()
        details_page = ScriptDetailsEditor(self, selected_item)
        details_page.signal_save.connect(self.update_from_details)
        details_page.show()
        details_page.raise_()
        details_page.activateWindow()

    def update_from_details(self):
        """Update the script selection combo box and script list after updates from the script details dialog.
        """
        selected_item = self.get_selected_item()
        self.update_combo_box_item(self.ui.preset_naming_scripts.currentIndex(), selected_item)
        self.ui.script_title.setText(selected_item.get_value('title'))

    def _insert_item(self, script_item):
        """Insert a new item into the script selection combo box and update the script list in the settings.

        Args:
            script_item (FileNamingScript): File naming scrip to insert.
        """
        self.ui.preset_naming_scripts.blockSignals(True)
        self.ui.preset_naming_scripts.insertItem(1, self.SCRIPT_TITLE_USER % script_item.title, script_item)
        self.ui.preset_naming_scripts.setCurrentIndex(1)
        self.ui.preset_naming_scripts.blockSignals(False)
        self.update_scripts_list()
        self.select_script()

    def new_script(self):
        """Add a new (empty) script to the script selection combo box and script list.
        """
        script_item = FileNamingScript(script='$noop()')
        self._insert_item(script_item)

    def copy_script(self):
        """Add a copy of the script as a new editable script to the script selection combo box and script list.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        script_item = self.ui.preset_naming_scripts.itemData(selected)
        new_item = script_item.copy()
        self._insert_item(new_item)

    def update_scripts_list(self):
        """Refresh the script list in the settings based on the contents of the script selection combo box.
        """
        self.naming_scripts = []
        for idx in range(self.ui.preset_naming_scripts.count()):
            script_item = self.ui.preset_naming_scripts.itemData(idx)
            # Only add items that can be removed -- no presets or the current file naming script
            if script_item.deletable:
                self.naming_scripts.append(script_item.to_json())
        config = get_config()
        config.setting["file_naming_scripts"] = self.naming_scripts

    def get_selected_item(self):
        """Get the selected item from the script selection combo box.

        Returns:
            FileNamingScript: The selected script.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        return self.ui.preset_naming_scripts.itemData(selected)

    def select_script(self):
        """Load the current script from the combo box into the editor.
        """
        script_item = self.get_selected_item()
        self.ui.script_title.setText(str(script_item.title).strip())
        self.set_script(script_item.script)
        self.set_button_states()
        self.update_examples()

    def update_combo_box_item(self, idx, script_item):
        """Update the title and item data for the specified script selection combo box item.

        Args:
            idx (int): Index of the item to update
            script_item (FileNamingScript): Updated script information
        """
        self.ui.preset_naming_scripts.setItemData(idx, script_item)
        self.ui.preset_naming_scripts.setItemText(idx, self.SCRIPT_TITLE_USER % script_item.get_value('title'))

    def set_button_states(self, save_enabled=True):
        """Set the button states based on the readonly and deletable attributes of the currently selected
        item in the script selection combo box.

        Args:
            save_enabled (bool, optional): Allow updates to be saved to this item. Defaults to True.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        if selected < 0:
            return
        script_item = self.get_selected_item()
        self.ui.script_title.setReadOnly(script_item.readonly or selected < 1)
        self.ui.file_naming_format.setReadOnly(script_item.readonly)
        self.ui.file_naming_editor_save.setEnabled(save_enabled and not script_item.readonly)
        self.ui.file_naming_editor_copy.setEnabled(save_enabled)
        self.ui.file_naming_editor_select.setEnabled(save_enabled)
        self.ui.file_naming_editor_delete.setEnabled(script_item.deletable and save_enabled)
        self.ui.import_script.setEnabled(save_enabled)
        self.ui.export_script.setEnabled(save_enabled)

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
        self.synchronize_selected_example_lines(self.examples_current_row, self.ui.example_filename_before, self.ui.example_filename_after)

    def match_before_to_after(self):
        """Sets the selected item in the 'before' list to the corresponding item in the 'after' list.
        """
        self.synchronize_selected_example_lines(self.examples_current_row, self.ui.example_filename_after, self.ui.example_filename_before)

    def delete_script(self):
        """Removes the currently selected script from the script selection combo box and script list.
        """
        if self.confirmation_dialog(_('Are you sure that you want to delete the script?')):
            idx = self.ui.preset_naming_scripts.currentIndex()
            self.ui.preset_naming_scripts.blockSignals(True)
            self.ui.preset_naming_scripts.removeItem(idx)
            self.ui.preset_naming_scripts.setCurrentIndex(0)
            self.ui.preset_naming_scripts.blockSignals(False)
            self.update_scripts_list()
            self.select_script()

    def save_script(self):
        """Saves changes to the current script to the script list and combo box item.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        if selected == 0:
            self.signal_save.emit()
        else:
            title = str(self.ui.script_title.text()).strip()
            if title:
                script_item = self.ui.preset_naming_scripts.itemData(selected)
                script_item.title = title
                script_item.script = self.get_script()
                self.ui.preset_naming_scripts.setItemData(selected, script_item)
                self.ui.preset_naming_scripts.setItemText(selected, title)
                self.update_scripts_list()
            else:
                self.display_error(OptionsCheckError(_("Error"), _("The script title must not be empty.")))

    def save_selected_script(self):
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
        """Sets the text of the file naming script into the editor.

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
        """Update the contents of the file naming examples before and after listboxes.

        Args:
            before_listbox (QListBox): The before listbox
            after_listbox (QListBox): The after listbox
            examples (ScriptEditorExamples): The object to use for the examples
        """
        before_listbox.clear()
        after_listbox.clear()
        for before, after in sorted(examples, key=lambda x: x[1]):
            before_listbox.addItem(before)
            after_listbox.addItem(after)

    def display_examples(self):
        """Update the display of the before and after file naming examples.
        """
        self.examples_current_row = -1
        examples = self.examples.get_examples()
        self.update_example_listboxes(self.ui.example_filename_before, self.ui.example_filename_after, examples)
        self.signal_update.emit()

    def toggle_wordwrap(self):
        """Toggles wordwrap in the script editing textbox.
        """
        if self.ui.file_naming_word_wrap.isChecked():
            self.ui.file_naming_format.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        else:
            self.ui.file_naming_format.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

    def output_error(self, title, fmt, filename, msg):
        """Log error and display error message dialog.

        Args:
            title (str): Title to display on the error dialog box
            fmt (str): Format for the error type being displayed
            filename (str): Name of the file being imported or exported
            msg (str): Error message to display
        """
        log.error(fmt, filename, msg)
        error_message = _(fmt) % (filename, _(msg))
        self.display_error(ScriptImportError(_(title), error_message))

    def output_file_error(self, fmt, filename, msg):
        """Log file error and display error message dialog.

        Args:
            fmt (str): Format for the error type being displayed
            filename (str): Name of the file being imported or exported
            msg (str): Error message to display
        """
        self.output_error(_("File Error"), fmt, filename, msg)

    def import_script(self):
        """Import from an external text file to a new script. Import can be either a plain text script or
        a naming script package.
        """

        dialog_title = _("Import Script File")
        dialog_file_types = self.FILE_TYPE_PACKAGE + ";;" + self.FILE_TYPE_SCRIPT + ";;" + self.FILE_TYPE_ALL
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, file_type = QtWidgets.QFileDialog.getOpenFileName(self, dialog_title, self.default_script_directory, dialog_file_types, options=options)
        if filename:
            log.debug('Importing naming script file: %s' % filename)
            try:
                with open(filename, 'r', encoding='utf8') as i_file:
                    file_content = i_file.read()
            except OSError as error:
                self.output_file_error(self.FILE_ERROR_IMPORT, filename, error.strerror)
                return
            if not file_content.strip():
                self.output_file_error(self.FILE_ERROR_IMPORT, filename, N_('The file was empty'))
                return
            if file_type == self.FILE_TYPE_PACKAGE:
                try:
                    script_item = FileNamingScript().create_from_json(file_content)
                except JSONDecodeError as error:
                    self.output_file_error(self.FILE_ERROR_DECODE, filename, error.msg)
                    return
                if not (script_item.get_value('title') and script_item.get_value('script')):
                    self.output_file_error(self.FILE_ERROR_DECODE, filename, N_('Invalid script package'))
                    return
            else:
                script_item = FileNamingScript(
                    title=_("Imported from ") + filename,
                    script=file_content.strip()
                )
            self._insert_item(script_item)

    def export_script(self):
        """Export the current script to an external file. Export can be either as a plain text
        script or a naming script package.
        """
        script_item = self.get_selected_item()
        script_text = self.get_script()

        if script_text:
            default_path = os.path.normpath(os.path.join(self.default_script_directory, self.default_script_filename))
            dialog_title = _("Export Script File")
            dialog_file_types = self.FILE_TYPE_PACKAGE + ";;" + self.FILE_TYPE_SCRIPT + ";;" + self.FILE_TYPE_ALL
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            filename, file_type = QtWidgets.QFileDialog.getSaveFileName(self, dialog_title, default_path, dialog_file_types, options=options)
            if filename:
                # Fix issue where Qt may set the extension twice
                (name, ext) = os.path.splitext(filename)
                if ext and str(name).endswith('.' + ext):
                    filename = name
                log.debug('Exporting naming script file: %s' % filename)
                if file_type == self.FILE_TYPE_PACKAGE:
                    script_text = script_item.to_json(indent=4)
                try:
                    with open(filename, 'w', encoding='utf8') as o_file:
                        o_file.write(script_text + '\n')
                except OSError as error:
                    self.output_file_error(self.FILE_ERROR_EXPORT, filename, error.strerror)
                else:
                    dialog = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Information,
                        _("Export Script"),
                        _("Script successfully exported to ") + filename,
                        QtWidgets.QMessageBox.Ok,
                        self
                    )
                    dialog.exec_()

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

    def confirmation_dialog(self, message_text):
        """Display a confirmation dialog with Ok and Cancel buttons.

        Args:
            message_text (str): Message to display

        Returns:
            bool: True if Ok, otherwise False
        """
        dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                       _('Confirm'),
                                       message_text,
                                       QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                                       self
                                       )
        return dialog.exec_() == QtWidgets.QMessageBox.Ok

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
        self.set_button_states(save_enabled=save_enabled)


class ScriptDetailsEditor(PicardDialog):
    """View / edit the metadata details for a script.
    """
    NAME = 'scriptdetails'
    TITLE = N_('Script Details')

    signal_save = QtCore.pyqtSignal()

    def __init__(self, parent, script_item):
        """Script metadata viewer / editor.

        Args:
            parent (ScriptEditorPage): The page used for editing the scripts
            script_item (FileNamingScript): The script whose metadata is displayed
        """
        super().__init__(parent=parent)
        self.script_item = script_item
        self.readonly = script_item.readonly
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.ui = Ui_ScriptDetails()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.connect(self.save_changes)
        self.ui.buttonBox.rejected.connect(self.close_window)
        self.ui.last_updated_now.clicked.connect(self.set_last_updated)

        self.ui.script_title.setText(self.script_item.get_value('title'))
        self.ui.script_author.setText(self.script_item.get_value('author'))
        self.ui.script_version.setText(self.script_item.get_value('version'))
        self.ui.script_last_updated.setText(self.script_item.get_value('last_updated'))
        self.ui.script_license.setText(self.script_item.get_value('license'))
        self.ui.script_description.setPlainText(self.script_item.get_value('description'))

        self.ui.script_last_updated.setReadOnly(self.readonly)
        self.ui.script_author.setReadOnly(self.readonly)
        self.ui.script_version.setReadOnly(self.readonly)
        self.ui.script_license.setReadOnly(self.readonly)
        self.ui.script_description.setReadOnly(self.readonly)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setVisible(self.readonly)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setVisible(not self.readonly)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setVisible(not self.readonly)
        self.ui.buttonBox.setFocus()

        self.setModal(True)

    def set_last_updated(self):
        self.ui.script_last_updated.setText(self.script_item.make_last_updated())
        self.ui.script_last_updated.setModified(True)

    def save_changes(self):
        """Update the script object with any changes to the metadata.
        """
        title = self.ui.script_title.text().strip()
        if not title:
            QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Critical,
                _("Error"),
                _("The script title must not be empty."),
                QtWidgets.QMessageBox.Ok,
                self
            ).exec_()
            return
        if not self.ui.script_last_updated.isModified() or not self.ui.script_last_updated.text().strip():
            self.set_last_updated()
        self.script_item.update_script_setting(
            title=title,
            author=self.ui.script_author.text(),
            version=self.ui.script_version.text(),
            license=self.ui.script_license.text(),
            description=self.ui.script_description.toPlainText(),
            last_updated=self.ui.script_last_updated.text()
        )
        self.signal_save.emit()
        self.close_window()

    def close_window(self):
        """Close the script metadata editor window.
        """
        self.close()
