# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2019-2021, 2025 Philipp Wolfer
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


from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.formats.wav import WAVFile
from picard.i18n import N_

from picard.ui.forms.ui_options_tags_compatibility_wave import (
    Ui_TagsCompatibilityOptionsPage,
)
from picard.ui.options import OptionsPage


class TagsCompatibilityWaveOptionsPage(OptionsPage):

    NAME = 'tags_compatibility_wave'
    TITLE = N_("WAVE")
    PARENT = 'tags'
    SORT_ORDER = 60
    ACTIVE = True
    HELP_URL = "/config/options_tags_compatibility_wave.html"

    OPTIONS = (
        ('write_wave_riff_info', ['write_wave_riff_info']),
        ('remove_wave_riff_info', ['remove_wave_riff_info']),
        ('wave_riff_info_encoding', ['wave_riff_info_enc_cp1252', 'wave_riff_info_enc_utf8']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_TagsCompatibilityOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.write_wave_riff_info.setChecked(config.setting['write_wave_riff_info'])
        self.ui.remove_wave_riff_info.setChecked(config.setting['remove_wave_riff_info'])
        if config.setting['wave_riff_info_encoding'] == 'utf-8':
            self.ui.wave_riff_info_enc_utf8.setChecked(True)
        else:
            self.ui.wave_riff_info_enc_cp1252.setChecked(True)

    def save(self):
        config = get_config()
        config.setting['write_wave_riff_info'] = self.ui.write_wave_riff_info.isChecked()
        config.setting['remove_wave_riff_info'] = self.ui.remove_wave_riff_info.isChecked()
        if self.ui.wave_riff_info_enc_utf8.isChecked():
            config.setting['wave_riff_info_encoding'] = 'utf-8'
        else:
            config.setting['wave_riff_info_encoding'] = 'windows-1252'


if WAVFile.supports_tag('artist'):
    register_options_page(TagsCompatibilityWaveOptionsPage)
