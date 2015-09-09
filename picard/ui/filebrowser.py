# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os
import sys
from PyQt4 import QtCore, QtGui
from picard import config
from picard.formats import supported_formats
from picard.util import find_existing_path


class FileBrowser(QtGui.QTreeView):

    options = [
        config.TextOption("persist", "current_browser_path", ""),
        config.BoolOption("persist", "show_hidden_files", False),
    ]

    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.move_files_here_action = QtGui.QAction(_("&Move Tagged Files Here"), self)
        self.move_files_here_action.triggered.connect(self.move_files_here)
        self.addAction(self.move_files_here_action)
        self.toggle_hidden_action = QtGui.QAction(_("Show &Hidden Files"), self)
        self.toggle_hidden_action.setCheckable(True)
        self.toggle_hidden_action.setChecked(config.persist["show_hidden_files"])
        self.toggle_hidden_action.toggled.connect(self.show_hidden)
        self.addAction(self.toggle_hidden_action)
        self.set_as_starting_directory_action = QtGui.QAction(_("&Set as starting directory"), self)
        self.set_as_starting_directory_action.triggered.connect(self.set_as_starting_directory)
        self.addAction(self.set_as_starting_directory_action)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.focused = False
        self._set_model()

    def _set_model(self):
        self.model = QtGui.QFileSystemModel()
        self.model.layoutChanged.connect(self._layout_changed)
        self.model.setRootPath("")
        self._set_model_filter()
        filters = []
        for exts, name in supported_formats():
            filters.extend("*" + e for e in exts)
        self.model.setNameFilters(filters)
        # Hide unsupported files completely
        self.model.setNameFilterDisables(False)
        self.model.sort(0, QtCore.Qt.AscendingOrder)
        self.setModel(self.model)
        if sys.platform == "darwin":
            self.setRootIndex(self.model.index("/Volumes"))
        header = self.header()
        header.hideSection(1)
        header.hideSection(2)
        header.hideSection(3)
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        header.setVisible(False)

    def _set_model_filter(self):
        filter = QtCore.QDir.AllDirs | QtCore.QDir.Files | QtCore.QDir.Drives | QtCore.QDir.NoDotAndDotDot
        if config.persist["show_hidden_files"]:
            filter |= QtCore.QDir.Hidden
        self.model.setFilter(filter)

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

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.NoUpdate)
        QtGui.QTreeView.mousePressEvent(self, event)

    def focusInEvent(self, event):
        self.focused = True
        QtGui.QTreeView.focusInEvent(self, event)

    def show_hidden(self, state):
        config.persist["show_hidden_files"] = state
        self._set_model_filter()

    def save_state(self):
        indexes = self.selectedIndexes()
        if indexes:
            path = self.model.filePath(indexes[0])
            config.persist["current_browser_path"] = os.path.normpath(unicode(path))

    def restore_state(self):
        pass

    def _restore_state(self):
        if config.setting["starting_directory"]:
            path = config.setting["starting_directory_path"]
            scrolltype = QtGui.QAbstractItemView.PositionAtTop
        else:
            path = config.persist["current_browser_path"]
            scrolltype = QtGui.QAbstractItemView.PositionAtCenter
        if path:
            index = self.model.index(find_existing_path(unicode(path)))
            self.setCurrentIndex(index)
            self.expand(index)
            self.scrollTo(index, scrolltype)

    def move_files_here(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        path = self.model.filePath(indexes[0])
        config.setting["move_files_to"] = os.path.normpath(unicode(path))

    def set_as_starting_directory(self):
        indexes = self.selectedIndexes()
        if indexes:
            path = self.model.filePath(indexes[0])
            config.setting["starting_directory_path"] = os.path.normpath(unicode(path))
