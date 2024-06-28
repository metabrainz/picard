# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Bob Swift
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

from PyQt6.QtCore import Qt

from picard.config import get_config
from picard.const.cover_processing import (
    COVER_CONVERTING_FORMATS,
    COVER_RESIZE_MODES,
)
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    _,
)

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
        self.register_setting('cover_tags_dont_enlarge')
        self.register_setting('cover_tags_resize')
        self.register_setting('cover_tags_resize_use_width')
        self.register_setting('cover_tags_resize_target_width')
        self.register_setting('cover_tags_resize_use_height')
        self.register_setting('cover_tags_resize_target_height')
        self.register_setting('cover_tags_resize_mode')
        self.register_setting('cover_tags_convert_images')
        self.register_setting('cover_tags_convert_to_format')
        self.register_setting('cover_file_dont_enlarge')
        self.register_setting('cover_file_resize')
        self.register_setting('cover_file_resize_use_width')
        self.register_setting('cover_file_resize_target_width')
        self.register_setting('cover_file_resize_use_height')
        self.register_setting('cover_file_resize_target_height')
        self.register_setting('cover_file_resize_mode')
        self.register_setting('cover_file_convert_images')
        self.register_setting('cover_file_convert_to_format')

        self.mode_number_to_line = {}   # Map of mode number to combo box line index
        self.mode_line_to_number = {}   # Map of combo box line index to mode number
        for item_id, resize_mode in enumerate(COVER_RESIZE_MODES):
            self.mode_line_to_number[item_id] = resize_mode.mode
            self.mode_number_to_line[resize_mode.mode] = item_id
            self.ui.tags_resize_mode.addItem(resize_mode.title, resize_mode.mode)
            self.ui.file_resize_mode.addItem(resize_mode.title, resize_mode.mode)
            self.ui.tags_resize_mode.setItemData(item_id, _(resize_mode.tooltip), Qt.ItemDataRole.ToolTipRole)
            self.ui.file_resize_mode.setItemData(item_id, _(resize_mode.tooltip), Qt.ItemDataRole.ToolTipRole)

        self.ui.convert_tags_format.addItems(COVER_CONVERTING_FORMATS)
        self.ui.convert_file_format.addItems(COVER_CONVERTING_FORMATS)

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
        self.ui.tags_scale_up.setChecked(config.setting['cover_tags_dont_enlarge'])
        self.ui.tags_scale_down.setChecked(config.setting['cover_tags_resize'])
        self.ui.tags_resize_width_label.setChecked(config.setting['cover_tags_resize_use_width'])
        self.ui.tags_resize_width_value.setValue(config.setting['cover_tags_resize_target_width'])
        self.ui.tags_resize_height_label.setChecked(config.setting['cover_tags_resize_use_height'])
        self.ui.tags_resize_height_value.setValue(config.setting['cover_tags_resize_target_height'])
        self.ui.tags_resize_mode.setCurrentIndex(self.mode_number_to_line[config.setting['cover_tags_resize_mode']]
                                                 if config.setting['cover_tags_resize_mode'] in self.mode_number_to_line
                                                 else 0)
        self.ui.convert_tags.setChecked(config.setting['cover_tags_convert_images'])
        self.ui.convert_tags_format.setCurrentText(config.setting['cover_tags_convert_to_format'])
        self.ui.file_scale_up.setChecked(config.setting['cover_file_dont_enlarge'])
        self.ui.file_scale_down.setChecked(config.setting['cover_file_resize'])
        self.ui.file_resize_width_label.setChecked(config.setting['cover_file_resize_use_width'])
        self.ui.file_resize_width_value.setValue(config.setting['cover_file_resize_target_width'])
        self.ui.file_resize_height_label.setChecked(config.setting['cover_file_resize_use_height'])
        self.ui.file_resize_height_value.setValue(config.setting['cover_file_resize_target_height'])
        self.ui.file_resize_mode.setCurrentIndex(self.mode_number_to_line[config.setting['cover_file_resize_mode']]
                                                 if config.setting['cover_file_resize_mode'] in self.mode_number_to_line
                                                 else 0)
        self.ui.convert_file.setChecked(config.setting['cover_file_convert_images'])
        self.ui.convert_file_format.setCurrentText(config.setting['cover_file_convert_to_format'])

    def save(self):
        config = get_config()
        config.setting['filter_cover_by_size'] = self.ui.filtering.isChecked()
        config.setting['cover_minimum_width'] = self.ui.filtering_width_value.value()
        config.setting['cover_minimum_height'] = self.ui.filtering_height_value.value()
        config.setting['cover_tags_dont_enlarge'] = self.ui.tags_scale_up.isChecked()
        config.setting['cover_tags_resize'] = self.ui.tags_scale_down.isChecked()
        config.setting['cover_tags_resize_use_width'] = self.ui.tags_resize_width_label.isChecked()
        config.setting['cover_tags_resize_target_width'] = self.ui.tags_resize_width_value.value()
        config.setting['cover_tags_resize_use_height'] = self.ui.tags_resize_height_label.isChecked()
        config.setting['cover_tags_resize_target_height'] = self.ui.tags_resize_height_value.value()
        config.setting['cover_tags_resize_mode'] = self.mode_line_to_number[self.ui.tags_resize_mode.currentIndex()]
        config.setting['cover_tags_convert_images'] = self.ui.convert_tags.isChecked()
        config.setting['cover_tags_convert_to_format'] = self.ui.convert_tags_format.currentText()
        config.setting['cover_file_dont_enlarge'] = self.ui.file_scale_up.isChecked()
        config.setting['cover_file_resize'] = self.ui.file_scale_down.isChecked()
        config.setting['cover_file_resize_use_width'] = self.ui.file_resize_width_label.isChecked()
        config.setting['cover_file_resize_target_width'] = self.ui.file_resize_width_value.value()
        config.setting['cover_file_resize_use_height'] = self.ui.file_resize_height_label.isChecked()
        config.setting['cover_file_resize_target_height'] = self.ui.file_resize_height_value.value()
        config.setting['cover_file_resize_mode'] = self.mode_line_to_number[self.ui.file_resize_mode.currentIndex()]
        config.setting['cover_file_convert_images'] = self.ui.convert_file.isChecked()
        config.setting['cover_file_convert_to_format'] = self.ui.convert_file_format.currentText()


register_options_page(CoverProcessingOptionsPage)
