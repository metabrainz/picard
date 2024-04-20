# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009, 2019-2022 Philipp Wolfer
# Copyright (C) 2013, 2015, 2018-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
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


import re

from PyQt6 import QtWidgets

from picard import log
from picard.config import get_config
from picard.i18n import _
from picard.plugin import ExtensionPoint


class OptionsCheckError(Exception):

    def __init__(self, title, info):
        self.title = title
        self.info = info


class OptionsPage(QtWidgets.QWidget):

    PARENT = None
    SORT_ORDER = 1000
    ACTIVE = True
    HELP_URL = None
    STYLESHEET_ERROR = "QWidget { background-color: #f55; color: white; font-weight:bold; padding: 2px; }"
    STYLESHEET = "QLabel { qproperty-wordWrap: true; }"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def restore_defaults(self):
        try:
            options = self.options
        except AttributeError:
            return
        config = get_config()
        old_options = {}
        for option in options:
            if option.section == 'setting' and config.setting[option.name] != option.default:
                log.debug("Option %s %s: %r -> %r" % (self.NAME, option.name, config.setting[option.name], option.default))
                old_options[option.name] = config.setting[option.name]
                config.setting[option.name] = option.default
        self.load()
        # Restore the config values incase the user doesn't save after restoring defaults
        for key in old_options:
            config.setting[key] = old_options[key]

    def display_error(self, error):
        dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Warning, error.title, error.info, QtWidgets.QMessageBox.StandardButton.Ok, self)
        dialog.exec()

    def init_regex_checker(self, regex_edit, regex_error):
        """
        regex_edit : a widget supporting text() and textChanged() methods, ie
        QLineEdit
        regex_error : a widget supporting setStyleSheet() and setText() methods,
        ie. QLabel
        """

        def check():
            try:
                re.compile(regex_edit.text())
            except re.error as e:
                raise OptionsCheckError(_("Regex Error"), str(e))

        def live_checker(text):
            regex_error.setStyleSheet("")
            regex_error.setText("")
            try:
                check()
            except OptionsCheckError as e:
                regex_error.setStyleSheet(self.STYLESHEET_ERROR)
                regex_error.setText(e.info)

        regex_edit.textChanged.connect(live_checker)


_pages = ExtensionPoint(label='pages')


def register_options_page(page_class):
    _pages.register(page_class.__module__, page_class)
