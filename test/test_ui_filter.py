# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025 Francisco Lisboa
# Copyright (C) 2025 Bob Swift
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

from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.tags.tagvar import (
    TagVar,
    TagVars,
)

from picard.ui.filter import Filter


TEST_TAGS = TagVars(
    TagVar(
        'album',
        shortdesc='Album',
        is_filterable=True,
    ),
    TagVar(
        'artist',
        shortdesc='Artist',
        is_filterable=True,
    ),
    TagVar(
        'bitrate',
        shortdesc='Bitrate',
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filename',
        shortdesc='File Name',
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filepath',
        shortdesc='File Path',
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'title',
        shortdesc='Title',
        is_filterable=True,
    ),
)


class FilterxTest(PicardTestCase):
    """Test the Filter widget functionality"""

    @patch('picard.ui.filter.ALL_TAGS', TEST_TAGS)
    def test_filter_button_text_logic(self):
        """Test the logic for updating filter button text from Filter._show_filter_dialog"""
        test_cases = [
            ([], None),
            (["~filename"], "File Name"),
            (["artist"], "Artist"),
            (["invalid_tag"], "invalid_tag"),
            (["~filename", "artist"], "2 filters"),
            (["~filename", "artist", "album", "title"], "4 filters"),
        ]

        for selected_filters, expected_text in test_cases:
            button_text = Filter.make_button_text(selected_filters)
            self.assertEqual(button_text, expected_text,
                           f"Filter list {selected_filters} should produce '{expected_text}'")

    @patch('picard.tags.ALL_TAGS', TEST_TAGS)
    def test_filterable_tags(self):
        """Test generation of valid tags"""
        Filter.load_filterable_tags(force=True)
        filterable_tags = set(str(x) for x in Filter.filterable_tags)
        self.assertEqual(len(filterable_tags), 3)

        tag_names = ['album', 'artist', 'title']
        for name in tag_names:
            self.assertTrue(name in filterable_tags)

        tag_names = ['bitrate', 'filename', 'filepath', 'invalid_tag']
        for name in tag_names:
            self.assertFalse(name in filterable_tags)
