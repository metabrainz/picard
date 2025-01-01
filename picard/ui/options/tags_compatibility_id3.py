# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2019-2021, 2023 Philipp Wolfer
# Copyright (C) 2021, 2023-2024 Laurent Monin
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

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_tags_compatibility_id3 import (
    Ui_TagsCompatibilityOptionsPage,
)
from picard.ui.options import OptionsPage


class TagsCompatibilityID3OptionsPage(OptionsPage):

    NAME = 'tags_compatibility_id3'
    TITLE = N_("ID3")
    PARENT = 'tags'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_tags_compatibility_id3.html"

    OPTIONS = (
        ('write_id3v23', ['write_id3v23', 'write_id3v24']),
        ('id3v2_encoding', ['enc_utf8', 'enc_utf16', 'enc_iso88591']),
        ('id3v23_join_with', ['id3v23_join_with']),
        ('itunes_compatible_grouping', ['itunes_compatible_grouping']),
        ('write_id3v1', ['write_id3v1']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_TagsCompatibilityOptionsPage()
        self.ui.setupUi(self)
        self.ui.write_id3v23.clicked.connect(self.update_encodings)
        self.ui.write_id3v24.clicked.connect(partial(self.update_encodings, force_utf8=True))

    def load(self):
        config = get_config()
        self.ui.write_id3v1.setChecked(config.setting['write_id3v1'])
        if config.setting['write_id3v23']:
            self.ui.write_id3v23.setChecked(True)
        else:
            self.ui.write_id3v24.setChecked(True)
        if config.setting['id3v2_encoding'] == 'iso-8859-1':
            self.ui.enc_iso88591.setChecked(True)
        elif config.setting['id3v2_encoding'] == 'utf-16':
            self.ui.enc_utf16.setChecked(True)
        else:
            self.ui.enc_utf8.setChecked(True)
        self.ui.id3v23_join_with.setEditText(config.setting['id3v23_join_with'])
        self.ui.itunes_compatible_grouping.setChecked(config.setting['itunes_compatible_grouping'])
        self.update_encodings()

    def save(self):
        config = get_config()
        config.setting['write_id3v1'] = self.ui.write_id3v1.isChecked()
        config.setting['write_id3v23'] = self.ui.write_id3v23.isChecked()
        config.setting['id3v23_join_with'] = self.ui.id3v23_join_with.currentText()
        if self.ui.enc_iso88591.isChecked():
            config.setting['id3v2_encoding'] = 'iso-8859-1'
        elif self.ui.enc_utf16.isChecked():
            config.setting['id3v2_encoding'] = 'utf-16'
        else:
            config.setting['id3v2_encoding'] = 'utf-8'
        config.setting['itunes_compatible_grouping'] = self.ui.itunes_compatible_grouping.isChecked()

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


register_options_page(TagsCompatibilityID3OptionsPage)
