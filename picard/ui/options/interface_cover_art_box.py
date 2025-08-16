# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Picard Contributors
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
from picard.i18n import N_

from picard.ui.forms.ui_options_interface_cover_art_box import (
    Ui_InterfaceCoverArtBoxOptionsPage,
)
from picard.ui.options import OptionsPage


class InterfaceCoverArtBoxOptionsPage(OptionsPage):
    NAME = 'interface_cover_art_box'
    TITLE = N_("Cover Art Box")
    PARENT = 'interface'
    SORT_ORDER = 40
    ACTIVE = True
    HELP_URL = "/config/options_interface_cover_art_box.html"

    OPTIONS = (
        ('show_cover_art_details', ['cb_show_cover_art_details']),
        ('show_cover_art_details_type', ['cb_show_cover_art_details_type']),
        ('show_cover_art_details_filesize', ['cb_show_cover_art_details_filesize']),
        ('show_cover_art_details_dimensions', ['cb_show_cover_art_details_dimensions']),
        ('show_cover_art_details_mimetype', ['cb_show_cover_art_details_mimetype']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_InterfaceCoverArtBoxOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.cb_show_cover_art_details.setChecked(config.setting['show_cover_art_details'])
        self.ui.cb_show_cover_art_details_type.setChecked(config.setting['show_cover_art_details_type'])
        self.ui.cb_show_cover_art_details_filesize.setChecked(config.setting['show_cover_art_details_filesize'])
        self.ui.cb_show_cover_art_details_dimensions.setChecked(config.setting['show_cover_art_details_dimensions'])
        self.ui.cb_show_cover_art_details_mimetype.setChecked(config.setting['show_cover_art_details_mimetype'])

    def save(self):
        config = get_config()
        config.setting['show_cover_art_details'] = self.ui.cb_show_cover_art_details.isChecked()
        config.setting['show_cover_art_details_type'] = self.ui.cb_show_cover_art_details_type.isChecked()
        config.setting['show_cover_art_details_filesize'] = self.ui.cb_show_cover_art_details_filesize.isChecked()
        config.setting['show_cover_art_details_dimensions'] = self.ui.cb_show_cover_art_details_dimensions.isChecked()
        config.setting['show_cover_art_details_mimetype'] = self.ui.cb_show_cover_art_details_mimetype.isChecked()


register_options_page(InterfaceCoverArtBoxOptionsPage)
