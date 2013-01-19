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
from picard.util import encode_filename, icontheme, partial
from picard.config import Option, TextOption
from picard.plugin import ExtensionPoint
from picard.ui.ratingwidget import RatingWidget
from picard.ui.collectionmenu import CollectionMenu


class BaseAction(QtGui.QAction):
    NAME = "Unknown"
    MENU = []

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
_clusterlist_actions = ExtensionPoint()
_track_actions = ExtensionPoint()
_file_actions = ExtensionPoint()

def register_album_action(action):
    _album_actions.register(action.__module__, action)

def register_cluster_action(action):
    _cluster_actions.register(action.__module__, action)

def register_clusterlist_action(action):
    _clusterlist_actions.register(action.__module__, action)

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
        self.views = [FileTreeView(window, self), AlbumTreeView(window, self)]
        self.views[0].itemSelectionChanged.connect(self.update_selection_0)
        self.views[1].itemSelectionChanged.connect(self.update_selection_1)
        self._selected_view = 0
        self._ignore_selection_changes = False
        self._selected_objects = set()

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

    def selected_objects(self):
        return list(self._selected_objects)

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

    def update_selection(self, i, j):
        self._selected_view = i
        self.views[j].clearSelection()
        self._selected_objects.clear()
        self._selected_objects.update(item.obj for item in self.views[i].selectedItems())
        self.window.update_selection(self.selected_objects())

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

    def update_current_view(self):
        self.update_selection(self._selected_view, abs(self._selected_view - 1))

    def remove(self, objects):
        self._ignore_selection_changes = True
        self.tagger.remove(objects)
        self._ignore_selection_changes = False

        view = self.views[self._selected_view]
        index = view.currentIndex()
        if index.isValid():
            # select the current index
            view.setCurrentIndex(index)
        else:
            self.update_current_view()


class BaseTreeView(QtGui.QTreeWidget):

    options = [
        Option("setting", "color_modified", QtGui.QColor(QtGui.QPalette.WindowText), QtGui.QColor),
        Option("setting", "color_saved", QtGui.QColor(0, 128, 0), QtGui.QColor),
        Option("setting", "color_error", QtGui.QColor(200, 0, 0), QtGui.QColor),
        Option("setting", "color_pending", QtGui.QColor(128, 128, 128), QtGui.QColor),
    ]

    def __init__(self, window, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        self.window = window
        self.panel = parent

        self.numHeaderSections = len(MainPanel.columns)
        self.setHeaderLabels([_(h) for h, n in MainPanel.columns])
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

        self.expand_all_action = QtGui.QAction(_("&Expand all"), self)
        self.expand_all_action.triggered.connect(self.expandAll)
        self.collapse_all_action = QtGui.QAction(_("&Collapse all"), self)
        self.collapse_all_action.triggered.connect(self.collapseAll)
        self.doubleClicked.connect(self.activate_item)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return
        obj = item.obj
        plugin_actions = None
        can_view_info = self.window.view_info_action.isEnabled()
        menu = QtGui.QMenu(self)

        if isinstance(obj, Track):
            if can_view_info:
                menu.addAction(self.window.view_info_action)
            plugin_actions = list(_track_actions)
            if obj.num_linked_files == 1:
                menu.addAction(self.window.open_file_action)
                menu.addAction(self.window.open_folder_action)
                plugin_actions.extend(_file_actions)
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            if isinstance(obj, NonAlbumTrack):
                menu.addAction(self.window.refresh_action)
        elif isinstance(obj, Cluster):
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            if isinstance(obj, UnmatchedFiles):
                menu.addAction(self.window.cluster_action)
            plugin_actions = list(_cluster_actions)
        elif isinstance(obj, ClusterList):
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            plugin_actions = list(_clusterlist_actions)
        elif isinstance(obj, File):
            if can_view_info:
                menu.addAction(self.window.view_info_action)
            menu.addAction(self.window.open_file_action)
            menu.addAction(self.window.open_folder_action)
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            plugin_actions = list(_file_actions)
        elif isinstance(obj, Album):
            if can_view_info:
                menu.addAction(self.window.view_info_action)
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            menu.addAction(self.window.refresh_action)
            plugin_actions = list(_album_actions)

        menu.addAction(self.window.save_action)
        menu.addAction(self.window.remove_action)

        bottom_separator = False

        if isinstance(obj, Album) and not isinstance(obj, NatAlbum) and obj.loaded:
            releases_menu = QtGui.QMenu(_("&Other versions"), menu)
            menu.addSeparator()
            menu.addMenu(releases_menu)
            loading = releases_menu.addAction(_('Loading...'))
            loading.setEnabled(False)
            bottom_separator = True

            def _add_other_versions():
                releases_menu.removeAction(loading)
                for version in obj.release_group.versions:
                    action = releases_menu.addAction(version["name"])
                    action.setCheckable(True)
                    if obj.id == version["id"]:
                        action.setChecked(True)
                    action.triggered.connect(partial(obj.switch_release_version, version["id"]))

            _add_other_versions() if obj.release_group.loaded else \
                obj.release_group.load_versions(_add_other_versions)

        if self.config.setting["enable_ratings"] and \
           len(self.window.selected_objects) == 1 and isinstance(obj, Track):
            menu.addSeparator()
            action = QtGui.QWidgetAction(menu)
            action.setDefaultWidget(RatingWidget(menu, obj))
            menu.addAction(action)
            menu.addSeparator()

        selected_albums = [a for a in self.window.selected_objects if type(a) == Album]
        if selected_albums:
            if not bottom_separator:
                menu.addSeparator()
            menu.addMenu(CollectionMenu(selected_albums, _("Collections"), menu))

        if plugin_actions:
            plugin_menu = QtGui.QMenu(_("&Plugins"), menu)
            plugin_menu.setIcon(self.panel.icon_plugins)
            menu.addSeparator()
            menu.addMenu(plugin_menu)

            plugin_menus = {}
            for action in plugin_actions:
                action_menu = plugin_menu
                for index in xrange(1, len(action.MENU)):
                    key = tuple(action.MENU[:index])
                    try:
                        action_menu = plugin_menus[key]
                    except KeyError:
                        action_menu = plugin_menus[key] = action_menu.addMenu(key[-1])
                action_menu.addAction(action)

        if isinstance(obj, Cluster) or isinstance(obj, ClusterList) or isinstance(obj, Album):
            menu.addSeparator()
            menu.addAction(self.expand_all_action)
            menu.addAction(self.collapse_all_action)

        menu.exec_(event.globalPos())
        event.accept()

    def restore_state(self):
        sizes = self.config.persist[self.view_sizes.name]
        header = self.header()
        sizes = sizes.split(" ")
        try:
            for i in range(self.numHeaderSections - 1):
                header.resizeSection(i, int(sizes[i]))
        except IndexError:
            pass

    def save_state(self):
        cols = range(self.numHeaderSections - 1)
        sizes = " ".join(str(self.header().sectionSize(i)) for i in cols)
        self.config.persist[self.view_sizes.name] = sizes

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def mimeTypes(self):
        """List of MIME types accepted by this view."""
        return ["text/uri-list", "application/picard.album-list"]

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.acceptProposedAction()

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
        files = []
        url = QtCore.QUrl.fromLocalFile
        for item in items:
            obj = item.obj
            if isinstance(obj, Album):
                album_ids.append(str(obj.id))
            elif isinstance(obj, Track):
                files.extend(url(file.filename) for file in obj.linked_files)
            elif isinstance(obj, File):
                files.append(url(obj.filename))
            elif isinstance(obj, Cluster):
                files.extend(url(file.filename) for file in obj.files)
            elif isinstance(obj, ClusterList):
                files.extend(url(file.filename) for cluster in obj for file in cluster.files)
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids))
        if files:
            mimeData.setUrls(files)
        return mimeData

    @staticmethod
    def drop_urls(urls, target):
        files = []
        new_files = []
        for url in urls:
            if url.scheme() == "file" or not url.scheme():
                # Dropping a file from iTunes gives a filename with a NULL terminator
                filename = os.path.normpath(os.path.realpath(unicode(url.toLocalFile()).rstrip("\0")))
                file = BaseTreeView.tagger.files.get(filename)
                if file:
                    files.append(file)
                elif os.path.isdir(encode_filename(filename)):
                    BaseTreeView.tagger.add_directory(filename)
                else:
                    new_files.append(filename)
            elif url.scheme() in ("http", "https"):
                path = unicode(url.path())
                match = re.search(r"/(release|recording)/([0-9a-z\-]{36})", path)
                if match:
                    entity = match.group(1)
                    mbid = match.group(2)
                    if entity == "release":
                        BaseTreeView.tagger.load_album(mbid)
                    elif entity == "recording":
                        BaseTreeView.tagger.load_nat(mbid)
        if files:
            BaseTreeView.tagger.move_files(files, target)
        if new_files:
            BaseTreeView.tagger.add_files(new_files, target=target)

    def dropEvent(self, event):
        return QtGui.QTreeView.dropEvent(self, event)

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
        # application/picard.album-list
        albums = data.data("application/picard.album-list")
        if albums:
            if isinstance(self, FileTreeView) and target is None:
                target = self.tagger.unmatched_files
            albums = [self.tagger.load_album(id) for id in str(albums).split("\n")]
            self.tagger.move_files(self.tagger.get_files_from_objects(albums), target)
            handled = True
        return handled

    def activate_item(self, index):
        obj = self.itemFromIndex(index).obj
        if obj.can_view_info():
            self.window.view_info()

    def add_cluster(self, cluster, parent_item=None):
        if parent_item is None:
            parent_item = self.clusters
        cluster_item = ClusterItem(cluster, not cluster.special, parent_item)
        if cluster.hide_if_empty and not cluster.files:
            cluster_item.update()
            cluster_item.setHidden(True)
        else:
            cluster_item.add_files(cluster.files)

    def moveCursor(self, action, modifiers):
        if action in (QtGui.QAbstractItemView.MoveUp, QtGui.QAbstractItemView.MoveDown):
            item = self.currentItem()
            if item and not item.isSelected():
                self.setCurrentItem(item)
        return QtGui.QTreeWidget.moveCursor(self, action, modifiers)


class FileTreeView(BaseTreeView):

    view_sizes = TextOption("persist", "file_view_sizes", "250 40 100")

    def __init__(self, window, parent=None):
        BaseTreeView.__init__(self, window, parent)
        self.unmatched_files = ClusterItem(self.tagger.unmatched_files, False, self)
        self.unmatched_files.update()
        self.setItemExpanded(self.unmatched_files, True)
        self.clusters = ClusterItem(self.tagger.clusters, False, self)
        self.clusters.setText(0, _(u"Clusters"))
        self.setItemExpanded(self.clusters, True)
        self.tagger.cluster_added.connect(self.add_cluster)
        self.tagger.cluster_removed.connect(self.remove_cluster)

    def remove_cluster(self, cluster):
        cluster.item.setSelected(False)
        self.clusters.removeChild(cluster.item)


class AlbumTreeView(BaseTreeView):

    view_sizes = TextOption("persist", "album_view_sizes", "250 40 100")

    def __init__(self, window, parent=None):
        BaseTreeView.__init__(self, window, parent)
        self.tagger.album_added.connect(self.add_album)
        self.tagger.album_removed.connect(self.remove_album)

    def add_album(self, album):
        item = AlbumItem(album, True, self)
        item.setIcon(0, AlbumItem.icon_cd)
        for i, column in enumerate(MainPanel.columns):
            font = item.font(i)
            font.setBold(True)
            item.setFont(i, font)
            item.setText(i, album.column(column[1]))
        self.add_cluster(album.unmatched_files, item)

    def remove_album(self, album):
        album.item.setSelected(False)
        self.takeTopLevelItem(self.indexOfTopLevelItem(album.item))


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


class ClusterItem(TreeItem):

    def __init__(self, *args):
        TreeItem.__init__(self, *args)
        self.setIcon(0, ClusterItem.icon_dir)

    def update(self):
        for i, column in enumerate(MainPanel.columns):
            self.setText(i, self.obj.column(column[1]))
        album = self.obj.related_album
        if self.obj.special and album and album.loaded:
            album.item.update(update_tracks=False)
        if self.isSelected():
            TreeItem.window.update_selection()

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
        file.item.setSelected(False)
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
        for i, column in enumerate(MainPanel.columns):
            self.setText(i, album.column(column[1]))
        if self.isSelected():
            TreeItem.window.update_selection()


class TrackItem(TreeItem):

    def update(self, update_album=True):
        track = self.obj
        if track.num_linked_files == 1:
            file = track.linked_files[0]
            file.item = self
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
                for i in xrange(newnum - 1, oldnum - 1, -1):
                    item = FileItem(track.linked_files[i], False)
                    item.update()
                    items.append(item)
                self.addChildren(items)
            self.setExpanded(True)
        self.setIcon(0, icon)
        for i, column in enumerate(MainPanel.columns):
            self.setText(i, track.column(column[1]))
            self.setForeground(i, color)
            self.setBackground(i, bgcolor)
        if self.isSelected():
            TreeItem.window.update_selection()
        if update_album:
            self.parent().update(update_tracks=False)


class FileItem(TreeItem):

    def update(self):
        file = self.obj
        self.setIcon(0, FileItem.decide_file_icon(file))
        color = FileItem.file_colors[file.state]
        bgcolor = get_match_color(file.similarity, TreeItem.base_color)
        for i, column in enumerate(MainPanel.columns):
            self.setText(i, file.column(column[1]))
            self.setForeground(i, color)
            self.setBackground(i, bgcolor)
        if self.isSelected():
            TreeItem.window.update_selection()

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
