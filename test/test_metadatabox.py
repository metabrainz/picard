# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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


from test.picardtestcase import PicardTestCase

from picard.browser.filelookup import FileLookup

from picard.ui.metadatabox import MetadataBox
from picard.ui.metadatabox.tagdiff import TagDiff


class MetadataBoxFileLookupTest(PicardTestCase):
    def test_filelook_methods(self):
        """Test if methods listed in MetadataBox.LOOKUP_TAGS are valid FileLookup methods"""
        for method_as_string in MetadataBox.LOOKUP_TAGS.values():
            method = getattr(FileLookup, method_as_string, None)
            self.assertIsNotNone(method, f"No such FileLookup.{method_as_string}")
            self.assertTrue(callable(method), f"FileLookup.{method_as_string} is not callable")


class MetadataBoxTagConversion(PicardTestCase):

    def test_unchanged_tag_to_json(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", ["Artist 1"])
        tags = MetadataBox.tags_to_json(data)
        self.assertEqual(tags, '{"artist": {"old": ["Artist 1"]}}')

    def test_new_tag_to_json(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", new=["Artist 1"])
        tags = MetadataBox.tags_to_json(data)
        self.assertEqual(tags, '{"artist": {"new": ["Artist 1"]}}')

    def test_modified_tag_to_json(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", ["Artist 1"], ["Artist 2"])
        tags = MetadataBox.tags_to_json(data)
        self.assertEqual(tags, '{"artist": {"old": ["Artist 1"], "new": ["Artist 2"]}}')

    def test_multiple_tags_to_json(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", ["Artist 1"], ["Artist 2"])
        data.tag_names.append("album")  # may not be necessary if TagDiff is internally consistent
        data.add("album", ["Album 1"], ["Album 2"])
        tags = MetadataBox.tags_to_json(data)
        self.assertEqual(tags, '{"artist": {"old": ["Artist 1"], "new": ["Artist 2"]}, "album": {"old": ["Album 1"], "new": ["Album 2"]}}')

    def test_unchanged_tag_to_tsv(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", ["Artist 1"])
        tags = MetadataBox.tags_to_tsv(data)
        self.assertEqual(tags, 'artist\tArtist 1')

    def test_new_tag_to_tsv(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", new=["Artist 1"])
        tags = MetadataBox.tags_to_tsv(data)
        self.assertEqual(tags, 'artist\t\tArtist 1')

    def test_modified_tag_to_tsv(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", ["Artist 1"], ["Artist 2"])
        tags = MetadataBox.tags_to_tsv(data)
        self.assertEqual(tags, 'artist\tArtist 1\tArtist 2')

    def test_multiple_tags_to_tsv(self):
        data = TagDiff()
        data.tag_names.append("artist")  # may not be necessary if TagDiff is internally consistent
        data.add("artist", ["Artist 1"], ["Artist 2"])
        data.tag_names.append("album")  # may not be necessary if TagDiff is internally consistent
        data.add("album", ["Album 1"], ["Album 2"])
        tags = MetadataBox.tags_to_tsv(data)
        self.assertEqual(tags, 'artist\tArtist 1\tArtist 2\nalbum\tAlbum 1\tAlbum 2')
