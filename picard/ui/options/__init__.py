# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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
from PyQt5 import QtWidgets
from picard import config
from picard.plugin import ExtensionPoint


class OptionsCheckError(Exception):

    def __init__(self, title, info):
        self.title = title
        self.info = info


class OptionsPage(QtWidgets.QWidget):

    PARENT = None
    SORT_ORDER = 1000
    ACTIVE = True
    STYLESHEET_ERROR = "QWidget { background-color: #f55; color: white; font-weight:bold }"
    STYLESHEET = "QLabel { qproperty-wordWrap: true; }"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(self.STYLESHEET)

    def info(self):
        raise NotImplementedError

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
        old_options = {}
        for option in options:
            if option.section == 'setting':
                old_options[option.name] = config.setting[option.name]
                config.setting[option.name] = option.default
        self.load()
        # Restore the config values incase the user doesn't save after restoring defaults
        for key in old_options:
            config.setting[key] = old_options[key]

    def display_error(self, error):
        dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, error.title, error.info, QtWidgets.QMessageBox.Ok, self)
        dialog.exec_()

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
                raise OptionsCheckError(_("Regex Error"), string_(e))

        def live_checker(text):
            regex_error.setStyleSheet("")
            regex_error.setText("")
            try:
                check()
            except OptionsCheckError as e:
                regex_error.setStyleSheet(self.STYLESHEET_ERROR)
                regex_error.setText(e.info)

        regex_edit.textChanged.connect(live_checker)


_pages = ExtensionPoint()


def register_options_page(page_class):
    _pages.register(page_class.__module__, page_class)
