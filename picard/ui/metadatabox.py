# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

from PyQt4 import QtCore, QtGui
from collections import defaultdict
from functools import partial
from picard import config
from picard.album import Album
from picard.cluster import Cluster
from picard.track import Track
from picard.file import File
from picard.util import format_time, throttle
from picard.util.tags import display_tag_name
from picard.ui.edittagdialog import EditTagDialog
from picard.metadata import MULTI_VALUED_JOINER


COMMON_TAGS = [
    "title",
    "artist",
    "album",
    "tracknumber",
    "~length",
    "date",
]


class TagStatus:

    NoChange = 1
    Added = 2
    Removed = 4
    # Added | Removed = Changed
    Changed = 6
    Empty = 8
    NotRemovable = 16


class TagCounter(dict):

    __slots__ = ("parent", "counts", "different")

    def __init__(self, parent):
        self.parent = parent
        self.counts = defaultdict(lambda: 0)
        self.different = set()

    def __getitem__(self, tag):
        return dict.get(self, tag, [""])

    def add(self, tag, values):
        if tag not in self.different:
            if tag not in self:
                self[tag] = values
            elif self[tag] != values:
                self.different.add(tag)
                self[tag] = [""]
        self.counts[tag] += 1

    def display_value(self, tag):
        count = self.counts[tag]
        missing = self.parent.objects - count

        if tag in self.different:
            return (ungettext("(different across %d item)", "(different across %d items)", count) % count, True)
        else:
            if tag == "~length":
                msg = format_time(self.get(tag, 0))
            else:
                msg = MULTI_VALUED_JOINER.join(self[tag])

            if count > 0 and missing > 0:
                return (msg + " " + (ungettext("(missing from %d item)", "(missing from %d items)", missing) % missing), True)
            else:
                return (msg, False)


class TagDiff(object):

    __slots__ = ("tag_names", "new", "orig", "status", "objects")

    def __init__(self):
        self.tag_names = []
        self.new = TagCounter(self)
        self.orig = TagCounter(self)
        self.status = defaultdict(lambda: 0)
        self.objects = 0

    def __tag_ne(self, tag, orig, new):
        if tag == "~length":
            return abs(float(orig) - float(new)) > 2000
        else:
            return orig != new

    def add(self, tag, orig_values, new_values, removable):
        if orig_values:
            self.orig.add(tag, orig_values)

        if new_values:
            self.new.add(tag, new_values)

        if orig_values and not new_values:
            self.status[tag] |= TagStatus.Removed
            removable = False
        elif new_values and not orig_values:
            self.status[tag] |= TagStatus.Added
            removable = True
        elif orig_values and new_values and self.__tag_ne(tag, orig_values, new_values):
            self.status[tag] |= TagStatus.Changed
        elif not (orig_values or new_values or tag in COMMON_TAGS):
            self.status[tag] |= TagStatus.Empty
        else:
            self.status[tag] |= TagStatus.NoChange

        if not removable:
            self.status[tag] |= TagStatus.NotRemovable

    def tag_status(self, tag):
        status = self.status[tag]
        for s in (TagStatus.Changed, TagStatus.Added,
                  TagStatus.Removed, TagStatus.Empty):
            if status & s == s:
                return s
        return TagStatus.NoChange


class MetadataBox(QtGui.QTableWidget):

    options = (
        config.TextOption("persist", "metadata_box_sizes", "150 300 300"),
        config.BoolOption("persist", "show_changes_first", False)
    )

    def __init__(self, parent):
        QtGui.QTableWidget.__init__(self, parent)
        self.parent = parent
        self.setAccessibleName(_("metadata view"))
        self.setAccessibleDescription(_("Displays original and new tags for the selected files"))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels((_("Tag"), _("Original Value"), _("New Value")))
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setClickable(False)
        self.verticalHeader().setDefaultSectionSize(21)
        self.verticalHeader().setVisible(False)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setTabKeyNavigation(False)
        self.setStyleSheet("QTableWidget {border: none;}")
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 1)
        self.colors = {
            TagStatus.NoChange: self.palette().color(QtGui.QPalette.Text),
            TagStatus.Removed: QtGui.QBrush(QtGui.QColor("red")),
            TagStatus.Added: QtGui.QBrush(QtGui.QColor("green")),
            TagStatus.Changed: QtGui.QBrush(QtGui.QColor("darkgoldenrod"))
        }
        self.files = set()
        self.tracks = set()
        self.objects = set()
        self.selection_mutex = QtCore.QMutex()
        self.selection_dirty = False
        self.editing = None # the QTableWidgetItem being edited
        self.clipboard = [""]
        self.add_tag_action = QtGui.QAction(_(u"Add New Tag..."), parent)
        self.add_tag_action.triggered.connect(partial(self.edit_tag, ""))
        self.changes_first_action = QtGui.QAction(_(u"Show Changes First"), parent)
        self.changes_first_action.setCheckable(True)
        self.changes_first_action.setChecked(config.persist["show_changes_first"])
        self.changes_first_action.toggled.connect(self.toggle_changes_first)

    def edit(self, index, trigger, event):
        if index.column() != 2:
            return False
        item = self.itemFromIndex(index)
        if item.flags() & QtCore.Qt.ItemIsEditable and \
           trigger in (QtGui.QAbstractItemView.DoubleClicked,
                       QtGui.QAbstractItemView.EditKeyPressed,
                       QtGui.QAbstractItemView.AnyKeyPressed):
            tag = self.tag_diff.tag_names[item.row()]
            values = self.tag_diff.new[tag]
            if len(values) > 1:
                self.edit_tag(tag)
                return False
            else:
                self.editing = item
                item.setText(values[0])
                return QtGui.QTableWidget.edit(self, index, trigger, event)
        return False

    def event(self, e):
        item = self.currentItem()
        if (item and e.type() == QtCore.QEvent.KeyPress and e.modifiers() == QtCore.Qt.ControlModifier):
            column = item.column()
            tag = self.tag_diff.tag_names[item.row()]
            if e.key() == QtCore.Qt.Key_C:
                if column == 1:
                    self.clipboard = list(self.tag_diff.orig[tag])
                elif column == 2:
                    self.clipboard = list(self.tag_diff.new[tag])
            elif e.key() == QtCore.Qt.Key_V and column == 2 and tag != "~length":
                self.set_tag_values(tag, list(self.clipboard))
        return QtGui.QTableWidget.event(self, e)

    def closeEditor(self, editor, hint):
        QtGui.QTableWidget.closeEditor(self, editor, hint)
        tag = self.tag_diff.tag_names[self.editing.row()]
        old = self.tag_diff.new[tag]
        new = [unicode(editor.text())]
        if old == new:
            self.editing.setText(old[0])
        else:
            self.set_tag_values(tag, new)
        self.editing = None
        self.update()

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        if self.objects:
            tags = self.selected_tags()
            if len(tags) == 1:
                edit_tag_action = QtGui.QAction(_(u"Edit..."), self.parent)
                edit_tag_action.triggered.connect(partial(self.edit_tag, list(tags)[0]))
                menu.addAction(edit_tag_action)
            removals = []
            useorigs = []
            for tag in tags:
                if self.tag_is_removable(tag):
                    removals.append(partial(self.remove_tag, tag))
                status = self.tag_diff.status[tag] & TagStatus.Changed
                if status == TagStatus.Changed or status == TagStatus.Removed:
                    for file in self.files:
                        objects = [file]
                        if file.parent in self.tracks and len(self.files & set(file.parent.linked_files)) == 1:
                            objects.append(file.parent)
                        orig_values = list(file.orig_metadata.getall(tag)) or [""]
                        useorigs.append(partial(self.set_tag_values, tag, orig_values, objects))
            if removals:
                remove_tag_action = QtGui.QAction(_(u"Remove"), self.parent)
                remove_tag_action.triggered.connect(lambda: [f() for f in removals])
                menu.addAction(remove_tag_action)
            if useorigs:
                name = ungettext("Use Original Value", "Use Original Values", len(useorigs))
                use_orig_value_action = QtGui.QAction(name, self.parent)
                use_orig_value_action.triggered.connect(lambda: [f() for f in useorigs])
                menu.addAction(use_orig_value_action)
                menu.addSeparator()
            if len(tags) == 1 or removals or useorigs:
                menu.addSeparator()
            menu.addAction(self.add_tag_action)
            menu.addSeparator()
        menu.addAction(self.changes_first_action)
        menu.exec_(event.globalPos())
        event.accept()

    def edit_tag(self, tag):
        EditTagDialog(self.parent, tag).exec_()

    def toggle_changes_first(self, checked):
        config.persist["show_changes_first"] = checked
        self.update()

    def set_tag_values(self, tag, values, objects=None):
        if objects is None:
            objects = self.objects
        self.parent.ignore_selection_changes = True
        if values != [""] or self.tag_is_removable(tag):
            for obj in objects:
                obj.metadata[tag] = values
                obj.update()
        self.update()
        self.parent.ignore_selection_changes = False

    def remove_tag(self, tag):
        self.set_tag_values(tag, [""])

    def remove_selected_tags(self):
        (self.remove_tag(tag) for tag in self.selected_tags() if self.tag_is_removable(tag))

    def tag_is_removable(self, tag):
        return self.tag_diff.status[tag] & TagStatus.NotRemovable == 0

    def selected_tags(self):
        tags = set(self.tag_diff.tag_names[item.row()]
                   for item in self.selectedItems())
        tags.discard("~length")
        return tags

    def _update_selection(self):
        files = set()
        tracks = set()
        objects = set()
        for obj in self.parent.selected_objects:
            if isinstance(obj, File):
                files.add(obj)
            elif isinstance(obj, Track):
                tracks.add(obj)
                files.update(obj.linked_files)
            elif isinstance(obj, Cluster) and obj.can_edit_tags():
                objects.add(obj)
                files.update(obj.files)
            elif isinstance(obj, Album):
                objects.add(obj)
                tracks.update(obj.tracks)
                for track in obj.tracks:
                    files.update(track.linked_files)
        objects.update(files)
        objects.update(tracks)
        self.selection_dirty = False

        self.selection_mutex.lock()
        self.files = files
        self.tracks = tracks
        self.objects = objects
        self.selection_mutex.unlock()

    @throttle(100)
    def update(self):
        if self.editing:
            return

        if self.selection_dirty:
            self._update_selection()

        self.tagger.other_queue.put((
            self._update_tags, self._update_items, QtCore.Qt.LowEventPriority))

    def _update_tags(self):
        self.selection_mutex.lock()
        files = self.files
        tracks = self.tracks
        self.selection_mutex.unlock()

        if not (files or tracks):
            return None

        tag_diff = TagDiff()
        orig_tags = tag_diff.orig
        new_tags = tag_diff.new
        # existing_tags are orig_tags that would not be overwritten by
        # any new_tags, assuming clear_existing_tags is disabled.
        existing_tags = set()
        tag_diff.objects = len(files)

        clear_existing_tags = config.setting["clear_existing_tags"]

        for file in files:
            new_metadata = file.metadata
            orig_metadata = file.orig_metadata
            tags = set(new_metadata.keys() + orig_metadata.keys())

            for name in filter(lambda x: not x.startswith("~"), tags):
                new_values = new_metadata.getall(name)
                orig_values = orig_metadata.getall(name)

                if not ((new_values and not name in existing_tags) or clear_existing_tags):
                    new_values = list(orig_values or [""])
                    existing_tags.add(name)

                tag_diff.add(name, orig_values, new_values, clear_existing_tags)

            tag_diff.add("~length",
                str(orig_metadata.length), str(new_metadata.length), False)

        for track in tracks:
            if track.num_linked_files == 0:
                for name, values in dict.iteritems(track.metadata):
                    if not name.startswith("~"):
                        tag_diff.add(name, values, values, True)

                length = str(track.metadata.length)
                tag_diff.add("~length", length, length, False)

                tag_diff.objects += 1

        all_tags = set(orig_tags.keys() + new_tags.keys())
        tag_names = COMMON_TAGS + sorted(all_tags.difference(COMMON_TAGS))

        if config.persist["show_changes_first"]:
            tags_by_status = {}

            for tag in tag_names:
                tags_by_status.setdefault(tag_diff.tag_status(tag), []).append(tag)

            for status in (TagStatus.Changed, TagStatus.Added,
                           TagStatus.Removed, TagStatus.NoChange):
                tag_diff.tag_names += tags_by_status.pop(status, [])
        else:
            tag_diff.tag_names = [
                tag for tag in tag_names if
                tag_diff.status[tag] != TagStatus.Empty]

        return tag_diff

    def _update_items(self, result=None, error=None):
        if self.editing:
            return

        if not (self.files or self.tracks):
            result = None

        self.tag_diff = result

        if result is None:
            self.setRowCount(0)
            return

        self.setRowCount(len(result.tag_names))

        orig_flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        new_flags = orig_flags | QtCore.Qt.ItemIsEditable

        for i, name in enumerate(result.tag_names):
            length = name == "~length"
            tag_item = self.item(i, 0)
            orig_item = self.item(i, 1)
            new_item = self.item(i, 2)
            if not tag_item:
                tag_item = QtGui.QTableWidgetItem()
                tag_item.setFlags(orig_flags)
                font = tag_item.font()
                font.setBold(True)
                tag_item.setFont(font)
                self.setItem(i, 0, tag_item)
            if not orig_item:
                orig_item = QtGui.QTableWidgetItem()
                orig_item.setFlags(orig_flags)
                self.setItem(i, 1, orig_item)
            if not new_item:
                new_item = QtGui.QTableWidgetItem()
                self.setItem(i, 2, new_item)
            tag_item.setText(display_tag_name(name))
            self.set_item_value(orig_item, self.tag_diff.orig, name)
            new_item.setFlags(orig_flags if length else new_flags)
            self.set_item_value(new_item, self.tag_diff.new, name)

            color = self.colors.get(result.tag_status(name),
                    self.colors[TagStatus.NoChange])
            orig_item.setForeground(color)
            new_item.setForeground(color)

    def set_item_value(self, item, tags, name):
        text, italic = tags.display_value(name)
        item.setText(text)
        font = item.font()
        font.setItalic(italic)
        item.setFont(font)

    def restore_state(self):
        sizes = config.persist["metadata_box_sizes"].split(" ")
        header = self.horizontalHeader()
        try:
            for i in range(header.count()):
                size = max(int(sizes[i]), header.sectionSizeHint(i))
                header.resizeSection(i, size)
        except IndexError:
            pass
        self.shrink_columns()

    def save_state(self):
        sizes = []
        header = self.horizontalHeader()
        for i in range(header.count()):
            sizes.append(str(header.sectionSize(i)))
        config.persist["metadata_box_sizes"] = " ".join(sizes)

    def shrink_columns(self):
        header = self.horizontalHeader()
        cols = [header.sectionSize(i) for i in range(3)]
        width = sum(cols)
        visible_width = self.contentsRect().width()
        scroll = self.verticalScrollBar()
        if scroll.isVisible():
            visible_width -= scroll.width()
        if width > visible_width:
            diff = float(width - visible_width)
            for i in range(3):
                sub = int(diff * cols[i] / width) + 1
                header.resizeSection(i, cols[i] - sub)
