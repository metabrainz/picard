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
from picard.track import Track
from picard.album import Album
from picard.track import Track
from picard.cluster import Cluster
from picard.collection import Collection, CollectedRelease, Release
from picard.util import icontheme


class TreeItem(object):

    def __init__(self, obj, parent, model):
        self.obj = obj
        obj.item = self

        self.parent = parent
        self.model = model
        self.children = []
        self.selected = False

        self.icon = None
        self.foreground = None
        self.background = None

    @property
    def row(self):
        return self.parent.children.index(self)


class TreeRoot(object):

    def __init__(self):
        self.row = 0
        self.children = []


class TreeModel(QtCore.QAbstractItemModel):

    columns = [
        (N_("Title"), "title"),
        (N_("Length"), "~length"),
        (N_("Artist"), "artist"),
    ]

    row_expanded = QtCore.pyqtSignal(QtCore.QModelIndex)
    row_hidden = QtCore.pyqtSignal(int, QtCore.QModelIndex, bool)

    def __init__(self, panel):
        QtCore.QAbstractItemModel.__init__(self)
        self.root = TreeRoot()
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
        return len(self.item(index).children)

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
        return self.indexOf(index.internalPointer().parent)

    def indexOf(self, item):
        if item == self.root:
            return QtCore.QModelIndex()
        return self.createIndex(item.row, 0, item)

    def insertObjects(self, row, objects, parent):
        self.beginInsertRows(self.indexOf(parent), row, row + len(objects) - 1)
        insert = parent.children.insert
        for obj in objects:
            insert(row, TreeItem(obj, parent, self))
            row += 1
        self.endInsertRows()
        for obj in objects:
            obj.update()

    def appendObjects(self, objects, parent):
        self.insertObjects(len(parent.children), objects, parent)

    def removeRows(self, row, count, parent):
        last = row + count
        self.beginRemoveRows(self.indexOf(parent), row, last - 1)
        del parent.children[row:last]
        self.endRemoveRows()

    @staticmethod
    def removeObject(obj):
        item = obj.item
        item.model.removeRows(item.row, 1, item.parent)

    def removeObjects(self, objects, parent):
        rows = sorted([obj.item.row for obj in objects], reverse=True)
        count = 1
        for i, row in enumerate(rows):
            try:
                prev = rows[i + 1]
            except IndexError:
                self.removeRows(row, count, parent)
            else:
                if row == prev + 1:
                    count += 1
                else:
                    self.removeRows(row, count, parent)
                    count = 1

    def clearChildren(self, item):
        self.removeRows(0, len(item.children), item)

    @staticmethod
    def update_item(item):
        model = item.model
        model.dataChanged.emit(model.indexOf(item),
            model.createIndex(item.row, len(model.columns) - 1, item))

    @staticmethod
    def update_cluster(cluster):
        TreeModel.update_item(cluster.item)

    def data(self, index, role):
        if not index.isValid():
            return None
        Qt = QtCore.Qt
        item = index.internalPointer()
        column = index.column()
        if role == Qt.DisplayRole:
            return item.obj.column(self.columns[column][1])
        elif role == Qt.ForegroundRole:
            return item.foreground
        elif role == Qt.BackgroundRole:
            return item.background
        elif role == Qt.DecorationRole and column == 0:
            return item.icon
        else:
            return None

    def flags(self, index):
        Qt = QtCore.Qt
        return (Qt.ItemIsSelectable | Qt.ItemIsDragEnabled |
                Qt.ItemIsDropEnabled | Qt.ItemIsEnabled)

    def expand_item(self, item):
        self.row_expanded.emit(self.indexOf(item))

    def add_cluster(self, cluster, parent=None):
        parent = parent or self.root
        self.appendObjects([cluster], parent)
        cluster.item.icon = self.icon_folder
        TreeModel.update_item(cluster.item)

    @staticmethod
    def move_file(file, dst):
        item = file.item
        dst_model = dst.model
        if item is None:
            dst_model.appendObjects([file], dst)
            return
        src = item.parent
        src_model = src.model
        if src_model == dst_model:
            row = item.row
            src_model.beginMoveRows(src_model.indexOf(src), row, row, src_model.indexOf(dst), len(dst.children))
            dst.children.append(item)
            item.parent = dst
            del src.children[row]
            src_model.endMoveRows()
        else:
            TreeModel.removeObject(file)
            dst_model.appendObjects([file], dst)

    @staticmethod
    def object_from_index(index):
        if index.isValid():
            return index.internalPointer().obj
        return None

    @staticmethod
    def get_match_color(similarity, basecolor):
        c1 = (basecolor.red(), basecolor.green(), basecolor.blue())
        c2 = (223, 125, 125)
        return QtGui.QColor(
            c2[0] + (c1[0] - c2[0]) * similarity,
            c2[1] + (c1[1] - c2[1]) * similarity,
            c2[2] + (c1[2] - c2[2]) * similarity)

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
        self.add_cluster(self.unmatched_files)
        self.tagger.cluster_added.connect(self.add_cluster)
        self.tagger.cluster_removed.connect(TreeModel.removeObject)
        self.tagger.cluster_updated.connect(TreeModel.update_cluster)
        self.tagger.files_added.connect(self.add_files)
        self.tagger.files_moved_to_cluster.connect(self.move_files_to_cluster)
        self.tagger.file_updated.connect(self.update_file)

    def add_files(self, files):
        self.appendObjects(files, self.unmatched_files.item)

    def move_files_to_cluster(self, files, cluster):
        item = cluster.item
        for file in files:
            TreeModel.move_file(file, item)

    def update_file(self, file):
        item = file.item
        item.icon = self.panel.file_icons[file.state]
        item.foreground = QtGui.QBrush(self.panel.file_colors[file.state])
        item.background = QtGui.QBrush(self.get_match_color(file.similarity, self.panel.base_color))
        TreeModel.update_item(item)

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
        children.sort(cmp=cmp_, reverse=reverse)
        children.insert(0, unmatched)
        self.layoutChanged.emit()

    def drop_files(self, files, target=None):
        if target is None or isinstance(target, File):
            target = self.unmatched_files
        for file in files:
            file.move(target)


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
        self.tagger.album_removed.connect(self.removeObject)
        self.tagger.album_updated.connect(self.update_album)
        self.tagger.cluster_hidden.connect(self.hide_cluster)
        self.tagger.track_updated.connect(self.update_track)
        self.tagger.file_moved_to_track.connect(self.move_file_to_track)

    def add_album(self, album):
        self.appendObjects([album], self.root)
        self.add_cluster(album.unmatched_files, parent=album.item)

    def update_album(self, album, update_tracks=True):
        item = album.item
        if update_tracks:
            children = item.children
            tracks = album.tracks
            old_size = len(children) - 1
            new_size = len(tracks)
            left = new_size
            if old_size > new_size:
                self.removeRows(new_size, old_size - new_size, item)
            elif new_size > old_size:
                self.insertObjects(old_size, tracks[old_size:new_size], parent=item)
                left = old_size
            for i in xrange(left):
                child = children[i]
                child.obj = tracks[i]
                tracks[i].item = child
            map(self.update_track, tracks)
        item.icon = self.icon_cd_saved if album.is_complete() else self.icon_cd
        TreeModel.update_item(item)

    def move_file_to_track(self, file, track):
        item = track.item
        files = track.linked_files
        expand = False
        if len(files) > 1:
            if len(item.children) > 0:
                files = [file]
            else:
                expand = True
            for file in files:
                TreeModel.move_file(file, item)
        elif file.item:
            TreeModel.removeObject(file)
            file.item = None
        if expand:
            self.expand_item(item)

    def hide_cluster(self, cluster, hidden):
        item = cluster.item
        self.row_hidden.emit(item.row, self.indexOf(item.parent), hidden)

    def update_track(self, track):
        item = track.item
        files = track.linked_files
        count = len(files)
        if count <= 1 and len(item.children) > 0:
            for child in item.children:
                child.obj.item = None
            self.clearChildren(item)
        if count == 1:
            file = files[0]
            item.foreground = QtGui.QBrush(self.track_colors[file.state])
            item.icon = self.get_match_icon(file)
            similarity = file.similarity
        else:
            item.foreground = QtGui.QBrush(self.panel.text_color)
            item.icon = self.icon_note
            similarity = 1
        item.background = QtGui.QBrush(self.get_match_color(similarity, self.panel.base_color))
        TreeModel.update_item(item)

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

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        cmp_ = lambda a, b: self.sort_cmp(a, b, column)
        reverse = order == QtCore.Qt.DescendingOrder
        self.root.children.sort(cmp=cmp_, reverse=reverse)
        self.layoutChanged.emit()

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
        Collection.model = self
        self.load()

    def set_pending(self, obj, pending=True):
        item = obj.item
        item.foreground = self.pending_color if pending else self.normal_color
        TreeModel.update_item(item)

    def add_releases(self, releases, collection, pending=False):
        item = collection.item
        collected = []
        for release in releases:
            obj = CollectedRelease(release, collection)
            collection.collected_releases[release] = obj
            collected.append(obj)
        self.appendObjects(collected, item)
        for release in collected:
            release.update(pending=pending)

    def remove_releases(self, releases, collection):
        item = collection.item
        objects = [collection.collected_releases.pop(r) for r in releases]
        self.removeObjects(objects, parent=item)
        TreeModel.update_item(item)

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
                self.appendObjects([collection], self.root)
        self.loaded = True

    def flags(self, index):
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEnabled
        if self.item(index).parent == self.root:
            return flags
        else:
            return flags | QtCore.Qt.ItemIsDragEnabled

    def refresh(self):
        self.clearChildren(self.root)
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
