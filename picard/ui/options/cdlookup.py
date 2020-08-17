# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2008, 2019 Philipp Wolfer
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013, 2018-2019 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
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
    HELP_URL = '/config/options_cdlookup.html'

    options = [
        config.TextOption("setting", "cd_lookup_device", ",".join(DEFAULT_DRIVES)),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CDLookupOptionsPage()
        self.ui.setupUi(self)
        if AUTO_DETECT_DRIVES:
            self._device_list = get_cdrom_drives()
            self.ui.cd_lookup_device.addItems(self._device_list)

    def load(self):
        device = config.setting["cd_lookup_device"]
        if AUTO_DETECT_DRIVES:
            try:
                self.ui.cd_lookup_device.setCurrentIndex(self._device_list.index(device))
            except ValueError:
                pass
        else:
            self.ui.cd_lookup_device.setText(device)

    def save(self):
        if AUTO_DETECT_DRIVES:
            device = self.ui.cd_lookup_device.currentText()
            device_list = self._device_list
        else:
            device = self.ui.cd_lookup_device.text()
            device_list = [device]
        config.setting["cd_lookup_device"] = device
        self.tagger.window.update_cd_lookup_drives(device_list)


register_options_page(CDLookupOptionsPage)
