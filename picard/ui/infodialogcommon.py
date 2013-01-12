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

        orig_images = []
        images = self.obj.metadata.images
        try:
            orig_images = self.obj.orig_metadata.images
        except AttributeError:
            pass

        if not images and not orig_images:
           self.hide_artwork_tab() # hide images tab as it is empty

        for image in orig_images:
            self._display_image(image)

        for image in images:
            self._display_image(image)


    def _display_image(self, image, **kwargs):
        item = QtGui.QListWidgetItem()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image.data)
        icon = QtGui.QIcon(pixmap)
        item.setIcon(icon)
        if image.is_main_cover:
            font = QtGui.QFont()
            font.setWeight(QtGui.QFont.Bold)
            item.setFont(font)
        text = []
        if image.types:
            text.append((",".join(image.types)))
        if image.description:
            text.append(image.description)
        if image.source is not None:
            parts = image.source.split('/')
            if len(parts) > 2:
                source = parts[2].split(':')[0] #host
            else:
                source = image.source
            text.append(_("Source: %s") % source)
        item.setText("\n".join(text))
        item.setToolTip(N_("Filename: %s") % image.filename)
        self.ui.artwork_list.addItem(item)
