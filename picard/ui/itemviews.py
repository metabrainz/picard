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
from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets
from picard import config, log
from picard.album import Album, NatAlbum
from picard.cluster import Cluster, ClusterList, UnclusteredFiles
from picard.file import File
from picard.track import Track, NonAlbumTrack
from picard.util import encode_filename, icontheme, restore_method
from picard.plugin import ExtensionPoint
from picard.ui.ratingwidget import RatingWidget
from picard.ui.collectionmenu import CollectionMenu


class BaseAction(QtWidgets.QAction):
    NAME = "Unknown"
    MENU = []

    def __init__(self):
        super().__init__(self.NAME, None)
        self.triggered.connect(self.__callback)

    def __callback(self):
        objs = self.tagger.window.selected_objects
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


class MainPanel(QtWidgets.QSplitter):

    options = [
        config.Option("persist", "splitter_state", QtCore.QByteArray()),
    ]

    columns = [
        (N_('Title'), 'title'),
        (N_('Length'), '~length'),
        (N_('Artist'), 'artist'),
    ]

    def __init__(self, window, parent=None):
        super().__init__(parent)
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
        TreeItem.text_color_secondary = self.palette() \
            .brush(QtGui.QPalette.Disabled, QtGui.QPalette.Text).color()
        TrackItem.track_colors = {
            File.NORMAL: config.setting["color_saved"],
            File.CHANGED: TreeItem.text_color,
            File.PENDING: config.setting["color_pending"],
            File.ERROR: config.setting["color_error"],
        }
        FileItem.file_colors = {
            File.NORMAL: TreeItem.text_color,
            File.CHANGED: config.setting["color_modified"],
            File.PENDING: config.setting["color_pending"],
            File.ERROR: config.setting["color_error"],
        }

    def save_state(self):
        config.persist["splitter_state"] = self.saveState()
        for view in self.views:
            view.save_state()

    @restore_method
    def restore_state(self):
        self.restoreState(config.persist["splitter_state"])

    def create_icons(self):
        if hasattr(QtWidgets.QStyle, 'SP_DirIcon'):
            ClusterItem.icon_dir = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        else:
            ClusterItem.icon_dir = icontheme.lookup('folder', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd = icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_modified = icontheme.lookup('media-optical-modified', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_saved = icontheme.lookup('media-optical-saved', icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_cd_saved_modified = icontheme.lookup('media-optical-saved-modified',
                                                            icontheme.ICON_SIZE_MENU)
        AlbumItem.icon_error = icontheme.lookup('media-optical-error', icontheme.ICON_SIZE_MENU)
        TrackItem.icon_audio = QtGui.QIcon(":/images/track-audio.png")
        TrackItem.icon_video = QtGui.QIcon(":/images/track-video.png")
        TrackItem.icon_data = QtGui.QIcon(":/images/track-data.png")
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
        FileItem.match_icons_info = [
            N_("Bad match"),
            N_("Poor match"),
            N_("Ok match"),
            N_("Good match"),
            N_("Great match"),
            N_("Excellent match"),
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
        self.window.update_selection(
            [item.obj for item in self.views[i].selectedItems()])

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


class BaseTreeView(QtWidgets.QTreeWidget):

    options = [
        config.Option("setting", "color_modified", QtGui.QColor(QtGui.QPalette.WindowText)),
        config.Option("setting", "color_saved", QtGui.QColor(0, 128, 0)),
        config.Option("setting", "color_error", QtGui.QColor(200, 0, 0)),
        config.Option("setting", "color_pending", QtGui.QColor(128, 128, 128)),
    ]

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.panel = parent

        self.numHeaderSections = len(MainPanel.columns)
        self.setHeaderLabels([_(h) for h, n in MainPanel.columns])
        self.restore_state()

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        # enable sorting, but don't actually use it by default
        # XXX it would be nice to be able to go to the 'no sort' mode, but the
        #     internal model that QTreeWidget uses doesn't support it
        self.header().setSortIndicator(-1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)

        self.expand_all_action = QtWidgets.QAction(_("&Expand all"), self)
        self.expand_all_action.triggered.connect(self.expandAll)
        self.collapse_all_action = QtWidgets.QAction(_("&Collapse all"), self)
        self.collapse_all_action.triggered.connect(self.collapseAll)
        self.select_all_action = QtWidgets.QAction(_("Select &all"), self)
        self.select_all_action.triggered.connect(self.selectAll)
        self.select_all_action.setShortcut(QtGui.QKeySequence(_("Ctrl+A")))
        self.doubleClicked.connect(self.activate_item)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return
        obj = item.obj
        plugin_actions = None
        can_view_info = self.window.view_info_action.isEnabled()
        menu = QtWidgets.QMenu(self)

        if isinstance(obj, Track):
            if can_view_info:
                menu.addAction(self.window.view_info_action)
            plugin_actions = list(_track_actions)
            if obj.num_linked_files == 1:
                menu.addAction(self.window.play_file_action)
                menu.addAction(self.window.open_folder_action)
                menu.addAction(self.window.track_search_action)
                plugin_actions.extend(_file_actions)
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            if isinstance(obj, NonAlbumTrack):
                menu.addAction(self.window.refresh_action)
        elif isinstance(obj, Cluster):
            if can_view_info:
                menu.addAction(self.window.view_info_action)
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            if isinstance(obj, UnclusteredFiles):
                menu.addAction(self.window.cluster_action)
            else:
                menu.addAction(self.window.album_search_action)
            plugin_actions = list(_cluster_actions)
        elif isinstance(obj, ClusterList):
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            plugin_actions = list(_clusterlist_actions)
        elif isinstance(obj, File):
            if can_view_info:
                menu.addAction(self.window.view_info_action)
            menu.addAction(self.window.play_file_action)
            menu.addAction(self.window.open_folder_action)
            menu.addAction(self.window.browser_lookup_action)
            menu.addSeparator()
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            menu.addAction(self.window.track_search_action)
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
            releases_menu = QtWidgets.QMenu(_("&Other versions"), menu)
            menu.addSeparator()
            menu.addMenu(releases_menu)
            loading = releases_menu.addAction(_('Loading...'))
            loading.setDisabled(True)
            bottom_separator = True

            if len(self.selectedIndexes()) == len(MainPanel.columns):
                def _add_other_versions():
                    releases_menu.removeAction(loading)
                    heading = releases_menu.addAction(obj.release_group.version_headings)
                    heading.setDisabled(True)
                    font = heading.font()
                    font.setBold(True)
                    heading.setFont(font)

                    versions = obj.release_group.versions

                    albumtracks = obj.get_num_total_files() if obj.get_num_total_files() else len(obj.tracks)
                    preferred_countries = set(config.setting["preferred_release_countries"])
                    preferred_formats = set(config.setting["preferred_release_formats"])
                    matches = ("trackmatch", "countrymatch", "formatmatch")
                    priorities = {}
                    for version in versions:
                        priority = {
                            "trackmatch": "0" if version['totaltracks'] == albumtracks else "?",
                            "countrymatch": "0" if len(preferred_countries) == 0 or preferred_countries & set(version['countries'] or '') else "?",
                            "formatmatch": "0" if len(preferred_formats) == 0 or preferred_formats & set(version['formats'] or '') else "?",
                        }
                        priorities[version['id']] = "".join(priority[k] for k in matches)
                    versions.sort(key=lambda version: priorities[version['id']] + version['name'])

                    priority = normal = False
                    for version in versions:
                        if not normal and "?" in priorities[version['id']]:
                            if priority:
                                releases_menu.addSeparator()
                            normal = True
                        else:
                            priority = True
                        action = releases_menu.addAction(version["name"])
                        action.setCheckable(True)
                        if obj.id == version["id"]:
                            action.setChecked(True)
                        action.triggered.connect(partial(obj.switch_release_version, version["id"]))

                if obj.release_group.loaded:
                    _add_other_versions()
                else:
                    obj.release_group.load_versions(_add_other_versions)
                releases_menu.setEnabled(True)
            else:
                releases_menu.setEnabled(False)

        if config.setting["enable_ratings"] and \
           len(self.window.selected_objects) == 1 and isinstance(obj, Track):
            menu.addSeparator()
            action = QtWidgets.QWidgetAction(menu)
            action.setDefaultWidget(RatingWidget(menu, obj))
            menu.addAction(action)
            menu.addSeparator()

        # Using type here is intentional. isinstance will return true for the
        # NatAlbum instance, which can't be part of a collection.
        selected_albums = [a for a in self.window.selected_objects if type(a) == Album]
        if selected_albums:
            if not bottom_separator:
                menu.addSeparator()
            menu.addMenu(CollectionMenu(selected_albums, _("Collections"), menu))

        if plugin_actions:
            plugin_menu = QtWidgets.QMenu(_("P&lugins"), menu)
            plugin_menu.setIcon(self.panel.icon_plugins)
            menu.addSeparator()
            menu.addMenu(plugin_menu)

            plugin_menus = {}
            for action in plugin_actions:
                action_menu = plugin_menu
                for index in range(1, len(action.MENU) + 1):
                    key = tuple(action.MENU[:index])
                    if key in plugin_menus:
                        action_menu = plugin_menus[key]
                    else:
                        action_menu = plugin_menus[key] = action_menu.addMenu(key[-1])
                action_menu.addAction(action)

        if isinstance(obj, Cluster) or isinstance(obj, ClusterList) or isinstance(obj, Album):
            menu.addSeparator()
            menu.addAction(self.expand_all_action)
            menu.addAction(self.collapse_all_action)

        menu.addAction(self.select_all_action)
        menu.exec_(event.globalPos())
        event.accept()

    @restore_method
    def restore_state(self):
        sizes = config.persist[self.view_sizes.name]
        header = self.header()
        sizes = sizes.split(" ")
        try:
            for i in range(self.numHeaderSections - 1):
                header.resizeSection(i, int(sizes[i]))
        except IndexError:
            pass

    def save_state(self):
        cols = range(self.numHeaderSections - 1)
        sizes = " ".join(string_(self.header().sectionSize(i)) for i in cols)
        config.persist[self.view_sizes.name] = sizes

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
            drag.exec_(QtCore.Qt.MoveAction)

    def mimeData(self, items):
        """Return MIME data for specified items."""
        album_ids = []
        files = []
        url = QtCore.QUrl.fromLocalFile
        for item in items:
            obj = item.obj
            if isinstance(obj, Album):
                album_ids.append(string_(obj.id))
            elif obj.iterfiles:
                files.extend([url(f.filename) for f in obj.iterfiles()])
        mimeData = QtCore.QMimeData()
        mimeData.setData("application/picard.album-list", "\n".join(album_ids).encode())
        if files:
            mimeData.setUrls(files)
        return mimeData

    @staticmethod
    def drop_urls(urls, target):
        files = []
        new_files = []
        for url in urls:
            log.debug("Dropped the URL: %r", url.toString(QtCore.QUrl.RemoveUserInfo))
            if url.scheme() == "file" or not url.scheme():
                filename = os.path.normpath(os.path.realpath(url.toLocalFile().rstrip("\0")))
                file = BaseTreeView.tagger.files.get(filename)
                if file:
                    files.append(file)
                elif os.path.isdir(encode_filename(filename)):
                    BaseTreeView.tagger.add_directory(filename)
                else:
                    new_files.append(filename)
            elif url.scheme() in ("http", "https"):
                path = url.path()
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
        return QtWidgets.QTreeView.dropEvent(self, event)

    def dropMimeData(self, parent, index, data, action):
        target = None
        if parent:
            if index == parent.childCount():
                item = parent
            else:
                item = parent.child(index)
            if item is not None:
                target = item.obj
        log.debug("Drop target = %r", target)
        handled = False
        # text/uri-list
        urls = data.urls()
        if urls:
            self.drop_urls(urls, target)
            handled = True
        # application/picard.album-list
        albums = data.data("application/picard.album-list")
        if albums:
            if isinstance(self, FileTreeView) and target is None:
                target = self.tagger.unclustered_files
            albums = [self.tagger.load_album(id) for id in string_(albums).split("\n")]
            self.tagger.move_files(self.tagger.get_files_from_objects(albums), target)
            handled = True
        return handled

    def activate_item(self, index):
        obj = self.itemFromIndex(index).obj
        # Double-clicking albums or clusters should expand them. The album info can be
        # viewed by using the toolbar button.
        if not isinstance(obj, (Album, Cluster)) and obj.can_view_info():
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
        if action in (QtWidgets.QAbstractItemView.MoveUp, QtWidgets.QAbstractItemView.MoveDown):
            item = self.currentItem()
            if item and not item.isSelected():
                self.setCurrentItem(item)
        return QtWidgets.QTreeWidget.moveCursor(self, action, modifiers)


class FileTreeView(BaseTreeView):

    view_sizes = config.TextOption("persist", "file_view_sizes", "250 40 100")

    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.setAccessibleName(_("file view"))
        self.setAccessibleDescription(_("Contains unmatched files and clusters"))
        self.unmatched_files = ClusterItem(self.tagger.unclustered_files, False, self)
        self.unmatched_files.update()
        self.unmatched_files.setExpanded(True)
        self.clusters = ClusterItem(self.tagger.clusters, False, self)
        self.set_clusters_text()
        self.clusters.setExpanded(True)
        self.tagger.cluster_added.connect(self.add_file_cluster)
        self.tagger.cluster_removed.connect(self.remove_file_cluster)

    def add_file_cluster(self, cluster, parent_item=None):
        self.add_cluster(cluster, parent_item)
        self.set_clusters_text()

    def remove_file_cluster(self, cluster):
        cluster.item.setSelected(False)
        self.clusters.removeChild(cluster.item)
        self.set_clusters_text()

    def set_clusters_text(self):
        self.clusters.setText(0, '%s (%d)' % (_("Clusters"), len(self.tagger.clusters)))


class AlbumTreeView(BaseTreeView):

    view_sizes = config.TextOption("persist", "album_view_sizes", "250 40 100")

    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.setAccessibleName(_("album view"))
        self.setAccessibleDescription(_("Contains albums and matched files"))
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


class TreeItem(QtWidgets.QTreeWidgetItem):

    __lt__ = lambda self, other: False

    def __init__(self, obj, sortable, *args):
        super().__init__(*args)
        self.obj = obj
        if obj is not None:
            obj.item = self
        if sortable:
            self.__lt__ = self._lt
        self.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _lt(self, other):
        column = self.treeWidget().sortColumn()
        if column == 1:
            return (self.obj.metadata.length or 0) < (other.obj.metadata.length or 0)
        return self.text(column).lower() < other.text(column).lower()


class ClusterItem(TreeItem):

    def __init__(self, *args):
        super().__init__(*args)
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
        # addChild used (rather than building an items list and adding with addChildren)
        # to be certain about item order in the cluster (addChildren adds in reverse order).
        # Benchmarked performance was not noticeably different.
        for file in files:
            item = FileItem(file, True)
            item.update()
            self.addChild(item)

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
            if oldnum > newnum:  # remove old items
                for i in range(oldnum - newnum):
                    self.takeChild(newnum - 1)
                oldnum = newnum
            # update existing items
            for i in range(oldnum):
                item = self.child(i)
                track = album.tracks[i]
                item.obj = track
                track.item = item
                item.update(update_album=False)
            if newnum > oldnum:  # add new items
                items = []
                for i in range(newnum - 1, oldnum - 1, -1):  # insertChildren is backwards
                    item = TrackItem(album.tracks[i], False)
                    item.setHidden(False)  # Workaround to make sure the parent state gets updated
                    items.append(item)
                self.insertChildren(oldnum, items)
                for item in items:  # Update after insertChildren so that setExpanded works
                    item.update(update_album=False)
        if album.errors:
            self.setIcon(0, AlbumItem.icon_error)
            self.setToolTip(0, _("Error"))
        elif album.is_complete():
            if album.is_modified():
                self.setIcon(0, AlbumItem.icon_cd_saved_modified)
                self.setToolTip(0, _("Album modified and complete"))
            else:
                self.setIcon(0, AlbumItem.icon_cd_saved)
                self.setToolTip(0, _("Album unchanged and complete"))
        else:
            if album.is_modified():
                self.setIcon(0, AlbumItem.icon_cd_modified)
                self.setToolTip(0, _("Album modified"))
            else:
                self.setIcon(0, AlbumItem.icon_cd)
                self.setToolTip(0, _("Album unchanged"))
        for i, column in enumerate(MainPanel.columns):
            self.setText(i, album.column(column[1]))
        if self.isSelected():
            TreeItem.window.update_selection()


class TrackItem(TreeItem):

    def update(self, update_album=True, update_files=True):
        track = self.obj
        if track.num_linked_files == 1:
            file = track.linked_files[0]
            file.item = self
            color = TrackItem.track_colors[file.state]
            bgcolor = get_match_color(file.similarity, TreeItem.base_color)
            icon = FileItem.decide_file_icon(file)
            self.setToolTip(0, _(FileItem.decide_file_icon_info(file)))
            self.takeChildren()
        else:
            self.setToolTip(0, "")
            if track.ignored_for_completeness():
                color = TreeItem.text_color_secondary
            else:
                color = TreeItem.text_color
            bgcolor = get_match_color(1, TreeItem.base_color)
            if track.is_video():
                icon = TrackItem.icon_video
            elif track.is_data():
                icon = TrackItem.icon_data
            else:
                icon = TrackItem.icon_audio
            if update_files:
                oldnum = self.childCount()
                newnum = track.num_linked_files
                if oldnum > newnum:  # remove old items
                    for i in range(oldnum - newnum):
                        self.takeChild(newnum - 1).obj.item = None
                    oldnum = newnum
                for i in range(oldnum):  # update existing items
                    item = self.child(i)
                    file = track.linked_files[i]
                    item.obj = file
                    file.item = item
                    item.update(update_track=False)
                if newnum > oldnum:  # add new items
                    items = []
                    for i in range(newnum - 1, oldnum - 1, -1):
                        item = FileItem(track.linked_files[i], False)
                        item.update(update_track=False)
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

    def update(self, update_track=True):
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

        parent = self.parent()
        if isinstance(parent, TrackItem) and update_track:
            parent.update(update_files=False)

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

    @staticmethod
    def decide_file_icon_info(file):
        # Note error state info is already handled
        if isinstance(file.parent, Track):
            if file.state == File.NORMAL:
                return N_("Track saved")
            elif file.state == File.PENDING:   # unsure how to use int(file.similarity * 5 + 0.5)
                return N_("Pending")
            else:   # returns description of the match ranging from bad to excellent
                return FileItem.match_icons_info[int(file.similarity * 5 + 0.5)]
        elif file.state == File.PENDING:
            return N_("Pending")
