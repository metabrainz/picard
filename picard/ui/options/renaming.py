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

from PyQt5 import QtWidgets
from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QPalette

from picard.config import (
    BoolOption,
    TextOption,
    get_config,
)
from picard.const import DEFAULT_FILE_NAMING_FORMAT
from picard.const.sys import IS_WIN
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
    ScriptEditorExamples,
    ScriptEditorPage,
)
from picard.ui.ui_options_renaming import Ui_RenamingOptionsPage
from picard.ui.util import enabledSlot


_default_music_dir = QStandardPaths.writableLocation(QStandardPaths.MusicLocation)


class RenamingOptionsPage(OptionsPage):

    NAME = "filerenaming"
    TITLE = N_("File Naming")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True
    HELP_URL = '/config/options_filerenaming.html'

    options = [
        BoolOption("setting", "windows_compatibility", True),
        BoolOption("setting", "ascii_filenames", False),
        BoolOption("setting", "rename_files", False),
        TextOption(
            "setting",
            "file_naming_format",
            DEFAULT_FILE_NAMING_FORMAT,
        ),
        BoolOption("setting", "move_files", False),
        TextOption("setting", "move_files_to", _default_music_dir),
        BoolOption("setting", "move_additional_files", False),
        TextOption("setting", "move_additional_files_pattern", "*.jpg *.png"),
        BoolOption("setting", "delete_empty_dirs", True),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_RenamingOptionsPage()
        self.ui.setupUi(self)

        self.ui.ascii_filenames.clicked.connect(self.update_examples)
        self.ui.windows_compatibility.clicked.connect(self.update_examples)
        self.ui.rename_files.clicked.connect(self.update_examples)
        self.ui.move_files.clicked.connect(self.update_examples)
        self.ui.move_files_to.editingFinished.connect(self.update_examples)

        self.ui.move_files.toggled.connect(
            partial(
                enabledSlot,
                self.toggle_file_moving
            )
        )
        self.ui.rename_files.toggled.connect(
            partial(
                enabledSlot,
                self.toggle_file_renaming
            )
        )
        self.ui.file_naming_format.textChanged.connect(self.check_formats)
        self.ui.file_naming_format_default.clicked.connect(self.set_file_naming_format_default)
        self.ui.open_script_editor.clicked.connect(self.show_script_editing_page)
        self.ui.move_files_to_browse.clicked.connect(self.move_files_to_browse)

        self.ui.example_filename_after.itemSelectionChanged.connect(self.match_before_to_after)
        self.ui.example_filename_before.itemSelectionChanged.connect(self.match_after_to_before)

        script_edit = self.ui.file_naming_format
        self.script_palette_normal = script_edit.palette()
        self.script_palette_readonly = QPalette(self.script_palette_normal)
        disabled_color = self.script_palette_normal.color(QPalette.Inactive, QPalette.Window)
        self.script_palette_readonly.setColor(QPalette.Disabled, QPalette.Base, disabled_color)
        self.ui.scripting_documentation_button.clicked.connect(self.show_scripting_documentation)
        self.ui.example_filename_sample_files_button.clicked.connect(self.update_example_files)
        self.examples = ScriptEditorExamples(self, self)
        self.script_editor_page = ScriptEditorPage(parent=self, examples=self.examples)

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

        # Set highlight colors for selected list items
        # stylesheet = "QListView::item:selected { color: white; background-color: blue; }"
        stylesheet = "QListView::item:selected { color: black; background-color: lightblue; }"
        self.ui.example_filename_after.setStyleSheet(stylesheet)
        self.ui.example_filename_before.setStyleSheet(stylesheet)
        self.current_row = -1

    def match_after_to_before(self):
        if self.ui.example_filename_before.currentRow() != self.current_row:
            self.current_row = self.ui.example_filename_before.currentRow()
            self.ui.example_filename_after.setCurrentRow(self.current_row)

    def match_before_to_after(self):
        if self.ui.example_filename_after.currentRow() != self.current_row:
            self.current_row = self.ui.example_filename_after.currentRow()
            self.ui.example_filename_before.setCurrentRow(self.current_row)

    def show_script_editing_page(self):
        self.script_editor_page.show()
        self.script_editor_page.raise_()
        self.script_editor_page.activateWindow()
        self.update_examples()

    def show_scripting_documentation(self):
        ScriptingDocumentationDialog.show_instance(parent=self)

    def toggle_file_moving(self, state):
        self.toggle_file_naming_format()
        self.ui.delete_empty_dirs.setEnabled(state)
        self.ui.move_files_to.setEnabled(state)
        self.ui.move_files_to_browse.setEnabled(state)
        self.ui.move_additional_files.setEnabled(state)
        self.ui.move_additional_files_pattern.setEnabled(state)

    def toggle_file_renaming(self, state):
        self.toggle_file_naming_format()

    def toggle_file_naming_format(self):
        active = self.ui.move_files.isChecked() or self.ui.rename_files.isChecked()
        self.ui.file_naming_format.setEnabled(active)
        self.ui.file_naming_format_default.setEnabled(active)
        self.ui.open_script_editor.setEnabled(active)
        palette = self.script_palette_normal if active else self.script_palette_readonly
        self.ui.file_naming_format.setPalette(palette)

        self.ui.ascii_filenames.setEnabled(active)
        if not IS_WIN:
            self.ui.windows_compatibility.setEnabled(active)

    def check_formats(self):
        self.test()
        self.update_examples()

    def update_example_files(self):
        self.examples.update_sample_example_files()
        self.update_examples()

    def update_examples(self):
        self.ui.example_filename_before.clear()
        self.ui.example_filename_after.clear()
        self.current_row = -1

        override = {
            'ascii_filenames': self.ui.ascii_filenames.isChecked(),
            'file_naming_format': self.ui.file_naming_format.toPlainText(),
            'move_files': self.ui.move_files.isChecked(),
            'move_files_to': os.path.normpath(self.ui.move_files_to.text()),
            'rename_files': self.ui.rename_files.isChecked(),
            'windows_compatibility': self.ui.windows_compatibility.isChecked(),
        }

        examples = self.examples.get_examples(override=override)
        for before, after in sorted(examples, key=lambda x: x[1]):
            self.ui.example_filename_before.addItem(before)
            self.ui.example_filename_after.addItem(after)

        self.script_editor_page.update_examples(override=override)

    def load(self):
        config = get_config()
        if IS_WIN:
            self.ui.windows_compatibility.setChecked(True)
            self.ui.windows_compatibility.setEnabled(False)
        else:
            self.ui.windows_compatibility.setChecked(config.setting["windows_compatibility"])
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
        if self.ui.move_files.isChecked() and not self.ui.move_files_to.text().strip():
            raise OptionsCheckError(_("Error"), _("The location to move files to must not be empty."))

    def check_format(self):
        parser = ScriptParser()
        try:
            parser.eval(self.ui.file_naming_format.toPlainText())
        except Exception as e:
            raise ScriptCheckError("", str(e))
        if self.ui.rename_files.isChecked():
            if not self.ui.file_naming_format.toPlainText().strip():
                raise ScriptCheckError("", _("The file naming format must not be empty."))

    def save(self):
        config = get_config()
        config.setting["windows_compatibility"] = self.ui.windows_compatibility.isChecked()
        config.setting["ascii_filenames"] = self.ui.ascii_filenames.isChecked()
        config.setting["rename_files"] = self.ui.rename_files.isChecked()
        config.setting["file_naming_format"] = self.ui.file_naming_format.toPlainText()
        self.tagger.window.enable_renaming_action.setChecked(config.setting["rename_files"])
        config.setting["move_files"] = self.ui.move_files.isChecked()
        config.setting["move_files_to"] = os.path.normpath(self.ui.move_files_to.text())
        config.setting["move_additional_files"] = self.ui.move_additional_files.isChecked()
        config.setting["move_additional_files_pattern"] = self.ui.move_additional_files_pattern.text()
        config.setting["delete_empty_dirs"] = self.ui.delete_empty_dirs.isChecked()
        self.tagger.window.enable_moving_action.setChecked(config.setting["move_files"])

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)

    def set_file_naming_format_default(self):
        self.ui.file_naming_format.setText(self.options[3].default)
#        self.ui.file_naming_format.setCursorPosition(0)

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
