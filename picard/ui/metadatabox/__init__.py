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
import json

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
    N_,
    gettext as _,
    ngettext,
)
from picard.metadata import MULTI_VALUED_JOINER
from picard.tags import display_tag_name
from picard.tags.docs import display_tag_tooltip
from picard.tags.preserved import UserPreservedTags
from picard.track import Track
from picard.util import (
    IgnoreUpdatesContext,
    icontheme,
    restore_method,
    thread,
    throttle,
)

from .edittagdialog import (
    EditTagDialog,
    TagEditorDelegate,
)
from .tagdiff import (
    TagDiff,
    TagStatus,
)

from picard.ui.colors import interface_colors
from picard.ui.metadatabox.mimedatahelper import MimeDataHelper


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
    MIMETYPE_PICARD_TAGS = "application/vdr.picard"
    MIMETYPE_TSV = 'text/tab-separated-values'
    MIMETYPE_TEXT = 'text/plain'

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

        # Connect to plugin manager signals to refresh when plugins change
        plugin_manager = self.tagger.get_plugin_manager()
        if plugin_manager:
            plugin_manager.plugin_state_changed.connect(self._on_plugin_changed)
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
        self.edit_tag_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence(_("Alt+Shift+E")), self, partial(self._edit_selected_tag)
        )
        # TR: Keyboard shortcut for "Remove" (tag)
        self.remove_tag_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence(_("Alt+Shift+R")), self, self.remove_selected_tags
        )
        self.preserved_tags = UserPreservedTags()
        self._single_file_album = False
        self._single_track_album = False
        self.ignore_updates = IgnoreUpdatesContext(on_exit=self.update)

        self.mimedata_helper = MimeDataHelper()
        self.mimedata_helper.register(
            self.MIMETYPE_PICARD_TAGS,
            encode_func=lambda tag_diff: tag_diff.to_json().encode('utf-8'),
            decode_func=lambda target, mimedata: target._paste_from_json(mimedata),
        )
        self.mimedata_helper.register(
            self.MIMETYPE_TSV,
            encode_func=lambda tag_diff: tag_diff.to_tsv().encode('utf-8'),
            decode_func=None,
        )
        self.mimedata_helper.register(
            self.MIMETYPE_TEXT,
            encode_func=lambda tag_diff: tag_diff.to_tsv().encode('utf-8'),
            decode_func=lambda target, mimedata: target._paste_from_text(mimedata),
        )

    def _on_setting_changed(self, name, old_value, new_value):
        settings_to_watch = {
            "clear_existing_tags",
            "file_naming_scripts",
            "move_files_to",
            "move_files",
            "rename_files",
            "selected_file_naming_script_id",
            "standardize_artists",
            "user_profile_settings",
            "user_profiles",
            "va_name",
            "windows_compatibility",
        }
        if name in settings_to_watch:
            self.update(drop_album_caches=False)

    def _on_plugin_changed(self, plugin):
        """Handle plugin enabled/disabled - refresh metadata display"""
        self.update(drop_album_caches=False)

    def _get_file_lookup(self):
        """Return a FileLookup object."""
        config = get_config()
        return FileLookup(
            self,
            config.setting['server_host'],
            config.setting['server_port'],
            self.tagger.browser_integration.port,
        )

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
        if item.flags() & QtCore.Qt.ItemFlag.ItemIsEditable and trigger in {
            QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked,
            QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed,
            QtWidgets.QAbstractItemView.EditTrigger.AnyKeyPressed,
        }:
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

    def get_selected_tags(self, items):
        result = TagDiff()
        for item in items:
            tag, value = self._get_row_info(item.row())
            col = item.column()
            result.add(
                tag=tag,
                old=value[self.COLUMN_ORIG] if col == self.COLUMN_ORIG else None,
                new=value[self.COLUMN_NEW] if col == self.COLUMN_NEW else None,
                removable=self.tag_diff.status[tag] != TagStatus.NOTREMOVABLE,
                readonly=self.tag_diff.status[tag] == TagStatus.READONLY,
            )

        result.update_tag_names()
        return result

    def _get_row_info(self, row):
        tag = self.tag_diff.tag_names[row]
        value = {
            self.COLUMN_ORIG: self.tag_diff.old[tag],
            self.COLUMN_NEW: self.tag_diff.new[tag],
        }
        return tag, value

    def _can_copy(self):
        return True

    def _copy_value(self):
        if not self._can_copy():
            msg = N_("Unable to copy current selection.")
            self.tagger.window.set_statusbar_message(msg, echo=log.info, timeout=3000)
            return

        items = self.selectedItems()
        if len(items) > 1:
            selected_data = self.get_selected_tags(items)
            # Build the mimedata to use for the clipboard
            mimedata = QtCore.QMimeData()
            converted_data_cache = {}
            for mimetype, encode_func in self.mimedata_helper.encode_funcs():
                try:
                    if encode_func not in converted_data_cache:
                        converted_data_cache[encode_func] = encode_func(selected_data)
                    mimedata.setData(mimetype, converted_data_cache[encode_func])
                except Exception as e:
                    log.error("Failed to convert %r to '%s': %s", selected_data, mimetype, e)
            # Ensure we actually have something to copy to the clipboard
            if mimedata.formats():
                log.debug("Copying %r to clipboard as %r", selected_data.tag_names, mimedata.formats())
                self.tagger.clipboard().setMimeData(mimedata)
        else:
            # Just copy the current item as a string
            item = self.currentItem()
            if item:
                tag, value = self._get_row_info(item.row())
                value = value[item.column()]
                if tag == '~length':
                    value = self.tag_diff.handle_length(value, prettify_times=True)
                if value is not None:
                    log.debug("Copying '%s' to clipboard (from tag '%s')", value, tag)
                    self.tagger.clipboard().setText(MULTI_VALUED_JOINER.join(value))

    def _paste_from_json(self, mimedata):
        def _decode_json(mimedata):
            try:
                text = mimedata.data(self.MIMETYPE_PICARD_TAGS).data()
                return json.loads(text)
            except json.JSONDecodeError as e:
                log.error("Failed to decode JSON data from clipboard: %r", e)

        def _apply_tag_dict(data):
            for tag in data:
                if self._tag_is_editable(tag):
                    # Prefer 'new' values, but fall back to 'old' if not available
                    value = data[tag].get(TagDiff.NEW_VALUE) or data[tag].get(TagDiff.OLD_VALUE)
                    if value:
                        if isinstance(value, list):
                            # There are multiple values for the tag
                            value = MULTI_VALUED_JOINER.join(value)
                        # each value may also represent multiple values
                        log.info("Pasting '%s' from JSON clipboard to tag '%s'", value, tag)
                        value = value.split(MULTI_VALUED_JOINER)
                        yield from self._set_tag_values_delayed_updates(tag, value)
                    else:
                        log.error("Tag '%s' without new or old value found in clipboard, ignoring.", tag)

        data = _decode_json(mimedata)
        return _apply_tag_dict(data) if data else []

    def _paste_from_text(self, mimedata):
        item = self.currentItem()
        column_is_editable = item.column() == self.COLUMN_NEW
        tag = self.tag_diff.tag_names[item.row()]
        value = mimedata.text()
        if column_is_editable and self._tag_is_editable(tag) and value:
            log.info("Pasting %s from text clipboard to tag %s", value, tag)
            value = value.split(MULTI_VALUED_JOINER)
            yield from self._set_tag_values_delayed_updates(tag, value)

    def _can_paste(self):
        mimedata = self.tagger.clipboard().mimeData()
        has_valid_mime_data = any(self.mimedata_helper.decode_funcs(mimedata))
        return has_valid_mime_data and len(self.tracks) <= 1 and len(self.files) <= 1

    def _paste_value(self):
        if not self._can_paste():
            msg = N_("No valid data in clipboard to paste")
            self.tagger.window.set_statusbar_message(msg, echo=log.info, timeout=3000)
            return

        objects_to_update = set()
        mimedata = self.tagger.clipboard().mimeData()

        for decode_func in self.mimedata_helper.decode_funcs(mimedata):
            objs = decode_func(self, mimedata)
            objects_to_update.update(objs)
            if objs:
                # We have successfully pasted from the clipboard, don't try other mimetypes
                break

        if objects_to_update:
            objects_to_update.add(self)
            self._update_objects(objects_to_update)

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

    def _add_single_tag_actions(self, menu, selected_tag):
        """
        Adds actions for a single selected tag to the context menu.

        Includes edit action and add/remove from preserved tags list.
        """
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

    def _collect_orig_tag_actions(self, tag, useorigs, mergeorigs):
        """
        Collects actions for restoring or merging original tag values for a given tag.

        - Adds actions for each file, track, and album where the tag has changed or been removed.
        - Ensures actions are only added once per object.
        """
        status = self.tag_diff.status[tag] & TagStatus.CHANGED
        if status not in (TagStatus.CHANGED, TagStatus.REMOVED):
            return

        file_tracks = []
        track_albums = set()

        # Add actions for files and their parent tracks/albums
        for file in self.files:
            self._process_file_for_orig_actions(file, tag, useorigs, mergeorigs, file_tracks, track_albums)

        # Add actions for tracks not already handled
        for track in set(self.tracks) - set(file_tracks):
            useorigs.append(partial(self._use_orig_tags, track, tag))
            mergeorigs.append(partial(self._merge_orig_tags, track, tag))
            track_albums.add(track.album)

        # Add actions for albums
        for album in track_albums:
            useorigs.append(partial(self._use_orig_tags, album, tag))
            mergeorigs.append(partial(self._merge_orig_tags, album, tag))

    def _process_file_for_orig_actions(self, file, tag, useorigs, mergeorigs, file_tracks, track_albums):
        """
        Helper for _collect_orig_tag_actions.
        Adds actions for a file and its parent track/album if appropriate.
        """
        extra_objects = []
        if file.parent_item in self.tracks and len(self.files & set(file.parent_item.files)) == 1:
            extra_objects.append(file.parent_item)
            file_tracks.append(file.parent_item)
            track_albums.add(file.parent_item.album)
        useorigs.append(partial(self._use_orig_tags, file, tag, extra_objects))
        mergeorigs.append(partial(self._merge_orig_tags, file, tag, extra_objects))

    def _add_tag_modification_actions(self, menu, removals, useorigs, mergeorigs):
        """
        Adds actions for removing, restoring, and merging tags to the context menu.
        """
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

    def _add_copy_paste_actions(self, menu):
        """
        Adds copy and paste actions to the context menu.
        """
        menu.addSeparator()
        copy_action = QtGui.QAction(icontheme.lookup('edit-copy', icontheme.ICON_SIZE_MENU), _("&Copy"), self)
        copy_action.triggered.connect(self._copy_value)
        copy_action.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        copy_action.setEnabled(self._can_copy())
        menu.addAction(copy_action)
        paste_action = QtGui.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _("&Paste"), self)
        paste_action.triggered.connect(self._paste_value)
        paste_action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        paste_action.setEnabled(self._can_paste())
        menu.addAction(paste_action)

    def contextMenuEvent(self, event):
        """
        Handles the right-click context menu event for the metadata table.

        Builds a context menu dynamically based on the current selection and state.
        Adds actions for editing, removing, restoring, merging, copying, pasting tags, etc.
        """
        menu = QtWidgets.QMenu(self)
        if self.objects:
            tags = list(self._selected_tags())
            single_tag = len(tags) == 1
            if single_tag:
                selected_tag = tags[0]
                self._add_single_tag_actions(menu, selected_tag)
            removals = []
            useorigs = []
            mergeorigs = []
            item = self.currentItem()
            if item:
                column = item.column()
                for tag in tags:
                    # Add lookup action for supported tags
                    if tag in self.LOOKUP_TAGS:
                        if (column == self.COLUMN_ORIG or column == self.COLUMN_NEW) and single_tag and item.text():
                            if column == self.COLUMN_ORIG:
                                values = self.tag_diff.old[tag]
                            else:
                                values = self.tag_diff.new[tag]
                            lookup_action = QtGui.QAction(_("Lookup in &Browser"), self)
                            lookup_action.triggered.connect(partial(self._open_link, values, tag))
                            menu.addAction(lookup_action)
                    # Collect removable tags
                    if self._tag_is_removable(tag):
                        removals.append(partial(self._remove_tag, tag))
                    # Collect actions for restoring/merging original tag values
                    self._collect_orig_tag_actions(tag, useorigs, mergeorigs)
                # Add actions for removing, restoring, merging tags
                self._add_tag_modification_actions(menu, removals, useorigs, mergeorigs)
                # Add copy/paste actions
                self._add_copy_paste_actions(menu)
            # Add separator and "Add New Tag" if relevant
            if single_tag or removals or useorigs:
                menu.addSeparator()
            menu.addAction(self.add_tag_action)
            menu.addSeparator()
        # Always add "Show Changes First" action
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

    def _set_tag_values_delayed_updates(self, tag, values, objects=None):
        if objects is None:
            objects = self.objects
        with self.tagger.window.ignore_selection_changes:
            if values == [""]:
                values = []
            if not values and self._tag_is_removable(tag):
                for obj in objects:
                    del obj.metadata[tag]
                    yield obj
            elif values:
                for obj in objects:
                    obj.metadata[tag] = values
                    yield obj

    def _update_objects(self, objects):
        for obj in set(objects):
            obj.update()

    def _set_tag_values(self, tag, values, objects=None):
        self._update_objects(self._set_tag_values_delayed_updates(tag, values, objects=objects))

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
        for tag in set(self.tag_diff.tag_names[item.row()] for item in self.selectedItems()):
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
        thread.run_task(
            partial(self._update_tags, new_selection, drop_album_caches),
            self._update_items,
            thread_pool=self.tagger.priority_thread_pool,
        )

    def _update_tags(self, new_selection=True, drop_album_caches=False):
        """
        Build a TagDiff object representing the differences between original and new metadata
        for the current selection of files and tracks.
        """
        self.selection_mutex.lock()
        files = self.files
        tracks = self.tracks
        self.selection_mutex.unlock()

        if not (files or tracks):
            return None

        # Update album/track grouping flags if selection changed or caches dropped
        if new_selection or drop_album_caches:
            self._single_file_album = len({file.metadata['album'] for file in files}) == 1
            self._single_track_album = len({track.metadata['album'] for track in tracks}) == 1

        # If selection didn't change and not a single file/track/album, skip update
        if not new_selection:
            if not (len(files) == 1 or len(tracks) == 1 or self._single_file_album or self._single_track_album):
                return self.tag_diff

        config = get_config()
        tag_diff = TagDiff(max_length_diff=config.setting['ignore_track_duration_difference_under'])
        tag_diff.objects = len(files)

        top_tags = config.setting['metadatabox_top_tags']

        self._add_files_to_tag_diff(files, tag_diff, config, top_tags)
        self._add_tracks_to_tag_diff(tracks, tag_diff, config)

        tag_diff.update_tag_names(config.persist['show_changes_first'], top_tags)
        return tag_diff

    def _add_files_to_tag_diff(self, files, tag_diff, config, top_tags):
        """
        Add file tags and special tags (~length, ~filepath) to tag_diff.
        """
        top_tags_set = set(top_tags)
        settings = config.setting.as_dict()
        clear_existing_tags = settings['clear_existing_tags']
        for file in files:
            new_metadata = file.metadata
            orig_metadata = file.orig_metadata
            tags = set(new_metadata) | set(orig_metadata)

            for tag in tags:
                if tag.startswith("~") or not file.supports_tag(tag):
                    continue
                new_values = file.format_specific_metadata(new_metadata, tag, settings)
                orig_values = file.format_specific_metadata(orig_metadata, tag, settings)

                if not clear_existing_tags and not new_values:
                    new_values = list(orig_values or [""])

                removed = tag in new_metadata.deleted_tags
                tag_diff.add(tag, old=orig_values, new=new_values, removed=removed, top_tags=top_tags_set)

            # Always add length tag
            tag_diff.add('~length', str(orig_metadata.length), str(new_metadata.length), removable=False, readonly=True)
            # Add filepath tag if only one file
            if len(files) == 1:
                if settings['rename_files'] or settings['move_files']:
                    new_filename = file.make_filename(file.filename, new_metadata)
                else:
                    new_filename = file.filename
                tag_diff.add('~filepath', old=[file.filename], new=[new_filename], removable=False, readonly=True)

    def _add_tracks_to_tag_diff(self, tracks, tag_diff, config):
        """
        Add track tags and ~length for tracks without linked files to tag_diff.
        """
        for track in tracks:
            if track.num_linked_files != 0:
                continue
            for tag, new_values in track.metadata.rawitems():
                if tag.startswith("~"):
                    continue
                orig_values = track.orig_metadata.getall(tag) if tag in track.orig_metadata else new_values
                tag_diff.add(tag, old=orig_values, new=new_values)
            length = str(track.metadata.length)
            tag_diff.add('~length', old=length, new=length, removable=False, readonly=True)
            tag_diff.objects += 1

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
            TagStatus.CHANGED: QtGui.QBrush(interface_colors.get_qcolor('tagstatus_changed')),
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
        item.setToolTip(display_tag_tooltip(tag))

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
