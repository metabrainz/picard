# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009, 2019-2022, 2025 Philipp Wolfer
# Copyright (C) 2013, 2015, 2018-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2025 Bob Swift
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


from collections import defaultdict
import re
from typing import (
    TypeAlias,
    TypedDict,
)

from PyQt6 import QtWidgets

from picard import (
    log,
    tagger_instance,
)
from picard.config import (
    Option,
    ProfileConfigSection,
    get_config,
    register_quick_menu_item,
)
from picard.i18n import gettext as _
from picard.profile import (
    profile_groups_add_setting,
    profile_groups_all_settings,
    profile_groups_update_highlights,
    setting_profile_key,
)
from picard.util.display_title_base import HasDisplayTitle


class OptionsCheckError(Exception):
    def __init__(self, title, info):
        self.title = title
        self.info = info


class OptionConfig(TypedDict, total=False):
    widgets: list[str]


PageOptionConfigs: TypeAlias = dict[str, OptionConfig]


class OptionsPage(QtWidgets.QWidget, HasDisplayTitle):
    NAME: str
    PARENT = None
    SORT_ORDER = 1000
    ACTIVE = True
    HELP_URL = None
    STYLESHEET_SUCCESS = "QWidget { background-color: #292; color: white; padding: 2px; }"
    STYLESHEET_ERROR = "QWidget { background-color: #f55; color: white; font-weight:bold; padding: 2px; }"
    STYLESHEET = "QLabel { qproperty-wordWrap: true; }"
    OPTIONS: PageOptionConfigs = {}

    # Config section where this page's options are stored.
    # Core pages use 'setting'. Plugin pages are set to 'plugin.<uuid>'
    # automatically by register_options_page().
    OPTION_SECTION = 'setting'

    _registered_settings: dict[str, list] = defaultdict(list)
    initialized = False
    loaded = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tagger = tagger_instance()
        self.setStyleSheet(self.STYLESHEET)

        # Keep track whether the options page has been destroyed to avoid
        # trying to update deleted UI widgets after plugin list refresh.
        self.deleted = False

        # The on destroyed cannot be created as a method on this class or it will never get called.
        # See https://stackoverflow.com/questions/16842955/widgets-destroyed-signal-is-not-fired-pyqt
        def on_destroyed(obj=None):
            self.deleted = True

        self.destroyed.connect(on_destroyed)

    def set_dialog(self, dialog):
        self.dialog = dialog

    def check(self):
        pass

    def load(self):
        pass

    def save(self):
        pass

    def _config_section(self, config):
        """Return the config section for this page's options."""
        if self.OPTION_SECTION == 'setting':
            return config.setting
        api = getattr(self, 'api', None)
        if api:
            return api.plugin_config
        return ProfileConfigSection(config, self.OPTION_SECTION)

    def restore_defaults(self):
        config = get_config()
        section = self._config_section(config)
        # Save current values (profile-aware), write defaults, load UI, then restore.
        # This gives the user a preview of defaults without permanently changing anything.
        old_options = {}
        for option in self._registered_settings[self.NAME]:
            default_value = option.default
            name = option.name
            current_value = section[name]
            if current_value != default_value:
                log.debug("Option %s %s: %r -> %r" % (self.NAME, name, current_value, default_value))
                old_options[name] = current_value
                section[name] = default_value
        self.load()
        # Restore the config values in case the user doesn't save after restoring defaults
        for name, old_value in old_options.items():
            section[name] = old_value

    def display_error(self, error):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Warning, error.title, error.info, QtWidgets.QMessageBox.StandardButton.Ok, self
        )
        dialog.exec()

    def init_regex_checker(self, regex_edit, regex_error):
        """
        regex_edit : a widget supporting text() and textChanged() methods, ie
        QLineEdit
        regex_error : a widget supporting setStyleSheet() and setText() methods,
        ie. QLabel
        """

        regex_error.setVisible(False)

        def check():
            try:
                re.compile(regex_edit.text())
            except re.error as e:
                raise OptionsCheckError(_("Regex Error"), str(e)) from None

        def live_checker(text):
            regex_error.setVisible(False)
            try:
                check()
            except OptionsCheckError as e:
                regex_error.setStyleSheet(self.STYLESHEET_ERROR)
                regex_error.setText(e.info)
                regex_error.setVisible(True)

        regex_edit.textChanged.connect(live_checker)

    @classmethod
    def register_setting(cls, name, highlights=None):
        """Register a setting edited in the page, used to restore defaults
        and to highlight when profiles are used"""
        section = cls.OPTION_SECTION
        option = Option.get(section, name)
        if option is None:
            raise Exception(f"Cannot register setting for non-existing option {name}")
        OptionsPage._registered_settings[cls.NAME].append(option)
        register_quick_menu_item(cls.SORT_ORDER, cls.NAME, cls.PARENT, cls.display_title(), option)
        pkey = setting_profile_key(name, section)
        if option.in_profile and pkey not in profile_groups_all_settings():
            profile_groups_add_setting(
                cls.NAME,
                name,
                tuple(highlights) if highlights else (),
                title=cls.display_title(),
                parent=cls.PARENT,
                section=section,
            )
        elif option.in_profile and highlights:
            profile_groups_update_highlights(section, name, tuple(highlights))
