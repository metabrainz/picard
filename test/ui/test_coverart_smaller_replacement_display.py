# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Aman Tebriwal
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


"""PICARD-3531: a smaller downloaded cover that "Never replace cover images
with smaller ones" will reject must not be shown as "New Cover Art"."""

from test.ui.test_coverart_removal_display import (
    FakeImage,
    _make_item,
    _RemovalBox,
)

from picard.config import get_config

import pytest


class SizedImage(FakeImage):
    can_be_saved_to_tags = True

    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height


@pytest.fixture
def no_smaller_settings():
    config = get_config()
    config.setting['save_images_to_tags'] = True
    config.setting['embed_only_one_front_image'] = False
    config.setting['save_images_to_files'] = False
    config.setting['remove_images_from_tags'] = False
    config.setting['dont_replace_with_smaller_cover'] = True
    config.setting['dont_replace_cover_of_types'] = False
    return config


def test_smaller_rejected_cover_not_shown_as_new(no_smaller_settings):
    orig = SizedImage(1000, 1000)
    new = SizedImage(500, 500)
    box = _RemovalBox(_make_item([new], [orig]))
    box.update_metadata()
    # Saving will keep the original embedded image, so the box should show a
    # single (unchanged) cover instead of a "New Cover Art" / "Original" pair.
    assert box.cover_art.data == box.orig_cover_art.data == [orig]


def test_bigger_cover_still_shown_as_new(no_smaller_settings):
    orig = SizedImage(500, 500)
    new = SizedImage(1000, 1000)
    box = _RemovalBox(_make_item([new], [orig]))
    box.update_metadata()
    assert box.cover_art.data == [new]


def test_smaller_cover_shown_when_option_disabled(no_smaller_settings):
    no_smaller_settings.setting['dont_replace_with_smaller_cover'] = False
    orig = SizedImage(1000, 1000)
    new = SizedImage(500, 500)
    box = _RemovalBox(_make_item([new], [orig]))
    box.update_metadata()
    assert box.cover_art.data == [new]
