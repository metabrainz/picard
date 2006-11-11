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
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.config import BoolOption, TextOption

class CoverOptionsPage(Component):

    implements(IOptionsPage)

    options = [
        BoolOption("setting", "save_images_to_tags", True),
        BoolOption("setting", "remove_images_from_tags", False),
        BoolOption("setting", "save_images_to_files", False),
        BoolOption("setting", "use_amazon_images", False),
        TextOption("setting", "cover_image_filename", u"cover"),
    ]

    def get_page_info(self):
        return _("Cover Art"), "cover", None, 35

    def get_page_widget(self, parent=None):
        self.widget = QtGui.QWidget(parent)
        from picard.ui.ui_options_cover import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self.widget)
        self.connect(self.ui.save_images_to_files, QtCore.SIGNAL("clicked()"),
            self.update_filename)
        return self.widget

    def load_options(self):
        self.ui.save_images_to_tags.setChecked(
            self.config.setting["save_images_to_tags"])
        self.ui.save_images_to_files.setChecked(
            self.config.setting["save_images_to_files"])
        self.ui.use_amazon_images.setChecked(
            self.config.setting["use_amazon_images"])
        self.ui.cover_image_filename.setText(
            self.config.setting["cover_image_filename"])
        self.update_filename()

    def save_options(self):
        self.config.setting["save_images_to_tags"] = \
            self.ui.save_images_to_tags.isChecked()
        self.config.setting["save_images_to_files"] = \
            self.ui.save_images_to_files.isChecked()
        self.config.setting["use_amazon_images"] = \
            self.ui.use_amazon_images.isChecked()
        self.config.setting["cover_image_filename"] = \
            unicode(self.ui.cover_image_filename.text())

    def update_filename(self):
        self.ui.cover_image_filename.setEnabled(
            self.ui.save_images_to_files.isChecked())

