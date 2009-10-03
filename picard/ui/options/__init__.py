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

from PyQt4 import QtGui
from picard.plugin import ExtensionPoint


class OptionsCheckError(Exception):

    def __init__(self, title, info):
        self.title = title
        self.info = info

class OptionsPage(QtGui.QWidget):

    PARENT = None
    SORT_ORDER = 1000
    ACTIVE = True

    def info(self):
        raise NotImplementedError

    def check(self):
        pass

    def load(self):
        pass

    def save(self):
        pass
    
    def display_error(self, error):
        dialog = QtGui.QMessageBox(QtGui.QMessageBox.Warning, error.title, error.info, QtGui.QMessageBox.Ok, self)
        dialog.exec_()


_pages = ExtensionPoint()

def register_options_page(page_class):
    _pages.register(page_class.__module__, page_class)
