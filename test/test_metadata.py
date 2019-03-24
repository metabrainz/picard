# -*- coding: utf-8 -*-
from test.picardtestcase import PicardTestCase
from test.test_coverart_image import create_image

from picard import config
from picard.metadata import (
    MULTI_VALUED_JOINER,
    Metadata,
)
from picard.util.tags import PRESERVED_TAGS


settings = {
    'write_id3v23': False,
    'id3v23_join_with': '/',
}


class MetadataTest(PicardTestCase):

    original = None
    tags = []

    def setUp(self):
        super().setUp()
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

        self.metadata_d1 = Metadata({'a': 'b', 'c': 2, 'd': ['x', 'y'], 'x': ''})
        self.metadata_d2 = Metadata({'a': 'b', 'c': 2, 'd': ['x', 'y'], 'x': 'z'})
        self.metadata_d3 = Metadata({'c': 3, 'd': ['u', 'w'], 'x': 'p'})

    def tearDown(self):
        pass

    def test_metadata_setitem(self):
        self.assertEqual(["single1-value"], self.metadata.getraw("single1"))
        self.assertEqual(["single2-value"], self.metadata.getraw("single2"))
        self.assertEqual(self.multi1, self.metadata.getraw("multi1"))
        self.assertEqual(self.multi2, self.metadata.getraw("multi2"))
        self.assertEqual(self.multi3, self.metadata.getraw("multi3"))
        self.assertEqual(["hidden-value"], self.metadata.getraw("~hidden"))

    def test_metadata_get(self):
        self.assertEqual("single1-value", self.metadata["single1"])
        self.assertEqual("single1-value", self.metadata.get("single1"))
        self.assertEqual(["single1-value"], self.metadata.getall("single1"))
        self.assertEqual(["single1-value"], self.metadata.getraw("single1"))

        self.assertEqual(MULTI_VALUED_JOINER.join(self.multi1), self.metadata["multi1"])
        self.assertEqual(MULTI_VALUED_JOINER.join(self.multi1), self.metadata.get("multi1"))
        self.assertEqual(self.multi1, self.metadata.getall("multi1"))
        self.assertEqual(self.multi1, self.metadata.getraw("multi1"))

        self.assertEqual("", self.metadata["nonexistent"])
        self.assertEqual(None, self.metadata.get("nonexistent"))
        self.assertEqual([], self.metadata.getall("nonexistent"))
        self.assertRaises(KeyError, self.metadata.getraw, "nonexistent")

        self.assertEqual(self.metadata._store.items(), self.metadata.rawitems())
        metadata_items = [(x, z) for (x, y) in self.metadata.rawitems() for z in y]
        self.assertEqual(metadata_items, list(self.metadata.items()))

    def test_metadata_delete(self):
        self.metadata.delete("single1")
        self.assertNotIn("single1", self.metadata)
        self.assertIn("single1", self.metadata.deleted_tags)

    def test_metadata_implicit_delete(self):
        self.metadata["single2"] = ""
        self.assertNotIn("single2", self.metadata)
        self.assertIn("single2", self.metadata.deleted_tags)

        self.metadata["unknown"] = ""
        self.assertNotIn("unknown", self.metadata)
        self.assertNotIn("unknown", self.metadata.deleted_tags)

    def test_metadata_set_explicit_empty(self):
        self.metadata.delete("single1")
        self.metadata.set("single1", [])
        self.assertIn("single1", self.metadata)
        self.assertNotIn("single1", self.metadata.deleted_tags)
        self.assertEqual([], self.metadata.getall("single1"))

    def test_metadata_undelete(self):
        self.metadata.delete("single1")
        self.assertNotIn("single1", self.metadata)
        self.assertIn("single1", self.metadata.deleted_tags)

        self.metadata["single1"] = "value1"
        self.assertIn("single1", self.metadata)
        self.assertNotIn("single1", self.metadata.deleted_tags)

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
        for (key, value) in self.metadata.rawitems():
            self.assertIn(key, m)
            self.assertEqual(value, m.getraw(key))
        for (key, value) in m.rawitems():
            self.assertIn(key, self.metadata)
            self.assertEqual(value, self.metadata.getraw(key))

    def test_metadata_clear(self):
        self.metadata.clear()
        self.assertEqual(0, len(self.metadata))

    def test_metadata_clear_deleted(self):
        self.metadata.delete("single1")
        self.assertIn("single1", self.metadata.deleted_tags)
        self.metadata.clear_deleted()
        self.assertNotIn("single1", self.metadata.deleted_tags)

    def test_metadata_applyfunc(self):
        def func(x): return x[1:]
        self.metadata.apply_func(func)

        self.assertEqual("ingle1-value", self.metadata["single1"])
        self.assertEqual("ingle1-value", self.metadata.get("single1"))
        self.assertEqual(["ingle1-value"], self.metadata.getall("single1"))

        self.assertEqual(MULTI_VALUED_JOINER.join(map(func, self.multi1)), self.metadata["multi1"])
        self.assertEqual(MULTI_VALUED_JOINER.join(map(func, self.multi1)), self.metadata.get("multi1"))
        self.assertEqual(list(map(func, self.multi1)), self.metadata.getall("multi1"))

    def test_metadata_applyfunc_preserve_tags(self):
        self.assertTrue(len(PRESERVED_TAGS) > 0)
        m = Metadata()
        m[PRESERVED_TAGS[0]] = 'value1'
        m['not_preserved'] = 'value2'

        def func(x): return x[1:]
        m.apply_func(func)

        self.assertEqual("value1", m[PRESERVED_TAGS[0]])
        self.assertEqual("alue2", m['not_preserved'])

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

    def test_compare_is_equal(self):
        m1 = Metadata()
        m1["title"] = "title1"
        m1["tracknumber"] = "2"
        m1.length = 360
        m2 = Metadata()
        m2["title"] = "title1"
        m2["tracknumber"] = "2"
        m2.length = 360
        self.assertEqual(m1.compare(m2), m2.compare(m1))
        self.assertEqual(m1.compare(m2), 1)

    def test_compare_lengths(self):
        m1 = Metadata()
        m1.length = 360
        m2 = Metadata()
        m2.length = 300
        self.assertAlmostEqual(m1.compare(m2), 0.998)

    def test_compare_tracknumber_difference(self):
        m1 = Metadata()
        m1["tracknumber"] = "1"
        m2 = Metadata()
        m2["tracknumber"] = "2"
        self.assertEqual(m1.compare(m2), 0)

    def test_compare_deleted(self):
        m1 = Metadata()
        m1["artist"] = "TheArtist"
        m1["title"] = "title1"
        m2 = Metadata()
        m2["artist"] = "TheArtist"
        m2.delete("title")
        self.assertTrue(m1.compare(m2) < 1)

    def test_strip_whitespace(self):
        m1 = Metadata()
        m1["artist"] = "  TheArtist  "
        m1["title"] = "\t\u00A0  tit le1 \r\n"
        m1.strip_whitespace()
        self.assertEqual(m1["artist"], "TheArtist")
        self.assertEqual(m1["title"], "tit le1")

    def test_metadata_mapping_init(self):
        d = {'a': 'b', 'c': 2, 'd': ['x', 'y'], 'x': '', 'z': {'u', 'w'}}
        deleted_tags = set('c')
        m = Metadata(d, deleted_tags=deleted_tags, length=1234)
        self.assertTrue('a' in m)
        self.assertEqual(m.getraw('a'), ['b'])
        self.assertEqual(m['d'], MULTI_VALUED_JOINER.join(d['d']))
        self.assertNotIn('c', m)
        self.assertNotIn('length', m)
        self.assertIn('c', m.deleted_tags)
        self.assertEqual(m.length, 1234)

    def test_metadata_mapping_init_zero(self):
        m = Metadata(tag1='a', tag2=0, tag3='', tag4=None)
        m['tag5'] = 0
        m['tag1'] = ''
        self.assertIn('tag1', m.deleted_tags)
        self.assertEqual(m['tag2'], '0')
        self.assertNotIn('tag3', m)
        self.assertNotIn('tag4', m)
        self.assertEqual(m['tag5'], '0')

    def test_metadata_mapping_del(self):
        m = self.metadata_d1
        self.assertEqual(m.getraw('a'), ['b'])
        self.assertNotIn('a', m.deleted_tags)

        self.assertNotIn('x', m.deleted_tags)
        self.assertRaises(KeyError, m.getraw, 'x')

        del m['a']
        self.assertRaises(KeyError, m.getraw, 'a')
        self.assertIn('a', m.deleted_tags)

        # NOTE: historic behavior of Metadata.delete()
        # an attempt to delete an non-existing tag, will add it to the list
        # of deleted tags
        # so this will not raise a KeyError
        # as is it differs from dict or even defaultdict behavior
        del m['unknown']
        self.assertIn('unknown', m.deleted_tags)

    def test_metadata_mapping_iter(self):
        l = set(self.metadata_d1)
        self.assertEqual(l, {'a', 'c', 'd'})

    def test_metadata_mapping_keys(self):
        l = set(self.metadata_d1.keys())
        self.assertEqual(l, {'a', 'c', 'd'})

    def test_metadata_mapping_values(self):
        l = set(self.metadata_d1.values())
        self.assertEqual(l, {'b', '2', 'x; y'})

    def test_metadata_mapping_len(self):
        m = self.metadata_d1
        self.assertEqual(len(m), 3)
        del m['x']
        self.assertEqual(len(m), 3)
        del m['c']
        self.assertEqual(len(m), 2)

    def _check_mapping_update(self, m):
        self.assertEqual(m['a'], 'b')
        self.assertEqual(m['c'], '3')
        self.assertEqual(m.getraw('d'), ['u', 'w'])
        self.assertEqual(m['x'], '')
        self.assertIn('x', m.deleted_tags)

    def test_metadata_mapping_update(self):
        # update from Metadata
        m = self.metadata_d2
        m2 = self.metadata_d3

        del m2['x']
        m.update(m2)
        self._check_mapping_update(m)

    def test_metadata_mapping_update_dict(self):
        # update from dict
        m = self.metadata_d2

        d2 = {'c': 3, 'd': ['u', 'w'], 'x': ''}

        m.update(d2)
        self._check_mapping_update(m)

    def test_metadata_mapping_update_tuple(self):
        # update from tuple
        m = self.metadata_d2

        d2 = (('c', 3), ('d', ['u', 'w']), ('x', ''))

        m.update(d2)
        self._check_mapping_update(m)

    def test_metadata_mapping_update_dictlike(self):
        # update from kwargs
        m = self.metadata_d2

        m.update(c=3, d=['u', 'w'], x='')
        self._check_mapping_update(m)

    def test_metadata_mapping_update_noparam(self):
        # update without parameter
        m = self.metadata_d2

        self.assertRaises(TypeError, m.update)
        self.assertEqual(m['a'], 'b')

    def test_metadata_mapping_update_intparam(self):
        # update without parameter
        m = self.metadata_d2

        self.assertRaises(TypeError, m.update, 123)

    def test_metadata_mapping_update_strparam(self):
        # update without parameter
        m = self.metadata_d2

        self.assertRaises(ValueError, m.update, 'abc')

    def test_metadata_mapping_update_kw(self):
        m = Metadata(tag1='a', tag2='b')
        m.update(tag1='c')
        self.assertEqual(m['tag1'], 'c')
        self.assertEqual(m['tag2'], 'b')
        m.update(tag2='')
        self.assertIn('tag2', m.deleted_tags)

    def test_metadata_mapping_update_kw_del(self):
        m = Metadata(tag1='a', tag2='b')
        del m['tag1']

        m2 = Metadata(tag1='c', tag2='d')
        del m2['tag2']

        m.update(m2)
        self.assertEqual(m['tag1'], 'c')
        self.assertNotIn('tag2', m)
        self.assertNotIn('tag1', m.deleted_tags)
        self.assertIn('tag2', m.deleted_tags)

    def test_metadata_mapping_images(self):
        image1 = create_image(b'A', comment='A')
        image2 = create_image(b'B', comment='B')

        m1 = Metadata(a='b', length=1234, images=[image1])
        self.assertEqual(m1.images[0], image1)
        self.assertEqual(len(m1), 2) # one tag, one image

        m1.images.append(image2)
        self.assertEqual(m1.images[1], image2)

        m1.images.pop(0)
        self.assertEqual(m1.images[0], image2)

        m2 = Metadata(a='c', length=4567, images=[image1])
        m1.update(m2)
        self.assertEqual(m1.images[0], image1)

        m1.images.pop(0)
        self.assertEqual(len(m1), 1) # one tag, zero image
        self.assertFalse(m1.images)

    def test_metadata_mapping_iterable(self):
        m = Metadata(tag_tuple=('a', 0))
        m['tag_set'] = {'c', 'd'}
        m['tag_dict'] = {'e': 1, 'f': 2}
        m['tag_str'] = 'gh'
        self.assertIn('0', m.getraw('tag_tuple'))
        self.assertIn('c', m.getraw('tag_set'))
        self.assertIn('e', m.getraw('tag_dict'))
        self.assertIn('gh', m.getraw('tag_str'))
