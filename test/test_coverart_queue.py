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


from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.coverart import CoverArt


class CoverArtAllImagesSatisfiedTest(PicardTestCase):
    """Tests for CoverArt._all_images_satisfied optimization."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.coverart')
        album = Mock()
        album.tagger = Mock()
        metadata = Mock()
        release = {}
        self.coverart = CoverArt(album, metadata, release)

    def _make_config(self, save_to_tags=True, embed_only_front=True, save_to_files=True, save_only_front_file=False):
        config = Mock()
        config.setting = {
            'save_images_to_tags': save_to_tags,
            'embed_only_one_front_image': embed_only_front,
            'save_images_to_files': save_to_files,
            'save_only_one_front_image': save_only_front_file,
        }
        return config

    def test_not_satisfied_when_no_front_found(self):
        """Never satisfied if no front image has been found yet."""
        self.coverart.front_image_found = False
        config = self._make_config()
        self.assertFalse(self.coverart._all_images_satisfied(config))

    def test_satisfied_tags_only_front_no_files(self):
        """Original case: only embedding one front, no external files."""
        self.coverart.front_image_found = True
        config = self._make_config(
            save_to_tags=True,
            embed_only_front=True,
            save_to_files=False,
            save_only_front_file=False,
        )
        self.assertTrue(self.coverart._all_images_satisfied(config))

    def test_not_satisfied_tags_wants_all(self):
        """Tags wants all images (embed_only_one_front_image=False)."""
        self.coverart.front_image_found = True
        config = self._make_config(
            save_to_tags=True,
            embed_only_front=False,
            save_to_files=False,
            save_only_front_file=False,
        )
        self.assertFalse(self.coverart._all_images_satisfied(config))

    def test_not_satisfied_files_wants_all(self):
        """Files wants all images (save_only_one_front_image=False)."""
        self.coverart.front_image_found = True
        config = self._make_config(
            save_to_tags=True,
            embed_only_front=True,
            save_to_files=True,
            save_only_front_file=False,
        )
        self.assertFalse(self.coverart._all_images_satisfied(config))

    def test_satisfied_both_want_only_front(self):
        """Both tags and files want only the front image."""
        self.coverart.front_image_found = True
        config = self._make_config(
            save_to_tags=True,
            embed_only_front=True,
            save_to_files=True,
            save_only_front_file=True,
        )
        self.assertTrue(self.coverart._all_images_satisfied(config))

    def test_satisfied_files_only_front_no_tags(self):
        """Only saving files with only front, tags disabled."""
        self.coverart.front_image_found = True
        config = self._make_config(
            save_to_tags=False,
            embed_only_front=False,
            save_to_files=True,
            save_only_front_file=True,
        )
        self.assertTrue(self.coverart._all_images_satisfied(config))

    def test_not_satisfied_both_disabled(self):
        """Both disabled — technically satisfied (nothing needed)."""
        self.coverart.front_image_found = True
        config = self._make_config(
            save_to_tags=False,
            embed_only_front=False,
            save_to_files=False,
            save_only_front_file=False,
        )
        self.assertTrue(self.coverart._all_images_satisfied(config))
