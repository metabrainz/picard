# -*- coding: utf-8 -*-
import unittest

from picard import config
from picard.metadata import Metadata, MULTI_VALUED_JOINER


settings = {
    'write_id3v23': False,
    'id3v23_join_with': '/',
}


class MetadataTest(unittest.TestCase):

    original = None
    tags = []

    def setUp(self):
        config.setting = settings.copy()
        self.metadata = Metadata()
        self.metadata["single1"] = "single1-value"
        self.metadata.add_unique("single2", "single2-value")
        self.metadata.add_unique("single2", "single2-value")
        self.multi1 = ["multi1-value", "multi1-value"]
        self.metadata.add("multi1", self.multi1[0])
        self.metadata.add("multi1", self.multi1[1])
        self.multi2 = ["multi2-value1", "multi2-value2"]
        self.metadata["multi2"] = self.multi2
        self.multi3 = ["multi3-value1", "multi3-value2"]
        self.metadata.set("multi3", self.multi3)
        self.metadata["~hidden"] = "hidden-value"

    def tearDown(self):
        pass

    def test_metadata_set(self):
        self.assertEqual(["single1-value"], dict.get(self.metadata,"single1"))
        self.assertEqual(["single2-value"], dict.get(self.metadata,"single2"))
        self.assertEqual(self.multi1, dict.get(self.metadata,"multi1"))
        self.assertEqual(self.multi2, dict.get(self.metadata,"multi2"))
        self.assertEqual(self.multi3, dict.get(self.metadata,"multi3"))
        self.assertEqual(["hidden-value"], dict.get(self.metadata,"~hidden"))

    def test_metadata_get(self):
        self.assertEqual("single1-value", self.metadata["single1"])
        self.assertEqual("single1-value", self.metadata.get("single1"))
        self.assertEqual(["single1-value"], self.metadata.getall("single1"))

        self.assertEqual(MULTI_VALUED_JOINER.join(self.multi1), self.metadata["multi1"])
        self.assertEqual(MULTI_VALUED_JOINER.join(self.multi1), self.metadata.get("multi1"))
        self.assertEqual(self.multi1, self.metadata.getall("multi1"))

        self.assertEqual("", self.metadata["nonexistent"])
        self.assertEqual(None, self.metadata.get("nonexistent"))
        self.assertEqual([], self.metadata.getall("nonexistent"))

        self.assertEqual(dict.items(self.metadata), self.metadata.rawitems())
        metadata_items = [(x, z) for (x, y) in dict.items(self.metadata) for z in y]
        self.assertEqual(metadata_items, list(self.metadata.items()))

    def test_metadata_delete(self):
        self.metadata.delete("single1")
        self.assertNotIn("single1", self.metadata)
        self.assertIn("single1", self.metadata.deleted_tags)

        self.metadata["single2"] = ""
        self.assertNotIn("single2", self.metadata)
        self.assertIn("single2", self.metadata.deleted_tags)

    def test_metadata_update(self):
        m = Metadata()
        m["old"] = "old-value"
        self.metadata.delete("single1")
        m.update(self.metadata)
        self.assertIn("old", m)
        self.assertNotIn("single1", m)
        self.assertIn("single1", m.deleted_tags)
        self.assertEqual("single2-value", m["single2"])
        self.assertEqual(self.metadata.deleted_tags, m.deleted_tags)

        self.metadata["old"] = "old-value"
        for (key, value) in dict.items(self.metadata):
            self.assertIn(key, m)
            self.assertEqual(value, dict.get(m, key))
        for (key, value) in dict.items(m):
            self.assertIn(key, self.metadata)
            self.assertEqual(value, dict.get(self.metadata, key))

    def test_metadata_clear(self):
        self.metadata.clear()
        self.assertEqual(0, len(self.metadata))

    def test_metadata_applyfunc(self):
        func = lambda x: x[1:]
        self.metadata.apply_func(func)

        self.assertEqual("ingle1-value", self.metadata["single1"])
        self.assertEqual("ingle1-value", self.metadata.get("single1"))
        self.assertEqual(["ingle1-value"], self.metadata.getall("single1"))

        self.assertEqual(MULTI_VALUED_JOINER.join(map(func, self.multi1)), self.metadata["multi1"])
        self.assertEqual(MULTI_VALUED_JOINER.join(map(func, self.multi1)), self.metadata.get("multi1"))
        self.assertEqual(list(map(func, self.multi1)), self.metadata.getall("multi1"))

        self.assertEqual("", self.metadata["nonexistent"])
        self.assertEqual(None, self.metadata.get("nonexistent"))
        self.assertEqual([], self.metadata.getall("nonexistent"))

        self.assertEqual(dict.items(self.metadata), self.metadata.rawitems())
        metadata_items = [(x, z) for (x, y) in dict.items(self.metadata) for z in y]
        self.assertEqual(metadata_items, list(self.metadata.items()))

    def test_length_score(self):
        results = [(20000, 0, 0.333333333333),
                   (20000, 10000, 0.666666666667),
                   (20000, 20000, 1.0),
                   (20000, 30000, 0.666666666667),
                   (20000, 40000, 0.333333333333),
                   (20000, 50000, 0.0)]
        for (a, b, expected) in results:
            actual = Metadata.length_score(a, b)
            self.assertAlmostEqual(expected, actual,
                                   msg="a={a}, b={b}".format(a=a, b=b))
