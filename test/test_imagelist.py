# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2019 Wieland Hoffmann
# Copyright (C) 2018-2021 Philipp Wolfer
# Copyright (C) 2018-2022, 2024-2026 Laurent Monin
# Copyright (C) 2025 Bob Swift
# Copyright (C) 2026 Bryan Roessler
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard.album import Album
from picard.cluster import Cluster
from picard.coverart.image import CoverArtImage
from picard.file import File
from picard.track import Track
from picard.util.imagelist import ImageList


def create_test_files():
    test_images = [
        CoverArtImage(url='file://file1', data=create_fake_png(b'a')),
        CoverArtImage(url='file://file2', data=create_fake_png(b'b')),
    ]
    test_files = [
        File('test1.flac'),
        File('test2.flac'),
        File('test2.flac'),
    ]
    test_files[0].metadata.images.append(test_images[0])
    test_files[1].metadata.images.append(test_images[1])
    test_files[2].metadata.images.append(test_images[1])
    test_files[0].orig_metadata.images.append(test_images[0])
    test_files[1].orig_metadata.images.append(test_images[1])
    test_files[2].orig_metadata.images.append(test_images[1])
    return (test_images, test_files)


def create_front_image(name, width, height):
    """Create a front CoverArtImage with explicit dimensions."""
    image = CoverArtImage(
        url='file://' + name,
        data=create_fake_png(name.encode('utf-8')),
        types=['front'],
        support_types=True,
    )
    image.width = width
    image.height = height
    return image


class UpdateMetadataImagesTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        (self.test_images, self.test_files) = create_test_files()

    def test_update_cluster_images(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files)
        self.assertTrue(cluster.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

        cluster.files.remove(self.test_files[2])
        self.assertFalse(cluster.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

        cluster.files.remove(self.test_files[0])
        self.assertTrue(cluster.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

        cluster.files.append(self.test_files[2])
        self.assertFalse(cluster.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_update_track_images(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files = list(self.test_files)
        self.assertTrue(track.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images), set(track.orig_metadata.images))
        self.assertFalse(track.orig_metadata.has_common_images)

        track.files.remove(self.test_files[2])
        self.assertFalse(track.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images), set(track.orig_metadata.images))
        self.assertFalse(track.orig_metadata.has_common_images)

        track.files.remove(self.test_files[0])
        self.assertTrue(track.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

        track.files.append(self.test_files[2])
        self.assertFalse(track.update_metadata_images_from_children())
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
        self.assertTrue(album.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images), set(album.orig_metadata.images))
        self.assertFalse(album.orig_metadata.has_common_images)

        album.tracks.remove(track2)
        self.assertFalse(album.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images), set(album.orig_metadata.images))
        self.assertFalse(album.orig_metadata.has_common_images)

        album.tracks.remove(track1)
        self.assertTrue(album.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.orig_metadata.has_common_images)

        album.tracks.append(track2)
        self.assertFalse(album.update_metadata_images_from_children())
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.orig_metadata.has_common_images)


class RemoveMetadataImagesTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        (self.test_images, self.test_files) = create_test_files()

    def test_remove_from_cluster(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files)
        self.assertTrue(cluster.update_metadata_images_from_children())
        cluster.files.remove(self.test_files[0])
        self.assertTrue(cluster.remove_metadata_images_from_children([self.test_files[0]]))
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_remove_from_cluster_with_common_images(self):
        cluster = Cluster('Test')
        cluster.files = list(self.test_files[1:])
        self.assertTrue(cluster.update_metadata_images_from_children())
        cluster.files.remove(self.test_files[1])
        self.assertFalse(cluster.remove_metadata_images_from_children([self.test_files[1]]))
        self.assertEqual(set(self.test_images[1:]), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_remove_from_empty_cluster(self):
        cluster = Cluster('Test')
        cluster.files.append(File('test1.flac'))
        self.assertFalse(cluster.update_metadata_images_from_children())
        self.assertFalse(cluster.remove_metadata_images_from_children([cluster.files[0]]))
        self.assertEqual(set(), set(cluster.metadata.images))
        self.assertTrue(cluster.metadata.has_common_images)

    def test_remove_from_track(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files = list(self.test_files)
        self.assertTrue(track.update_metadata_images_from_children())
        track.files.remove(self.test_files[0])
        self.assertTrue(track.remove_metadata_images_from_children([self.test_files[0]]))
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_track_with_common_images(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files = list(self.test_files[1:])
        self.assertTrue(track.update_metadata_images_from_children())
        track.files.remove(self.test_files[1])
        self.assertFalse(track.remove_metadata_images_from_children([self.test_files[1]]))
        self.assertEqual(set(self.test_images[1:]), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_empty_track(self):
        track = Track('00000000-0000-0000-0000-000000000000')
        track.files.append(File('test1.flac'))
        self.assertFalse(track.update_metadata_images_from_children())
        self.assertFalse(track.remove_metadata_images_from_children([track.files[0]]))
        self.assertEqual(set(), set(track.orig_metadata.images))
        self.assertTrue(track.orig_metadata.has_common_images)

    def test_remove_from_album(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        album.unmatched_files.files = list(self.test_files)
        self.assertTrue(album.update_metadata_images_from_children())
        album.unmatched_files.files.remove(self.test_files[0])
        self.assertTrue(album.remove_metadata_images_from_children([self.test_files[0]]))
        self.assertEqual(set(self.test_images[1:]), set(album.metadata.images))
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.metadata.has_common_images)
        self.assertTrue(album.orig_metadata.has_common_images)

    def test_remove_from_album_with_common_images(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        album.unmatched_files.files = list(self.test_files[1:])
        self.assertTrue(album.update_metadata_images_from_children())
        album.unmatched_files.files.remove(self.test_files[1])
        self.assertFalse(album.remove_metadata_images_from_children([self.test_files[1]]))
        self.assertEqual(set(self.test_images[1:]), set(album.metadata.images))
        self.assertEqual(set(self.test_images[1:]), set(album.orig_metadata.images))
        self.assertTrue(album.metadata.has_common_images)
        self.assertTrue(album.orig_metadata.has_common_images)

    def test_remove_from_empty_album(self):
        album = Album('00000000-0000-0000-0000-000000000000')
        album.unmatched_files.files.append(File('test1.flac'))
        self.assertFalse(album.update_metadata_images_from_children())
        self.assertFalse(album.remove_metadata_images_from_children([album.unmatched_files.files[0]]))
        self.assertEqual(set(), set(album.metadata.images))
        self.assertEqual(set(), set(album.orig_metadata.images))
        self.assertTrue(album.metadata.has_common_images)
        self.assertTrue(album.orig_metadata.has_common_images)


class AddMetadataImagesTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        (self.test_images, self.test_files) = create_test_files()

    def test_add_to_cluster(self):
        cluster = Cluster('Test')
        cluster.files = [self.test_files[0]]
        self.assertTrue(cluster.update_metadata_images_from_children())
        cluster.files += self.test_files[1:]
        self.assertTrue(cluster.add_metadata_images_from_children(self.test_files[1:]))
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))
        self.assertFalse(cluster.metadata.has_common_images)

    def test_add_no_changes(self):
        cluster = Cluster('Test')
        cluster.files = self.test_files
        self.assertTrue(cluster.update_metadata_images_from_children())
        self.assertFalse(cluster.add_metadata_images_from_children([self.test_files[1]]))
        self.assertEqual(set(self.test_images), set(cluster.metadata.images))

    def test_add_nothing(self):
        cluster = Cluster('Test')
        cluster.files = self.test_files
        self.assertTrue(cluster.update_metadata_images_from_children())
        self.assertFalse(cluster.add_metadata_images_from_children([]))


class ImageListTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.imagelist = ImageList()

        def create_image(name, types):
            return CoverArtImage(
                url='file://file' + name,
                data=create_fake_png(name.encode('utf-8')),
                types=types,
                support_types=True,
                support_multi_types=True,
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

    def test_to_be_saved_to_tags_with_previous_images(self):
        """A "never replace with smaller" rejection only excludes the image
        from tags, it stays available for external file saving."""
        self.set_config_values(
            {
                'dont_replace_with_smaller_cover': True,
                'dont_replace_cover_of_types': False,
                'dont_replace_included_types': [],
            }
        )
        settings = {
            "save_images_to_tags": True,
            "embed_only_one_front_image": False,
        }
        previous_image = self.images['b']  # front, larger by default (same size here)
        previous_image.width = 1000
        previous_image.height = 1000
        previous_images = ImageList([previous_image])

        smaller_front = self.images['c']
        smaller_front.width = 500
        smaller_front.height = 500
        self.imagelist.append(smaller_front)

        # rejected for tags because it is smaller than the previous front image
        self.assertEqual(list(self.imagelist.to_be_saved_to_tags(settings, previous_images)), [])
        # still available for saving to an external file
        self.assertEqual(
            list(
                self.imagelist.to_be_saved_to_files({"save_images_to_files": True, "save_only_one_front_image": False})
            ),
            [smaller_front],
        )

        # without previous_images, no per-file filtering happens
        self.assertEqual(list(self.imagelist.to_be_saved_to_tags(settings)), [smaller_front])

    def test_to_be_saved_to_files(self):
        def to_be_saved(settings):
            return self.imagelist.to_be_saved_to_files(settings=settings)

        settings = {
            "save_images_to_files": True,
            "save_only_one_front_image": False,
        }
        # save all but no images in list
        self.assertEqual(list(to_be_saved(settings)), [])

        # save all, only one non-front image in the list
        self.imagelist.append(self.images['a'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['a']])

        # save all, 2 images, one of them is a front image (b)
        self.imagelist.append(self.images['b'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['a'], self.images['b']])

        # save only one front, 2 images, one of them is a front image (b)
        settings["save_only_one_front_image"] = True
        self.assertEqual(list(to_be_saved(settings)), [self.images['b']])

        # save only one front, 3 images, two of them have front type (b & c)
        self.imagelist.append(self.images['c'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['b']])

        # save only one front, but no front image exists — falls back to all
        self.imagelist = ImageList()
        self.imagelist.append(self.images['a'])
        self.assertEqual(list(to_be_saved(settings)), [self.images['a']])

        # 3 images, but save disabled
        self.imagelist.append(self.images['b'])
        self.imagelist.append(self.images['c'])
        settings["save_images_to_files"] = False
        self.assertEqual(list(to_be_saved(settings)), [])

        # settings is missing a setting
        del settings["save_images_to_files"]
        with self.assertRaises(KeyError):
            next(to_be_saved(settings))

    def test_should_remove_images_from_tags_requires_something_to_export(self):
        """Never report tags-removal as intended unless an image will
        actually be saved to an external file, to avoid deleting cover art
        without keeping it anywhere (see PICARD-3380)."""
        settings = {
            "remove_images_from_tags": True,
            "save_images_to_files": True,
            "save_only_one_front_image": False,
        }
        # nothing in the list to export: must not report removal as safe
        self.assertFalse(self.imagelist.should_remove_images_from_tags(settings))

        # an image is available to export: removal is safe
        self.imagelist.append(self.images['a'])
        self.assertTrue(self.imagelist.should_remove_images_from_tags(settings))

        # explicitly disabled by user
        settings["remove_images_from_tags"] = False
        self.assertFalse(self.imagelist.should_remove_images_from_tags(settings))

        # not saving to files at all: nothing will be kept
        settings["remove_images_from_tags"] = True
        settings["save_images_to_files"] = False
        self.assertFalse(self.imagelist.should_remove_images_from_tags(settings))

    def test_to_be_saved_to_files_keeps_higher_quality_previous_image(self):
        """When tags are about to be cleared, a previously tagged image is
        exported to disk instead of being lost, unless a same-or-better
        replacement is already being exported (see PICARD-3380)."""

        settings = {
            "remove_images_from_tags": True,
            "save_images_to_files": True,
            "save_only_one_front_image": False,
        }
        previous_front = create_front_image('previous', 1000, 1000)
        previous_images = ImageList([previous_front])

        # no new image at all: the previous (tagged) image is preserved
        self.assertEqual(list(self.imagelist.to_be_saved_to_files(settings, previous_images)), [previous_front])

        # new replacement is smaller: the previous, bigger image is used instead
        smaller_front = create_front_image('smaller', 500, 500)
        self.imagelist.append(smaller_front)
        self.assertEqual(list(self.imagelist.to_be_saved_to_files(settings, previous_images)), [previous_front])

        # new replacement is bigger: it is exported, the previous one is not duplicated
        bigger_front = create_front_image('bigger', 2000, 2000)
        self.imagelist = ImageList([bigger_front])
        self.assertEqual(list(self.imagelist.to_be_saved_to_files(settings, previous_images)), [bigger_front])

        # without previous_images, nothing extra is added
        self.assertEqual(list(self.imagelist.to_be_saved_to_files(settings)), [bigger_front])

    def test_get_types_dict_keeps_biggest_image_per_type(self):
        """The biggest image of each type must win.

        `is_bigger_image_filter()` compares a downloaded image against this
        mapping to avoid replacing embedded art with something smaller, so the
        mapping has to hold the biggest image already present for a type, not
        the smallest. The result must not depend on insertion order.
        """
        big = create_front_image('big', 1000, 1000)
        small = create_front_image('small', 200, 200)

        for images in ([big, small], [small, big]):
            with self.subTest(order=[(image.width, image.height) for image in images]):
                types_dict = ImageList(images).get_types_dict()
                self.assertEqual(types_dict[big.normalized_types()], big)

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
