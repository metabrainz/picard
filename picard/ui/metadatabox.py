# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007, 2012 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Nikolai Prokoschenko
# Copyright (C) 2013-2014, 2021 Sophist-UK
# Copyright (C) 2013-2014, 2017-2019 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 Wieland Hoffmann
# Copyright (C) 2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 Gabriel Ferreira
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


from collections import defaultdict
from functools import partial

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.album import Album
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster
from picard.config import (
    BoolOption,
    Option,
    get_config,
)
from picard.file import File
from picard.metadata import MULTI_VALUED_JOINER
from picard.track import Track
from picard.util import (
    format_time,
    icontheme,
    restore_method,
    thread,
    throttle,
)
from picard.util.preservedtags import PreservedTags
from picard.util.tags import display_tag_name

from picard.ui.colors import interface_colors
from picard.ui.edittagdialog import (
    EditTagDialog,
    TagEditorDelegate,
)


class TagStatus:

    NOCHANGE = 1
    ADDED = 2
    REMOVED = 4
    CHANGED = ADDED | REMOVED
    EMPTY = 8
    NOTREMOVABLE = 16
    READONLY = 32


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

    def add(self, tag, orig_values, new_values, removable, removed=False, readonly=False, top_tags=None):
        if orig_values:
            self.orig.add(tag, orig_values)

        if new_values:
            self.new.add(tag, new_values)

        if not top_tags:
            top_tags = set()

        if (orig_values and not new_values) or removed:
            self.status[tag] |= TagStatus.REMOVED
        elif new_values and not orig_values:
            self.status[tag] |= TagStatus.ADDED
            removable = True
        elif orig_values and new_values and self.__tag_ne(tag, orig_values, new_values):
            self.status[tag] |= TagStatus.CHANGED
        elif not (orig_values or new_values or tag in top_tags):
            self.status[tag] |= TagStatus.EMPTY
        else:
            self.status[tag] |= TagStatus.NOCHANGE

        if not removable:
            self.status[tag] |= TagStatus.NOTREMOVABLE

        if readonly:
            self.status[tag] |= TagStatus.READONLY

    def tag_status(self, tag):
        status = self.status[tag]
        for s in (TagStatus.CHANGED, TagStatus.ADDED,
                  TagStatus.REMOVED, TagStatus.EMPTY):
            if status & s == s:
                return s
        return TagStatus.NOCHANGE


class TableTagEditorDelegate(TagEditorDelegate):

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if editor and isinstance(editor, QtWidgets.QPlainTextEdit):
            table = self.parent()
            # Set the editor to the row height, but at least 80 pixel
            # to allow for proper multiline editing.
            height = max(80, table.rowHeight(index.row()) - 1)
            editor.setMinimumSize(QtCore.QSize(0, height))
            # Resize the row so the editor fits in. Add 1 pixel, otherwise the
            # frame gets hidden.
            table.setRowHeight(index.row(), editor.frameSize().height() + 1)
        return editor

    def sizeHint(self, option, index):
        # Expand the row for multiline content, but limit the maximum row height.
        size_hint = super().sizeHint(option, index)
        return QtCore.QSize(size_hint.width(), min(160, size_hint.height()))

    def get_tag_name(self, index):
        return index.data(QtCore.Qt.UserRole)


class MetadataBox(QtWidgets.QTableWidget):

    options = (
        Option("persist", "metadatabox_header_state", QtCore.QByteArray()),
        BoolOption("persist", "show_changes_first", False)
    )

    COLUMN_ORIG = 1
    COLUMN_NEW = 2

    def __init__(self, parent):
        super().__init__(parent)
        config = get_config()
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
        self.setItemDelegate(TableTagEditorDelegate(self))
        self.setWordWrap(False)
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
        # TR: Keyboard shortcut for "Add New Tag..."
        self.add_tag_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(_("Alt+Shift+A")), self, partial(self.edit_tag, ""))
        self.add_tag_action.setShortcut(self.add_tag_shortcut.key())
        # TR: Keyboard shortcut for "Edit..." (tag)
        self.edit_tag_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(_("Alt+Shift+E")), self, partial(self.edit_selected_tag))
        # TR: Keyboard shortcut for "Remove" (tag)
        self.remove_tag_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(_("Alt+Shift+R")), self, self.remove_selected_tags)
        self.preserved_tags = PreservedTags()
        self._single_file_album = False
        self._single_track_album = False
        self.tagger.clipboard().dataChanged.connect(self.update_clipboard)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        config = get_config()
        return FileLookup(self, config.setting["server_host"],
                          config.setting["server_port"],
                          self.tagger.browser_integration.port)

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
            "musicbrainz_discid": lookup.discid_lookup,
            "acoustid_id": lookup.acoust_lookup
        }
        return LOOKUP_TAGS

    def open_link(self, values, tag):
        lookup = self.lookup_tags()
        lookup_func = lookup[tag]
        for v in values:
            lookup_func(v)

    def edit(self, index, trigger, event):
        if index.column() != self.COLUMN_NEW:
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

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy_value()
        elif event.matches(QtGui.QKeySequence.Paste):
            self.paste_value()
        else:
            super().keyPressEvent(event)

    def copy_value(self):
        item = self.currentItem()
        if item:
            column = item.column()
            tag = self.tag_diff.tag_names[item.row()]
            value = None
            if column == self.COLUMN_ORIG:
                value = self.tag_diff.orig[tag]
            elif column == self.COLUMN_NEW:
                value = self.tag_diff.new[tag]
            if tag == '~length':
                value = [format_time(value or 0), ]
            if value is not None:
                self.tagger.clipboard().setText(MULTI_VALUED_JOINER.join(value))
                self.clipboard = value

    def paste_value(self):
        item = self.currentItem()
        if item:
            column = item.column()
            tag = self.tag_diff.tag_names[item.row()]
            if column == self.COLUMN_NEW and self.tag_is_editable(tag):
                self.set_tag_values(tag, self.clipboard)
                self.update()

    def update_clipboard(self):
        clipboard = self.tagger.clipboard().text().split(MULTI_VALUED_JOINER)
        if clipboard:
            self.clipboard = clipboard

    def closeEditor(self, editor, hint):
        super().closeEditor(editor, hint)
        tag = self.tag_diff.tag_names[self.editing.row()]
        old = self.tag_diff.new[tag]
        new = [self._get_editor_value(editor)]
        if old == new:
            self.editing.setText(old[0])
        else:
            self.set_tag_values(tag, new)
        self.editing = None
        self.update(drop_album_caches=tag == 'album')

    @staticmethod
    def _get_editor_value(editor):
        if hasattr(editor, 'text'):
            return editor.text()
        elif hasattr(editor, 'toPlainText'):
            return editor.toPlainText()
        return ''

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        if self.objects:
            tags = self.selected_tags()
            single_tag = len(tags) == 1
            if single_tag:
                selected_tag = tags[0]
                editable = self.tag_is_editable(selected_tag)
                edit_tag_action = QtWidgets.QAction(_("Edit..."), self.parent)
                edit_tag_action.triggered.connect(partial(self.edit_tag, selected_tag))
                edit_tag_action.setShortcut(self.edit_tag_shortcut.key())
                edit_tag_action.setEnabled(editable)
                menu.addAction(edit_tag_action)
                if selected_tag not in self.preserved_tags:
                    add_to_preserved_tags_action = QtWidgets.QAction(_("Add to 'Preserve Tags' List"), self.parent)
                    add_to_preserved_tags_action.triggered.connect(partial(self.preserved_tags.add, selected_tag))
                    add_to_preserved_tags_action.setEnabled(editable)
                    menu.addAction(add_to_preserved_tags_action)
                else:
                    remove_from_preserved_tags_action = QtWidgets.QAction(_("Remove from 'Preserve Tags' List"), self.parent)
                    remove_from_preserved_tags_action.triggered.connect(partial(self.preserved_tags.discard, selected_tag))
                    remove_from_preserved_tags_action.setEnabled(editable)
                    menu.addAction(remove_from_preserved_tags_action)
            removals = []
            useorigs = []
            item = self.currentItem()
            if item:
                column = item.column()
                for tag in tags:
                    if tag in self.lookup_tags().keys():
                        if (column == self.COLUMN_ORIG or column == self.COLUMN_NEW) and single_tag and item.text():
                            if column == self.COLUMN_ORIG:
                                values = self.tag_diff.orig[tag]
                            else:
                                values = self.tag_diff.new[tag]
                            lookup_action = QtWidgets.QAction(_("Lookup in &Browser"), self.parent)
                            lookup_action.triggered.connect(partial(self.open_link, values, tag))
                            menu.addAction(lookup_action)
                    if self.tag_is_removable(tag):
                        removals.append(partial(self.remove_tag, tag))
                    status = self.tag_diff.status[tag] & TagStatus.CHANGED
                    if status == TagStatus.CHANGED or status == TagStatus.REMOVED:
                        file_tracks = []
                        track_albums = set()
                        for file in self.files:
                            objects = [file]
                            if file.parent in self.tracks and len(self.files & set(file.parent.files)) == 1:
                                objects.append(file.parent)
                                file_tracks.append(file.parent)
                                track_albums.add(file.parent.album)
                            orig_values = list(file.orig_metadata.getall(tag)) or [""]
                            useorigs.append(partial(self.set_tag_values, tag, orig_values, objects))
                        for track in set(self.tracks)-set(file_tracks):
                            objects = [track]
                            orig_values = list(track.orig_metadata.getall(tag)) or [""]
                            useorigs.append(partial(self.set_tag_values, tag, orig_values, objects))
                            track_albums.add(track.album)
                        for album in track_albums:
                            objects = [album]
                            orig_values = list(album.orig_metadata.getall(tag)) or [""]
                            useorigs.append(partial(self.set_tag_values, tag, orig_values, objects))
                remove_tag_action = QtWidgets.QAction(_("Remove"), self.parent)
                remove_tag_action.triggered.connect(partial(self._apply_update_funcs, removals))
                remove_tag_action.setShortcut(self.remove_tag_shortcut.key())
                remove_tag_action.setEnabled(bool(removals))
                menu.addAction(remove_tag_action)
                if useorigs:
                    name = ngettext("Use Original Value", "Use Original Values", len(useorigs))
                    use_orig_value_action = QtWidgets.QAction(name, self.parent)
                    use_orig_value_action.triggered.connect(partial(self._apply_update_funcs, useorigs))
                    menu.addAction(use_orig_value_action)
                    menu.addSeparator()
                if single_tag:
                    menu.addSeparator()
                    copy_action = QtWidgets.QAction(icontheme.lookup('edit-copy', icontheme.ICON_SIZE_MENU), _("&Copy"), self)
                    copy_action.triggered.connect(self.copy_value)
                    copy_action.setShortcut(QtGui.QKeySequence.Copy)
                    menu.addAction(copy_action)
                    paste_action = QtWidgets.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _("&Paste"), self)
                    paste_action.triggered.connect(self.paste_value)
                    paste_action.setShortcut(QtGui.QKeySequence.Paste)
                    paste_action.setEnabled(editable)
                    menu.addAction(paste_action)
            if single_tag or removals or useorigs:
                menu.addSeparator()
            menu.addAction(self.add_tag_action)
            menu.addSeparator()
        menu.addAction(self.changes_first_action)
        menu.exec_(event.globalPos())
        event.accept()

    def _apply_update_funcs(self, funcs):
        with self.parent.ignore_selection_changes:
            for f in funcs:
                f()
        self.parent.update_selection(new_selection=False, drop_album_caches=True)

    def edit_tag(self, tag):
        EditTagDialog(self.parent, tag).exec_()

    def edit_selected_tag(self):
        tags = self.selected_tags(filter_func=self.tag_is_editable)
        if len(tags) == 1:
            self.edit_tag(tags[0])

    def toggle_changes_first(self, checked):
        config = get_config()
        config.persist["show_changes_first"] = checked
        self.update()

    def set_tag_values(self, tag, values, objects=None):
        if objects is None:
            objects = self.objects
        with self.parent.ignore_selection_changes:
            if values == [""]:
                values = []
            if not values and self.tag_is_removable(tag):
                for obj in objects:
                    del obj.metadata[tag]
                    obj.update()
            elif values:
                for obj in objects:
                    obj.metadata[tag] = values
                    obj.update()

    def remove_tag(self, tag):
        self.set_tag_values(tag, [])

    def remove_selected_tags(self):
        for tag in self.selected_tags(filter_func=self.tag_is_removable):
            if self.tag_is_removable(tag):
                self.remove_tag(tag)
        self.parent.update_selection(new_selection=False, drop_album_caches=True)

    def tag_is_removable(self, tag):
        return self.tag_diff.status[tag] & TagStatus.NOTREMOVABLE == 0

    def tag_is_editable(self, tag):
        return self.tag_diff.status[tag] & TagStatus.READONLY == 0

    def selected_tags(self, filter_func=None):
        tags = set(self.tag_diff.tag_names[item.row()]
                   for item in self.selectedItems())
        if filter_func:
            tags = filter(filter_func, tags)
        return list(tags)

    def _update_selection(self):
        files = set()
        tracks = set()
        objects = set()
        for obj in self.parent.selected_objects:
            if isinstance(obj, File):
                files.add(obj)
            elif isinstance(obj, Track):
                tracks.add(obj)
                files.update(obj.files)
            elif isinstance(obj, Cluster) and obj.can_edit_tags():
                objects.add(obj)
                files.update(obj.files)
            elif isinstance(obj, Album):
                objects.add(obj)
                tracks.update(obj.tracks)
                for track in obj.tracks:
                    files.update(track.files)
        objects.update(files)
        objects.update(tracks)
        self.selection_dirty = False

        self.selection_mutex.lock()
        self.files = files
        self.tracks = tracks
        self.objects = objects
        self.selection_mutex.unlock()

    @throttle(100)
    def update(self, drop_album_caches=False):
        if self.editing:
            return
        new_selection = self.selection_dirty
        if self.selection_dirty:
            self._update_selection()
        thread.run_task(partial(self._update_tags, new_selection, drop_album_caches), self._update_items,
            thread_pool=self.tagger.priority_thread_pool)

    def _update_tags(self, new_selection=True, drop_album_caches=False):
        self.selection_mutex.lock()
        files = self.files
        tracks = self.tracks
        self.selection_mutex.unlock()

        if not (files or tracks):
            return None

        if new_selection or drop_album_caches:
            self._single_file_album = len(set([file.metadata["album"] for file in files])) == 1
            self._single_track_album = len(set([track.metadata["album"] for track in tracks])) == 1

        while not new_selection:  # Just an if with multiple exit points
            # If we are dealing with the same selection
            # skip updates unless it we are dealing with a single file/track
            if len(files) == 1:
                break
            if len(tracks) == 1:
                break
            # Or if we are dealing with a single cluster/album
            if self._single_file_album:
                break
            if self._single_track_album:
                break
            return self.tag_diff

        self.colors = {
            TagStatus.NOCHANGE: self.palette().color(QtGui.QPalette.Text),
            TagStatus.REMOVED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_removed')),
            TagStatus.ADDED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_added')),
            TagStatus.CHANGED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_changed'))
        }

        config = get_config()
        tag_diff = TagDiff(max_length_diff=config.setting["ignore_track_duration_difference_under"])
        orig_tags = tag_diff.orig
        new_tags = tag_diff.new
        tag_diff.objects = len(files)

        clear_existing_tags = config.setting["clear_existing_tags"]
        top_tags = config.setting['metadatabox_top_tags']
        top_tags_set = set(top_tags)

        settings = config.setting.as_dict()

        for file in files:
            new_metadata = file.metadata
            orig_metadata = file.orig_metadata
            tags = set(list(new_metadata.keys()) + list(orig_metadata.keys()))

            for name in filter(lambda x: not x.startswith("~") and file.supports_tag(x), tags):
                new_values = file.format_specific_metadata(new_metadata, name, settings)
                orig_values = file.format_specific_metadata(orig_metadata, name, settings)

                if not clear_existing_tags and not new_values:
                    new_values = list(orig_values or [""])

                removed = name in new_metadata.deleted_tags
                tag_diff.add(name, orig_values, new_values, True, removed, top_tags=top_tags_set)

            tag_diff.add("~length", str(orig_metadata.length), str(new_metadata.length),
                         removable=False, readonly=True)

        for track in tracks:
            if track.num_linked_files == 0:
                for name, new_values in track.metadata.rawitems():
                    if not name.startswith("~"):
                        if name in track.orig_metadata:
                            orig_values = track.orig_metadata.getall(name)
                        else:
                            orig_values = new_values
                        tag_diff.add(name, orig_values, new_values, True)

                length = str(track.metadata.length)
                tag_diff.add("~length", length, length, removable=False, readonly=True)

                tag_diff.objects += 1

        all_tags = set(list(orig_tags.keys()) + list(new_tags.keys()))
        common_tags = [tag for tag in top_tags if tag in all_tags]
        tag_names = common_tags + sorted(all_tags.difference(common_tags),
                                         key=lambda x: display_tag_name(x).lower())

        if config.persist["show_changes_first"]:
            tags_by_status = {}

            for tag in tag_names:
                tags_by_status.setdefault(tag_diff.tag_status(tag), []).append(tag)

            for status in (TagStatus.CHANGED, TagStatus.ADDED,
                           TagStatus.REMOVED, TagStatus.NOCHANGE):
                tag_diff.tag_names += tags_by_status.pop(status, [])
        else:
            tag_diff.tag_names = [
                tag for tag in tag_names if
                tag_diff.status[tag] != TagStatus.EMPTY]

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
            if result.tag_status(name) == TagStatus.REMOVED:
                font.setStrikeOut(True)
            else:
                font.setStrikeOut(False)

            new_item.setFont(font)

            color = self.colors.get(result.tag_status(name),
                                    self.colors[TagStatus.NOCHANGE])
            orig_item.setForeground(color)
            new_item.setForeground(color)

            alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
            tag_item.setTextAlignment(alignment)
            orig_item.setTextAlignment(alignment)
            new_item.setTextAlignment(alignment)

            # Adjust row height to content size
            self.setRowHeight(i, self.sizeHintForRow(i))

    def set_item_value(self, item, tags, name):
        text, italic = tags.display_value(name)
        item.setData(QtCore.Qt.UserRole, name)
        item.setText(text)
        font = item.font()
        font.setItalic(italic)
        item.setFont(font)

    @restore_method
    def restore_state(self):
        config = get_config()
        state = config.persist["metadatabox_header_state"]
        header = self.horizontalHeader()
        header.restoreState(state)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

    def save_state(self):
        config = get_config()
        header = self.horizontalHeader()
        state = header.saveState()
        config.persist["metadatabox_header_state"] = state
