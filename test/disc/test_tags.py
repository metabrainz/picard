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

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.disc import (
    ConflictingDiscTags,
    DiscTagsError,
    NoDiscTags,
    toc_string_from_tags,
)
from picard.metadata import Metadata


TAG = '5023F08C+100000+4+150+30000+50000+90000'


def _files(*tags):
    files = []
    for tag in tags:
        metadata = Metadata()
        if tag:
            metadata['itunes_cddb_1'] = tag
        files.append(MagicMock(metadata=metadata))
    return files


class TocStringFromTagsTest(PicardTestCase):
    def test_toc_string_of_the_disc(self):
        self.assertEqual(toc_string_from_tags(_files(*[TAG] * 4)), '1+4+100000+150+30000+50000+90000')

    def test_a_single_track_disc(self):
        self.assertEqual(toc_string_from_tags(_files('F001F000+4096+1+0')), '1+1+4096+0')

    def test_files_without_the_tag_still_count_as_tracks(self):
        self.assertEqual(toc_string_from_tags(_files(TAG, None, TAG, None)), '1+4+100000+150+30000+50000+90000')

    def test_no_file_has_the_tag(self):
        with self.assertRaises(NoDiscTags):
            toc_string_from_tags(_files(None, None))

    def test_no_files(self):
        with self.assertRaises(NoDiscTags):
            toc_string_from_tags([])

    def test_files_disagree(self):
        other = '5023F08C+100000+4+150+30000+50000+90001'
        with self.assertRaises(ConflictingDiscTags):
            toc_string_from_tags(_files(TAG, other, TAG, TAG))

    def test_tag_that_cannot_be_parsed(self):
        with self.assertRaises(DiscTagsError) as cm:
            toc_string_from_tags(_files('garbage'))
        self.assertIn('Failed to parse disc information from tags', str(cm.exception))
        self.assertNotIsInstance(cm.exception, (NoDiscTags, ConflictingDiscTags))

    def test_track_count_not_matching_the_files(self):
        with self.assertRaises(DiscTagsError) as cm:
            toc_string_from_tags(_files(TAG, TAG))
        self.assertIn('Number of tracks (4) does not match number of selected files (2)', str(cm.exception))
        self.assertNotIsInstance(cm.exception, (NoDiscTags, ConflictingDiscTags))

    def test_errors_share_a_base_class(self):
        self.assertTrue(issubclass(NoDiscTags, DiscTagsError))
        self.assertTrue(issubclass(ConflictingDiscTags, DiscTagsError))
