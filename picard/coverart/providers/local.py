# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2015, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2019-2021 Philipp Wolfer
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
import re

from picard.config import get_config
from picard.const.defaults import DEFAULT_LOCAL_COVER_ART_REGEX
from picard.coverart.image import LocalFileCoverArtImage
from picard.coverart.providers.provider import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import CAA_TYPES
from picard.i18n import N_

from picard.ui.forms.ui_provider_options_local import Ui_LocalOptions


class ProviderOptionsLocal(ProviderOptions):
    """
    Options for Local Files cover art provider
    """

    HELP_URL = '/config/options_local_files.html'

    _options_ui = Ui_LocalOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_regex_checker(self.ui.local_cover_regex_edit, self.ui.local_cover_regex_error)
        self.ui.local_cover_regex_default.clicked.connect(self.set_local_cover_regex_default)

    def set_local_cover_regex_default(self):
        self.ui.local_cover_regex_edit.setText(DEFAULT_LOCAL_COVER_ART_REGEX)

    def load(self):
        config = get_config()
        self.ui.local_cover_regex_edit.setText(config.setting['local_cover_regex'])

    def save(self):
        config = get_config()
        config.setting['local_cover_regex'] = self.ui.local_cover_regex_edit.text()


class CoverArtProviderLocal(CoverArtProvider):
    """Get cover art from local files"""

    NAME = "Local Files"
    TITLE = N_("Local Files")
    OPTIONS = ProviderOptionsLocal

    _types_split_re = re.compile('[^a-z0-9]', re.IGNORECASE)
    _known_types = {t['name'] for t in CAA_TYPES}
    _default_types = ['front']

    def queue_images(self):
        config = get_config()
        regex = config.setting['local_cover_regex']
        if regex:
            _match_re = re.compile(regex, re.IGNORECASE)
            dirs_done = set()

            for file in self.album.iterfiles():
                current_dir = os.path.dirname(file.filename)
                if current_dir in dirs_done:
                    continue
                dirs_done.add(current_dir)
                for image in self.find_local_images(current_dir, _match_re):
                    self.queue_put(image)
        return CoverArtProvider.QueueState.FINISHED

    def get_types(self, string):
        found = {x.lower() for x in self._types_split_re.split(string) if x}
        return list(found.intersection(self._known_types))

    def find_local_images(self, current_dir, match_re):
        for root, _dirs, files in os.walk(current_dir):
            for filename in files:
                m = match_re.search(filename)
                if not m:
                    continue
                filepath = os.path.join(current_dir, root, filename)
                if not os.path.exists(filepath):
                    continue
                try:
                    type_from_filename = self.get_types(m.group(1))
                except IndexError:
                    type_from_filename = []
                yield LocalFileCoverArtImage(
                    filepath,
                    types=type_from_filename or self._default_types,
                    support_types=True,
                    support_multi_types=True,
                )
