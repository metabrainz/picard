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

from PyQt5 import QtCore, QtGui, QtWidgets
from collections import defaultdict
from functools import partial
from picard import config
from picard.album import Album
from picard.cluster import Cluster
from picard.track import Track
from picard.file import File
from picard.util import format_time, throttle, thread, uniqify, restore_method
from picard.util.tags import display_tag_name
from picard.ui.edittagdialog import EditTagDialog
from picard.metadata import MULTI_VALUED_JOINER
from picard.browser.filelookup import FileLookup
from picard.browser.browser import BrowserIntegration


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
        return super().get(tag, [""])

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
            return (ngettext("(different across %d item)", "(different across %d items)", count) % count, True)
        else:
            if tag == "~length":
                msg = format_time(self.get(tag, 0))
            else:
                msg = MULTI_VALUED_JOINER.join(self[tag])

            if count > 0 and missing > 0:
                return (msg + " " + (ngettext("(missing from %d item)", "(missing from %d items)", missing) % missing), True)
            else:
                return (msg, False)


class TagDiff(object):

    __slots__ = ("tag_names", "new", "orig", "status", "objects", "max_length_delta_ms")

    def __init__(self, max_length_diff=2):
        self.tag_names = []
        self.new = TagCounter(self)
        self.orig = TagCounter(self)
        self.status = defaultdict(lambda: 0)
        self.objects = 0
        self.max_length_delta_ms = max_length_diff * 1000

    def __tag_ne(self, tag, orig, new):
        if tag == "~length":
            return abs(float(orig) - float(new)) > self.max_length_delta_ms
        else:
            return orig != new

    def add(self, tag, orig_values, new_values, removable, removed=False):
        if orig_values:
            self.orig.add(tag, orig_values)

        if new_values:
            self.new.add(tag, new_values)

        if (orig_values and not new_values) or removed:
            self.status[tag] |= TagStatus.Removed
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


class PreservedTags:

    opt_name = 'preserved_tags'

    def __init__(self):
        self._tags = self._from_config()

    def _to_config(self):
        config.setting[self.opt_name] =  ", ".join(sorted(self._tags))

    def _from_config(self):
        tags = config.setting[self.opt_name].split(',')
        return set(filter(bool, map(str.strip, tags)))

    def add(self, name):
        self._tags.add(name)
        self._to_config()

    def discard(self, name):
        self._tags.discard(name)
        self._to_config()

    def __contains__(self, key):
        return key in self._tags


class MetadataBox(QtWidgets.QTableWidget):

    options = (
        config.Option("persist", "metadatabox_header_state", QtCore.QByteArray()),
        config.BoolOption("persist", "show_changes_first", False)
    )

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setAccessibleName(_("metadata view"))
        self.setAccessibleDescription(_("Displays original and new tags for the selected files"))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels((_("Tag"), _("Original Value"), _("New Value")))
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionsClickable(False)
        self.verticalHeader().setDefaultSectionSize(21)
        self.verticalHeader().setVisible(False)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
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
        self.editing = None  # the QTableWidgetItem being edited
        self.clipboard = [""]
        self.add_tag_action = QtWidgets.QAction(_("Add New Tag..."), parent)
        self.add_tag_action.triggered.connect(partial(self.edit_tag, ""))
        self.changes_first_action = QtWidgets.QAction(_("Show Changes First"), parent)
        self.changes_first_action.setCheckable(True)
        self.changes_first_action.setChecked(config.persist["show_changes_first"])
        self.changes_first_action.toggled.connect(self.toggle_changes_first)
        self.browser_integration = BrowserIntegration()
        # TR: Keyboard shortcut for "Add New Tag..."
        self.add_tag_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(_("Alt+Shift+A")), self, partial(self.edit_tag, ""))
        self.add_tag_action.setShortcut(self.add_tag_shortcut.key())
        # TR: Keyboard shortcut for "Edit..." (tag)
        self.edit_tag_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(_("Alt+Shift+E")), self, partial(self.edit_selected_tag))
        # TR: Keyboard shortcut for "Remove" (tag)
        self.remove_tag_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(_("Alt+Shift+R")), self, self.remove_selected_tags)
        self.preserved_tags = PreservedTags()

    def get_file_lookup(self):
        """Return a FileLookup object."""
        return FileLookup(self, config.setting["server_host"],
                          config.setting["server_port"],
                          self.browser_integration.port)

    def lookup_tags(self):
        lookup = self.get_file_lookup()
        LOOKUP_TAGS = {
            "musicbrainz_recordingid": lookup.recording_lookup,
            "musicbrainz_trackid": lookup.track_lookup,
            "musicbrainz_albumid": lookup.album_lookup,
            "musicbrainz_workid": lookup.work_lookup,
            "musicbrainz_artistid": lookup.artist_lookup,
            "musicbrainz_albumartistid": lookup.artist_lookup,
            "musicbrainz_releasegroupid": lookup.release_group_lookup,
            "acoustid_id": lookup.acoust_lookup
        }
        return LOOKUP_TAGS

    def open_link(self, values, tag):
        lookup = self.lookup_tags()
        lookup_func = lookup[tag]
        for v in values:
            lookup_func(v)

    def edit(self, index, trigger, event):
        if index.column() != 2:
            return False
        item = self.itemFromIndex(index)
        if item.flags() & QtCore.Qt.ItemIsEditable and \
           trigger in (QtWidgets.QAbstractItemView.DoubleClicked,
                       QtWidgets.QAbstractItemView.EditKeyPressed,
                       QtWidgets.QAbstractItemView.AnyKeyPressed):
            tag = self.tag_diff.tag_names[item.row()]
            values = self.tag_diff.new[tag]
            if len(values) > 1:
                self.edit_tag(tag)
                return False
            else:
                self.editing = item
                item.setText(values[0])
                return super().edit(index, trigger, event)
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
        return super().event(e)

    def closeEditor(self, editor, hint):
        super().closeEditor(editor, hint)
        tag = self.tag_diff.tag_names[self.editing.row()]
        old = self.tag_diff.new[tag]
        new = [editor.text()]
        if old == new:
            self.editing.setText(old[0])
        else:
            self.set_tag_values(tag, new)
        self.editing = None
        self.update()

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        if self.objects:
            tags = self.selected_tags(discard=('~length',))
            if len(tags) == 1:
                selected_tag = tags[0]
                edit_tag_action = QtWidgets.QAction(_("Edit..."), self.parent)
                edit_tag_action.triggered.connect(partial(self.edit_tag, selected_tag))
                edit_tag_action.setShortcut(self.edit_tag_shortcut.key())
                menu.addAction(edit_tag_action)
                if selected_tag not in self.preserved_tags:
                    add_to_preserved_tags_action = QtWidgets.QAction(_("Add to 'Preserve Tags' List"), self.parent)
                    add_to_preserved_tags_action.triggered.connect(partial(self.preserved_tags.add, selected_tag))
                    menu.addAction(add_to_preserved_tags_action)
                else:
                    remove_from_preserved_tags_action = QtWidgets.QAction(_("Remove from 'Preserve Tags' List"), self.parent)
                    remove_from_preserved_tags_action.triggered.connect(partial(self.preserved_tags.discard, selected_tag))
                    menu.addAction(remove_from_preserved_tags_action)
            removals = []
            useorigs = []
            item = self.currentItem()
            if item:
                column = item.column()
                for tag in tags:
                    if tag in self.lookup_tags().keys():
                        if (column == 1 or column == 2) and len(tags) == 1 and item.text():
                            if column == 1:
                                values = self.tag_diff.orig[tag]
                            else:
                                values = self.tag_diff.new[tag]
                            lookup_action = QtWidgets.QAction(_("Lookup in &Browser"), self.parent)
                            lookup_action.triggered.connect(partial(self.open_link, values, tag))
                            menu.addAction(lookup_action)
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
                    remove_tag_action = QtWidgets.QAction(_("Remove"), self.parent)
                    remove_tag_action.triggered.connect(lambda: [f() for f in removals])
                    remove_tag_action.setShortcut(self.remove_tag_shortcut.key())
                    menu.addAction(remove_tag_action)
                if useorigs:
                    name = ngettext("Use Original Value", "Use Original Values", len(useorigs))
                    use_orig_value_action = QtWidgets.QAction(name, self.parent)
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

    def edit_selected_tag(self):
        tags = self.selected_tags(discard=('~length',))
        if len(tags) == 1:
            self.edit_tag(tags[0])

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
        for tag in self.selected_tags(discard=('~length',)):
            if self.tag_is_removable(tag):
                self.remove_tag(tag)

    def tag_is_removable(self, tag):
        return self.tag_diff.status[tag] & TagStatus.NotRemovable == 0

    def selected_tags(self, discard=None):
        if discard is None:
            discard = set()
        tags = set(self.tag_diff.tag_names[item.row()]
                   for item in self.selectedItems())
        return list(tags.difference(discard))

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
        thread.run_task(self._update_tags, self._update_items)

    def _update_tags(self):
        self.selection_mutex.lock()
        files = self.files
        tracks = self.tracks
        self.selection_mutex.unlock()

        if not (files or tracks):
            return None

        tag_diff = TagDiff(max_length_diff=config.setting["ignore_track_duration_difference_under"])
        orig_tags = tag_diff.orig
        new_tags = tag_diff.new
        # existing_tags are orig_tags that would not be overwritten by
        # any new_tags, assuming clear_existing_tags is disabled.
        existing_tags = set()
        tag_diff.objects = len(files)

        clear_existing_tags = config.setting["clear_existing_tags"]

        for file in files:
            new_metadata = file.new_metadata
            orig_metadata = file.orig_metadata
            tags = set(list(new_metadata.keys()) + list(orig_metadata.keys()))

            for name in filter(lambda x: not x.startswith("~") and file.supports_tag(x), tags):
                new_values = new_metadata.getall(name)
                orig_values = orig_metadata.getall(name)

                if not ((new_values and name not in existing_tags) or clear_existing_tags):
                    new_values = list(orig_values or [""])
                    existing_tags.add(name)

                removed = name in new_metadata.deleted_tags
                tag_diff.add(name, orig_values, new_values, True, removed)

            tag_diff.add("~length",
                         string_(orig_metadata.length), string_(new_metadata.length), False)

        for track in tracks:
            if track.num_linked_files == 0:
                for name, values in track.metadata.rawitems():
                    if not name.startswith("~"):
                        tag_diff.add(name, values, values, True)

                length = string_(track.metadata.length)
                tag_diff.add("~length", length, length, False)

                tag_diff.objects += 1

        all_tags = set(list(orig_tags.keys()) + list(new_tags.keys()))
        tag_names = COMMON_TAGS + \
                    sorted(all_tags.difference(COMMON_TAGS),
                           key=lambda x: display_tag_name(x).lower())

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
            tag_item = self.item(i, 0)
            orig_item = self.item(i, 1)
            new_item = self.item(i, 2)
            if not tag_item:
                tag_item = QtWidgets.QTableWidgetItem()
                tag_item.setFlags(orig_flags)
                font = tag_item.font()
                font.setBold(True)
                tag_item.setFont(font)
                self.setItem(i, 0, tag_item)
            if not orig_item:
                orig_item = QtWidgets.QTableWidgetItem()
                orig_item.setFlags(orig_flags)
                self.setItem(i, 1, orig_item)
            if not new_item:
                new_item = QtWidgets.QTableWidgetItem()
                self.setItem(i, 2, new_item)
            tag_item.setText(display_tag_name(name))
            self.set_item_value(orig_item, self.tag_diff.orig, name)
            if name == "~length":
                new_item.setFlags(orig_flags)
            else:
                new_item.setFlags(new_flags)
            self.set_item_value(new_item, self.tag_diff.new, name)

            font = new_item.font()
            if result.tag_status(name) == TagStatus.Removed:
                font.setStrikeOut(True)
            else:
                font.setStrikeOut(False)

            new_item.setFont(font)

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

    @restore_method
    def restore_state(self):
        state = config.persist["metadatabox_header_state"]
        header = self.horizontalHeader()
        header.restoreState(state)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

    def save_state(self):
        header = self.horizontalHeader()
        state = header.saveState()
        config.persist["metadatabox_header_state"] = state
