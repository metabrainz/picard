# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2009 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2019-2021 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013-2015, 2017-2020 Laurent Monin
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

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    get_config,
)
from picard.const.sys import IS_MACOS
from picard.script import ScriptParser
from picard.script.serializer import (
    PicardScript,
    ScriptImportError,
)

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_script import Ui_ScriptingOptionsPage
from picard.ui.ui_scripting_documentation_dialog import (
    Ui_ScriptingDocumentationDialog,
)
from picard.ui.widgets.scriptdocumentation import ScriptingDocumentationWidget
from picard.ui.widgets.scriptlistwidget import ScriptListWidgetItem


class ScriptCheckError(OptionsCheckError):
    pass


class ScriptFileError(OptionsCheckError):
    pass


class ScriptingDocumentationDialog(PicardDialog, SingletonDialog):
    defaultsize = QtCore.QSize(570, 400)

    def __init__(self, parent):
        super().__init__(parent)
        # on macOS having this not a dialog causes the window to be placed
        # behind the options dialog.
        if not IS_MACOS:
            self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.parent = parent
        self.ui = Ui_ScriptingDocumentationDialog()
        self.ui.setupUi(self)
        doc_widget = ScriptingDocumentationWidget(self)
        self.ui.documentation_layout.addWidget(doc_widget)
        self.ui.buttonBox.rejected.connect(self.close)

    def closeEvent(self, event):
        super().closeEvent(event)


class ScriptingOptionsPage(OptionsPage):

    NAME = "scripting"
    TITLE = N_("Scripting")
    PARENT = None
    SORT_ORDER = 85
    ACTIVE = True
    HELP_URL = '/config/options_scripting.html'

    options = [
        BoolOption("setting", "enable_tagger_scripts", False),
        ListOption("setting", "list_of_scripts", []),
        IntOption("persist", "last_selected_script_pos", 0),
    ]

    default_script_directory = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation))
    default_script_filename = "picard_tagging_script.ptsp"

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

        self.FILE_TYPE_ALL = _("All Files") + " (*)"
        self.FILE_TYPE_SCRIPT = _("Picard Script Files") + " (*.pts *.txt)"
        self.FILE_TYPE_PACKAGE = _("Picard Tagging Script Package") + " (*.ptsp *.yaml)"

    def show_scripting_documentation(self):
        ScriptingDocumentationDialog.show_instance(parent=self)

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
        a Picard script package.
        """
        FILE_ERROR_IMPORT = N_('Error importing "%s". %s.')
        FILE_ERROR_DECODE = N_('Error decoding "%s". %s.')

        dialog_title = _("Import Script File")
        dialog_file_types = self._get_dialog_filetypes()
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, file_type = QtWidgets.QFileDialog.getOpenFileName(self, dialog_title, self.default_script_directory, dialog_file_types, options=options)
        if filename:
            log.debug('Importing tagging script file: %s' % filename)
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
                    script_item = PicardScript().create_from_yaml(file_content)
                except ScriptImportError as error:
                    self.output_file_error(FILE_ERROR_DECODE, filename, error)
                    return
            else:
                script_item = PicardScript(
                    title=_("Imported from %s") % filename,
                    script=file_content.strip()
                )
            title = _("%s (imported)") % script_item["title"]
            list_item = ScriptListWidgetItem(title, False, script_item["script"])
            self.ui.script_list.addItem(list_item)
            self.ui.script_list.setCurrentRow(self.ui.script_list.count() - 1)

    def export_script(self):
        """Export the current script to an external file. Export can be either as a plain text
        script or a naming script package.
        """
        FILE_ERROR_EXPORT = N_('Error exporting file "%s". %s.')

        items = self.ui.script_list.selectedItems()
        if not items:
            return

        item = items[0]
        script_text = item.script
        script_title = item.name if item.name.strip() else _("Unnamed Script")

        if script_text:
            script_item = PicardScript(title=script_title, script=script_text)
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

    def enable_tagger_scripts_toggled(self, on):
        if on and self.ui.script_list.count() == 0:
            self.ui.script_list.add_script()

    def script_selected(self):
        items = self.ui.script_list.selectedItems()
        if items:
            item = items[0]
            self.ui.tagger_script.setEnabled(True)
            self.ui.tagger_script.setText(item.script)
            self.ui.tagger_script.setFocus(QtCore.Qt.OtherFocusReason)
            self.ui.export_button.setEnabled(True)
        else:
            self.ui.tagger_script.setEnabled(False)
            self.ui.tagger_script.setText("")
            self.ui.export_button.setEnabled(False)

    def live_update_and_check(self):
        items = self.ui.script_list.selectedItems()
        if items:
            script = items[0]
            script.script = self.ui.tagger_script.toPlainText()
        self.ui.script_error.setStyleSheet("")
        self.ui.script_error.setText("")
        try:
            self.check()
        except OptionsCheckError as e:
            self.ui.script_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.script_error.setText(e.info)
            return

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
        self.ui.enable_tagger_scripts.setChecked(config.setting["enable_tagger_scripts"])
        self.ui.script_list.clear()
        for pos, name, enabled, text in config.setting["list_of_scripts"]:
            list_item = ScriptListWidgetItem(name, enabled, text)
            self.ui.script_list.addItem(list_item)

        # Select the last selected script item
        last_selected_script_pos = config.persist["last_selected_script_pos"]
        last_selected_script = self.ui.script_list.item(last_selected_script_pos)
        if last_selected_script:
            self.ui.script_list.setCurrentItem(last_selected_script)
            last_selected_script.setSelected(True)

    def _all_scripts(self):
        for row in range(0, self.ui.script_list.count()):
            item = self.ui.script_list.item(row)
            yield item.get_all()

    def save(self):
        config = get_config()
        config.setting["enable_tagger_scripts"] = self.ui.enable_tagger_scripts.isChecked()
        config.setting["list_of_scripts"] = list(self._all_scripts())
        config.persist["last_selected_script_pos"] = self.ui.script_list.currentRow()

    def display_error(self, error):
        # Ignore scripting errors, those are handled inline
        if not isinstance(error, ScriptCheckError):
            super().display_error(error)


register_options_page(ScriptingOptionsPage)
