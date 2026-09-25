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


from functools import partial

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata

from picard.ui.metadatabox import MetadataBox
from picard.ui.metadatabox.tagdiff import (
    TagDiff,
    TagStatus,
)


class FakeTaggedObject:
    """Minimal File/Track stand-in with metadata, orig_metadata and a counting update()."""

    def __init__(self, **tags):
        self.metadata = Metadata()
        self.orig_metadata = Metadata()
        for tag, values in tags.items():
            # orig_metadata holds the "original" (pre-edit) values; metadata is
            # the current (edited) state. Start them equal, callers mutate
            # metadata afterwards to simulate edits.
            self.orig_metadata[tag] = values
            self.metadata[tag] = values
        self.update_count = 0

    def update(self):
        self.update_count += 1


class FakeMetadataBox:
    """Minimal stand-in for MetadataBox avoiding QTableWidget instantiation.

    Binds the real MetadataBox methods that make up the "Use/Merge Original
    Values" code path so the update-coalescing behaviour can be tested without
    a live Qt widget. Methods are bound by name so the fake keeps working
    across internal helper renames/refactors of that path.
    """

    # Every internal helper the orig-values path might route through. Bound
    # dynamically below; names that do not exist on MetadataBox are skipped so
    # the test does not depend on a specific set of private helpers.
    _BOUND_METHODS = (
        '_apply_update_funcs',
        '_use_orig_tags',
        '_merge_orig_tags',
        '_set_tag_values',
        '_set_tag_values_extra_delayed_updates',
        '_set_tag_values_delayed_updates',
        '_update_objects',
        '_tag_is_removable',
    )

    def __init__(self, tagger):
        self.tagger = tagger
        self.tag_diff = TagDiff()
        self.objects = set()
        self.tracks = set()
        self.files = set()


for _name in FakeMetadataBox._BOUND_METHODS:
    _method = getattr(MetadataBox, _name, None)
    if _method is not None:
        setattr(FakeMetadataBox, _name, _method)


class UseOriginalValuesUpdateCoalescingTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.box = FakeMetadataBox(self.tagger)

    def _mark_changed(self, *tags):
        """Mark the given tags as CHANGED in the tag_diff so removability checks pass."""
        for tag in tags:
            self.box.tag_diff.status[tag] = TagStatus.CHANGED

    def _build_useorig_funcs(self, objects, tags):
        """Build the per-(object, tag) funcs exactly like _collect_orig_tag_actions does."""
        funcs = []
        for tag in tags:
            for obj in objects:
                funcs.append(partial(self.box._use_orig_tags, obj, tag))
        return funcs

    def test_use_orig_updates_each_object_once_not_per_tag(self):
        """Regression (PICARD-2530): restoring N objects x G tags must call
        obj.update() once per object, not once per (object, tag) pair.

        The old behaviour updated eagerly inside every func, so an object with
        G changed tags was refreshed G times, giving O(N*G) File.update() calls
        (and the multi-minute UI freeze reported in the ticket).
        """
        tags = ['artist', 'album', 'title', 'genre', 'date']
        objects = [FakeTaggedObject(**{t: ['edited'] for t in tags}) for _ in range(10)]
        # Simulate edits: current metadata differs from orig_metadata.
        for obj in objects:
            for t in tags:
                obj.metadata[t] = ['edited value']
                obj.orig_metadata[t] = ['original value']
        self.box.objects = set(objects)
        self._mark_changed(*tags)

        funcs = self._build_useorig_funcs(objects, tags)
        self.box._apply_update_funcs(funcs)

        # Each object must be updated exactly once, regardless of tag count.
        for obj in objects:
            self.assertEqual(
                obj.update_count,
                1,
                f"expected 1 update per object, got {obj.update_count} (O(N*G) regression)",
            )

    def test_use_orig_restores_original_values(self):
        """The coalescing must not change the functional outcome: original
        values are restored on every object and tag."""
        tags = ['artist', 'title']
        objects = [FakeTaggedObject(**{t: ['edited'] for t in tags}) for _ in range(3)]
        for obj in objects:
            for t in tags:
                obj.metadata[t] = ['edited value']
                obj.orig_metadata[t] = [f'orig {t}']
        self.box.objects = set(objects)
        self._mark_changed(*tags)

        funcs = self._build_useorig_funcs(objects, tags)
        self.box._apply_update_funcs(funcs)

        for obj in objects:
            for t in tags:
                self.assertEqual(obj.metadata.getall(t), [f'orig {t}'])

    def test_merge_orig_updates_each_object_once(self):
        """Same coalescing guarantee for 'Merge Original Values'."""
        tags = ['artist', 'genre', 'comment']
        objects = [FakeTaggedObject(**{t: ['edited'] for t in tags}) for _ in range(5)]
        for obj in objects:
            for t in tags:
                obj.metadata[t] = ['current']
                obj.orig_metadata[t] = ['original']
        self.box.objects = set(objects)
        self._mark_changed(*tags)

        funcs = []
        for tag in tags:
            for obj in objects:
                funcs.append(partial(self.box._merge_orig_tags, obj, tag))
        self.box._apply_update_funcs(funcs)

        for obj in objects:
            self.assertEqual(obj.update_count, 1)
