# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2013-2015, 2018-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019, 2021-2022, 2024 Philipp Wolfer
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


from html import escape as html_escape

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import PICARD_DISPLAY_NAME
from picard.config import get_config
from picard.const.sys import (
    IS_LINUX,
    IS_MACOS,
    IS_WIN,
)
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import find_existing_path

from picard.ui.enums import MainAction


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
                icon = QtCore.QCoreApplication.instance().style().standardIcon(getattr(QtWidgets.QStyle, iconname))
                args = [icon, label]
        super().__init__(*args)


def find_starting_directory():
    config = get_config()
    if config.setting['starting_directory']:
        path = config.setting['starting_directory_path']
    else:
        path = config.persist['current_directory'] or QtCore.QDir.homePath()
    return find_existing_path(path)


def _picardize_caption(caption):
    return _("%s - %s") % (caption, PICARD_DISPLAY_NAME)


def _filedialog_caption(caption, default_caption=""):
    if not caption:
        caption = default_caption
    return _picardize_caption(caption)


def _filedialog_options(options, default=None):
    if options is None:
        # returns default flags or empty enum flag
        return default or QtWidgets.QFileDialog.Option(0)
    else:
        return options


class FileDialog(QtWidgets.QFileDialog):
    """Wrap QFileDialog & its static methods"""

    def __init__(self, parent=None, caption="", directory="", filter=""):
        if not caption:
            caption = _("Select a file or a directory")
        caption = _picardize_caption(caption)
        super().__init__(parent=parent, caption=caption, directory=directory, filter=filter)

    @staticmethod
    def getSaveFileName(parent=None, caption="", dir="", filter="", selectedFilter="", options=None):
        caption = _filedialog_caption(caption, _("Select a target file"))
        options = _filedialog_options(options)
        return QtWidgets.QFileDialog.getSaveFileName(
            parent=parent, caption=caption, directory=dir,
            filter=filter, initialFilter=selectedFilter, options=options
        )

    @staticmethod
    def getOpenFileName(parent=None, caption="", dir="", filter="", selectedFilter="", options=None):
        caption = _filedialog_caption(caption, _("Select a file"))
        options = _filedialog_options(options)
        return QtWidgets.QFileDialog.getOpenFileName(
            parent=parent, caption=caption, directory=dir,
            filter=filter, initialFilter=selectedFilter, options=options
        )

    @staticmethod
    def getOpenFileNames(parent=None, caption="", dir="", filter="", selectedFilter="", options=None):
        caption = _filedialog_caption(caption, _("Select one or more files"))
        options = _filedialog_options(options)
        return QtWidgets.QFileDialog.getOpenFileNames(
            parent=parent, caption=caption, directory=dir,
            filter=filter, initialFilter=selectedFilter, options=options
        )

    @staticmethod
    def getExistingDirectory(parent=None, caption="", dir="", options=None):
        caption = _filedialog_caption(caption, _("Select a directory"))
        options = _filedialog_options(options, default=QtWidgets.QFileDialog.Option.ShowDirsOnly)
        return QtWidgets.QFileDialog.getExistingDirectory(
            parent=parent, caption=caption, directory=dir, options=options
        )

    @staticmethod
    def getMultipleDirectories(parent=None, caption="", directory="", filter=""):
        """Custom file selection dialog which allows the selection
        of multiple directories.
        Depending on the platform, dialog may fallback on non-native.
        """
        if not caption:
            caption = _("Select one or more directories")
        file_dialog = FileDialog(parent=parent, caption=caption, directory=directory, filter=filter)
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        file_dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly)
        # The native dialog doesn't allow selecting >1 directory
        file_dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog)
        for view in file_dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
            if isinstance(view.model(), QtGui.QFileSystemModel):
                view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        # Allow access to all mounted drives in the sidebar
        root_volume = "/"
        volume_paths = []
        for volume in QtCore.QStorageInfo.mountedVolumes():
            if volume.isValid() and volume.isReady():
                path = volume.rootPath()
                if volume.isRoot():
                    root_volume = path
                else:
                    if not IS_LINUX or (path.startswith("/media/") or path.startswith("/mnt/")):
                        volume_paths.append(path)
        paths = [
            root_volume,
            QtCore.QDir.homePath(),
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.MusicLocation),
        ]
        file_dialog.setSidebarUrls(QtCore.QUrl.fromLocalFile(p) for p in paths + sorted(volume_paths) if p)
        dirs = ()
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            dirs = file_dialog.selectedFiles()
        return tuple(dirs)


def qlistwidget_items(qlistwidget):
    """Yield all items from a QListWidget"""
    for i in range(qlistwidget.count()):
        yield qlistwidget.item(i)


def changes_require_restart_warning(parent, warnings=None, notes=None):
    """Display a warning dialog about modified options requiring a restart"""
    if not warnings:
        return
    text = '<p><ul>'
    for warning in warnings:
        text += '<li>' + html_escape(warning) + '</li>'
    text += "</ul></p>"
    if notes:
        for note in notes:
            text += "<p><em>" + html_escape(note) + "</em></p>"
    text += "<p><strong>" + _("You have to restart Picard for the changes to take effect.") + "</strong></p>"
    QtWidgets.QMessageBox.warning(
        parent,
        _("Changes only applied on restart"),
        text
    )


def menu_builder(menu, main_actions, *args):
    """Adds each argument to menu, depending on their type"""
    for arg in args:
        if arg == '-':
            menu.addSeparator()
        elif isinstance(arg, QtWidgets.QMenu):
            menu.addMenu(arg)
        elif isinstance(arg, MainAction) and main_actions[arg]:
            menu.addAction(main_actions[arg])
        elif isinstance(arg, QtWidgets.QWidgetAction):
            menu.addAction(arg)
