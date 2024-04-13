# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2010, 2018-2021 Philipp Wolfer
# Copyright (C) 2012, 2014 Wieland Hoffmann
# Copyright (C) 2012-2014 Michael Wiencek
# Copyright (C) 2013-2015, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2021 Bob Swift
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
    Option,
    TextOption,
    get_config,
)
from picard.const import DEFAULT_COVER_IMAGE_FILENAME
from picard.coverart.providers import cover_art_providers

from picard.ui.checkbox_list_item import CheckboxListItem
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_cover import Ui_CoverOptionsPage
from picard.ui.util import qlistwidget_items


DEFAULT_CA_PROVIDERS = [
    ('Cover Art Archive', True),
    ('UrlRelationships', True),
    ('CaaReleaseGroup', True),
    ('Local', False),
]


class CoverOptionsPage(OptionsPage):

    NAME = 'cover'
    TITLE = N_("Cover Art")
    PARENT = None
    SORT_ORDER = 35
    ACTIVE = True
    HELP_URL = "/config/options_cover.html"

    options = [
        BoolOption('setting', 'save_images_to_tags', True, title=N_("Embed cover images into tags")),
        BoolOption('setting', 'embed_only_one_front_image', True, title=N_("Embed only a single front image")),
        BoolOption('setting', 'save_images_to_files', False, title=N_("Save cover images as separate files")),
        TextOption('setting', 'cover_image_filename', DEFAULT_COVER_IMAGE_FILENAME, title=N_("File name for images")),
        BoolOption('setting', 'save_images_overwrite', False, title=N_("Overwrite existing image files")),
        BoolOption('setting', 'save_only_one_front_image', False, title=N_("Save only a single front image as separate file")),
        BoolOption('setting', 'image_type_as_filename', False, title=N_("Always use the primary image type as the file name for non-front images")),
        ListOption('setting', 'ca_providers', DEFAULT_CA_PROVIDERS, title=N_("Cover art providers")),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.cover_image_filename.setPlaceholderText(Option.get('setting', 'cover_image_filename').default)
        self.ui.save_images_to_files.clicked.connect(self.update_ca_providers_groupbox_state)
        self.ui.save_images_to_tags.clicked.connect(self.update_ca_providers_groupbox_state)
        self.ui.save_only_one_front_image.toggled.connect(self.ui.image_type_as_filename.setDisabled)
        self.move_view = MoveableListView(self.ui.ca_providers_list, self.ui.up_button,
                                          self.ui.down_button)

    def restore_defaults(self):
        # Remove previous entries
        self.ui.ca_providers_list.clear()
        super().restore_defaults()

    def _load_cover_art_providers(self):
        """Load available providers, initialize provider-specific options, restore state of each
        """
        self.ui.ca_providers_list.clear()
        for p in cover_art_providers():
            item = CheckboxListItem(_(p.title), checked=p.enabled, data=p.name)
            self.ui.ca_providers_list.addItem(item)

    def load(self):
        config = get_config()
        self.ui.save_images_to_tags.setChecked(config.setting['save_images_to_tags'])
        self.ui.cb_embed_front_only.setChecked(config.setting['embed_only_one_front_image'])
        self.ui.save_images_to_files.setChecked(config.setting['save_images_to_files'])
        self.ui.cover_image_filename.setText(config.setting['cover_image_filename'])
        self.ui.save_images_overwrite.setChecked(config.setting['save_images_overwrite'])
        self.ui.save_only_one_front_image.setChecked(config.setting['save_only_one_front_image'])
        self.ui.image_type_as_filename.setChecked(config.setting['image_type_as_filename'])
        self._load_cover_art_providers()
        self.ui.ca_providers_list.setCurrentRow(0)
        self.update_ca_providers_groupbox_state()

    def _ca_providers(self):
        for item in qlistwidget_items(self.ui.ca_providers_list):
            yield (item.data, item.checked)

    def save(self):
        config = get_config()
        config.setting['save_images_to_tags'] = self.ui.save_images_to_tags.isChecked()
        config.setting['embed_only_one_front_image'] = self.ui.cb_embed_front_only.isChecked()
        config.setting['save_images_to_files'] = self.ui.save_images_to_files.isChecked()
        config.setting['cover_image_filename'] = self.ui.cover_image_filename.text()
        config.setting['save_images_overwrite'] = self.ui.save_images_overwrite.isChecked()
        config.setting['save_only_one_front_image'] = self.ui.save_only_one_front_image.isChecked()
        config.setting['image_type_as_filename'] = self.ui.image_type_as_filename.isChecked()
        config.setting['ca_providers'] = list(self._ca_providers())

    def update_ca_providers_groupbox_state(self):
        files_enabled = self.ui.save_images_to_files.isChecked()
        tags_enabled = self.ui.save_images_to_tags.isChecked()
        self.ui.ca_providers_groupbox.setEnabled(files_enabled or tags_enabled)


register_options_page(CoverOptionsPage)
