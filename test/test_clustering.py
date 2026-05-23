# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021, 2026 Philipp Wolfer
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

from unittest.mock import (
    Mock,
    patch,
)

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
        self.patch_tagger_instance('picard.item')
        self.cluster = Cluster("Test")

    def test_cluster_is_truthy(self):
        # Empty cluster should still be truthy
        self.assertEqual(0, len(self.cluster))
        self.assertTrue(self.cluster)

    def test_column(self):
        self.cluster.metadata['test'] = 'foo'
        self.assertEqual(self.cluster.column('test'), 'foo')
        self.assertEqual(self.cluster.column('unknown'), '')

    def test_column_special(self):
        self.cluster.metadata['album'] = 'Foo'
        self.cluster.metadata.images.append(Mock())
        file1 = File('somefile.opus')
        file1.metadata.length = 6000
        self.cluster.files.append(file1)
        self.assertEqual(self.cluster.column('album'), 'Foo')
        self.assertEqual(self.cluster.column('covercount'), '1')
        self.assertEqual(self.cluster.column('~length'), '0:06')

        self.cluster.special = True
        self.assertEqual(self.cluster.column('album'), '')
        self.assertEqual(self.cluster.column('covercount'), '')
        self.assertEqual(self.cluster.column('~length'), '')

    def test_column_length(self):
        self.assertEqual(self.cluster.column('~length'), '?:??')
        file1 = File('somefile.opus')
        file1.metadata.length = 6000
        self.cluster.files.append(file1)
        self.assertEqual(self.cluster.files.length, 6000)
        self.assertEqual(self.cluster.column('~length'), '0:06')
        file2 = File('somefile.opus')
        file2.metadata.length = 7000
        self.cluster.files.append(file2)
        self.assertEqual(self.cluster.files.length, 13000)
        self.assertEqual(self.cluster.column('~length'), '0:13')

    def test_column_title(self):
        self.assertEqual(self.cluster.column('title'), 'Test (0)')
        self.cluster.files.append(File('somefile.opus'))
        self.assertEqual(self.cluster.column('title'), 'Test (1)')

    def test_column_artist(self):
        self.cluster.metadata['artist'] = 'The Artist'
        self.cluster.metadata['albumartist'] = 'The Album Artist'
        self.assertEqual(self.cluster.column('artist'), 'The Album Artist')
        self.assertEqual(self.cluster.column('artist'), self.cluster.column('albumartist'))

    def test_column_tracknumber(self):
        self.cluster.metadata['tracknumber'] = '3'
        self.cluster.metadata['totaltracks'] = '42'
        self.assertEqual(self.cluster.column('tracknumber'), '42')
        self.assertEqual(self.cluster.column('tracknumber'), self.cluster.column('totaltracks'))

    def test_column_discnumber(self):
        self.cluster.metadata['discnumber'] = '3'
        self.cluster.metadata['totaldiscs'] = '42'
        self.assertEqual(self.cluster.column('discnumber'), '42')
        self.assertEqual(self.cluster.column('discnumber'), self.cluster.column('totaldiscs'))

    def test_column_coverart(self):
        image = Mock()
        image.dimensions_as_string.return_value = '100x100'
        self.cluster.metadata.images.append(image)
        self.assertEqual(self.cluster.column('covercount'), '1')
        self.assertEqual(self.cluster.column('coverdimensions'), '100x100')

    def test_remove_file_not_in_list(self):
        """Test that removing a file not in the cluster doesn't crash (race condition)"""
        file = Mock()
        # File is NOT in the cluster
        self.assertNotIn(file, self.cluster.files)
        # Mock all the methods that would be called
        with (
            patch.object(self.cluster, 'update'),
            patch.object(self.cluster, '_ui_item', Mock()),
            patch.object(self.cluster, 'remove_metadata_images_from_children'),
        ):
            # This should not raise ValueError
            self.cluster.remove_file(file, new_album=False)
            self.cluster.remove_file(file, new_album=False)


class ClusteringTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(
            {
                'windows_compatibility': False,
                'va_name': 'Diverse Interpreten',
            }
        )

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
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

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


class ComputeAggregateTagsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.cluster = Cluster("Test")

    def _add_files(self, tag, values):
        for v in values:
            f = File('test.flac')
            if v:
                f.metadata[tag] = v
            self.cluster.files.append(f)

    def test_all_agree(self):
        self._add_files('barcode', ['123', '123', '123'])
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result['barcode'], '123')

    def test_majority_agree(self):
        self._add_files('barcode', ['123', '123', '123', '', ''])
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result['barcode'], '123')

    def test_below_majority(self):
        self._add_files('barcode', ['123', '', '', '', ''])
        result = self.cluster._compute_aggregate_tags()
        self.assertNotIn('barcode', result)

    def test_disagreement(self):
        self._add_files('barcode', ['123', '456', '123', '456', '123'])
        result = self.cluster._compute_aggregate_tags()
        self.assertNotIn('barcode', result)

    def test_no_files(self):
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result, {})

    def test_multi_valued_identical(self):
        self._add_files('label', ['Rhino; Warner', 'Rhino; Warner', 'Rhino; Warner'])
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result['label'], 'Rhino; Warner')

    def test_multi_valued_intersection(self):
        self._add_files('label', ['Rhino; Warner', 'Rhino; Warner', 'Rhino'])
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result['label'], 'Rhino')

    def test_multi_valued_no_common(self):
        self._add_files('label', ['Rhino', 'Rhino', 'Warner'])
        result = self.cluster._compute_aggregate_tags()
        self.assertNotIn('label', result)

    def test_multi_valued_different_order(self):
        self._add_files('label', ['Rhino; Warner', 'Warner; Rhino', 'Rhino; Warner'])
        result = self.cluster._compute_aggregate_tags()
        # All have same components, fast path catches identical strings for 2/3,
        # slow path finds intersection {Rhino, Warner}
        self.assertIn('Rhino', result['label'])
        self.assertIn('Warner', result['label'])

    def test_date_all_agree(self):
        self._add_files('date', ['2007-03-30', '2007-03-30', '2007-03-30'])
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result['date'], '2007-03-30')

    def test_date_disagree(self):
        self._add_files('date', ['2007-03-30', '2007-03-30', '2007'])
        result = self.cluster._compute_aggregate_tags()
        self.assertNotIn('date', result)

    def test_catno_intersection(self):
        self._add_files('catalognumber', ['ABC-123; DEF-456', 'ABC-123; DEF-456', 'ABC-123'])
        result = self.cluster._compute_aggregate_tags()
        self.assertEqual(result['catalognumber'], 'ABC-123')
