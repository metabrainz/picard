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

from functools import partial

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
        self.register_setting('cover_tags_scale_up')
        self.register_setting('cover_tags_scale_down')
        self.register_setting('cover_tags_resize_use_width')
        self.register_setting('cover_tags_resize_target_width')
        self.register_setting('cover_tags_resize_use_height')
        self.register_setting('cover_tags_resize_target_height')
        self.register_setting('cover_tags_stretch')
        self.register_setting('cover_tags_crop')
        self.register_setting('cover_file_scale_up')
        self.register_setting('cover_file_scale_down')
        self.register_setting('cover_file_resize_use_width')
        self.register_setting('cover_file_resize_target_width')
        self.register_setting('cover_file_resize_use_height')
        self.register_setting('cover_file_resize_target_height')
        self.register_setting('cover_file_stretch')
        self.register_setting('cover_file_crop')

        tags_checkboxes = (self.ui.tags_resize_width_label, self.ui.tags_resize_height_label)
        tags_at_least_one_checked = partial(self._ensure_at_least_one_checked, tags_checkboxes)
        for checkbox in tags_checkboxes:
            checkbox.clicked.connect(tags_at_least_one_checked)
        file_checkboxes = (self.ui.file_resize_width_label, self.ui.file_resize_height_label)
        file_at_least_one_checked = partial(self._ensure_at_least_one_checked, file_checkboxes)
        for checkbox in file_checkboxes:
            checkbox.clicked.connect(file_at_least_one_checked)

        self._spinboxes = {
            self.ui.tags_resize_width_label: self.ui.tags_resize_width_value,
            self.ui.tags_resize_height_label: self.ui.tags_resize_height_value,
            self.ui.file_resize_width_label: self.ui.file_resize_width_value,
            self.ui.file_resize_height_label: self.ui.file_resize_height_value,
        }
        for checkbox, spinbox in self._spinboxes.items():
            spinbox.setEnabled(checkbox.isChecked())
            checkbox.stateChanged.connect(self._update_resize_spinboxes)

    def _update_resize_spinboxes(self):
        spinbox = self._spinboxes[self.sender()]
        spinbox.setEnabled(self.sender().isChecked())

    def _ensure_at_least_one_checked(self, checkboxes, clicked):
        if not clicked and not any(checkbox.isChecked() for checkbox in checkboxes):
            sender = self.sender()
            sender.setChecked(True)

    def load(self):
        config = get_config()
        self.ui.filtering.setChecked(config.setting['filter_cover_by_size'])
        self.ui.filtering_width_value.setValue(config.setting['cover_minimum_width'])
        self.ui.filtering_height_value.setValue(config.setting['cover_minimum_height'])
        self.ui.tags_scale_up.setChecked(config.setting['cover_tags_scale_up'])
        self.ui.tags_scale_down.setChecked(config.setting['cover_tags_scale_down'])
        self.ui.tags_resize_width_label.setChecked(config.setting['cover_tags_resize_use_width'])
        self.ui.tags_resize_width_value.setValue(config.setting['cover_tags_resize_target_width'])
        self.ui.tags_resize_height_label.setChecked(config.setting['cover_tags_resize_use_height'])
        self.ui.tags_resize_height_value.setValue(config.setting['cover_tags_resize_target_height'])
        self.ui.tags_stretch.setChecked(config.setting['cover_tags_stretch'])
        self.ui.tags_crop.setChecked(config.setting['cover_tags_crop'])
        self.ui.file_scale_up.setChecked(config.setting['cover_file_scale_up'])
        self.ui.file_scale_down.setChecked(config.setting['cover_file_scale_down'])
        self.ui.file_resize_width_label.setChecked(config.setting['cover_file_resize_use_width'])
        self.ui.file_resize_width_value.setValue(config.setting['cover_file_resize_target_width'])
        self.ui.file_resize_height_label.setChecked(config.setting['cover_file_resize_use_height'])
        self.ui.file_resize_height_value.setValue(config.setting['cover_file_resize_target_height'])
        self.ui.file_stretch.setChecked(config.setting['cover_file_stretch'])
        self.ui.file_crop.setChecked(config.setting['cover_file_crop'])

    def save(self):
        config = get_config()
        config.setting['filter_cover_by_size'] = self.ui.filtering.isChecked()
        config.setting['cover_minimum_width'] = self.ui.filtering_width_value.value()
        config.setting['cover_minimum_height'] = self.ui.filtering_height_value.value()
        config.setting['cover_tags_scale_up'] = self.ui.tags_scale_up.isChecked()
        config.setting['cover_tags_scale_down'] = self.ui.tags_scale_down.isChecked()
        config.setting['cover_tags_resize_use_width'] = self.ui.tags_resize_width_label.isChecked()
        config.setting['cover_tags_resize_target_width'] = self.ui.tags_resize_width_value.value()
        config.setting['cover_tags_resize_use_height'] = self.ui.tags_resize_height_label.isChecked()
        config.setting['cover_tags_resize_target_height'] = self.ui.tags_resize_height_value.value()
        config.setting['cover_tags_stretch'] = self.ui.tags_stretch.isChecked()
        config.setting['cover_tags_crop'] = self.ui.tags_crop.isChecked()
        config.setting['cover_file_scale_up'] = self.ui.file_scale_up.isChecked()
        config.setting['cover_file_scale_down'] = self.ui.file_scale_down.isChecked()
        config.setting['cover_file_resize_use_width'] = self.ui.file_resize_width_label.isChecked()
        config.setting['cover_file_resize_target_width'] = self.ui.file_resize_width_value.value()
        config.setting['cover_file_resize_use_height'] = self.ui.file_resize_height_label.isChecked()
        config.setting['cover_file_resize_target_height'] = self.ui.file_resize_height_value.value()
        config.setting['cover_file_stretch'] = self.ui.file_stretch.isChecked()
        config.setting['cover_file_crop'] = self.ui.file_crop.isChecked()


register_options_page(CoverProcessingOptionsPage)
