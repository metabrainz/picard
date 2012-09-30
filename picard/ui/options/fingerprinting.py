# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2011 Lukáš Lalinský
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

import os
from PyQt4 import QtCore, QtGui
from picard.util import webbrowser2, find_executable
from picard.const import FPCALC_NAMES
from picard.config import BoolOption, TextOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_fingerprinting import Ui_FingerprintingOptionsPage


class FingerprintingOptionsPage(OptionsPage):

    NAME = "fingerprinting"
    TITLE = N_("Fingerprinting")
    PARENT = None
    SORT_ORDER = 45
    ACTIVE = True

    options = [
        TextOption("setting", "fingerprinting_system", "acoustid"),
        TextOption("setting", "acoustid_fpcalc", ""),
        TextOption("setting", "acoustid_apikey", ""),
    ]

    def __init__(self, parent=None):
        super(FingerprintingOptionsPage, self).__init__(parent)
        self.ui = Ui_FingerprintingOptionsPage()
        self.ui.setupUi(self)
        self.ui.disable_fingerprinting.clicked.connect(self.update_groupboxes)
        self.ui.use_acoustid.clicked.connect(self.update_groupboxes)
        self.ui.acoustid_fpcalc_browse.clicked.connect(self.acoustid_fpcalc_browse)
        self.ui.acoustid_fpcalc_download.clicked.connect(self.acoustid_fpcalc_download)
        self.ui.acoustid_apikey_get.clicked.connect(self.acoustid_apikey_get)

    def load(self):
        if self.config.setting["fingerprinting_system"] == "acoustid":
            self.ui.use_acoustid.setChecked(True)
        else:
            self.ui.disable_fingerprinting.setChecked(True)
        self.ui.acoustid_fpcalc.setText(self.config.setting["acoustid_fpcalc"])
        self.ui.acoustid_apikey.setText(self.config.setting["acoustid_apikey"])
        self.update_groupboxes()

    def save(self):
        if self.ui.use_acoustid.isChecked():
            self.config.setting["fingerprinting_system"] = "acoustid"
        else:
            self.config.setting["fingerprinting_system"] = ""
        self.config.setting["acoustid_fpcalc"] = unicode(self.ui.acoustid_fpcalc.text())
        self.config.setting["acoustid_apikey"] = unicode(self.ui.acoustid_apikey.text())

    def update_groupboxes(self):
        if self.ui.use_acoustid.isChecked():
            self.ui.acoustid_settings.setEnabled(True)
            if self.ui.acoustid_fpcalc.text().isEmpty():
                fpcalc_path = find_executable(*FPCALC_NAMES)
                if fpcalc_path:
                    self.ui.acoustid_fpcalc.setText(fpcalc_path)
        else:
            self.ui.acoustid_settings.setEnabled(False)

    def acoustid_fpcalc_browse(self):
        path = QtGui.QFileDialog.getOpenFileName(self, "", self.ui.acoustid_fpcalc.text())
        if path:
            path = os.path.normpath(unicode(path))
            self.ui.acoustid_fpcalc.setText(path)

    def acoustid_fpcalc_download(self):
        webbrowser2.open("http://acoustid.org/chromaprint#download")

    def acoustid_apikey_get(self):
        webbrowser2.open("http://acoustid.org/api-key")


register_options_page(FingerprintingOptionsPage)
