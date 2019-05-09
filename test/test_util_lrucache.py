# -*- coding: utf-8 -*-

from test.picardtestcase import PicardTestCase

from picard.util.lrucache import LRUCache


class LRUCacheTest(PicardTestCase):

    def test_simple_getset(self):
        lrucache = LRUCache(3)
        lrucache['test'] = 1
        self.assertEquals(lrucache['test'], 1)
        self.assertIn('test', lrucache._ordered_keys)

    def test_simple_del(self):
        lrucache = LRUCache(3)
        lrucache['test'] = 1
        del lrucache['test']
        self.assertNotIn('test', lrucache)
        self.assertNotIn('test', lrucache._ordered_keys)

    def test_max_size(self):
        lrucache = LRUCache(3)
        lrucache['test1'] = 1
        lrucache['test2'] = 2
        lrucache['test3'] = 3
        lrucache['test4'] = 4
        self.assertNotIn('test1', lrucache)

    def test_lru(self):
        lrucache = LRUCache(3)
        lrucache['test1'] = 1
        lrucache['test2'] = 2
        lrucache['test3'] = 3
        self.assertEquals(len(lrucache._ordered_keys), 3)
        self.assertEquals('test3', lrucache._ordered_keys[0])
        self.assertEquals('test2', lrucache._ordered_keys[1])
        self.assertEquals('test1', lrucache._ordered_keys[2])
        v = lrucache['test2']
        self.assertEquals('test2', lrucache._ordered_keys[0])
        self.assertEquals('test3', lrucache._ordered_keys[1])
        self.assertEquals('test1', lrucache._ordered_keys[2])
        lrucache['test1'] = 4
        self.assertEquals('test1', lrucache._ordered_keys[0])
        self.assertEquals('test2', lrucache._ordered_keys[1])
        self.assertEquals('test3', lrucache._ordered_keys[2])

    def test_dict_like_init(self):
        lrucache = LRUCache(3, [('test1', 1), ('test2', 2)])
        self.assertEquals(lrucache['test1'], 1)
        self.assertEquals(lrucache['test2'], 2)

    def test_get_keyerror(self):
        lrucache = LRUCache(3)
        with self.assertRaises(KeyError):
            value = lrucache['notakey']

    def test_del_keyerror(self):
        lrucache = LRUCache(3)
        with self.assertRaises(KeyError):
            del lrucache['notakey']
