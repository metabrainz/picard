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

from PyQt6.QtGui import (
    QTextBlockFormat,
    QTextCursor,
)

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

from picard.ui.colors import interface_colors
from picard.ui.forms.ui_provider_options_local import Ui_LocalOptions
from picard.ui.options import PageOptionConfigs


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

    OPTIONS: PageOptionConfigs = {
        'local_cover_regex': {'widgets': ['local_cover_regex_edit']},
    }

    _options_ui = Ui_LocalOptions

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_regex_checker(self.ui.local_cover_regex_edit, self.ui.local_cover_regex_error)

        self.ui.local_cover_regex_edit.textChanged.connect(self.update_test_coverart_filter)
        self.ui.test_coverart_filter.setToolTip(_(TOOLTIP_TEST_COVERART_FILTER))
        self.ui.test_coverart_filter.setPlaceholderText(_("Enter file names to test, one per line"))
        self.ui.test_coverart_filter.textChanged.connect(self.update_test_coverart_filter)

        # FIXME: colors aren't great from accessibility POV
        self.fmt_match = QTextBlockFormat()
        self.fmt_match.setBackground(self._highlight_color('tagstatus_added'))

        self.fmt_skip = QTextBlockFormat()
        self.fmt_skip.setBackground(self._highlight_color('tagstatus_removed'))

        self.fmt_clear = QTextBlockFormat()
        self.fmt_clear.clearBackground()

    @staticmethod
    def _highlight_color(color_key):
        alpha = 90 if interface_colors.dark_theme else 60
        color = interface_colors.get_qcolor(color_key)
        color.setAlpha(alpha)
        return color

    def load(self):
        config = get_config()
        self.ui.local_cover_regex_edit.setText(config.setting['local_cover_regex'])

    def save(self):
        config = get_config()
        config.setting['local_cover_regex'] = self.ui.local_cover_regex_edit.text()

    def update_test_coverart_filter(self):
        test_text = self.ui.test_coverart_filter.toPlainText()

        regex_text = self.ui.local_cover_regex_edit.text()
        try:
            coverart_filter = re.compile(regex_text, re.IGNORECASE) if regex_text else None
        except re.error:
            coverart_filter = None

        def set_line_fmt(lineno, textformat):
            obj = self.ui.test_coverart_filter
            if lineno < 0:
                # use current cursor position
                cursor = obj.textCursor()
            else:
                cursor = QTextCursor(obj.document().findBlockByNumber(lineno))
            obj.blockSignals(True)
            cursor.setBlockFormat(textformat)
            obj.blockSignals(False)

        set_line_fmt(-1, self.fmt_clear)

        if not coverart_filter:
            return

        for lineno, line in enumerate(test_text.splitlines()):
            line = line.strip()
            fmt = self.fmt_clear
            if line:
                if coverart_filter.search(line):
                    fmt = self.fmt_match
                else:
                    fmt = self.fmt_skip
            set_line_fmt(lineno, fmt)


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
