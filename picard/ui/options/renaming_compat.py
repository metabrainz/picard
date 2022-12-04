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


from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.config import (
    BoolOption,
    get_config,
)
from picard.const.sys import IS_WIN
from picard.util import system_supports_long_paths

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_renaming_compat import Ui_RenamingCompatOptionsPage


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
    ]

    options_changed = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_RenamingCompatOptionsPage()
        self.ui.setupUi(self)
        self.ui.ascii_filenames.toggled.connect(self.on_options_changed)
        self.ui.windows_compatibility.toggled.connect(self.on_options_changed)
        self.ui.windows_long_paths.toggled.connect(self.on_options_changed)

    def load(self):
        config = get_config()
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
        }


register_options_page(RenamingCompatOptionsPage)
