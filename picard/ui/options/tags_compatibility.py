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

from functools import partial

from picard import config

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_tags_compatibility import (
    Ui_TagsCompatibilityOptionsPage,
)


class TagsCompatibilityOptionsPage(OptionsPage):

    NAME = "tags_compatibility"
    TITLE = N_("Tag Compatibility")
    PARENT = "tags"
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        config.BoolOption("setting", "write_id3v1", True),
        config.BoolOption("setting", "write_id3v23", True),
        config.TextOption("setting", "id3v2_encoding", "utf-16"),
        config.TextOption("setting", "id3v23_join_with", "/"),
        config.BoolOption("setting", "itunes_compatible_grouping", False),
        config.BoolOption("setting", "aac_save_ape", True),
        config.BoolOption("setting", "remove_ape_from_aac", False),
        config.BoolOption("setting", "ac3_save_ape", True),
        config.BoolOption("setting", "remove_ape_from_ac3", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TagsCompatibilityOptionsPage()
        self.ui.setupUi(self)
        self.ui.write_id3v23.clicked.connect(self.update_encodings)
        self.ui.write_id3v24.clicked.connect(partial(self.update_encodings, force_utf8=True))
        self.ui.aac_no_tags.toggled.connect(self.ui.remove_ape_from_aac.setEnabled)
        self.ui.ac3_no_tags.toggled.connect(self.ui.remove_ape_from_ac3.setEnabled)

    def load(self):
        self.ui.write_id3v1.setChecked(config.setting["write_id3v1"])
        if config.setting["write_id3v23"]:
            self.ui.write_id3v23.setChecked(True)
        else:
            self.ui.write_id3v24.setChecked(True)
        if config.setting["id3v2_encoding"] == "iso-8859-1":
            self.ui.enc_iso88591.setChecked(True)
        elif config.setting["id3v2_encoding"] == "utf-16":
            self.ui.enc_utf16.setChecked(True)
        else:
            self.ui.enc_utf8.setChecked(True)
        self.ui.id3v23_join_with.setEditText(config.setting["id3v23_join_with"])
        self.ui.itunes_compatible_grouping.setChecked(config.setting["itunes_compatible_grouping"])
        if config.setting["aac_save_ape"]:
            self.ui.aac_save_ape.setChecked(True)
        else:
            self.ui.aac_no_tags.setChecked(True)
        self.ui.remove_ape_from_aac.setChecked(config.setting["remove_ape_from_aac"])
        self.ui.remove_ape_from_aac.setEnabled(not config.setting["aac_save_ape"])
        if config.setting["ac3_save_ape"]:
            self.ui.ac3_save_ape.setChecked(True)
        else:
            self.ui.ac3_no_tags.setChecked(True)
        self.ui.remove_ape_from_ac3.setChecked(config.setting["remove_ape_from_ac3"])
        self.ui.remove_ape_from_ac3.setEnabled(not config.setting["ac3_save_ape"])
        self.update_encodings()

    def save(self):
        config.setting["write_id3v1"] = self.ui.write_id3v1.isChecked()
        config.setting["write_id3v23"] = self.ui.write_id3v23.isChecked()
        config.setting["id3v23_join_with"] = self.ui.id3v23_join_with.currentText()
        if self.ui.enc_iso88591.isChecked():
            config.setting["id3v2_encoding"] = "iso-8859-1"
        elif self.ui.enc_utf16.isChecked():
            config.setting["id3v2_encoding"] = "utf-16"
        else:
            config.setting["id3v2_encoding"] = "utf-8"
        config.setting["itunes_compatible_grouping"] = self.ui.itunes_compatible_grouping.isChecked()
        config.setting["aac_save_ape"] = self.ui.aac_save_ape.isChecked()
        config.setting["remove_ape_from_aac"] = self.ui.remove_ape_from_aac.isChecked()
        config.setting["ac3_save_ape"] = self.ui.ac3_save_ape.isChecked()
        config.setting["remove_ape_from_ac3"] = self.ui.remove_ape_from_ac3.isChecked()

    def update_encodings(self, force_utf8=False):
        if self.ui.write_id3v23.isChecked():
            if self.ui.enc_utf8.isChecked():
                self.ui.enc_utf16.setChecked(True)
            self.ui.enc_utf8.setEnabled(False)
            self.ui.label_id3v23_join_with.setEnabled(True)
            self.ui.id3v23_join_with.setEnabled(True)
        else:
            self.ui.enc_utf8.setEnabled(True)
            if force_utf8:
                self.ui.enc_utf8.setChecked(True)
            self.ui.label_id3v23_join_with.setEnabled(False)
            self.ui.id3v23_join_with.setEnabled(False)


register_options_page(TagsCompatibilityOptionsPage)
