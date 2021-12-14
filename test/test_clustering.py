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
    FileCluster,
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
            'windows_compatibility': False,
            'va_name': 'Diverse Interpreten',
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
        self.assertEqual(1, len(clusters))

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
            self._create_file('album single', 'artist bar'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(3, len(clusters))
        self.assertClusterEqual('album cluster1', 'artist bar', {files[0], files[2]}, clusters[0])
        self.assertClusterEqual('album cluster2', 'artist foo', {files[1], files[3]}, clusters[1])
        self.assertClusterEqual('album single', 'artist bar', {files[4]}, clusters[2])

    def test_cluster_by_path(self):
        files = [
            self._create_file(None, None, 'artist1/album1/foo1.ogg'),
            self._create_file(None, None, 'album2/foo1.ogg'),
            self._create_file(None, None, 'artist1/album1/foo2.ogg'),
            self._create_file(None, None, 'album2/foo2.ogg'),
            self._create_file(None, None, 'single/foo.ogg'),
            self._create_file(None, None, 'album1/foo3.ogg'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(3, len(clusters))
        self.assertClusterEqual('album1', 'artist1', {files[0], files[2], files[5]}, clusters[0])
        self.assertClusterEqual('album2', 'Diverse Interpreten', {files[1], files[3]}, clusters[1])
        self.assertClusterEqual('single', 'Diverse Interpreten', {files[4]}, clusters[2])

    def test_cluster_no_metadata(self):
        files = [
            self._create_file(None, None, 'foo1.ogg'),
            self._create_file(None, None, 'foo2.ogg'),
            self._create_file(None, None, 'foo3.ogg'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(0, len(clusters))

    def test_common_artist_name(self):
        files = [
            self._create_file('cluster 1', 'artist 1'),
            self._create_file('cluster 1', 'artist 2'),
            self._create_file('cluster 1', 'artist2'),
            self._create_file('cluster 1', 'artist 1'),
            self._create_file('cluster 1', 'artist 2'),
        ]
        clusters = list(Cluster.cluster(files))
        self.assertEqual(1, len(clusters))
        self.assertClusterEqual('cluster 1', 'artist 2', files, clusters[0])


class FileClusterTest(PicardTestCase):

    def test_single(self):
        file = File('foo')
        fc = FileCluster()
        fc.add('album 1', 'artist 1', file)
        self.assertEqual('album 1', fc.title)
        self.assertEqual('artist 1', fc.artist)
        self.assertEqual([file], list(fc.files))

    def test_multi(self):
        files = [
            File('foo1'),
            File('foo2'),
            File('foo3'),
            File('foo4'),
            File('foo5'),
        ]
        fc = FileCluster()
        fc.add('album 1', 'artist1', files[0])
        fc.add('Album 1', 'artist 2', files[1])
        fc.add('album\t1', 'Artist 1', files[2])
        fc.add('Album 1', 'Artist 2', files[3])
        fc.add('album 2', 'Artist 1', files[4])
        self.assertEqual('Album 1', fc.title)
        self.assertEqual('Artist 1', fc.artist)
        self.assertEqual(files, list(fc.files))
