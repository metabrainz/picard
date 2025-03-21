# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007, 2012 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Nikolai Prokoschenko
# Copyright (C) 2013-2014, 2017-2024 Laurent Monin
# Copyright (C) 2013-2014, 2021 Sophist-UK
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 Wieland Hoffmann
# Copyright (C) 2015, 2018-2025 Philipp Wolfer
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 Felix Schwarz
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2024 Arnab Chakraborty
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


from functools import partial

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.album import Album
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster
from picard.config import get_config
from picard.file import File
from picard.i18n import (
    gettext as _,
    ngettext,
)
from picard.metadata import MULTI_VALUED_JOINER
from picard.track import Track
from picard.util import (
    IgnoreUpdatesContext,
    format_time,
    icontheme,
    restore_method,
    thread,
    throttle,
)
from picard.util.preservedtags import PreservedTags
from picard.util.tags import display_tag_name

from .edittagdialog import (
    EditTagDialog,
    TagEditorDelegate,
)
from .tagdiff import (
    TagDiff,
    TagStatus,
)

from picard.ui.colors import interface_colors


class TableTagEditorDelegate(TagEditorDelegate):
    """
    A delegate for editing tags in a table, providing multiline editing support.

    This delegate extends TagEditorDelegate to allow for multiline
    editing of tag values within metadata box QTableWidget.
    It ensures that the editor is sized appropriately for multiline content
    and that the row height is adjusted to fit the editor.
    """

    MIN_EDITOR_HEIGHT = 80  # The minimum height for the editor widget
    MAX_ROW_HEIGHT = 160  # The maximum height for a row

    def createEditor(self, parent, option, index):
        """
        Creates the editor widget for the given index.
        If it's an instance of QtWidgets.QPlainTextEdit set editor and row heights.

        Args:
            parent: The parent widget of the editor.
            option: The style option for the editor.
            index: The model index for the item being edited.
        Returns:
            The editor widget.
        """
        editor = super().createEditor(parent, option, index)
        if editor and isinstance(editor, QtWidgets.QPlainTextEdit):
            table = self.parent()
            # Set the editor to the row height, but at least MIN_EDITOR_HEIGHT pixels
            # to allow for proper multiline editing.
            height = max(self.MIN_EDITOR_HEIGHT, table.rowHeight(index.row()) - 1)
            editor.setMinimumSize(QtCore.QSize(0, height))
            # Resize the row so the editor fits in. Add 1 pixel, otherwise the
            # frame gets hidden.
            table.setRowHeight(index.row(), editor.frameSize().height() + 1)
        return editor

    def sizeHint(self, option, index):
        """
        Returns the size hint for the item at the given index.

        This method expands the row height to accommodate multiline content,
        but limits the maximum row height to MAX_ROW_HEIGHT pixels.

        Args:
            option: The style option for the item.
            index: The model index for the item.

        Returns:
            The size hint (QSize) for the item.
        """
        size_hint = super().sizeHint(option, index)
        height = min(self.MAX_ROW_HEIGHT, size_hint.height())
        return QtCore.QSize(size_hint.width(), height)

    def get_tag_name(self, index):
        """Retrieves the tag name associated with the given index."""
        return index.data(QtCore.Qt.ItemDataRole.UserRole)


class MetadataBox(QtWidgets.QTableWidget):

    COLUMN_TAG = 0
    COLUMN_ORIG = 1
    COLUMN_NEW = 2

    # keys are tags
    # values are FileLookup methods (as string)
    # to use to look up for the matching tag
    LOOKUP_TAGS = {
        'acoustid_id': 'acoust_lookup',
        'musicbrainz_albumartistid': 'artist_lookup',
        'musicbrainz_albumid': 'album_lookup',
        'musicbrainz_artistid': 'artist_lookup',
        'musicbrainz_discid': 'discid_lookup',
        'musicbrainz_recordingid': 'recording_lookup',
        'musicbrainz_releasegroupid': 'release_group_lookup',
        'musicbrainz_trackid': 'track_lookup',
        'musicbrainz_workid': 'work_lookup',
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tagger = QtCore.QCoreApplication.instance()
        config = get_config()
        config.setting.setting_changed.connect(self._on_setting_changed)
        self.setAccessibleName(_("metadata view"))
        self.setAccessibleDescription(_("Displays original and new tags for the selected files"))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels((_("Tag"), _("Original Value"), _("New Value")))
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionsClickable(False)
        self.verticalHeader().setDefaultSectionSize(21)
        self.verticalHeader().setVisible(False)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setTabKeyNavigation(False)
        self.setStyleSheet("QTableWidget {border: none;}")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect, 1)
        self.setItemDelegate(TableTagEditorDelegate(self))
        self.setWordWrap(False)
        self.files = set()
        self.tracks = set()
        self.objects = set()
        self.tag_diff = None
        self.selection_mutex = QtCore.QMutex()
        self.selection_dirty = False
        self.editing = None  # the QTableWidgetItem being edited
        self.clipboard = [""]
        self.add_tag_action = QtGui.QAction(_("Add New Tag…"), self)
        self.add_tag_action.triggered.connect(partial(self._edit_tag, ""))
        self.changes_first_action = QtGui.QAction(_("Show Changes First"), self)
        self.changes_first_action.setCheckable(True)
        self.changes_first_action.setChecked(config.persist['show_changes_first'])
        self.changes_first_action.toggled.connect(self._toggle_changes_first)
        # TR: Keyboard shortcut for "Add New Tag…"
        self.add_tag_shortcut = QtGui.QShortcut(QtGui.QKeySequence(_("Alt+Shift+A")), self, partial(self._edit_tag, ""))
        self.add_tag_action.setShortcut(self.add_tag_shortcut.key())
        # TR: Keyboard shortcut for "Edit…" (tag)
        self.edit_tag_shortcut = QtGui.QShortcut(QtGui.QKeySequence(_("Alt+Shift+E")), self, partial(self._edit_selected_tag))
        # TR: Keyboard shortcut for "Remove" (tag)
        self.remove_tag_shortcut = QtGui.QShortcut(QtGui.QKeySequence(_("Alt+Shift+R")), self, self.remove_selected_tags)
        self.preserved_tags = PreservedTags()
        self._single_file_album = False
        self._single_track_album = False
        self.ignore_updates = IgnoreUpdatesContext(on_exit=self.update)
        self.tagger.clipboard().dataChanged.connect(self._update_clipboard)

    def _on_setting_changed(self, name, old_value, new_value):
        settings_to_watch = {
            "enabled_plugins",
            "clear_existing_tags",
            "file_naming_scripts",
            "move_files_to",
            "move_files",
            "rename_files",
            "selected_file_naming_script_id",
            "standardize_artists",
            "user_profile_settings"
            "user_profiles",
            "va_name",
            "windows_compatibility",
        }
        if name in settings_to_watch:
            self.update(drop_album_caches=False)

    def _get_file_lookup(self):
        """Return a FileLookup object."""
        config = get_config()
        return FileLookup(self, config.setting['server_host'],
                          config.setting['server_port'],
                          self.tagger.browser_integration.port)

    def _lookup_tag(self, tag):
        lookup = self._get_file_lookup()
        return getattr(lookup, self.LOOKUP_TAGS[tag])

    def _open_link(self, values, tag):
        lookup_func = self._lookup_tag(tag)
        for v in values:
            lookup_func(v)

    def edit(self, index, trigger, event):
        if index.column() != self.COLUMN_NEW:
            return False
        item = self.itemFromIndex(index)
        if item.flags() & QtCore.Qt.ItemFlag.ItemIsEditable and \
           trigger in {QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked,
                       QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed,
                       QtWidgets.QAbstractItemView.EditTrigger.AnyKeyPressed}:
            tag = self.tag_diff.tag_names[item.row()]
            values = self.tag_diff.new[tag]
            if len(values) > 1:
                self._edit_tag(tag)
                return False
            else:
                self.editing = item
                item.setText(values[0])
                return super().edit(index, trigger, event)
        return False

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.StandardKey.Copy):
            self._copy_value()
        elif event.matches(QtGui.QKeySequence.StandardKey.Paste):
            self._paste_value()
        else:
            super().keyPressEvent(event)

    def _copy_value(self):
        item = self.currentItem()
        if item:
            column = item.column()
            tag = self.tag_diff.tag_names[item.row()]
            value = None
            if column == self.COLUMN_ORIG:
                value = self.tag_diff.old[tag]
            elif column == self.COLUMN_NEW:
                value = self.tag_diff.new[tag]

            if tag == '~length':
                try:
                    value = [format_time(value or 0), ]
                except (TypeError, ValueError) as why:
                    log.warning(why)
                    value = ['']

            if value is not None:
                self.tagger.clipboard().setText(MULTI_VALUED_JOINER.join(value))
                self.clipboard = value

    def _paste_value(self):
        item = self.currentItem()
        if item:
            column = item.column()
            tag = self.tag_diff.tag_names[item.row()]
            if column == self.COLUMN_NEW and self._tag_is_editable(tag):
                self._set_tag_values(tag, self.clipboard)
                self.update()

    def _update_clipboard(self):
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
            self._set_tag_values(tag, new)
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
            tags = list(self._selected_tags())
            single_tag = len(tags) == 1
            if single_tag:
                selected_tag = tags[0]
                editable = self._tag_is_editable(selected_tag)
                edit_tag_action = QtGui.QAction(_("Edit…"), self)
                edit_tag_action.triggered.connect(partial(self._edit_tag, selected_tag))
                edit_tag_action.setShortcut(self.edit_tag_shortcut.key())
                edit_tag_action.setEnabled(editable)
                menu.addAction(edit_tag_action)
                if selected_tag not in self.preserved_tags:
                    add_to_preserved_tags_action = QtGui.QAction(_("Add to 'Preserve Tags' List"), self)
                    add_to_preserved_tags_action.triggered.connect(partial(self.preserved_tags.add, selected_tag))
                    add_to_preserved_tags_action.setEnabled(editable)
                    menu.addAction(add_to_preserved_tags_action)
                else:
                    remove_from_preserved_tags_action = QtGui.QAction(_("Remove from 'Preserve Tags' List"), self)
                    remove_from_preserved_tags_action.triggered.connect(partial(self.preserved_tags.discard, selected_tag))
                    remove_from_preserved_tags_action.setEnabled(editable)
                    menu.addAction(remove_from_preserved_tags_action)
            removals = []
            useorigs = []
            mergeorigs = []
            item = self.currentItem()
            if item:
                column = item.column()
                for tag in tags:
                    if tag in self.LOOKUP_TAGS:
                        if (column == self.COLUMN_ORIG or column == self.COLUMN_NEW) and single_tag and item.text():
                            if column == self.COLUMN_ORIG:
                                values = self.tag_diff.old[tag]
                            else:
                                values = self.tag_diff.new[tag]
                            lookup_action = QtGui.QAction(_("Lookup in &Browser"), self)
                            lookup_action.triggered.connect(partial(self._open_link, values, tag))
                            menu.addAction(lookup_action)
                    if self._tag_is_removable(tag):
                        removals.append(partial(self._remove_tag, tag))
                    status = self.tag_diff.status[tag] & TagStatus.CHANGED
                    if status == TagStatus.CHANGED or status == TagStatus.REMOVED:
                        file_tracks = []
                        track_albums = set()
                        for file in self.files:
                            extra_objects = []
                            if file.parent_item in self.tracks and len(self.files & set(file.parent_item.files)) == 1:
                                extra_objects.append(file.parent_item)
                                file_tracks.append(file.parent_item)
                                track_albums.add(file.parent_item.album)
                            useorigs.append(partial(self._use_orig_tags, file, tag, extra_objects))
                            mergeorigs.append(partial(self._merge_orig_tags, file, tag, extra_objects))
                        for track in set(self.tracks)-set(file_tracks):
                            useorigs.append(partial(self._use_orig_tags, track, tag))
                            mergeorigs.append(partial(self._merge_orig_tags, track, tag))
                            track_albums.add(track.album)
                        for album in track_albums:
                            useorigs.append(partial(self._use_orig_tags, album, tag))
                            mergeorigs.append(partial(self._merge_orig_tags, album, tag))
                remove_tag_action = QtGui.QAction(_("Remove"), self)
                remove_tag_action.triggered.connect(partial(self._apply_update_funcs, removals))
                remove_tag_action.setShortcut(self.remove_tag_shortcut.key())
                remove_tag_action.setEnabled(bool(removals))
                menu.addAction(remove_tag_action)
                if useorigs:
                    name = ngettext("Use Original Value", "Use Original Values", len(useorigs))
                    use_orig_value_action = QtGui.QAction(name, self)
                    use_orig_value_action.triggered.connect(partial(self._apply_update_funcs, useorigs))
                    menu.addAction(use_orig_value_action)
                    merge_tags_action = QtGui.QAction(_("Merge Original Values"), self)
                    merge_tags_action.triggered.connect(partial(self._apply_update_funcs, mergeorigs))
                    menu.addAction(merge_tags_action)
                    menu.addSeparator()
                if single_tag:
                    menu.addSeparator()
                    copy_action = QtGui.QAction(icontheme.lookup('edit-copy', icontheme.ICON_SIZE_MENU), _("&Copy"), self)
                    copy_action.triggered.connect(self._copy_value)
                    copy_action.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
                    menu.addAction(copy_action)
                    paste_action = QtGui.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _("&Paste"), self)
                    paste_action.triggered.connect(self._paste_value)
                    paste_action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
                    paste_action.setEnabled(editable)
                    menu.addAction(paste_action)
            if single_tag or removals or useorigs:
                menu.addSeparator()
            menu.addAction(self.add_tag_action)
            menu.addSeparator()
        menu.addAction(self.changes_first_action)
        menu.exec(event.globalPos())
        event.accept()

    def _apply_update_funcs(self, funcs):
        with self.tagger.window.ignore_selection_changes:
            for f in funcs:
                f()
        self.tagger.window.update_selection(new_selection=False, drop_album_caches=True)

    def _use_orig_tags(self, obj, tag, extra_objects=None):
        orig_values = list(obj.orig_metadata.getall(tag)) or [""]
        self._set_tag_values_extra(tag, orig_values, obj, extra_objects)

    def _merge_orig_tags(self, obj, tag, extra_objects=None):
        values = list(obj.orig_metadata.getall(tag))
        for new_value in obj.metadata.getall(tag):
            if new_value not in values:
                values.append(new_value)
        self._set_tag_values_extra(tag, values, obj, extra_objects)

    def _edit_tag(self, tag):
        if self.tag_diff is not None:
            EditTagDialog(self, tag).exec()

    def _edit_selected_tag(self):
        tags = list(self._selected_tags(filter_func=self._tag_is_editable))
        if len(tags) == 1:
            self._edit_tag(tags[0])

    def _toggle_changes_first(self, checked):
        config = get_config()
        config.persist['show_changes_first'] = checked
        self.update()

    def _set_tag_values_extra(self, tag, values, obj, extra_objects):
        objects = [obj]
        if extra_objects:
            objects.extend(extra_objects)
        self._set_tag_values(tag, values, objects=objects)

    def _set_tag_values(self, tag, values, objects=None):
        if objects is None:
            objects = self.objects
        with self.tagger.window.ignore_selection_changes:
            if values == [""]:
                values = []
            if not values and self._tag_is_removable(tag):
                for obj in objects:
                    del obj.metadata[tag]
                    obj.update()
            elif values:
                for obj in objects:
                    obj.metadata[tag] = values
                    obj.update()

    def _remove_tag(self, tag):
        self._set_tag_values(tag, [])

    def remove_selected_tags(self):
        for tag in self._selected_tags(filter_func=self._tag_is_removable):
            self._remove_tag(tag)
        self.tagger.window.update_selection(new_selection=False, drop_album_caches=True)

    def _tag_is_removable(self, tag):
        return self.tag_diff.status[tag] & TagStatus.NOTREMOVABLE == 0

    def _tag_is_editable(self, tag):
        return self.tag_diff.status[tag] & TagStatus.READONLY == 0

    def _selected_tags(self, filter_func=None):
        for tag in set(self.tag_diff.tag_names[item.row()]
                       for item in self.selectedItems()):
            if filter_func is None or filter_func(tag):
                yield tag

    def _update_selection(self):
        if not hasattr(self.tagger, 'window'):
            # main window not yet available
            # FIXME: early call strictly needed?
            return
        files = set()
        tracks = set()
        objects = set()
        for obj in self.tagger.window.selected_objects:
            if isinstance(obj, File):
                files.add(obj)
            elif isinstance(obj, Track):
                tracks.add(obj)
                files.update(obj.files)
            elif isinstance(obj, Cluster) and obj.can_edit_tags:
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
        new_selection = self.selection_dirty
        if self.editing or (self.ignore_updates and not new_selection):
            return
        if new_selection:
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
            self._single_file_album = len({file.metadata['album'] for file in files}) == 1
            self._single_track_album = len({track.metadata['album'] for track in tracks}) == 1

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

        config = get_config()
        tag_diff = TagDiff(max_length_diff=config.setting['ignore_track_duration_difference_under'])
        tag_diff.objects = len(files)

        clear_existing_tags = config.setting['clear_existing_tags']
        top_tags = config.setting['metadatabox_top_tags']
        top_tags_set = set(top_tags)

        settings = config.setting.as_dict()

        for file in files:
            new_metadata = file.metadata
            orig_metadata = file.orig_metadata
            tags = set(new_metadata) | set(orig_metadata)

            for tag in tags:
                if tag.startswith("~"):
                    continue
                if not file.supports_tag(tag):
                    continue
                new_values = file.format_specific_metadata(new_metadata, tag, settings)
                orig_values = file.format_specific_metadata(orig_metadata, tag, settings)

                if not clear_existing_tags and not new_values:
                    new_values = list(orig_values or [""])

                removed = tag in new_metadata.deleted_tags
                tag_diff.add(tag, old=orig_values, new=new_values, removed=removed, top_tags=top_tags_set)

            tag_diff.add('~length', str(orig_metadata.length), str(new_metadata.length),
                         removable=False, readonly=True)
            if len(files) == 1:
                if settings['rename_files'] or settings['move_files']:
                    new_filename = file.make_filename(file.filename, new_metadata)
                else:
                    new_filename = file.filename
                tag_diff.add('~filepath', old=[file.filename], new=[new_filename], removable=False, readonly=True)

        for track in tracks:
            if track.num_linked_files == 0:
                for tag, new_values in track.metadata.rawitems():
                    if not tag.startswith("~"):
                        if tag in track.orig_metadata:
                            orig_values = track.orig_metadata.getall(tag)
                        else:
                            orig_values = new_values
                        tag_diff.add(tag, old=orig_values, new=new_values)

                length = str(track.metadata.length)
                tag_diff.add('~length', old=length, new=length, removable=False, readonly=True)

                tag_diff.objects += 1

        tag_diff.update_tag_names(config.persist['show_changes_first'], top_tags)
        return tag_diff

    def _update_items(self, result=None, error=None):
        if self.editing:
            return

        if not (self.files or self.tracks):
            result = None

        self.tag_diff = result

        if self.tag_diff is None:
            self.setRowCount(0)
            return

        self.setRowCount(len(self.tag_diff.tag_names))

        readonly_item_flags = QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
        editable_item_flags = readonly_item_flags | QtCore.Qt.ItemFlag.ItemIsEditable
        alignment = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        colors = {
            TagStatus.UNCHANGED: self.palette().color(QtGui.QPalette.ColorRole.Text),
            TagStatus.REMOVED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_removed')),
            TagStatus.ADDED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_added')),
            TagStatus.CHANGED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_changed'))
        }

        def get_table_item(row, column):
            """
            Returns item for row and column if it exists or create a new one
            By default, set it as read-only
            """
            item = self.item(row, column)
            if not item:
                item = QtWidgets.QTableWidgetItem()
                item.setTextAlignment(alignment)
                self.setItem(row, column, item)
            item.setFlags(readonly_item_flags)
            return item

        for row, tag in enumerate(self.tag_diff.tag_names):
            tag_item = get_table_item(row, self.COLUMN_TAG)
            self._set_item_tag(tag_item, tag)

            color = colors.get(self.tag_diff.tag_status(tag), colors[TagStatus.UNCHANGED])

            orig_item = get_table_item(row, self.COLUMN_ORIG)
            self._set_item_value(orig_item, self.tag_diff.old, tag, color)

            new_item = get_table_item(row, self.COLUMN_NEW)
            if not self.tag_diff.is_readonly(tag):
                new_item.setFlags(editable_item_flags)
            strikeout = self.tag_diff.tag_status(tag) == TagStatus.REMOVED
            self._set_item_value(new_item, self.tag_diff.new, tag, color, strikeout=strikeout)

            # Adjust row height to content size
            self.setRowHeight(row, self.sizeHintForRow(row))

    @staticmethod
    def _set_item_tag(item, tag):
        item.setText(display_tag_name(tag))
        font = item.font()
        font.setBold(True)
        item.setFont(font)

    @staticmethod
    def _set_item_value(item, tags, tag, color, strikeout=False):
        display_value = tags.display_value(tag)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, tag)
        item.setText(display_value.text)
        item.setForeground(color)
        font = item.font()
        font.setItalic(display_value.is_grouped)
        font.setStrikeOut(strikeout)
        item.setFont(font)

    @restore_method
    def restore_state(self):
        config = get_config()
        state = config.persist['metadatabox_header_state']
        header = self.horizontalHeader()
        header.restoreState(state)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)

    def save_state(self):
        config = get_config()
        header = self.horizontalHeader()
        state = header.saveState()
        config.persist['metadatabox_header_state'] = state
