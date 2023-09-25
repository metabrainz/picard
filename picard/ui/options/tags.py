# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009-2010, 2018-2021 Philipp Wolfer
# Copyright (C) 2012 Erik Wasser
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2018, 2020-2022 Laurent Monin
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


from picard.config import (
    BoolOption,
    ListOption,
    get_config,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_tags import Ui_TagsOptionsPage


class TagsOptionsPage(OptionsPage):

    NAME = 'tags'
    TITLE = N_("Tags")
    PARENT = None
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_tags.html"

    options = [
        BoolOption('setting', 'dont_write_tags', False),
        BoolOption('setting', 'preserve_timestamps', False),
        BoolOption('setting', 'clear_existing_tags', False),
        BoolOption('setting', 'preserve_images', False),
        BoolOption('setting', 'remove_id3_from_flac', False),
        BoolOption('setting', 'remove_ape_from_mp3', False),
        BoolOption('setting', 'fix_missing_seekpoints_flac', False),
        ListOption('setting', 'preserved_tags', []),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.write_tags.setChecked(not config.setting['dont_write_tags'])
        self.ui.preserve_timestamps.setChecked(config.setting['preserve_timestamps'])
        self.ui.clear_existing_tags.setChecked(config.setting['clear_existing_tags'])
        self.ui.preserve_images.setChecked(config.setting['preserve_images'])
        self.ui.remove_ape_from_mp3.setChecked(config.setting['remove_ape_from_mp3'])
        self.ui.remove_id3_from_flac.setChecked(config.setting['remove_id3_from_flac'])
        self.ui.fix_missing_seekpoints_flac.setChecked(config.setting['fix_missing_seekpoints_flac'])
        self.ui.preserved_tags.update(config.setting['preserved_tags'])
        self.ui.preserved_tags.set_user_sortable(False)

    def save(self):
        config = get_config()
        config.setting['dont_write_tags'] = not self.ui.write_tags.isChecked()
        config.setting['preserve_timestamps'] = self.ui.preserve_timestamps.isChecked()
        clear_existing_tags = self.ui.clear_existing_tags.isChecked()
        if clear_existing_tags != config.setting['clear_existing_tags']:
            config.setting['clear_existing_tags'] = clear_existing_tags
            self.tagger.window.metadata_box.update()
        config.setting['preserve_images'] = self.ui.preserve_images.isChecked()
        config.setting['remove_ape_from_mp3'] = self.ui.remove_ape_from_mp3.isChecked()
        config.setting['remove_id3_from_flac'] = self.ui.remove_id3_from_flac.isChecked()
        config.setting['fix_missing_seekpoints_flac'] = self.ui.fix_missing_seekpoints_flac.isChecked()
        config.setting['preserved_tags'] = list(self.ui.preserved_tags.tags)
        self.tagger.window.enable_tag_saving_action.setChecked(not config.setting['dont_write_tags'])


register_options_page(TagsOptionsPage)
