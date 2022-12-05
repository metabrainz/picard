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
# Copyright (C) 2013-2015, 2018-2021 Laurent Monin
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

import re

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.config import (
    BoolOption,
    Option,
    TextOption,
    get_config,
)
from picard.const.sys import IS_WIN
from picard.util import system_supports_long_paths

from picard.ui import PicardDialog
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_renaming_compat import Ui_RenamingCompatOptionsPage
from picard.ui.ui_win_compat_dialog import Ui_WinCompatDialog


DEFAULT_REPLACEMENT = '_'


class RenamingCompatOptionsPage(OptionsPage):

    NAME = "filerenaming_compat"
    TITLE = N_("Compatibility")
    PARENT = "filerenaming"
    ACTIVE = True
    HELP_URL = '/config/options_filerenaming_compat.html'

    options = [
        BoolOption("setting", "windows_compatibility", True),
        BoolOption("setting", "windows_long_paths", system_supports_long_paths() if IS_WIN else False),
        BoolOption("setting", "ascii_filenames", False),
        BoolOption("setting", "replace_spaces_with_underscores", False),
        TextOption("setting", "replace_dir_separator", DEFAULT_REPLACEMENT),
        Option("setting", "win_compat_replacements", {
            '*': DEFAULT_REPLACEMENT,
            ':': DEFAULT_REPLACEMENT,
            '<': DEFAULT_REPLACEMENT,
            '>': DEFAULT_REPLACEMENT,
            '?': DEFAULT_REPLACEMENT,
            '|': DEFAULT_REPLACEMENT,
            '"': DEFAULT_REPLACEMENT,
        })
    ]

    options_changed = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        config = get_config()
        self.win_compat_replacements = config.setting["win_compat_replacements"]
        self.ui = Ui_RenamingCompatOptionsPage()
        self.ui.setupUi(self)
        self.ui.ascii_filenames.toggled.connect(self.on_options_changed)
        self.ui.windows_compatibility.toggled.connect(self.on_options_changed)
        self.ui.windows_long_paths.toggled.connect(self.on_options_changed)
        self.ui.replace_spaces_with_underscores.toggled.connect(self.on_options_changed)
        self.ui.replace_dir_separator.textChanged.connect(self.on_options_changed)
        self.ui.btn_windows_compatibility_change.clicked.connect(self.open_win_compat_dialog)

    def load(self):
        config = get_config()
        self.win_compat_replacements = config.setting["win_compat_replacements"]
        try:
            self.ui.windows_long_paths.toggled.disconnect(self.toggle_windows_long_paths)
        except TypeError:
            pass
        if IS_WIN:
            self.ui.windows_compatibility.setChecked(True)
            self.ui.windows_compatibility.setEnabled(False)
        else:
            self.ui.windows_compatibility.setChecked(config.setting["windows_compatibility"])
        self.ui.windows_long_paths.setChecked(config.setting["windows_long_paths"])
        self.ui.ascii_filenames.setChecked(config.setting["ascii_filenames"])
        self.ui.replace_spaces_with_underscores.setChecked(config.setting["replace_spaces_with_underscores"])
        self.ui.replace_dir_separator.setText(config.setting["replace_dir_separator"])
        self.ui.windows_long_paths.toggled.connect(self.toggle_windows_long_paths)

    def save(self):
        config = get_config()
        options = self.get_options()
        for key, value in options.items():
            config.setting[key] = value

    def toggle_windows_long_paths(self, state):
        if state and not system_supports_long_paths():
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Information,
                _('Windows long path support'),
                _(
                    'Enabling long paths on Windows might cause files being saved with path names '
                    'exceeding the 259 character limit traditionally imposed by the Windows API. '
                    'Some software might not be able to properly access those files.'
                ),
                QtWidgets.QMessageBox.StandardButton.Ok,
                self)
            dialog.exec_()

    def on_options_changed(self):
        self.options_changed.emit(self.get_options())

    def get_options(self):
        return {
            'ascii_filenames': self.ui.ascii_filenames.isChecked(),
            'windows_compatibility': self.ui.windows_compatibility.isChecked(),
            'windows_long_paths': self.ui.windows_long_paths.isChecked(),
            'replace_spaces_with_underscores': self.ui.replace_spaces_with_underscores.isChecked(),
            'replace_dir_separator': self.ui.replace_dir_separator.text(),
            'win_compat_replacements': self.win_compat_replacements,
        }

    def open_win_compat_dialog(self):
        dialog = WinCompatDialog(self.win_compat_replacements, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.DialogCode.Accepted:
            self.win_compat_replacements = dialog.replacements
            self.on_options_changed()


class WinCompatReplacementValidator(QtGui.QValidator):
    _re_valid_win_replacement = re.compile(r'^[^"*:<>?|/\\\s]?$')

    def validate(self, text: str, pos):
        if self._re_valid_win_replacement.match(text):
            state = QtGui.QValidator.State.Acceptable
        else:
            state = QtGui.QValidator.State.Invalid
        return state, text, pos


class WinCompatDialog(PicardDialog):
    def __init__(self, replacements, parent=None):
        super().__init__(parent)
        self.replacements = dict(replacements)
        self.ui = Ui_WinCompatDialog()
        self.ui.setupUi(self)
        self.ui.replace_asterisk.setValidator(WinCompatReplacementValidator())
        self.ui.replace_colon.setValidator(WinCompatReplacementValidator())
        self.ui.replace_gt.setValidator(WinCompatReplacementValidator())
        self.ui.replace_lt.setValidator(WinCompatReplacementValidator())
        self.ui.replace_pipe.setValidator(WinCompatReplacementValidator())
        self.ui.replace_questionmark.setValidator(WinCompatReplacementValidator())
        self.ui.replace_quotationmark.setValidator(WinCompatReplacementValidator())
        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        reset_button = QtWidgets.QPushButton(_("Restore &Defaults"))
        self.ui.buttonbox.addButton(reset_button, QtWidgets.QDialogButtonBox.ButtonRole.ResetRole)
        reset_button.clicked.connect(self.restore_defaults)
        self.load()

    def load(self):
        self.ui.replace_asterisk.setText(self.replacements['*'])
        self.ui.replace_colon.setText(self.replacements[':'])
        self.ui.replace_gt.setText(self.replacements['>'])
        self.ui.replace_lt.setText(self.replacements['<'])
        self.ui.replace_pipe.setText(self.replacements['|'])
        self.ui.replace_questionmark.setText(self.replacements['?'])
        self.ui.replace_quotationmark.setText(self.replacements['"'])

    def accept(self):
        self.replacements['*'] = self.ui.replace_asterisk.text()
        self.replacements[':'] = self.ui.replace_colon.text()
        self.replacements['>'] = self.ui.replace_gt.text()
        self.replacements['<'] = self.ui.replace_lt.text()
        self.replacements['|'] = self.ui.replace_pipe.text()
        self.replacements['?'] = self.ui.replace_questionmark.text()
        self.replacements['"'] = self.ui.replace_quotationmark.text()
        super().accept()

    def restore_defaults(self):
        self.ui.replace_asterisk.setText(DEFAULT_REPLACEMENT)
        self.ui.replace_colon.setText(DEFAULT_REPLACEMENT)
        self.ui.replace_gt.setText(DEFAULT_REPLACEMENT)
        self.ui.replace_lt.setText(DEFAULT_REPLACEMENT)
        self.ui.replace_pipe.setText(DEFAULT_REPLACEMENT)
        self.ui.replace_questionmark.setText(DEFAULT_REPLACEMENT)
        self.ui.replace_quotationmark.setText(DEFAULT_REPLACEMENT)


register_options_page(RenamingCompatOptionsPage)
