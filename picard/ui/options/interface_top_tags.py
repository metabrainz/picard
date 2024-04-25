# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021 Philipp Wolfer
# Copyright (C) 2020-2021, 2023-2024 Laurent Monin
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
from picard.i18n import N_
from picard.profile import register_profile_highlights

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_interface_top_tags import (
    Ui_InterfaceTopTagsOptionsPage,
)


class InterfaceTopTagsOptionsPage(OptionsPage):

    NAME = 'interface_top_tags'
    TITLE = N_("Top Tags")
    PARENT = 'interface'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_interface_top_tags.html"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_InterfaceTopTagsOptionsPage()
        self.ui.setupUi(self)

        register_profile_highlights('interface', 'metadatabox_top_tags', ['top_tags_groupBox'])

    def load(self):
        config = get_config()
        tags = config.setting['metadatabox_top_tags']
        self.ui.top_tags_list.update(tags)

    def save(self):
        config = get_config()
        tags = list(self.ui.top_tags_list.tags)
        if tags != config.setting['metadatabox_top_tags']:
            config.setting['metadatabox_top_tags'] = tags
            self.tagger.window.metadata_box.update()

    def restore_defaults(self):
        self.ui.top_tags_list.clear()
        super().restore_defaults()


register_options_page(InterfaceTopTagsOptionsPage)
