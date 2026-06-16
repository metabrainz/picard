# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2014-2015, 2018-2022, 2024-2025 Philipp Wolfer
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

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.forms.ui_options_renaming import Ui_RenamingOptionsPage
from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    PageOptionConfigs,
)
from picard.ui.scripteditor.examples import ScriptEditorExamples
from picard.ui.scripteditor.utils import (
    populate_script_selection_combo_box,
    synchronize_vertical_scrollbars,
)
from picard.ui.util import FileDialog


class RenamingOptionsPage(OptionsPage):
    NAME = 'filerenaming'
    TITLE = N_("File Naming")
    PARENT = None
    SORT_ORDER = 40
    ACTIVE = True
    HELP_URL = "/config/options_filerenaming.html"

    OPTIONS: PageOptionConfigs = {
        'move_files': {'widgets': ['move_files']},
        'move_files_to': {'widgets': ['move_files_to']},
        'move_overwrite_existing_files': {'widgets': ['move_overwrite_existing_files']},
        'move_additional_files': {'widgets': ['move_additional_files']},
        'move_additional_files_pattern': {'widgets': ['move_additional_files_pattern']},
        'delete_empty_dirs': {'widgets': ['delete_empty_dirs']},
        'rename_files': {'widgets': ['rename_files']},
        'active_file_naming_script_id': {'widgets': ['naming_script_selector']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_RenamingOptionsPage()
        self.ui.setupUi(self)

        # Set open directory icon on folder browse button
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon)
        self.ui.move_files_to_browse.setIcon(icon)
        self.ui.move_files_to_browse.clicked.connect(self.move_files_to_browse)

        self.ui.naming_script_selector.currentIndexChanged.connect(self._update_examples)
        self.ui.rename_files.toggled.connect(self._update_examples)
        self.ui.move_files.toggled.connect(self._update_examples)
        self.ui.move_files_to.editingFinished.connect(self._update_examples)

        self.examples = ScriptEditorExamples(tagger=self.tagger)
        synchronize_vertical_scrollbars((self.ui.example_filename_before, self.ui.example_filename_after))

    def load(self):
        config = get_config()
        self.ui.rename_files.setChecked(config.setting['rename_files'])
        self.ui.move_files.setChecked(config.setting['move_files'])
        self.ui.move_files_to.setText(config.setting['move_files_to'])
        self.ui.move_files_to.setCursorPosition(0)
        self.ui.move_additional_files.setChecked(config.setting['move_additional_files'])
        self.ui.move_additional_files_pattern.setText(config.setting['move_additional_files_pattern'])
        self.ui.delete_empty_dirs.setChecked(config.setting['delete_empty_dirs'])
        self.ui.move_overwrite_existing_files.setChecked(config.setting['move_overwrite_existing_files'])
        populate_script_selection_combo_box(
            config.setting['file_renaming_scripts'],
            config.setting['active_file_naming_script_id'],
            self.ui.naming_script_selector,
        )
        self._update_examples()

    def check(self):
        if self.ui.move_files.isChecked() and not self.ui.move_files_to.text().strip():
            raise OptionsCheckError(_("Error"), _("The location to move files to must not be empty."))

    def save(self):
        config = get_config()
        config.setting['rename_files'] = self.ui.rename_files.isChecked()
        config.setting['move_files'] = self.ui.move_files.isChecked()
        config.setting['move_files_to'] = os.path.normpath(self.ui.move_files_to.text())
        config.setting['move_additional_files'] = self.ui.move_additional_files.isChecked()
        config.setting['move_additional_files_pattern'] = self.ui.move_additional_files_pattern.text()
        config.setting['delete_empty_dirs'] = self.ui.delete_empty_dirs.isChecked()
        config.setting['move_overwrite_existing_files'] = self.ui.move_overwrite_existing_files.isChecked()
        idx = self.ui.naming_script_selector.currentIndex()
        script_item = self.ui.naming_script_selector.itemData(idx)
        if script_item and script_item['id'] in config.setting['file_renaming_scripts']:
            config.setting['active_file_naming_script_id'] = script_item['id']

    def _update_examples(self):
        """Update the file naming examples based on current settings."""
        idx = self.ui.naming_script_selector.currentIndex()
        script_item = self.ui.naming_script_selector.itemData(idx)
        if script_item:
            override = {
                'rename_files': self.ui.rename_files.isChecked(),
                'move_files': self.ui.move_files.isChecked(),
                'move_files_to': os.path.normpath(self.ui.move_files_to.text()),
            }
            self.examples.update_examples(script_text=script_item['script'], override=override)
            self.examples.update_example_listboxes(
                self.ui.example_filename_before,
                self.ui.example_filename_after,
            )

    def move_files_to_browse(self):
        path = FileDialog.getExistingDirectory(
            parent=self,
            directory=self.ui.move_files_to.text(),
        )
        if path:
            path = os.path.normpath(path)
            self.ui.move_files_to.setText(path)


register_options_page(RenamingOptionsPage)
