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


import logging
from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_tags import Ui_TagsOptionsPage
from picard.ui.options import OptionsPage


class TagsOptionsPage(OptionsPage):
    """
    Options page for configuring tag writing and preservation in Picard.
    Provides UI and logic for tag-related settings.
    """

    NAME: str = 'tags'
    TITLE: str = N_("Tags")
    PARENT: None = None
    SORT_ORDER: int = 30
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_tags.html"

    OPTIONS: tuple[tuple[str, list[str]], ...] = (
        ('dont_write_tags', ['write_tags']),
        ('preserve_timestamps', ['preserve_timestamps']),
        ('clear_existing_tags', ['clear_existing_tags']),
        ('preserve_images', ['preserve_images']),
        ('remove_id3_from_flac', ['remove_id3_from_flac']),
        ('remove_ape_from_mp3', ['remove_ape_from_mp3']),
        ('fix_missing_seekpoints_flac', ['fix_missing_seekpoints_flac']),
        ('preserved_tags', ['preserved_tags']),
    )

    ui: Ui_TagsOptionsPage
    logger: logging.Logger

    def __init__(self, parent: object = None) -> None:
        """
        Initialize the TagsOptionsPage, set up the UI and connect logic.
        :param parent: The parent widget.
        Sets up logging for this options page.
        """
        super().__init__(parent=parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)
        self.logger = logging.getLogger("picard.ui.options.tags")

    def load(self: "TagsOptionsPage") -> None:
        """
        Load current tag settings from the configuration and update the UI accordingly. Logs errors.
        """
        try:
            config = get_config()
            self.ui.write_tags.setChecked(not config.setting.get('dont_write_tags', False))
            self.ui.preserve_timestamps.setChecked(config.setting.get('preserve_timestamps', False))
            self.ui.clear_existing_tags.setChecked(config.setting.get('clear_existing_tags', False))
            self.ui.preserve_images.setChecked(config.setting.get('preserve_images', False))
            self.ui.remove_ape_from_mp3.setChecked(config.setting.get('remove_ape_from_mp3', False))
            self.ui.remove_id3_from_flac.setChecked(config.setting.get('remove_id3_from_flac', False))
            self.ui.fix_missing_seekpoints_flac.setChecked(config.setting.get('fix_missing_seekpoints_flac', False))
            self.ui.preserved_tags.update(config.setting.get('preserved_tags', []))
            self.ui.preserved_tags.set_user_sortable(False)
        except Exception as e:
            self.logger.error(f"Error loading tag options: {e}")

    def save(self: "TagsOptionsPage") -> None:
        """
        Save the current tag settings from the UI to the configuration. Logs errors.
        """
        try:
            config = get_config()
            config.setting['dont_write_tags'] = not self.ui.write_tags.isChecked()
            config.setting['preserve_timestamps'] = self.ui.preserve_timestamps.isChecked()
            config.setting['clear_existing_tags'] = self.ui.clear_existing_tags.isChecked()
            config.setting['preserve_images'] = self.ui.preserve_images.isChecked()
            config.setting['remove_ape_from_mp3'] = self.ui.remove_ape_from_mp3.isChecked()
            config.setting['remove_id3_from_flac'] = self.ui.remove_id3_from_flac.isChecked()
            config.setting['fix_missing_seekpoints_flac'] = self.ui.fix_missing_seekpoints_flac.isChecked()
            config.setting['preserved_tags'] = list(self.ui.preserved_tags.tags)
        except Exception as e:
            self.logger.error(f"Error saving tag options: {e}")


register_options_page(TagsOptionsPage)
