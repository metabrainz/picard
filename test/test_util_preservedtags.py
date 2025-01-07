# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
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

from picard import config
from picard.util.preservedtags import PreservedTags


class PreservedTagsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        config.setting[PreservedTags.opt_name] = ["tag1", "tag2"]

    def test_load_and_contains(self):
        preserved = PreservedTags()
        self.assertIn("tag1", preserved)
        self.assertIn("tag2", preserved)
        self.assertIn("TAG1", preserved)
        self.assertIn(" tag1", preserved)

    def test_add(self):
        preserved = PreservedTags()
        self.assertNotIn("tag3", preserved)
        preserved.add("tag3")
        self.assertIn("tag3", preserved)
        # Add must persists the change
        self.assertIn("tag3", PreservedTags())

    def test_add_case_insensitive(self):
        preserved = PreservedTags()
        self.assertNotIn("tag3", preserved)
        preserved.add("TAG3")
        self.assertIn("tag3", preserved)

    def test_discard(self):
        preserved = PreservedTags()
        self.assertIn("tag1", preserved)
        preserved.discard("tag1")
        self.assertNotIn("tag1", preserved)
        # Discard must persists the change
        self.assertNotIn("tag1", PreservedTags())

    def test_discard_case_insensitive(self):
        preserved = PreservedTags()
        self.assertIn("tag1", preserved)
        preserved.discard("TAG1")
        self.assertNotIn("tag1", preserved)

    def test_order(self):
        preserved = PreservedTags()
        preserved.add('tag3')
        preserved.add('tag2')
        preserved.add('tag1')
        preserved.discard('tag2')
        self.assertEqual(config.setting[PreservedTags.opt_name], ['tag1', 'tag3'])
