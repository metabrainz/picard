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
from typing import ClassVar

from picard.config import get_config
from picard.coverart.image import LocalFileCoverArtImage
from picard.coverart.providers.provider import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import CAA_TYPES
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.forms.ui_provider_options_local import Ui_LocalOptions
from picard.ui.options import PageOptionConfigs
from picard.ui.playground import Playground


TOOLTIP_TEST_COVERART_FILTER = N_("""<html><head/><body>
<p>Enter file names to test the regex against, one per line.<br/>
This playground will not be preserved on exit.
</p>
<p>
Red background means the file name does not match.<br/>
Green background means the file name matches.
</p>
</body></html>""")


class ProviderOptionsLocal(ProviderOptions):
    """
    Options for Local Files cover art provider
    """

    NAME = "provider_local"
    HELP_URL = '/config/options_local_files.html'

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'local_cover_regex': {'widgets': ['local_cover_regex_edit']},
    }

    _options_ui = Ui_LocalOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_regex_checker(self.ui.local_cover_regex_edit, self.ui.local_cover_regex_error)

        self.ui.local_cover_regex_edit.textChanged.connect(self._update_test_coverart_filter)
        self.ui.test_coverart_filter.setToolTip(_(TOOLTIP_TEST_COVERART_FILTER))
        self.ui.test_coverart_filter.setPlaceholderText(_("Enter file names to test, one per line"))
        self.ui.test_coverart_filter.textChanged.connect(self._update_test_coverart_filter)

        self.playground = Playground(self.ui.test_coverart_filter)

    def load(self):
        config = get_config()
        self.ui.local_cover_regex_edit.setText(config.setting['local_cover_regex'])

    def save(self):
        config = get_config()
        config.setting['local_cover_regex'] = self.ui.local_cover_regex_edit.text()

    def _update_test_coverart_filter(self):
        regex_text = self.ui.local_cover_regex_edit.text()
        try:
            coverart_filter = re.compile(regex_text, re.IGNORECASE) if regex_text else None
        except re.error:
            coverart_filter = None

        def check_line(line: str) -> bool:
            return bool(coverart_filter.search(line))

        self.playground.update(check_line if coverart_filter else None)


class CoverArtProviderLocal(CoverArtProvider):
    """Get cover art from local files"""

    NAME = "Local Files"
    TITLE = N_("Local Files")
    OPTIONS = ProviderOptionsLocal

    _types_split_re = re.compile('[^a-z0-9]', re.IGNORECASE)
    _known_types = frozenset(t['name'] for t in CAA_TYPES)
    _default_types = tuple('front')

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
