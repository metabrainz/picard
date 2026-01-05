# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2018-2021, 2024-2025 Philipp Wolfer
# Copyright (C) 2012 Erik Wasser
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2018, 2020-2024 Laurent Monin
# Copyright (C) 2022 Marcin Szalowicz
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

from PyQt6 import QtWidgets

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.formats.util import date_sanitization_format_entries
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.forms.ui_options_tags import Ui_TagsOptionsPage
from picard.ui.options import OptionsPage


class TagsOptionsPage(OptionsPage):
    NAME = 'tags'
    TITLE = N_("Tags")
    PARENT = None
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_tags.html"

    OPTIONS = (
        ('enable_tag_saving', ['write_tags']),
        ('preserve_timestamps', ['preserve_timestamps']),
        ('clear_existing_tags', ['clear_existing_tags']),
        ('preserve_images', ['preserve_images']),
        ('remove_id3_from_flac', ['remove_id3_from_flac']),
        ('remove_ape_from_mp3', ['remove_ape_from_mp3']),
        ('fix_missing_seekpoints_flac', ['fix_missing_seekpoints_flac']),
        ('preserved_tags', ['preserved_tags']),
        ('disable_date_sanitization_formats', ['disable_date_sanitization_formats']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)

        # Add multi-select combo for disabling date sanitization per format
        self._init_disable_date_sanitization_formats_control()
        self.tagger.format_registry.formats_changed.connect(self._rebuild_date_sanitization_model)

    def load(self):
        config = get_config()
        self.ui.write_tags.setChecked(config.setting['enable_tag_saving'])
        self.ui.preserve_timestamps.setChecked(config.setting['preserve_timestamps'])
        self.ui.clear_existing_tags.setChecked(config.setting['clear_existing_tags'])
        self.ui.preserve_images.setChecked(config.setting['preserve_images'])
        self.ui.remove_ape_from_mp3.setChecked(config.setting['remove_ape_from_mp3'])
        self.ui.remove_id3_from_flac.setChecked(config.setting['remove_id3_from_flac'])
        self.ui.fix_missing_seekpoints_flac.setChecked(config.setting['fix_missing_seekpoints_flac'])
        self.ui.preserved_tags.update(config.setting['preserved_tags'])
        self.ui.preserved_tags.set_user_sortable(False)

        # Load disable date sanitization formats
        disabled = config.setting['disable_date_sanitization_formats']
        self._set_disable_date_sanitization_checked(disabled)

    def save(self):
        config = get_config()
        config.setting['enable_tag_saving'] = self.ui.write_tags.isChecked()
        config.setting['preserve_timestamps'] = self.ui.preserve_timestamps.isChecked()
        config.setting['clear_existing_tags'] = self.ui.clear_existing_tags.isChecked()
        config.setting['preserve_images'] = self.ui.preserve_images.isChecked()
        config.setting['remove_ape_from_mp3'] = self.ui.remove_ape_from_mp3.isChecked()
        config.setting['remove_id3_from_flac'] = self.ui.remove_id3_from_flac.isChecked()
        config.setting['fix_missing_seekpoints_flac'] = self.ui.fix_missing_seekpoints_flac.isChecked()
        config.setting['preserved_tags'] = list(self.ui.preserved_tags.tags)
        config.setting['disable_date_sanitization_formats'] = self._get_disable_date_sanitization_checked()

    # --- Disable date sanitization formats control ---
    def _init_disable_date_sanitization_formats_control(self):
        label = QtWidgets.QLabel(self)
        label.setObjectName('disable_date_sanitization_formats_label')
        label.setText(_("Do not sanitize dates for these tag formats:"))

        self._disable_date_sanitization_container = QtWidgets.QWidget(self)
        self._disable_date_sanitization_container.setObjectName('disable_date_sanitization_formats_container')
        self._disable_date_sanitization_layout = QtWidgets.QVBoxLayout(self._disable_date_sanitization_container)
        self._disable_date_sanitization_layout.setContentsMargins(0, 0, 0, 0)
        self._disable_date_sanitization_layout.setSpacing(4)
        self._disable_date_sanitization_checkboxes: dict[str, QtWidgets.QCheckBox] = {}

        self._rebuild_date_sanitization_model()
        self.ui.vboxlayout.addWidget(label)
        self.ui.vboxlayout.addWidget(self._disable_date_sanitization_container)

    def _clear_disable_date_sanitization_checkboxes(self):
        while self._disable_date_sanitization_layout.count():
            item = self._disable_date_sanitization_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._disable_date_sanitization_checkboxes.clear()

    def _rebuild_date_sanitization_model(self):
        currently_checked = set(self._get_disable_date_sanitization_checked())

        self._clear_disable_date_sanitization_checkboxes()

        date_sanitization_entries = date_sanitization_format_entries(self.tagger.format_registry)

        for key, title in date_sanitization_entries:
            checkbox = QtWidgets.QCheckBox(
                _(title),
                self._disable_date_sanitization_container,
            )
            checkbox.setObjectName(f"disable_date_sanitization_{key}")
            checkbox.setChecked(key in currently_checked)
            checkbox.setProperty("format_key", key)

            self._disable_date_sanitization_layout.addWidget(checkbox)
            self._disable_date_sanitization_checkboxes[key] = checkbox

        self._disable_date_sanitization_layout.addStretch(1)

    def _set_disable_date_sanitization_checked(self, keys):
        checked = set(keys)
        for key, checkbox in self._disable_date_sanitization_checkboxes.items():
            checkbox.setChecked(key in checked)

    def _get_disable_date_sanitization_checked(self) -> list[str]:
        keys: list[str] = []
        for key, checkbox in self._disable_date_sanitization_checkboxes.items():
            if checkbox.isChecked():
                keys.append(key)
        return keys


register_options_page(TagsOptionsPage)
