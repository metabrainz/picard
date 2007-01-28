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

import sys
from PyQt4 import QtGui
from picard.config import TextOption
from picard.ui.options import OptionsPage, register_options_page
if sys.platform == "win32":
    import win32file
    from picard.ui.ui_options_cdlookup_win32 import Ui_CDLookupOptionsPage
else:
    from picard.ui.ui_options_cdlookup import Ui_CDLookupOptionsPage


class CDLookupOptionsPage(OptionsPage):

    NAME = "cdlookup"
    TITLE = N_("CD Lookup")
    PARENT = None
    SORT_ORDER = 50
    ACTIVE = True

    options = [
        TextOption("setting", "cd_lookup_device", ""),
    ]

    def __init__(self, parent=None):
        super(CDLookupOptionsPage, self).__init__(parent)
        self.ui = Ui_CDLookupOptionsPage()
        self.ui.setupUi(self)
        if sys.platform == "win32":
            self.drives = self.__get_cdrom_drives()
            self.ui.cd_lookup_device.addItems(self.drives)

    def load(self):
        if sys.platform == "win32":
            try:
                self.ui.cd_lookup_device.setCurrentIndex(self.drives.index(self.config.setting["cd_lookup_device"]))
            except ValueError:
                pass
        else:
            self.ui.cd_lookup_device.setText(self.config.setting["cd_lookup_device"])

    def save(self):
        if sys.platform == "win32":
            self.config.setting["cd_lookup_device"] = unicode(self.ui.cd_lookup_device.currentText())
        else:
            self.config.setting["cd_lookup_device"] = unicode(self.ui.cd_lookup_device.text())

    def __get_cdrom_drives(self):
        drives = []
        mask = win32file.GetLogicalDrives()
        for i in range(26):
            if mask >> i & 1:
                drive = unicode(chr(i + ord("A"))) + u":\\"
                if win32file.GetDriveType(drive) == win32file.DRIVE_CDROM:
                    drives.append(drive)
        return drives


register_options_page(CDLookupOptionsPage)
