# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Wieland Hoffmann
# Copyright (C) 2017-2018, 2020-2024 Laurent Monin
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019-2022, 2024 Philipp Wolfer
# Copyright (C) 2023 certuna
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


from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.const import (
    RELEASE_FORMATS,
    RELEASE_PRIMARY_GROUPS,
    RELEASE_SECONDARY_GROUPS,
    RELEASE_STATUS,
)
from picard.const.countries import RELEASE_COUNTRIES
from picard.i18n import gettext as _
from picard.util import temporary_disconnect
from picard.util.tags import tag_names

from picard.ui import PicardDialog
from picard.ui.forms.ui_edittagdialog import Ui_EditTagDialog


AUTOCOMPLETE_RELEASE_TYPES = [s.lower() for s
                              in sorted(RELEASE_PRIMARY_GROUPS) + sorted(RELEASE_SECONDARY_GROUPS)]
AUTOCOMPLETE_RELEASE_STATUS = sorted(s.lower() for s in RELEASE_STATUS)
AUTOCOMPLETE_RELEASE_COUNTRIES = sorted(RELEASE_COUNTRIES, key=str.casefold)
AUTOCOMPLETE_RELEASE_FORMATS = sorted(RELEASE_FORMATS, key=str.casefold)

MULTILINE_TAGS = {'comment', 'lyrics', 'syncedlyrics'}
DATE_YYYYMMDD_TAGS = {'date', 'originaldate', 'releasedate'}
DATE_YYYY_TAGS = {'originalyear'}


class CompleterConfig:
    """Configuration for creating and setting up QCompleter instances."""

    def __init__(self, options, case_insensitive_sort=True):
        """Initialize completer configuration.

        Args:
            options: List of completion options
            case_insensitive_sort: Whether to use case-insensitive sorting
        """
        self.options = options
        self.case_insensitive_sort = case_insensitive_sort

    def create_completer(self, editor):
        """Create and configure a QCompleter instance.

        Args:
            editor: The editor widget to attach the completer to

        Returns:
            Configured QCompleter instance
        """
        completer = QtWidgets.QCompleter(self.options, editor)
        completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        if self.case_insensitive_sort:
            completer.setModelSorting(QtWidgets.QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        return completer


COMPLETER_CONFIG = {
    'releasetype': CompleterConfig(AUTOCOMPLETE_RELEASE_TYPES, case_insensitive_sort=False),
    'releasestatus': CompleterConfig(AUTOCOMPLETE_RELEASE_STATUS),
    'releasecountry': CompleterConfig(AUTOCOMPLETE_RELEASE_COUNTRIES),
    'media': CompleterConfig(AUTOCOMPLETE_RELEASE_FORMATS)
}


class TagEditorDelegate(QtWidgets.QItemDelegate):

    def createEditor(self, parent, option, index):
        if not index.isValid():
            return None

        tag = self.get_tag_name(index)
        editor = self._create_editor_based_on_tag_type(parent, tag, option, index)
        self._configure_editor_for_tag(editor, tag)
        return editor

    def _create_editor_based_on_tag_type(self, parent, tag, option, index):
        """Create appropriate editor widget based on tag type.

        Args:
            parent: Parent widget
            tag: Tag name
            option: Style options
            index: Model index

        Returns:
            QWidget subclass appropriate for editing the tag
        """
        if tag.partition(':')[0] in MULTILINE_TAGS:
            editor = QtWidgets.QPlainTextEdit(parent)
            editor.setFrameStyle(editor.style().styleHint(
                QtWidgets.QStyle.StyleHint.SH_ItemView_DrawDelegateFrame, None, editor))
            editor.setMinimumSize(QtCore.QSize(0, 80))
            return editor
        return super().createEditor(parent, option, index)

    def _configure_editor_for_tag(self, editor, tag):
        """Configure editor widget for specific tag.

        Args:
            editor: Editor widget to configure
            tag: Tag name
        """
        placeholder = self._get_placeholder_text(tag)
        if placeholder is not None:
            editor.setPlaceholderText(placeholder)
        completer = self._create_completer_for_tag(editor, tag)
        if completer:
            editor.setCompleter(completer)

    def _get_placeholder_text(self, tag):
        """Get placeholder text for specified tag.

        Args:
            tag: Tag name
        """
        if tag in DATE_YYYYMMDD_TAGS:
            return _("YYYY-MM-DD")
        if tag in DATE_YYYY_TAGS:
            return _("YYYY")
        return None

    def _create_completer_for_tag(self, editor, tag):
        """Create completer for tag if configured.

        Args:
            editor: Editor widget
            tag: Tag name

        Returns:
            QCompleter instance or None
        """
        if tag in COMPLETER_CONFIG:
            return COMPLETER_CONFIG[tag].create_completer(editor)
        return None

    def get_tag_name(self, index):
        """Get the tag name for the given index.
        Args:
            index: QModelIndex of the item
        Returns:
            str: The tag name
        """
        return self.parent().tag


class EditTagDialog(PicardDialog):

    def __init__(self, metadata_box, tag):
        super().__init__(parent=metadata_box)
        self.ui = Ui_EditTagDialog()
        self.ui.setupUi(self)
        self.value_list = self.ui.value_list
        self.metadata_box = metadata_box
        self.tag = tag
        self.modified_tags = {}
        self.is_grouped = False
        self._updating_tag = False
        self._metadata_mutex = QtCore.QMutex()

        self._initialize_ui()
        self.tag_changed(tag)
        self.value_selection_changed()

    def _initialize_ui(self):
        """Initialize the UI."""
        self._setup_tag_combobox()
        self._setup_value_list()
        self._connect_signals()

    def _setup_tag_combobox(self):
        """Set up the tag name combobox with supported tags."""
        self.default_tags = self._get_supported_tags()
        visible_tags = (tn for tn in self.default_tags if not tn.startswith("~"))  # TODO: use TagVar.is_hidden?

        self.ui.tag_names.addItem("")
        self.ui.tag_names.addItems(visible_tags)

        self.completer = QtWidgets.QCompleter(visible_tags, self.ui.tag_names)
        self.completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.ui.tag_names.setCompleter(self.completer)

    def _get_supported_tags(self):
        """Get the list of supported tags for the current files.

        Returns:
            List of supported tag names
        """
        tags = sorted(set(tag_names()) + self.metadata_box.tag_diff.tag_names)
        if len(self.metadata_box.files) == 1:
            current_file = list(self.metadata_box.files)[0]
            tags = list(filter(current_file.supports_tag, tags))
        return tags

    def _setup_value_list(self):
        """Set up the value list widget."""
        self.ui.value_list.setItemDelegate(TagEditorDelegate(self))

    def _connect_signals(self):
        """Connect UI signals to their respective slots."""
        model = self.ui.value_list.model()
        model.rowsInserted.connect(self.on_rows_inserted)
        model.rowsRemoved.connect(self.on_rows_removed)
        model.rowsMoved.connect(self.on_rows_moved)

    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.KeyboardModifier.NoModifier
            and event.key() in {QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return}):
            self.add_or_edit_value()
            event.accept()
        elif event.matches(QtGui.QKeySequence.StandardKey.Delete):
            self.remove_value()
        elif event.key() == QtCore.Qt.Key.Key_Insert:
            self.add_value()
        else:
            super().keyPressEvent(event)

    def tag_selected(self, index):
        """Handle selection of a tag from the combobox.

        Args:
            index: Index of the selected tag
        """
        self.add_or_edit_value()

    def edit_value(self):
        """Start editing the currently selected value in the list."""
        item = self.value_list.currentItem()
        if item:
            # Do not initialize editing if editor is already active. Avoids flickering of the edit field
            # when already in edit mode. `isPersistentEditorOpen` is only supported in Qt 5.10 and later.
            if hasattr(self.value_list, 'isPersistentEditorOpen') and self.value_list.isPersistentEditorOpen(item):
                return
            self.value_list.editItem(item)

    def add_value(self):
        """Add a new empty value to the value list and start editing it."""
        item = self._create_value_item('')
        self.value_list.addItem(item)
        self.value_list.setCurrentItem(item)
        self.value_list.editItem(item)

    def add_or_edit_value(self):
        """Add a new value or edit the last value if it's empty."""
        last_item = self.value_list.item(self.value_list.count() - 1)
        # Edit the last item, if it is empty, or add a new empty item
        if last_item and not last_item.text():
            self.value_list.setCurrentItem(last_item)
            self.edit_value()
        else:
            self.add_value()

    def _group(self, is_grouped):
        """Set the grouped state of the tag editor.

        Args:
            is_grouped: Whether the tag is in a grouped state
        """
        self.is_grouped = is_grouped
        self.ui.add_value.setEnabled(not is_grouped)

    def remove_value(self):
        """Remove the currently selected value from the list."""
        value_list = self.value_list
        row = value_list.currentRow()
        if row == 0 and self.is_grouped:
            self._group(False)
        value_list.takeItem(row)

    def on_rows_inserted(self, parent, first, last):
        for row in range(first, last + 1):
            item = self.value_list.item(row)
            self._current_tag_values().insert(row, item.text())

    def on_rows_removed(self, parent, first, last):
        for row in range(first, last + 1):
            del self._current_tag_values()[row]

    def on_rows_moved(self, parent, start, end, destination, row):
        modified_tag = self._current_tag_values()
        moved_values = modified_tag[start:end + 1]
        del modified_tag[start:end + 1]
        for value in reversed(moved_values):
            modified_tag.insert(row, value)

    def move_row_up(self):
        """Move the currently selected row up in the list."""
        row = self.value_list.currentRow()
        if row > 0:
            self._move_row(row, -1)

    def move_row_down(self):
        """Move the currently selected row down in the list."""
        row = self.value_list.currentRow()
        if row + 1 < self.value_list.count():
            self._move_row(row, 1)

    def _move_row(self, row, direction):
        """Move a row in the value list up or down.

        Args:
            row: The index of the row to move
            direction: The direction to move the row (-1 for up, 1 for down)
        """
        value_list = self.value_list
        item = value_list.takeItem(row)
        new_row = row + direction
        value_list.insertItem(new_row, item)
        value_list.setCurrentRow(new_row)

    def _set_ui_enabled_state(self, enabled):
        """Enable or disable the tag value editing UI components.

        Args:
            enabled: Whether to enable the components (boolean)
        """
        if not enabled:
            self.value_list.clear()
        self.value_list.setEnabled(enabled)
        self.ui.add_value.setEnabled(enabled)

    def _get_tag_values(self):
        """Get the current values for the selected tag.

        Returns:
            List of tag values
        """
        values = self.modified_tags.get(self.tag, None)
        if values is None:
            new_tags = self.metadata_box.tag_diff.new
            display_value = new_tags.display_value(self.tag)
            if display_value.is_grouped:
                # grouped values have a special text, which isn't a valid tag value
                values = [display_value.text]
                self._group(True)
            else:
                # normal tag values
                values = new_tags[self.tag]
                self._group(False)
        return values

    def _update_tag_values(self, values):
        """Update the value list with the given tag values.

        Args:
            values: List of tag values to display
        """
        with temporary_disconnect(self.value_list.model().rowsInserted, self.on_rows_inserted):
            self._add_value_items(values)
        self.value_list.setCurrentItem(self.value_list.item(0), QtCore.QItemSelectionModel.SelectionFlag.SelectCurrent)

    def _update_tag_combobox(self, tag):
        """Update the tag combobox with the current tag.

        Args:
            tag: The tag to update in the combobox
        """
        tag_names = self.ui.tag_names
        line_edit = tag_names.lineEdit()
        cursor_pos = line_edit.cursorPosition()
        flags = QtCore.Qt.MatchFlag.MatchFixedString | QtCore.Qt.MatchFlag.MatchCaseSensitive

        # if the previous tag was new and has no value, remove it from the QComboBox.
        # e.g. typing "XYZ" should not leave "X" or "XY" in the QComboBox.
        if self._current_tag_is_transient():
            tag_names.removeItem(tag_names.findText(self.tag, flags))

        row = tag_names.findText(tag, flags)
        self.tag = tag
        if row <= 0:
            if tag:
                # add custom tags to the QComboBox immediately
                tag_names.addItem(tag)
                tag_names.model().sort(0)
                row = tag_names.findText(tag, flags)
            else:
                # the QLineEdit is empty, disable everything
                self._set_ui_enabled_state(False)
                tag_names.setCurrentIndex(0)
                return

        self._set_ui_enabled_state(True)
        tag_names.setCurrentIndex(row)
        line_edit.setCursorPosition(cursor_pos)

    def tag_changed(self, tag):
        """Handle changes to the selected tag.

        Args:
            tag: The tag name
        """
        if self._updating_tag:
            return

        self._updating_tag = True
        try:
            with temporary_disconnect(self.ui.tag_names.editTextChanged, self.tag_changed):
                self._update_tag_combobox(tag)
                self.value_list.clear()
                values = self._get_tag_values()
                self._update_tag_values(values)
        finally:
            self._updating_tag = False

    def _set_item_style(self, item):
        """Set the visual style of a list item based on its grouped state.

        Args:
            item: The QListWidgetItem to style
        """
        font = item.font()
        font.setItalic(self.is_grouped)
        item.setFont(font)

    def _create_value_item(self, value):
        """Create a QListWidgetItem for the given tag value.

        Args:
            value: The tag value to display in the item

        Returns:
            QListWidgetItem: Configured list item
        """
        item = QtWidgets.QListWidgetItem(value)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
                      | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
        self._set_item_style(item)
        return item

    def _add_value_items(self, values):
        """Add items to the value list for the given tag values.

        Args:
            values: List of tag values to add
        """
        for value in values:
            item = self._create_value_item(value)
            self.value_list.addItem(item)

    def value_edited(self, item):
        """Handle editing of a value in the list.

        Args:
            item: The QListWidgetItem that was edited
        """
        row = self.value_list.row(item)
        value = item.text()
        if row == 0 and self.is_grouped:
            self.modified_tags[self.tag] = [value]
            self._group(False)
            self._set_item_style(item)
        else:
            self._current_tag_values()[row] = value
            # add tags to the completer model once they get values
            cm = self.completer.model()
            if self.tag not in cm.stringList():
                cm.insertRows(0, 1)
                cm.setData(cm.index(0, 0), self.tag)
                cm.sort(0)

    def _update_button_states(self, enabled):
        """Update the state of value-related action buttons.

        Args:
            enabled: Whether items should be enabled (boolean)
        """
        self.ui.edit_value.setEnabled(enabled)
        self.ui.remove_value.setEnabled(enabled)
        self.ui.move_value_up.setEnabled(enabled)
        self.ui.move_value_down.setEnabled(enabled)

    def value_selection_changed(self):
        """Handle changes to the value list selection."""
        enabled = bool(self.value_list.selectedItems())
        self._update_button_states(enabled)

    def _current_tag_values(self):
        """Get or create the list of modified values for the current tag.

        Returns:
            List of modified tag values, with at least one empty string if no values exist
        """
        return self.modified_tags.setdefault(
            self.tag,
            list(self.metadata_box.tag_diff.new[self.tag])
        )

    def _current_tag_is_transient(self):
        """Check if the current tag is a custom tag that can be removed from
        the list of tags if empty.
        """
        return (self.tag and self.tag not in self.default_tags
                and not any(self._current_tag_values()))

    def _modified_tags_without_empty_values(self):
        """Generate each modified tag and its non-empty values."""
        for tag, values in self.modified_tags.items():
            yield (tag, [v for v in values if v])

    def _update_metadata_with_modified_tags(self):
        """Update the metadata of all objects with the modified tags."""
        self._metadata_mutex.lock()
        try:
            for obj in self.metadata_box.objects:
                obj.metadata.update(self._modified_tags_without_empty_values())
                obj.update()
        finally:
            self._metadata_mutex.unlock()

    def accept(self):
        """Save the modified tags and close the dialog."""
        with self.tagger.window.ignore_selection_changes:
            self._update_metadata_with_modified_tags()
        super().accept()
