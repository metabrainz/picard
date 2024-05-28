# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2009 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2019-2023 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013-2015, 2017-2024 Laurent Monin
# Copyright (C) 2014 m42i
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Suhas
# Copyright (C) 2018 Vishal Choudhary
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


import os

from PyQt6 import QtCore

from picard import log
from picard.config import get_config
from picard.const.sys import IS_MACOS
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.script import (
    ScriptParser,
    TaggingScriptSetting,
    iter_tagging_scripts_from_config,
    save_tagging_scripts_to_config,
)
from picard.script.serializer import (
    ScriptSerializerImportExportError,
    TaggingScriptInfo,
)

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)
from picard.ui.forms.ui_options_script import Ui_ScriptingOptionsPage
from picard.ui.forms.ui_scripting_documentation_dialog import (
    Ui_ScriptingDocumentationDialog,
)
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
)
from picard.ui.util import qlistwidget_items
from picard.ui.widgets.scriptdocumentation import ScriptingDocumentationWidget
from picard.ui.widgets.scriptlistwidget import ScriptListWidgetItem


class ScriptCheckError(OptionsCheckError):
    pass


class ScriptFileError(OptionsCheckError):
    pass


class ScriptingDocumentationDialog(PicardDialog, SingletonDialog):
    defaultsize = QtCore.QSize(570, 400)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # on macOS having this not a dialog causes the window to be placed
        # behind the options dialog.
        if not IS_MACOS:
            self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.ui = Ui_ScriptingDocumentationDialog()
        self.ui.setupUi(self)
        doc_widget = ScriptingDocumentationWidget(self)
        self.ui.documentation_layout.addWidget(doc_widget)
        self.ui.buttonBox.rejected.connect(self.close)

    def closeEvent(self, event):
        super().closeEvent(event)


class ScriptingOptionsPage(OptionsPage):

    NAME = 'scripting'
    TITLE = N_("Scripting")
    PARENT = None
    SORT_ORDER = 75
    ACTIVE = True
    HELP_URL = "/config/options_scripting.html"

    default_script_directory = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation))
    default_script_extension = "ptsp"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ScriptingOptionsPage()
        self.ui.setupUi(self)
        self.ui.tagger_script.setEnabled(False)
        self.ui.scripting_options_splitter.setStretchFactor(1, 2)
        self.move_view = MoveableListView(self.ui.script_list, self.ui.move_up_button,
                                          self.ui.move_down_button)
        self.ui.scripting_documentation_button.clicked.connect(self.show_scripting_documentation)
        self.ui.scripting_documentation_button.setToolTip(_("Show scripting documentation in new window."))

        self.ui.import_button.clicked.connect(self.import_script)
        self.ui.import_button.setToolTip(_("Import a script file as a new script."))

        self.ui.export_button.clicked.connect(self.export_script)
        self.ui.export_button.setToolTip(_("Export the current script to a file."))

        self.FILE_TYPE_ALL = _("All files") + " (*)"
        self.FILE_TYPE_SCRIPT = _("Picard script files") + " (*.pts *.txt)"
        self.FILE_TYPE_PACKAGE = _("Picard tagging script package") + " (*.ptsp *.yaml)"

        self.ui.script_list.signal_reset_selected_item.connect(self.reset_selected_item)

        self.register_setting('enable_tagger_scripts', ['enable_tagger_scripts'])
        self.register_setting('list_of_scripts', ['script_list'])

    def show_scripting_documentation(self):
        ScriptingDocumentationDialog.show_instance(parent=self)

    def output_error(self, title, fmt, params):
        """Log error and display error message dialog.

        Args:
            title (str): Title to display on the error dialog box
            fmt (str): Format for the error type being displayed
            params: values used for substitution in fmt
        """
        log.error(fmt, params)
        error_message = _(fmt) % params
        self.display_error(ScriptFileError(_(title), error_message))

    def output_file_error(self, error: ScriptSerializerImportExportError):
        """Log file error and display error message dialog.

        Args:
            fmt (str): Format for the error type being displayed
            error (ScriptSerializerImportExportError): The error as a ScriptSerializerImportExportError instance
        """
        params = {
            'filename': error.filename,
            'error': _(error.error_msg)
        }
        self.output_error(_("File Error"), error.format, params)

    def import_script(self):
        """Import from an external text file to a new script. Import can be either a plain text script or
        a Picard script package.
        """
        try:
            tagging_script = TaggingScriptInfo().import_script(self)
        except ScriptSerializerImportExportError as error:
            self.output_file_error(error)
            return
        if tagging_script:
            title = _("%s (imported)") % tagging_script['title']
            script = TaggingScriptSetting(name=title, enabled=False, content=tagging_script['script'])
            list_item = ScriptListWidgetItem(script)
            self.ui.script_list.addItem(list_item)
            self.ui.script_list.setCurrentRow(self.ui.script_list.count() - 1)

    def export_script(self):
        """Export the current script to an external file. Export can be either as a plain text
        script or a naming script package.
        """
        list_items = self.ui.script_list.selectedItems()
        if not list_items:
            return

        list_item = list_items[0]
        content = list_item.script.content
        if content:
            name = list_item.script.name.strip()
            title = name or _("Unnamed Script")
            tagging_script = TaggingScriptInfo(title=title, script=content)
            try:
                tagging_script.export_script(parent=self)
            except ScriptSerializerImportExportError as error:
                self.output_file_error(error)

    def enable_tagger_scripts_toggled(self, on):
        if on and self.ui.script_list.count() == 0:
            self.ui.script_list.add_script()

    def script_selected(self):
        list_items = self.ui.script_list.selectedItems()
        if list_items:
            list_item = list_items[0]
            self.ui.tagger_script.setEnabled(True)
            self.ui.tagger_script.setText(list_item.script.content)
            self.ui.tagger_script.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
            self.ui.export_button.setEnabled(True)
        else:
            self.ui.tagger_script.setEnabled(False)
            self.ui.tagger_script.setText("")
            self.ui.export_button.setEnabled(False)

    def live_update_and_check(self):
        list_items = self.ui.script_list.selectedItems()
        if not list_items:
            return
        list_item = list_items[0]
        list_item.script.content = self.ui.tagger_script.toPlainText()
        self.ui.script_error.setStyleSheet("")
        self.ui.script_error.setText("")
        try:
            self.check()
        except OptionsCheckError as e:
            list_item.has_error = True
            self.ui.script_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.script_error.setText(e.info)
            return
        list_item.has_error = False

    def reset_selected_item(self):
        widget = self.ui.script_list
        widget.setCurrentRow(widget.bad_row)

    def check(self):
        parser = ScriptParser()
        try:
            parser.eval(self.ui.tagger_script.toPlainText())
        except Exception as e:
            raise ScriptCheckError(_("Script Error"), str(e))

    def restore_defaults(self):
        # Remove existing scripts
        self.ui.script_list.clear()
        self.ui.tagger_script.setText("")
        super().restore_defaults()

    def load(self):
        config = get_config()
        self.ui.enable_tagger_scripts.setChecked(config.setting['enable_tagger_scripts'])
        self.ui.script_list.clear()
        for script in iter_tagging_scripts_from_config(config=config):
            list_item = ScriptListWidgetItem(script)
            self.ui.script_list.addItem(list_item)

        # Select the last selected script item
        last_selected_script_pos = config.persist['last_selected_script_pos']
        last_selected_script = self.ui.script_list.item(last_selected_script_pos)
        if last_selected_script:
            self.ui.script_list.setCurrentItem(last_selected_script)
            last_selected_script.setSelected(True)

    def _all_scripts(self):
        for item in qlistwidget_items(self.ui.script_list):
            yield item.get_script()

    def save(self):
        config = get_config()
        config.setting['enable_tagger_scripts'] = self.ui.enable_tagger_scripts.isChecked()
        save_tagging_scripts_to_config(self._all_scripts())
        config.persist['last_selected_script_pos'] = self.ui.script_list.currentRow()

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)


register_options_page(ScriptingOptionsPage)
