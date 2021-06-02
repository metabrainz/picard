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
import os.path

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt5.QtGui import QPalette

from picard import log
from picard.config import (
    BoolOption,
    ListOption,
    TextOption,
    get_config,
)
from picard.const import DEFAULT_FILE_NAMING_FORMAT
from picard.file import File
from picard.script import (
    ScriptError,
    ScriptParser,
    get_file_naming_script_presets,
)
from picard.script.serializer import (
    FileNamingScript,
    ScriptImportError,
)
from picard.util import (
    icontheme,
    webbrowser2,
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


class ScriptFileError(OptionsCheckError):
    pass


class ScriptEditorExamples():
    """File naming script examples.
    """
    max_samples = 10  # pick up to 10 samples

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

    def update_example_listboxes(self, before_listbox, after_listbox):
        """Update the contents of the file naming examples before and after listboxes.

        Args:
            before_listbox (QListBox): The before listbox
            after_listbox (QListBox): The after listbox
            examples (ScriptEditorExamples): The object to use for the examples
        """
        before_listbox.clear()
        after_listbox.clear()
        for before, after in sorted(self.get_examples(), key=lambda x: x[1]):
            before_listbox.addItem(before)
            after_listbox.addItem(after)

    def get_examples(self):
        """Get the list of examples.

        Returns:
            [list]: List of the before and after file name example tuples
        """
        return self.example_list

    @staticmethod
    def synchronize_selected_example_lines(current_row, source, target):
        """Matches selected item in target to source"""
        if source.currentRow() != current_row:
            current_row = source.currentRow()
            target.blockSignals(True)
            target.setCurrentRow(current_row)
            target.blockSignals(False)

    @classmethod
    def get_notes_text(cls):
        return _(
            "If you select files from the Cluster pane or Album pane prior to opening the Options screen, "
            "up to %u files will be randomly chosen from your selection as file naming examples.  If you "
            "have not selected any files, then some default examples will be provided.") % cls.max_samples

    @classmethod
    def get_tooltip_text(cls):
        return _("Reload up to %u items chosen at random from files selected in the main window") % cls.max_samples

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


def confirmation_dialog(parent, message):
    """Displays a confirmation dialog.

    Returns:
        bool: True if accepted, otherwise False.
    """
    dialog = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Warning,
        _('Confirm'),
        message,
        QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
        parent
    )
    return dialog.exec_() == QtWidgets.QMessageBox.Ok


def synchronize_vertical_scrollbars(widgets):
    """Synchronize position of vertical scrollbars and selections for listed widgets.

    Args:
        widgets (list): List of QListView widgets to synchronize
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
            widget.verticalScrollBar().valueChanged.connect(partial(_sync_scrollbar_vert, other))
        widget.setStyleSheet(stylesheet)


def populate_script_selection_combo_box(naming_scripts, selected_script_id, combo_box):
    """Populate the specified script selection combo box and identify the selected script.

    Args:
        naming_scripts (list): List of available user-defined naming scripts in YAML format
        selected_script_id (str): ID code for the currently selected script
        combo_box (QComboBox): Combo box object to populate

    Returns:
        int: The index of the currently selected script
    """
    SCRIPT_TITLE_USER = _("User: %s")
    if not selected_script_id:
        script_item = FileNamingScript(
            script=get_config().setting["file_naming_format"],
            title=_("Primary file naming script"),
            readonly=False,
            deletable=True,
        )
        naming_scripts.insert(0, script_item.to_yaml())
        selected_script_id = script_item['id']

    combo_box.blockSignals(True)
    combo_box.clear()

    def _add_and_check(idx, count, title, item):
        combo_box.addItem(title, item)
        if item['id'] == selected_script_id:
            idx = count
        count += 1
        return idx, count

    idx = 0
    count = 0   # Use separate counter rather than `i` in case ScriptImportError triggers, resulting in an incorrect index count.
    for i in range(len(naming_scripts)):
        try:
            script_item = FileNamingScript().create_from_yaml(naming_scripts[i], create_new_id=False)
        except ScriptImportError:
            pass
        else:
            naming_scripts[i] = script_item.to_yaml()  # Ensure scripts are stored with id codes
            idx, count = _add_and_check(idx, count, SCRIPT_TITLE_USER % script_item["title"], script_item)

    # Add preset scripts not provided in the user-defined scripts list.
    for script_item in get_file_naming_script_presets():
        idx, count = _add_and_check(idx, count, script_item['title'], script_item)

    combo_box.setCurrentIndex(idx)
    combo_box.blockSignals(False)
    return idx


class ScriptEditorDialog(PicardDialog):
    """File Naming Script Editor Page
    """
    TITLE = N_("File naming script editor")
    STYLESHEET_ERROR = OptionsPage.STYLESHEET_ERROR

    help_url = '/config/options_filerenaming_editor.html'

    options = [
        TextOption("setting", "file_naming_format", DEFAULT_FILE_NAMING_FORMAT),
        ListOption("setting", "file_naming_scripts", []),
        TextOption("setting", "selected_file_naming_script_id", ""),
        BoolOption('persist', 'script_editor_show_documentation', False),
    ]

    signal_save = QtCore.pyqtSignal()
    signal_update = QtCore.pyqtSignal()
    signal_selection_changed = QtCore.pyqtSignal()

    default_script_directory = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation))
    default_script_filename = "picard_naming_script.ptsp"

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
        self.FILE_TYPE_PACKAGE = _("Picard Naming Script Package") + " (*.ptsp *.yaml)"

        self.SCRIPT_TITLE_USER = _("User: %s")

        # TODO: Make this work properly so that it can be accessed from both the main window and the options window.
        # self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.loading = True
        self.ui = Ui_ScriptEditor()
        self.ui.setupUi(self)
        self.make_menu()

        self.ui.label.setWordWrap(False)

        self.installEventFilter(self)

        # Dialog buttons
        self.reset_button = QtWidgets.QPushButton(_('Revert'))
        self.reset_button.setToolTip(self.reset_action.toolTip())
        self.reset_button.clicked.connect(self.reset_script)
        self.ui.buttonbox.addButton(self.reset_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.save_button = self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.Save)
        self.save_button.setToolTip(self.save_action.toolTip())
        self.ui.buttonbox.accepted.connect(self.save_script)
        self.close_button = self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.Close)
        self.close_button.setToolTip(self.close_action.toolTip())
        self.ui.buttonbox.rejected.connect(self.close_window)
        self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.Help)
        self.ui.buttonbox.helpRequested.connect(self.show_help)

        self.ui.file_naming_format.setEnabled(True)

        # Add scripting documentation to parent frame.
        doc_widget = ScriptingDocumentationWidget(self, include_link=False)
        self.ui.documentation_frame_layout.addWidget(doc_widget)

        self.ui.file_naming_format.textChanged.connect(self.check_formats)

        self._sampled_example_files = []

        self.ui.example_filename_after.itemSelectionChanged.connect(self.match_before_to_after)
        self.ui.example_filename_before.itemSelectionChanged.connect(self.match_after_to_before)

        self.ui.preset_naming_scripts.currentIndexChanged.connect(partial(self.select_script, skip_check=False))

        synchronize_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

        self.toggle_documentation()  # Force update to display
        self.examples_current_row = -1

        self.script_metadata_changed = False

        self.load()
        self.loading = False

    def make_menu(self):
        """Build the menu bar.
        """
        config = get_config()
        main_menu = QtWidgets.QMenuBar()

        # File menu settings
        file_menu = main_menu.addMenu(_('&File'))
        file_menu.setToolTipsVisible(True)

        self.import_action = QtWidgets.QAction(_("&Import a script file"), self)
        self.import_action.setToolTip(_("Import a file as a new script"))
        self.import_action.setIcon(icontheme.lookup('document-open'))
        self.import_action.triggered.connect(self.import_script)
        file_menu.addAction(self.import_action)

        self.export_action = QtWidgets.QAction(_("&Export a script file"), self)
        self.export_action.setToolTip(_("Export the script to a file"))
        self.export_action.setIcon(icontheme.lookup('document-save'))
        self.export_action.triggered.connect(self.export_script)
        file_menu.addAction(self.export_action)

        self.close_action = QtWidgets.QAction(_("E&xit / Close editor"), self)
        self.close_action.setToolTip(_("Close the script editor"))
        self.close_action.triggered.connect(self.close_window)
        file_menu.addAction(self.close_action)

        # Script menu settings
        script_menu = main_menu.addMenu(_('&Script'))
        script_menu.setToolTipsVisible(True)

        self.details_action = QtWidgets.QAction(_("Edit Script &Metadata"), self)
        self.details_action.setToolTip(_("Display the details for the script"))
        self.details_action.triggered.connect(self.view_script_details)
        self.details_action.setShortcut(QtGui.QKeySequence(_("Ctrl+M")))
        script_menu.addAction(self.details_action)

        self.add_action = QtWidgets.QAction(_("Add a &new script"), self)
        self.add_action.setToolTip(_("Create a new file naming script"))
        self.add_action.setIcon(icontheme.lookup('add-item'))
        self.add_action.triggered.connect(self.new_script)
        script_menu.addAction(self.add_action)

        self.copy_action = QtWidgets.QAction(_("&Copy the current script"), self)
        self.copy_action.setToolTip(_("Save a copy of the script as a new script"))
        self.copy_action.setIcon(icontheme.lookup('edit-copy'))
        self.copy_action.triggered.connect(self.copy_script)
        script_menu.addAction(self.copy_action)

        self.delete_action = QtWidgets.QAction(_("&Delete the current script"), self)
        self.delete_action.setToolTip(_("Delete the script"))
        self.delete_action.setIcon(icontheme.lookup('list-remove'))
        self.delete_action.triggered.connect(self.delete_script)
        script_menu.addAction(self.delete_action)

        self.reset_action = QtWidgets.QAction(_("&Revert the current script"), self)
        self.reset_action.setToolTip(_("Revert the script to the last saved value"))
        self.reset_action.setIcon(icontheme.lookup('view-refresh'))
        self.reset_action.triggered.connect(self.reset_script)
        script_menu.addAction(self.reset_action)

        self.save_action = QtWidgets.QAction(_("&Save the current script"), self)
        self.save_action.setToolTip(_("Save changes to the script"))
        self.save_action.setIcon(icontheme.lookup('document-save'))
        self.save_action.setShortcut(QtGui.QKeySequence(_("Ctrl+S")))
        self.save_action.triggered.connect(self.save_script)
        script_menu.addAction(self.save_action)

        # Display menu settings
        display_menu = main_menu.addMenu(_('&View'))
        display_menu.setToolTipsVisible(True)

        self.examples_action = QtWidgets.QAction(_("&Reload random example files"), self)
        self.examples_action.setToolTip(self.examples.get_tooltip_text())
        self.examples_action.setIcon(icontheme.lookup('view-refresh'))
        self.examples_action.triggered.connect(self.update_example_files)
        display_menu.addAction(self.examples_action)

        display_menu.addAction(self.ui.file_naming_format.wordwrap_action)
        display_menu.addAction(self.ui.file_naming_format.show_tooltips_action)

        self.docs_action = QtWidgets.QAction(_("&Show documentation"), self)
        self.docs_action.setToolTip(_("View the scripting documentation in a sidebar"))
        self.docs_action.triggered.connect(self.toggle_documentation)
        self.docs_action.setShortcut(QtGui.QKeySequence(_("Ctrl+H")))
        self.docs_action.setCheckable(True)
        self.docs_action.setChecked(config.persist["script_editor_show_documentation"])
        display_menu.addAction(self.docs_action)

        # Help menu settings
        help_menu = main_menu.addMenu(_('&Help'))
        help_menu.setToolTipsVisible(True)

        self.help_action = QtWidgets.QAction(_("&Help..."), self)
        self.help_action.setShortcut(QtGui.QKeySequence.HelpContents)
        self.help_action.triggered.connect(self.show_help)
        help_menu.addAction(self.help_action)

        self.scripting_docs_action = QtWidgets.QAction(_("&Scripting documentation..."), self)
        self.scripting_docs_action.setToolTip(_("Open the scripting documentation in your browser"))
        self.scripting_docs_action.triggered.connect(self.docs_browser)
        help_menu.addAction(self.scripting_docs_action)

        self.ui.layout_for_menubar.addWidget(main_menu)

    def load(self):
        """Load initial configuration.
        """
        config = get_config()
        self.examples.settings = config.setting
        self.naming_scripts = config.setting["file_naming_scripts"]
        self.selected_script_id = config.setting["selected_file_naming_script_id"]
        self.selected_script_index = 0
        self.populate_script_selector()
        if not self.loading:
            self.select_script(skip_check=True)

    def docs_browser(self):
        """Open the scriping documentation in a browser.
        """
        webbrowser2.open('doc_scripting')

    def eventFilter(self, object, event):
        """Process selected events.
        """
        evtype = event.type()
        if evtype in {QtCore.QEvent.WindowActivate, QtCore.QEvent.FocusIn}:
            self.update_examples()
        return False

    def close_window(self):
        """Close the window.
        """
        self.close()

    def closeEvent(self, event):
        """Custom close event handler to check for unsaved changes.
        """
        if self.unsaved_changes_confirmation():
            if self.has_changed():
                self.select_script(skip_check=True)
            super().closeEvent(event)
        else:
            event.ignore()

    def populate_script_selector(self):
        """Populate the script selection combo box.
        """
        idx = populate_script_selection_combo_box(self.naming_scripts, self.selected_script_id, self.ui.preset_naming_scripts)
        self.update_scripts_list()
        self.set_selected_script_index(idx)

    def toggle_documentation(self):
        """Toggle the display of the scripting documentation sidebar.
        """
        checked = self.docs_action.isChecked()
        config = get_config()
        config.persist["script_editor_show_documentation"] = checked
        self.ui.documentation_frame.setVisible(checked)

    def view_script_details(self):
        """View and edit (if not readonly) the metadata associated with the script.
        """
        selected_item = self.get_selected_item()
        details_page = ScriptDetailsEditor(self, selected_item)
        details_page.signal_save.connect(self.update_from_details)
        details_page.show()
        details_page.raise_()
        details_page.activateWindow()

    def has_changed(self):
        """Check if the current script has pending edits to the title or script that have not been saved.

        Returns:
            bool: True if there are unsaved changes, otherwise false.
        """
        script_item = self.ui.preset_naming_scripts.itemData(self.selected_script_index)
        return self.ui.script_title.text().strip() != script_item['title'] or \
            self.get_script() != script_item['script'] or \
            self.script_metadata_changed

    def update_from_details(self):
        """Update the script selection combo box and script list after updates from the script details dialog.
        """
        selected_item = self.get_selected_item()
        self.update_combo_box_item(self.ui.preset_naming_scripts.currentIndex(), selected_item)
        self.ui.script_title.setText(selected_item['title'])
        self.script_metadata_changed = True

    def _set_combobox_index(self, idx):
        """Sets the index of the script selector combo box.

        Args:
            idx (int): New index position
        """
        self.ui.preset_naming_scripts.blockSignals(True)
        self.ui.preset_naming_scripts.setCurrentIndex(idx)
        self.ui.preset_naming_scripts.blockSignals(False)
        self.selected_script_index = idx

    def _insert_item(self, script_item):
        """Insert a new item into the script selection combo box and update the script list in the settings.

        Args:
            script_item (FileNamingScript): File naming script to insert.
        """
        idx = len(self.naming_scripts)
        self.ui.preset_naming_scripts.blockSignals(True)
        self.ui.preset_naming_scripts.insertItem(idx, self.SCRIPT_TITLE_USER % script_item['title'], script_item)
        self.ui.preset_naming_scripts.blockSignals(False)
        self._set_combobox_index(idx)
        self.update_scripts_list()
        self.select_script(skip_check=True)

    def new_script(self):
        """Add a new (empty) script to the script selection combo box and script list.
        """
        if self.unsaved_changes_confirmation():
            script_item = FileNamingScript(script='$noop()')
            self._insert_item(script_item)

    def copy_script(self):
        """Add a copy of the script as a new editable script to the script selection combo box and script list.
        """
        if self.unsaved_changes_confirmation():
            selected = self.ui.preset_naming_scripts.currentIndex()
            script_item = self.ui.preset_naming_scripts.itemData(selected)
            new_item = script_item.copy()
            self._insert_item(new_item)

    def update_script_in_settings(self, script_item):
        self.signal_save.emit()

    def update_scripts_list(self):
        """Refresh the script list in the settings based on the contents of the script selection combo box.
        """
        self.naming_scripts = []
        for idx in range(self.ui.preset_naming_scripts.count()):
            script_item = self.ui.preset_naming_scripts.itemData(idx)
            # Only add items that can be removed -- no presets
            if script_item.deletable:
                self.naming_scripts.append(script_item.to_yaml())

    def get_selected_item(self):
        """Get the selected item from the script selection combo box.

        Returns:
            FileNamingScript: The selected script.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        return self.ui.preset_naming_scripts.itemData(selected)

    def unsaved_changes_confirmation(self):
        """Check if there are unsaved changes and ask the user to confirm the action resulting in their loss.

        Returns:
            bool: True if no unsaved changes or user confirms the action, otherwise False.
        """
        if not self.loading and self.has_changed() and not confirmation_dialog(self,
            _("There are unsaved changes to the current script.  Do you want to continue and lose these changes?")
        ):
            self._set_combobox_index(self.selected_script_index)
            return False
        return True

    def set_selected_script_index(self, idx, send_signal=True):
        """Select the script at the specified combo box index.

        Args:
            idx (int): Index of the script to select
            send_signal (bool, optional): Determines whether the update signal should be emitted. Defaults to True.
        """
        self._set_combobox_index(idx)
        self.select_script(skip_check=True, send_signal=send_signal)

    def select_script(self, skip_check=False, send_signal=True):
        """Load the current script from the combo box into the editor.

        Args:
            skip_check (bool): Skip the check for unsaved edits.  Defaults to False.
            send_signal (bool, optional): Determines whether the update signal should be emitted. Defaults to True.
        """
        if not self.loading or skip_check or self.unsaved_changes_confirmation():
            script_item = self.get_selected_item()
            self.ui.script_title.setText(script_item['title'])
            self.set_script(script_item['script'])
            self.selected_script_id = script_item['id']
            self.selected_script_index = self.ui.preset_naming_scripts.currentIndex()
            self.script_metadata_changed = False
            self.update_script_in_settings(script_item)
            self.set_button_states()
            self.update_examples()
            if send_signal:
                self.signal_selection_changed.emit()

    def update_combo_box_item(self, idx, script_item):
        """Update the title and item data for the specified script selection combo box item.

        Args:
            idx (int): Index of the item to update
            script_item (FileNamingScript): Updated script information
        """
        self.ui.preset_naming_scripts.setItemData(idx, script_item)
        self.ui.preset_naming_scripts.setItemText(idx, self.SCRIPT_TITLE_USER % script_item['title'])
        self.update_script_in_settings(script_item)
        self.update_scripts_list()

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
        readonly = script_item['readonly']
        self.ui.script_title.setReadOnly(readonly or selected < 1)

        # Buttons
        self.ui.file_naming_format.setReadOnly(readonly)
        self.save_button.setEnabled(save_enabled and not readonly)
        self.reset_button.setEnabled(not readonly)

        # Menu items
        self.save_action.setEnabled(save_enabled and not readonly)
        self.reset_action.setEnabled(not readonly)
        self.add_action.setEnabled(save_enabled)
        self.copy_action.setEnabled(save_enabled)
        self.delete_action.setEnabled(script_item['deletable'] and save_enabled)
        self.import_action.setEnabled(save_enabled)
        self.export_action.setEnabled(save_enabled)

    def match_after_to_before(self):
        """Sets the selected item in the 'after' list to the corresponding item in the 'before' list.
        """
        self.examples.synchronize_selected_example_lines(self.examples_current_row, self.ui.example_filename_before, self.ui.example_filename_after)

    def match_before_to_after(self):
        """Sets the selected item in the 'before' list to the corresponding item in the 'after' list.
        """
        self.examples.synchronize_selected_example_lines(self.examples_current_row, self.ui.example_filename_after, self.ui.example_filename_before)

    def delete_script(self):
        """Removes the currently selected script from the script selection combo box and script list.
        """
        if confirmation_dialog(self, _('Are you sure that you want to delete the script?')):
            idx = self.ui.preset_naming_scripts.currentIndex()
            self.ui.preset_naming_scripts.blockSignals(True)
            self.ui.preset_naming_scripts.removeItem(idx)
            self.ui.preset_naming_scripts.blockSignals(False)
            if idx >= self.ui.preset_naming_scripts.count():
                idx = self.ui.preset_naming_scripts.count() - 1
            self._set_combobox_index(idx)
            self.update_scripts_list()
            self.select_script(skip_check=True)

    def save_script(self):
        """Saves changes to the current script to the script list and combo box item.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        self.signal_save.emit()
        title = str(self.ui.script_title.text()).strip()
        if title:
            script_item = self.ui.preset_naming_scripts.itemData(selected)
            script_item.title = title
            script_item.script = self.get_script()
            self.update_combo_box_item(selected, script_item)
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                _("Save Script"),
                _("Changes to the script have been saved."),
                QtWidgets.QMessageBox.Ok,
                self
            )
            dialog.exec_()
        else:
            self.display_error(OptionsCheckError(_("Error"), _("The script title must not be empty.")))

    def get_script(self):
        """Provides the text of the file naming script currently loaded into the editor.

        Returns:
            str: File naming script
        """
        return str(self.ui.file_naming_format.toPlainText()).strip()

    def set_script(self, script_text):
        """Sets the text of the file naming script into the editor and settings.

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

    def display_examples(self, send_signal=True):
        """Update the display of the before and after file naming examples.

        Args:
            send_signal (bool, optional): Determines whether the update signal should be emitted. Defaults to True.
        """
        self.examples_current_row = -1
        self.examples.update_example_listboxes(self.ui.example_filename_before, self.ui.example_filename_after)
        if send_signal:
            self.signal_update.emit()

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
        self.display_error(ScriptFileError(_(title), error_message))

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
        FILE_ERROR_IMPORT = N_('Error importing "%s". %s.')
        FILE_ERROR_DECODE = N_('Error decoding "%s". %s.')

        if not self.unsaved_changes_confirmation():
            return

        dialog_title = _("Import Script File")
        dialog_file_types = self._get_dialog_filetypes()
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, file_type = QtWidgets.QFileDialog.getOpenFileName(self, dialog_title, self.default_script_directory, dialog_file_types, options=options)
        if filename:
            log.debug('Importing naming script file: %s' % filename)
            try:
                with open(filename, 'r', encoding='utf8') as i_file:
                    file_content = i_file.read()
            except OSError as error:
                self.output_file_error(FILE_ERROR_IMPORT, filename, error.strerror)
                return
            if not file_content.strip():
                self.output_file_error(FILE_ERROR_IMPORT, filename, _('The file was empty'))
                return
            if file_type == self.FILE_TYPE_PACKAGE:
                try:
                    script_item = FileNamingScript().create_from_yaml(file_content)
                except ScriptImportError as error:
                    self.output_file_error(FILE_ERROR_DECODE, filename, error)
                    return
            else:
                script_item = FileNamingScript(
                    title=_("Imported from %s") % filename,
                    script=file_content.strip()
                )
            self._insert_item(script_item)

    def export_script(self):
        """Export the current script to an external file. Export can be either as a plain text
        script or a naming script package.
        """
        FILE_ERROR_EXPORT = N_('Error exporting file "%s". %s.')

        script_item = self.get_selected_item()
        script_text = self.get_script()

        if script_text:
            default_path = os.path.normpath(os.path.join(self.default_script_directory, self.default_script_filename))
            dialog_title = _("Export Script File")
            dialog_file_types = self._get_dialog_filetypes()
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
                    script_text = script_item.to_yaml()
                try:
                    with open(filename, 'w', encoding='utf8') as o_file:
                        o_file.write(script_text)
                except OSError as error:
                    self.output_file_error(FILE_ERROR_EXPORT, filename, error.strerror)
                else:
                    dialog = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Information,
                        _("Export Script"),
                        _("Script successfully exported to %s") % filename,
                        QtWidgets.QMessageBox.Ok,
                        self
                    )
                    dialog.exec_()

    def _get_dialog_filetypes(self):
        """Helper function to build file type string used in the file dialogs.

        Returns:
            str: File type selection string
        """
        return ";;".join((
            self.FILE_TYPE_PACKAGE,
            self.FILE_TYPE_SCRIPT,
            self.FILE_TYPE_ALL,
        ))

    def reset_script(self):
        """Reset the script to the last saved value.
        """
        if self.has_changed():
            if confirmation_dialog(self, _("Are you sure that you want to reset the script to its last saved value?")):
                self.select_script(skip_check=True)
        else:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                _("Revert Script"),
                _("There have been no changes made since the last time the script was saved."),
                QtWidgets.QMessageBox.Ok,
                self
            )
            dialog.exec_()

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
            parent (ScriptEditorDialog): The page used for editing the scripts
            script_item (FileNamingScript): The script whose metadata is displayed
        """
        super().__init__(parent=parent)
        self.script_item = script_item
        self.readonly = script_item.readonly
        self.setWindowTitle(self.TITLE)
        self.displaying = False
        self.ui = Ui_ScriptDetails()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.connect(self.save_changes)
        self.ui.buttonBox.rejected.connect(self.close_window)
        self.ui.last_updated_now.clicked.connect(self.set_last_updated)

        self.ui.script_title.setText(self.script_item['title'])
        self.ui.script_author.setText(self.script_item['author'])
        self.ui.script_version.setText(self.script_item['version'])
        self.ui.script_last_updated.setText(self.script_item['last_updated'])
        self.ui.script_license.setText(self.script_item['license'])
        self.ui.script_description.setPlainText(self.script_item['description'])

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
        self.skip_change_check = False

    def has_changed(self):
        """Check if the current script metadata has pending edits that have not been saved.

        Returns:
            bool: True if there are unsaved changes, otherwise false.
        """
        return self.script_item['title'] != self.ui.script_title.text().strip() or \
            self.script_item['author'] != self.ui.script_author.text().strip() or \
            self.script_item['version'] != self.ui.script_version.text().strip() or \
            self.script_item['license'] != self.ui.script_license.text().strip() or \
            self.script_item['description'] != self.ui.script_description.toPlainText().strip()

    def change_check(self):
        """Confirm whether the unsaved changes should be lost.

        Returns:
            bool: True if changes can be lost, otherwise False.
        """
        return confirmation_dialog(
            self,
            _("There are unsaved changes to the current metadata.  Do you want to continue and lose these changes?"),
        )

    def set_last_updated(self):
        """Set the last updated value to the current timestamp.
        """
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
        if self.has_changed():
            if self.change_check():
                if not self.ui.script_last_updated.isModified() or not self.ui.script_last_updated.text().strip():
                    self.set_last_updated()
                self.script_item.update_script_setting(
                    title=self.ui.script_title.text().strip(),
                    author=self.ui.script_author.text().strip(),
                    version=self.ui.script_version.text().strip(),
                    license=self.ui.script_license.text().strip(),
                    description=self.ui.script_description.toPlainText().strip(),
                    last_updated=self.ui.script_last_updated.text().strip()
                )
                self.signal_save.emit()
            else:
                return
        self.skip_change_check = True
        self.close_window()

    def close_window(self):
        """Close the script metadata editor window.
        """
        self.close()

    def closeEvent(self, event):
        """Custom close event handler to check for unsaved changes.
        """
        if self.skip_change_check or not self.has_changed() or (self.has_changed() and self.change_check()):
            event.accept()
        else:
            event.ignore()
