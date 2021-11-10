# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
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


from PyQt5 import QtWidgets

from picard.util.tags import TAG_NAMES

from picard.ui.ui_widget_taglisteditor import Ui_TagListEditor
from picard.ui.widgets.editablelistview import (
    AutocompleteItemDelegate,
    EditableListModel,
)


class TagListEditor(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_TagListEditor()
        self.ui.setupUi(self)
        list_view = self.ui.tag_list_view
        model = EditableListModel()
        model.user_sortable_changed.connect(self.on_user_sortable_changed)
        self.ui.sort_buttons.setVisible(model.user_sortable)
        list_view.setModel(model)
        list_view.setItemDelegate(AutocompleteItemDelegate(
            sorted(TAG_NAMES.keys())))

        selection = list_view.selectionModel()
        selection.selectionChanged.connect(self.on_selection_changed)
        self.on_selection_changed([], [])

    def on_selection_changed(self, selected, deselected):
        indexes = self.ui.tag_list_view.selectedIndexes()
        last_row = self.ui.tag_list_view.model().rowCount() - 1
        buttons_enabled = len(indexes) > 0
        move_up_enabled = buttons_enabled and all(i.row() != 0 for i in indexes)
        move_down_enabled = buttons_enabled and all(i.row() != last_row for i in indexes)
        self.ui.tags_remove_btn.setEnabled(buttons_enabled)
        self.ui.tags_move_up_btn.setEnabled(move_up_enabled)
        self.ui.tags_move_down_btn.setEnabled(move_down_enabled)

    def clear(self):
        self.ui.tag_list_view.update([])

    def update(self, tags):
        self.ui.tag_list_view.update(tags)

    @property
    def tags(self):
        return self.ui.tag_list_view.items

    def on_user_sortable_changed(self, user_sortable):
        self.ui.sort_buttons.setVisible(user_sortable)

    def set_user_sortable(self, user_sortable):
        self.ui.tag_list_view.model().user_sortable = user_sortable
