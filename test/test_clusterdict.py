# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
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

from picard.cluster import ClusterDict


class ClusterDictTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.clusterdict = ClusterDict()

    def test_tokenize(self):
        token = self.clusterdict._tokenize("")
        self.assertEqual(token, "")

        token = self.clusterdict._tokenize(" \t ")
        self.assertEqual(token, "")

        token = self.clusterdict._tokenize(" A\tWord-test ")
        self.assertEqual(token, "awordtest")

    def test_add(self):
        self.assertEqual(self.clusterdict.get_size(), 0)

        index = self.clusterdict.add("")
        self.assertEqual(self.clusterdict.get_size(), 0)
        self.assertEqual(index, -1)

        # only spaces
        index = self.clusterdict.add("  \t")
        self.assertEqual(self.clusterdict.get_size(), 0)
        self.assertEqual(index, -1)

        index = self.clusterdict.add("a word")
        self.assertEqual(self.clusterdict.get_size(), 1)
        self.assertEqual(index, 0)

        index = self.clusterdict.add("another word")
        self.assertEqual(self.clusterdict.get_size(), 2)
        self.assertEqual(index, 1)

        # same word shouldn't increase size & index
        index = self.clusterdict.add("another word")
        self.assertEqual(self.clusterdict.get_size(), 2)
        self.assertEqual(index, 1)

    def test_get_word(self):
        word = "a word"
        index = self.clusterdict.add(word)
        self.assertEqual(self.clusterdict.get_word(index), word)

    def test_get_token(self):
        index = self.clusterdict.add("a word")
        self.assertEqual(self.clusterdict.get_token(index), "aword")

    def test_get_word_and_count(self):
        word1 = "a word"
        word2 = "Another WORD"
        index1 = self.clusterdict.add(word1)
        index2 = self.clusterdict.add(word2)
        self.assertEqual(self.clusterdict.get_word_and_count(index1), (word1, 1))
        self.assertEqual(self.clusterdict.get_word_and_count(index2), (word2, 1))

        index3 = self.clusterdict.add(word1)
        index4 = self.clusterdict.add(word2)
        self.assertEqual(self.clusterdict.get_word_and_count(index3), (word1, 2))
        self.assertEqual(self.clusterdict.get_word_and_count(index4), (word2, 2))
