# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2009, 2019-2023 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2013, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2018, 2023-2024 Bob Swift
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

from picard.config import get_config
from picard.const.languages import UI_LANGUAGES
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
    gettext_constants,
)
from picard.util import strxfrm

from picard.ui.forms.ui_options_interface import Ui_InterfaceOptionsPage
from picard.ui.options import OptionsPage
from picard.ui.theme import (
    AVAILABLE_UI_THEMES,
    OS_SUPPORTS_THEMES,
    UiTheme,
)
from picard.ui.util import changes_require_restart_warning


class InterfaceOptionsPage(OptionsPage):

    NAME = 'interface'
    TITLE = N_("User Interface")
    PARENT = None
    SORT_ORDER = 80
    ACTIVE = True
    HELP_URL = "/config/options_interface.html"

    # Those are labels for theme display
    _UI_THEME_LABELS = {
        UiTheme.DEFAULT: {
            'label': N_("Default"),
            'desc': N_("The default color scheme based on the operating system display settings"),
        },
        UiTheme.DARK: {
            'label': N_("Dark"),
            'desc': N_("A dark display theme"),
        },
        UiTheme.LIGHT: {
            'label': N_("Light"),
            'desc': N_("A light display theme"),
        },
        UiTheme.SYSTEM: {
            'label': N_("System"),
            'desc': N_("The Qt6 theme configured in the desktop environment"),
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
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

        self.ui.ui_language.addItem(_("System default"), '')
        language_list = [(lang[0], lang[1], gettext_constants(lang[2])) for lang in UI_LANGUAGES]

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

        self.ui.allow_multi_dirs_selection.stateChanged.connect(self.multi_selection_warning)

        self.register_setting('toolbar_show_labels', ['toolbar_show_labels'])
        self.register_setting('show_menu_icons', ['show_menu_icons'])
        self.register_setting('ui_language', ['ui_language', 'label'])
        self.register_setting('ui_theme', ['ui_theme', 'label_theme'])
        self.register_setting('allow_multi_dirs_selection', ['allow_multi_dirs_selection'])
        self.register_setting('builtin_search', ['builtin_search'])
        self.register_setting('use_adv_search_syntax', ['use_adv_search_syntax'])
        self.register_setting('show_new_user_dialog', ['new_user_dialog'])
        self.register_setting('quit_confirmation', ['quit_confirmation'])
        self.register_setting('file_save_warning', ['file_save_warning'])
        self.register_setting('filebrowser_horizontal_autoscroll', ['filebrowser_horizontal_autoscroll'])
        self.register_setting('starting_directory', ['starting_directory'])
        self.register_setting('starting_directory_path', ['starting_directory_path'])

    def load(self):
        # Don't display the multi-selection warning when loading values.
        # This is required because loading a different option profile could trigger the warning.
        self.ui.allow_multi_dirs_selection.blockSignals(True)

        config = get_config()
        self.ui.toolbar_show_labels.setChecked(config.setting['toolbar_show_labels'])
        self.ui.allow_multi_dirs_selection.setChecked(config.setting['allow_multi_dirs_selection'])
        self.ui.show_menu_icons.setChecked(config.setting['show_menu_icons'])
        self.ui.builtin_search.setChecked(config.setting['builtin_search'])
        self.ui.use_adv_search_syntax.setChecked(config.setting['use_adv_search_syntax'])
        self.ui.new_user_dialog.setChecked(config.setting['show_new_user_dialog'])
        self.ui.quit_confirmation.setChecked(config.setting['quit_confirmation'])
        self.ui.file_save_warning.setChecked(config.setting['file_save_warning'])
        current_ui_language = config.setting['ui_language']
        self.ui.ui_language.setCurrentIndex(self.ui.ui_language.findData(current_ui_language))
        self.ui.filebrowser_horizontal_autoscroll.setChecked(config.setting['filebrowser_horizontal_autoscroll'])
        self.ui.starting_directory.setChecked(config.setting['starting_directory'])
        self.ui.starting_directory_path.setText(config.setting['starting_directory_path'])
        current_theme = UiTheme(config.setting['ui_theme'])
        self.ui.ui_theme.setCurrentIndex(self.ui.ui_theme.findData(current_theme))

        # re-enable the multi-selection warning
        self.ui.allow_multi_dirs_selection.blockSignals(False)

    def save(self):
        config = get_config()
        config.setting['toolbar_show_labels'] = self.ui.toolbar_show_labels.isChecked()
        config.setting['allow_multi_dirs_selection'] = self.ui.allow_multi_dirs_selection.isChecked()
        config.setting['show_menu_icons'] = self.ui.show_menu_icons.isChecked()
        self.tagger.enable_menu_icons(config.setting['show_menu_icons'])
        config.setting['builtin_search'] = self.ui.builtin_search.isChecked()
        config.setting['use_adv_search_syntax'] = self.ui.use_adv_search_syntax.isChecked()
        config.setting['show_new_user_dialog'] = self.ui.new_user_dialog.isChecked()
        config.setting['quit_confirmation'] = self.ui.quit_confirmation.isChecked()
        config.setting['file_save_warning'] = self.ui.file_save_warning.isChecked()
        self.tagger.window.update_toolbar_style()
        new_theme_setting = str(self.ui.ui_theme.itemData(self.ui.ui_theme.currentIndex()))
        new_language = self.ui.ui_language.itemData(self.ui.ui_language.currentIndex())
        warnings = []
        notes = []
        if new_theme_setting != config.setting['ui_theme']:
            warnings.append(_("You have changed the application theme."))
            if new_theme_setting == str(UiTheme.SYSTEM):
                notes.append(_(
                    'Please note that using the system theme might cause the user interface to be not shown correctly. '
                    'If this is the case select the "Default" theme option to use Picard\'s default theme again.'
                ))
            config.setting['ui_theme'] = new_theme_setting
        if new_language != config.setting['ui_language']:
            config.setting['ui_language'] = new_language
            warnings.append(_("You have changed the interface language."))
        changes_require_restart_warning(self, warnings=warnings, notes=notes)

        config.setting['filebrowser_horizontal_autoscroll'] = self.ui.filebrowser_horizontal_autoscroll.isChecked()
        config.setting['starting_directory'] = self.ui.starting_directory.isChecked()
        config.setting['starting_directory_path'] = os.path.normpath(self.ui.starting_directory_path.text())

    def starting_directory_browse(self):
        item = self.ui.starting_directory_path
        path = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            directory=item.text(),
        )
        if path:
            path = os.path.normpath(path)
            item.setText(path)

    def multi_selection_warning(self):
        if not self.ui.allow_multi_dirs_selection.isChecked():
            return

        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Warning,
            _('Option Setting Warning'),
            _(
                'When enabling the multiple directories option setting Picard will no longer use the system '
                'file picker for selecting directories. This may result in reduced functionality.\n\n'
                'Are you sure that you want to enable this setting?'
            ),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            self)
        if dialog.exec() == QtWidgets.QMessageBox.StandardButton.No:
            self.ui.allow_multi_dirs_selection.setCheckState(QtCore.Qt.CheckState.Unchecked)


register_options_page(InterfaceOptionsPage)
