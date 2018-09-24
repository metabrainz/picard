# -*- coding: utf-8 -*-

import os
import struct
import unittest

from picard.album import Album
from picard.cluster import Cluster
from picard.coverart.image import CoverArtImage
from picard.track import Track
from picard.file import File
from picard.util.imagelist import (
    update_metadata_images
)


def create_fake_png(extra):
    """Creates fake PNG data that satisfies Picard's internal image type detection"""
    return b'\x89PNG\x0D\x0A\x1A\x0A' + (b'a' * 4) + b'IHDR' + struct.pack('>LL', 100, 100) + extra


class UpdateMetadataImagesTest(unittest.TestCase):

    def setUp(self):
        self.test_images = [
            CoverArtImage(data=create_fake_png(b'a')),
            CoverArtImage(data=create_fake_png(b'b')),
        ]
        self.test_files = [
            File('test1.flac'),
            File('test2.flac'),
            File('test2.flac')
        ]
        self.test_files[0].metadata.append_image(self.test_images[0])
        self.test_files[1].metadata.append_image(self.test_images[1])
        self.test_files[2].metadata.append_image(self.test_images[1])
        self.test_files[0].orig_metadata.append_image(self.test_images[0])
        self.test_files[1].orig_metadata.append_image(self.test_images[1])
        self.test_files[2].orig_metadata.append_image(self.test_images[1])

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
