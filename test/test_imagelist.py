# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2019, 2021 Philipp Wolfer
# Copyright (C) 2018-2019 Wieland Hoffmann
# Copyright (C) 2018-2020 Laurent Monin
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
    ImageList,
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
    test_files[0].metadata.images.append(test_images[0])
    test_files[1].metadata.images.append(test_images[1])
    test_files[2].metadata.images.append(test_images[1])
    test_files[0].orig_metadata.images.append(test_images[0])
    test_files[1].orig_metadata.images.append(test_images[1])
    test_files[2].orig_metadata.images.append(test_images[1])
    return (test_images, test_files)


class UpdateMetadataImagesTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        (self.test_images, self.test_files) = create_test_files()

    def test_update_cluster_images(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files)
        self.assertTrue(update_metadata_images(cluster))
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

        cluster.files.remove(self.test_files[2])
        self.assertFalse(update_metadata_images(cluster))
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

        cluster.files.remove(self.test_files[0])
        self.assertTrue(update_metadata_images(cluster))
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

        cluster.files.append(self.test_files[2])
        self.assertFalse(update_metadata_images(cluster))
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_update_track_images(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files = list(self.test_files)
        self.assertTrue(update_metadata_images(track))
        self.assertEqual(set(self.test_images), set(track.orig_metadata.images))
        self.assertFalse(track.orig_metadata.has_common_images)

        track.files.remove(self.test_files[2])
        self.assertFalse(update_metadata_images(track))
        self.assertEqual(set(self.test_images), set(track.orig_metadata.images))
        self.assertFalse(track.orig_metadata.has_common_images)

        track.files.remove(self.test_files[0])
        self.assertTrue(update_metadata_images(track))
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

        track.files.append(self.test_files[2])
        self.assertFalse(update_metadata_images(track))
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_update_album_images(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        track1 = Track('00000000-0000-0000-0000-000000000001')
        track1.files.append(self.test_files[0])
        track2 = Track('00000000-0000-0000-0000-000000000002')
        track2.files.append(self.test_files[1])
        album.tracks = [track1, track2]
        album.unmatched_files.files.append(self.test_files[2])
        self.assertTrue(update_metadata_images(album))
        self.assertEqual(set(self.test_images), set(album.orig_metadata.images))
        self.assertFalse(album.orig_metadata.has_common_images)

        album.tracks.remove(track2)
        self.assertFalse(update_metadata_images(album))
        self.assertEqual(set(self.test_images), set(album.orig_metadata.images))
        self.assertFalse(album.orig_metadata.has_common_images)

        # album.unmatched_files.files.remove(self.test_files[2])
        album.tracks.remove(track1)
        self.assertTrue(update_metadata_images(album))
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.orig_metadata.has_common_images)

        album.tracks.append(track2)
        self.assertFalse(update_metadata_images(album))
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
        track.files = list(self.test_files)
        update_metadata_images(track)
        track.files.remove(self.test_files[0])
        remove_metadata_images(track, [self.test_files[0]])
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_track_with_common_images(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files = list(self.test_files[1:])
        update_metadata_images(track)
        track.files.remove(self.test_files[1])
        remove_metadata_images(track, [self.test_files[1]])
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_empty_track(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files.append(File('test1.flac'))
        update_metadata_images(track)
        remove_metadata_images(track, [track.files[0]])
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
        added = add_metadata_images(cluster, self.test_files[1:])
        self.assertTrue(added)
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

    def test_add_no_changes(self):
        cluster = Cluster('Test')
        cluster.files = self.test_files
        update_metadata_images(cluster)
        added = add_metadata_images(cluster, [self.test_files[1]])
        self.assertFalse(added)
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))

    def test_add_nothing(self):
        cluster = Cluster('Test')
        cluster.files = self.test_files
        update_metadata_images(cluster)
        added = add_metadata_images(cluster, [])
        self.assertFalse(added)


class ImageListTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.imagelist = ImageList()

        def create_image(name, types):
            return CoverArtImage(
                url='file://file' + name,
                data=create_fake_png(name.encode('utf-8')),
                types=types,
                support_types=True,
                support_multi_types=True
            )

        self.images = {
            'a': create_image('a', ["booklet"]),
            'b': create_image('b', ["booklet", "front"]),
            'c': create_image('c', ["front", "booklet"]),
        }

    def test_append(self):
        self.imagelist.append(self.images['a'])
        self.assertEqual(self.imagelist[0], self.images['a'])

    def test_eq(self):
        list1 = ImageList()
        list2 = ImageList()
        list3 = ImageList()

        list1.append(self.images['a'])
        list1.append(self.images['b'])

        list2.append(self.images['b'])
        list2.append(self.images['a'])

        list3.append(self.images['a'])
        list3.append(self.images['c'])

        self.assertEqual(list1, list2)
        self.assertNotEqual(list1, list3)

    def test_get_front_image(self):
        self.imagelist.append(self.images['a'])
        self.imagelist.append(self.images['b'])
        self.assertEqual(self.imagelist.get_front_image(), self.images['b'])

    def test_to_be_saved_to_tags(self):

        def to_be_saved(settings):
            return self.imagelist.to_be_saved_to_tags(settings=settings)

        settings = {
            "save_images_to_tags": True,
            "embed_only_one_front_image": False,
        }
        # save all but no images
        self.assertEqual(list(to_be_saved(settings)), [])

        # save all, only one non-front image in the list
        self.imagelist.append(self.images['a'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['a']])

        # save all, 2 images, one of them is a front image (b)
        self.imagelist.append(self.images['b'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['a'], self.images['b']])

        # save only one front, 2 images, one of them is a front image (b)
        settings["embed_only_one_front_image"] = True
        self.assertEqual(list(to_be_saved(settings)), [self.images['b']])

        # save only one front, 3 images, two of them have front type (b & c)
        self.imagelist.append(self.images['c'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['b']])

        # 3 images, but do not save
        settings["save_images_to_tags"] = False
        self.assertEqual(list(to_be_saved(settings)), [])

        # settings is missing a setting
        del settings["save_images_to_tags"]
        with self.assertRaises(KeyError):
            next(to_be_saved(settings))

    def test_strip_front_images(self):
        self.imagelist.append(self.images['a'])
        self.imagelist.append(self.images['b'])
        self.imagelist.append(self.images['c'])

        # strip front images from list, only a isn't
        self.assertEqual(len(self.imagelist), 3)
        self.imagelist.strip_front_images()
        self.assertNotIn(self.images['b'], self.imagelist)
        self.assertNotIn(self.images['c'], self.imagelist)
        self.assertIn(self.images['a'], self.imagelist)
        self.assertEqual(len(self.imagelist), 1)

    def test_imagelist_insert(self):
        imagelist = ImageList()
        imagelist.insert(0, 'a')
        self.assertEqual(imagelist[0], 'a')
        imagelist.insert(0, 'b')
        self.assertEqual(imagelist[0], 'b')
        self.assertEqual(imagelist[1], 'a')

    def test_imagelist_clear(self):
        imagelist = ImageList(['a', 'b'])
        self.assertEqual(len(imagelist), 2)
        imagelist.clear()
        self.assertEqual(len(imagelist), 0)

    def test_imagelist_copy(self):
        imagelist1 = ImageList(['a', 'b'])
        imagelist2 = imagelist1.copy()
        imagelist3 = imagelist1
        imagelist1[0] = 'c'
        self.assertEqual(imagelist2[0], 'a')
        self.assertEqual(imagelist3[0], 'c')

    def test_imagelist_del(self):
        imagelist = ImageList(['a', 'b'])
        del imagelist[0]
        self.assertEqual(imagelist[0], 'b')
        self.assertEqual(len(imagelist), 1)
