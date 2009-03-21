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
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.file import File
from picard.track import Track
from picard.util import encode_filename, icontheme, partial
from picard.config import Option, TextOption
from picard.plugin import ExtensionPoint
from picard.const import RELEASE_FORMATS


class BaseAction(QtGui.QAction):
    NAME = "Unknown"

    def __init__(self):
        QtGui.QAction.__init__(self, self.NAME, None)
        self.connect(self, QtCore.SIGNAL("triggered()"), self.__callback)

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
        self.connect(self.tagger, QtCore.SIGNAL("cluster_updated"), self.update_cluster)
        self.connect(self.tagger, QtCore.SIGNAL("file_added_to_cluster"), self.add_file_to_cluster)
        self.connect(self.tagger, QtCore.SIGNAL("files_added_to_cluster"), self.add_files_to_cluster)
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
        self.icon_plugins = icontheme.lookup('applications-system', icontheme.ICON_SIZE_MENU)
        self.match_icons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]

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

    def update_object(self, obj, item):
        oldobj = self._item_to_object[item]
        if oldobj != obj:
            self._object_to_item[obj] = item
            self._item_to_object[item] = obj
            del self._object_to_item[oldobj]

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
        item.setIcon(0, self.decide_file_icon(file))
        color = self.file_colors[file.state]
        for i, column in enumerate(self.columns):
            text, similarity = file.column(column[1])
            item.setText(i, text)
            item.setTextColor(i, color)
            item.setBackgroundColor(i, get_match_color(similarity))
    
    def decide_file_icon(self, file):
        if file.state == File.ERROR:
            return self.icon_error
        elif isinstance(file.parent, Track):
            if file.state == File.NORMAL:
                return self.icon_saved
            else:
                return self.match_icons[int(file.similarity * 5 + 0.5)]
        else:
            return self.icon_file

    def update_cluster(self, cluster, item=None):
        if item is None:
            try:
                item = self.item_from_object(cluster)
            except KeyError:
                self.log.debug("Item for %r not found", cluster)
                return
        for i, column in enumerate(self.columns):
            item.setText(i, cluster.column(column[1]))
        album = cluster.related_album
        if cluster.special == 2 and album and album.loaded:
            self.views[1].update_album(album, update_tracks=False)

    def add_file_to_cluster(self, cluster, file):
        try:
            cluster_item = self.item_from_object(cluster)
        except KeyError:
            self.log.debug("Item for %r not found", cluster)
            return
        if cluster.special == 2 and cluster.files:
            cluster_item.setHidden(False)
        self.update_cluster(cluster, cluster_item)
        item = QtGui.QTreeWidgetItem(cluster_item)
        self.register_object(file, item)
        self.update_file(file, item)

    def add_files_to_cluster(self, cluster, files):
        cluster_item = self.item_from_object(cluster)
        if cluster.special == 2 and cluster.files:
            cluster_item.setHidden(False)
        self.update_cluster(cluster, cluster_item)
        items = []
        for file in files:
            item = QtGui.QTreeWidgetItem()
            self.register_object(file, item)
            self.update_file(file, item)
            items.append(item)
        cluster_item.addChildren(items)

    def remove_file_from_cluster(self, cluster, file):
        try:
            cluster_item = self.item_from_object(cluster)
        except KeyError:
            self.log.debug("Item for %r not found", cluster)
            return
        index = cluster_item.indexOfChild(self.item_from_object(file))
        if cluster_item.takeChild(index):
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

    def set_current_release_event(self, album, checked):
        index = self.sender().data().toInt()[0]
        album.set_current_release_event(album.release_events[index])

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return
        obj = self.panel.object_from_item(item)

        plugin_actions = None
        menu = QtGui.QMenu(self)
        if isinstance(obj, Track):
            menu.addAction(self.window.edit_tags_action)
            plugin_actions = list(_track_actions)
            if len(obj.linked_files) == 1:
                plugin_actions.extend(_file_actions)
        elif isinstance(obj, Cluster):
            menu.addAction(self.window.autotag_action)
            menu.addAction(self.window.analyze_action)
            if isinstance(obj, UnmatchedFiles):
                menu.addAction(self.window.cluster_action)
            plugin_actions = list(_cluster_actions)
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

        if isinstance(obj, Album):
            releases_menu = QtGui.QMenu(_("&Releases"), menu)
            #releases_menu.addActions(list(plugin_actions))
            self._set_current_release_event = partial(self.set_current_release_event, obj)
            for i, rel in enumerate(obj.release_events):
                name = []
                if rel.date:
                    name.append(rel.date)
                if rel.releasecountry:
                    name.append(rel.releasecountry)
                if rel.label:
                    name.append(rel.label)
                if rel.catalognumber:
                    name.append(rel.catalognumber)
                if rel.format:
                    try: name.append(RELEASE_FORMATS[rel.format])
                    except (KeyError): name.append(rel.format)
                event_name = " / ".join(name).replace('&', '&&')
                action = releases_menu.addAction(event_name or _('No release event'))
                action.setData(QtCore.QVariant(i))
                action.setCheckable(True)
                self.connect(action, QtCore.SIGNAL("triggered(bool)"), self._set_current_release_event)
                if obj.current_release_event == rel:
                    action.setChecked(True)
            menu.addSeparator()
            menu.addMenu(releases_menu)

        if plugin_actions is not None:
            plugin_menu = QtGui.QMenu(_("&Plugins"), menu)
            plugin_menu.addActions(plugin_actions)
            plugin_menu.setIcon(self.panel.icon_plugins)
            menu.addSeparator()
            menu.addMenu(plugin_menu)

        menu.exec_(event.globalPos())
        event.accept()

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
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

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

    def dropEvent(self, event):
        data = event.mimeData()
        target = None
        item = self.itemAt(event.pos())
        if item:
            target = self.panel.object_from_item(item)
        if not target:
            target = self.tagger.unmatched_files
        self.log.debug("Drop target = %r", target)
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
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()

    def activate_item(self, index):
        obj = self.panel.object_from_item(self.itemFromIndex(index))
        if obj.can_edit_tags():
            self.window.edit_tags([obj])

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

    def remove_cluster(self, cluster):
        index = self.clusters.indexOfChild(self.panel.item_from_object(cluster))
        if self.clusters.takeChild(index):
            for file in cluster.files:
                self.panel.unregister_object(file)
            self.panel.unregister_object(cluster)


class AlbumTreeView(BaseTreeView):

    def __init__(self, window, parent=None):
        BaseTreeView.__init__(self, window, parent)
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

    def update_track(self, track, item=None, update_album=True):
        if item is None:
            try:
                item = self.panel.item_from_object(track)
            except KeyError:
                self.log.debug("Item for %r not found", track)
                return
        if len(track.linked_files) == 1:
            file = track.linked_files[0]
            color = self.track_colors[file.state]
            icon = self.panel.decide_file_icon(file)
            
            # remove old files
            for i in range(item.childCount()):
                file_item = item.takeChild(0)
                self.panel.unregister_object(item=file_item)
        else:
            color = self.palette().text().color()
            bgcolor = get_match_color(1)
            icon = self.panel.icon_note
            
            #Add linked files (there will either be 0 or >1)
            oldnum = item.childCount()
            newnum = len(track.linked_files)
            # remove old items
            if oldnum > newnum:
                for i in range(oldnum - newnum):
                    file_item = item.takeChild(newnum - 1)
                    self.panel.unregister_object(item=file_item)
                oldnum = newnum
            # update existing items
            file_item = None
            for i in range(oldnum):
                file_item = item.child(i)
                file = track.linked_files[i]
                self.panel.update_object(file, file_item)
                self.panel.update_file(file, file_item)
            # add new items
            if newnum > oldnum:
                for i in range(oldnum, newnum):
                    file_item = QtGui.QTreeWidgetItem(item, file_item)
                    file = track.linked_files[i]
                    self.panel.register_object(file, file_item)
                    self.panel.update_file(file, file_item)
            self.expandItem (item)
        item.setIcon(0, icon)
        for i, column in enumerate(self.columns):
            text, similarity = track.column(column[1])
            item.setText(i, text)
            item.setTextColor(i, color)
            item.setBackgroundColor(i, get_match_color(similarity))
        if update_album:
            self.update_album(track.album, update_tracks=False)

    def add_album(self, album):
        item = QtGui.QTreeWidgetItem(self)
        self.panel.register_object(album, item)
        item.setIcon(0, self.panel.icon_cd)
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
            font = album_item.font(i)
            if album.is_complete():
                font.setItalic(False)
            else:
                font.setItalic(True)
            album_item.setFont(i, font)
            album_item.setText(i, album.column(column[1]))
        if update_tracks:
            oldnum = album_item.childCount() - 1
            newnum = len(album.tracks)
            # remove old items
            if oldnum > newnum:
                for i in range(oldnum - newnum):
                    item = album_item.takeChild(newnum - 1)
                    self.panel.unregister_object(item=item)
                oldnum = newnum
            # update existing items
            item = None
            for i in range(oldnum):
                item = album_item.child(i)
                track = album.tracks[i]
                self.panel.update_object(track, item)
                self.update_track(track, item)
            # add new items
            if newnum > oldnum:
                for i in range(oldnum, newnum):
                    item = QtGui.QTreeWidgetItem(album_item, item)
                    track = album.tracks[i]
                    self.panel.register_object(track, item)
                    self.update_track(track, item, update_album=False)
        if album_item.isSelected():
            self.window.updateSelection(self.panel.selected_objects())

    def remove_album(self, album):
        index = self.indexOfTopLevelItem(self.panel.item_from_object(album))
        if self.takeTopLevelItem(index):
            for track in album.tracks:
                self.panel.unregister_object(track)
            self.panel.unregister_object(album)
