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

from collections import defaultdict
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPalette
from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_cover import Ui_CoverOptionsPage
from picard.coverart.providers import cover_art_providers, is_provider_enabled
from picard.ui.sortablecheckboxlist import (
    SortableCheckboxListWidget,
    SortableCheckboxListItem
)



class CoverOptionsPage(OptionsPage):

    NAME = "cover"
    TITLE = N_("Cover Art")
    PARENT = None
    SORT_ORDER = 35
    ACTIVE = True

    options = [
        config.BoolOption("setting", "save_images_to_tags", True),
        config.BoolOption("setting", "save_only_front_images_to_tags", True),
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
        super(CoverOptionsPage, self).__init__(parent)
        self.ui = Ui_CoverOptionsPage()
        self.ui.setupUi(self)
        self.ui.save_images_to_files.clicked.connect(self.update_filename)

    def update_providers_options(self, items):
        new = []
        for item in items:
            new.append((item.data, item.checked))
        config.setting['ca_providers'] = new

    def load_cover_art_providers(self):
        """Load available providers, initialize tabs, restore state of each
        """
        widget = SortableCheckboxListWidget()
        self.provider_options = defaultdict(list)
        providers = cover_art_providers()
        for provider in providers:
            if hasattr(provider, 'TITLE'):
                title = _(provider.TITLE)
            else:
                title = provider.NAME

            widget.addItem(SortableCheckboxListItem(title,
                                                    checked=is_provider_enabled(provider.NAME),
                                                    data=provider.NAME))
        self.ui.ca_providers_list.insertWidget(0, widget)
        widget.changed.connect(self.update_providers_options)

    def load(self):
        self.ui.save_images_to_tags.setChecked(config.setting["save_images_to_tags"])
        self.ui.cb_embed_front_only.setChecked(config.setting["save_only_front_images_to_tags"])
        self.ui.save_images_to_files.setChecked(config.setting["save_images_to_files"])
        self.ui.cover_image_filename.setText(config.setting["cover_image_filename"])
        self.ui.save_images_overwrite.setChecked(config.setting["save_images_overwrite"])
        self.update_filename()
        self.load_cover_art_providers()

    def save(self):
        config.setting["save_images_to_tags"] = self.ui.save_images_to_tags.isChecked()
        config.setting["save_only_front_images_to_tags"] = self.ui.cb_embed_front_only.isChecked()
        config.setting["save_images_to_files"] = self.ui.save_images_to_files.isChecked()
        config.setting["cover_image_filename"] = unicode(self.ui.cover_image_filename.text())
        config.setting["save_images_overwrite"] = self.ui.save_images_overwrite.isChecked()

    def update_filename(self):
        enabled = self.ui.save_images_to_files.isChecked()
        self.ui.cover_image_filename.setEnabled(enabled)
        self.ui.save_images_overwrite.setEnabled(enabled)


register_options_page(CoverOptionsPage)
