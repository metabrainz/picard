# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2009, 2019-2022 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2013, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018, 2020-2021 Laurent Monin
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

from PyQt5 import (
    QtCore,
    QtWidgets,
)
from PyQt5.QtCore import QStandardPaths

from picard.config import (
    BoolOption,
    TextOption,
    get_config,
)
from picard.const import UI_LANGUAGES
from picard.const.sys import IS_MACOS
from picard.util import strxfrm

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


_default_starting_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)


class InterfaceOptionsPage(OptionsPage):

    NAME = "interface"
    TITLE = N_("User Interface")
    PARENT = None
    SORT_ORDER = 80
    ACTIVE = True
    HELP_URL = '/config/options_interface.html'

    options = [
        BoolOption("setting", "toolbar_show_labels", True),
        BoolOption("setting", "toolbar_multiselect", False),
        BoolOption("setting", "show_menu_icons", True if not IS_MACOS else False),  # On macOS it is not common that the global menu shows icons
        BoolOption("setting", "builtin_search", True),
        BoolOption("setting", "use_adv_search_syntax", False),
        BoolOption("setting", "quit_confirmation", True),
        TextOption("setting", "ui_language", ""),
        TextOption("setting", "ui_theme", str(UiTheme.DEFAULT)),
        BoolOption("setting", "filebrowser_horizontal_autoscroll", True),
        BoolOption("setting", "starting_directory", False),
        TextOption("setting", "starting_directory_path", _default_starting_dir),
        TextOption("setting", "load_image_behavior", "append"),
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
            self.ui.ui_theme.setItemData(idx, _(desc), QtCore.Qt.ItemDataRole.ToolTipRole)
        self.ui.ui_theme.setCurrentIndex(self.ui.ui_theme.findData(UiTheme.DEFAULT))

        self.ui.ui_language.addItem(_('System default'), '')
        language_list = [(lang[0], lang[1], _(lang[2])) for lang in UI_LANGUAGES]

        def fcmp(x):
            return strxfrm(x[2])
        for lang_code, native, translation in sorted(language_list, key=fcmp):
            if native and native != translation:
                name = '%s (%s)' % (translation, native)
            else:
                name = translation
            self.ui.ui_language.addItem(name, lang_code)
        self.ui.starting_directory.toggled.connect(
            self.ui.starting_directory_path.setEnabled
        )
        self.ui.starting_directory.toggled.connect(
            self.ui.starting_directory_browse.setEnabled
        )
        self.ui.starting_directory_browse.clicked.connect(self.starting_directory_browse)

        if not OS_SUPPORTS_THEMES:
            self.ui.ui_theme_container.hide()

    def load(self):
        config = get_config()
        self.ui.toolbar_show_labels.setChecked(config.setting["toolbar_show_labels"])
        self.ui.toolbar_multiselect.setChecked(config.setting["toolbar_multiselect"])
        self.ui.show_menu_icons.setChecked(config.setting["show_menu_icons"])
        self.ui.builtin_search.setChecked(config.setting["builtin_search"])
        self.ui.use_adv_search_syntax.setChecked(config.setting["use_adv_search_syntax"])
        self.ui.quit_confirmation.setChecked(config.setting["quit_confirmation"])
        current_ui_language = config.setting["ui_language"]
        self.ui.ui_language.setCurrentIndex(self.ui.ui_language.findData(current_ui_language))
        self.ui.filebrowser_horizontal_autoscroll.setChecked(config.setting["filebrowser_horizontal_autoscroll"])
        self.ui.starting_directory.setChecked(config.setting["starting_directory"])
        self.ui.starting_directory_path.setText(config.setting["starting_directory_path"])
        current_theme = UiTheme(config.setting["ui_theme"])
        self.ui.ui_theme.setCurrentIndex(self.ui.ui_theme.findData(current_theme))

    def save(self):
        config = get_config()
        config.setting["toolbar_show_labels"] = self.ui.toolbar_show_labels.isChecked()
        config.setting["toolbar_multiselect"] = self.ui.toolbar_multiselect.isChecked()
        config.setting["show_menu_icons"] = self.ui.show_menu_icons.isChecked()
        self.tagger.enable_menu_icons(config.setting["show_menu_icons"])
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
                QtWidgets.QMessageBox.Icon.Information,
                restart_warning_title,
                restart_warning,
                QtWidgets.QMessageBox.StandardButton.Ok,
                self)
            dialog.exec_()
        config.setting["ui_theme"] = new_theme_setting
        config.setting["ui_language"] = self.ui.ui_language.itemData(self.ui.ui_language.currentIndex())
        config.setting["filebrowser_horizontal_autoscroll"] = self.ui.filebrowser_horizontal_autoscroll.isChecked()
        config.setting["starting_directory"] = self.ui.starting_directory.isChecked()
        config.setting["starting_directory_path"] = os.path.normpath(self.ui.starting_directory_path.text())

    def starting_directory_browse(self):
        item = self.ui.starting_directory_path
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "", item.text())
        if path:
            path = os.path.normpath(path)
            item.setText(path)


register_options_page(InterfaceOptionsPage)
