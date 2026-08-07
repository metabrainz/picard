#
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata

from picard.ui.metadatabox import apply_tag_values


class FakeObject:
    """Minimal object with a Metadata instance, mimicking File/Track."""

    def __init__(self, **tags):
        self.metadata = Metadata()
        for tag, values in tags.items():
            self.metadata[tag] = values
        self.update_called = False

    def update(self):
        self.update_called = True


class TestApplyTagValues(PicardTestCase):
    def test_set_single_value(self):
        obj = FakeObject(artist=['Old Artist'])
        affected = list(apply_tag_values([obj], 'artist', ['New Artist']))
        self.assertEqual(affected, [obj])
        self.assertEqual(obj.metadata.getall('artist'), ['New Artist'])

    def test_set_multiple_values(self):
        obj = FakeObject(artist=['Old'])
        affected = list(apply_tag_values([obj], 'artist', ['A', 'B']))
        self.assertEqual(affected, [obj])
        self.assertEqual(obj.metadata.getall('artist'), ['A', 'B'])

    def test_set_value_on_multiple_objects(self):
        obj1 = FakeObject(title=['X'])
        obj2 = FakeObject(title=['Y'])
        affected = list(apply_tag_values([obj1, obj2], 'title', ['Z']))
        self.assertEqual(affected, [obj1, obj2])
        self.assertEqual(obj1.metadata.getall('title'), ['Z'])
        self.assertEqual(obj2.metadata.getall('title'), ['Z'])

    def test_delete_tag_with_empty_list(self):
        obj = FakeObject(artist=['Artist'])
        affected = list(apply_tag_values([obj], 'artist', []))
        self.assertEqual(affected, [obj])
        self.assertNotIn('artist', obj.metadata)
        self.assertIn('artist', obj.metadata.deleted_tags)

    def test_delete_tag_with_empty_string_list(self):
        """values=[""] is treated the same as values=[] (deletion)."""
        obj = FakeObject(artist=['Artist'])
        affected = list(apply_tag_values([obj], 'artist', ['']))
        self.assertEqual(affected, [obj])
        self.assertNotIn('artist', obj.metadata)
        self.assertIn('artist', obj.metadata.deleted_tags)

    def test_delete_nonexistent_tag_does_not_raise(self):
        obj = FakeObject()
        affected = list(apply_tag_values([obj], 'nosuch', []))
        self.assertEqual(affected, [obj])
        self.assertIn('nosuch', obj.metadata.deleted_tags)

    def test_does_not_call_update(self):
        """apply_tag_values must not call obj.update() — that's the caller's job."""
        obj = FakeObject(artist=['A'])
        list(apply_tag_values([obj], 'artist', ['B']))
        self.assertFalse(obj.update_called)

    def test_empty_objects_yields_nothing(self):
        affected = list(apply_tag_values([], 'artist', ['X']))
        self.assertEqual(affected, [])

    def test_set_creates_tag_if_not_present(self):
        obj = FakeObject()
        affected = list(apply_tag_values([obj], 'genre', ['Rock']))
        self.assertEqual(affected, [obj])
        self.assertEqual(obj.metadata.getall('genre'), ['Rock'])

    def test_delete_multiple_tags_across_objects(self):
        """Simulate batch removal of multiple tags from multiple objects."""
        obj1 = FakeObject(artist=['A'], title=['T1'])
        obj2 = FakeObject(artist=['B'], title=['T2'])
        objects = [obj1, obj2]

        all_affected = set()
        for tag in ['artist', 'title']:
            all_affected.update(apply_tag_values(objects, tag, []))

        self.assertEqual(all_affected, {obj1, obj2})
        self.assertNotIn('artist', obj1.metadata)
        self.assertNotIn('artist', obj2.metadata)
        self.assertNotIn('title', obj1.metadata)
        self.assertNotIn('title', obj2.metadata)

    def test_yields_each_object_once_per_call(self):
        """Each call yields each object exactly once."""
        obj1 = FakeObject(artist=['A'])
        obj2 = FakeObject(artist=['B'])
        affected = list(apply_tag_values([obj1, obj2], 'artist', ['C']))
        self.assertEqual(len(affected), 2)
        self.assertIn(obj1, affected)
        self.assertIn(obj2, affected)
