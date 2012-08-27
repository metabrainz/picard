# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2012 Wieland Hoffmann
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
from picard.config import BoolOption, IntOption, TextOption
from picard.ui.options import register_options_page, OptionsPage
from picard.ui.ui_options_coverart import Ui_CoverartOptionsPage

class CoverArtOptionsPage(OptionsPage):
    NAME = "coverartproviders"
    TITLE = "Providers"
    PARENT = "cover"

    options = [
            BoolOption("setting", "ca_provider_use_amazon", True),
            BoolOption("setting", "ca_provider_use_cdbaby", True),
            BoolOption("setting", "ca_provider_use_caa", True),
            BoolOption("setting", "ca_provider_use_jamendo", True),
            BoolOption("setting", "ca_provider_use_whitelist", True),
            BoolOption("setting", "caa_approved_only", False),
            IntOption("setting", "caa_image_size", 2),
            TextOption("setting", "caa_image_types", "front"),
            ]

    def __init__(self, parent=None):
        super(CoverArtOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverartOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.caprovider_amazon.setChecked(self.config.setting["ca_provider_use_amazon"])
        self.ui.caprovider_cdbaby.setChecked(self.config.setting["ca_provider_use_cdbaby"])
        self.ui.caprovider_caa.setChecked(self.config.setting["ca_provider_use_caa"])
        self.ui.caprovider_jamendo.setChecked(self.config.setting["ca_provider_use_jamendo"])
        self.ui.caprovider_whitelist.setChecked(self.config.setting["ca_provider_use_whitelist"])
        self.ui.gb_caa.setEnabled(self.config.setting["ca_provider_use_caa"])

        self.ui.cb_image_size.setCurrentIndex(self.config.setting["caa_image_size"])
        self.ui.le_image_types.setText(self.config.setting["caa_image_types"])
        self.ui.cb_approved_only.setChecked(self.config.setting["caa_approved_only"])

    def save(self):
        self.config.setting["ca_provider_use_amazon"] =\
            self.ui.caprovider_amazon.isChecked()
        self.config.setting["ca_provider_use_cdbaby"] =\
            self.ui.caprovider_cdbaby.isChecked()
        self.config.setting["ca_provider_use_caa"] =\
            self.ui.caprovider_caa.isChecked()
        self.config.setting["ca_provider_use_jamendo"] =\
            self.ui.caprovider_jamendo.isChecked()
        self.config.setting["ca_provider_use_whitelist"] =\
            self.ui.caprovider_whitelist.isChecked()
        self.config.setting["caa_image_size"] =\
            self.ui.cb_image_size.currentIndex()
        self.config.setting["caa_image_types"] = self.ui.le_image_types.text()
        self.config.setting["caa_approved_only"] =\
            self.ui.cb_approved_only.isChecked()

register_options_page(CoverArtOptionsPage)
