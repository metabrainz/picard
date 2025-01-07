# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Bob Swift
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2025 Philipp Wolfer
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
from PyQt6.QtWidgets import QSpinBox

from picard.config import get_config
from picard.const.cover_processing import (
    COVER_CONVERTING_FORMATS,
    COVER_RESIZE_MODES,
    ResizeModes,
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

    OPTIONS = (
        ('filter_cover_by_size', None),
        ('cover_minimum_width', None),
        ('cover_minimum_height', None),
        ('cover_tags_enlarge', None),
        ('cover_tags_resize', None),
        ('cover_tags_resize_target_width', None),
        ('cover_tags_resize_target_height', None),
        ('cover_tags_resize_mode', None),
        ('cover_tags_convert_images', None),
        ('cover_tags_convert_to_format', None),
        ('cover_file_enlarge', None),
        ('cover_file_resize', None),
        ('cover_file_resize_target_width', None),
        ('cover_file_resize_target_height', None),
        ('cover_file_resize_mode', None),
        ('cover_file_convert_images', None),
        ('cover_file_convert_to_format', None),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CoverProcessingOptionsPage()
        self.ui.setupUi(self)

        for resize_mode in COVER_RESIZE_MODES:
            self.ui.tags_resize_mode.addItem(resize_mode.title, resize_mode.mode.value)
            self.ui.file_resize_mode.addItem(resize_mode.title, resize_mode.mode.value)
            self.ui.tags_resize_mode.setItemData(resize_mode.mode, _(resize_mode.tooltip), Qt.ItemDataRole.ToolTipRole)
            self.ui.file_resize_mode.setItemData(resize_mode.mode, _(resize_mode.tooltip), Qt.ItemDataRole.ToolTipRole)

        self.ui.convert_tags_format.addItems(COVER_CONVERTING_FORMATS)
        self.ui.convert_file_format.addItems(COVER_CONVERTING_FORMATS)

        tags_resize_mode_changed = partial(
            self._resize_mode_changed,
            self.ui.tags_resize_width_widget,
            self.ui.tags_resize_height_widget
        )
        file_resize_mode_changed = partial(
            self._resize_mode_changed,
            self.ui.file_resize_width_widget,
            self.ui.file_resize_height_widget
        )
        self.ui.tags_resize_mode.currentIndexChanged.connect(tags_resize_mode_changed)
        self.ui.file_resize_mode.currentIndexChanged.connect(file_resize_mode_changed)

    def _resize_mode_changed(self, width_widget, height_widget, index):
        width_visible = True
        height_visible = True
        if index == ResizeModes.SCALE_TO_WIDTH:
            height_visible = False
        elif index == ResizeModes.SCALE_TO_HEIGHT:
            width_visible = False
        width_widget.setEnabled(width_visible)
        width_spinbox = width_widget.findChildren(QSpinBox)[0]
        width_spinbox.lineEdit().setVisible(width_visible)
        height_widget.setEnabled(height_visible)
        height_spinbox = height_widget.findChildren(QSpinBox)[0]
        height_spinbox.lineEdit().setVisible(height_visible)

    def load(self):
        config = get_config()
        self.ui.filtering.setChecked(config.setting['filter_cover_by_size'])
        self.ui.filtering_width_value.setValue(config.setting['cover_minimum_width'])
        self.ui.filtering_height_value.setValue(config.setting['cover_minimum_height'])
        self.ui.tags_scale_up.setChecked(config.setting['cover_tags_enlarge'])
        self.ui.tags_scale_down.setChecked(config.setting['cover_tags_resize'])
        self.ui.tags_resize_width_value.setValue(config.setting['cover_tags_resize_target_width'])
        self.ui.tags_resize_height_value.setValue(config.setting['cover_tags_resize_target_height'])
        current_index = self.ui.tags_resize_mode.findData(config.setting['cover_tags_resize_mode'])
        if current_index == -1:
            current_index = ResizeModes.MAINTAIN_ASPECT_RATIO
        self.ui.tags_resize_mode.setCurrentIndex(current_index)
        self.ui.convert_tags.setChecked(config.setting['cover_tags_convert_images'])
        self.ui.convert_tags_format.setCurrentText(config.setting['cover_tags_convert_to_format'])
        self.ui.file_scale_up.setChecked(config.setting['cover_file_enlarge'])
        self.ui.file_scale_down.setChecked(config.setting['cover_file_resize'])
        self.ui.file_resize_width_value.setValue(config.setting['cover_file_resize_target_width'])
        self.ui.file_resize_height_value.setValue(config.setting['cover_file_resize_target_height'])
        current_index = self.ui.file_resize_mode.findData(config.setting['cover_file_resize_mode'])
        if current_index == -1:
            current_index = ResizeModes.MAINTAIN_ASPECT_RATIO
        self.ui.file_resize_mode.setCurrentIndex(current_index)
        self.ui.convert_file.setChecked(config.setting['cover_file_convert_images'])
        self.ui.convert_file_format.setCurrentText(config.setting['cover_file_convert_to_format'])

    def save(self):
        config = get_config()
        config.setting['filter_cover_by_size'] = self.ui.filtering.isChecked()
        config.setting['cover_minimum_width'] = self.ui.filtering_width_value.value()
        config.setting['cover_minimum_height'] = self.ui.filtering_height_value.value()
        config.setting['cover_tags_enlarge'] = self.ui.tags_scale_up.isChecked()
        config.setting['cover_tags_resize'] = self.ui.tags_scale_down.isChecked()
        config.setting['cover_tags_resize_target_width'] = self.ui.tags_resize_width_value.value()
        config.setting['cover_tags_resize_target_height'] = self.ui.tags_resize_height_value.value()
        config.setting['cover_tags_resize_mode'] = self.ui.tags_resize_mode.currentData()
        config.setting['cover_tags_convert_images'] = self.ui.convert_tags.isChecked()
        config.setting['cover_tags_convert_to_format'] = self.ui.convert_tags_format.currentText()
        config.setting['cover_file_enlarge'] = self.ui.file_scale_up.isChecked()
        config.setting['cover_file_resize'] = self.ui.file_scale_down.isChecked()
        config.setting['cover_file_resize_target_width'] = self.ui.file_resize_width_value.value()
        config.setting['cover_file_resize_target_height'] = self.ui.file_resize_height_value.value()
        config.setting['cover_file_resize_mode'] = self.ui.file_resize_mode.currentData()
        config.setting['cover_file_convert_images'] = self.ui.convert_file.isChecked()
        config.setting['cover_file_convert_to_format'] = self.ui.convert_file_format.currentText()


register_options_page(CoverProcessingOptionsPage)
