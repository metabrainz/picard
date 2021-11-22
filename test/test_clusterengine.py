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

from picard.cluster import (
    ClusterDict,
    ClusterEngine,
    ClusterType,
)


class ClusterEngineTest(PicardTestCase):

    def setUp(self):
        super().setUp()

    def test_init(self):
        clusterdict = ClusterDict()
        clusterengine = ClusterEngine(clusterdict, ClusterType.ARTIST)
        self.assertEqual(clusterengine.cluster_count, 0)
        self.assertEqual(clusterengine.cluster_type, ClusterType.ARTIST)

    def test_get_cluster_title_negative_index(self):
        clusterdict = ClusterDict()
        clusterengine = ClusterEngine(clusterdict, ClusterType.ARTIST)
        title = clusterengine.get_cluster_title(-1)
        self.assertEqual(title, "")

    def test_one_cluster(self):
        clusterdict = ClusterDict()
        clusterdict.add("word 1")
        clusterdict.add("WORD  1")
        clusterdict.add("Word 1")
        clusterengine = ClusterEngine(clusterdict, ClusterType.ARTIST)
        clusterengine.cluster(1.0)
        self.assertEqual(clusterengine.cluster_count, 1)

        title = clusterengine.get_cluster_title(0)
        self.assertEqual(title, "Word 1")

    def test_two_clusters(self):
        clusterdict = ClusterDict()
        clusterdict.add("ABC")
        clusterdict.add("DEF")
        clusterdict.add("abc ")
        clusterdict.add("def")
        clusterdict.add("abc")
        clusterengine = ClusterEngine(clusterdict, ClusterType.ARTIST)
        clusterengine.cluster(1.0)
        self.assertEqual(clusterengine.cluster_count, 2)

        titles = {}
        for i in clusterengine.cluster_bins:
            titles[i] = clusterengine.get_cluster_title(i)
        self.assertEqual(titles, {0: 'abc', 1: 'def'})

        self.assertEqual(clusterengine.cluster_bins, {0: [0, 2, 4], 1: [1, 3]})
        self.assertEqual(clusterengine.index_id_cluster, {2: 0, 3: 1, 0: 0, 4: 0, 1: 1})

    def test_two_clusters_with_dupes(self):
        clusterdict = ClusterDict()
        clusterdict.add("abc")
        clusterdict.add("def")
        clusterdict.add("abc")
        clusterdict.add("def")
        clusterdict.add("abc")
        clusterengine = ClusterEngine(clusterdict, ClusterType.ARTIST)
        clusterengine.cluster(1.0)
        self.assertEqual(clusterengine.cluster_count, 2)

        titles = {}
        for i in clusterengine.cluster_bins:
            titles[i] = clusterengine.get_cluster_title(i)
        self.assertEqual(titles, {0: 'abc', 1: 'def'})

        self.assertEqual(clusterengine.cluster_bins, {0: [0], 1: [1]})
        self.assertEqual(clusterengine.index_id_cluster, {0: 0, 1: 1})

    def test_two_clusters_with_almost_dupes(self):
        clusterdict = ClusterDict()
        clusterdict.add("def ")
        clusterdict.add("def")
        clusterdict.add("abc")
        clusterdict.add(" abc")

        clusterdict.add("ABC")
        clusterdict.add("DEF")

        clusterdict.add("abc ")
        clusterdict.add("def ")
        clusterdict.add(" ABC")
        clusterdict.add("def")
        clusterdict.add("abc")
        clusterdict.add("x")
        clusterdict.add("x")
        clusterdict.add("x")

        clusterengine = ClusterEngine(clusterdict, ClusterType.ARTIST)
        clusterengine.cluster(1.0)
        self.assertEqual(clusterengine.cluster_count, 4)

        titles = {}
        for i in clusterengine.cluster_bins:
            titles[i] = clusterengine.get_cluster_title(i)
        self.assertEqual(titles, {0: 'def', 2: 'abc', 3: 'x'})

        self.assertEqual(clusterengine.cluster_bins, {0: [0, 1, 5], 2: [2, 3, 4, 6, 7], 3: [8]})
        self.assertEqual(clusterengine.index_id_cluster, {0: 0, 1: 0, 2: 2, 3: 2, 4: 2, 5: 0, 6: 2, 7: 2, 8: 3})
