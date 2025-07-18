# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2009, 2019-2025 Philipp Wolfer
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
import logging

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
    sort_key,
)

from picard.ui.forms.ui_options_interface import Ui_InterfaceOptionsPage
from picard.ui.options import OptionsPage
from picard.ui.theme import (
    AVAILABLE_UI_THEMES,
    OS_SUPPORTS_THEMES,
    UiTheme,
)
from picard.ui.util import (
    FileDialog,
    changes_require_restart_warning,
)


class InterfaceOptionsPage(OptionsPage):
    """
    Options page for configuring the user interface in Picard.
    Provides UI and logic for interface-related settings.
    """

    NAME: str = 'interface'
    TITLE: str = N_("User Interface")
    PARENT: None = None
    SORT_ORDER: int = 80
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_interface.html"

    OPTIONS: tuple[tuple[str, list[str]], ...] = (
        ('toolbar_show_labels', ['toolbar_show_labels']),
        ('show_menu_icons', ['show_menu_icons']),
        ('ui_language', ['ui_language']),
        ('ui_theme', ['ui_theme']),
        ('allow_multi_dirs_selection', ['allow_multi_dirs_selection']),
        ('builtin_search', ['builtin_search']),
        ('use_adv_search_syntax', ['use_adv_search_syntax']),
        ('show_new_user_dialog', ['new_user_dialog']),
        ('quit_confirmation', ['quit_confirmation']),
        ('file_save_warning', ['file_save_warning']),
        ('filebrowser_horizontal_autoscroll', ['filebrowser_horizontal_autoscroll']),
        ('starting_directory', ['starting_directory']),
        ('starting_directory_path', ['starting_directory_path']),
    )

    ui: Ui_InterfaceOptionsPage
    _UI_THEME_LABELS: dict[UiTheme, dict[str, str]]
    logger: logging.Logger

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """
        Initialize the InterfaceOptionsPage, set up the UI and connect logic.
        :param parent: The parent widget (optional).
        Sets up logging for this options page.
        """
        super().__init__(parent=parent)
        self.ui = Ui_InterfaceOptionsPage()
        self.ui.setupUi(self)
        self.logger = logging.getLogger("picard.ui.options.interface")

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

        def fcmp(x: tuple[str, str, str]) -> str:
            """
            Sort key for language list.
            :param x: Tuple containing language code, native name, and translation.
            :return: Sort key string.
            """
            return sort_key(x[2])
        # Add all available UI languages to the dropdown, sorted by translation name
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

    def load(self: "InterfaceOptionsPage") -> None:
        """
        Load current interface settings from the configuration and update the UI accordingly.
        Adds error handling for config access and logs errors.
        """
        self.ui.allow_multi_dirs_selection.blockSignals(True)
        try:
            config = get_config()
            self.ui.toolbar_show_labels.setChecked(config.setting.get('toolbar_show_labels', True))
            self.ui.allow_multi_dirs_selection.setChecked(config.setting.get('allow_multi_dirs_selection', False))
            self.ui.show_menu_icons.setChecked(config.setting.get('show_menu_icons', True))
            self.ui.builtin_search.setChecked(config.setting.get('builtin_search', True))
            self.ui.use_adv_search_syntax.setChecked(config.setting.get('use_adv_search_syntax', False))
            self.ui.new_user_dialog.setChecked(config.setting.get('show_new_user_dialog', True))
            self.ui.quit_confirmation.setChecked(config.setting.get('quit_confirmation', True))
            self.ui.file_save_warning.setChecked(config.setting.get('file_save_warning', True))
            current_ui_language = config.setting.get('ui_language', '')
            self.ui.ui_language.setCurrentIndex(self.ui.ui_language.findData(current_ui_language))
            self.ui.filebrowser_horizontal_autoscroll.setChecked(config.setting.get('filebrowser_horizontal_autoscroll', False))
            self.ui.starting_directory.setChecked(config.setting.get('starting_directory', False))
            self.ui.starting_directory_path.setText(config.setting.get('starting_directory_path', ''))
            current_theme = UiTheme(config.setting.get('ui_theme', str(UiTheme.DEFAULT)))
            self.ui.ui_theme.setCurrentIndex(self.ui.ui_theme.findData(current_theme))
        except Exception as e:
            self.logger.error(f"Error loading interface options: {e}")
        finally:
            self.ui.allow_multi_dirs_selection.blockSignals(False)

    def save(self: "InterfaceOptionsPage") -> None:
        """
        Save the current interface settings from the UI to the configuration.
        Adds error handling and logs theme/language changes and errors.
        """
        try:
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
            if new_theme_setting != config.setting.get('ui_theme', str(UiTheme.DEFAULT)):
                self.logger.info(f"Theme changed: {config.setting.get('ui_theme')} -> {new_theme_setting}")
                warnings.append(_("You have changed the application theme."))
                if new_theme_setting == str(UiTheme.SYSTEM):
                    notes.append(_(
                        'Please note that using the system theme might cause the user interface to be not shown correctly. '
                        'If this is the case select the "Default" theme option to use Picard\'s default theme again.'
                    ))
                config.setting['ui_theme'] = new_theme_setting
            if new_language != config.setting.get('ui_language', ''):
                self.logger.info(f"Interface language changed: {config.setting.get('ui_language')} -> {new_language}")
                config.setting['ui_language'] = new_language
                warnings.append(_("You have changed the interface language."))
            changes_require_restart_warning(self, warnings=warnings, notes=notes)

            config.setting['filebrowser_horizontal_autoscroll'] = self.ui.filebrowser_horizontal_autoscroll.isChecked()
            config.setting['starting_directory'] = self.ui.starting_directory.isChecked()
            config.setting['starting_directory_path'] = os.path.normpath(self.ui.starting_directory_path.text())
        except Exception as e:
            self.logger.error(f"Error saving interface options: {e}")

    def starting_directory_browse(self: "InterfaceOptionsPage") -> None:
        """
        Open a dialog to select the starting directory and update the UI field. Logs the selected path or cancellation.
        """
        item = self.ui.starting_directory_path
        path = FileDialog.getExistingDirectory(
            parent=self,
            dir=item.text(),
        )
        if path:
            path = os.path.normpath(path)
            item.setText(path)
            self.logger.info(f"Starting directory selected: {path}")
        else:
            self.logger.info("Starting directory selection cancelled.")

    def multi_selection_warning(self: "InterfaceOptionsPage") -> None:
        """
        Show a warning dialog when enabling multiple directory selection. Logs user response.
        """
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
        result = dialog.exec()
        if result == QtWidgets.QMessageBox.StandardButton.No:
            self.ui.allow_multi_dirs_selection.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.logger.info("User cancelled enabling multiple directory selection.")
        else:
            self.logger.info("User confirmed enabling multiple directory selection.")


register_options_page(InterfaceOptionsPage)
