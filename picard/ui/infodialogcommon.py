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

import os.path
from PyQt4 import QtGui
from picard.util import format_time, encode_filename
from picard.ui.ui_infodialog import Ui_InfoDialog


class InfoDialogCommon(QtGui.QDialog):

    def __init__(self, obj, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.obj = obj
        self.ui = Ui_InfoDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _hide_tab(self, widget):
        tab_idx = self.ui.tabWidget.indexOf(widget)
        if tab_idx >= 0:
            self.ui.tabWidget.removeTab(tab_idx)

    def hide_info_tab(self):
        self._hide_tab(self.ui.info_tab)

    def hide_artwork_tab(self):
        self._hide_tab(self.ui.artwork_tab)

    def display_images(self):
        bold = QtGui.QFont()
        bold.setWeight(QtGui.QFont.Bold)

        for image in self.obj.metadata.images:
            item = QtGui.QListWidgetItem()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(image.data)
            icon = QtGui.QIcon(pixmap)
            item.setIcon(icon)
            if image.is_main_cover:
                item.setFont(bold)
            item.setText("\n".join((",".join(image.types), image.description)))
            item.setToolTip(N_("Filename: %s") % image.filename)
            self.ui.artwork_list.addItem(item)
