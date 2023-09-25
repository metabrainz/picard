# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2019-2021 Philipp Wolfer
# Copyright (C) 2021 Laurent Monin
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
    get_config,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_tags_compatibility_aac import (
    Ui_TagsCompatibilityOptionsPage,
)


class TagsCompatibilityAACOptionsPage(OptionsPage):

    NAME = 'tags_compatibility_aac'
    TITLE = N_("AAC")
    PARENT = 'tags'
    SORT_ORDER = 40
    ACTIVE = True
    HELP_URL = "/config/options_tags_compatibility_aac.html"

    options = [
        BoolOption('setting', 'aac_save_ape', True),
        BoolOption('setting', 'remove_ape_from_aac', False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TagsCompatibilityOptionsPage()
        self.ui.setupUi(self)
        self.ui.aac_no_tags.toggled.connect(self.ui.remove_ape_from_aac.setEnabled)

    def load(self):
        config = get_config()
        if config.setting['aac_save_ape']:
            self.ui.aac_save_ape.setChecked(True)
        else:
            self.ui.aac_no_tags.setChecked(True)
        self.ui.remove_ape_from_aac.setChecked(config.setting['remove_ape_from_aac'])
        self.ui.remove_ape_from_aac.setEnabled(not config.setting['aac_save_ape'])

    def save(self):
        config = get_config()
        config.setting['aac_save_ape'] = self.ui.aac_save_ape.isChecked()
        config.setting['remove_ape_from_aac'] = self.ui.remove_ape_from_aac.isChecked()


register_options_page(TagsCompatibilityAACOptionsPage)
