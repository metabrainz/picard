# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (c) 2004 Robert Kaye
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
from picard.util.cdrom import (
    AUTO_DETECT_DRIVES,
    DEFAULT_DRIVES,
    get_cdrom_drives,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)

if AUTO_DETECT_DRIVES:
    from picard.ui.ui_options_cdlookup_select import Ui_CDLookupOptionsPage
else:
    from picard.ui.ui_options_cdlookup import Ui_CDLookupOptionsPage


class CDLookupOptionsPage(OptionsPage):

    NAME = "cdlookup"
    TITLE = N_("CD Lookup")
    PARENT = None
    SORT_ORDER = 50
    ACTIVE = True

    options = [
        config.TextOption("setting", "cd_lookup_device",
                          ",".join(DEFAULT_DRIVES)),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CDLookupOptionsPage()
        self.ui.setupUi(self)
        if AUTO_DETECT_DRIVES:
            self.drives = get_cdrom_drives()
            self.ui.cd_lookup_device.addItems(self.drives)

    def load(self):
        if AUTO_DETECT_DRIVES:
            try:
                self.ui.cd_lookup_device.setCurrentIndex(self.drives.index(config.setting["cd_lookup_device"]))
            except ValueError:
                pass
        else:
            self.ui.cd_lookup_device.setText(config.setting["cd_lookup_device"])

    def save(self):
        if AUTO_DETECT_DRIVES:
            config.setting["cd_lookup_device"] = self.ui.cd_lookup_device.currentText()
        else:
            config.setting["cd_lookup_device"] = self.ui.cd_lookup_device.text()


register_options_page(CDLookupOptionsPage)
