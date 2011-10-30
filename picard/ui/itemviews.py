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
from picard.album import Album, NatAlbum
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.file import File
from picard.track import Track, NonAlbumTrack
from picard.collection import Collection, CollectedRelease, CollectionList
from picard.util import encode_filename, icontheme, partial, webbrowser2
from picard.config import Option, TextOption
from picard.plugin import ExtensionPoint
from picard.const import RELEASE_COUNTRIES


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


_album_actions = ExtensionPoint()
_cluster_actions = ExtensionPoint()
_track_actions = ExtensionPoint()
_file_actions = ExtensionPoint()

def register_album_action(action):
    _album_actions.register(action.__module__, action)

def register_cluster_action(action):
    _cluster_actions.register(action.__module__, action)

def register_track_action(action):
    _track_actions.register(action.__module__, action)

def register_file_action(action):
    _file_actions.register(action.__module__, action)


def get_match_color(similarity, basecolor):
    c1 = (basecolor.red(), basecolor.green(), basecolor.blue())
    c2 = (223, 125, 125)
    return QtGui.QColor(
        c2[0] + (c1[0] - c2[0]) * similarity,
        c2[1] + (c1[1] - c2[1]) * similarity,
        c2[2] + (c1[2] - c2[2]) * similarity)


class MainPanel(QtGui.QSplitter):

    options = [
        Option("persist", "splitter_state", QtCore.QByteArray(), QtCore.QVariant.toByteArray),
        TextOption("persist", "file_view_sizes", "250 40 100"),
        TextOption("persist", "album_view_sizes", "250 40 100"),
        TextOption("persist", "collection_view_sizes", "250 200 60 60 100 50 130"),
        Option("setting", "color_modified", QtGui.QColor(QtGui.QPalette.WindowText), QtGui.QColor),
        Option("setting", "color_saved", QtGui.QColor(0, 128, 0), QtGui.QColor),
        Option("setting", "color_error", QtGui.QColor(200, 0, 0), QtGui.QColor),
        Option("setting", "color_pending", QtGui.QColor(128, 128, 128), QtGui.QColor),
    ]

    def __init__(self, window, parent=None):
        QtGui.QSplitter.__init__(self, parent)
        self.window = window
        self.create_icons()

        self.views = [FileTreeView(window, self), AlbumTreeView(window, self)]
        self.views[0].itemSelectionChanged.connect(self.update_selection_0)
        self.views[1].itemSelectionChanged.connect(self.update_selection_1)
        self._selected_view = 0
        self._ignore_selection_changes = False
        TreeItem.window = window

        TreeItem.base_color = self.palette().base().color()
        TreeItem.text_color = self.palette().text().color()
        TrackItem.track_colors = {
            File.NORMAL: self.config.setting["color_saved"],
            File.CHANGED: TreeItem.text_color,
            File.PENDING: self.config.setting["color_pending"],
            File.ERROR: self.config.setting["color_error"],
        }
        FileItem.file_colors = {
            File.NORMAL: TreeItem.text_color,
            File.CHANGED: self.config.setting["color_modified"],
            File.PENDING: self.config.setting["color_pending"],
            File.ERROR: self.config.setting["color_error"],
        }

    def save_state(self):
        self.config.persist["splitter_state"] = self.saveState()
        for view in self.views:
            view.save_state()

    def restore_state(self):
        self.restoreState(self.config.persist["splitter_state"])

    def create_icons(self):
        if hasattr(QtGui.QStyle, 'SP_DirIcon'):
            ClusterItem.icon_dir = self.style().standardIcon(QtGui.QStyle.SP_DirIcon)
        else:
            ClusterItem.icon_dir = icontheme.lookup('folder', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd = icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_saved = icontheme.lookup('media-optical-saved', icontheme.ICON_SIZE_MENU)
        TrackItem.icon_note = QtGui.QIcon(":/images/note.png")
        FileItem.icon_file = QtGui.QIcon(":/images/file.png")
        FileItem.icon_file_pending = QtGui.QIcon(":/images/file-pending.png")
        FileItem.icon_error = icontheme.lookup('dialog-error', icontheme.ICON_SIZE_MENU)
        FileItem.icon_saved = QtGui.QIcon(":/images/track-saved.png")
        FileItem.match_icons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]
        FileItem.match_pending_icons = [
            QtGui.QIcon(":/images/match-pending-50.png"),
            QtGui.QIcon(":/images/match-pending-60.png"),
            QtGui.QIcon(":/images/match-pending-70.png"),
            QtGui.QIcon(":/images/match-pending-80.png"),
            QtGui.QIcon(":/images/match-pending-90.png"),
            QtGui.QIcon(":/images/match-pending-100.png"),
        ]
        self.icon_plugins = icontheme.lookup('applications-system', icontheme.ICON_SIZE_MENU)

    def selected_objects(self):
        return map(lambda itm: itm.obj, self.views[self._selected_view].selectedItems())

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


class BaseTreeView(QtGui.QTreeWidget):

    def __init__(self, window, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        self.window = window
        self.panel = parent

        self.numHeaderSections = len(self.columns)
        self.setHeaderLabels([_(h) for h, n in self.columns])
        self.restore_state()

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        # enable sorting, but don't actually use it by default
        # XXX it would be nice to be able to go to the 'no sort' mode, but the
        #     internal model that QTreeWidget uses doesn't support it
        self.header().setSortIndicator(-1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)

    def restore_state(self):
        sizes = self.config.persist[self.column_sizes].split()
        header = self.header()
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
        self.config.persist[self.column_sizes] = sizes

    def mimeTypes(self):
        return self.mime_types

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

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
        items = self.selectedItems()
        if items:
            drag = QtGui.QDrag(self)
            drag.setMimeData(self.mimeData(items))
            drag.start(supportedActions)

    def dropEvent(self, event):
        return QtGui.QTreeView.dropEvent(self, event)


class MainPanelView(BaseTreeView):

    columns = [
        (N_('Title'), 'title'),
        (N_('Length'), '~length'),
        (N_('Artist'), 'artist'),
    ]

    def __init__(self, window, parent=None):
        BaseTreeView.__init__(self, window, parent)
        self.expand_all_action = QtGui.QAction(_("&Expand all"), self)
        self.expand_all_action.triggered.connect(self.expandAll)
        self.collapse_all_action = QtGui.QAction(_("&Collapse all"), self)
        self.collapse_all_action.triggered.connect(self.collapseAll)
        self.doubleClicked.connect(self.activate_item)

    def activate_item(self, index):
        obj = self.itemFromIndex(index).obj
        if obj.can_edit_tags():
            self.window.edit_tags([obj])

    def mimeData(self, items):
        """Return MIME data for specified items."""
        album_ids = []
        file_ids = []
        for item in items:
            obj = item.obj
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
            elif isinstance(obj, ClusterList):
                for cluster in obj:
                    for file in cluster.files:
                        file_ids.append(str(file.id))
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids))
        mimeData.setData("application/picard.file-list", "\n".join(file_ids))
        return mimeData

    def dropMimeData(self, parent, index, data, action):
        target = None
        if parent:
            if index == parent.childCount():
                item = parent
            else:
                item = parent.child(index)
            if item is not None:
                target = item.obj
        self.log.debug("Drop target = %r", target)
        handled = False
        # text/uri-list
        urls = data.urls()
        if urls:
            if target is None:
                target = self.tagger.unmatched_files
            self.drop_urls(urls, target)
            handled = True
        files = set()
        # application/picard.file-list
        file_list = data.data("application/picard.file-list")
        if file_list:
            files.update([self.tagger.get_file_by_id(int(id)) for id in str(file_list).split("\n")])
        # application/picard.album-list
        album_list = data.data("application/picard.album-list")
        if album_list:
            albums = [self.tagger.load_album(id) for id in str(album_list).split("\n")]
            files.update(self.tagger.get_files_from_objects(albums))
        if files and target is not None:
            handled = True
            target.take_files(files)
        releases = data.data("application/picard.collections-data")
        if releases:
            for id in [release.id for release in releases]:
                self.tagger.load_album(id)
            handled = True
        return handled

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
                match = re.search(r"/(release|recording)/([0-9a-z\-]{36})", path)
                if not match:
                    continue
                entity = match.group(1)
                mbid = match.group(2)
                if entity == "release":
                    self.tagger.load_album(mbid)
                elif entity == "recording":
                    self.tagger.load_nat(mbid)
        if files:
            self.tagger.add_files(files)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return
        obj = item.obj
        plugin_actions = None
        window = self.window
        menu = QtGui.QMenu(self)

        if isinstance(obj, Track):
            menu.addAction(window.edit_tags_action)
            plugin_actions = list(_track_actions)
            if obj.num_linked_files == 1:
                plugin_actions.extend(_file_actions)
            if isinstance(obj, NonAlbumTrack):
                menu.addAction(window.refresh_action)
        elif isinstance(obj, Cluster):
            menu.addActions((window.autotag_action, window.analyze_action))
            if isinstance(obj, UnmatchedFiles):
                menu.addAction(window.cluster_action)
            plugin_actions = list(_cluster_actions)
        elif isinstance(obj, File):
            menu.addActions((window.edit_tags_action, window.autotag_action, window.analyze_action))
            plugin_actions = list(_file_actions)
        elif isinstance(obj, Album):
            menu.addAction(window.refresh_action)
            plugin_actions = list(_album_actions)

        menu.addActions((window.save_action, window.remove_action))
        separator = False

        if isinstance(obj, Album) and not isinstance(obj, NatAlbum) and obj.loaded:
            releases_menu = QtGui.QMenu(_("&Other versions"), menu)
            separator = True
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

            if obj.rgloaded:
                _add_other_versions()
            elif obj.rgid:
                obj.release_group_loaded.connect(_add_other_versions)
                kwargs = {"release-group": obj.rgid, "limit": 100}
                self.tagger.xmlws.browse_releases(obj._release_group_request_finished, **kwargs)

        collections = window.collections_panel.collection_list

        if collections.loaded:
            selected_albums = {}
            for obj in window.selected_objects:
                if isinstance(obj, Album) and obj.loaded:
                    selected_albums[obj.id] = obj

            if selected_albums:
                collections_menu = QtGui.QMenu(_("Collections"), menu)
                selected_ids = set(selected_albums.keys())

                def nextCheckState(checkbox, collection):
                    if selected_ids & collection.pending:
                        return
                    ids = selected_ids - set(collection.releases.keys())
                    diff = dict([(id, CollectedRelease(id, None, album=selected_albums[id])) for id in ids])
                    if not diff:
                        collection.remove_releases(selected_ids)
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

                    diff = selected_ids - set(collection.releases.keys())
                    if not diff:
                        checkbox.setCheckState(QtCore.Qt.Checked)
                    elif diff == selected_ids:
                        checkbox.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        checkbox.setCheckState(QtCore.Qt.PartiallyChecked)
                    checkbox.nextCheckState = partial(nextCheckState, checkbox, collection)

                if not collections_menu.isEmpty():
                    if not separator:
                        menu.addSeparator()
                    menu.addMenu(collections_menu)

        if plugin_actions:
            plugin_menu = QtGui.QMenu(_("&Plugins"), menu)
            plugin_menu.addActions(plugin_actions)
            plugin_menu.setIcon(self.panel.icon_plugins)
            menu.addSeparator()
            menu.addMenu(plugin_menu)

        menu.addSeparator()
        menu.addActions((self.expand_all_action, self.collapse_all_action))

        menu.exec_(event.globalPos())
        event.accept()


class FileTreeView(MainPanelView):

    column_sizes = "file_view_sizes"
    mime_types = ["text/uri-list",
                  "application/picard.file-list",
                  "application/picard.album-list"]

    def __init__(self, window, parent=None):
        MainPanelView.__init__(self, window, parent)
        self.unmatched_files = ClusterItem(self.tagger.unmatched_files, False, self)
        self.unmatched_files.update()
        self.setItemExpanded(self.unmatched_files, True)
        self.clusters = ClusterItem(None, False, self)
        self.clusters.setText(0, _(u"Clusters"))
        self.setItemExpanded(self.clusters, True)
        self.tagger.cluster_added.connect(self.add_cluster)
        self.tagger.cluster_removed.connect(self.remove_cluster)

    def add_cluster(self, cluster):
        item = ClusterItem(cluster, True, self.clusters)
        if cluster.files:
            item.add_files(cluster.files)
        else:
            item.update()

    def remove_cluster(self, cluster):
        self.clusters.removeChild(cluster.item)


class AlbumTreeView(MainPanelView):

    column_sizes = "album_view_sizes"
    mime_types = ["text/uri-list",
                  "application/picard.file-list",
                  "application/picard.album-list",
                  "application/picard.collections-data"]

    def __init__(self, window, parent=None):
        MainPanelView.__init__(self, window, parent)
        self.tagger.album_added.connect(self.add_album)
        self.tagger.album_removed.connect(self.remove_album)

    def add_album(self, album):
        item = AlbumItem(album, True, self)
        item.setIcon(0, AlbumItem.icon_cd)
        for i, column in enumerate(MainPanelView.columns):
            font = item.font(i)
            font.setBold(True)
            item.setFont(i, font)
            item.setText(i, album.column(column[1]))
        cluster = album.unmatched_files
        cluster_item = ClusterItem(cluster, False, item)
        if cluster.files:
            cluster_item.add_files(cluster.files)
        else:
            cluster_item.update()
            cluster_item.setHidden(True)

    def remove_album(self, album):
        self.takeTopLevelItem(self.indexOfTopLevelItem(album.item))


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


class CollectionTreeView(BaseTreeView):

    column_sizes = "collection_view_sizes"
    columns = [
        (N_("Title"), "title"),
        (N_("Artist"), "albumartist"),
        (N_("Format"), "media"),
        (N_("Tracks"), "totaltracks"),
        (N_("Date"), "date"),
        (N_("Country"), "releasecountry"),
        (N_("Barcode"), "barcode")
    ]
    mime_types = ["application/picard.album-list",
                  "application/picard.collections-data"]

    def __init__(self, window, parent):
        BaseTreeView.__init__(self, window, parent)
        CollectedReleaseItem.normal_color = FileItem.file_colors[File.NORMAL]
        CollectedReleaseItem.pending_color = QtGui.QColor(128, 128, 128)
        self.restore_state()
        self.refresh_action = QtGui.QAction(icontheme.lookup("view-refresh", icontheme.ICON_SIZE_MENU), _("&Refresh"), self)
        self.refresh_action.triggered.connect(self.refresh)
        self.create_action = QtGui.QAction(_("&Create new collection"), self)
        self.create_action.triggered.connect(self.create_collection)
        self.set_message(N_("Loading collections..."))
        self.collection_list = CollectionList(self)

    def add_collection(self, collection):
        item = CollectionItem(collection, True, self)
        item.setFirstColumnSpanned(True)
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        item.update()

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        menu.addAction(self.refresh_action)
        removals = {}
        for item in self.selectedItems():
            obj = item.obj
            if isinstance(obj, CollectedRelease):
                removals.setdefault(obj.collection, set()).add(obj.id)
        if removals:
            def remove_releases():
                for collection, release_ids in removals.iteritems():
                    collection.remove_releases(release_ids)
            remove_action = QtGui.QAction(icontheme.lookup("list-remove"), _("&Remove releases"), self)
            remove_action.triggered.connect(remove_releases)
            menu.addAction(remove_action)
        menu.addSeparator()
        item = self.itemAt(event.pos())
        if item:
            open_action = QtGui.QAction(_("&View on MusicBrainz"), self)
            open_action.triggered.connect(partial(self.open_in_browser, item.obj))
            menu.addAction(open_action)
        menu.addAction(self.create_action)
        menu.exec_(event.globalPos())
        event.accept()

    def mimeData(self, items):
        releases = []
        for item in items:
            obj = item.obj
            if isinstance(obj, CollectedRelease):
                releases.append(CollectedRelease(obj.id, None, data=obj.data))
        if releases:
            return CollectionsMimeData(releases)
        return QtCore.QMimeData()

    def dropMimeData(self, parent, index, data, action):
        if parent is None:
            return False
        target = parent.obj
        if isinstance(target, CollectedRelease):
            target = target.collection
        ids = set(target.releases.keys()) | target.pending
        releases = {}
        albums = data.data("application/picard.album-list")
        if albums:
            for id in str(albums).split("\n"):
                if id not in ids:
                    album = self.tagger.albums.get(id)
                    if album and album.loaded:
                        releases[id] = CollectedRelease(id, target, album=album)
        collected_releases = data.data("application/picard.collections-data")
        if collected_releases:
            for cr in collected_releases:
                if cr.id not in ids:
                    releases[cr.id] = cr
        if releases:
            target.add_releases(releases)
            return True
        return False

    def open_in_browser(self, obj):
        if isinstance(obj, CollectedRelease):
            entity = "release"
        elif isinstance(obj, Collection):
            entity = "collection"
        setting = self.config.setting
        host, port = setting["server_host"], setting["server_port"]
        url = "http://%s:%s/%s/%s" % (host, port, entity, obj.id)
        webbrowser2.open(url)

    def create_collection(self):
        s = self.config.setting
        url = "http://%s:%s/collection/create" % (s["server_host"], s["server_port"])
        webbrowser2.open(url)

    def refresh(self):
        self.set_message(N_("Loading collections..."))
        self.collection_list.load()

    def set_message(self, message):
        self.clear()
        item = QtGui.QTreeWidgetItem(self)
        item.setFlags(QtCore.Qt.NoItemFlags)
        item.setFirstColumnSpanned(True)
        font = item.font(0)
        font.setItalic(True)
        item.setFont(0, font)
        item.setText(0, message)


class TreeItem(QtGui.QTreeWidgetItem):

    __lt__ = lambda self, other: False

    def __init__(self, obj, sortable, *args):
        QtGui.QTreeWidgetItem.__init__(self, *args)
        self.obj = obj
        if obj is not None:
            obj.item = self
        if sortable:
            self.__lt__ = self._lt

    def _lt(self, other):
        column = self.treeWidget().sortColumn()
        if column == 1:
            return (self.obj.metadata.length or 0) < (other.obj.metadata.length or 0)
        return self.text(column).toLower() < other.text(column).toLower()

    def update_window(self):
        selection = TreeItem.window.selected_objects
        if len(selection) == 1 and self.obj in selection:
            TreeItem.window.updateSelection()


class ClusterItem(TreeItem):

    def __init__(self, *args):
        TreeItem.__init__(self, *args)
        self.setIcon(0, ClusterItem.icon_dir)

    def update(self):
        for i, column in enumerate(MainPanelView.columns):
            self.setText(i, self.obj.column(column[1]))
        album = self.obj.related_album
        if self.obj.special and album and album.loaded:
            album.item.update(update_tracks=False)

    def add_file(self, file):
        self.add_files([file])

    def add_files(self, files):
        if self.obj.hide_if_empty and self.obj.files:
            self.setHidden(False)
        self.update()
        items = []
        for file in files:
            item = FileItem(file, True)
            item.update()
            items.append(item)
        self.addChildren(items)

    def remove_file(self, file):
        self.removeChild(file.item)
        self.update()
        if self.obj.hide_if_empty and not self.obj.files:
            self.setHidden(True)


class AlbumItem(TreeItem):

    def update(self, update_tracks=True):
        album = self.obj
        if update_tracks:
            oldnum = self.childCount() - 1
            newnum = len(album.tracks)
            if oldnum > newnum: # remove old items
                for i in xrange(oldnum - newnum):
                    self.takeChild(newnum - 1)
                oldnum = newnum
            # update existing items
            for i in xrange(oldnum):
                item = self.child(i)
                track = album.tracks[i]
                item.obj = track
                track.item = item
                item.update(update_album=False)
            if newnum > oldnum: # add new items
                items = []
                for i in xrange(newnum - 1, oldnum - 1, -1): # insertChildren is backwards
                    item = TrackItem(album.tracks[i], False)
                    item.setHidden(False) # Workaround to make sure the parent state gets updated
                    items.append(item)
                self.insertChildren(oldnum, items)
                for item in items: # Update after insertChildren so that setExpanded works
                    item.update(update_album=False)
        self.setIcon(0, AlbumItem.icon_cd_saved if album.is_complete() else AlbumItem.icon_cd)
        for i, column in enumerate(MainPanelView.columns):
            self.setText(i, album.column(column[1]))
        self.setHidden(False)
        self.update_window()


class TrackItem(TreeItem):

    def update(self, update_album=True):
        track = self.obj
        if track.num_linked_files == 1:
            file = track.linked_files[0]
            color = TrackItem.track_colors[file.state]
            bgcolor = get_match_color(file.similarity, TreeItem.base_color)
            icon = FileItem.decide_file_icon(file)
            self.takeChildren()
        else:
            color = TreeItem.text_color
            bgcolor = get_match_color(1, TreeItem.base_color)
            icon = TrackItem.icon_note
            oldnum = self.childCount()
            newnum = track.num_linked_files
            if oldnum > newnum: # remove old items
                for i in xrange(oldnum - newnum):
                    self.takeChild(newnum - 1).obj.item = None
                oldnum = newnum
            for i in xrange(oldnum): # update existing items
                item = self.child(i)
                file = track.linked_files[i]
                item.obj = file
                file.item = item
                item.update()
            if newnum > oldnum: # add new items
                items = []
                for i in xrange(oldnum, newnum):
                    item = FileItem(track.linked_files[i], False)
                    item.update()
                    items.append(item)
                self.addChildren(items)
            self.setExpanded(True)
        self.setIcon(0, icon)
        for i, column in enumerate(MainPanelView.columns):
            self.setText(i, track.column(column[1]))
            self.setForeground(i, color)
            self.setBackground(i, bgcolor)
        if update_album:
            self.parent().update(update_tracks=False)
        self.update_window()


class FileItem(TreeItem):

    def update(self):
        file = self.obj
        self.setIcon(0, FileItem.decide_file_icon(file))
        color = FileItem.file_colors[file.state]
        bgcolor = get_match_color(file.similarity, TreeItem.base_color)
        for i, column in enumerate(MainPanelView.columns):
            self.setText(i, file.column(column[1]))
            self.setForeground(i, color)
            self.setBackground(i, bgcolor)
        self.update_window()

    @staticmethod
    def decide_file_icon(file):
        if file.state == File.ERROR:
            return FileItem.icon_error
        elif isinstance(file.parent, Track):
            if file.state == File.NORMAL:
                return FileItem.icon_saved
            elif file.state == File.PENDING:
                return FileItem.match_pending_icons[int(file.similarity * 5 + 0.5)]
            else:
                return FileItem.match_icons[int(file.similarity * 5 + 0.5)]
        elif file.state == File.PENDING:
            return FileItem.icon_file_pending
        else:
            return FileItem.icon_file


class CollectionItem(TreeItem):

    def update(self):
        column = self.obj.column
        for i, col in enumerate(CollectionTreeView.columns):
            self.setText(i, column(col[1]))

    def add_releases(self, releases):
        items = []
        for release in releases:
            item = CollectedReleaseItem(release, True, self)
            item.setIcon(0, AlbumItem.icon_cd)
            item.update()
            items.append(item)
        self.addChildren(items)
        self.update()

    def remove_releases(self, releases):
        for release in releases:
            self.removeChild(release.item)
        self.update()


class CollectedReleaseItem(TreeItem):

    def update(self):
        color = self.pending_color if self.obj.pending else self.normal_color
        column = self.obj.column
        for i, col in enumerate(CollectionTreeView.columns):
            self.setText(i, column(col[1]))
            self.setForeground(i, color)
