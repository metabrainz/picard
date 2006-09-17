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
from picard.util import format_time, encode_filename, decode_filename
from picard.config import TextOption

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

    options = [
        TextOption("persist", "file_view_sizes", "250 40 100"),
        TextOption("persist", "album_view_sizes", "250 40 100"),
    ]
    
    def __init__(self, main_window, parent):
        QtGui.QTreeWidget.__init__(self, parent)
        self.main_window = main_window

        self.numHeaderSections = 3
        self.setHeaderLabels([_(u"Title"), _(u"Time"), _(u"Artist")])
        self.restoreState()
        
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
        self.lookupAct = QtGui.QAction(QtGui.QIcon(":/images/search.png"), _("&Lookup"), self)
        
        #self.analyze_action = QtGui.QAction(QtGui.QIcon(":/images/analyze.png"), _("&Analyze"), self)
        
        self.contextMenu = QtGui.QMenu(self)
        self.contextMenu.addAction(self.main_window.edit_tags_action)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.lookupAct)
        self.contextMenu.addAction(self.main_window.analyze_action)
        self.contextMenu.addAction(self.main_window.save_action)
        self.contextMenu.addAction(self.main_window.remove_action)

        self.objectToItem = {}
        self.itemToObject = {}

    def restoreState(self):
        if self.__class__.__name__ == "FileTreeView":
            sizes = self.config.persist["file_view_sizes"]
        else:
            sizes = self.config.persist["album_view_sizes"]
        header = self.header()
        sizes = sizes.split(" ")
        for i in range(self.numHeaderSections):
            header.resizeSection(i, int(sizes[i]))

    def saveState(self):
        sizes = []
        header = self.header()
        for i in range(self.numHeaderSections):
            sizes.append(str(self.header().sectionSize(i)))
        sizes = " ".join(sizes)
        if self.__class__.__name__ == "FileTreeView":
            self.config.persist["file_view_sizes"] = sizes
        else:
            self.config.persist["album_view_sizes"] = sizes

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

    def selected_objects(self):
        items = self.selectedItems()
        return [self.itemToObject[item] for item in items]

    def mimeData(self, items):
        """Return MIME data for specified items."""
        album_ids = []
        file_ids = []
        for item in items:
            obj = self.getObjectFromItem(item)
            if isinstance(obj, Album):
                album_ids.append(str(obj.id))
            elif isinstance(obj, Track):
                print "track:", obj
                if obj.is_linked():
                    file_ids.append(str(obj.linked_file.id))
            elif isinstance(obj, File):
                file_ids.append(str(obj.id))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids))
        mimeData.setData("application/picard.file-list", "\n".join(file_ids))
        print "\n".join(file_ids)
        return mimeData
        
    def dropFiles(self, files, target):
        # File -> Track
        if isinstance(target, Track):
            for file in files:
                file.move_to_track(target)
        # File -> Cluster
        elif isinstance(target, Cluster):
            for file in files:
                file.move_to_cluster(target)
        # File -> File
        elif isinstance(target, File):
            if target.cluster:
                for file in files:
                    file.move_to_cluster(target.cluster)
        # File -> Album
        elif isinstance(target, Album):
            for file in files:
                target.matchFile(file)

    def dropAlbums(self, albums, target):
        # Album -> Cluster
        if isinstance(target, Cluster):
            for album in albums:
                for track in album.tracks:
                    if track.linked_file:
                        file = track.linked_file
                        file.move_to_cluster(target)
                
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
        self.emit(QtCore.SIGNAL("add_files"), files)

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
            files = [self.tagger.get_file_by_id(int(file_id)) for file_id in str(files).split("\n")]
            self.dropFiles(files, target)

        # application/picard.album-list
        albums = data.data("application/picard.album-list")
        if albums:
            albums = [self.tagger.get_album_by_id(albumsId) for albumsId in str(albums).split("\n")]
            self.dropAlbums(albums, target)

        return True

class FileTreeView(BaseTreeView):

    def __init__(self, main_window, parent):
        BaseTreeView.__init__(self, main_window, parent)
        
        # Prepare some common icons
        self.dirIcon = QtGui.QIcon(":/images/dir.png")
        self.fileIcon = QtGui.QIcon(":/images/file.png")
        
        # "Unmatched Files"
        self.unmatched_files_item = QtGui.QTreeWidgetItem()
        self.unmatched_files_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)
        self.unmatched_files_item.setIcon(0, self.dirIcon)
        self.registerObject(self.tagger.unmatched_files, self.unmatched_files_item)
        self.updateCluster(self.tagger.unmatched_files)
        self.addTopLevelItem(self.unmatched_files_item)
        self.setItemExpanded(self.unmatched_files_item, True)
        
        self.connect(self.tagger, QtCore.SIGNAL("file_updated"), self.update_file)
        
        unmatched = self.tagger.unmatched_files
        self.connect(unmatched, QtCore.SIGNAL("fileAdded"), self.add_fileToCluster)
        self.connect(unmatched, QtCore.SIGNAL("fileRemoved"), self.remove_fileFromCluster)
        
        #self.fileGroupsItem = QtGui.QTreeWidgetItem()
        #self.fileGroupsItem.setFlags(QtCore.Qt.ItemIsEnabled)
        #self.fileGroupsItem.setText(0, "Track Groups")
        #self.fileGroupsItem.setIcon(0, self.dirIcon)
        #self.addTopLevelItem(self.fileGroupsItem)
        
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
            
        #self.editTagsAct.setEnabled(canEditTags)
        #self.lookupAct.setEnabled(canLookup)
        #self.analyze_action.setEnabled(canAnalyze)
        #self.remove_action.setEnabled(canRemove)
        
        self.contextMenu.popup(event.globalPos())
        event.accept()

    def update_file(self, file):
        try:
            item = self.getItemFromObject(file)
        except KeyError:
            return

        file.lock_for_read()
        try:
            metadata = file.metadata
            item.setText(0, metadata["title"])
            item.setText(1, format_time(metadata.get("~#length", 0)))
            item.setText(2, metadata["artist"])
            color = matchColor(file.similarity)
            for i in range(3):
                item.setBackgroundColor(i, color)
        finally:
            file.unlock()

    def remove_files(self):
        files = self.selected_objects()
        self.tagger.remove_files(files)

    def updateCluster(self, cluster):
        item = self.getItemFromObject(cluster)
        item.setText(0, u"%s (%d)" % (cluster.name, cluster.get_num_files()))

    def add_fileToCluster(self, cluster, file, index):
        fileItem = QtGui.QTreeWidgetItem()
        fileItem.setIcon(0, self.fileIcon)
        fileItem.setText(0, file.orig_metadata.get("TITLE", ""))
        fileItem.setText(1, format_time(file.orig_metadata.get("~#length", 0)))
        fileItem.setText(2, file.orig_metadata.get("ARTIST", ""))
        clusterItem = self.getItemFromObject(cluster)
        clusterItem.addChild(fileItem)
        self.registerObject(file, fileItem)
        self.updateCluster(cluster)

    def remove_fileFromCluster(self, cluster, file, index):
        clusterItem = self.getItemFromObject(cluster)
        clusterItem.takeChild(index)
        self.unregisterObject(file)
        self.updateCluster(cluster)

    def handleDoubleClick(self, index):
        obj = self.itemToObject[self.itemFromIndex(index)]
        if obj.can_edit_tags():
            self.main_window.edit_tags(obj)

class AlbumTreeView(BaseTreeView):

    def __init__(self, main_window, parent):
        BaseTreeView.__init__(self, main_window, parent)

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
        self.icon_saved = QtGui.QIcon(":/images/track-saved.png")

        self.connect(self.tagger, QtCore.SIGNAL("albumAdded"), self.addAlbum)
        self.connect(self.tagger, QtCore.SIGNAL("albumRemoved"), self.remove_album)
        self.connect(self.tagger.worker, QtCore.SIGNAL("albumLoaded(QString)"),
            self.updateAlbum)
        self.connect(self.tagger, QtCore.SIGNAL("track_updated"),
                     self.update_track)

    def update_track(self, track):
        # Update track background
        item = self.getItemFromObject(track)
        if track.is_linked():
            file = track.linked_file
            if file.state == File.SAVED:
                similarity = 1.0
                icon = self.icon_saved
            else:
                similarity = track.linked_file.similarity
                icon = self.matchIcons[int(similarity * 5 + 0.5)]
        else:
            similarity = 1
            icon = self.noteIcon

        color = matchColor(similarity)
        for i in range(3):
            item.setBackgroundColor(i, color)
        item.setIcon(0, icon)

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

    def updateAlbum(self, album_id):
        self.log.debug("updateAlbum, %s", album_id)
        album = self.tagger.get_album_by_id(unicode(album_id))
        albumItem = self.getItemFromObject(album)
        albumItem.setText(0, album.getName())
        albumItem.setText(1, format_time(album.duration))
        albumItem.setText(2, album.artist.name)
        i = 1
        for track in album.tracks:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, "%d. %s" % (i, track.name))
            item.setIcon(0, self.noteIcon)
            item.setText(1, format_time(track.duration))
            item.setText(2, track.artist.name)
            self.registerObject(track, item)
            albumItem.addChild(item)
            i += 1

    def remove_album(self, album, index):
        self.unregisterObject(album)
        self.takeTopLevelItem(index)

