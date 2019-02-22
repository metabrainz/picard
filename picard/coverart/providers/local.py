# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2015 Laurent Monin
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

from picard import config
from picard.coverart.image import LocalFileCoverArtImage
from picard.coverart.providers import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import CAA_TYPES

from picard.ui.ui_provider_options_local import Ui_LocalOptions


class ProviderOptionsLocal(ProviderOptions):
    """
        Options for Local Files cover art provider
    """

    _DEFAULT_LOCAL_COVER_ART_REGEX = r'^(?:cover|folder|albumart)(.*)\.(?:jpe?g|png|gif|tiff?)$'

    options = [
        config.TextOption("setting", "local_cover_regex",
                          _DEFAULT_LOCAL_COVER_ART_REGEX),
    ]

    _options_ui = Ui_LocalOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_regex_checker(self.ui.local_cover_regex_edit, self.ui.local_cover_regex_error)
        self.ui.local_cover_regex_default.clicked.connect(self.set_local_cover_regex_default)

    def set_local_cover_regex_default(self):
        self.ui.local_cover_regex_edit.setText(self._DEFAULT_LOCAL_COVER_ART_REGEX)

    def load(self):
        self.ui.local_cover_regex_edit.setText(config.setting["local_cover_regex"])

    def save(self):
        config.setting["local_cover_regex"] = self.ui.local_cover_regex_edit.text()


class CoverArtProviderLocal(CoverArtProvider):

    """Get cover art from local files"""

    NAME = "Local"
    TITLE = N_("Local Files")
    OPTIONS = ProviderOptionsLocal

    _types_split_re = re.compile('[^a-z0-9]', re.IGNORECASE)
    _known_types = set([t['name'] for t in CAA_TYPES])

    def enabled(self):
        enabled = CoverArtProvider.enabled(self)
        return enabled and not self.coverart.front_image_found

    def queue_images(self):
        _match_re = re.compile(config.setting['local_cover_regex'], re.IGNORECASE)
        dirs_done = set()

        for file in self.album.iterfiles():
            current_dir = os.path.dirname(file.filename)
            if current_dir in dirs_done:
                continue
            dirs_done.add(current_dir)
            for root, dirs, files in os.walk(current_dir):
                for filename in files:
                    m = _match_re.search(filename)
                    if not m:
                        continue
                    filepath = os.path.join(current_dir, root, filename)
                    if os.path.exists(filepath):
                        types = self.get_types(m.group(1)) or ['front']
                        self.queue_put(
                            LocalFileCoverArtImage(filepath,
                                                   types=types,
                                                   support_types=True,
                                                   support_multi_types=True))
        return CoverArtProvider.FINISHED

    def get_types(self, string):
        found = set([x.lower() for x in self._types_split_re.split(string) if x])
        return list(found.intersection(self._known_types))
