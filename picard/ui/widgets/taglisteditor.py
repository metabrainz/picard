# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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

from picard.util.tags import (
    TAG_NAMES,
    display_tag_name,
)

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
        model = TagListModel()
        list_view.setModel(model)
        list_view.setItemDelegate(AutocompleteItemDelegate(
            sorted(TAG_NAMES.keys())))

        selection = list_view.selectionModel()
        selection.selectionChanged.connect(self.on_selection_changed)
        self.on_selection_changed([], [])

    def on_selection_changed(self, selected, deselected):
        buttons_enabled = len(self.ui.tag_list_view.selectedIndexes()) > 0
        self.ui.tags_remove_btn.setEnabled(buttons_enabled)
        self.ui.tags_move_up_btn.setEnabled(buttons_enabled)
        self.ui.tags_move_down_btn.setEnabled(buttons_enabled)

    def clear(self):
        self.ui.tag_list_view.update([])

    def update(self, tags):
        self.ui.tag_list_view.update(tags)

    @property
    def tags(self):
        return self.ui.tag_list_view.tags


class TagListModel(EditableListModel):
    def get_display_name(self, item):
        return display_tag_name(item)
