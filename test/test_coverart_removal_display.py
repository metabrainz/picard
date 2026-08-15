# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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

"""Tests for consistent display of cover art marked for removal from tags."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt6 import (
    QtCore,
    QtGui,
)

from picard.config import get_config
from picard.util.imagelist import ImageList
from picard.util.lrucache import LRUCache

import pytest

from picard.ui.coverartbox import CoverArtBox
from picard.ui.infodialog.dialog import ArtworkRow


def _png_bytes() -> bytes:
    image = QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor('blue'))
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, 'PNG')
    buffer.close()
    return bytes(data)


class FakeImage:
    external_file_coverart = None
    width = 100
    height = 100

    def __init__(self, data: bytes = b'') -> None:
        self._data = data

    @property
    def data(self) -> bytes:
        return self._data

    def types_as_string(self) -> str:
        return "front"

    def is_front_image(self) -> bool:
        return True

    def normalized_types(self) -> tuple[str, ...]:
        return ('front',)


# --- ArtworkRow "New Exported" fallback -------------------------------------


def test_artwork_row_uses_external_file_coverart() -> None:
    image = FakeImage()
    external = FakeImage()
    image.external_file_coverart = external
    row = ArtworkRow(new_image=image)
    assert row.new_external_image is external


def test_artwork_row_no_fallback_by_default() -> None:
    row = ArtworkRow(new_image=FakeImage())
    assert row.new_external_image is None


def test_artwork_row_falls_back_to_image_when_removal_predicted() -> None:
    image = FakeImage()
    row = ArtworkRow(new_image=image, external_fallback=True)
    assert row.new_external_image is image


def test_artwork_row_prefers_external_over_fallback() -> None:
    image = FakeImage()
    external = FakeImage()
    image.external_file_coverart = external
    row = ArtworkRow(new_image=image, external_fallback=True)
    assert row.new_external_image is external


def test_artwork_row_falls_back_to_orig_image_when_no_new_image() -> None:
    """When no new replacement was fetched, the originally tagged image
    itself is what gets exported to a file instead of being lost."""
    orig_image = FakeImage()
    row = ArtworkRow(orig_image=orig_image, new_image=None, external_fallback=True)
    assert row.new_external_image is orig_image


def test_artwork_row_no_orig_fallback_without_removal_predicted() -> None:
    orig_image = FakeImage()
    row = ArtworkRow(orig_image=orig_image, new_image=None, external_fallback=False)
    assert row.new_external_image is None


# --- CoverArtThumbnail removal overlay ---------------------------------------


@pytest.fixture
def thumbnail(qapp, monkeypatch):
    from PyQt6 import QtWidgets

    mock_tagger = MagicMock()
    mock_tagger.primaryScreen.return_value.devicePixelRatio.return_value = 1.0
    monkeypatch.setattr(
        'picard.ui.coverartbox.coverartthumbnail.tagger_instance',
        lambda: mock_tagger,
    )
    from picard.ui.coverartbox.coverartthumbnail import CoverArtThumbnail

    parent = QtWidgets.QWidget()
    thumb = CoverArtThumbnail(pixmap_cache=LRUCache(10), parent=parent)
    yield thumb
    parent.deleteLater()


def test_thumbnail_removal_overlay_changes_pixmap(thumbnail) -> None:
    image = FakeImage(_png_bytes())
    thumbnail.set_data([image], force=True)
    unmarked = thumbnail.pixmap().toImage()
    key = thumbnail.current_pixmap_key

    thumbnail.set_marked_for_removal(True)
    marked = thumbnail.pixmap().toImage()
    assert marked != unmarked
    # Marking must not change image identity used to compare thumbnails
    assert thumbnail.current_pixmap_key == key

    thumbnail.set_marked_for_removal(False)
    assert thumbnail.pixmap().toImage() == unmarked


def test_thumbnail_removal_overlay_kept_on_new_data(thumbnail) -> None:
    thumbnail.set_marked_for_removal(True)
    image = FakeImage(_png_bytes())
    thumbnail.set_data([image], force=True)
    marked = thumbnail.pixmap().toImage()

    thumbnail.set_marked_for_removal(False)
    assert thumbnail.pixmap().toImage() != marked


# --- CoverArtBox marking logic -----------------------------------------------


class _RemovalThumb:
    def __init__(self) -> None:
        self.data: list[object] | None = None
        self.marked_for_removal = False
        self.related_images: list[object] = []

    def set_metadata(self, metadata) -> None:
        if metadata is not None and metadata.images:
            self.data = list(metadata.images)
        else:
            self.data = None

    def set_marked_for_removal(self, marked_for_removal) -> None:
        self.marked_for_removal = bool(marked_for_removal)

    def __eq__(self, other) -> bool:
        return self.data == other.data


class _RemovalBox:
    _REMOVAL_SETTINGS = CoverArtBox._REMOVAL_SETTINGS
    update_metadata = CoverArtBox.update_metadata

    def __init__(self, item) -> None:
        self.item = item
        self.cover_art = _RemovalThumb()
        self.orig_cover_art = _RemovalThumb()
        self._exported_images = None

    def update_display(self, force: bool = False) -> None:
        pass


def _make_item(new_images: list[object], orig_images: list[object]):
    return SimpleNamespace(
        metadata=SimpleNamespace(images=ImageList(new_images)),
        orig_metadata=SimpleNamespace(images=ImageList(orig_images)),
    )


@pytest.fixture
def removal_settings():
    config = get_config()
    config.setting['save_images_to_files'] = True
    config.setting['remove_images_from_tags'] = True
    config.setting['save_images_to_tags'] = False
    config.setting['embed_only_one_front_image'] = False
    return config


def test_update_metadata_marks_single_view(removal_settings) -> None:
    image = FakeImage()
    box = _RemovalBox(_make_item([image], [image]))
    box.update_metadata()
    assert box._removal_predicted
    assert box.orig_cover_art.marked_for_removal
    # The exported copy is shown as its own unmarked panel, even though its
    # data is identical to the original tagged image
    assert not box.cover_art.marked_for_removal


def test_update_metadata_marks_only_orig_when_images_differ(removal_settings) -> None:
    box = _RemovalBox(_make_item([FakeImage()], [FakeImage()]))
    box.update_metadata()
    assert box._removal_predicted
    assert box.orig_cover_art.marked_for_removal
    assert not box.cover_art.marked_for_removal


def test_update_metadata_unmarks_when_removal_disabled(removal_settings) -> None:
    image = FakeImage()
    box = _RemovalBox(_make_item([image], [image]))
    box.update_metadata()
    assert box.orig_cover_art.marked_for_removal

    # Regression: stale marking must be cleared when prediction no longer holds
    removal_settings.setting['remove_images_from_tags'] = False
    box.update_metadata()
    assert not box._removal_predicted
    assert not box.cover_art.marked_for_removal
    assert not box.orig_cover_art.marked_for_removal


def test_update_metadata_no_removal_without_orig_images(removal_settings) -> None:
    box = _RemovalBox(_make_item([FakeImage()], []))
    box.update_metadata()
    assert not box._removal_predicted
    assert not box.cover_art.marked_for_removal


def test_update_metadata_keeps_showing_exported_image_after_save(removal_settings) -> None:
    """Once a save has cleared orig_metadata.images (see File._saving_finished),
    cover_art must keep showing the image that was exported instead of falling
    back to nothing, since neither metadata nor orig_metadata reference it
    anymore."""
    image = FakeImage()
    box = _RemovalBox(_make_item([], [image]))
    box.update_metadata()
    assert box._removal_predicted
    assert box.cover_art.data == [image]

    # Simulate the save completing: orig_metadata.images is now empty too.
    box.item = _make_item([], [])
    box.update_metadata()
    assert not box._removal_predicted
    assert box.cover_art.data == [image]
    assert box.orig_cover_art.data is None


def test_setting_changed_triggers_update_metadata(removal_settings, monkeypatch) -> None:
    """Changing remove_images_from_tags via the config signal must trigger
    update_metadata so the cover art box refreshes without re-selecting."""
    config = get_config()
    image = FakeImage()
    box = _RemovalBox(_make_item([image], [image]))
    box.update_metadata()
    assert box._removal_predicted

    # Simulate the signal path: connect _on_setting_changed and fire it
    from picard.ui.coverartbox import CoverArtBox

    call_log = []
    original_update = box.update_metadata

    def tracking_update():
        call_log.append('update_metadata')
        original_update()

    box.update_metadata = tracking_update
    on_setting_changed = CoverArtBox._on_setting_changed.__get__(box, type(box))

    # Disabling the option should trigger an update
    config.setting['remove_images_from_tags'] = False
    on_setting_changed('remove_images_from_tags', True, False)
    assert 'update_metadata' in call_log
    assert not box._removal_predicted

    # An unrelated setting should not trigger an update
    call_log.clear()
    on_setting_changed('some_other_setting', None, None)
    assert call_log == []
