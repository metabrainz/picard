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
from picard.album import Album
from picard.cluster import Cluster
from picard.track import Track
from picard.file import File
from picard.config import TextOption
from picard.util.tags import display_tag_name
from picard.ui.ui_edittagdialog import Ui_EditTagDialog


class EditTagDialog(QtGui.QDialog):

    def __init__(self, parent, values):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_EditTagDialog()
        self.ui.setupUi(self)
        self.values = values
        self.list = self.ui.value_list
        for value in values[0]:
            item = QtGui.QListWidgetItem(value)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            self.list.addItem(item)
        self.list.setCurrentItem(self.list.item(0), QtGui.QItemSelectionModel.SelectCurrent)
        self.ui.add_value.clicked.connect(self.add_value)
        self.ui.remove_value.clicked.connect(self.remove_value)

    def add_value(self):
        item = QtGui.QListWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        self.list.addItem(item)
        self.list.editItem(item)

    def remove_value(self):
        vals = self.list
        vals.takeItem(vals.row(vals.currentItem()))

    def accept(self):
        values = []
        for i in xrange(self.list.count()):
            value = unicode(self.list.item(i).text())
            if value:
                values.append(value)
        self.values[0] = tuple(values)
        QtGui.QDialog.accept(self)


class TagCounter(dict):

    empty = [("",)]

    def __init__(self):
        self._counts = {}
        self._different = set()

    def add(self, tag, values):
        if tag not in self._different:
            vals = self.setdefault(tag, set())
            vals.add(tuple(sorted(values)))
            if len(vals) > 1:
                self._different.add(tag)
                self[tag] = self.empty
        self._counts[tag] = self._counts.get(tag, 0) + 1

    def different(self, tag):
        return tag in self._different

    def count(self, tag):
        return self._counts.get(tag, 0)

    def clear(self):
        dict.clear(self)
        self._counts.clear()
        self._different.clear()
        return self


class MetadataBox(QtGui.QTableWidget):

    options = (
        TextOption("persist", "metadata_box_sizes", "150 300 300")
    )

    common_tags = (
        "title",
        "artist",
        "album",
        "tracknumber",
        "~length",
        "date",
    )

    def __init__(self, parent):
        QtGui.QTableWidget.__init__(self, parent)
        self.parent = parent
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels((N_("Tag"), N_("Original value"), N_("New value")))
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setClickable(False)
        self.verticalHeader().setDefaultSectionSize(18)
        self.verticalHeader().setVisible(False)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setStyleSheet("border: none; font-size: 11px;")
        self.itemChanged.connect(self.item_changed)
        self._item_signals = True
        self.colors = {
            "default": self.palette().color(QtGui.QPalette.Text),
            "removed": QtGui.QBrush(QtGui.QColor("red")),
            "added": QtGui.QBrush(QtGui.QColor("green")),
            "changed": QtGui.QBrush(QtGui.QColor("darkgoldenrod")),
        }
        self.files = set()
        self.tracks = set()
        self.objects = set()
        self.orig_tags = TagCounter()
        self.new_tags = TagCounter()
        self.selection_mutex = QtCore.QMutex()
        self.updating = False
        self.update_pending = False
        self.selection_dirty = False

    def edit(self, index, trigger, event):
        if index.column() != 2:
            return False
        if trigger in (QtGui.QAbstractItemView.DoubleClicked,
                       QtGui.QAbstractItemView.EditKeyPressed,
                       QtGui.QAbstractItemView.AnyKeyPressed):
            item = self.itemFromIndex(index)
            tag = self.tag_names[item.row()]
            values = self.new_tags[tag]
            if len(values) == 1 and len(values[0]) > 1:
                dialog = EditTagDialog(self.parent, values)
                if dialog.exec_():
                    self.set_item_value(item, values)
                    self._item_signals = False
                    self.set_row_colors(item.row())
                    self._item_signals = True
                return False
            else:
                return QtGui.QTableWidget.edit(self, index, trigger, event)
        return False

    def update_selection(self):
        self.selection_mutex.lock()
        self.selection_dirty = True
        self.selection_mutex.unlock()

    def _update_selection(self):
        files = self.files
        tracks = self.tracks
        objects = self.objects
        files.clear()
        tracks.clear()
        objects.clear()
        for obj in self.parent.panel._selected_objects:
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

    def update(self):
        if not self.updating:
            self.updating = True
            self.update_pending = False
            self.tagger.other_queue.put((self._update_tags, self._update_items, QtCore.Qt.LowEventPriority))
        else:
            self.update_pending = True

    def _update_tags(self):
        self.selection_mutex.lock()
        if self.selection_dirty:
            self._update_selection()
        self.selection_mutex.unlock()

        files = self.files
        tracks = self.tracks
        if not (files or tracks):
            return None
        orig_tags = self.orig_tags.clear()
        new_tags = self.new_tags.clear()
        orig_total = 0

        for file in files:
            for name, values in file.orig_metadata._items.iteritems():
                if not name.startswith("~") or name == "~length":
                    orig_tags.add(name, values)
            for name, values in file.metadata._items.iteritems():
                if not name.startswith("~") or name == "~length":
                    new_tags.add(name, values)
            orig_total += 1

        new_total = orig_total
        for track in tracks:
            if track.num_linked_files == 0:
                for name, values in track.metadata._items.iteritems():
                    if not name.startswith("~") or name == "~length":
                        new_tags.add(name, values)
                new_total += 1

        common_tags = MetadataBox.common_tags
        all_tags = set(orig_tags.keys() + new_tags.keys())
        self.tag_names = [t for t in common_tags if t in all_tags] + sorted(all_tags.difference(common_tags))
        return (orig_total, new_total)

    def _update_items(self, result=None, error=None):
        if result is None or error is not None:
            self.orig_tags.clear()
            self.new_tags.clear()
            self.tag_names = None
            self.setRowCount(0)
            self.updating = False
            if self.update_pending:
                self.update()
            return

        self._item_signals = False
        orig_total, new_total = result
        orig_tags = self.orig_tags
        new_tags = self.new_tags
        tag_names = self.tag_names
        self.setRowCount(len(tag_names))
        set_item_value = self.set_item_value

        for i, name in enumerate(tag_names):
            tag_item = self.item(i, 0)
            if not tag_item:
                tag_item = QtGui.QTableWidgetItem()
                tag_item.setFlags(QtCore.Qt.ItemIsEnabled)
                font = tag_item.font()
                font.setBold(True)
                tag_item.setFont(font)
                self.setItem(i, 0, tag_item)
            tag_item.setText(display_tag_name(name))

            orig_values = orig_tags[name] = list(orig_tags.get(name, TagCounter.empty))
            new_values = new_tags[name] = list(new_tags.get(name, TagCounter.empty))

            orig_item = self.item(i, 1)
            if not orig_item:
                orig_item = QtGui.QTableWidgetItem()
                orig_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.setItem(i, 1, orig_item)
            set_item_value(orig_item, orig_values, orig_tags.different(name), orig_tags.count(name), orig_total)

            new_item = self.item(i, 2)
            if not new_item:
                new_item = QtGui.QTableWidgetItem()
                self.setItem(i, 2, new_item)
            if name == "~length":
                new_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            set_item_value(new_item, new_values, new_tags.different(name), new_tags.count(name), new_total)
            self.set_row_colors(i)

        self._item_signals = True
        self.updating = False
        if self.update_pending:
            self.update()

    def set_item_value(self, item, values, different=False, count=0, total=0):
        font = item.font()
        missing = total - count
        if different or (count > 0 and missing > 0):
            if missing > 0:
                item.setText(ungettext("(missing from %d item)", "(missing from %d items)", missing) % missing)
            else:
                item.setText(_("(different across %d items)") % total)
            font.setItalic(True)
        else:
            value = values[0]
            if len(value) > 1:
                item.setText("; ".join(value))
            else:
                item.setText(value[0])
            font.setItalic(False)
        item.setFont(font)

    def set_row_colors(self, row):
        orig_item = self.item(row, 1)
        new_item = self.item(row, 2)
        tag = self.tag_names[row]
        orig_values = self.orig_tags[tag]
        new_values = self.new_tags[tag]
        orig_blank = orig_values == TagCounter.empty and not self.orig_tags.different(tag)
        new_blank = new_values == TagCounter.empty and not self.new_tags.different(tag)
        if new_blank and not orig_blank:
            orig_item.setForeground(self.colors["removed"])
        elif orig_blank and not new_blank:
            new_item.setForeground(self.colors["added"])
        elif not (orig_blank or new_blank) and orig_values != new_values:
            orig_item.setForeground(self.colors["changed"])
            new_item.setForeground(self.colors["changed"])
        else:
            orig_item.setForeground(self.colors["default"])
            new_item.setForeground(self.colors["default"])

    def item_changed(self, item):
        if not self._item_signals:
            return
        self._item_signals = False
        self.tagger.selected_metadata_changed.disconnect(self.parent.update_selection)
        tag = self.tag_names[item.row()]
        values = self.new_tags[tag]
        if len(values) == 1 and len(values[0]) > 1:
            # The tag editor dialog already updated self.new_tags
            value = list(values[0])
        else:
            value = unicode(item.text())
            new_values = self.new_tags[tag] = [(value,)]
            font = item.font()
            font.setItalic(False)
            item.setFont(font)
            self.set_row_colors(item.row())
        for obj in self.objects:
            obj.metadata[tag] = value
            obj.update()
        self.tagger.selected_metadata_changed.connect(self.parent.update_selection)
        self._item_signals = True

    def restore_state(self):
        sizes = self.config.persist["metadata_box_sizes"].split(" ")
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
        self.config.persist["metadata_box_sizes"] = " ".join(sizes)

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
