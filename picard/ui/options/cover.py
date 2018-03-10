# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_cover import Ui_CoverOptionsPage
from picard.coverart.providers import cover_art_providers, is_provider_enabled
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.checkbox_list_item import CheckboxListItem


class CoverOptionsPage(OptionsPage):

    NAME = "cover"
    TITLE = N_("Cover Art")
    PARENT = None
    SORT_ORDER = 35
    ACTIVE = True

    options = [
        config.BoolOption("setting", "save_images_to_tags", True),
        config.BoolOption("setting", "embed_only_one_front_image", True),
        config.BoolOption("setting", "save_images_to_files", False),
        config.TextOption("setting", "cover_image_filename", "cover"),
        config.BoolOption("setting", "save_images_overwrite", False),
        config.ListOption("setting", "ca_providers", [
            ('Cover Art Archive', True),
            ('Amazon', True),
            ('Whitelist', True),
            ('CaaReleaseGroup', False),
            ('Local', False),
        ]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.save_images_to_files.clicked.connect(self.update_filename)
        self.ui.save_images_to_tags.clicked.connect(self.update_save_images_to_tags)
        self.move_view = MoveableListView(self.ui.ca_providers_list, self.ui.up_button,
                                          self.ui.down_button)

    def load_cover_art_providers(self):
        """Load available providers, initialize provider-specific options, restore state of each
        """
        providers = cover_art_providers()
        for provider in providers:
            try:
                title = _(provider.TITLE)
            except AttributeError:
                title = provider.NAME
            checked = is_provider_enabled(provider.NAME)
            self.ui.ca_providers_list.addItem(CheckboxListItem(title, checked=checked, data=provider.NAME))

    def restore_defaults(self):
        # Remove previous entries
        self.provider_list_widget.clear()
        super().restore_defaults()

    def ca_providers(self):
        items = []
        for i in range(self.ui.ca_providers_list.count()):
            item = self.ui.ca_providers_list.item(i)
            items.append((item.data, item.checked))
        return items

    def load(self):
        self.ui.save_images_to_tags.setChecked(config.setting["save_images_to_tags"])
        self.ui.cb_embed_front_only.setChecked(config.setting["embed_only_one_front_image"])
        self.ui.save_images_to_files.setChecked(config.setting["save_images_to_files"])
        self.ui.cover_image_filename.setText(config.setting["cover_image_filename"])
        self.ui.save_images_overwrite.setChecked(config.setting["save_images_overwrite"])
        self.load_cover_art_providers()
        self.ui.ca_providers_list.setCurrentRow(0)
        self.update_all()

    def save(self):
        config.setting["save_images_to_tags"] = self.ui.save_images_to_tags.isChecked()
        config.setting["embed_only_one_front_image"] = self.ui.cb_embed_front_only.isChecked()
        config.setting["save_images_to_files"] = self.ui.save_images_to_files.isChecked()
        config.setting["cover_image_filename"] = self.ui.cover_image_filename.text()
        config.setting["save_images_overwrite"] = self.ui.save_images_overwrite.isChecked()
        config.setting["ca_providers"] = self.ca_providers()

    def update_all(self):
        self.update_filename()
        self.update_save_images_to_tags()

    def update_filename(self):
        enabled = self.ui.save_images_to_files.isChecked()
        self.ui.cover_image_filename.setEnabled(enabled)
        self.ui.save_images_overwrite.setEnabled(enabled)

    def update_save_images_to_tags(self):
        enabled = self.ui.save_images_to_tags.isChecked()
        self.ui.cb_embed_front_only.setEnabled(enabled)

register_options_page(CoverOptionsPage)
