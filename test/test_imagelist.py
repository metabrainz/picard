# -*- coding: utf-8 -*-

from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard.album import Album
from picard.cluster import Cluster
from picard.coverart.image import CoverArtImage
from picard.file import File
from picard.track import Track
from picard.util.imagelist import (
    add_metadata_images,
    remove_metadata_images,
    update_metadata_images,
)


def create_test_files():
    test_images = [
        CoverArtImage(url='file://file1', data=create_fake_png(b'a')),
        CoverArtImage(url='file://file2', data=create_fake_png(b'b')),
    ]
    test_files = [
        File('test1.flac'),
        File('test2.flac'),
        File('test2.flac')
    ]
    test_files[0].metadata.append_image(test_images[0])
    test_files[1].metadata.append_image(test_images[1])
    test_files[2].metadata.append_image(test_images[1])
    test_files[0].orig_metadata.append_image(test_images[0])
    test_files[1].orig_metadata.append_image(test_images[1])
    test_files[2].orig_metadata.append_image(test_images[1])
    return (test_images, test_files)


class UpdateMetadataImagesTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        (self.test_images, self.test_files) = create_test_files()

    def test_update_cluster_images(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files)
        update_metadata_images(cluster)
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

        cluster.files.remove(self.test_files[2])
        update_metadata_images(cluster)
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

        cluster.files.remove(self.test_files[0])
        update_metadata_images(cluster)
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

        cluster.files.append(self.test_files[2])
        update_metadata_images(cluster)
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_update_track_images(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.linked_files = list(self.test_files)
        update_metadata_images(track)
        self.assertEqual(set(self.test_images), set(track.orig_metadata.images))
        self.assertFalse(track.orig_metadata.has_common_images)

        track.linked_files.remove(self.test_files[2])
        update_metadata_images(track)
        self.assertEqual(set(self.test_images), set(track.orig_metadata.images))
        self.assertFalse(track.orig_metadata.has_common_images)

        track.linked_files.remove(self.test_files[0])
        update_metadata_images(track)
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

        track.linked_files.append(self.test_files[2])
        update_metadata_images(track)
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_update_album_images(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        track1 = Track('00000000-0000-0000-0000-000000000001')
        track1.linked_files.append(self.test_files[0])
        track2 = Track('00000000-0000-0000-0000-000000000002')
        track2.linked_files.append(self.test_files[1])
        album.tracks = [track1, track2]
        album.unmatched_files.files.append(self.test_files[2])
        update_metadata_images(album)
        self.assertEqual(set(self.test_images), set(album.orig_metadata.images))
        self.assertFalse(album.orig_metadata.has_common_images)

        album.tracks.remove(track2)
        update_metadata_images(album)
        self.assertEqual(set(self.test_images), set(album.orig_metadata.images))
        self.assertFalse(album.orig_metadata.has_common_images)

        # album.unmatched_files.files.remove(self.test_files[2])
        album.tracks.remove(track1)
        update_metadata_images(album)
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.orig_metadata.has_common_images)

        album.tracks.append(track2)
        update_metadata_images(album)
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.orig_metadata.has_common_images)


class RemoveMetadataImagesTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        (self.test_images, self.test_files) = create_test_files()

    def test_remove_from_cluster(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files)
        update_metadata_images(cluster)
        cluster.files.remove(self.test_files[0])
        remove_metadata_images(cluster, [self.test_files[0]])
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_remove_from_cluster_with_common_images(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files[1:])
        update_metadata_images(cluster)
        cluster.files.remove(self.test_files[1])
        remove_metadata_images(cluster, [self.test_files[1]])
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_remove_from_empty_cluster(self):
        cluster = Cluster('Test')
        cluster.files.append(File('test1.flac'))
        update_metadata_images(cluster)
        remove_metadata_images(cluster, [cluster.files[0]])
        self.assertEqual(set(), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_remove_from_track(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.linked_files = list(self.test_files)
        update_metadata_images(track)
        track.linked_files.remove(self.test_files[0])
        remove_metadata_images(track, [self.test_files[0]])
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_track_with_common_images(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.linked_files = list(self.test_files[1:])
        update_metadata_images(track)
        track.linked_files.remove(self.test_files[1])
        remove_metadata_images(track, [self.test_files[1]])
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_empty_track(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.linked_files.append(File('test1.flac'))
        update_metadata_images(track)
        remove_metadata_images(track, [track.linked_files[0]])
        self.assertEqual(set(), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_album(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        album.unmatched_files.files = list(self.test_files)
        update_metadata_images(album)
        album.unmatched_files.files.remove(self.test_files[0])
        remove_metadata_images(album, [self.test_files[0]])
        self.assertEqual(set(self.test_images[1:]), set(album.metadata.images))
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.metadata.has_common_images)
        self.assertTrue(album.orig_metadata.has_common_images)

    def test_remove_from_album_with_common_images(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        album.unmatched_files.files = list(self.test_files[1:])
        update_metadata_images(album)
        album.unmatched_files.files.remove(self.test_files[1])
        remove_metadata_images(album, [self.test_files[1]])
        self.assertEqual(set(self.test_images[1:]), set(album.metadata.images))
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.metadata.has_common_images)
        self.assertTrue(album.orig_metadata.has_common_images)

    def test_remove_from_empty_album(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        album.unmatched_files.files.append(File('test1.flac'))
        update_metadata_images(album)
        remove_metadata_images(album, [album.unmatched_files.files[0]])
        self.assertEqual(set(), set(album.metadata.images))
        self.assertEqual(set(), set(album.orig_metadata.images))
        self.assertTrue(album.metadata.has_common_images)
        self.assertTrue(album.orig_metadata.has_common_images)


class AddMetadataImagesTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        (self.test_images, self.test_files) = create_test_files()

    def test_add_to_cluster(self):
        cluster = Cluster('Test')
        cluster.files = [self.test_files[0]]
        update_metadata_images(cluster)
        cluster.files += self.test_files[1:]
        add_metadata_images(cluster, self.test_files[1:])
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)
