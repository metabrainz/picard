# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata
from picard.tagdiff import (
    TagDiff,
    add_files_to_tag_diff,
)


def _make_file(filename, new_filename):
    metadata = Metadata()
    metadata['title'] = 'Title'
    metadata.length = 200000
    file = Mock()
    file.metadata = metadata
    file.orig_metadata = Metadata()
    file.orig_metadata['title'] = 'Title'
    file.orig_metadata.length = 200000
    file.supports_tag = lambda tag: True
    file.format_specific_metadata = lambda md, tag, settings: md.getall(tag)
    file.filename = filename
    file.make_filename = lambda filename, metadata: new_filename
    return file


class TagDiffFilepathSameFileTest(PicardTestCase):
    """Regression tests for PICARD-3573.

    On Windows a file loaded from a mapped drive is reported with its UNC
    path, while the target directory is configured with the drive letter.
    Both paths refer to the same file and must not be shown as a change.
    """

    def setUp(self):
        super().setUp()
        self._settings = {
            'clear_existing_tags': False,
            'rename_files': True,
            'move_files': True,
            'ignore_track_duration_difference_under': 2,
            'metadatabox_top_tags': [],
        }

    def _filepath_diff(self, file, same):
        tag_diff = TagDiff(max_length_diff=2)
        with patch('picard.util.filenaming.samefile', return_value=same):
            add_files_to_tag_diff({file}, tag_diff, self._settings, top_tags=[])
        return tag_diff

    def test_alias_path_is_not_a_change(self):
        file = _make_file('/mnt/share/Music/song.flac', '/mnt/mapped/Music/song.flac')
        tag_diff = self._filepath_diff(file, same=True)
        self.assertEqual(tag_diff.new['~filepath'], ['/mnt/share/Music/song.flac'])
        self.assertEqual(tag_diff.old['~filepath'], tag_diff.new['~filepath'])

    def test_different_file_is_a_change(self):
        file = _make_file('/music/song.flac', '/other/song.flac')
        tag_diff = self._filepath_diff(file, same=False)
        self.assertEqual(tag_diff.new['~filepath'], ['/other/song.flac'])

    def test_case_only_rename_is_a_change(self):
        file = _make_file('/music/song.flac', '/music/Song.flac')
        tag_diff = self._filepath_diff(file, same=True)
        self.assertEqual(tag_diff.new['~filepath'], ['/music/Song.flac'])
