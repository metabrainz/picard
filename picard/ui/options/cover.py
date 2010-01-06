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

from PyQt4 import QtCore, QtGui
from picard.config import BoolOption, TextOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_cover import Ui_CoverOptionsPage


class CoverOptionsPage(OptionsPage):

    NAME = "cover"
    TITLE = N_("Cover Art")
    PARENT = None
    SORT_ORDER = 35
    ACTIVE = True

    options = [
        BoolOption("setting", "save_images_to_tags", True),
        BoolOption("setting", "save_images_to_files", False),
        TextOption("setting", "cover_image_filename", "cover"),
        BoolOption("setting", "save_images_overwrite", False),
    ]

    def __init__(self, parent=None):
        super(CoverOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.connect(self.ui.save_images_to_files, QtCore.SIGNAL("clicked()"), self.update_filename)

    def load(self):
        self.ui.save_images_to_tags.setChecked(self.config.setting["save_images_to_tags"])
        self.ui.save_images_to_files.setChecked(self.config.setting["save_images_to_files"])
        self.ui.cover_image_filename.setText(self.config.setting["cover_image_filename"])
        self.ui.save_images_overwrite.setChecked(self.config.setting["save_images_overwrite"])
        self.update_filename()

    def save(self):
        self.config.setting["save_images_to_tags"] = self.ui.save_images_to_tags.isChecked()
        self.config.setting["save_images_to_files"] = self.ui.save_images_to_files.isChecked()
        self.config.setting["cover_image_filename"] = unicode(self.ui.cover_image_filename.text())
        self.config.setting["save_images_overwrite"] = self.ui.save_images_overwrite.isChecked()

    def update_filename(self):
        enabled = self.ui.save_images_to_files.isChecked()
        self.ui.cover_image_filename.setEnabled(enabled)
        self.ui.save_images_overwrite.setEnabled(enabled)


register_options_page(CoverOptionsPage)
