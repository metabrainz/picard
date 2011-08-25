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

from picard.album import Album, NatAlbum
from picard.medium import Medium
from picard.cluster import Cluster, AlbumCluster, UnmatchedCluster
from picard.track import Track, NonAlbumTrack
from picard.file import File
from picard.collection import Collection, Release, CollectedRelease
from picard.ui.itemmodels import TreeModel, FileTreeModel, AlbumTreeModel, CollectionTreeModel
from picard.plugin import ExtensionPoint
from picard.util import icontheme, partial, webbrowser2
from picard.config import Option, TextOption


_album_actions = ExtensionPoint()
_track_actions = ExtensionPoint()
_file_actions = ExtensionPoint()
_cluster_actions = ExtensionPoint()

def register_album_action(action):
    _album_actions.register(action.__module__, action)

def register_track_action(action):
    _track_actions.register(action.__module__, action)

def register_file_action(action):
    _file_actions.register(action.__module__, action)

def register_cluster_action(action):
    _cluster_actions.register(action.__module__, action)


class BaseAction(QtGui.QAction):
    NAME = "Unknown"

    def __init__(self):
        QtGui.QAction.__init__(self, self.NAME, None)
        self.triggered.connect(self.__callback)

    def __callback(self):
        objs = self.tagger.window.panel.selected_objects()
        self.callback(objs)

    def callback(self, objs):
        raise NotImplementedError


class TreeView(QtGui.QTreeView):

    options = [
        Option("setting", "color_modified", QtGui.QColor(QtGui.QPalette.WindowText), QtGui.QColor),
        Option("setting", "color_saved", QtGui.QColor(0, 128, 0), QtGui.QColor),
        Option("setting", "color_error", QtGui.QColor(200, 0, 0), QtGui.QColor),
        Option("setting", "color_pending", QtGui.QColor(128, 128, 128), QtGui.QColor)
    ]

    selection_changed = QtCore.pyqtSignal(QtGui.QTreeView)

    def __init__(self, window, parent=None):
        QtGui.QTreeView.__init__(self, parent)

        self.window = window
        self.panel = parent

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setUniformRowHeights(True)
        self.setSortingEnabled(True)
        self.header().setClickable(True)

        self.expand_all_action = QtGui.QAction(_("&Expand all"), self)
        self.expand_all_action.triggered.connect(self.expandAll)
        self.collapse_all_action = QtGui.QAction(_("&Collapse all"), self)
        self.collapse_all_action.triggered.connect(self.collapseAll)

        self.doubleClicked.connect(self.activate_item)

    def setModel(self, model):
        QtGui.QTreeView.setModel(self, model)
        model.row_expanded.connect(self.expand)
        model.row_hid.connect(self.setRowHidden)

    def selectedObjects(self):
        for index in self.selectionModel().selectedRows():
            yield TreeModel.object_from_index(index)

    def selectionChanged(self, selected, deselected):
        QtGui.QTreeView.selectionChanged(self, selected, deselected)
        for index in iter(selected.indexes()):
            if index.isValid():
                index.internalPointer().selected = True
        for index in iter(deselected.indexes()):
            if index.isValid():
                index.internalPointer().selected = False
        self.selection_changed.emit(self)

    def contextMenuEvent(self, event):
        obj = TreeModel.object_from_index(self.currentIndex())
        if obj is None:
            return

        plugin_actions = None
        menu = QtGui.QMenu(self)
        if isinstance(obj, AlbumCluster):
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            if isinstance(obj, UnmatchedCluster):
                menu.addAction(self.window.cluster_action)
            plugin_actions = list(_cluster_actions)
        elif isinstance(obj, File):
            menu.addAction(self.window.edit_tags_action)
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            plugin_actions = list(_file_actions)

        menu.addAction(self.window.save_action)
        menu.addAction(self.window.remove_action)

        if plugin_actions:
            plugin_menu = QtGui.QMenu(_("&Plugins"), menu)
            plugin_menu.addActions(plugin_actions)
            plugin_menu.setIcon(self.panel.icon_plugins)
            menu.addSeparator()
            menu.addMenu(plugin_menu)

        if isinstance(obj, AlbumCluster) or isinstance(obj, Album):
            menu.addAction(self.expand_all_action)
            menu.addAction(self.collapse_all_action)

        menu.exec_(event.globalPos())
        event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.accept()

    def startDrag(self, supportedActions):
        """Start drag, *without* using pixmap."""
        objects = self.selectedObjects()
        if objects:
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.mimeData(objects))
            drag.start(supportedActions)

    def mimeData(self, objects):
        """Return MIME data for specified objects."""
        album_ids = []
        file_ids = []
        for obj in objects:
            if isinstance(obj, Album):
                album_ids.append(str(obj.id))
            elif isinstance(obj, Track):
                for file in obj.linked_files:
                    file_ids.append(str(file.id))
            elif isinstance(obj, File):
                file_ids.append(str(obj.id))
            elif isinstance(obj, Cluster):
                for file in obj.files:
                    file_ids.append(str(file.id))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids))
        mimeData.setData("application/picard.file-list", "\n".join(file_ids))
        return mimeData

    def activate_item(self, index):
        obj = TreeModel.object_from_index(index)
        if obj.can_edit_tags():
            self.window.edit_tags([obj])

    def restore_state(self, name):
        sizes = self.config.persist[name].split(" ")
        header = self.header()
        for i, size in enumerate(sizes):
            header.resizeSection(i, int(size))

    def save_state(self, name):
        header = self.header()
        sizes = " ".join([str(header.sectionSize(i)) for i in range(header.count())])
        self.config.persist[name] = sizes


class FileTreeView(TreeView):

    options = [TextOption("persist", "file_view_sizes", "250 40 100")]

    def __init__(self, window, parent):
        TreeView.__init__(self, window, parent)
        self.model = FileTreeModel(parent)
        self.setModel(self.model)
        self.expandAll()
        self.model.unmatched_files.item.expanded = True
        self.restore_state("file_view_sizes")

    def selected_files(self):
        files = []
        for index in self.selectionModel().selectedRows():
            item = index.internalPointer()
            if isinstance(item.parent.obj, UnmatchedCluster):
                files.append(item.obj)
        return files

    def remove_selection(self):
        root = self.model.root
        unmatched = root.children[0]
        unmatched.selected = False
        clusters = []
        files = {}
        for index in self.selectionModel().selectedRows():
            item = index.internalPointer()
            parent = item.parent
            obj = item.obj
            if isinstance(obj, File) and not parent.selected:
                obj.remove()
                try:
                    files[parent].append(obj)
                except KeyError:
                    files[parent] = [obj]
            elif isinstance(obj, AlbumCluster):
                obj.remove()
                clusters.append(obj)
        if clusters:
            root.remove_objects(clusters)
        for cluster, files_ in files.iteritems():
            cluster.remove_objects(files_)
            cluster.obj.remove_files(files_)
            if not cluster.size and cluster != unmatched:
                root.remove_rows(cluster.row, 1)


class AlbumTreeView(TreeView):

    options = [TextOption("persist", "album_view_sizes", "250 40 100")]

    def __init__(self, window, parent):
        TreeView.__init__(self, window, parent)
        self.model = AlbumTreeModel(parent)
        self.setModel(self.model)
        self.restore_state("album_view_sizes")

    def selectedAlbums(self):
        for a in self.selectedObjects():
            if isinstance(a, Album):
                yield a

    def contextMenuEvent(self, event):
        obj = TreeModel.object_from_index(self.currentIndex())
        if obj is None:
            return

        plugin_actions = None
        menu = QtGui.QMenu(self)
        if isinstance(obj, Track):
            menu.addAction(self.window.edit_tags_action)
            plugin_actions = list(_track_actions)
            if len(obj.linked_files) == 1:
                plugin_actions.extend(_file_actions)
            if isinstance(obj, NonAlbumTrack):
                menu.addAction(self.window.refresh_action)
        elif isinstance(obj, File):
            menu.addAction(self.window.edit_tags_action)
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            plugin_actions = list(_file_actions)
        elif isinstance(obj, Album):
            menu.addAction(self.window.refresh_action)
            plugin_actions = list(_album_actions)

        menu.addAction(self.window.save_action)
        menu.addAction(self.window.remove_action)

        if isinstance(obj, Album) and not isinstance(obj, NatAlbum) and obj.loaded:
            releases_menu = QtGui.QMenu(_("&Other versions"), menu)
            menu.addSeparator()
            menu.addMenu(releases_menu)
            loading = releases_menu.addAction(_('Loading...'))
            loading.setEnabled(False)

            def _add_other_versions():
                releases_menu.removeAction(loading)
                actions = []
                for i, version in enumerate(obj.other_versions):
                    keys = ("date", "country", "labels", "catnums", "tracks", "format")
                    name = " / ".join([version[k] for k in keys if version[k]]).replace("&", "&&")
                    if name == version["tracks"]:
                        name = "%s / %s" % (_('[no release info]'), name)
                    action = releases_menu.addAction(name)
                    action.setCheckable(True)
                    if obj.id == version["mbid"]:
                        action.setChecked(True)
                    action.triggered.connect(partial(obj.switch_release_version, version["mbid"]))

            if not obj.group_loaded:
                if obj.group_id:
                    obj.release_group_loaded.connect(_add_other_versions)
                    kwargs = {"release-group": obj.group_id, "limit": 100}
                    self.tagger.xmlws.browse_releases(obj._release_group_request_finished, **kwargs)
            else:
                _add_other_versions()

        collections = self.window.collections_panel.model

        if collections.loaded:

            selected_releases = set()
            for album in self.selectedAlbums():
                if album.loaded:
                    selected_releases.add(Release(album.id, album.metadata))

            if selected_releases:
                collections_menu = QtGui.QMenu(_("Collections"), menu)

                def nextCheckState(checkbox, collection):
                    if selected_releases & collection.pending:
                        return
                    diff = selected_releases - collection.releases
                    if not diff:
                        collection.remove_releases(selected_releases)
                        checkbox.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        collection.add_releases(diff)
                        checkbox.setCheckState(QtCore.Qt.Checked)

                for collection in collections.collections:
                    action = QtGui.QWidgetAction(collections_menu)
                    checkbox = QtGui.QCheckBox(collection.name)
                    checkbox.setTristate(True)
                    action.setDefaultWidget(checkbox)
                    collections_menu.addAction(action)

                    diff = selected_releases - collection.releases

                    if not diff:
                        checkbox.setCheckState(QtCore.Qt.Checked)
                    elif diff == selected_releases:
                        checkbox.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        checkbox.setCheckState(QtCore.Qt.PartiallyChecked)

                    checkbox.nextCheckState = partial(nextCheckState, checkbox, collection)

                if not collections_menu.isEmpty():
                    menu.addMenu(collections_menu)

        if plugin_actions:
            plugin_menu = QtGui.QMenu(_("&Plugins"), menu)
            plugin_menu.addActions(plugin_actions)
            plugin_menu.setIcon(self.panel.icon_plugins)
            menu.addSeparator()
            menu.addMenu(plugin_menu)

        if isinstance(obj, Album):
            menu.addAction(self.expand_all_action)
            menu.addAction(self.collapse_all_action)

        menu.exec_(event.globalPos())
        event.accept()

    def remove_selection(self):
        albums = []
        unmatched = {}
        for index in self.selectionModel().selectedRows():
            item = index.internalPointer()
            parent = item.parent
            obj = item.obj
            if isinstance(obj, Track) and not parent.selected:
                obj.remove()
            elif isinstance(obj, Album):
                albums.append(obj)
            elif isinstance(obj, File) and not parent.parent.selected:
                obj.remove()
                try:
                    unmatched[parent].append(obj)
                except KeyError:
                    unmatched[parent] = [obj]
        if albums:
            self.model.root.remove_objects(albums)
            for album in albums:
                album.remove()
        for cluster, files in unmatched.iteritems():
            cluster.remove_objects(files)
            cluster.obj.remove_files(files)


class CollectionsMimeData(QtCore.QMimeData):

    def __init__(self, releases):
        QtCore.QMimeData.__init__(self)
        self.mimeType = "application/picard.collections-data"
        self.releases = releases

    def hasFormat(self, mimeType):
        return mimeType == self.mimeType

    def data(self, mimeType):
        if mimeType == self.mimeType:
            return self.releases
        else:
            return QtCore.QByteArray()


class CollectionTreeView(TreeView):

    options = [TextOption("persist", "collection_view_sizes", "250 200 60 60 100 50 130")]

    def __init__(self, window, parent):
        TreeView.__init__(self, window, parent)
        self.model = CollectionTreeModel(parent)
        self.setModel(self.model)
        self.restore_state("collection_view_sizes")
        self.refresh_action = QtGui.QAction(icontheme.lookup("view-refresh", icontheme.ICON_SIZE_MENU), _("&Refresh"), self)
        self.refresh_action.triggered.connect(self.model.refresh)

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        menu.addAction(self.refresh_action)
        selected = self.selectedObjects()
        count = 0
        removals = {}
        for obj in selected:
            count += 1
            if isinstance(obj, CollectedRelease):
                removals.setdefault(obj.collection, set())
                removals[obj.collection].add(obj.release)
        if removals:
            def remove_releases():
                for collection, releases in removals.iteritems():
                    collection.remove_releases(releases)
            remove_action = QtGui.QAction(icontheme.lookup("list-remove"), _("&Remove releases"), self)
            remove_action.triggered.connect(remove_releases)
            menu.addAction(remove_action)
        current_obj = TreeModel.object_from_index(self.currentIndex())
        if current_obj and count > 0:
            menu.addSeparator()
            open_action = QtGui.QAction(_("&View on MusicBrainz"), self)
            open_action.triggered.connect(partial(self.open_in_browser, current_obj))
            menu.addAction(open_action)
        menu.exec_(event.globalPos())
        event.accept()

    def mimeTypes(self):
        return ["application/picard.album-list", "application/picard.collections-data"]

    def mimeData(self, objects):
        releases = [obj.release for obj in objects if isinstance(obj, CollectedRelease)]
        if releases:
            return CollectionsMimeData(releases)
        return QtCore.QMimeData()

    def open_in_browser(self, obj):
        if isinstance(obj, CollectedRelease):
            entity = "release"
            id = obj.release.id
        elif isinstance(obj, Collection):
            entity = "collection"
            id = obj.id
        setting = self.config.setting
        host, port = setting["server_host"], setting["server_port"]
        url = "http://%s:%s/%s/%s" % (host, port, entity, id)
        webbrowser2.open(url)
