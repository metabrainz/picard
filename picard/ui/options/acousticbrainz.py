# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2011-2012 Lukáš Lalinský
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018, 2020-2021 Laurent Monin
# Copyright (C) 2015, 2020-2021 Philipp Wolfer
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2021 Gabriel Ferreira
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

from PyQt5 import QtWidgets

from picard.acousticbrainz import (
    ab_check_version,
    ab_setup_extractor,
    find_extractor,
)
from picard.config import (
    BoolOption,
    TextOption,
    get_config,
)
from picard.const import ACOUSTICBRAINZ_DOWNLOAD_URL
from picard.util import webbrowser2

from picard.ui.options import (
    OptionsCheckError,
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_acousticbrainz import Ui_AcousticBrainzOptionsPage


class AcousticBrainzOptionsPage(OptionsPage):

    NAME = "acousticbrainz"
    TITLE = N_("AcousticBrainz")
    PARENT = None
    SORT_ORDER = 45
    ACTIVE = True
    HELP_URL = '/config/options_acousticbrainz.html'

    options = [
        BoolOption("setting", "use_acousticbrainz", False),
        TextOption("setting", "acousticbrainz_extractor", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._extractor_valid = True
        self.ui = Ui_AcousticBrainzOptionsPage()
        self.ui.setupUi(self)
        self.ui.disable_acoustic_features.clicked.connect(self.update_groupboxes)
        self.ui.use_acoustic_features.clicked.connect(self.update_groupboxes)
        self.ui.acousticbrainz_extractor.textEdited.connect(self._acousticbrainz_extractor_check)
        self.ui.acousticbrainz_extractor_browse.clicked.connect(self.acousticbrainz_extractor_browse)
        self.ui.acousticbrainz_extractor_download.clicked.connect(self.acousticbrainz_extractor_download)
        self.ui.acousticbrainz_extractor_download.setToolTip(
            _("Open AcousticBrainz website in browser to download extractor binary")
        )
        self._config = get_config()

    def load(self):
        if self._config.setting["use_acousticbrainz"]:
            self.ui.use_acoustic_features.setChecked(True)
        else:
            self.ui.disable_acoustic_features.setChecked(True)

        extractor_path = self._config.setting["acousticbrainz_extractor"]
        if not extractor_path or not ab_check_version(extractor_path):
            self.ui.acousticbrainz_extractor.clear()
        else:
            self.ui.acousticbrainz_extractor.setText(extractor_path)

        self.update_groupboxes()

    def save(self):
        enabled = self.ui.acousticbrainz_settings.isEnabled()
        changed = self._config.setting["use_acousticbrainz"] != enabled
        if changed:
            self._config.setting["use_acousticbrainz"] = enabled
            self.tagger.window.update_actions()
        if enabled:
            self._config.setting["acousticbrainz_extractor"] = self.ui.acousticbrainz_extractor.text()
            ab_setup_extractor()

    def update_groupboxes(self):
        enabled = self.ui.use_acoustic_features.isChecked()
        self.ui.acousticbrainz_settings.setEnabled(enabled)
        self._acousticbrainz_extractor_check()

    def acousticbrainz_extractor_browse(self):
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(self, "", self.ui.acousticbrainz_extractor.text())
        if path:
            path = os.path.normpath(path)
            self.ui.acousticbrainz_extractor.setText(path)
            self._acousticbrainz_extractor_check()

    def acousticbrainz_extractor_download(self):
        webbrowser2.open(ACOUSTICBRAINZ_DOWNLOAD_URL)

    def _acousticbrainz_extractor_check(self):
        enabled = self.ui.acousticbrainz_settings.isEnabled()
        self.ui.acousticbrainz_extractor.setPlaceholderText(_("Path to streaming_extractor_music(.exe)"))

        if not enabled:
            self._acousticbrainz_extractor_set_success("")
            return

        extractor_path = self.ui.acousticbrainz_extractor.text()
        try_find = not extractor_path
        if try_find:
            extractor_path = find_extractor()

        if extractor_path:
            version = ab_check_version(extractor_path)
            if version:
                if try_find:
                    # extractor path will not be saved to config file if it was auto-detected
                    self.ui.acousticbrainz_extractor.clear()
                    self.ui.acousticbrainz_extractor.setPlaceholderText(extractor_path)
                self._acousticbrainz_extractor_set_success(_("Extractor version: %s") % version)
                return
        self._acousticbrainz_extractor_set_error()

    def _acousticbrainz_extractor_set_success(self, version):
        self._extractor_valid = True
        self.ui.acousticbrainz_extractor_info.setStyleSheet("")
        self.ui.acousticbrainz_extractor_info.setText(version)

    def _acousticbrainz_extractor_set_error(self):
        self._extractor_valid = False
        self.ui.acousticbrainz_extractor_info.setStyleSheet(self.STYLESHEET_ERROR)
        self.ui.acousticbrainz_extractor_info.setText(_("Please select a valid extractor executable."))

    def check(self):
        if not self._extractor_valid:
            raise OptionsCheckError(_("Invalid extractor executable"), _("Please select a valid extractor executable."))

    def display_error(self, error):
        pass


register_options_page(AcousticBrainzOptionsPage)
