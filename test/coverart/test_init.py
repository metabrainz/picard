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

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

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

    @subtest_cases(
        "config_overrides,expected",
        {
            'tags want only the front, no external files': ({'save_to_files': False}, True),
            'tags want all images': ({'embed_only_front': False, 'save_to_files': False}, False),
            'files want all images': ({}, False),
            'both want only the front': ({'save_only_front_file': True}, True),
            'files want only the front, tags disabled': (
                {'save_to_tags': False, 'embed_only_front': False, 'save_only_front_file': True},
                True,
            ),
            'both destinations disabled': (
                {'save_to_tags': False, 'embed_only_front': False, 'save_to_files': False},
                True,
            ),
        },
    )
    def test_all_images_satisfied(self, config_overrides, expected):
        """A front image has been found; check each combination of destinations.

        Each case lists only the settings that differ from `_make_config()`'s
        defaults (save_to_tags=True, embed_only_front=True, save_to_files=True,
        save_only_front_file=False).
        """
        self.coverart.front_image_found = True
        config = self._make_config(**config_overrides)
        # assertTrue/assertFalse rather than assertEqual, to keep the original
        # truthiness checks rather than requiring exactly True/False
        check = self.assertTrue if expected else self.assertFalse
        check(self.coverart._all_images_satisfied(config))
