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
from picard.cluster import Cluster, ClusterList
from picard.file import File
from picard.track import Track
from picard.util import encode_filename
from picard.util import icontheme
from picard.config import Option, TextOption


def get_match_color(similarity):
    c1 = (255, 255, 255)
    c2 = (223, 125, 125)
    return QtGui.QColor(
        c2[0] + (c1[0] - c2[0]) * similarity,
        c2[1] + (c1[1] - c2[1]) * similarity,
        c2[2] + (c1[2] - c2[2]) * similarity)


class MainPanel(QtGui.QSplitter):

    options = [
        Option("persist", "splitter_state", QtCore.QByteArray(), QtCore.QVariant.toByteArray),
    ]

    columns = [
        (N_('Title'), 'title'),
        (N_('Length'), '~length'),
        (N_('Artist'), 'artist'),
    ]

    def __init__(self, window, parent=None):
        QtGui.QSplitter.__init__(self, parent)
        self.window = window
        self.create_icons()
        self._object_to_item = {}
        self._item_to_object = {}
        self.views = [FileTreeView(window, self), AlbumTreeView(window, self)]
        self._selected_view = 0
        self._ignore_selection_changes = False
        self.connect(self.views[0], QtCore.SIGNAL("itemSelectionChanged()"), self.update_selection_0)
        self.connect(self.views[1], QtCore.SIGNAL("itemSelectionChanged()"), self.update_selection_1)
        self.file_colors = {
            File.NORMAL: self.palette().text().color(),
            File.CHANGED: self.config.setting["color_modified"],
            File.PENDING: self.config.setting["color_pending"],
            File.ERROR: self.config.setting["color_error"],
        }
        self.connect(self.tagger, QtCore.SIGNAL("file_updated"), self.update_file)
        self.connect(self.tagger, QtCore.SIGNAL("file_added_to_cluster"), self.add_file_to_cluster)
        self.connect(self.tagger, QtCore.SIGNAL("file_removed_from_cluster"), self.remove_file_from_cluster)

    def save_state(self):
        self.config.persist["splitter_state"] = self.saveState()
        for view in self.views:
            view.save_state()

    def restore_state(self):
        self.restoreState(self.config.persist["splitter_state"])

    def create_icons(self):
        if hasattr(QtGui.QStyle, 'SP_DirIcon'):
            self.icon_dir = self.style().standardIcon(QtGui.QStyle.SP_DirIcon)
        else:
            self.icon_dir = icontheme.lookup('folder', icontheme.ICON_SIZE_MENU)
        self.icon_file = QtGui.QIcon(":/images/file.png")
        self.icon_cd = icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)
        self.icon_note = QtGui.QIcon(":/images/note.png")
        self.icon_error = icontheme.lookup('dialog-error', icontheme.ICON_SIZE_MENU)
        self.icon_saved = QtGui.QIcon(":/images/track-saved.png")

    def selected_objects(self):
        items = self.views[self._selected_view].selectedItems()
        return map(self.object_from_item, items)

    def update_selection(self, i, j):
        self._selected_view = i
        self.views[j].clearSelection()
        self.window.updateSelection(self.selected_objects())

    def update_selection_0(self):
        if not self._ignore_selection_changes:
            self._ignore_selection_changes = True
            self.update_selection(0, 1)
            self._ignore_selection_changes = False

    def update_selection_1(self):
        if not self._ignore_selection_changes:
            self._ignore_selection_changes = True
            self.update_selection(1, 0)
            self._ignore_selection_changes = False

    def register_object(self, obj, item):
        self._object_to_item[obj] = item
        self._item_to_object[item] = obj

    def unregister_object(self, obj=None, item=None):
        if obj is None and item is not None:
            obj = self.object_from_item(item)
        if obj is not None and item is None:
            item = self.item_from_object(obj)
        del self._object_to_item[obj]
        del self._item_to_object[item]

    def object_from_item(self, item):
        return self._item_to_object[item]

    def item_from_object(self, obj):
        return self._object_to_item[obj]

    def update_file(self, file, item=None):
        if item is None:
            try:
                item = self.item_from_object(file)
            except KeyError:
                self.log.debug("Item for %r not found", file)
                return
        if file.state == File.ERROR:
            item.setIcon(0, self.icon_error)
        else:
            item.setIcon(0, self.icon_file)
        color = self.file_colors[file.state]
        for i, column in enumerate(self.columns):
            text, similarity = file.column(column[1])
            item.setText(i, text)
            item.setTextColor(i, color)
            item.setBackgroundColor(i, get_match_color(similarity))

    def update_cluster(self, cluster, item=None):
        if item is None:
            try:
                item = self.item_from_object(cluster)
            except KeyError:
                self.log.debug("Item for %r not found", cluster)
                return
        for i, column in enumerate(self.columns):
            item.setText(i, cluster.column(column[1]))

    def add_file_to_cluster(self, cluster, file):
        try:
            cluster_item = self.item_from_object(cluster)
        except KeyError:
            self.log.debug("Item for %r not found", cluster)
            return
        item = QtGui.QTreeWidgetItem(cluster_item)
        self.register_object(file, item)
        self.update_file(file, item)
        self.update_cluster(cluster, cluster_item)
        if cluster.special == 2 and cluster.files:
            cluster_item.setHidden(False)

    def remove_file_from_cluster(self, cluster, file, index):
        try:
            cluster_item = self.item_from_object(cluster)
        except KeyError:
            self.log.debug("Item for %r not found", cluster)
            return
        cluster_item.takeChild(index)
        self.unregister_object(file)
        self.update_cluster(cluster, cluster_item)
        if cluster.special == 2 and not cluster.files:
            cluster_item.setHidden(True)


class BaseTreeView(QtGui.QTreeWidget):

    options = [
        TextOption("persist", "file_view_sizes", "250 40 100"),
        TextOption("persist", "album_view_sizes", "250 40 100"),
        Option("setting", "color_modified", QtGui.QColor(0, 0, 0), QtGui.QColor),
        Option("setting", "color_saved", QtGui.QColor(0, 128, 0), QtGui.QColor),
        Option("setting", "color_error", QtGui.QColor(200, 0, 0), QtGui.QColor),
        Option("setting", "color_pending", QtGui.QColor(128, 128, 128), QtGui.QColor),
    ]

    def __init__(self, window, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        self.window = window
        self.panel = parent
        self.columns = self.panel.columns

        self.numHeaderSections = len(self.columns)
        self.setHeaderLabels([_(h) for h, n in self.columns])
        self.restore_state()

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.activate_item)

        self.addAction(window.edit_tags_action)
        self.addAction(window.refresh_action)
        self.addAction(window.analyze_action)
        self.addAction(window.save_action)
        self.addAction(window.remove_action)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

    def restore_state(self):
        if self.__class__.__name__ == "FileTreeView":
            sizes = self.config.persist["file_view_sizes"]
        else:
            sizes = self.config.persist["album_view_sizes"]
        header = self.header()
        sizes = sizes.split(" ")
        try:
            for i in range(self.numHeaderSections - 1):
                header.resizeSection(i, int(sizes[i]))
        except IndexError:
            pass

    def save_state(self):
        sizes = []
        header = self.header()
        for i in range(self.numHeaderSections - 1):
            sizes.append(str(self.header().sectionSize(i)))
        sizes = " ".join(sizes)
        if self.__class__.__name__ == "FileTreeView":
            self.config.persist["file_view_sizes"] = sizes
        else:
            self.config.persist["album_view_sizes"] = sizes

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
            drag.start(supportedActions)

    def mimeData(self, items):
        """Return MIME data for specified items."""
        album_ids = []
        file_ids = []
        for item in items:
            obj = self.panel.object_from_item(item)
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
            elif isinstance(obj, ClusterList):
                for cluster in obj:
                    for file in cluster.files:
                        file_ids.append(str(file.id))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids))
        mimeData.setData("application/picard.file-list", "\n".join(file_ids))
        return mimeData

    def drop_files(self, files, target):
        if isinstance(target, (Track, Cluster)):
            for file in files:
                file.move(target)
        elif isinstance(target, File):
            if target.parent:
                for file in files:
                    file.move(target.parent)
        elif isinstance(target, Album):
            self.tagger.move_files_to_album(files, album=target)
        elif isinstance(target, ClusterList):
            self.tagger.cluster(files)

    def drop_albums(self, albums, target):
        files = self.tagger.get_files_from_objects(albums)
        if isinstance(target, Cluster):
            for file in files:
                file.move(target)
        elif isinstance(target, Album):
            self.tagger.move_files_to_album(files, album=target)
        elif isinstance(target, ClusterList):
            self.tagger.cluster(files)

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
            target = self.panel.object_from_item(parent)
        self.log.debug("Drop target = %r", target)
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

    def activate_item(self, index):
        obj = self.panel.object_from_item(self.itemFromIndex(index))
        if obj.can_edit_tags():
            self.window.edit_tags(obj)

    def add_cluster(self, cluster, parent_item=None):
        if parent_item is None:
            parent_item = self.clusters
        cluster_item = QtGui.QTreeWidgetItem(parent_item)
        cluster_item.setIcon(0, self.panel.icon_dir)
        self.panel.update_cluster(cluster, cluster_item)
        self.panel.register_object(cluster, cluster_item)
        for file in cluster.files:
            item = QtGui.QTreeWidgetItem(cluster_item)
            self.panel.register_object(file, item)
            self.panel.update_file(file, item)
        if cluster.special == 2 and not cluster.files:
            cluster_item.setHidden(True)


class FileTreeView(BaseTreeView):

    def __init__(self, window, parent=None):
        BaseTreeView.__init__(self, window, parent)
        self.unmatched_files = QtGui.QTreeWidgetItem(self)
        self.unmatched_files.setIcon(0, self.panel.icon_dir)
        self.panel.register_object(self.tagger.unmatched_files, self.unmatched_files)
        self.panel.update_cluster(self.tagger.unmatched_files)
        self.setItemExpanded(self.unmatched_files, True)
        self.clusters = QtGui.QTreeWidgetItem(self)
        self.clusters.setText(0, _(u"Clusters"))
        self.clusters.setIcon(0, self.panel.icon_dir)
        self.panel.register_object(self.tagger.clusters, self.clusters)
        self.setItemExpanded(self.clusters, True)
        self.connect(self.tagger, QtCore.SIGNAL("cluster_added"), self.add_cluster)
        self.connect(self.tagger, QtCore.SIGNAL("cluster_removed"), self.remove_cluster)

    def remove_cluster(self, cluster, index):
        for file in cluster.files:
            self.panel.unregister_object(file)
        self.panel.unregister_object(cluster)
        self.clusters.takeChild(index)


class AlbumTreeView(BaseTreeView):

    def __init__(self, window, parent=None):
        BaseTreeView.__init__(self, window, parent)
        self.match_icons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]
        self.track_colors = {
            File.NORMAL: self.config.setting["color_saved"],
            File.CHANGED: self.palette().text().color(),
            File.PENDING: self.config.setting["color_pending"],
            File.ERROR: self.config.setting["color_error"],
        }
        self.connect(self.tagger, QtCore.SIGNAL("album_added"), self.add_album)
        self.connect(self.tagger, QtCore.SIGNAL("album_removed"), self.remove_album)
        self.connect(self.tagger, QtCore.SIGNAL("album_updated"), self.update_album)
        self.connect(self.tagger, QtCore.SIGNAL("track_updated"), self.update_track)

    def update_track(self, track, item=None):
        if item is None:
            try:
                item = self.panel.item_from_object(track)
            except KeyError:
                self.log.debug("Item for %r not found", track)
                return
        if track.is_linked():
            file = track.linked_file
            color = self.track_colors[file.state]
            if file.state == File.ERROR:
                icon = self.panel.icon_error
            elif file.state == File.NORMAL:
                icon = self.panel.icon_saved
            else:
                icon = self.match_icons[int(file.similarity * 5 + 0.5)]
        else:
            color = self.palette().text().color()
            bgcolor = get_match_color(1)
            icon = self.panel.icon_note
        item.setIcon(0, icon)
        for i, column in enumerate(self.columns):
            text, similarity = track.column(column[1])
            item.setText(i, text)
            item.setTextColor(i, color)
            item.setBackgroundColor(i, get_match_color(similarity))

    def add_album(self, album):
        item = QtGui.QTreeWidgetItem(self)
        self.panel.register_object(album, item)
        for i, column in enumerate(self.columns):
            font = item.font(i)
            font.setBold(True)
            item.setFont(i, font)
            item.setText(i, album.column(column[1]))
        self.add_cluster(album.unmatched_files, item)

    def update_album(self, album, update_tracks=True):
        try:
            album_item = self.panel.item_from_object(album)
        except KeyError:
            self.log.debug("Item for %r not found", album)
            return
        for i, column in enumerate(self.columns):
            album_item.setText(i, album.column(column[1]))
        if update_tracks:
            items = album_item.takeChildren()
            for item in items:
                self.panel.unregister_object(item=item)
            for track in album.tracks:
                item = QtGui.QTreeWidgetItem(album_item)
                self.panel.register_object(track, item)
                self.update_track(track, item)
            self.add_cluster(album.unmatched_files, album_item)

    def remove_album(self, album, index):
        self.panel.unregister_object(album)
        self.takeTopLevelItem(index)
        for track in album.tracks:
            self.panel.unregister_object(track)
