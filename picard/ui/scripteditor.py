# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2022 Laurent Monin
# Copyright (C) 2021-2022 Philipp Wolfer
# Copyright (C) 2021-2023 Bob Swift
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


from collections import namedtuple
from copy import deepcopy
from functools import partial
import os.path
import random

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt5.QtGui import QPalette

from picard import log
from picard.config import (
    BoolOption,
    Option,
    SettingConfigSection,
    TextOption,
    get_config,
)
from picard.const import (
    DEFAULT_COPY_TEXT,
    DEFAULT_NAMING_PRESET_ID,
    DEFAULT_SCRIPT_NAME,
    PICARD_URLS,
)
from picard.file import File
from picard.metadata import Metadata
from picard.script import (
    ScriptError,
    ScriptParser,
    get_file_naming_script,
    get_file_naming_script_presets,
)
from picard.script.serializer import (
    FileNamingScript,
    ScriptImportExportError,
)
from picard.util import (
    get_base_title,
    icontheme,
    iter_files_from_objects,
    unique_numbered_title,
    webbrowser2,
)
from picard.util.filenaming import WinPathTooLong
from picard.util.settingsoverride import SettingsOverride

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)
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
        self.script_text = get_file_naming_script(self.settings)

    def _get_samples(self, candidates):
        candidates = tuple(candidates)
        length = min(self.max_samples, len(candidates))
        return random.sample(candidates, k=length)

    def update_sample_example_files(self):
        """Get a new sample of randomly selected / loaded files to use as renaming examples.
        """
        if self.tagger.window.selected_objects:
            # If files/albums/tracks are selected, sample example files from them
            candidates = iter_files_from_objects(self.tagger.window.selected_objects)
        else:
            # If files/albums/tracks are not selected, sample example files from the pool of loaded files
            candidates = self.tagger.files.values()

        files = self._get_samples(candidates)
        self._sampled_example_files = files or list(self.default_examples())
        self.update_examples()

    def update_examples(self, override=None, script_text=None):
        """Update the before and after file naming examples list.

        Args:
            override (dict, optional): Dictionary of settings overrides to apply. Defaults to None.
            script_text (str, optional): Text of the file naming script to use. Defaults to None.
        """
        if override and isinstance(override, dict):
            self.settings = SettingsOverride(self.settings, override)
        if script_text and isinstance(script_text, str):
            self.script_text = script_text

        if self.settings['move_files'] or self.settings['rename_files']:
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
        # Operate on a copy of the file object metadata to avoid multiple changes to file metadata.  See PICARD-2508.
        c_metadata = Metadata()
        c_metadata.copy(file.metadata)
        try:
            # Only apply scripts if the original file metadata has not been changed.
            if self.settings['enable_tagger_scripts'] and not c_metadata.diff(file.orig_metadata):
                for s_pos, s_name, s_enabled, s_text in self.settings['list_of_scripts']:
                    if s_enabled and s_text:
                        parser = ScriptParser()
                        parser.eval(s_text, c_metadata)
            filename_before = file.filename
            filename_after = file.make_filename(filename_before, c_metadata, self.settings, self.script_text)
            if not self.settings['move_files']:
                return os.path.basename(filename_before), os.path.basename(filename_after)
            return filename_before, filename_after
        except (ScriptError, TypeError, WinPathTooLong):
            return "", ""

    def update_example_listboxes(self, before_listbox, after_listbox):
        """Update the contents of the file naming examples before and after listboxes.

        Args:
            before_listbox (QListBox): The before listbox
            after_listbox (QListBox): The after listbox
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
        """Sets the current row in the target to match the current row in the source.

        Args:
            current_row (int): Currently selected row
            source (QListView): Source list
            target (QListView): Target list
        """
        if source.currentRow() != current_row:
            current_row = source.currentRow()
            target.blockSignals(True)
            target.setCurrentRow(current_row)
            target.blockSignals(False)

    @classmethod
    def get_notes_text(cls):
        """Provides usage notes text suitable for display on the dialog.

        Returns:
            str: Notes text
        """
        return _(
            "If you select files from the Cluster pane or Album pane prior to opening the Options screen, "
            "up to %u files will be randomly chosen from your selection as file naming examples.  If you "
            "have not selected any files, then some default examples will be provided.") % cls.max_samples

    @classmethod
    def get_tooltip_text(cls):
        """Provides tooltip text suitable for display on the dialog.

        Returns:
            str: Tooltip text
        """
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
            'musicbrainz_trackid': '392639f5-5629-477e-b04b-93bffa703405',
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
            'musicbrainz_trackid': 'f8649a05-da39-39ba-957c-7abf8f9012be',
            'musicbrainz_albumartistid': '89ad4ac3-39f7-470e-963a-56509c546377',
            'musicbrainz_artistid': ['7b593455-d207-482c-8c6f-19ce22c94679', '9e082466-2390-40d1-891e-4803531f43fd'],
        })
        yield efile


def confirmation_dialog(parent, message):
    """Displays a confirmation dialog.

    Args:
        parent (object): Parent object / window making the call to set modality
        message (str): Message to be displayed

    Returns:
        bool: True if accepted, otherwise False.
    """
    dialog = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Warning,
        _("Confirm"),
        message,
        QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
        parent
    )
    return dialog.exec_() == QtWidgets.QMessageBox.StandardButton.Ok


def synchronize_vertical_scrollbars(widgets):
    """Synchronize position of vertical scrollbars and selections for listed widgets.

    Args:
        widgets (list): List of QListView widgets to synchronize
    """
    # Set highlight colors for selected list items
    example_style = widgets[0].palette()
    highlight_bg = example_style.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
    highlight_fg = example_style.color(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText)
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
        naming_scripts (dict): Dictionary of available user-defined naming scripts as script dictionaries as produced by FileNamingScript().to_dict()
        selected_script_id (str): ID code for the currently selected script
        combo_box (QComboBox): Combo box object to populate

    Returns:
        int: The index of the currently selected script
    """
    combo_box.blockSignals(True)
    combo_box.clear()

    def _add_and_check(idx, count, title, item):
        combo_box.addItem(title, item)
        if item['id'] == selected_script_id:
            idx = count
        return idx

    idx = 0
    count = -1
    for count, (id, naming_script) in enumerate(sorted(naming_scripts.items(), key=lambda item: item[1]['title'])):
        idx = _add_and_check(idx, count, naming_script['title'], naming_script)

    combo_box.setCurrentIndex(idx)
    combo_box.blockSignals(False)
    return idx


class NotEmptyValidator(QtGui.QValidator):
    def validate(self, text: str, pos):
        if bool(text.strip()):
            state = QtGui.QValidator.State.Acceptable
        else:
            state = QtGui.QValidator.State.Intermediate  # so that field can be made empty temporarily
        return state, text, pos


class ScriptEditorDialog(PicardDialog, SingletonDialog):
    """File Naming Script Editor Page
    """
    TITLE = N_("File naming script editor")
    STYLESHEET_ERROR = OptionsPage.STYLESHEET_ERROR

    PROFILES_KEY = SettingConfigSection.PROFILES_KEY
    SETTINGS_KEY = SettingConfigSection.SETTINGS_KEY
    SELECTED_SCRIPT_KEY = 'selected_file_naming_script_id'
    SCRIPTS_LIST_KEY = 'file_renaming_scripts'

    help_url = PICARD_URLS['doc_naming_script_edit']

    options = [
        BoolOption('persist', 'script_editor_show_documentation', False),
        Option('setting', SCRIPTS_LIST_KEY, {}),
        TextOption('setting', SELECTED_SCRIPT_KEY, ''),
    ]

    signal_save = QtCore.pyqtSignal()
    signal_update = QtCore.pyqtSignal()
    signal_selection_changed = QtCore.pyqtSignal()
    signal_index_changed = QtCore.pyqtSignal()

    default_script_directory = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation))
    default_script_filename = "picard_naming_script.ptsp"

    Profile = namedtuple('Profile', ['id', 'title', 'script_id'])

    @classmethod
    def show_instance(cls, *args, **kwargs):
        if cls._instance:
            # Accommodate condition where OptionsPage closing may have destroyed the
            # ScriptEditorDialog instance without resetting the cls._instance property
            cls._instance.show()
            if not cls._instance.isVisible():
                cls._instance = None
        instance = super().show_instance(*args, **kwargs)

        # Manually set examples in case of re-using an existing instance of the dialog
        instance.examples = kwargs['examples']
        instance.update_examples()

        # Reset formatting lost when changing parent.
        instance.ui.label.setWordWrap(False)

        return instance

    def __init__(self, parent=None, examples=None):
        """Stand-alone file naming script editor.

        Args:
            parent (QMainWindow or OptionsPage, optional): Parent object. Defaults to None.
            examples (ScriptEditorExamples, required): Object containing examples to display. Defaults to None.
        """
        super().__init__(parent)
        self.examples = examples

        self.setWindowTitle(_(self.TITLE))
        self.loading = True
        self.ui = Ui_ScriptEditor()
        self.ui.setupUi(self)
        self.make_menu()

        self.ui.label.setWordWrap(False)

        self.installEventFilter(self)

        # Dialog buttons
        self.reset_button = QtWidgets.QPushButton(_("Reset"))
        self.reset_button.setToolTip(self.reset_action.toolTip())
        self.reset_button.clicked.connect(self.reload_from_config)
        self.ui.buttonbox.addButton(self.reset_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        self.save_button = self.ui.buttonbox.addButton(_("Make It So!"), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.save_button.setToolTip(self.save_action.toolTip())
        self.ui.buttonbox.accepted.connect(self.make_it_so)

        self.close_button = self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.close_button.setToolTip(self.close_action.toolTip())
        self.ui.buttonbox.rejected.connect(self.close)

        self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Help)
        self.ui.buttonbox.helpRequested.connect(self.show_help)

        # Add links to edit script metadata
        self.ui.script_title.installEventFilter(self)
        self.ui.script_title.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        self.ui.script_title.addAction(self.details_action)

        self.ui.file_naming_format.setEnabled(True)

        # Add scripting documentation to parent frame.
        doc_widget = ScriptingDocumentationWidget(self, include_link=False)
        self.ui.documentation_frame_layout.addWidget(doc_widget)

        self.ui.file_naming_format.textChanged.connect(self.check_formats)
        self.ui.script_title.textChanged.connect(self.update_script_title)
        self.ui.script_title.setValidator(NotEmptyValidator(self.ui.script_title))

        self._sampled_example_files = []

        self.ui.example_filename_after.itemSelectionChanged.connect(self.match_before_to_after)
        self.ui.example_filename_before.itemSelectionChanged.connect(self.match_after_to_before)

        self.ui.preset_naming_scripts.currentIndexChanged.connect(partial(self.select_script, update_last_selected=True))

        synchronize_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

        self.toggle_documentation()  # Force update to display
        self.examples_current_row = -1

        self.selected_script_index = 0
        self.current_item_dict = None

        self.original_script_id = ''
        self.original_script_title = ''

        self.last_selected_id = ''

        self.load()
        self.loading = False

    def setParent(self, parent):
        """Custom setParent() method to check that parent is different to avoid display problems.

        Args:
            parent (object): Parent to set for the instance
        """
        if self.parent() != parent:
            flags = self.windowFlags() | QtCore.Qt.WindowType.Window
            super().setParent(parent, flags)
            # Set appropriate state of script selector in parent
            save_enabled = self.save_button.isEnabled()
            self.set_selector_states(save_enabled=save_enabled)

    def make_menu(self):
        """Build the menu bar.
        """
        config = get_config()
        main_menu = QtWidgets.QMenuBar()

        # File menu settings
        file_menu = main_menu.addMenu(_("&File"))
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

        self.reset_action = QtWidgets.QAction(_("&Reset all scripts"), self)
        self.reset_action.setToolTip(_("Reset all scripts to the saved values"))
        self.reset_action.setIcon(icontheme.lookup('view-refresh'))
        self.reset_action.triggered.connect(self.reload_from_config)
        file_menu.addAction(self.reset_action)

        self.save_action = QtWidgets.QAction(_("&Save and exit"), self)
        self.save_action.setToolTip(_("Save changes to the script settings and exit"))
        self.save_action.setIcon(icontheme.lookup('document-save'))
        self.save_action.triggered.connect(self.make_it_so)
        file_menu.addAction(self.save_action)

        self.close_action = QtWidgets.QAction(_("E&xit without saving"), self)
        self.close_action.setToolTip(_("Close the script editor without saving changes"))
        self.close_action.triggered.connect(self.close)
        file_menu.addAction(self.close_action)

        # Script menu settings
        script_menu = main_menu.addMenu(_("&Script"))
        script_menu.setToolTipsVisible(True)

        self.details_action = QtWidgets.QAction(_("View/Edit Script &Metadata"), self)
        self.details_action.setToolTip(_("Display the details for the script"))
        self.details_action.triggered.connect(self.view_script_details)
        self.details_action.setShortcut(QtGui.QKeySequence(_("Ctrl+M")))
        script_menu.addAction(self.details_action)

        self.add_action = QtWidgets.QMenu(_("Add a &new script"))
        self.add_action.setIcon(icontheme.lookup('add-item'))
        self.make_script_template_selector_menu()
        script_menu.addMenu(self.add_action)

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

        # Display menu settings
        display_menu = main_menu.addMenu(_("&View"))
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
        help_menu = main_menu.addMenu(_("&Help"))
        help_menu.setToolTipsVisible(True)

        self.help_action = QtWidgets.QAction(_("&Help…"), self)
        self.help_action.setShortcut(QtGui.QKeySequence.StandardKey.HelpContents)
        self.help_action.triggered.connect(self.show_help)
        help_menu.addAction(self.help_action)

        self.scripting_docs_action = QtWidgets.QAction(_("&Scripting documentation…"), self)
        self.scripting_docs_action.setToolTip(_("Open the scripting documentation in your browser"))
        self.scripting_docs_action.triggered.connect(self.docs_browser)
        help_menu.addAction(self.scripting_docs_action)

        self.ui.layout_for_menubar.addWidget(main_menu)

    def make_script_template_selector_menu(self):
        """Update the sub-menu of available file naming script templates.
        """

        self.add_action.clear()

        def _add_menu_item(title, script):
            script_action = QtWidgets.QAction(title, self.add_action)
            script_action.triggered.connect(partial(self.new_script, script))
            self.add_action.addAction(script_action)

        # Add blank script template
        _add_menu_item(_("Empty / blank script"), f"$noop( {_('New Script')} )")

        # Add preset script templates
        for script_item in get_file_naming_script_presets():
            _add_menu_item(script_item['title'], script_item['script'])

    def is_options_ui(self):
        return self.parent().__class__.__name__ == 'RenamingOptionsPage'

    def is_main_ui(self):
        return self.parent().__class__.__name__ == 'MainWindow'

    def load(self, reload=False):
        """Load initial configuration.
        """
        config = get_config()
        self.naming_scripts = config.setting[self.SCRIPTS_LIST_KEY]
        self.selected_script_id = config.setting[self.SELECTED_SCRIPT_KEY]
        if not self.selected_script_id or self.selected_script_id not in self.naming_scripts:
            self.selected_script_id = DEFAULT_NAMING_PRESET_ID
        self.last_selected_id = self.selected_script_id
        if not reload:
            self.examples.settings = config.setting
            self.original_script_id = self.selected_script_id
            self.original_script_title = self.all_scripts()[self.original_script_id]['title']
        if self.is_options_ui():
            selector = self.parent().ui.naming_script_selector
            idx = selector.currentIndex()
            sel_id = selector.itemData(idx)['id']
            if sel_id in self.all_scripts():
                self.selected_script_id = sel_id
        self.selected_script_index = 0
        self.populate_script_selector()
        if not self.loading:
            self.select_script()

    def all_scripts(self, scripts=None):
        """Get dictionary of all current scripts.

        Returns:
            dict: All current scripts
        """
        return deepcopy(scripts if scripts is not None else self.naming_scripts)

    def reload_from_config(self):
        """Reload the scripts and selected script from the configuration.
        """
        if self.unsaved_changes_in_profile_confirmation():
            self.load(reload=True)

    def docs_browser(self):
        """Open the scriping documentation in a browser.
        """
        webbrowser2.open('doc_scripting')

    def eventFilter(self, object, event):
        """Process selected events.
        """
        evtype = event.type()
        if evtype in {QtCore.QEvent.Type.WindowActivate, QtCore.QEvent.Type.FocusIn}:
            self.update_examples()
        elif object == self.ui.script_title and evtype == QtCore.QEvent.Type.MouseButtonDblClick:
            self.details_action.trigger()
            return True
        return False

    def closeEvent(self, event):
        """Custom close event handler to check for unsaved changes.
        """
        if self.unsaved_changes_in_profile_confirmation():
            self.reset_script_in_settings()
            self.set_selector_states(save_enabled=True)
            event.ignore()
            super().closeEvent(event)
        else:
            event.ignore()

    def unsaved_changes_in_profile_confirmation(self):
        """Confirm reset of selected script in profile if it points to an unsaved script.

        Returns:
            bool: False if user chooses to cancel, otherwise True.
        """
        all_naming_scripts = self.all_scripts()
        profiles_with_scripts = self.scripts_in_profiles()
        for script_id in self.unsaved_scripts():
            profile = self.is_used_in_profile(script_id=script_id, profiles=profiles_with_scripts)
            if not profile:
                continue
            old_script_title = all_naming_scripts[script_id]['title']
            new_script_title = self.original_script_title
            if confirmation_dialog(
                self,
                _(
                    'At least one unsaved script has been attached to an option profile.\n\n'
                    '   Profile: {profile_title}\n'
                    '   Script: {old_script_title}\n\n'
                    'Continuing without saving will reset the selected script in the profile to:\n\n'
                    '   {new_script_title}\n\n'
                    'Are you sure that you want to continue?'
                ).format(
                    profile_title=profile.title,
                    old_script_title=old_script_title,
                    new_script_title=new_script_title,
                )
            ):
                self.reset_script_in_profiles()
                break
            else:
                return False
        return True

    def reset_script_in_settings(self):
        """Reset the currently selected script if it was not saved and is no longer available.
        """
        config = get_config()
        unsaved = set(id for id in self.unsaved_scripts())
        if config.setting[self.SELECTED_SCRIPT_KEY] in unsaved:
            config.setting[self.SELECTED_SCRIPT_KEY] = self.original_script_id
        self.naming_scripts = config.setting[self.SCRIPTS_LIST_KEY]
        all_scripts = self.all_scripts()
        if self.selected_script_id not in all_scripts:
            if self.last_selected_id in all_scripts:
                self.selected_script_id = self.last_selected_id
            if self.selected_script_id not in all_scripts:
                self.selected_script_id = list(all_scripts.keys())[0]
        script_text = all_scripts[self.selected_script_id]['script']
        self.update_examples(script_text=script_text)
        self.signal_selection_changed.emit()

    def reset_script_in_profiles(self):
        """Reset the selected script in profiles if it was not saved and is no longer available.
        """
        config = get_config()
        profiles_with_scripts = self.scripts_in_profiles()
        for script_id in self.unsaved_scripts():
            profile = self.is_used_in_profile(script_id=script_id, profiles=profiles_with_scripts)
            if profile:
                config.profiles[self.SETTINGS_KEY][profile.id][self.SELECTED_SCRIPT_KEY] = self.original_script_id

    def unsaved_scripts(self):
        """Generate ID codes of scripts that have not been saved.

        Yields:
            str: ID code for the unsaved script
        """
        config = get_config()
        cfg_naming_scripts = config.setting[self.SCRIPTS_LIST_KEY]
        all_naming_scripts = self.all_scripts(scripts=cfg_naming_scripts)
        for script_id in self.naming_scripts.keys():
            if script_id not in all_naming_scripts:
                yield script_id

    def scripts_in_profiles(self):
        """Get list of script IDs saved to option profiles.

        Returns:
            list: List of Profile named tuples
        """
        profiles_list = []
        config = get_config()
        profiles = config.profiles[self.PROFILES_KEY]
        profile_settings = config.profiles[self.SETTINGS_KEY]
        for profile in profiles:
            settings = profile_settings[profile['id']]
            if self.SELECTED_SCRIPT_KEY in settings:
                profiles_list.append(
                    self.Profile(
                        profile['id'],
                        profile['title'],
                        settings[self.SELECTED_SCRIPT_KEY]
                    )
                )
        return profiles_list

    def update_script_text(self):
        """Updates the combo box item with changes to the current script.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        script_item = self.ui.preset_naming_scripts.itemData(selected)
        script_item['script'] = self.get_script()
        self.update_combo_box_item(selected, script_item)

    def check_duplicate_script_title(self, new_title=None):
        """Checks the script title to see if it is a duplicate of an existing script title.
        If no title is provided, then it will be extracted from the item data for the
        currently selected script.

        Args:
            new_title (string, optional): New title to check. Defaults to None.

        Returns:
            bool: True if the title is unique, otherwise False.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        title = self.ui.preset_naming_scripts.itemData(selected)['title'] if new_title is None else new_title
        for i in range(self.ui.preset_naming_scripts.count()):
            if i == selected:
                continue
            if title == self.ui.preset_naming_scripts.itemData(i)['title']:
                return False
        return True

    def update_script_title(self):
        """Update the script selection combo box after updating the script title.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        title = str(self.ui.script_title.text()).strip()
        script_item = self.ui.preset_naming_scripts.itemData(selected)
        if title:
            if self.check_duplicate_script_title(new_title=title):
                script_item['title'] = title
                self.update_combo_box_item(selected, script_item)
                self.save_script()
                self.signal_selection_changed.emit()
            else:
                self.display_error(OptionsCheckError(_("Error"), _("There is already a script with that title.")))
                self.ui.script_title.setFocus()
        else:
            self.display_error(OptionsCheckError(_("Error"), _("The script title must not be empty.")))
            self.ui.script_title.setText(script_item['title'])
            self.ui.script_title.setFocus()

    def populate_script_selector(self):
        """Populate the script selection combo box.
        """
        idx = populate_script_selection_combo_box(self.naming_scripts, self.selected_script_id, self.ui.preset_naming_scripts)
        self.set_selected_script_index(idx)

    def toggle_documentation(self):
        """Toggle the display of the scripting documentation sidebar.
        """
        checked = self.docs_action.isChecked()
        config = get_config()
        config.persist['script_editor_show_documentation'] = checked
        self.ui.documentation_frame.setVisible(checked)

    def view_script_details(self):
        """View and edit the metadata associated with the script.
        """
        self.current_item_dict = self.get_selected_item()
        details_page = ScriptDetailsEditor(self, self.current_item_dict)
        details_page.signal_save.connect(self.update_from_details)
        details_page.show()
        details_page.raise_()
        details_page.activateWindow()

    def update_from_details(self):
        """Update the script selection combo box and script list after updates from the script details dialog.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        new_title = self.current_item_dict['title']
        old_title = self.ui.preset_naming_scripts.itemData(selected)['title']
        if not self.check_duplicate_script_title(new_title=new_title):
            self.current_item_dict['title'] = old_title
        self.update_combo_box_item(selected, self.current_item_dict)
        self.ui.script_title.setText(new_title)
        self.save_script()

    def _set_combobox_index(self, idx):
        """Sets the index of the script selector combo box.

        Args:
            idx (int): New index position
        """
        widget = self.ui.preset_naming_scripts
        widget.blockSignals(True)
        widget.setCurrentIndex(idx)
        widget.blockSignals(False)
        self.selected_script_index = idx
        self.signal_index_changed.emit()

    def _insert_item(self, script_item):
        """Insert a new item into the script selection combo box and update the script list in the settings.

        Args:
            script_item (dict): File naming script to insert as produced by FileNamingScript().to_dict()
        """
        self.selected_script_id = script_item['id']
        self.naming_scripts[self.selected_script_id] = script_item
        idx = populate_script_selection_combo_box(
            self.naming_scripts,
            self.selected_script_id,
            self.ui.preset_naming_scripts
        )
        self._set_combobox_index(idx)
        self.naming_scripts = self.get_scripts_dict()
        self.select_script(update_last_selected=False)
        self.save_script()

    def new_script_name(self, base_title=None):
        """Get new unique script name.
        """
        default_title = base_title if base_title is not None else gettext_constants(DEFAULT_SCRIPT_NAME)
        existing_titles = set(script['title'] for script in self.naming_scripts.values())
        return unique_numbered_title(default_title, existing_titles)

    def new_script(self, script):
        """Add a new script to the script selection combo box and script list.
        """
        script_item = FileNamingScript(script=script)
        script_item.title = self.new_script_name()
        self._insert_item(script_item.to_dict())

    def copy_script(self):
        """Add a copy of the script as a new editable script to the script selection combo box.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        script_item = self.ui.preset_naming_scripts.itemData(selected)
        new_item = FileNamingScript.create_from_dict(script_dict=script_item).copy()

        base_title = "%s %s" % (get_base_title(script_item['title']), gettext_constants(DEFAULT_COPY_TEXT))
        new_item.title = self.new_script_name(base_title)

        self._insert_item(new_item.to_dict())

    def make_it_so(self):
        """Save the scripts and settings to configuration and exit.
        """
        script_item = self.get_selected_item()
        self.selected_script_id = script_item['id']
        self.naming_scripts = self.get_scripts_dict()
        config = get_config()
        config.setting[self.SCRIPTS_LIST_KEY] = self.naming_scripts
        config.setting[self.SELECTED_SCRIPT_KEY] = script_item['id']
        self.close()

    def get_scripts_dict(self):
        """Get dictionary of scripts from the combo box items suitable for saving to the configuration settings.

        Returns:
            dict: Dictionary of scripts
        """
        naming_scripts = {}
        for idx in range(self.ui.preset_naming_scripts.count()):
            script_item = self.ui.preset_naming_scripts.itemData(idx)
            naming_scripts[script_item['id']] = script_item
        return naming_scripts

    def get_selected_item(self, idx=None):
        """Get the specified item from the script selection combo box.

        Args:
            idx (int, optional): Index of the combo box item to retrieve. Defaults to None.

        Returns:
            dict: File naming script dictionary as produced by FileNamingScript().to_dict()
        """
        if idx is None:
            idx = self.ui.preset_naming_scripts.currentIndex()
        return self.ui.preset_naming_scripts.itemData(idx)

    def set_selected_script_id(self, id):
        """Select the script with the specified ID.

        Args:
            id (str): ID of the script to select
        """
        idx = 0
        for i in range(self.ui.preset_naming_scripts.count()):
            script_item = self.ui.preset_naming_scripts.itemData(i)
            if script_item['id'] == id:
                idx = i
                break
        self.set_selected_script_index(idx)

    def set_selected_script_index(self, idx):
        """Select the script at the specified combo box index.

        Args:
            idx (int): Index of the script to select
        """
        self._set_combobox_index(idx)
        self.select_script()

    def select_script(self, update_last_selected=True):
        """Load the current script from the combo box into the editor.
        """
        self.selected_script_index = self.ui.preset_naming_scripts.currentIndex()
        script_item = self.get_selected_item()
        self.ui.script_title.setText(script_item['title'])
        self.ui.file_naming_format.setPlainText(str(script_item['script']).strip())
        self.selected_script_id = script_item['id']
        if update_last_selected:
            self.last_selected_id = self.selected_script_id
        if not self.loading:
            self.save_script()
            self.signal_save.emit()
        self.set_button_states()
        self.update_examples()
        if not self.loading:
            self.signal_selection_changed.emit()

    def update_combo_box_item(self, idx, script_item):
        """Update the title and item data for the specified script selection combo box item.

        Args:
            idx (int): Index of the item to update
            script_item (dict): Updated file naming script information as produced by FileNamingScript().to_dict()
        """
        self.ui.preset_naming_scripts.setItemData(idx, script_item)
        title = script_item['title']
        self.ui.preset_naming_scripts.setItemText(idx, title)
        self.naming_scripts = self.get_scripts_dict()
        if not self.loading:
            self.signal_save.emit()

    def set_selector_states(self, save_enabled=True):
        """Set the script selector enabled states based on the save_enabled state of the currently selected
        item in the script selection combo box.

        Args:
            save_enabled (bool, optional): Allow selection of different script item. Defaults to True.
        """
        self.ui.preset_naming_scripts.setEnabled(save_enabled)
        if self.is_options_ui():
            self.parent().ui.naming_script_selector.setEnabled(save_enabled)
        elif self.is_main_ui():
            self.parent().script_quick_selector_menu.setEnabled(save_enabled)

    def set_button_states(self, save_enabled=True):
        """Set the button states based on the readonly and deletable attributes of the currently selected
        item in the script selection combo box.

        Args:
            save_enabled (bool, optional): Allow updates to be saved to this item. Defaults to True.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        if selected < 0:
            return

        # Script selectors
        self.set_selector_states(save_enabled=save_enabled)

        # Buttons
        self.save_action.setEnabled(save_enabled)
        self.save_button.setEnabled(save_enabled)

        # Menu items
        self.add_action.setEnabled(save_enabled)
        self.copy_action.setEnabled(save_enabled)
        self.delete_action.setEnabled(save_enabled and self.ui.preset_naming_scripts.count() > 1)
        self.import_action.setEnabled(save_enabled)
        self.export_action.setEnabled(save_enabled)

    def match_after_to_before(self):
        """Sets the selected item in the 'after' list to the corresponding item in the 'before' list.
        """
        self.examples.synchronize_selected_example_lines(
            self.examples_current_row,
            self.ui.example_filename_before,
            self.ui.example_filename_after
        )

    def match_before_to_after(self):
        """Sets the selected item in the 'before' list to the corresponding item in the 'after' list.
        """
        self.examples.synchronize_selected_example_lines(
            self.examples_current_row,
            self.ui.example_filename_after,
            self.ui.example_filename_before
        )

    def delete_script(self):
        """Removes the currently selected script from the script selection combo box and script list.
        """
        profile = self.is_used_in_profile()
        if profile is not None:
            QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                _("Error Deleting Script"),
                _(
                    "The script could not be deleted because it is used in one of the user profiles."
                    "\n\n"
                    "Profile: %s"
                ) % profile.title,
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            ).exec_()
            return

        if confirmation_dialog(self, _("Are you sure that you want to delete the script?")):
            widget = self.ui.preset_naming_scripts
            idx = widget.currentIndex()
            widget.blockSignals(True)
            widget.removeItem(idx)
            widget.blockSignals(False)
            if idx >= widget.count():
                idx = widget.count() - 1
            self._set_combobox_index(idx)
            self.selected_script_index = idx
            self.naming_scripts = self.get_scripts_dict()
            self.select_script(update_last_selected=False)

    def is_used_in_profile(self, script_id=None, profiles=None):
        """Check if the script is included in any profile settings.

        Args:
            script_id (str, optional): ID of the script to check or ID of current script if not specified.
            profiles (list, optional): List of Profile named tuples.

        Returns:
            Profile: Named tuple of profile script information if the script is used in a profile otherwise None
        """
        if script_id is None:
            script_id = self.selected_script_id
        if profiles is None:
            profiles = self.scripts_in_profiles()
        for profile in profiles:
            if profile.script_id == script_id:
                return profile
        return None

    def save_script(self):
        """Saves changes to the current script to the script list and combo box item.
        """
        selected = self.ui.preset_naming_scripts.currentIndex()
        title = str(self.ui.script_title.text()).strip()
        if title:
            script_item = self.ui.preset_naming_scripts.itemData(selected)
            if self.check_duplicate_script_title(new_title=title):
                script_item['title'] = title
            script_item['script'] = self.get_script()
            self.update_combo_box_item(selected, script_item)
        else:
            self.display_error(OptionsCheckError(_("Error"), _("The script title must not be empty.")))

    def get_script(self):
        """Provides the text of the file naming script currently loaded into the editor.

        Returns:
            str: File naming script
        """
        return str(self.ui.file_naming_format.toPlainText()).strip()

    def update_example_files(self):
        """Update the before and after file naming examples list.
        """
        self.examples.update_sample_example_files()
        self.display_examples()

    def update_examples(self, script_text=None):
        """Update the before and after file naming examples using the current file naming script in the editor.
        """
        if script_text is None:
            script_text = self.get_script()
        self.examples.update_examples(script_text=script_text)
        self.display_examples()

    def display_examples(self):
        """Update the display of the before and after file naming examples.
        """
        self.examples_current_row = -1
        self.examples.update_example_listboxes(self.ui.example_filename_before, self.ui.example_filename_after)
        if not self.loading:
            self.signal_update.emit()

    def output_file_error(self, fmt, filename, msg):
        """Log file error and display error message dialog.

        Args:
            fmt (str): Format for the error type being displayed
            filename (str): Name of the file being imported or exported
            msg (str): Error message to display
        """
        log.error(fmt, filename, msg)
        error_message = _(fmt) % (filename, _(msg))
        self.display_error(ScriptFileError(_("File Error"), error_message))

    def import_script(self):
        """Import from an external text file to a new script. Import can be either a plain text script or
        a naming script package.
        """
        try:
            script_item = FileNamingScript().import_script(self)
        except ScriptImportExportError as error:
            self.output_file_error(error.format, error.filename, error.error_msg)
            return
        if script_item:
            title = script_item.title.strip()
            for id in self.naming_scripts:
                existing_script = self.naming_scripts[id]
                if title != existing_script['title']:
                    continue
                box = QtWidgets.QMessageBox()
                box.setIcon(QtWidgets.QMessageBox.Icon.Question)
                box.setWindowTitle(_("Confirm"))
                box.setText(
                    _(
                        "A script named \"{script_name}\" already exists.\n"
                        "\n"
                        "Do you want to overwrite it, add as a copy or cancel?"
                    ).format(script_name=title,))
                box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel)
                buttonY = box.button(QtWidgets.QMessageBox.StandardButton.Yes)
                buttonY.setText(_("Overwrite"))
                buttonN = box.button(QtWidgets.QMessageBox.StandardButton.No)
                buttonN.setText(_("Copy"))
                box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)
                box.exec_()

                if box.clickedButton() == buttonY:
                    # Overwrite pressed
                    script_item.id = id
                elif box.clickedButton() == buttonN:
                    # Copy pressed
                    titles = [self.naming_scripts[id]['title'] for id in self.naming_scripts]
                    script_item.title = unique_numbered_title(title, titles)
                else:
                    return

            self._insert_item(script_item.to_dict())

    def export_script(self):
        """Export the current script to an external file. Export can be either as a plain text
        script or a naming script package.
        """
        selected = self.get_selected_item()
        script_item = FileNamingScript.create_from_dict(script_dict=selected, create_new_id=False)
        script_item.title = get_base_title(script_item.title)
        try:
            script_item.export_script(parent=self)
        except ScriptImportExportError as error:
            self.output_file_error(error.format, error.filename, error.error_msg)

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
        if config.setting['rename_files']:
            if not self.get_script():
                raise ScriptCheckError("", _("The file naming format must not be empty."))

    def display_error(self, error):
        """Display an error message for the specified error.

        Args:
            error (Exception): The exception to display.
        """
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning, error.title,
                error.info, QtWidgets.QMessageBox.StandardButton.Ok, self
            )
            dialog.exec_()

    def test(self):
        """Parse the script and display any errors.
        """
        self.ui.renaming_error.setStyleSheet("")
        self.ui.renaming_error.setText("")
        save_enabled = True
        try:
            self.check_format()
            # Update script in combobox item if no errors.
            self.update_script_text()
        except ScriptCheckError as e:
            self.ui.renaming_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.renaming_error.setText(e.info)
            save_enabled = False
        self.set_button_states(save_enabled=save_enabled)


class ScriptDetailsEditor(PicardDialog):
    """View / edit the metadata details for a script.
    """
    NAME = 'scriptdetails'
    TITLE = N_("Script Details")

    signal_save = QtCore.pyqtSignal()

    def __init__(self, parent, script_item):
        """Script metadata viewer / editor.

        Args:
            parent (ScriptEditorDialog): The page used for editing the scripts
            script_item (dict): The script whose metadata is displayed
        """
        super().__init__(parent=parent)
        self.script_item = script_item
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

        self.ui.buttonBox.setFocus()

        self.setModal(True)
        self.setWindowTitle(_(self.TITLE))
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
            _(
                "There are unsaved changes to the current metadata."
                "\n\n"
                "Do you want to continue and lose these changes?"
            ),
        )

    def set_last_updated(self):
        """Set the last updated value to the current timestamp.
        """
        self.ui.script_last_updated.setText(FileNamingScript.make_last_updated())
        self.ui.script_last_updated.setModified(True)

    def save_changes(self):
        """Update the script object with any changes to the metadata.
        """
        title = self.ui.script_title.text().strip()
        if not title:
            QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Critical,
                _("Error"),
                _("The script title must not be empty."),
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            ).exec_()
            return
        if self.has_changed():
            last_updated = self.ui.script_last_updated
            if not last_updated.isModified() or not last_updated.text().strip():
                self.set_last_updated()
            self.script_item['title'] = self.ui.script_title.text().strip()
            self.script_item['author'] = self.ui.script_author.text().strip()
            self.script_item['version'] = self.ui.script_version.text().strip()
            self.script_item['license'] = self.ui.script_license.text().strip()
            self.script_item['description'] = self.ui.script_description.toPlainText().strip()
            self.script_item['last_updated'] = self.ui.script_last_updated.text().strip()
            self.signal_save.emit()
        self.skip_change_check = True
        self.close_window()

    def close_window(self):
        """Close the script metadata editor window.
        """
        self.close()

    def closeEvent(self, event):
        """Custom close event handler to check for unsaved changes.
        """
        if (self.skip_change_check
            or not self.has_changed()
            or (self.has_changed() and self.change_check())):
            event.accept()
        else:
            event.ignore()
