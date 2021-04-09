# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2009, 2019-2020 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2013, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018 Laurent Monin
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


from functools import partial
import locale
import os.path

from PyQt5 import (
    QtCore,
    QtWidgets,
)
from PyQt5.QtCore import QStandardPaths

from picard.config import (
    BoolOption,
    ListOption,
    TextOption,
    get_config,
)
from picard.const import UI_LANGUAGES
from picard.util import icontheme

from picard.ui import PicardDialog
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.theme import (
    AVAILABLE_UI_THEMES,
    OS_SUPPORTS_THEMES,
    UiTheme,
)
from picard.ui.ui_options_interface import Ui_InterfaceOptionsPage
from picard.ui.util import enabledSlot


_default_starting_dir = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)


class InterfaceOptionsPage(OptionsPage):

    NAME = "interface"
    TITLE = N_("User Interface")
    PARENT = None
    SORT_ORDER = 80
    ACTIVE = True
    HELP_URL = '/config/options_interface.html'
    SEPARATOR = '—' * 5
    TOOLBAR_BUTTONS = {
        'add_directory_action': {
            'label': N_('Add Folder'),
            'icon': 'folder'
        },
        'add_files_action': {
            'label': N_('Add Files'),
            'icon': 'document-open'
        },
        'cluster_action': {
            'label': N_('Cluster'),
            'icon': 'picard-cluster'
        },
        'autotag_action': {
            'label': N_('Lookup'),
            'icon': 'picard-auto-tag'
        },
        'analyze_action': {
            'label': N_('Scan'),
            'icon': 'picard-analyze'
        },
        'browser_lookup_action': {
            'label': N_('Lookup in Browser'),
            'icon': 'lookup-musicbrainz'
        },
        'save_action': {
            'label': N_('Save'),
            'icon': 'document-save'
        },
        'view_info_action': {
            'label': N_('Info'),
            'icon': 'picard-edit-tags'
        },
        'remove_action': {
            'label': N_('Remove'),
            'icon': 'list-remove'
        },
        'submit_acoustid_action': {
            'label': N_('Submit AcoustIDs'),
            'icon': 'acoustid-fingerprinter'
        },
        'generate_fingerprints_action': {
            'label': N_("Generate Fingerprints"),
            'icon': 'fingerprint'
        },
        'play_file_action': {
            'label': N_('Open in Player'),
            'icon': 'play-music'
        },
        'cd_lookup_action': {
            'label': N_('Lookup CD...'),
            'icon': 'media-optical'
        },
        'tags_from_filenames_action': {
            'label': N_('Parse File Names...'),
            'icon': 'picard-tags-from-filename'
        },
    }
    ACTION_NAMES = set(TOOLBAR_BUTTONS.keys())
    options = [
        BoolOption("setting", "toolbar_show_labels", True),
        BoolOption("setting", "toolbar_multiselect", False),
        BoolOption("setting", "builtin_search", True),
        BoolOption("setting", "use_adv_search_syntax", False),
        BoolOption("setting", "quit_confirmation", True),
        TextOption("setting", "ui_language", ""),
        TextOption("setting", "ui_theme", str(UiTheme.DEFAULT)),
        BoolOption("setting", "filebrowser_horizontal_autoscroll", True),
        BoolOption("setting", "starting_directory", False),
        TextOption("setting", "starting_directory_path", _default_starting_dir),
        TextOption("setting", "load_image_behavior", "append"),
        ListOption("setting", "toolbar_layout", [
            'add_directory_action',
            'add_files_action',
            'separator',
            'cluster_action',
            'separator',
            'autotag_action',
            'analyze_action',
            'browser_lookup_action',
            'separator',
            'save_action',
            'view_info_action',
            'remove_action',
            'separator',
            'cd_lookup_action',
            'separator',
            'submit_acoustid_action',
        ]),
    ]

    # Those are labels for theme display
    _UI_THEME_LABELS = {
        UiTheme.DEFAULT: {
            'label': N_('Default'),
            'desc': N_('The default color scheme based on the operating system display settings'),
        },
        UiTheme.DARK: {
            'label': N_('Dark'),
            'desc': N_('A dark display theme'),
        },
        UiTheme.LIGHT: {
            'label': N_('Light'),
            'desc': N_('A light display theme'),
        },
        UiTheme.SYSTEM: {
            'label': N_('System'),
            'desc': N_('The Qt5 theme configured in the desktop environment'),
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_InterfaceOptionsPage()
        self.ui.setupUi(self)

        self.ui.ui_theme.clear()
        for theme in AVAILABLE_UI_THEMES:
            label = self._UI_THEME_LABELS[theme]['label']
            desc = self._UI_THEME_LABELS[theme]['desc']
            self.ui.ui_theme.addItem(_(label), theme)
            idx = self.ui.ui_theme.findData(theme)
            self.ui.ui_theme.setItemData(idx, _(desc), QtCore.Qt.ToolTipRole)
        self.ui.ui_theme.setCurrentIndex(self.ui.ui_theme.findData(UiTheme.DEFAULT))

        self.ui.ui_language.addItem(_('System default'), '')
        language_list = [(lang[0], lang[1], _(lang[2])) for lang in UI_LANGUAGES]

        def fcmp(x):
            return locale.strxfrm(x[2])
        for lang_code, native, translation in sorted(language_list, key=fcmp):
            if native and native != translation:
                name = '%s (%s)' % (translation, native)
            else:
                name = translation
            self.ui.ui_language.addItem(name, lang_code)
        self.ui.starting_directory.stateChanged.connect(
            partial(
                enabledSlot,
                self.ui.starting_directory_path.setEnabled
            )
        )
        self.ui.starting_directory.stateChanged.connect(
            partial(
                enabledSlot,
                self.ui.starting_directory_browse.setEnabled
            )
        )
        self.ui.starting_directory_browse.clicked.connect(self.starting_directory_browse)
        self.ui.add_button.clicked.connect(self.add_to_toolbar)
        self.ui.insert_separator_button.clicked.connect(self.insert_separator)
        self.ui.remove_button.clicked.connect(self.remove_action)
        self.move_view = MoveableListView(self.ui.toolbar_layout_list, self.ui.up_button,
                                          self.ui.down_button, self.update_action_buttons)
        self.update_buttons = self.move_view.update_buttons

        if not OS_SUPPORTS_THEMES:
            self.ui.ui_theme_container.hide()

    def load(self):
        config = get_config()
        self.ui.toolbar_show_labels.setChecked(config.setting["toolbar_show_labels"])
        self.ui.toolbar_multiselect.setChecked(config.setting["toolbar_multiselect"])
        self.ui.builtin_search.setChecked(config.setting["builtin_search"])
        self.ui.use_adv_search_syntax.setChecked(config.setting["use_adv_search_syntax"])
        self.ui.quit_confirmation.setChecked(config.setting["quit_confirmation"])
        current_ui_language = config.setting["ui_language"]
        self.ui.ui_language.setCurrentIndex(self.ui.ui_language.findData(current_ui_language))
        self.ui.filebrowser_horizontal_autoscroll.setChecked(config.setting["filebrowser_horizontal_autoscroll"])
        self.ui.starting_directory.setChecked(config.setting["starting_directory"])
        self.ui.starting_directory_path.setText(config.setting["starting_directory_path"])
        self.populate_action_list()
        self.ui.toolbar_layout_list.setCurrentRow(0)
        current_theme = UiTheme(config.setting["ui_theme"])
        self.ui.ui_theme.setCurrentIndex(self.ui.ui_theme.findData(current_theme))
        self.update_buttons()

    def save(self):
        config = get_config()
        config.setting["toolbar_show_labels"] = self.ui.toolbar_show_labels.isChecked()
        config.setting["toolbar_multiselect"] = self.ui.toolbar_multiselect.isChecked()
        config.setting["builtin_search"] = self.ui.builtin_search.isChecked()
        config.setting["use_adv_search_syntax"] = self.ui.use_adv_search_syntax.isChecked()
        config.setting["quit_confirmation"] = self.ui.quit_confirmation.isChecked()
        self.tagger.window.update_toolbar_style()
        new_theme_setting = str(self.ui.ui_theme.itemData(self.ui.ui_theme.currentIndex()))
        new_language = self.ui.ui_language.itemData(self.ui.ui_language.currentIndex())
        restart_warning = None
        if new_theme_setting != config.setting["ui_theme"]:
            restart_warning_title = _('Theme changed')
            restart_warning = _('You have changed the application theme. You have to restart Picard in order for the change to take effect.')
            if new_theme_setting == str(UiTheme.SYSTEM):
                restart_warning += '\n\n' + _(
                    'Please note that using the system theme might cause the user interface to be not shown correctly. '
                    'If this is the case select the "Default" theme option to use Picard\'s default theme again.'
                )
        elif new_language != config.setting["ui_language"]:
            restart_warning_title = _('Language changed')
            restart_warning = _('You have changed the interface language. You have to restart Picard in order for the change to take effect.')
        if restart_warning:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                restart_warning_title,
                restart_warning,
                QtWidgets.QMessageBox.Ok,
                self)
            dialog.exec_()
        config.setting["ui_theme"] = new_theme_setting
        config.setting["ui_language"] = self.ui.ui_language.itemData(self.ui.ui_language.currentIndex())
        config.setting["filebrowser_horizontal_autoscroll"] = self.ui.filebrowser_horizontal_autoscroll.isChecked()
        config.setting["starting_directory"] = self.ui.starting_directory.isChecked()
        config.setting["starting_directory_path"] = os.path.normpath(self.ui.starting_directory_path.text())
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

    def _get_icon_from_name(self, name):
        return self.TOOLBAR_BUTTONS[name]['icon']

    def _insert_item(self, action, index=None):
        list_item = ToolbarListItem(action)
        list_item.setToolTip(_('Drag and Drop to re-order'))
        if action in self.TOOLBAR_BUTTONS:
            # TODO: Remove temporary workaround once https://github.com/python-babel/babel/issues/415 has been resolved.
            babel_415_workaround = self.TOOLBAR_BUTTONS[action]['label']
            list_item.setText(_(babel_415_workaround))
            list_item.setIcon(icontheme.lookup(self._get_icon_from_name(action), icontheme.ICON_SIZE_MENU))
        else:
            list_item.setText(self.SEPARATOR)
        if index is not None:
            self.ui.toolbar_layout_list.insertItem(index, list_item)
        else:
            self.ui.toolbar_layout_list.addItem(list_item)
        return list_item

    def _all_list_items(self):
        return [self.ui.toolbar_layout_list.item(i).action_name
                for i in range(self.ui.toolbar_layout_list.count())]

    def _added_actions(self):
        actions = self._all_list_items()
        return set(action for action in actions if action != 'separator')

    def populate_action_list(self):
        self.ui.toolbar_layout_list.clear()
        config = get_config()
        for name in config.setting['toolbar_layout']:
            if name in self.ACTION_NAMES or name == 'separator':
                self._insert_item(name)

    def update_action_buttons(self):
        self.ui.add_button.setEnabled(self._added_actions() != self.ACTION_NAMES)

    def add_to_toolbar(self):
        display_list = set.difference(self.ACTION_NAMES, self._added_actions())
        selected_action, ok = AddActionDialog.get_selected_action(display_list, self)
        if ok:
            list_item = self._insert_item(selected_action, self.ui.toolbar_layout_list.currentRow() + 1)
            self.ui.toolbar_layout_list.setCurrentItem(list_item)
        self.update_buttons()

    def insert_separator(self):
        insert_index = self.ui.toolbar_layout_list.currentRow() + 1
        self._insert_item('separator', insert_index)

    def remove_action(self):
        item = self.ui.toolbar_layout_list.takeItem(self.ui.toolbar_layout_list.currentRow())
        del item
        self.update_buttons()

    def update_layout_config(self):
        config = get_config()
        config.setting['toolbar_layout'] = self._all_list_items()
        self._update_toolbar()

    def _update_toolbar(self):
        widget = self.parent()
        while not isinstance(widget, QtWidgets.QMainWindow):
            widget = widget.parent()
        # Call the main window's create toolbar method
        widget.create_action_toolbar()
        widget.set_tab_order()


class ToolbarListItem(QtWidgets.QListWidgetItem):
    def __init__(self, action_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_name = action_name


class AddActionDialog(PicardDialog):
    def __init__(self, action_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowModality(QtCore.Qt.WindowModal)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

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
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_action(self):
        return self.action_list[self.combo_box.currentIndex()][1]

    @staticmethod
    def get_selected_action(action_list, parent=None):
        dialog = AddActionDialog(action_list, parent)
        result = dialog.exec_()
        selected_action = dialog.selected_action()
        return (selected_action, result == QtWidgets.QDialog.Accepted)


register_options_page(InterfaceOptionsPage)
