# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
from picard.cluster import TempItemList
from picard.coverart.image import CoverArtImage
from picard.file import File


class TempItemListTest(PicardTestCase):
    """PICARD-3461: TempItemList is a display-only aggregate over an arbitrary
    set of items (albums, tracks, files). Its cover-art images come from all
    selected items, so an album that carries cover art but has no linked files
    (e.g. after moving its files back to the unclustered list) still contributes
    its image instead of showing the placeholder.
    """

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    def _album_with_image(self, album_id, data):
        album = Album(album_id)
        image = CoverArtImage(url='file://' + album_id, data=create_fake_png(data), types=['front'], support_types=True)
        album.metadata.images.append(image)
        album.orig_metadata.images.append(image)
        return album, image

    def test_aggregates_images_from_file_less_albums(self):
        album1, image1 = self._album_with_image('a1', b'a')
        album2, image2 = self._album_with_image('a2', b'b')
        # Neither album has any linked files.
        self.assertEqual([], list(album1.iterfiles()))

        temp = TempItemList(items=[album1, album2])

        image_hashes = set(temp.metadata.images.hash_dict())
        self.assertIn(image1.datahash.hash, image_hashes)
        self.assertIn(image2.datahash.hash, image_hashes)
        self.assertEqual(2, len(temp.metadata.images))

    def test_shared_image_deduplicated(self):
        # Items sharing identical cover art contribute a single image.
        album1, _image1 = self._album_with_image('a1', b'same')
        album2 = Album('a2')
        shared = CoverArtImage(url='file://a2', data=create_fake_png(b'same'), types=['front'], support_types=True)
        album2.metadata.images.append(shared)
        album2.orig_metadata.images.append(shared)

        temp = TempItemList(items=[album1, album2])

        self.assertEqual(1, len(temp.metadata.images))

    def test_iterfiles_yields_underlying_files(self):
        # Files of the selected items are exposed for file operations / drops.
        f1 = File('a.flac')
        f2 = File('b.flac')
        temp = TempItemList(items=[f1, f2])
        self.assertEqual({f1, f2}, set(temp.iterfiles()))

    def test_files_contribute_their_images(self):
        f = File('t.flac')
        image = CoverArtImage(url='file://t', data=create_fake_png(b'z'), types=['front'], support_types=True)
        f.metadata.images.append(image)
        f.orig_metadata.images.append(image)

        temp = TempItemList(items=[f])

        self.assertIn(image.datahash.hash, set(temp.metadata.images.hash_dict()))

    def test_clear_disconnects_and_empties(self):
        album, _image = self._album_with_image('a1', b'a')
        temp = TempItemList(items=[album])
        self.assertEqual(1, len(list(temp.children_metadata_items())))

        temp.clear()

        self.assertEqual([], list(temp.children_metadata_items()))
        # After clear, an image change on the former child must not touch temp.
        images_before = set(temp.metadata.images.hash_dict())
        album.metadata_images_changed.emit()
        self.assertEqual(images_before, set(temp.metadata.images.hash_dict()))
