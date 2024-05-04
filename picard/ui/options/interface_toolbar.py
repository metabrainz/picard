# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2009, 2019-2023 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2013, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2018 Bob Swift
# Copyright (C) 2021 Gabriel Ferreira
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


import os.path

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import icontheme

from picard.ui import PicardDialog
from picard.ui.mainwindow_actions import MainAction
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_interface_toolbar import (
    Ui_InterfaceToolbarOptionsPage,
)
from picard.ui.util import qlistwidget_items


class InterfaceToolbarOptionsPage(OptionsPage):

    NAME = 'interface_toolbar'
    TITLE = N_("Action Toolbar")
    PARENT = 'interface'
    SORT_ORDER = 60
    ACTIVE = True
    HELP_URL = "/config/options_interface_toolbar.html"
    SEPARATOR = '—' * 5
    TOOLBAR_BUTTONS = {
        MainAction.ADD_DIRECTORY: {
            'label': N_("Add Folder"),
            'icon': 'folder'
        },
        MainAction.ADD_FILES: {
            'label': N_("Add Files"),
            'icon': 'document-open'
        },
        MainAction.CLUSTER: {
            'label': N_("Cluster"),
            'icon': 'picard-cluster'
        },
        MainAction.AUTOTAG: {
            'label': N_("Lookup"),
            'icon': 'picard-auto-tag'
        },
        MainAction.ANALYZE: {
            'label': N_("Scan"),
            'icon': 'picard-analyze'
        },
        MainAction.BROWSER_LOOKUP: {
            'label': N_("Lookup in Browser"),
            'icon': 'lookup-musicbrainz'
        },
        MainAction.SAVE: {
            'label': N_("Save"),
            'icon': 'document-save'
        },
        MainAction.VIEW_INFO: {
            'label': N_("Info"),
            'icon': 'picard-edit-tags'
        },
        MainAction.REMOVE: {
            'label': N_("Remove"),
            'icon': 'list-remove'
        },
        MainAction.SUBMIT_ACOUSTID: {
            'label': N_("Submit AcoustIDs"),
            'icon': 'acoustid-fingerprinter'
        },
        MainAction.GENERATE_FINGERPRINTS: {
            'label': N_("Generate Fingerprints"),
            'icon': 'fingerprint'
        },
        MainAction.PLAY_FILE: {
            'label': N_("Open in Player"),
            'icon': 'play-music'
        },
        MainAction.CD_LOOKUP: {
            'label': N_("Lookup CD…"),
            'icon': 'media-optical'
        },
        MainAction.TAGS_FROM_FILENAMES: {
            'label': N_("Parse File Names…"),
            'icon': 'picard-tags-from-filename'
        },
        MainAction.SIMILAR_ITEMS_SEARCH: {
            'label': N_("Similar items"),
            'icon': 'system-search'
        },
    }
    ACTION_IDS = set(TOOLBAR_BUTTONS)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_InterfaceToolbarOptionsPage()
        self.ui.setupUi(self)

        self.ui.add_button.clicked.connect(self.add_to_toolbar)
        self.ui.insert_separator_button.clicked.connect(self.insert_separator)
        self.ui.remove_button.clicked.connect(self.remove_action)
        self.move_view = MoveableListView(self.ui.toolbar_layout_list, self.ui.up_button,
                                          self.ui.down_button, self.update_action_buttons)
        self.update_buttons = self.move_view.update_buttons

        self.register_setting('toolbar_layout', ['toolbar_layout_list'])

    def load(self):
        self.populate_action_list()
        self.ui.toolbar_layout_list.setCurrentRow(0)
        self.update_buttons()

    def save(self):
        self.tagger.window.update_toolbar_style()
        self.update_layout_config()

    def restore_defaults(self):
        super().restore_defaults()
        self.update_buttons()

    def starting_directory_browse(self):
        item = self.ui.starting_directory_path
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "", item.text())
        if path:
            path = os.path.normpath(path)
            item.setText(path)

    def _get_icon_from_action_id(self, action_id):
        return self.TOOLBAR_BUTTONS[action_id]['icon']

    def _insert_item(self, data, index=None):
        list_item = QtWidgets.QListWidgetItem()
        list_item.setToolTip(_("Drag and Drop to re-order"))
        if isinstance(data, MainAction) and data in self.TOOLBAR_BUTTONS:
            action_id = data
            # TODO: Remove temporary workaround once https://github.com/python-babel/babel/issues/415 has been resolved.
            babel_415_workaround = self.TOOLBAR_BUTTONS[action_id]['label']
            list_item.setText(_(babel_415_workaround))
            list_item.setIcon(icontheme.lookup(self._get_icon_from_action_id(action_id), icontheme.ICON_SIZE_MENU))
            list_item.setData(QtCore.Qt.ItemDataRole.UserRole, action_id)
        else:
            list_item.setText(self.SEPARATOR)
            list_item.setData(QtCore.Qt.ItemDataRole.UserRole, 'separator')
        if index is not None:
            self.ui.toolbar_layout_list.insertItem(index, list_item)
        else:
            self.ui.toolbar_layout_list.addItem(list_item)
        return list_item

    def _itemlist_datas(self):
        for item in qlistwidget_items(self.ui.toolbar_layout_list):
            yield item.data(QtCore.Qt.ItemDataRole.UserRole)

    def _added_actions(self):
        return set(data for data in self._itemlist_datas() if isinstance(data, MainAction))

    def populate_action_list(self):
        self.ui.toolbar_layout_list.clear()
        config = get_config()
        for name in config.setting['toolbar_layout']:
            if name == 'separator':
                self._insert_item(name)
            else:
                try:
                    action_id = MainAction(name)
                    if action_id in self.ACTION_IDS:
                        self._insert_item(action_id)
                except ValueError as e:
                    log.debug(e)

    def update_action_buttons(self):
        self.ui.add_button.setEnabled(self._added_actions() != self.ACTION_IDS)

    def add_to_toolbar(self):
        display_list = set.difference(self.ACTION_IDS, self._added_actions())
        selected_action, ok = AddActionDialog.get_selected_action(display_list, self)
        if ok:
            insert_index = self.ui.toolbar_layout_list.currentRow() + 1
            list_item = self._insert_item(selected_action, index=insert_index)
            self.ui.toolbar_layout_list.setCurrentItem(list_item)
        self.update_buttons()

    def insert_separator(self):
        insert_index = self.ui.toolbar_layout_list.currentRow() + 1
        self._insert_item('separator', index=insert_index)

    def remove_action(self):
        item = self.ui.toolbar_layout_list.takeItem(self.ui.toolbar_layout_list.currentRow())
        del item
        self.update_buttons()

    def _data2layout(self):
        for data in self._itemlist_datas():
            if isinstance(data, MainAction):
                yield data.value
            else:
                yield data

    def update_layout_config(self):
        config = get_config()
        config.setting['toolbar_layout'] = list(self._data2layout())
        self._update_toolbar()

    def _update_toolbar(self):
        widget = self.parent()
        while not isinstance(widget, QtWidgets.QMainWindow):
            widget = widget.parent()
        # Call the main window's create toolbar method
        widget.create_action_toolbar()
        widget.update_toolbar_style()
        widget.set_tab_order()


class AddActionDialog(PicardDialog):
    def __init__(self, action_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)

        # TODO: Remove temporary workaround once https://github.com/python-babel/babel/issues/415 has been resolved.
        babel_415_workaround_list = []
        for action in action_list:
            babel_415_workaround = self.parent().TOOLBAR_BUTTONS[action]['label']
            babel_415_workaround_list.append([_(babel_415_workaround), action])
        self.action_list = sorted(babel_415_workaround_list)

        self.combo_box = QtWidgets.QComboBox(self)
        self.combo_box.addItems([label for label, action in self.action_list])
        layout.addWidget(self.combo_box)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            QtCore.Qt.Orientation.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_action(self):
        return self.action_list[self.combo_box.currentIndex()][1]

    @staticmethod
    def get_selected_action(action_list, parent=None):
        dialog = AddActionDialog(action_list, parent)
        result = dialog.exec()
        selected_action = dialog.selected_action()
        return (selected_action, result == QtWidgets.QDialog.DialogCode.Accepted)


register_options_page(InterfaceToolbarOptionsPage)
