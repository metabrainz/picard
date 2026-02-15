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
from picard.metadata import Metadata
from picard.util.scripttofilename import script_to_filename

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
        self.ui.local_cover_use_script.toggled.connect(self._update_visibility)
        self.ui.local_cover_script_edit.textChanged.connect(self._update_script_preview)

        self.ui.local_cover_regex_edit.textChanged.connect(self._update_test_coverart_filter)
        self.ui.test_coverart_filter.setToolTip(_(TOOLTIP_TEST_COVERART_FILTER))
        self.ui.test_coverart_filter.setPlaceholderText(_("Enter file names to test, one per line"))
        self.ui.test_coverart_filter.textChanged.connect(self._update_test_coverart_filter)

        self.playground = Playground(self.ui.test_coverart_filter)

        self._update_visibility()

    def _get_example_metadata(self):
        """Create sample metadata for script preview."""
        metadata = Metadata()
        metadata['album'] = 'Abbey Road'
        metadata['albumartist'] = 'The Beatles'
        metadata['artist'] = 'The Beatles'
        metadata['title'] = 'Come Together'
        metadata['date'] = '1969'
        metadata['originaldate'] = '1969-09-26'
        metadata['releasetype'] = 'album'
        metadata['releasestatus'] = 'official'
        metadata['~releasecomment'] = 'releasecomment'
        metadata['releasecountry'] = 'GB'
        metadata['label'] = 'Apple Records'
        metadata['catalognumber'] = 'PCS 7088'
        metadata['barcode'] = 'barcode'
        metadata['media'] = 'CD'
        metadata['discnumber'] = '1'
        metadata['totaldiscs'] = '1'
        metadata['tracknumber'] = '1'
        metadata['totaltracks'] = '17'
        return metadata

    def _update_script_preview(self):
        """Update the script preview with sample metadata."""
        script = self.ui.local_cover_script_edit.toPlainText()
        if not script:
            self.ui.script_preview_value.setText("")
            self.ui.script_preview_value.setStyleSheet("")
            return

        try:
            result = script_to_filename(script, self._get_example_metadata())
            if result:
                self.ui.script_preview_value.setText(result)
                self.ui.script_preview_value.setStyleSheet("font-weight: bold;")
            else:
                self.ui.script_preview_value.setText(_("(empty result - script will not match any files)"))
                self.ui.script_preview_value.setStyleSheet(self.STYLESHEET_ERROR)
        except Exception as e:
            self.ui.script_preview_value.setText(_("Error: %s") % str(e))
            self.ui.script_preview_value.setStyleSheet(self.STYLESHEET_ERROR)

    def _update_visibility(self):
        use_script = self.ui.local_cover_use_script.isChecked()
        # Toggle visibility based on mode
        for widget in (
            self.ui.local_cover_regex_label,
            self.ui.local_cover_regex_edit,
            self.ui.local_cover_regex_error,
            self.ui.regex_note,
            self.ui.label_test_coverart_filter,
            self.ui.test_coverart_filter,
        ):
            widget.setVisible(not use_script)
        for widget in (
            self.ui.local_cover_script_label,
            self.ui.local_cover_script_edit,
            self.ui.script_preview_label,
            self.ui.script_preview_value,
            self.ui.script_note,
        ):
            widget.setVisible(use_script)
        if use_script:
            self._update_script_preview()

    def load(self):
        config = get_config()
        self.ui.local_cover_regex_edit.setText(config.setting['local_cover_regex'])
        self.ui.local_cover_script_edit.setPlainText(config.setting['local_cover_script'])
        self.ui.local_cover_use_script.setChecked(config.setting['local_cover_use_script'])
        self._update_visibility()

    def save(self):
        config = get_config()
        config.setting['local_cover_regex'] = self.ui.local_cover_regex_edit.text()
        config.setting['local_cover_script'] = self.ui.local_cover_script_edit.toPlainText()
        config.setting['local_cover_use_script'] = self.ui.local_cover_use_script.isChecked()

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
    _known_types = {t['name'] for t in CAA_TYPES}
    _default_types = ['front']

    def queue_images(self):
        config = get_config()

        if config.setting['local_cover_use_script']:
            value = config.setting['local_cover_script']
            queue_method = self._queue_images_script
        else:
            value = config.setting['local_cover_regex']
            queue_method = self._queue_images_regex

        if value:
            queue_method(value)

        return CoverArtProvider.QueueState.FINISHED

    def _queue_images_regex(self, regex):
        match_re = re.compile(regex, re.IGNORECASE)
        dirs_done = set()

        for file in self.album.iterfiles():
            current_dir = os.path.dirname(file.filename)
            if current_dir in dirs_done:
                continue
            dirs_done.add(current_dir)
            for image in self.find_local_images(current_dir, match_re):
                self.queue_put(image)

    def _queue_images_script(self, script):
        dirs_done = set()

        for file in self.album.iterfiles():
            current_dir = os.path.dirname(file.filename)
            if current_dir in dirs_done:
                continue
            dirs_done.add(current_dir)

            expected_filename = script_to_filename(script, file.metadata)
            if expected_filename:
                for image in self.find_local_images_by_script(current_dir, expected_filename):
                    self.queue_put(image)

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

    def find_local_images_by_script(self, current_dir, expected_filename):
        for root, _dirs, files in os.walk(current_dir):
            for filename in files:
                name_without_ext, ext = os.path.splitext(filename)
                if name_without_ext == expected_filename:
                    filepath = os.path.join(current_dir, root, filename)
                    if os.path.exists(filepath):
                        yield LocalFileCoverArtImage(
                            filepath,
                            types=self._default_types,
                            support_types=True,
                            support_multi_types=True,
                        )
