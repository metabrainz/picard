# -*- coding: UTF-8 -*-
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

import sys
from PyQt4 import QtCore, QtGui
from picard.formats import supported_formats
from picard.config import Option, TextOption, BoolOption
from picard.util import find_existing_path

class FileBrowser(QtGui.QTreeView):

    options = [
        TextOption("persist", "current_browser_path", ""),
        BoolOption("persist", "show_hidden_files", False),
    ]

    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.refresh_action = QtGui.QAction(_("&Refresh"), self)
        self.connect(self.refresh_action, QtCore.SIGNAL("triggered()"), self.refresh)
        self.addAction(self.refresh_action)
        self.toggle_hidden_action = QtGui.QAction(_("Show &hidden files"), self)
        self.toggle_hidden_action.setCheckable(True)
        self.toggle_hidden_action.setChecked(self.config.persist["show_hidden_files"])
        self.connect(self.toggle_hidden_action, QtCore.SIGNAL("toggled(bool)"), self.show_hidden)
        self.addAction(self.toggle_hidden_action)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self._set_model()
        self._restore_state()

    def showEvent(self, event):
        self.refresh()
        QtGui.QTreeView.showEvent(self, event)

    def _set_model(self):
        self.dirmodel = QtGui.QDirModel()
        self.dirmodel.setLazyChildCount(True)
        if sys.platform == "win32":
            self.dirmodel.setSorting(QtCore.QDir.Name | QtCore.QDir.DirsFirst | QtCore.QDir.IgnoreCase)
        else:
            self.dirmodel.setSorting(QtCore.QDir.Name | QtCore.QDir.DirsFirst)
        self._set_model_filter()
        filters = []
        for exts, name in supported_formats():
            filters.extend("*" + e for e in exts)
        self.dirmodel.setNameFilters(filters)
        self.setModel(self.dirmodel)
        header = self.header()
        header.hideSection(1)
        header.hideSection(2)
        header.hideSection(3)
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        header.setVisible(False)
        
    def _set_model_filter(self):
        filter = QtCore.QDir.AllDirs | QtCore.QDir.Files | QtCore.QDir.Drives | QtCore.QDir.NoDotAndDotDot
        if self.config.persist["show_hidden_files"]:
            filter |= QtCore.QDir.Hidden
        self.dirmodel.setFilter(filter)
        
    def startDrag(self, supportedActions):
        indexes = self.selectedIndexes()
        if len(indexes):
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.model().mimeData(indexes)) 
            if drag.start(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
                pass

    def refresh(self):
        for index in self.selectedIndexes():
            self.dirmodel.refresh(index)
            self.scrollTo(index)
            self.expand(index)
            
    def show_hidden(self, state):
        self.config.persist["show_hidden_files"] = state
        if self.isVisible():
            self._set_model_filter()

    def save_state(self):
        indexes = self.selectedIndexes()
        if indexes:
            path = self.dirmodel.filePath(indexes[0])
            self.config.persist["current_browser_path"] = path

    def restore_state(self):
        pass

    def _restore_state(self):
        path = self.config.persist["current_browser_path"]
        if path:
            path = find_existing_path(unicode(path))
            index = self.dirmodel.index(path)
            self.selectionModel().select(index, QtGui.QItemSelectionModel.SelectCurrent)
            self.scrollTo(index)
            self.expand(index)
