# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021, 2025-2026 Philipp Wolfer
# Copyright (C) 2020-2021, 2023-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from typing import ClassVar

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_interface_top_tags import Ui_InterfaceTopTagsOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)


class InterfaceTopTagsOptionsPage(OptionsPage):
    NAME = 'interface_top_tags'
    TITLE = N_("Top Tags")
    PARENT = 'interface'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_interface_top_tags.html"

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'metadatabox_top_tags': {'widgets': ['top_tags_groupBox']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_InterfaceTopTagsOptionsPage()
        self.ui.setupUi(self)

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
