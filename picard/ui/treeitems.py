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

from picard.collection import CollectedRelease


class TreeItem:

    def __init__(self, obj, parent, row, model):
        self.obj = obj
        if obj is not None:
            obj.item = self

        self.parent = parent
        self.row = row
        self.rowCount = 0
        self.children = []
        self.selected = False

        self.model = model
        self.columnCount = model.columnCount(self)
        self.dataChanged = model.dataChanged.emit
        self.createIndex = model.createIndex

        self.icon = None
        self.foreground = None
        self.background = None

    @property
    def size(self):
        return len(self.children)

    @property
    def index(self):
        return self.createIndex(self.row, 0, self)

    def remove_rows(self, row, count):
        last = row + count
        model = self.model
        model.beginRemoveRows(self.index, row, last - 1)
        del self.children[row:last]
        self.rowCount -= count
        if len(self.children) > row:
            self._reindex()
        model.endRemoveRows()

    def _reindex(self):
        children = self.children
        for i in xrange(len(children)):
            children[i].row = i

    def clear_rows(self):
        self.remove_rows(0, self.size)

    def add_object(self, obj, cls):
        item = cls(obj, self, self.size, self.model)
        self.children.append(item)
        item.update()
        return item

    def add_objects(self, objects, cls):
        children = self.children
        model = self.model
        for obj in iter(objects):
            item = cls(obj, self, self.size, model)
            children.append(item)
            item.update()

    def remove_object(self, obj):
        self.remove_rows(obj.item.row, 1)

    def remove_objects(self, objects):
        self._remove_rows([obj.item.row for obj in objects])

    def _remove_rows(self, rows):
        rows.sort(reverse=True)
        rows = iter(rows)
        cur = rows.next()
        count = 1
        while True:
            try:
                prev = rows.next()
                if cur == prev + 1:
                    count += 1
                elif cur == prev:
                    continue
                else:
                    self.remove_rows(cur, count)
                    count = 1
                cur = prev
            except StopIteration:
                self.remove_rows(cur, count)
                break

    def expand(self):
        self.model.row_expanded.emit(self.index)

    def data_changed(self):
        self.dataChanged(self.index,
            self.createIndex(self.row, self.columnCount - 1, self))


class TreeRoot(TreeItem):

    def __init__(self, model):
        TreeItem.__init__(self, None, None, 0, model)
        del self.icon
        del self.foreground
        del self.background


class ClusterItem(TreeItem):

    def __init__(self, cluster, parent, row, model):
        TreeItem.__init__(self, cluster, parent, row, model)
        self.icon = self.model.icon_folder

    def add_file(self, file):
        self.add_object(file, FileItem)
        self.model.fetchMore(self.index)
        self.data_changed()

    def remove_file(self, file):
        self.remove_object(file)
        self.data_changed()

    def remove_files(self, files):
        self.remove_objects(files)
        self.data_changed()

    def update(self):
        self.data_changed()


class UnmatchedClusterItem(ClusterItem):

    def __init__(self, cluster, parent, row, model):
        ClusterItem.__init__(self, cluster, parent, row, model)
        self.hidden = False

    def update(self):
        cluster = self.obj
        if not cluster.always_visible:
            hide = not cluster.files
            if hide != self.hidden:
                self.hidden = hide
                self.hide(hide)
        self.data_changed()

    def hide(self, hide):
        self.model.row_hid.emit(self.row, self.parent.index, hide)


class AlbumClusterItem(ClusterItem):

    def remove_file(self, file):
        self.remove_object(file)
        self._update()

    def remove_files(self, files):
        self.remove_objects(files)
        self._update()

    def _update(self):
        if not self.size:
            self.parent.remove_rows(self.row, 1)
        else:
            self.data_changed()


class AlbumItem(TreeItem):

    def __init__(self, album, parent, row, model):
        TreeItem.__init__(self, album, parent, row, model)
        self.add_object(album.unmatched_files, UnmatchedClusterItem).update()

    def update(self, update_tracks=True):
        album = self.obj
        if update_tracks:
            children = self.children
            unmatched = children.pop()
            tracks = album.tracks
            old_size, new_size = self.size, len(tracks)
            left = new_size
            if old_size > new_size:
                self.remove_rows(new_size - 1, old_size - new_size)
            elif new_size > old_size:
                self.add_objects(tracks[old_size:new_size], TrackItem)
                left = old_size
            for i in xrange(left):
                child = children[i]
                child.obj = tracks[i]
                tracks[i].item = child
            children.append(unmatched)
            unmatched.row = new_size
            if unmatched.hidden:
                unmatched.hide(True)
            if new_size > old_size:
                self.model.fetchMore(self.index)
        self.icon = self.model.icon_cd_saved if album.is_complete() else self.model.icon_cd
        self.data_changed()


class TrackItem(TreeItem):

    def add_file(self, file):
        files = self.obj.linked_files
        if len(files) > 1:
            size = self.size
            if size > 0:
                self.add_object(file, FileItem)
            else:
                self.add_objects(files, FileItem)
            self.model.fetchMore(self.index)
        else:
            file.item = None
        self.update()

    def remove_file(self, file):
        if self.size == 2:
            self.clear_rows()
        elif self.size > 0:
            self.remove_object(file)
        self.update()

    def update(self):
        files = self.obj.linked_files
        count = len(files)
        panel = self.model.panel
        if count == 1:
            file = files[0]
            self.foreground = QtGui.QBrush(self.model.track_colors[file.state])
            self.icon = self.model.get_match_icon(file)
            similarity = file.similarity
        else:
            self.foreground = QtGui.QBrush(panel.text_color)
            self.icon = self.model.icon_note
            similarity = 1
            if count > 0:
                self.expand()
        self.background = QtGui.QBrush(FileItem.get_match_color(similarity, panel.base_color))
        self.data_changed()


class FileItem(TreeItem):

    def update(self):
        file = self.obj
        panel = self.model.panel
        self.icon = panel.file_icons[file.state]
        self.foreground = QtGui.QBrush(panel.file_colors[file.state])
        self.background = QtGui.QBrush(self.get_match_color(file.similarity, panel.base_color))
        self.data_changed()

    @staticmethod
    def get_match_color(similarity, basecolor):
        c1 = (basecolor.red(), basecolor.green(), basecolor.blue())
        c2 = (223, 125, 125)
        return QtGui.QColor(
            c2[0] + (c1[0] - c2[0]) * similarity,
            c2[1] + (c1[1] - c2[1]) * similarity,
            c2[2] + (c1[2] - c2[2]) * similarity)


class CollectionItem(TreeItem):

    def update(self, pending=False):
        color = self.model.pending_color if pending else self.model.normal_color
        self.foreground = color
        self.data_changed()

    def add_releases(self, releases, pending=False):
        collection = self.obj
        collected = []
        for release in releases:
            obj = CollectedRelease(release, collection)
            collection.collected_releases[release] = obj
            collected.append(obj)
        self.add_objects(collected, CollectedReleaseItem)
        self.update()

    def remove_releases(self, releases):
        objects = [self.obj.collected_releases.pop(r) for r in releases]
        self.remove_objects(releases)
        self.update()

    def update_releases(self, releases, pending=False):
        collected = self.obj.collected_releases
        for release in releases:
            collected[release].update(pending)


class CollectedReleaseItem(TreeItem):

    def update(self, pending=False):
        color = self.model.pending_color if pending else self.model.normal_color
        self.foreground = color
        self.data_changed()
