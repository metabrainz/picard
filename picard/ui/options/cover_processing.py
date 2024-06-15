# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
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

from picard.ui.forms.ui_options_cover_processing import (
    Ui_CoverProcessingOptionsPage,
)
from picard.ui.options import OptionsPage


class CoverProcessingOptionsPage(OptionsPage):

    NAME = 'cover_processing'
    TITLE = N_("Processing")
    PARENT = 'cover'
    SORT_ORDER = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CoverProcessingOptionsPage()
        self.ui.setupUi(self)
        self.register_setting('filter_cover_by_size')
        self.register_setting('cover_minimum_width')
        self.register_setting('cover_minimum_height')
        self.register_setting('resize_images_saved_to_tags')
        self.register_setting('cover_tags_maximum_width')
        self.register_setting('cover_tags_maximum_height')
        self.register_setting('resize_images_saved_to_file')
        self.register_setting('cover_file_maximum_width')
        self.register_setting('cover_file_maximum_height')

    def load(self):
        config = get_config()
        self.ui.filtering.setChecked(config.setting['filter_cover_by_size'])
        self.ui.filtering_width_value.setValue(config.setting['cover_minimum_width'])
        self.ui.filtering_height_value.setValue(config.setting['cover_minimum_height'])
        self.ui.save_to_tags.setChecked(config.setting['resize_images_saved_to_tags'])
        self.ui.tags_resized_width_value.setValue(config.setting['cover_tags_maximum_width'])
        self.ui.tags_resized_height_value.setValue(config.setting['cover_tags_maximum_height'])
        self.ui.save_to_file.setChecked(config.setting['resize_images_saved_to_file'])
        self.ui.file_resized_width_value.setValue(config.setting['cover_file_maximum_width'])
        self.ui.file_resized_height_value.setValue(config.setting['cover_file_maximum_height'])

    def save(self):
        config = get_config()
        config.setting['filter_cover_by_size'] = self.ui.filtering.isChecked()
        config.setting['cover_minimum_width'] = self.ui.filtering_width_value.value()
        config.setting['cover_minimum_height'] = self.ui.filtering_height_value.value()
        config.setting['resize_images_saved_to_tags'] = self.ui.save_to_tags.isChecked()
        config.setting['cover_tags_maximum_width'] = self.ui.tags_resized_width_value.value()
        config.setting['cover_tags_maximum_height'] = self.ui.tags_resized_height_value.value()
        config.setting['resize_images_saved_to_file'] = self.ui.save_to_file.isChecked()
        config.setting['cover_file_maximum_width'] = self.ui.file_resized_width_value.value()
        config.setting['cover_file_maximum_height'] = self.ui.file_resized_height_value.value()


register_options_page(CoverProcessingOptionsPage)
