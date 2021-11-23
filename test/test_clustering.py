# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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
    Cluster,
    tokenize,
)
from picard.file import File


class TokenizeTest(PicardTestCase):

    def test_tokenize(self):
        token = tokenize("")
        self.assertEqual(token, "")

        token = tokenize(" \t ")
        self.assertEqual(token, "")

        token = tokenize(" A\tWord-test ")
        self.assertEqual(token, "awordtest")


class ClusterTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values({
            'windows_compatibility': False
        })

    def _create_file(self, album, artist, filename="foo.mp3"):
        file = File(filename)
        file.metadata['album'] = album
        file.metadata['artist'] = artist
        return file

    def assertClusterEqual(self, album, artist, files, cluster):
        self.assertEqual(album, cluster.title)
        self.assertEqual(artist, cluster.artist)
        self.assertEqual(set(files), set(cluster.files))

    def test_cluster_none(self):
        clusters = list(Cluster.cluster([]))
        # No cluster is being created
        self.assertEqual(0, len(clusters))

    def test_cluster_single_file(self):
        files = [
            self._create_file('album foo', 'artist foo'),
        ]
        clusters = list(Cluster.cluster(files))
        # No cluster is being created for single files
        self.assertEqual(0, len(clusters))

    def test_cluster_single_cluster(self):
        files = [
            self._create_file('album foo', 'artist bar'),
            self._create_file('album foo', 'artist foo'),
            self._create_file('album foo', 'artist foo'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(1, len(clusters))
        self.assertClusterEqual('album foo', 'artist foo', files, clusters[0])

    def test_cluster_multi(self):
        files = [
            self._create_file('album cluster1', 'artist bar'),
            self._create_file('album cluster2', 'artist foo'),
            self._create_file('album cluster1', 'artist foo'),
            self._create_file('albumcluster2', 'artist bar'),
            self._create_file('album nocluster', 'artist bar'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(2, len(clusters))
        self.assertClusterEqual('album cluster1', 'artist bar', {files[0], files[2]}, clusters[0])
        self.assertClusterEqual('album cluster2', 'artist foo', {files[1], files[3]}, clusters[1])

    def test_cluster_by_path(self):
        files = [
            self._create_file(None, None, 'artist1/album1/foo1.ogg'),
            self._create_file(None, None, 'album2/foo1.ogg'),
            self._create_file(None, None, 'artist1/album1/foo2.ogg'),
            self._create_file(None, None, 'album2/foo2.ogg'),
            self._create_file(None, None, 'nocluster/foo.ogg'),
            self._create_file(None, None, 'album1/foo3.ogg'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(2, len(clusters))
        self.assertClusterEqual('album1', 'artist1', {files[0], files[2], files[5]}, clusters[0])
        self.assertClusterEqual('album2', 'Various Artists', {files[1], files[3]}, clusters[1])

    def test_cluster_no_metadata(self):
        files = [
            self._create_file(None, None, 'foo1.ogg'),
            self._create_file(None, None, 'foo2.ogg'),
            self._create_file(None, None, 'foo3.ogg'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(0, len(clusters))

    # def test_common_artist_name(self):
    #     files = [
    #         self._create_file('cluster 1', 'artist 1'),
    #         self._create_file('cluster 1', 'artist 2'),
    #         self._create_file('cluster 1', 'artist2'),
    #         self._create_file('cluster 1', 'artist 1'),
    #         self._create_file('cluster 1', 'artist 2'),
    #     ]
    #     clusters = list(Cluster.cluster(files))
    #     self.assertEqual(1, len(clusters))
    #     self.assertClusterEqual('cluster 1', 'artist 2', files, clusters[0])
