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
    create_image,
)

from picard.album import Album
from picard.cluster import TempItemList
from picard.coverart.setters import (
    CoverArtSetter,
    CoverArtSetterMode,
)
from picard.file import File
from picard.track import Track


def _front_image(name, data):
    return create_image(data, types=['front'], support_types=True, url='file://' + name)


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
        image = _front_image(album_id, data)
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
        shared = _front_image('a2', b'same')
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
        image = _front_image('t', b'z')
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


class TempItemListCoverArtSetterTest(PicardTestCase):
    """PICARD-3511: Replacing cover art on a multi-track selection in the right
    pane must propagate the image down to the underlying files, not only to the
    aggregate/track metadata. Only the files' metadata is written on save, so if
    the image never reaches the files it is silently dropped even though the UI
    shows it as "New Embedded".
    """

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    @staticmethod
    def _track_with_file(track_id, file_name, image):
        """Build a Track with a single linked file, both carrying ``image``."""
        track = Track(track_id)
        file = File(file_name)
        file.metadata.images.append(image)
        file.orig_metadata.images.append(image)
        track.files.append(file)
        track.metadata.images.append(image)
        track.orig_metadata.images.append(image)
        return track, file

    def test_replace_on_multiselection_reaches_files(self):
        old1 = _front_image('old1', b'old1')
        old2 = _front_image('old2', b'old2')
        track1, file1 = self._track_with_file('t1', 'a.flac', old1)
        track2, file2 = self._track_with_file('t2', 'b.flac', old2)

        temp = TempItemList(items=[track1, track2])

        new_image = _front_image('new', b'new-front')
        setter = CoverArtSetter(CoverArtSetterMode.REPLACE, new_image, temp)
        self.assertTrue(setter.set_coverart())

        # The replaced image must land in each file's metadata, because that is
        # what actually gets embedded when the files are saved.
        for file in (file1, file2):
            file_hashes = set(file.metadata.images.hash_dict())
            self.assertIn(
                new_image.datahash.hash,
                file_hashes,
                msg=f"New front image not embedded in {file.filename}",
            )
            # REPLACE must have stripped the previous front image.
            self.assertEqual([new_image.datahash.hash], list(file_hashes))

    def test_append_on_multiselection_reaches_files(self):
        old1 = _front_image('old1', b'old1')
        old2 = _front_image('old2', b'old2')
        track1, file1 = self._track_with_file('t1', 'a.flac', old1)
        track2, file2 = self._track_with_file('t2', 'b.flac', old2)

        temp = TempItemList(items=[track1, track2])

        new_image = _front_image('new', b'new-front')
        setter = CoverArtSetter(CoverArtSetterMode.APPEND, new_image, temp)
        self.assertTrue(setter.set_coverart())

        for file in (file1, file2):
            file_hashes = set(file.metadata.images.hash_dict())
            self.assertIn(new_image.datahash.hash, file_hashes)

    def test_fileless_album_in_selection_keeps_its_image(self):
        # PICARD-3461 must not regress: an album with cover art but no linked
        # files still gets the replacement image set on its own metadata (it is
        # not wiped by a rebuild-from-children of its empty file list).
        track, _file = self._track_with_file('t1', 'a.flac', _front_image('old', b'old'))
        album = Album('a1')
        album.metadata.images.append(_front_image('albumart', b'albumart'))
        self.assertEqual([], list(album.iterfiles()))

        temp = TempItemList(items=[track, album])

        new_image = _front_image('new', b'new-front')
        setter = CoverArtSetter(CoverArtSetterMode.REPLACE, new_image, temp)
        self.assertTrue(setter.set_coverart())

        self.assertIn(new_image.datahash.hash, set(album.metadata.images.hash_dict()))

    def test_shared_file_not_duplicated_on_append(self):
        # A file reachable via two selected items (an album and one of its
        # tracks) must receive the appended image only once.
        old = _front_image('old', b'old')
        track, file = self._track_with_file('t1', 'a.flac', old)
        album = Album('a1')
        album.tracks = [track]
        # The album exposes the same file through its track.
        self.assertEqual([file], list(album.iterfiles()))

        temp = TempItemList(items=[album, track])

        new_image = _front_image('new', b'new-front')
        setter = CoverArtSetter(CoverArtSetterMode.APPEND, new_image, temp)
        self.assertTrue(setter.set_coverart())

        new_hash = new_image.datahash.hash
        occurrences = [img for img in file.metadata.images if img.datahash.hash == new_hash]
        self.assertEqual(1, len(occurrences))
