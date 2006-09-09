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
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track
from picard.util import formatTime, encode_filename, decode_filename
from picard.ui.tageditor import TagEditor

__all__ = ["FileTreeView", "AlbumTreeView"]

def matchColor(similarity):
    colors = ((255, 255, 255), (223, 125, 125))
    res = [0, 0, 0]
    #similarity = (1 - similarity) * (1 - similarity)
    similarity = 1 - similarity
    for i in range(3):
        res[i] = colors[0][i] + (colors[1][i] - colors[0][i]) * similarity
    return QtGui.QColor(res[0], res[1], res[2])

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
        self.setDropIndicatorShown(True)
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

    def unregisterObject(self, obj):
        item = self.getItemFromObject(obj)
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
        return ["text/uri-list", "application/picard.file-list", "application/picard.album-list"]
        
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

    def mimeData(self, items):
        """Return MIME data for specified items."""
        albumIds = []
        fileIds = []
        for item in items:
            obj = self.getObjectFromItem(item)
            if isinstance(obj, Album):
                albumIds.append(str(obj.getId()))
            elif isinstance(obj, Track):
                print "track:", obj
                if obj.isLinked():
                    fileIds.append(str(obj.getLinkedFile().getId()))
            elif isinstance(obj, File):
                fileIds.append(str(obj.getId()))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(albumIds))
        mimeData.setData("application/picard.file-list", "\n".join(fileIds))
        print "\n".join(fileIds)
        return mimeData
        
    def dropFiles(self, files, target):
        # File -> Track
        if isinstance(target, Track):
            for file in files:
                file.moveToTrack(target)
        # File -> Cluster
        elif isinstance(target, Cluster):
            for file in files:
                file.moveToCluster(target)
        # File -> File
        elif isinstance(target, File):
            if target.cluster:
                for file in files:
                    file.moveToCluster(target.cluster)
        # File -> Album
        elif isinstance(target, Album):
            for file in files:
                target.matchFile(file)

    def dropAlbums(self, albums, target):
        # Album -> Cluster
        if isinstance(target, Cluster):
            for album in albums:
                for track in album.tracks:
                    if track.isLinked():
                        file = track.getLinkedFile()
                        file.moveToCluster(target)
                
    def dropUrls(self, urls, target):
        # URL -> Unmatched Files
        # TODO: use the drop target to move files to specific albums/tracks/clusters
        from urllib import unquote
        
        files = []
        for url in urls:
            if url.startswith("file:///"):
                filename = unquote(url[8:]).decode("UTF-8")
                if os.path.isdir(encode_filename(filename)):
                    self.emit(QtCore.SIGNAL("addDirectory"), filename)
                else:
                    files.append(filename)
        self.emit(QtCore.SIGNAL("addFiles"), files)

    def dropMimeData(self, parent, index, data, action):
        target = None
        if parent:
#            if index:
#                item = parent.child(index)
#            else:
#                item = parent
            target = self.getObjectFromItem(parent)

        self.log.debug("Drop target = %s", target)
        if not target:
            return False

        # text/uri-list
        urls = data.data("text/uri-list")
        if urls:
            urls = [url.strip() for url in str(urls).split("\n")]
            self.dropUrls(urls, target)

        # application/picard.file-list
        files = data.data("application/picard.file-list")
        if files:
            files = [self.tagger.fileManager.getFile(int(fileId)) for fileId in str(files).split("\n")]
            self.dropFiles(files, target)

        # application/picard.album-list
        albums = data.data("application/picard.album-list")
        if albums:
            albums = [self.tagger.getAlbumById(albumsId) for albumsId in str(albums).split("\n")]
            self.dropAlbums(albums, target)

        return True

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
        self.unmatched_filesItem = QtGui.QTreeWidgetItem()
        self.unmatched_filesItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)
        self.unmatched_filesItem.setIcon(0, self.dirIcon)
        self.registerObject(self.tagger.unmatched_files, self.unmatched_filesItem)
        self.updateCluster(self.tagger.unmatched_files)
        self.addTopLevelItem(self.unmatched_filesItem)
        
        unmatched = self.tagger.unmatched_files
        self.connect(unmatched, QtCore.SIGNAL("fileAdded"), self.addFileToCluster)
        self.connect(unmatched, QtCore.SIGNAL("fileRemoved"), self.removeFileFromCluster)
        
        self.fileGroupsItem = QtGui.QTreeWidgetItem()
        self.fileGroupsItem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.fileGroupsItem.setText(0, "Track Groups")
        self.fileGroupsItem.setIcon(0, self.dirIcon)
        self.addTopLevelItem(self.fileGroupsItem)
        
        #self.connect(self, QtCore.SIGNAL("itemSelectionChanged()"), self.updateSelection)
        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.handleDoubleClick)

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

    def updateCluster(self, cluster):
        item = self.getItemFromObject(cluster)
        item.setText(0, u"%s (%d)" % (cluster.name, cluster.getNumFiles()))

    def addFileToCluster(self, cluster, file, index):
        fileItem = QtGui.QTreeWidgetItem()
        fileItem.setIcon(0, self.fileIcon)
        fileItem.setText(0, file.localMetadata.get("TITLE", ""))
        fileItem.setText(1, formatTime(file.audioProperties.length))
        fileItem.setText(2, file.localMetadata.get("ARTIST", ""))
        clusterItem = self.getItemFromObject(cluster)
        clusterItem.addChild(fileItem)
        self.registerObject(file, fileItem)
        self.updateCluster(cluster)

    def removeFileFromCluster(self, cluster, file, index):
        clusterItem = self.getItemFromObject(cluster)
        clusterItem.takeChild(index)
        self.unregisterObject(file)
        self.updateCluster(cluster)

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

class AlbumTreeView(BaseTreeView):

    def __init__(self, mainWindow, parent):
        BaseTreeView.__init__(self, mainWindow, parent)

        self.cdIcon = QtGui.QIcon(":/images/cd.png")
        self.noteIcon = QtGui.QIcon(":/images/note.png")
        self.matchIcons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]

        self.connect(self.tagger, QtCore.SIGNAL("albumAdded"), self.addAlbum)
        self.connect(self.tagger, QtCore.SIGNAL("albumRemoved"), self.removeAlbum)
        self.connect(self.tagger, QtCore.SIGNAL("trackUpdated"), self.updateTrack)
        self.connect(self.tagger.worker, QtCore.SIGNAL("albumLoaded(QString)"),
            self.updateAlbum)

    def updateTrack(self, track):
        # Update track background
        item = self.getItemFromObject(track)
        if track.isLinked():
            similarity = track.getLinkedFile().getSimilarity()
            item.setIcon(0, self.matchIcons[int(similarity * 5 + 0.5)])
        else:
            similarity = 1
            item.setIcon(0, self.noteIcon)
        color = matchColor(similarity)
        for i in range(3):
            item.setBackgroundColor(i, color)
            
        # Update track name
        albumItem = self.getItemFromObject(track.album)
        albumItem.setText(0, track.album.getName())

    def addAlbum(self, album):
        item = QtGui.QTreeWidgetItem()
        item.setText(0, album.getName())
        item.setIcon(0, self.cdIcon)
        font = item.font(0)
        font.setBold(True)
        for i in range(3):
            item.setFont(i, font)
        self.registerObject(album, item)
        self.addTopLevelItem(item)

    def updateAlbum(self, albumId):
        self.log.debug("updateAlbum, %s", albumId)
        album = self.tagger.getAlbumById(unicode(albumId))
        albumItem = self.getItemFromObject(album)
        albumItem.setText(0, album.getName())
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

    def removeAlbum(self, album, index):
        self.unregisterObject(album)
        self.takeTopLevelItem(index)

