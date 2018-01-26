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
from PyQt5 import QtCore, QtWidgets
from picard import config
from picard.util import webbrowser2, find_executable
from picard.const import FPCALC_NAMES
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_fingerprinting import Ui_FingerprintingOptionsPage


class FingerprintingOptionsPage(OptionsPage):

    NAME = "fingerprinting"
    TITLE = N_("Fingerprinting")
    PARENT = None
    SORT_ORDER = 45
    ACTIVE = True

    options = [
        config.BoolOption("setting", "ignore_existing_acoustid_fingerprints", False),
        config.TextOption("setting", "fingerprinting_system", "acoustid"),
        config.TextOption("setting", "acoustid_fpcalc", ""),
        config.TextOption("setting", "acoustid_apikey", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fpcalc_valid = True
        self.ui = Ui_FingerprintingOptionsPage()
        self.ui.setupUi(self)
        self.ui.disable_fingerprinting.clicked.connect(self.update_groupboxes)
        self.ui.use_acoustid.clicked.connect(self.update_groupboxes)
        self.ui.acoustid_fpcalc.textChanged.connect(self._acoustid_fpcalc_check)
        self.ui.acoustid_fpcalc_browse.clicked.connect(self.acoustid_fpcalc_browse)
        self.ui.acoustid_fpcalc_download.clicked.connect(self.acoustid_fpcalc_download)
        self.ui.acoustid_apikey_get.clicked.connect(self.acoustid_apikey_get)

    def load(self):
        if config.setting["fingerprinting_system"] == "acoustid":
            self.ui.use_acoustid.setChecked(True)
        else:
            self.ui.disable_fingerprinting.setChecked(True)
        self.ui.acoustid_fpcalc.setText(config.setting["acoustid_fpcalc"])
        self.ui.acoustid_apikey.setText(config.setting["acoustid_apikey"])
        self.ui.ignore_existing_acoustid_fingerprints.setChecked(config.setting["ignore_existing_acoustid_fingerprints"])
        self.update_groupboxes()

    def save(self):
        if self.ui.use_acoustid.isChecked():
            config.setting["fingerprinting_system"] = "acoustid"
        else:
            config.setting["fingerprinting_system"] = ""
        config.setting["acoustid_fpcalc"] = self.ui.acoustid_fpcalc.text()
        config.setting["acoustid_apikey"] = self.ui.acoustid_apikey.text()
        config.setting["ignore_existing_acoustid_fingerprints"] = self.ui.ignore_existing_acoustid_fingerprints.isChecked()

    def update_groupboxes(self):
        if self.ui.use_acoustid.isChecked():
            self.ui.acoustid_settings.setEnabled(True)
            if not self.ui.acoustid_fpcalc.text():
                fpcalc_path = find_executable(*FPCALC_NAMES)
                if fpcalc_path:
                    self.ui.acoustid_fpcalc.setText(fpcalc_path)
        else:
            self.ui.acoustid_settings.setEnabled(False)
        self._acoustid_fpcalc_check()

    def acoustid_fpcalc_browse(self):
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(self, "", self.ui.acoustid_fpcalc.text())
        if path:
            path = os.path.normpath(path)
            self.ui.acoustid_fpcalc.setText(path)

    def acoustid_fpcalc_download(self):
        webbrowser2.goto('chromaprint')

    def acoustid_apikey_get(self):
        webbrowser2.goto('acoustid_apikey')

    def _acoustid_fpcalc_check(self):
        if not self.ui.use_acoustid.isChecked():
            self._acoustid_fpcalc_set_success("")
            return
        fpcalc = self.ui.acoustid_fpcalc.text()
        if not fpcalc:
            self._acoustid_fpcalc_set_success("")
            return

        self._fpcalc_valid = False
        process = QtCore.QProcess(self)
        process.finished.connect(self._on_acoustid_fpcalc_check_finished)
        process.error.connect(self._on_acoustid_fpcalc_check_error)
        process.start(fpcalc, ["-v"])

    def _on_acoustid_fpcalc_check_finished(self, exit_code, exit_status):
        process = self.sender()
        if exit_code == 0 and exit_status == 0:
            output = string_(process.readAllStandardOutput())
            if output.startswith("fpcalc version"):
                self._acoustid_fpcalc_set_success(output.strip())
            else:
                self._acoustid_fpcalc_set_error()
        else:
            self._acoustid_fpcalc_set_error()

    def _on_acoustid_fpcalc_check_error(self, error):
        self._acoustid_fpcalc_set_error()

    def _acoustid_fpcalc_set_success(self, version):
        self._fpcalc_valid = True
        self.ui.acoustid_fpcalc_info.setStyleSheet("")
        self.ui.acoustid_fpcalc_info.setText(version)

    def _acoustid_fpcalc_set_error(self):
        self._fpcalc_valid = False
        self.ui.acoustid_fpcalc_info.setStyleSheet(self.STYLESHEET_ERROR)
        self.ui.acoustid_fpcalc_info.setText(_("Please select a valid fpcalc executable."))

    def check(self):
        if not self._fpcalc_valid:
            raise OptionsCheckError(_("Invalid fpcalc executable"), _("Please select a valid fpcalc executable."))

    def display_error(self, error):
        pass

register_options_page(FingerprintingOptionsPage)
