# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2013-2015, 2018-2022 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019, 2021-2022 Philipp Wolfer
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

from picard.config import get_config
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.util import find_existing_path


class StandardButton(QtWidgets.QPushButton):

    OK = 0
    CANCEL = 1
    HELP = 2
    CLOSE = 4

    __types = {
        OK: (N_("&Ok"), 'SP_DialogOkButton'),
        CANCEL: (N_("&Cancel"), 'SP_DialogCancelButton'),
        HELP: (N_("&Help"), 'SP_DialogHelpButton'),
        CLOSE: (N_("Clos&e"), 'SP_DialogCloseButton'),
    }

    def __init__(self, btntype):
        label = _(self.__types[btntype][0])
        args = [label]
        if not IS_WIN and not IS_MACOS:
            iconname = self.__types[btntype][1]
            if hasattr(QtWidgets.QStyle, iconname):
                icon = self.tagger.style().standardIcon(getattr(QtWidgets.QStyle, iconname))
                args = [icon, label]
        super().__init__(*args)


def find_starting_directory():
    config = get_config()
    if config.setting['starting_directory']:
        path = config.setting['starting_directory_path']
    else:
        path = config.persist['current_directory'] or QtCore.QDir.homePath()
    return find_existing_path(path)


class MultiDirsSelectDialog(QtWidgets.QFileDialog):

    """Custom file selection dialog which allows the selection
    of multiple directories.
    Depending on the platform, dialog may fallback on non-native.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.setFileMode(self.Directory)
        self.setOption(self.ShowDirsOnly)
        # The native dialog doesn't allow selecting >1 directory
        self.setOption(self.DontUseNativeDialog)
        for view in self.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)


def qlistwidget_items(qlistwidget):
    """Yield all items from a QListWidget"""
    for i in range(qlistwidget.count()):
        yield qlistwidget.item(i)
