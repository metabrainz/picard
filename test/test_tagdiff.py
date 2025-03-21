# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from picard.ui.metadatabox.tagdiff import (
    TagCounter,
    TagDiff,
    TagStatus,
)


class TestTagCounter(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.parent = TagDiff()
        self.parent.objects = 3
        self.counter = TagCounter(self.parent)

    def test_add_new_tag(self):
        self.counter.add("artist", ["Artist 1"])
        self.assertEqual(self.counter["artist"], ["Artist 1"])
        self.assertEqual(self.counter.counts["artist"], 1)
        self.assertNotIn("artist", self.counter.different)

    def test_add_same_tag_multiple_times(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 1"])
        self.assertEqual(self.counter["artist"], ["Artist 1"])
        self.assertEqual(self.counter.counts["artist"], 2)
        self.assertNotIn("artist", self.counter.different)

    def test_add_different_tag_value(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        self.assertEqual(self.counter["artist"], [""])
        self.assertEqual(self.counter.counts["artist"], 2)
        self.assertIn("artist", self.counter.different)

    def test_get_missing_tag(self):
        self.assertEqual(self.counter["missing"], [""])

    def test_status_different(self):
        self.parent.objects = 2
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        status = self.counter.status("artist")
        self.assertEqual(status.count, 2)
        self.assertTrue(status.is_different)
        self.assertEqual(status.missing, 0)
        self.assertTrue(status.is_grouped)

    def test_status_same(self):
        self.parent.objects = 2
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 1"])
        status = self.counter.status("artist")
        self.assertEqual(status.count, 2)
        self.assertFalse(status.is_different)
        self.assertEqual(status.missing, 0)
        self.assertFalse(status.is_grouped)

    def test_status_missing_and_different(self):
        self.parent.objects = 3
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        status = self.counter.status("artist")
        self.assertEqual(status.count, 2)
        self.assertTrue(status.is_different)
        self.assertEqual(status.missing, 1)
        self.assertTrue(status.is_grouped)

    def test_display_value_different(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 2"])
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "(different across 2 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_same(self):
        self.counter.add("artist", ["Artist 1"])
        self.counter.add("artist", ["Artist 1"])
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "Artist 1 (missing from 1 item)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_missing(self):
        self.counter.add("artist", ["Artist 1"])
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "Artist 1 (missing from 2 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_length(self):
        self.counter.add("~length", 60000)
        display_value = self.counter.display_value("~length")
        self.assertEqual(display_value.text, "1:00 (missing from 2 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_length_missing(self):
        self.counter.add("~length", "60000")
        self.parent.objects = 5
        display_value = self.counter.display_value("~length")
        self.assertEqual(display_value.text, "1:00 (missing from 4 items)")
        self.assertTrue(display_value.is_grouped)

    def test_display_value_nothing(self):
        self.counter.add("artist", ["Artist 1"])
        self.parent.objects = 0
        display_value = self.counter.display_value("artist")
        self.assertEqual(display_value.text, "Artist 1")
        self.assertFalse(display_value.is_grouped)


class TestTagDiff(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.tag_diff = TagDiff()
        self.tag_diff.objects = 3

    def test_add_new_tag(self):
        self.tag_diff.add("artist", new=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.ADDED)
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 1"])
        self.assertIsNone(self.tag_diff.old.get("artist"))

    def test_add_removed_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.REMOVED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertIsNone(self.tag_diff.new.get("artist"))

    def test_add_removed_removed_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"], removed=True)
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.REMOVED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertIsNone(self.tag_diff.new.get("artist"))

    def test_add_changed_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 2"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 2"])

    def test_add_nochange_tag(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 1"])
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.UNCHANGED)
        self.assertEqual(self.tag_diff.old["artist"], ["Artist 1"])
        self.assertEqual(self.tag_diff.new["artist"], ["Artist 1"])

    def test_add_nochange_no_values(self):
        self.tag_diff.add("artist")
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.EMPTY)

    def test_add_nochange_no_values_top(self):
        self.tag_diff.add("artist", top_tags={"artist"})
        self.assertEqual(self.tag_diff.tag_status("artist"), TagStatus.UNCHANGED)

    def test_add_length_changed_2s(self):
        self.tag_diff = TagDiff(max_length_diff=2)
        self.tag_diff.objects = 3
        self.tag_diff.add("~length", old="10000", new="15000")
        self.assertEqual(self.tag_diff.tag_status("~length"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["~length"], "10000")
        self.assertEqual(self.tag_diff.new["~length"], "15000")

    def test_add_length_no_changed_2s(self):
        self.tag_diff = TagDiff(max_length_diff=2)
        self.tag_diff.objects = 3
        self.tag_diff.add("~length", old="10000", new="12000")
        self.assertEqual(self.tag_diff.tag_status("~length"), TagStatus.UNCHANGED)
        self.assertEqual(self.tag_diff.old["~length"], "10000")
        self.assertEqual(self.tag_diff.new["~length"], "12000")

    def test_add_length_no_changed_1s(self):
        self.tag_diff = TagDiff(max_length_diff=1)
        self.tag_diff.objects = 3
        self.tag_diff.add("~length", old="10000", new="12000")
        self.assertEqual(self.tag_diff.tag_status("~length"), TagStatus.CHANGED)
        self.assertEqual(self.tag_diff.old["~length"], "10000")
        self.assertEqual(self.tag_diff.new["~length"], "12000")

    def test_is_readonly(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 2"], readonly=True)
        self.assertTrue(self.tag_diff.is_readonly("artist"))
        self.assertFalse(self.tag_diff.is_readonly("unknown"))

    def test_add_not_removable(self):
        self.tag_diff.add("artist", old=["Artist 1"], new=["Artist 2"], removable=False)
        self.assertEqual(self.tag_diff.status["artist"], TagStatus.CHANGED | TagStatus.NOTREMOVABLE)

    def test_update_tag_names(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names()
        self.assertEqual(self.tag_diff.tag_names, ["album", "artist", "title"])

    def test_update_tag_names_top_tags(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names(top_tags={"title"})
        self.assertEqual(self.tag_diff.tag_names, ["title", "album", "artist"])

    def test_update_tag_names_changes_first(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", old=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names(changes_first=True)
        self.assertEqual(self.tag_diff.tag_names, ["title", "album", "artist"])

    def test_update_tag_names_top_tags_changed(self):
        self.tag_diff.add("title", old=["Title 1"], new=["Title 2"])
        self.tag_diff.add("artist", new=["Artist 2"])
        self.tag_diff.add("album", old=["Album 1"])
        self.tag_diff.update_tag_names(changes_first=True, top_tags={"title"})
        self.assertEqual(self.tag_diff.tag_names, ["title", "artist", "album"])

    @staticmethod
    def _special_handler(old, new):
        for old_value, new_value in zip(old, new):
            try:
                if abs(int(old_value) - int(new_value)) > 2000:
                    return True
            except (ValueError, TypeError):
                return True
        return False

    def test_special_handler_changed(self):
        self.tag_diff = TagDiff()
        self.tag_diff.objects = 2

        self.tag_diff.tag_ne_handlers['~length_list'] = self._special_handler
        self.tag_diff.add("~length_list", old=["10000", "12000"], new=["11000", "14500"])
        self.assertEqual(self.tag_diff.tag_status("~length_list"), TagStatus.CHANGED)

    def test_special_handler_unchanged(self):
        self.tag_diff = TagDiff()
        self.tag_diff.objects = 2

        self.tag_diff.tag_ne_handlers['~length_list'] = self._special_handler
        self.tag_diff.add("~length_list", old=["10000", "12000"], new=["11000", "13500"])
        self.assertEqual(self.tag_diff.tag_status("~length_list"), TagStatus.UNCHANGED)
