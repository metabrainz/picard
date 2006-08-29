# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from PyQt4 import QtCore, QtGui
import os
from picard.album import Album
from picard.file import File
from picard.albummanager import UnmatchedFiles
from picard.util import formatTime, encodeFileName
from picard.ui.tageditor import TagEditor

__all__ = ["FileTreeView", "AlbumTreeView"]

class BaseTreeView(QtGui.QTreeWidget):

    def __init__(self, mainWindow, parent):
        QtGui.QTreeWidget.__init__(self, parent)
        self.mainWindow = mainWindow

        self.numHeaderSections = 3
        self.defaultSectionSizes = (250, 40, 100, 100)
        self.setHeaderLabels([_(u"Title"), _(u"Time"), _(u"Artist")])
        self.restoreState()
        
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
        self.objectToItem = {}
        self.itemToObject = {}

    def restoreState(self):
        name = "header" + self.__class__.__name__
        header = self.header()
        for i in range(self.numHeaderSections):
            size = self.config.persist.getInt("%s%d" % (name, i), \
                self.defaultSectionSizes[i])
            header.resizeSection(i, size)

    def saveState(self):
        name = "header" + self.__class__.__name__
        for i in range(self.numHeaderSections):
            size = self.header().sectionSize(i)
            self.config.persist.set("%s%d" % (name, i), size)

    def registerObject(self, obj, item):
        self.objectToItem[obj] = item
        self.itemToObject[item] = obj 

    def unregisterObject(self, obj, item):
        del self.objectToItem[obj]
        del self.itemToObject[item] 

    def getObjectFromItem(self, item):
        return self.itemToObject[item]

    def getItemFromObject(self, obj):
        return self.objectToItem[obj]

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction
            
    def mimeTypes(self):
        """List of MIME types accepted by this view."""
        return ["text/uri-list", "application/picard.file", "application/picard.album"]
        
    def startDrag(self, supportedActions):
        """Start drag, *without* using pixmap."""
        items = self.selectedItems()
        if items:
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.mimeData(items))
            if drag.start(supportedActions) == QtCore.Qt.MoveAction:
                self.log.debug("MoveAction")

    def selectedObjects(self):
        items = self.selectedItems()
        return [self.itemToObject[item] for item in items]
                
        
class FileTreeView(BaseTreeView):

    def __init__(self, mainWindow, parent):
        BaseTreeView.__init__(self, mainWindow, parent)

        
        
        # Create the context menu
        
        self.editTagsAct = QtGui.QAction(_("Edit &Tags..."), self)
        self.connect(self.editTagsAct, QtCore.SIGNAL("triggered()"), self.editTags)
        
        self.lookupAct = QtGui.QAction(QtGui.QIcon(":/images/search.png"), _("&Lookup"), self)
        
        self.analyzeAct = QtGui.QAction(QtGui.QIcon(":/images/analyze.png"), _("&Analyze"), self)
        
        self.contextMenu = QtGui.QMenu(self)
        self.contextMenu.addAction(self.editTagsAct)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.lookupAct)
        self.contextMenu.addAction(self.analyzeAct)
        self.contextMenu.addAction(self.mainWindow.removeAct)
        
        # Prepare some common icons
        
        self.dirIcon = QtGui.QIcon(":/images/dir.png")
        self.fileIcon = QtGui.QIcon(":/images/file.png")
        
        # "Unmatched Files"
        
        self.unmatchedFilesItem = QtGui.QTreeWidgetItem()
        self.unmatchedFilesItem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.unmatchedFilesItem.setText(0, "Unmatched Files")
        self.unmatchedFilesItem.setIcon(0, self.dirIcon)
        self.addTopLevelItem(self.unmatchedFilesItem)
        self.objectToItem[self.tagger.albumManager.unmatchedFiles] = self.unmatchedFilesItem
        self.itemToObject[self.unmatchedFilesItem] = self.tagger.albumManager.unmatchedFiles 
        
        unmatched = self.tagger.albumManager.unmatchedFiles
        self.connect(unmatched, QtCore.SIGNAL("fileAdded(int)"), self.addUnmatchedFile)
        self.connect(unmatched, QtCore.SIGNAL("fileAboutToBeRemoved"), self.beginRemoveFile)
        self.connect(unmatched, QtCore.SIGNAL("fileRemoved"), self.endRemoveFile)
        
        self.fileGroupsItem = QtGui.QTreeWidgetItem()
        self.fileGroupsItem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.fileGroupsItem.setText(0, "Track Groups")
        self.fileGroupsItem.setIcon(0, self.dirIcon)
        self.addTopLevelItem(self.fileGroupsItem)
        
        #self.connect(self, QtCore.SIGNAL("itemSelectionChanged()"), self.updateSelection)
        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.handleDoubleClick)

        
    def addUnmatchedFile(self, fileId):
        unmatchedFiles = self.tagger.albumManager.unmatchedFiles
        file = self.tagger.fileManager.getFile(fileId)
        fileItem = QtGui.QTreeWidgetItem()
        fileItem.setIcon(0, self.fileIcon)
        fileItem.setText(0, file.localMetadata.get("TITLE", ""))
        fileItem.setText(1, formatTime(file.audioProperties.length))
        fileItem.setText(2, file.localMetadata.get("ARTIST", ""))
        self.unmatchedFilesItem.addChild(fileItem)
        
        self.objectToItem[file] = fileItem
        self.itemToObject[fileItem] = file
        
        # Update title for pseudo-album "Unmatched Tracks"
        self.unmatchedFilesItem.setText(0, unmatchedFiles.name)

        
#        self.emit(QtCore.SIGNAL("rowsInserted(const QModelIndex &, int, int)"),
#            self.createIndex(0, 0, self.tagger.albumManager.unmatchedFiles),
#            0, 0)
        
    def contextMenuEvent(self, event):
        items = self.selectedItems()

        canEditTags = False
        canLookup = False
        canAnalyze = False
        canRemove = False
        
        if len(items) == 1:
            canEditTags = True
            canLookup = True
            
        if len(items) > 0:
            #canAnalyze = True
            canRemove = True
            
        self.editTagsAct.setEnabled(canEditTags)
        self.lookupAct.setEnabled(canLookup)
        self.analyzeAct.setEnabled(canAnalyze)
        #self.removeAct.setEnabled(canRemove)
        
        self.contextMenu.popup(event.globalPos())
        event.accept()

    def removeFiles(self):
        files = self.selectedObjects()
        self.tagger.fileManager.removeFiles(files)
        
    def beginRemoveFile(self, row):
        file = self.tagger.albumManager.unmatchedFiles.unmatchedFiles[row]
        item = self.objectToItem[file]
        index = self.unmatchedFilesItem.indexOfChild(item)
        self.unmatchedFilesItem.takeChild(index)
        del self.objectToItem[file]
        del self.itemToObject[item]
    
    def endRemoveFile(self, row):
        # Update title for pseudo-album "Unmatched Tracks"
        unmatchedFiles = self.tagger.albumManager.unmatchedFiles
        self.unmatchedFilesItem.setText(0, unmatchedFiles.name)
        
    def openTagEditor(self, obj):
        tagEditor = TagEditor(obj.getNewMetadata(), self)
        tagEditor.exec_()
        self.emit(QtCore.SIGNAL("selectionChanged"), [obj])
        
    def editTags(self):
        objects = self.selectedObjects()
        self.openTagEditor(objects[0])
        
    def handleDoubleClick(self, index):
        obj = self.itemToObject[self.itemFromIndex(index)]
        if isinstance(obj, File):
            self.openTagEditor(obj)
        
    # Drag & drop
    
    def dropMimeData(self, parent, index, data, action):
        """Handle drop."""
        print "dropMimeType"
        print data
        print [unicode(i) for i in data.formats()]
        files = []
        uriList = data.urls()
        for uri in uriList:
            print uri.scheme()
            print uri.host()
            if uri.scheme() == "file":
                fileName = str(uri.toLocalFile())
                fileName = unicode(QtCore.QUrl.fromPercentEncoding(QtCore.QByteArray(fileName)))
                if os.path.isdir(encodeFileName(fileName)):
                    self.emit(QtCore.SIGNAL("addDirectory"), fileName)
                else:
                    files.append(fileName)
        print files
        self.emit(QtCore.SIGNAL("addFiles"), files)
        return True
    
    def mimeData(self, items):
        """Return MIME data for specified items."""
        fileIds = []
        for item in items:
            obj = self.itemToObject[item]
            fileIds.append(str(obj.getId()))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.file", "\n".join(fileIds))
        return mimeData
 
        
class AlbumTreeView(BaseTreeView):

    def __init__(self, mainWindow, parent):
        BaseTreeView.__init__(self, mainWindow, parent)

        self.cdIcon = QtGui.QIcon(":/images/cd.png")
        self.noteIcon = QtGui.QIcon(":/images/note.png")
        
        self.connect(self.tagger.albumManager, QtCore.SIGNAL("albumAdded"),
            self.addAlbum)
        self.connect(self.tagger.worker, QtCore.SIGNAL("albumLoaded(QString)"),
            self.updateAlbum)
            
    def addAlbum(self, album):
        item = QtGui.QTreeWidgetItem()
        item.setText(0, album.name)
        item.setIcon(0, self.cdIcon)
        font = item.font(0)
        font.setBold(True)
        for i in range(3):
            item.setFont(i, font)
        self.registerObject(album, item)
        self.addTopLevelItem(item)

    def updateAlbum(self, albumId):
        self.log.debug("updateAlbum, %s", albumId)
        album = self.tagger.albumManager.getAlbumById(unicode(albumId))
        albumItem = self.getItemFromObject(album)
        albumItem.setText(0, album.name)
        albumItem.setText(1, formatTime(album.duration))
        albumItem.setText(2, album.artist.name)
        i = 1
        for track in album.tracks:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, "%d. %s" % (i, track.name))
            item.setIcon(0, self.noteIcon)
            item.setText(1, formatTime(track.duration))
            item.setText(2, track.artist.name)
            self.registerObject(track, item)
            albumItem.addChild(item)
            i += 1
            
    def mimeData(self, items):
        """Return MIME data for specified items."""
        albumIds = []
        for item in items:
            obj = self.getObjectFromItem(item)
            if isinstance(obj, Album):
                albumIds.append(str(obj.getId()))
            #elif isinstance(obj, Track):
            #    trackIds.append(str(obj.getId()))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album", "\n".join(albumIds))
        return mimeData
        
