# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2014-2015, 2018-2022 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2011-2013 Wieland Hoffmann
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2015, 2018-2024 Laurent Monin
# Copyright (C) 2015 Alex Berman
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Gabriel Ferreira
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

from PyQt6 import QtWidgets
from PyQt6.QtGui import QPalette

from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.script import ScriptParser

from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    register_options_page,
)
from picard.ui.options.scripting import (
    ScriptCheckError,
    ScriptingDocumentationDialog,
)
from picard.ui.scripteditor import (
    ScriptEditorDialog,
    ScriptEditorExamples,
    populate_script_selection_combo_box,
    synchronize_vertical_scrollbars,
)
from picard.ui.ui_options_renaming import Ui_RenamingOptionsPage


class RenamingOptionsPage(OptionsPage):

    NAME = 'filerenaming'
    TITLE = N_("File Naming")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True
    HELP_URL = "/config/options_filerenaming.html"

    options = [
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.script_text = ""
        self.compat_options = {}
        self.ui = Ui_RenamingOptionsPage()
        self.ui.setupUi(self)

        self.ui.rename_files.clicked.connect(self.update_examples_from_local)
        self.ui.move_files.clicked.connect(self.update_examples_from_local)
        self.ui.move_files_to.editingFinished.connect(self.update_examples_from_local)

        self.ui.move_files.toggled.connect(self.toggle_file_naming_format)
        self.ui.rename_files.toggled.connect(self.toggle_file_naming_format)
        self.toggle_file_naming_format(None)
        self.ui.open_script_editor.clicked.connect(self.show_script_editing_page)
        self.ui.move_files_to_browse.clicked.connect(self.move_files_to_browse)

        self.ui.naming_script_selector.currentIndexChanged.connect(self.update_selector_in_editor)

        self.ui.example_filename_after.itemSelectionChanged.connect(self.match_before_to_after)
        self.ui.example_filename_before.itemSelectionChanged.connect(self.match_after_to_before)

        script_edit = self.ui.move_additional_files_pattern
        self.script_palette_normal = script_edit.palette()
        self.script_palette_readonly = QPalette(self.script_palette_normal)
        disabled_color = self.script_palette_normal.color(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window)
        self.script_palette_readonly.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, disabled_color)

        self.ui.example_filename_sample_files_button.clicked.connect(self.update_example_files)

        self.examples = ScriptEditorExamples(tagger=self.tagger)
        # Script editor dialog object will not be created until it is specifically requested, in order to ensure proper window modality.
        self.script_editor_dialog = None

        self.ui.example_selection_note.setText(self.examples.get_notes_text())
        self.ui.example_filename_sample_files_button.setToolTip(self.examples.get_tooltip_text())

        # Sync example lists vertical scrolling and selection colors
        synchronize_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

        self.current_row = -1

    def update_selector_from_editor(self):
        """Update the script selector combo box from the script editor page.
        """
        self.naming_scripts = self.script_editor_dialog.naming_scripts
        self.selected_naming_script_id = self.script_editor_dialog.selected_script_id
        populate_script_selection_combo_box(self.naming_scripts, self.selected_naming_script_id, self.ui.naming_script_selector)
        self.display_examples()

    def update_selector_from_settings(self):
        """Update the script selector combo box from the settings.
        """
        populate_script_selection_combo_box(self.naming_scripts, self.selected_naming_script_id, self.ui.naming_script_selector)
        self.update_selector_in_editor()

    def update_selector_in_editor(self):
        """Update the selection in the script editor page to match local selection.
        """
        idx = self.ui.naming_script_selector.currentIndex()
        if self.script_editor_dialog:
            self.script_editor_dialog.set_selected_script_index(idx)
        else:
            script_item = self.ui.naming_script_selector.itemData(idx)
            self.script_text = script_item["script"]
            self.selected_naming_script_id = script_item["id"]
            self.examples.update_examples(script_text=self.script_text)
            self.update_examples_from_local()

    def match_after_to_before(self):
        """Sets the selected item in the 'after' list to the corresponding item in the 'before' list.
        """
        self.examples.synchronize_selected_example_lines(self.current_row, self.ui.example_filename_before, self.ui.example_filename_after)

    def match_before_to_after(self):
        """Sets the selected item in the 'before' list to the corresponding item in the 'after' list.
        """
        self.examples.synchronize_selected_example_lines(self.current_row, self.ui.example_filename_after, self.ui.example_filename_before)

    def show_script_editing_page(self):
        self.script_editor_dialog = ScriptEditorDialog.show_instance(parent=self, examples=self.examples)

        self.script_editor_dialog.signal_save.connect(self.save_from_editor)
        self.script_editor_dialog.signal_update.connect(self.display_examples)
        self.script_editor_dialog.signal_selection_changed.connect(self.update_selector_from_editor)
        self.script_editor_dialog.finished.connect(self.script_editor_dialog_close)

        if self.tagger.window.script_editor_dialog is not None:
            self.update_selector_from_editor()
        else:
            self.script_editor_dialog.loading = True
            self.script_editor_dialog.naming_scripts = self.naming_scripts
            self.script_editor_dialog.populate_script_selector()
            self.update_selector_in_editor()
            self.script_editor_dialog.loading = False
            self.update_examples_from_local()
            self.tagger.window.script_editor_dialog = True

    def script_editor_dialog_close(self):
        self.tagger.window.script_editor_dialog = None

    def show_scripting_documentation(self):
        ScriptingDocumentationDialog.show_instance(parent=self)

    def toggle_file_naming_format(self, state):
        active = self.ui.move_files.isChecked() or self.ui.rename_files.isChecked()
        self.ui.open_script_editor.setEnabled(active)

    def save_from_editor(self):
        self.script_text = self.script_editor_dialog.get_script()
        self.update_selector_from_editor()

    def check_formats(self):
        self.test()
        self.update_examples_from_local()

    def update_example_files(self):
        self.examples.update_sample_example_files()
        self.update_displayed_examples()

    def update_examples_from_local(self):
        override = dict(self.compat_options)
        override['move_files'] = self.ui.move_files.isChecked()
        override['move_files_to'] = os.path.normpath(self.ui.move_files_to.text())
        override['rename_files'] = self.ui.rename_files.isChecked()
        self.examples.update_examples(override=override)
        self.update_displayed_examples()

    def update_displayed_examples(self):
        if self.script_editor_dialog is not None:
            # Update examples in script editor which will trigger update locally
            self.script_editor_dialog.display_examples()
        else:
            self.display_examples()

    def display_examples(self):
        self.current_row = -1
        self.examples.update_example_listboxes(self.ui.example_filename_before, self.ui.example_filename_after)

    def load(self):
        # React to changes of compat options
        compat_page = self.dialog.get_page('filerenaming_compat')
        self.compat_options = compat_page.get_options()
        compat_page.options_changed.connect(self.on_compat_options_changed)

        config = get_config()
        self.ui.rename_files.setChecked(config.setting['rename_files'])
        self.ui.move_files.setChecked(config.setting['move_files'])
        self.ui.move_files_to.setText(config.setting['move_files_to'])
        self.ui.move_files_to.setCursorPosition(0)
        self.ui.move_additional_files.setChecked(config.setting['move_additional_files'])
        self.ui.move_additional_files_pattern.setText(config.setting['move_additional_files_pattern'])
        self.ui.delete_empty_dirs.setChecked(config.setting['delete_empty_dirs'])
        self.naming_scripts = config.setting['file_renaming_scripts']
        self.selected_naming_script_id = config.setting['selected_file_naming_script_id']
        if self.script_editor_dialog:
            self.script_editor_dialog.load()
        else:
            self.update_selector_from_settings()
        self.update_examples_from_local()

    def on_compat_options_changed(self, options):
        self.compat_options = options
        self.update_examples_from_local()

    def check(self):
        self.check_format()
        if self.ui.move_files.isChecked() and not self.ui.move_files_to.text().strip():
            raise OptionsCheckError(_("Error"), _("The location to move files to must not be empty."))

    def check_format(self):
        parser = ScriptParser()
        try:
            parser.eval(self.script_text)
        except Exception as e:
            raise ScriptCheckError("", str(e))
        if self.ui.rename_files.isChecked():
            if not self.script_text.strip():
                raise ScriptCheckError("", _("The file naming format must not be empty."))

    def save(self):
        config = get_config()
        config.setting['rename_files'] = self.ui.rename_files.isChecked()
        config.setting['move_files'] = self.ui.move_files.isChecked()
        config.setting['move_files_to'] = os.path.normpath(self.ui.move_files_to.text())
        config.setting['move_additional_files'] = self.ui.move_additional_files.isChecked()
        config.setting['move_additional_files_pattern'] = self.ui.move_additional_files_pattern.text()
        config.setting['delete_empty_dirs'] = self.ui.delete_empty_dirs.isChecked()
        config.setting['selected_file_naming_script_id'] = self.selected_naming_script_id
        self.tagger.window.enable_renaming_action.setChecked(config.setting['rename_files'])
        self.tagger.window.enable_moving_action.setChecked(config.setting['move_files'])
        self.tagger.window.make_script_selector_menu()

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)

    def move_files_to_browse(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "", self.ui.move_files_to.text())
        if path:
            path = os.path.normpath(path)
            self.ui.move_files_to.setText(path)

    def test(self):
        self.ui.renaming_error.setStyleSheet("")
        self.ui.renaming_error.setText("")
        try:
            self.check_format()
        except ScriptCheckError as e:
            self.ui.renaming_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.renaming_error.setText(e.info)
            return


register_options_page(RenamingOptionsPage)
