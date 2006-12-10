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

import os
import re
from PyQt4 import QtCore, QtGui
from picard.album import Album
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track
from picard.util import format_time, encode_filename, decode_filename
from picard.config import TextOption

__all__ = ["FileTreeView", "AlbumTreeView"]

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

        self.dirIcon = QtGui.QIcon(":/images/dir.png")
        self.fileIcon = QtGui.QIcon(":/images/file.png")
        self.cdIcon = QtGui.QIcon(":/images/cd.png")
        self.noteIcon = QtGui.QIcon(":/images/note.png")
        self.errorIcon = QtGui.QIcon(":/images/error.png")

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.lookupAct = QtGui.QAction(QtGui.QIcon(":/images/search.png"), _("&Lookup"), self)

        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"),
                     self.handle_double_click)

        self.contextMenu = QtGui.QMenu(self)
        self.contextMenu.addAction(self.main_window.edit_tags_action)
        self.contextMenu.addAction(self.main_window.refresh_action)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction(self.lookupAct)
        self.contextMenu.addAction(self.main_window.analyze_action)
        self.contextMenu.addAction(self.main_window.save_action)
        self.contextMenu.addAction(self.main_window.remove_action)

        self.__file_state_colors[File.NORMAL] = self.tagger.palette().text().color()

        self.objectToItem = {}
        self.itemToObject = {}

    def restoreState(self):
        if self.__class__.__name__ == "FileTreeView":
            sizes = self.config.persist["file_view_sizes"]
        else:
            sizes = self.config.persist["album_view_sizes"]
        header = self.header()
        sizes = sizes.split(" ")
        for i in range(self.numHeaderSections - 1):
            header.resizeSection(i, int(sizes[i]))

    def saveState(self):
        sizes = []
        header = self.header()
        for i in range(self.numHeaderSections - 1):
            sizes.append(str(self.header().sectionSize(i)))
        sizes = " ".join(sizes)
        if self.__class__.__name__ == "FileTreeView":
            self.config.persist["file_view_sizes"] = sizes
        else:
            self.config.persist["album_view_sizes"] = sizes

    def register_object(self, obj, item):
        self.objectToItem[obj] = item
        self.itemToObject[item] = obj

    def unregister_object(self, obj):
        item = self.get_item_from_object(obj)
        del self.objectToItem[obj]
        del self.itemToObject[item]

    def get_object_from_item(self, item):
        return self.itemToObject[item]

    def get_item_from_object(self, obj):
        return self.objectToItem[obj]

    __file_state_colors = {
        File.PENDING: QtGui.QColor(128, 128, 128),
        File.NORMAL: QtGui.QColor(0, 0, 0),
        File.CHANGED: QtGui.QColor(0, 0, 64),
        File.ERROR: QtGui.QColor(200, 0, 0),
        File.SAVED: QtGui.QColor(0, 128, 0),
    }

    def get_file_state_color(self, state):
        return self.__file_state_colors[state]

    def get_file_match_color(self, similarity):
        c1 = (255, 255, 255)
        c2 = (223, 125, 125)
        return QtGui.QColor(
            c2[0] + (c1[0] - c2[0]) * similarity,
            c2[1] + (c1[1] - c2[1]) * similarity,
            c2[2] + (c1[2] - c2[2]) * similarity)

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
                self.log.debug(u"MoveAction")

    def selected_objects(self):
        items = self.selectedItems()
        return [self.itemToObject[item] for item in items]

    def mimeData(self, items):
        """Return MIME data for specified items."""
        album_ids = []
        file_ids = []
        for item in items:
            obj = self.get_object_from_item(item)
            if isinstance(obj, Album):
                album_ids.append(str(obj.id))
            elif isinstance(obj, Track):
                if obj.is_linked():
                    file_ids.append(str(obj.linked_file.id))
            elif isinstance(obj, File):
                file_ids.append(str(obj.id))
            elif isinstance(obj, Cluster):
                for file in obj.files:
                    file_ids.append(str(file.id))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids))
        mimeData.setData("application/picard.file-list", "\n".join(file_ids))
        return mimeData

    def drop_files(self, files, target):
        # File -> Track or Cluster
        if isinstance(target, (Track, Cluster)):
            for file in files:
                file.move(target)
        # File -> File
        elif isinstance(target, File):
            if target.parent:
                for file in files:
                    file.move(target.parent)
        # File -> Album
        elif isinstance(target, Album):
            self.tagger.match_files_to_album(files, target)

    def drop_albums(self, albums, target):
        # Album -> Cluster
        if isinstance(target, Cluster):
            for album in albums:
                for track in album.tracks:
                    if track.linked_file:
                        track.linked_file.move(target)
        # Album -> Album
        elif isinstance(target, Album):
            files = []
            for album in albums:
                for track in album.tracks:
                    if track.linked_file:
                        files.append(track.linked_file)
            self.tagger.match_files_to_album(files, target)

    def drop_urls(self, urls, target):
        # URL -> Unmatched Files
        # TODO: use the drop target to move files to specific albums/tracks/clusters
        files = []
        for url in urls:
            if url.scheme() == "file" or not url.scheme():
                filename = unicode(url.toLocalFile())
                if os.path.isdir(encode_filename(filename)):
                    self.tagger.add_directory(filename)
                else:
                    files.append(filename)
            elif url.scheme() == "http":
                path = unicode(url.path())
                match = re.search(r"release/([0-9a-z\-]{36})", path)
                if match:
                    self.tagger.load_album(match.group(1))
        if files:
            self.tagger.add_files(files)

    def dropMimeData(self, parent, index, data, action):
        target = None
        if parent:
            target = self.get_object_from_item(parent)
        self.log.debug(u"Drop target = %s", target)
        if not target:
            self.target = self.tagger.unmatched_files
        # text/uri-list
        urls = data.urls()
        if urls:
            self.drop_urls(urls, target)
        # application/picard.file-list
        files = data.data("application/picard.file-list")
        if files:
            files = [self.tagger.get_file_by_id(int(file_id)) for file_id in str(files).split("\n")]
            self.drop_files(files, target)
        # application/picard.album-list
        albums = data.data("application/picard.album-list")
        if albums:
            albums = [self.tagger.get_album_by_id(albumsId) for albumsId in str(albums).split("\n")]
            self.drop_albums(albums, target)
        return True

    def handle_double_click(self, index):
        obj = self.itemToObject[self.itemFromIndex(index)]
        if obj.can_edit_tags():
            self.main_window.edit_tags(obj)

    def contextMenuEvent(self, event):
        self.contextMenu.popup(event.globalPos())
        event.accept()


class FileTreeView(BaseTreeView):

    def __init__(self, main_window, parent):
        BaseTreeView.__init__(self, main_window, parent)


        # "Unmatched Files"
        self.unmatched_files_item = QtGui.QTreeWidgetItem()
        self.unmatched_files_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled)
        self.unmatched_files_item.setIcon(0, self.dirIcon)
        self.register_object(self.tagger.unmatched_files, self.unmatched_files_item)
        self.update_cluster(self.tagger.unmatched_files)
        self.addTopLevelItem(self.unmatched_files_item)
        self.setItemExpanded(self.unmatched_files_item, True)

        self.connect(self.tagger, QtCore.SIGNAL("file_updated"), self.update_file)

        # Catch adding and removing files from clusters
        self.connect(self.tagger, QtCore.SIGNAL("file_added_to_cluster"),
                     self.add_file_to_cluster)
        self.connect(self.tagger, QtCore.SIGNAL("file_removed_from_cluster"),
                     self.remove_file_from_cluster)

        self.clusters_item = QtGui.QTreeWidgetItem()
        self.clusters_item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.clusters_item.setText(0, _(u"Clusters"))
        self.clusters_item.setIcon(0, self.dirIcon)
        self.addTopLevelItem(self.clusters_item)
        self.setItemExpanded(self.clusters_item, True)
        self.register_object(self.tagger.clusters, self.clusters_item)
        self.connect(self.tagger, QtCore.SIGNAL("cluster_added"), self.add_cluster)
        self.connect(self.tagger, QtCore.SIGNAL("cluster_removed"), self.remove_cluster)


        #self.connect(self, QtCore.SIGNAL("itemSelectionChanged()"), self.updateSelection)

    def _set_file_metadata(self, file, item):
        metadata = file.metadata
        if file.state == File.ERROR:
            item.setIcon(0, self.errorIcon)
        else:
            item.setIcon(0, self.fileIcon)
        item.setText(0, metadata[u"title"])
        item.setText(1, format_time(metadata.get(u"~#length", 0)))
        item.setText(2, metadata[u"artist"])
        fg_color = self.get_file_state_color(file.state)
        bg_color = self.get_file_match_color(file.similarity)
        for i in range(3):
            item.setTextColor(i, fg_color)
            item.setBackgroundColor(i, bg_color)

    def update_file(self, file):
        try:
            item = self.get_item_from_object(file)
        except KeyError:
            return
        self._set_file_metadata(file, item)

    def remove_files(self):
        files = self.selected_objects()
        self.tagger.remove_files(files)

    def update_cluster(self, cluster, item=None):
        if item is None:
            item = self.get_item_from_object(cluster)
        item.setText(0, u"%s (%d)" % (cluster.metadata["album"],
                                      cluster.get_num_files()))
        if not cluster.special:
            item.setText(1, format_time(cluster.metadata["~#length"]))
            item.setText(2, cluster.metadata["artist"])

    def add_file_to_cluster(self, cluster, file):
        """Add ``file`` to ``cluster`` """
        cluster_item = self.get_item_from_object(cluster)
        item = QtGui.QTreeWidgetItem(cluster_item)
        self._set_file_metadata(file, item)
        self.register_object(file, item)
        self.update_cluster(cluster, cluster_item)

    def remove_file_from_cluster(self, cluster, file, index):
        """Remove ``file`` on position ``index`` from ``cluster`` """
        cluster_item = self.get_item_from_object(cluster)
        cluster_item.takeChild(index)
        self.unregister_object(file)
        self.update_cluster(cluster, cluster_item)

    def add_cluster(self, cluster):
        cluster_item = QtGui.QTreeWidgetItem(self.clusters_item)
        cluster_item.setIcon(0, self.cdIcon)
        self.update_cluster(cluster, cluster_item)
        self.register_object(cluster, cluster_item)
        for file in cluster.files:
            item = QtGui.QTreeWidgetItem(cluster_item)
            self._set_file_metadata(file, item)
            self.register_object(file, item)

    def remove_cluster(self, cluster, index):
        for file in cluster.files:
            self.unregister_object(file)
        self.unregister_object(cluster)
        self.clusters_item.takeChild(index)


class AlbumTreeView(BaseTreeView):

    def __init__(self, main_window, parent):
        BaseTreeView.__init__(self, main_window, parent)

        self.matchIcons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]
        self.icon_saved = QtGui.QIcon(":/images/track-saved.png")

        self.connect(self.tagger, QtCore.SIGNAL("album_added"),
                     self.add_album)
        self.connect(self.tagger, QtCore.SIGNAL("album_removed"),
                     self.remove_album)
        self.connect(self.tagger, QtCore.SIGNAL("album_updated"),
                     self.update_album)
        self.connect(self.tagger, QtCore.SIGNAL("track_updated"),
                     self.update_track)

    def _set_track_metadata(self, track, item=None):
        if not item:
            item = self.get_item_from_object(track)
        metadata = track.metadata
        item.setText(0, u"%s. %s" % (
            metadata[u"tracknumber"], metadata[u"title"]))
        item.setIcon(0, self.noteIcon)
        item.setText(1, format_time(metadata.get(u"~#length", 0)))
        item.setText(2, metadata[u"artist"])

    def _set_album_metadata(self, album, item=None):
        if not item:
            item = self.get_item_from_object(album)
        metadata = album.metadata
        ntracks = album.getNumTracks()
        if ntracks:
            nfiles = album.getNumLinkedFiles()
            item.setText(0, u"%s (%d / %d)" % (
                metadata[u"album"], ntracks, nfiles))
        else:
            item.setText(0, metadata[u"album"])
        item.setIcon(0, self.cdIcon)
        item.setText(1, format_time(metadata.get("~#length", 0)))
        item.setText(2, metadata[u"albumartist"])

    def update_track(self, track):
        # Update track background
        item = self.get_item_from_object(track)
        if track.is_linked():
            file = track.linked_file
            state = file.state
            if file.state == File.SAVED:
                similarity = 1.0
                icon = self.icon_saved
            else:
                if file.state == File.ERROR:
                    icon = self.errorIcon
                similarity = track.linked_file.similarity
                icon = self.matchIcons[int(similarity * 5 + 0.5)]
        else:
            similarity = 1
            state = File.NORMAL
            icon = self.noteIcon
        # Colors
        fg_color = self.get_file_state_color(state)
        bg_color = self.get_file_match_color(similarity)
        for i in range(3):
            item.setTextColor(i, fg_color)
            item.setBackgroundColor(i, bg_color)
        # Icon
        item.setIcon(0, icon)
        self._set_album_metadata(track.album)

    def add_album(self, album):
        item = QtGui.QTreeWidgetItem(self)
        self.register_object(album, item)
        self._set_album_metadata(album, item)
        font = item.font(0)
        font.setBold(True)
        for i in range(3):
            item.setFont(i, font)

    def update_album(self, album):
        album_item = self.get_item_from_object(album)
        self._set_album_metadata(album, album_item)
        # XXX unregister tracks
        album_item.takeChildren()
        for track in album.tracks:
            item = QtGui.QTreeWidgetItem(album_item)
            self.register_object(track, item)
            self._set_track_metadata(track, item)

    def remove_album(self, album, index):
        self.unregister_object(album)
        self.takeTopLevelItem(index)
        # XXX unregister tracks
