# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from picard.i18n import setup_gettext

import pytest

from picard.ui.coverartbox import CoverArtBox


class _ImgLike:
    def types_as_string(self) -> str:
        return "orig"

    @property
    def data(self) -> bytes:
        return b"\x89PNG\r\n\x1a\nIHDR"  # valid PNG header + chunk id to avoid libpng error

    def __hash__(self) -> int:  # make hashable for pixmap cache key
        return hash(id(self))


class _ImgLikeNew(_ImgLike):
    def types_as_string(self) -> str:
        return "new"


class _DummyThumb:
    def __init__(self) -> None:
        self.data: list[object] | None = None
        self.related_images: list[object] = []
        self.current_pixmap_key: int | None = None
        self._visible: bool = True
        self._tooltip: str = ""

    def setVisible(self, visible: bool) -> None:  # noqa: N802 (Qt-style API)
        self._visible = visible

    def isVisible(self) -> bool:  # noqa: N802
        return self._visible

    def setToolTip(self, text: str) -> None:  # noqa: N802
        self._tooltip = text

    def toolTip(self) -> str:  # noqa: N802
        return self._tooltip


class _DummyLabel:
    def __init__(self) -> None:
        self._text: str = ""
        self._visible: bool = True

    def setText(self, text: str) -> None:  # noqa: N802
        self._text = text

    def text(self) -> str:
        return self._text

    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self._visible = visible

    def isVisible(self) -> bool:  # noqa: N802
        return self._visible


class _DummyButton:
    def __init__(self) -> None:
        self._visible: bool = False

    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self._visible = visible

    def isVisible(self) -> bool:  # noqa: N802
        return self._visible


class CoverArtBoxLite:
    def __init__(self) -> None:
        self.item = None
        self.cover_art_label = _DummyLabel()
        self.cover_art_info_label = _DummyLabel()
        self.orig_cover_art_label = _DummyLabel()
        self.orig_cover_art_info_label = _DummyLabel()
        self.show_details_button = _DummyButton()
        self.cover_art = _DummyThumb()
        self.orig_cover_art = _DummyThumb()
        # Reuse real implementation helpers
        self._first_image_info_lines = CoverArtBox._first_image_info_lines  # type: ignore[assignment]

    def isHidden(self) -> bool:  # noqa: N802
        return False

    def show(self) -> None:
        # No-op for compatibility with widget-based tests
        pass

    def update_display(self, force: bool = False) -> None:
        # Delegate to real implementation using our lightweight attributes
        CoverArtBox.update_display(self, force=force)


@pytest.fixture
def cover_art_box() -> CoverArtBoxLite:
    # Use a lightweight dummy avoiding QPixmap usage for thread safety
    return CoverArtBoxLite()


@pytest.fixture
def lightweight_box() -> type[CoverArtBox]:
    # Use class directly since _first_image_info_lines is now staticmethod
    return CoverArtBox


@pytest.fixture(autouse=True)
def i18n_c_locale() -> None:
    # Ensure deterministic number formatting for bytes2human
    setup_gettext(None, 'C')


@pytest.fixture(autouse=True)
def setup_config() -> None:
    # Ensure config is set up for tests
    from picard.config import get_config

    config = get_config()

    if config is None:
        from unittest.mock import Mock

        import picard.config as config_module

        fake_config = Mock()
        fake_config.setting = {}
        fake_config.persist = {}
        fake_config.profiles = {}
        config_module.config = fake_config
        config = fake_config

    # Set default values for cover art details preferences
    config.setting['show_cover_art_details'] = False
    config.setting['show_cover_art_details_type'] = True
    config.setting['show_cover_art_details_filesize'] = True
    config.setting['show_cover_art_details_dimensions'] = True
    config.setting['show_cover_art_details_mimetype'] = True


@dataclass
class DummyImage:
    types_text: str
    datalength: int
    width: int | None = None
    height: int | None = None
    mimetype: str | None = None

    def types_as_string(self) -> str:
        return self.types_text


def lines_to_text(lines: Iterable[str]) -> str:
    return "\n".join(lines)


@pytest.mark.parametrize(
    ("image", "expected_lines"),
    [
        (
            DummyImage(
                types_text="Front",
                datalength=55300,  # 55.3 kB (54.0 KiB)
                width=500,
                height=500,
                mimetype="image/jpeg",
            ),
            [
                "Front",
                "55.3 kB (54 KiB)",
                "500 x 500",
                "image/jpeg",
            ],
        ),
        (
            DummyImage(
                types_text="Back",
                datalength=1024,
                width=None,
                height=None,
                mimetype="image/png",
            ),
            [
                "Back",
                "1 kB (1 KiB)",
                # no dimensions line
                "image/png",
            ],
        ),
        (
            DummyImage(
                types_text="Other",
                datalength=1000,
                width=100,
                height=200,
                mimetype="",
            ),
            [
                "Other",
                "1 kB (1000 B)",
                "100 x 200",
                # no mime line
            ],
        ),
    ],
)
def test_first_image_info_lines_formatting(
    lightweight_box: type[CoverArtBox], image: DummyImage, expected_lines: list[str]
) -> None:
    lines = lightweight_box._first_image_info_lines([image])
    # Remove empty lines possibly produced by missing data
    lines = [line for line in lines if line]
    assert lines == expected_lines


def test_first_image_info_lines_uses_only_first(lightweight_box: type[CoverArtBox]) -> None:
    img1 = DummyImage("Front", 2000, 10, 10, "image/gif")
    img2 = DummyImage("Back", 3000, 20, 20, "image/png")
    lines = lightweight_box._first_image_info_lines([img1, img2])
    assert lines[0] == "Front"
    assert "gif" in lines[-1]
    # Ensure second image has no effect
    assert all("Back" not in part for part in lines)


def test_update_display_sets_labels_and_tooltips_single(cover_art_box: CoverArtBox) -> None:
    img = DummyImage("Front", 55300, 500, 500, "image/jpeg")
    cover_art_box.cover_art.related_images = [img]
    cover_art_box.orig_cover_art.related_images = []

    cover_art_box.show()
    cover_art_box.update_display(force=True)

    expected_lines = [
        "Front",
        "55.3 kB (54 KiB)",
        "500 x 500",
        "image/jpeg",
    ]
    # When details display is disabled by default, labels are empty but tooltips still show details
    assert cover_art_box.cover_art_info_label.text() == ""
    assert cover_art_box.cover_art.toolTip() == "<br/>".join(expected_lines)
    # Only new cover is shown → header cleared, original info hidden
    assert cover_art_box.cover_art_label.text() == ""
    assert not cover_art_box.orig_cover_art_info_label.isVisible()


def test_update_display_both_visible_headers_and_info(cover_art_box: CoverArtBox) -> None:
    img_new = DummyImage("Front", 2000, 10, 10, "image/png")
    img_orig = DummyImage("Back", 3000, 20, 20, "image/jpeg")

    cover_art_box.cover_art.related_images = [img_new]
    cover_art_box.orig_cover_art.related_images = [img_orig]
    # Mark both thumbnails as having list-like data with minimal image-like objects
    # Ensure len(data) > 0 and make thumbnails not equal by setting different keys
    cover_art_box.cover_art.data = [_ImgLikeNew()]
    cover_art_box.orig_cover_art.data = [_ImgLike()]
    cover_art_box.cover_art.current_pixmap_key = 1
    cover_art_box.orig_cover_art.current_pixmap_key = 2

    cover_art_box.show()
    cover_art_box.update_display(force=True)

    assert cover_art_box.cover_art_label.text() == "New Cover Art"
    assert cover_art_box.orig_cover_art_label.text() == "Original Cover Art"
    # Details labels are hidden by default when show_cover_art_details is False
    assert not cover_art_box.orig_cover_art_info_label.isVisible()
    assert cover_art_box.cover_art_info_label.text() == ""
    assert cover_art_box.orig_cover_art_info_label.text() == ""
