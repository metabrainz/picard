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


from test.picardtestcase import PicardTestCase

from picard.const.tags import ALL_TAGS
from picard.tags.tagvar import (
    TagVar,
    TagVars,
)


class TagVarReadOnlyTest(PicardTestCase):
    def test_default_is_not_read_only(self):
        var = TagVar('foo')
        self.assertFalse(var.is_read_only)

    def test_explicit_read_only(self):
        var = TagVar('foo', is_read_only=True)
        self.assertTrue(var.is_read_only)

    def test_preserved_implies_read_only(self):
        # Preserved tags are kept from the original file and never written,
        # so they are considered read-only even without the explicit flag.
        var = TagVar('foo', is_preserved=True)
        self.assertTrue(var.is_read_only)

    def test_not_preserved_not_explicit_is_not_read_only(self):
        var = TagVar('foo', is_preserved=False)
        self.assertFalse(var.is_read_only)


class TagVarReadOnlyNoteTest(PicardTestCase):
    def _notes(self, var):
        tagvars = TagVars(var)
        return list(tagvars.notes(var))

    def test_read_only_note_present_for_explicit(self):
        self.assertIn('read-only', self._notes(TagVar('foo', is_read_only=True)))

    def test_read_only_note_present_for_preserved(self):
        notes = self._notes(TagVar('foo', is_preserved=True))
        self.assertIn('read-only', notes)
        self.assertIn('preserved', notes)

    def test_no_read_only_note_for_plain_tag(self):
        self.assertNotIn('read-only', self._notes(TagVar('foo')))


class MetadataBoxReadOnlyTagsTest(PicardTestCase):
    """The tags shown as read-only in the metadata box must report read-only."""

    def test_length_is_read_only(self):
        var = ALL_TAGS.tagvar_from_name('~length')
        self.assertIsNotNone(var)
        self.assertTrue(var.is_read_only)

    def test_filepath_is_read_only(self):
        var = ALL_TAGS.tagvar_from_name('~filepath')
        self.assertIsNotNone(var)
        self.assertTrue(var.is_read_only)
