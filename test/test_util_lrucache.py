# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Laurent Monin
# Copyright (C) 2020 Philipp Wolfer
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

from picard.util.lrucache import LRUCache


class LRUCacheTest(PicardTestCase):

    def test_simple_getset(self):
        lrucache = LRUCache(3)
        lrucache['test'] = 1
        self.assertEqual(lrucache['test'], 1)
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
        self.assertEqual(len(lrucache._ordered_keys), 3)
        self.assertEqual('test3', lrucache._ordered_keys[0])
        self.assertEqual('test2', lrucache._ordered_keys[1])
        self.assertEqual('test1', lrucache._ordered_keys[2])
        self.assertEqual(2, lrucache['test2'])
        self.assertEqual('test2', lrucache._ordered_keys[0])
        self.assertEqual('test3', lrucache._ordered_keys[1])
        self.assertEqual('test1', lrucache._ordered_keys[2])
        lrucache['test1'] = 4
        self.assertEqual('test1', lrucache._ordered_keys[0])
        self.assertEqual('test2', lrucache._ordered_keys[1])
        self.assertEqual('test3', lrucache._ordered_keys[2])

    def test_dict_like_init(self):
        lrucache = LRUCache(3, [('test1', 1), ('test2', 2)])
        self.assertEqual(lrucache['test1'], 1)
        self.assertEqual(lrucache['test2'], 2)

    def test_get_keyerror(self):
        lrucache = LRUCache(3)
        with self.assertRaises(KeyError):
            value = lrucache['notakey']  # noqa: F841

    def test_del_keyerror(self):
        lrucache = LRUCache(3)
        with self.assertRaises(KeyError):
            del lrucache['notakey']
