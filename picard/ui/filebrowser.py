# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008 Lukáš Lalinský
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2009, 2019-2022 Philipp Wolfer
# Copyright (C) 2011 Andrew Barnert
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013 Wieland Hoffmann
# Copyright (C) 2013, 2017 Sophist-UK
# Copyright (C) 2013, 2018-2022 Laurent Monin
# Copyright (C) 2015 Jeroen Kromwijk
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
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

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt6.QtCore import QStandardPaths

from picard import log
from picard.config import (
    BoolOption,
    TextOption,
    get_config,
)
from picard.const.sys import IS_MACOS
from picard.formats import supported_formats
from picard.util import find_existing_path


def _macos_find_root_volume():
    try:
        for entry in os.scandir("/Volumes/"):
            if entry.is_symlink() and os.path.realpath(entry.path) == "/":
                return entry.path
    except OSError:
        log.warning("Could not detect macOS boot volume", exc_info=True)
    return None


def _macos_extend_root_volume_path(path):
    if not path.startswith("/Volumes/"):
        root_volume = _macos_find_root_volume()
        if root_volume:
            if path.startswith("/"):
                path = path[1:]
            path = os.path.join(root_volume, path)
    return path


_default_current_browser_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)

if IS_MACOS:
    _default_current_browser_path = _macos_extend_root_volume_path(_default_current_browser_path)


class FileBrowser(QtWidgets.QTreeView):

    options = [
        TextOption('persist', 'current_browser_path', _default_current_browser_path),
        BoolOption('persist', 'show_hidden_files', False),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.load_selected_files_action = QtGui.QAction(_("&Load selected files"), self)
        self.load_selected_files_action.triggered.connect(self.load_selected_files)
        self.addAction(self.load_selected_files_action)
        self.move_files_here_action = QtGui.QAction(_("&Move tagged files here"), self)
        self.move_files_here_action.triggered.connect(self.move_files_here)
        self.addAction(self.move_files_here_action)
        self.toggle_hidden_action = QtGui.QAction(_("Show &hidden files"), self)
        self.toggle_hidden_action.setCheckable(True)
        config = get_config()
        self.toggle_hidden_action.setChecked(config.persist['show_hidden_files'])
        self.toggle_hidden_action.toggled.connect(self.show_hidden)
        self.addAction(self.toggle_hidden_action)
        self.set_as_starting_directory_action = QtGui.QAction(_("&Set as starting directory"), self)
        self.set_as_starting_directory_action.triggered.connect(self.set_as_starting_directory)
        self.addAction(self.set_as_starting_directory_action)
        self.doubleClicked.connect(self.load_file_for_item)
        self.focused = False

    def showEvent(self, event):
        if not self.model():
            self._set_model()

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.load_selected_files_action)
        menu.addSeparator()
        menu.addAction(self.move_files_here_action)
        menu.addAction(self.toggle_hidden_action)
        menu.addAction(self.set_as_starting_directory_action)
        menu.exec(event.globalPos())
        event.accept()

    def _set_model(self):
        model = QtGui.QFileSystemModel()
        self.setModel(model)
        model.layoutChanged.connect(self._layout_changed)
        model.setRootPath("")
        self._set_model_filter()
        filters = []
        for exts, name in supported_formats():
            filters.extend("*" + e for e in exts)
        model.setNameFilters(filters)
        # Hide unsupported files completely
        model.setNameFilterDisables(False)
        model.sort(0, QtCore.Qt.SortOrder.AscendingOrder)
        if IS_MACOS:
            self.setRootIndex(model.index("/Volumes"))
        header = self.header()
        header.hideSection(1)
        header.hideSection(2)
        header.hideSection(3)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        header.setVisible(False)

    def _set_model_filter(self):
        config = get_config()
        model_filter = QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.Files | QtCore.QDir.Filter.Drives | QtCore.QDir.Filter.NoDotAndDotDot
        if config.persist['show_hidden_files']:
            model_filter |= QtCore.QDir.Filter.Hidden
        self.model().setFilter(model_filter)

    def _layout_changed(self):
        def scroll():
            # XXX The currentIndex seems to change while QFileSystemModel is
            # populating itself (so setCurrentIndex in __init__ won't last).
            # The time it takes to load varies and there are no signals to find
            # out when it's done. As a workaround, keep restoring the state as
            # long as the layout is updating, and the user hasn't focused yet.
            if not self.focused:
                self._restore_state()
            self.scrollTo(self.currentIndex())
        QtCore.QTimer.singleShot(0, scroll)

    def scrollTo(self, index, scrolltype=QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible):
        # QTreeView.scrollTo resets the horizontal scroll position to 0.
        # Reimplemented to instead scroll to horizontal parent position or keep previous position.
        config = get_config()
        if index and config.setting['filebrowser_horizontal_autoscroll']:
            level = -1
            parent = index.parent()
            root = self.rootIndex()
            while parent.isValid() and parent != root:
                parent = parent.parent()
                level += 1
            pos_x = max(self.indentation() * level, 0)
        else:
            pos_x = self.horizontalScrollBar().value()
        super().scrollTo(index, scrolltype)
        self.horizontalScrollBar().setValue(pos_x)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        index = self.indexAt(event.pos())
        if index.isValid():
            self.selectionModel().setCurrentIndex(index, QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)

    def focusInEvent(self, event):
        self.focused = True
        super().focusInEvent(event)

    def show_hidden(self, state):
        config = get_config()
        config.persist['show_hidden_files'] = state
        self._set_model_filter()

    def save_state(self):
        indexes = self.selectedIndexes()
        if indexes:
            path = self.model().filePath(indexes[0])
            config = get_config()
            config.persist['current_browser_path'] = os.path.normpath(path)

    def restore_state(self):
        pass

    def _restore_state(self):
        config = get_config()
        if config.setting['starting_directory']:
            path = config.setting['starting_directory_path']
            scrolltype = QtWidgets.QAbstractItemView.ScrollHint.PositionAtTop
        else:
            path = config.persist['current_browser_path']
            scrolltype = QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter
        if path:
            index = self.model().index(find_existing_path(path))
            self.setCurrentIndex(index)
            self.expand(index)
            self.scrollTo(index, scrolltype)

    def _get_destination_from_path(self, path):
        destination = os.path.normpath(path)
        if not os.path.isdir(destination):
            destination = os.path.dirname(destination)
        return destination

    def load_file_for_item(self, index):
        model = self.model()
        if not model.isDir(index):
            QtCore.QObject.tagger.add_paths([
                model.filePath(index)
            ])

    def load_selected_files(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        paths = set(self.model().filePath(index) for index in indexes)
        QtCore.QObject.tagger.add_paths(paths)

    def move_files_here(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        config = get_config()
        path = self.model().filePath(indexes[0])
        config.setting['move_files_to'] = self._get_destination_from_path(path)

    def set_as_starting_directory(self):
        indexes = self.selectedIndexes()
        if indexes:
            config = get_config()
            path = self.model().filePath(indexes[0])
            config.setting['starting_directory_path'] = self._get_destination_from_path(path)
