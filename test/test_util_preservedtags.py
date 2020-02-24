# -*- coding: utf-8 -*-
from test.picardtestcase import PicardTestCase

from picard import config
from picard.util.preservedtags import PreservedTags


class PreservedTagsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        config.setting[PreservedTags.opt_name] = "tag1, tag2"

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
        self.assertEqual(config.setting[PreservedTags.opt_name], 'tag1, tag3')

