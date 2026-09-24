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


from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata
from picard.script.parser import (
    ScriptUnknownFunction,
    StackItem,
)

from picard.ui.metadatabox import MetadataBox
from picard.ui.metadatabox.tagdiff import TagDiff


class _FakeMetadataBox:
    """Minimal stand-in for calling _add_files_to_tag_diff as an unbound method."""


def _make_file(make_filename):
    """Build a mock File with a single title tag and the given make_filename."""
    new_metadata = Metadata()
    new_metadata['title'] = 'New Title'
    new_metadata.length = 200000
    orig_metadata = Metadata()
    orig_metadata['title'] = 'Old Title'
    orig_metadata.length = 200000

    file = Mock()
    file.metadata = new_metadata
    file.orig_metadata = orig_metadata
    file.supports_tag = lambda tag: True
    file.format_specific_metadata = lambda md, tag, settings: md.getall(tag)
    file.filename = '/music/song.flac'
    file.make_filename = make_filename
    return file


class TestMetadataBoxNamingScriptError(PicardTestCase):
    """Regression tests for PICARD-3466.

    A broken file naming script (e.g. one referencing an unknown function,
    which happens after upgrading from Picard 2 with a plugin-provided function
    such as ``$album_all``) must not blank the whole metadata box. The filename
    preview (``~filepath``) may be unavailable, but the real tag values must
    still be added to the tag diff.
    """

    def setUp(self):
        super().setUp()
        self._settings = {
            'clear_existing_tags': False,
            'rename_files': True,
            'move_files': False,
            'ignore_track_duration_difference_under': 2,
            'metadatabox_top_tags': [],
        }

    def _make_config(self):
        settings = dict(self._settings)

        class _Setting(dict):
            def as_dict(self):
                return dict(self)

        setting = _Setting(settings)
        return Mock(setting=setting)

    def _add_files(self, file):
        config = self._make_config()
        tag_diff = TagDiff(max_length_diff=2)
        MetadataBox._add_files_to_tag_diff(
            _FakeMetadataBox(),
            {file},
            tag_diff,
            config,
            top_tags=[],
        )
        return tag_diff

    def test_script_error_does_not_abort_tag_diff(self):
        def raising_make_filename(filename, metadata):
            raise ScriptUnknownFunction(StackItem(1, 21, 'album_all'))

        file = _make_file(raising_make_filename)
        # Before the fix this raises ScriptUnknownFunction, aborting the whole
        # tag diff (which empties the metadata box).
        tag_diff = self._add_files(file)

        # The real tag(s) must still be present.
        self.assertIn('title', tag_diff.new)
        # The informational length row is always added.
        self.assertIn('~length', tag_diff.new)

    def test_valid_script_still_produces_filepath_preview(self):
        def ok_make_filename(filename, metadata):
            return '/music/New Title.flac'

        file = _make_file(ok_make_filename)
        tag_diff = self._add_files(file)

        self.assertIn('title', tag_diff.new)
        self.assertIn('~filepath', tag_diff.new)
        self.assertEqual(tag_diff.new['~filepath'], ['/music/New Title.flac'])
