# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Laurent Monin
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

from PyQt4 import QtCore, QtGui
from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_colors import Ui_ColorsOptionsPage


class ColorIcon(QtGui.QIcon):

    def __init__(self, qcolor, w=20, h=20):
        pixmap = QtGui.QPixmap(w, h)
        pixmap.fill(qcolor)
        super(QtGui.QIcon, self).__init__(pixmap)


class ColorChooserButton(QtGui.QPushButton):

    def __init__(self, key, text=None, parent=None):
        if text is None:
            text = _("Set color")
        self.key = key
        self.color = config.color[key]
        super(QtGui.QPushButton, self).__init__(ColorIcon(self.color), text, parent)
        self.clicked.connect(self._showDialog)
        self.default_button = None

    def _showDialog(self):
        col = QtGui.QColorDialog.getColor()
        if col.isValid():
            self.set_color(col)

    def set_color(self, qcolor):
        self.color = qcolor
        config.color[self.key] = qcolor
        self.setIcon(ColorIcon(qcolor))
        if self.default_button is not None:
            self.default_button.setEnabled(self.default_button.color != qcolor)

    def set_default_button(self, button):
        self.default_button = button


class ColorDefaultButton(QtGui.QPushButton):

    def __init__(self, key, chooserbutton, text=None, parent=None):
        if text is None:
            text = _("Restore default color")
        self.key = key
        self.color = config.color.get_default(key)
        self.chooserbutton = chooserbutton
        self.chooserbutton.set_default_button(self)
        super(QtGui.QPushButton, self).__init__(ColorIcon(self.color), text, parent)
        self.clicked.connect(self._setdefault)
        self.setEnabled(self.chooserbutton.color != self.color)

    def _setdefault(self):
        self.chooserbutton.set_color(self.color)


class ColorsOptionsPage(OptionsPage):

    NAME = "colors"
    TITLE = N_("Color Theme")
    PARENT = "advanced"
    SORT_ORDER = 60
    ACTIVE = True

    options = []

    def __init__(self, parent=None):
        super(ColorsOptionsPage, self).__init__(parent)
        self.ui = Ui_ColorsOptionsPage()
        self.ui.setupUi(self)

        grid = self.ui.gridLayout
        grid.setColumnStretch(0, 2)
        for i, key in enumerate(sorted([k for k in config.color.keys()])):
            grid.addWidget(QtGui.QLabel(_(config.color.get_description(key))), i, 0)
            button = ColorChooserButton(key)
            grid.addWidget(button, i, 1)
            defbutton = ColorDefaultButton(key, button)
            grid.addWidget(defbutton, i, 2)

        self.show()

    def load(self):
        pass

    def save(self):
        pass


register_options_page(ColorsOptionsPage)
