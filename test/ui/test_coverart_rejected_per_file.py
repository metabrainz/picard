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


"""PICARD-3531: the "never replace" filters run on each file against its own
embedded images, so an item made of several files (album, cluster, multiple
selection) must not be judged on the union of their images."""

from unittest.mock import MagicMock

from test.picardtestcase import create_image
from test.ui.test_coverart_removal_display import _RemovalBox

from picard.cluster import TempItemList
from picard.config import get_config
from picard.file import File

import pytest

from picard.ui.coverartbox import CoverArtBox


def _front(name, size):
    image = create_image(name, types=['front'], support_types=True, url='file://' + name.decode())
    image.width = image.height = size
    return image


def _file(name, orig, new):
    file = File('/tmp/%s.flac' % name)
    if orig is not None:
        file.orig_metadata.images.append(orig)
    file.metadata.images.append(new)
    return file


@pytest.fixture
def settings(patch_tagger_instance):
    patch_tagger_instance('picard.item')
    config = get_config()
    config.setting['save_images_to_tags'] = True
    config.setting['save_images_to_files'] = False
    config.setting['remove_images_from_tags'] = False
    config.setting['embed_only_one_front_image'] = False
    config.setting['dont_replace_with_smaller_cover'] = True
    config.setting['dont_replace_cover_of_types'] = False
    return config


def _shown(item):
    box = _RemovalBox(item)
    box.update_metadata()
    return box.cover_art.data


def test_single_file_rejecting_shows_original(settings):
    big, new = _front(b'big', 1000), _front(b'new', 800)
    item = TempItemList(items=[_file('a', big, new)])
    assert _shown(item) == [big]


def test_files_all_rejecting_show_originals(settings):
    big, new = _front(b'big', 1000), _front(b'new', 800)
    item = TempItemList(items=[_file('a', big, new), _file('b', big, new)])
    assert _shown(item) == [big]


def test_one_file_accepting_shows_new_image(settings):
    big, small, new = _front(b'big', 1000), _front(b'small', 500), _front(b'new', 800)
    # Saving keeps the original of the first file, replaces the one of the second.
    item = TempItemList(items=[_file('a', big, new), _file('b', small, new)])
    assert _shown(item) == [new]


def test_file_without_embedded_art_accepts_new_image(settings):
    big, new = _front(b'big', 1000), _front(b'new', 800)
    item = TempItemList(items=[_file('a', big, new), _file('b', None, new)])
    assert _shown(item) == [new]


def test_file_without_pending_change_is_ignored(settings):
    big, new = _front(b'big', 1000), _front(b'new', 800)
    unchanged = _file('c', big, big)
    item = TempItemList(items=[_file('a', big, new), unchanged])
    assert _shown(item) == [big]


@pytest.fixture
def real_box(settings, patch_tagger_instance):
    """A real CoverArtBox, to check what the user actually sees."""
    patch_tagger_instance('picard.ui.coverartbox', 'picard.ui.coverartbox.coverartthumbnail')
    settings.setting.setting_changed = MagicMock()
    box = CoverArtBox()
    box.show()
    return box


def test_displayed_state_when_rejected(real_box):
    """The reporter's case: no "New Cover Art" header, no second panel."""
    big, new = _front(b'big', 1000), _front(b'new', 800)
    real_box.set_item(TempItemList(items=[_file('a', big, new)]))
    assert real_box.cover_art_label.text() == ''
    assert not real_box.orig_cover_art.isVisible()


def test_displayed_state_when_one_file_is_replaced(real_box):
    big, small, new = _front(b'big', 1000), _front(b'small', 500), _front(b'new', 800)
    real_box.set_item(TempItemList(items=[_file('a', big, new), _file('b', small, new)]))
    assert real_box.cover_art_label.text() == 'New Cover Art'
    assert real_box.orig_cover_art.isVisible()
