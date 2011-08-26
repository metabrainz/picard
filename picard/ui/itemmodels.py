# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011 Michael Wiencek
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

from picard.file import File
from picard.album import Album
from picard.track import Track
from picard.cluster import Cluster
from picard.collection import Collection
from picard.ui.treeitems import TreeRoot, AlbumClusterItem, UnmatchedClusterItem, FileItem, AlbumItem, CollectionItem
from picard.util import icontheme


class TreeModel(QtCore.QAbstractItemModel):

    columns = [
        (N_("Title"), "title"),
        (N_("Length"), "~length"),
        (N_("Artist"), "artist"),
    ]

    row_expanded = QtCore.pyqtSignal(QtCore.QModelIndex)
    row_hid = QtCore.pyqtSignal(int, QtCore.QModelIndex, bool)

    def __init__(self, panel):
        QtCore.QAbstractItemModel.__init__(self)
        self.root = TreeRoot(self)
        self.panel = panel
        self.icon_folder = icontheme.lookup("folder", icontheme.ICON_SIZE_MENU)

    def columnCount(self, parent):
        return len(self.columns)

    def item(self, index):
        if index.isValid():
            return index.internalPointer()
        return self.root

    def rowCount(self, index):
        if index.column() > 0:
            return 0
        return self.item(index).rowCount

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.columns[section][0]
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        return self.createIndex(row, column, self.item(parent).children[row])

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        parent = index.internalPointer().parent
        if parent == self.root:
            return QtCore.QModelIndex()
        return self.createIndex(parent.row, 0, parent)

    def data(self, index, role):
        if not index.isValid():
            return None
        Qt = QtCore.Qt
        item = index.internalPointer()
        column = index.column()
        if role == Qt.DisplayRole:
            return item.obj.column(self.columns[index.column()][1])
        elif role == Qt.ForegroundRole:
            return item.foreground
        elif role == Qt.BackgroundRole:
            return item.background
        elif role == Qt.DecorationRole and column == 0:
            return item.icon
        else:
            return None

    def flags(self, index):
        return (QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsDragEnabled |
                QtCore.Qt.ItemIsDropEnabled |
                QtCore.Qt.ItemIsEnabled)

    def canFetchMore(self, parent):
        item = self.item(parent)
        return item.rowCount < item.size

    def fetchMore(self, parent):
        item = self.item(parent)
        self.beginInsertRows(parent, item.rowCount, item.size - 1)
        item.rowCount = item.size
        self.endInsertRows()

    def hasChildren(self, parent):
        return self.item(parent).size > 0

    @staticmethod
    def object_from_index(index):
        if index.isValid():
            return index.internalPointer().obj
        else:
            return None

    def sort_cmp(self, a, b, column):
        a, b = a.obj, b.obj
        name = self.columns[column][1]
        if name == "~length":
            return cmp(a.metadata.length, b.metadata.length)
        else:
            return cmp(a.column(name), b.column(name))

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def dropMimeData(self, data, action, row, column, parent):
        target = TreeModel.object_from_index(parent)
        handled = False

        urls = data.urls()
        if urls:
            self.tagger.add_urls(urls)
            handled = True

        files = set()

        file_list = data.data("application/picard.file-list")
        if file_list:
            files.update([self.tagger.get_file_by_id(int(id)) for id in str(file_list).split("\n")])

        album_list = data.data("application/picard.album-list")
        if album_list:
            albums = [self.tagger.load_album(id) for id in str(album_list).split("\n")]
            files.update(self.tagger.get_files_from_objects(albums))

        if files:
            handled = True
            self.drop_files(files, target)

        releases = data.data("application/picard.collections-data")
        if releases:
            for id in [release.id for release in releases]:
                self.tagger.load_album(id)
            handled = True

        return handled


class FileTreeModel(TreeModel):

    def __init__(self, panel):
        TreeModel.__init__(self, panel)
        self.unmatched_files = self.tagger.unmatched_files
        self.root.add_object(self.unmatched_files, UnmatchedClusterItem)
        self.tagger.cluster_added.connect(self.add_cluster)
        self.tagger.files_added.connect(self.add_unmatched_files)
        self.tagger.file_moved.connect(self.move_file)

    def add_cluster(self, cluster):
        self.root.add_object(cluster, AlbumClusterItem)

    def add_unmatched_files(self, files):
        self.layoutAboutToBeChanged.emit()
        uf = self.unmatched_files
        uf.add_files(files)
        uf.item.add_objects(files, FileItem)
        self.layoutChanged.emit()

    def move_file(self, file, dest):
        item = file.item
        if item:
            item.parent.remove_file(file)
        dest.item.add_file(file)

    def mimeTypes(self):
        return ["text/uri-list",
                "application/picard.file-list",
                "application/picard.album-list"]

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        cmp_ = lambda a, b: self.sort_cmp(a, b, column)
        reverse = order == QtCore.Qt.DescendingOrder
        children = self.root.children
        unmatched = children.pop(0)
        unmatched.children.sort(cmp=cmp_, reverse=reverse)
        unmatched._reindex()
        children.sort(cmp=cmp_, reverse=reverse)
        children.insert(0, unmatched)
        self.root._reindex()
        self.layoutChanged.emit()

    def drop_files(self, files, target=None):
        if target is None or isinstance(target, File):
            target = self.tagger.unmatched_files
        self.layoutAboutToBeChanged.emit()
        for file in files:
            file.move(target)
        self.layoutChanged.emit()


class AlbumTreeModel(TreeModel):

    def __init__(self, panel):
        TreeModel.__init__(self, panel)

        self.track_colors = {
            File.NORMAL: self.config.setting["color_saved"],
            File.CHANGED: self.panel.text_color,
            File.PENDING: self.config.setting["color_pending"],
            File.ERROR: self.config.setting["color_error"],
        }

        self.icon_cd = icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)
        self.icon_cd_saved = icontheme.lookup('media-optical-saved', icontheme.ICON_SIZE_MENU)
        self.icon_note = QtGui.QIcon(":/images/note.png")
        self.icon_saved = QtGui.QIcon(":/images/track-saved.png")
        self.match_icons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]
        self.match_pending_icons = [
            QtGui.QIcon(":/images/match-pending-50.png"),
            QtGui.QIcon(":/images/match-pending-60.png"),
            QtGui.QIcon(":/images/match-pending-70.png"),
            QtGui.QIcon(":/images/match-pending-80.png"),
            QtGui.QIcon(":/images/match-pending-90.png"),
            QtGui.QIcon(":/images/match-pending-100.png"),
        ]

        self.tagger.album_added.connect(self.add_album)

    def add_album(self, album):
        self.layoutAboutToBeChanged.emit()
        self.root.add_object(album, AlbumItem)
        self.layoutChanged.emit()

    def get_match_icon(self, file):
        if file.state == File.NORMAL:
            return self.icon_saved
        elif file.state == File.PENDING:
            return self.match_pending_icons[int(file.similarity * 5 + 0.5)]
        else:
            return self.match_icons[int(file.similarity * 5 + 0.5)]

    def mimeTypes(self):
        return ["text/uri-list",
                "application/picard.file-list",
                "application/picard.album-list",
                "application/picard.collections-data"]

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


class CollectionTreeModel(TreeModel):

    columns = [
        (N_("Title"), "title"),
        (N_("Artist"), "albumartist"),
        (N_("Format"), "media"),
        (N_("Tracks"), "totaltracks"),
        (N_("Date"), "date"),
        (N_("Country"), "releasecountry"),
        (N_("Barcode"), "barcode")
    ]

    def __init__(self, panel):
        TreeModel.__init__(self, panel)
        self.normal_color = QtGui.QBrush(self.panel.file_colors[File.NORMAL])
        self.pending_color = QtGui.QBrush(QtGui.QColor(128, 128, 128))
        self.load()

    def add_collection(self, collection):
        self.root.add_object(collection, CollectionItem).update(pending=True)

    def load(self):
        self.collections = []
        self.loaded = False
        if self.config.setting["username"] and self.config.setting["password"]:
            self.tagger.xmlws.get_collection_list(self._request_finished)

    def _request_finished(self, document, reply, error):
        if error:
            self.tagger.window.set_statusbar_message(N_("Could not load user collections: %s"), unicode(reply.errorString()))
            return
        collection_list = document.metadata[0].collection_list[0]
        if "collection" in collection_list.children:
            for node in collection_list.collection:
                collection = Collection(node.id, node.name[0].text, node.release_list[0].count)
                self.collections.append(collection)
                self.add_collection(collection)
        self.loaded = True

    def flags(self, index):
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEnabled
        if index.parent().internalPointer() == self.root:
            return flags
        else:
            return flags | QtCore.Qt.ItemIsDragEnabled

    def refresh(self):
        self.root.clear_rows()
        self.load()

    def dropMimeData(self, data, action, row, column, parent):
        target = TreeModel.object_from_index(parent)
        if target is None:
            return False
        if isinstance(target, CollectedRelease):
            target = target.collection
        releases = set()
        albums = data.data("application/picard.album-list")
        if albums:
            for id in str(albums).split("\n"):
                album = self.tagger.albums.get(id)
                if album and album.loaded:
                    releases.add(Release(id, album.metadata))
        releases_ = data.data("application/picard.collections-data")
        if releases_:
            releases.update(releases_)
        releases.difference_update(target.releases)
        if releases:
            target.add_releases(releases)
            return True
        return False
