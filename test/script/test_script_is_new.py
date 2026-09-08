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


"""Tests for the $get_new and $get_original script functions."""

from test.picardtestcase import PicardTestCase

from picard.metadata import (
    Metadata,
    MultiMetadataProxy,
)
from picard.script.parser import ScriptParser


class TestGetNewFunction(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({'enabled_plugins': ''})
        self.parser = ScriptParser()
        ScriptParser._cache = {}

    def test_get_new_with_proxy_tag_in_track_metadata(self):
        """$get_new returns value when tag exists in track/MB metadata."""
        track_metadata = Metadata()
        track_metadata['composer'] = 'MB Composer'

        file_metadata = Metadata()

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_new(composer)", proxy)
        self.assertEqual(result, "MB Composer")

    def test_get_new_with_proxy_tag_only_in_file(self):
        """$get_new returns empty when tag only exists in file metadata."""
        track_metadata = Metadata()

        file_metadata = Metadata()
        file_metadata['composer'] = 'Old File Composer'

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_new(composer)", proxy)
        self.assertEqual(result, "")

    def test_get_new_with_proxy_tag_in_both(self):
        """$get_new returns track value when tag exists in both."""
        track_metadata = Metadata()
        track_metadata['composer'] = 'MB Composer'

        file_metadata = Metadata()
        file_metadata['composer'] = 'Old File Composer'

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_new(composer)", proxy)
        self.assertEqual(result, "MB Composer")

    def test_get_new_with_proxy_tag_nowhere(self):
        """$get_new returns empty when tag doesn't exist anywhere."""
        track_metadata = Metadata()
        file_metadata = Metadata()

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_new(composer)", proxy)
        self.assertEqual(result, "")

    def test_get_new_with_plain_metadata(self):
        """$get_new on plain Metadata returns value (same as %name%)."""
        metadata = Metadata()
        metadata['composer'] = 'Some Composer'

        result = self.parser.eval("$get_new(composer)", metadata)
        self.assertEqual(result, "Some Composer")

    def test_get_new_used_in_if_condition(self):
        """$get_new works in $if for the user's use case."""
        track_metadata = Metadata()
        track_metadata['lyricist'] = 'Some Lyricist'

        file_metadata = Metadata()
        file_metadata['composer'] = 'Old File Composer'

        metadata = Metadata(track_metadata)
        proxy = MultiMetadataProxy(metadata, file_metadata)

        script = '$if($get_new(composer),,$set(composer,$if2(%lyricist%,%writer%,%arranger%)))'
        self.parser.eval(script, proxy)

        # Script fires because $get_new(composer) is empty
        self.assertEqual(metadata['composer'], 'Some Lyricist')


class TestGetOriginalFunction(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({'enabled_plugins': ''})
        self.parser = ScriptParser()
        ScriptParser._cache = {}

    def test_get_original_with_proxy_tag_in_file(self):
        """$get_original returns file's value."""
        track_metadata = Metadata()
        track_metadata['composer'] = 'MB Composer'

        file_metadata = Metadata()
        file_metadata['composer'] = 'Old File Composer'

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_original(composer)", proxy)
        self.assertEqual(result, "Old File Composer")

    def test_get_original_with_proxy_tag_only_in_track(self):
        """$get_original returns empty when tag only exists in track metadata."""
        track_metadata = Metadata()
        track_metadata['composer'] = 'MB Composer'

        file_metadata = Metadata()

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_original(composer)", proxy)
        self.assertEqual(result, "")

    def test_get_original_with_proxy_tag_nowhere(self):
        """$get_original returns empty when tag doesn't exist anywhere."""
        track_metadata = Metadata()
        file_metadata = Metadata()

        proxy = MultiMetadataProxy(Metadata(track_metadata), file_metadata)
        result = self.parser.eval("$get_original(composer)", proxy)
        self.assertEqual(result, "")

    def test_get_original_with_plain_metadata(self):
        """$get_original on plain Metadata returns value (same as %name%)."""
        metadata = Metadata()
        metadata['composer'] = 'Some Composer'

        result = self.parser.eval("$get_original(composer)", metadata)
        self.assertEqual(result, "Some Composer")

    def test_get_original_use_in_script(self):
        """$get_original can be used to reference file's original value."""
        track_metadata = Metadata()
        track_metadata['artist'] = 'MB Artist'

        file_metadata = Metadata()
        file_metadata['artist'] = 'File Artist'

        metadata = Metadata(track_metadata)
        proxy = MultiMetadataProxy(metadata, file_metadata)

        script = '$set(comment,Original: $get_original(artist))'
        self.parser.eval(script, proxy)

        self.assertEqual(metadata['comment'], 'Original: File Artist')
