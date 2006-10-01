# -*- coding: UTF-8 -*-
#
# Copyright (C) 2006  Lukáš Lalinský 
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

from PyQt4 import QtCore, QtGui

class FileBrowser(QtGui.QTreeView):

    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        self.dirmodel = QtGui.QDirModel()
        self.dirmodel.setSorting(QtCore.QDir.Name | QtCore.QDir.DirsFirst)
        self.setModel(self.dirmodel)
        self.header().hideSection(1)
        self.header().hideSection(2)
        self.header().hideSection(3)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        indexes = self.selectedIndexes()
        if len(indexes):
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.model().mimeData(indexes)) 
            if drag.start(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
                self.takeItem(self.row(item))

