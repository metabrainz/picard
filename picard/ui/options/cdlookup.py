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
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.config import TextOption

class CDLookupOptionsPage(Component):

    implements(IOptionsPage)

    options = [
        TextOption("setting", "cd_lookup_device", ""),
    ]

    def get_page_info(self):
        return (_(u"CD Lookup"), "cdlookup", None, 50)

    def get_page_widget(self, parent=None):
        self.widget = QtGui.QWidget(parent)
        if sys.platform == "win32":
            from picard.ui.ui_options_cdlookup_win32 import Ui_Form
            self.ui = Ui_Form()
            self.ui.setupUi(self.widget)
            self.drives = self.__get_cdrom_drives()
            self.ui.cd_lookup_device.addItems(self.drives)
        else:
            from picard.ui.ui_options_cdlookup import Ui_Form
            self.ui = Ui_Form()
            self.ui.setupUi(self.widget)
        return self.widget

    def load_options(self):
        if sys.platform == "win32":
            try:
                self.ui.cd_lookup_device.setCurrentIndex(
                    self.drives.index(self.config.setting["cd_lookup_device"]))
            except ValueError:
                pass
        else:
            self.ui.cd_lookup_device.setText(
                self.config.setting["cd_lookup_device"])

    def save_options(self):
        if sys.platform == "win32":
            self.config.setting["cd_lookup_device"] = unicode(
                self.ui.cd_lookup_device.currentText())
        else:
            self.config.setting["cd_lookup_device"] = unicode(
                self.ui.cd_lookup_device.text())

    def __get_cdrom_drives(self):
        import win32file
        drives = []
        mask = win32file.GetLogicalDrives()
        for i in range(26):
            if mask >> i & 1:
                drive = unicode(chr(i + ord("A"))) + u":\\"
                if win32file.GetDriveType(drive) == win32file.DRIVE_CDROM:
                    drives.append(drive)
        return drives

