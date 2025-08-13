# -*- coding: utf-8 -*-

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import os
from typing import Iterator, cast
from unittest.mock import Mock

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication

from picard.config import (
    Option,
    get_config,
)

import pytest

from picard.ui.coverartbox import CoverArtBox


@pytest.fixture(scope="session", autouse=True)
def qapplication() -> QApplication:
    os.environ.setdefault('QT_QPA_PLATFORM', "offscreen")
    app = QApplication.instance() or QApplication([])

    # Install a minimal QCoreApplication.instance compatible object for tests
    class _FakeTagger(QtCore.QObject):
        def primaryScreen(self):  # noqa: N802
            class _Screen:
                @staticmethod
                def devicePixelRatio() -> float:  # pragma: no cover - constant
                    return 1.0

            return _Screen()

    QtCore.QCoreApplication.instance = lambda: _FakeTagger()  # type: ignore[assignment]

    # Initialize a fake global config for tests
    from picard import config as config_mod

    fake_config = Mock()
    fake_config.setting = {}
    fake_config.persist = {}
    fake_config.profiles = {}
    config_mod.config = fake_config
    config_mod.setting = fake_config.setting
    config_mod.persist = fake_config.persist
    config_mod.profiles = fake_config.profiles

    # Ensure options are registered
    # Populate default values for all registered 'setting' options
    from picard.config import Option as _Option
    import picard.options  # noqa: F401

    for (section, name), opt in list(_Option.registry.items()):
        if section == "setting":
            fake_config.setting.setdefault(name, opt.default)

    return cast(QApplication, app)


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


class _DummyThumb:
    def __init__(self) -> None:
        self.data: list[object] | None = None
        self.related_images: list[DummyImage] = []
        self.current_pixmap_key: int | None = None
        self._visible: bool = True
        self._tooltip: str = ""

    def setVisible(self, visible: bool) -> None:  # noqa: N802
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
        # Bind helpers from real implementation
        self._first_image_info_lines = CoverArtBox._first_image_info_lines  # type: ignore[assignment]
        self._filter_info_lines = CoverArtBox._filter_info_lines  # type: ignore[assignment]

    def isHidden(self) -> bool:  # noqa: N802
        return False

    def update_display(self, force: bool = False) -> None:
        CoverArtBox.update_display(self, force=force)


@pytest.fixture
def box() -> CoverArtBoxLite:
    return CoverArtBoxLite()


def test_option_default() -> None:
    opt = Option.get('setting', "show_cover_art_details")
    assert opt is not None
    assert opt.default is False


@pytest.mark.skip(reason="This test fails if ran in parallel")
def test_options_page_load_and_save() -> None:
    from picard.ui.options.cover import CoverOptionsPage

    page = CoverOptionsPage()
    page.load()
    config = get_config()
    # Default is False
    assert config.setting['show_cover_art_details'] is False
    assert page.ui.cb_show_cover_art_details.isChecked() is False

    # Toggle on and save
    page.ui.cb_show_cover_art_details.setChecked(True)
    page.save()
    assert config.setting['show_cover_art_details'] is True


@pytest.mark.parametrize("show_details", [False, True])
def test_coverartbox_label_toggle_and_tooltip_always_on(box: CoverArtBoxLite, show_details: bool) -> None:
    # Configure option toggle
    config = get_config()
    config.setting['show_cover_art_details'] = show_details

    # Provide one image on the new/current thumbnail
    img = DummyImage("Front", 55300, 500, 500, "image/jpeg")
    box.cover_art.related_images = [img]
    box.orig_cover_art.related_images = []

    box.update_display(force=True)

    expected_lines = [
        "Front",
        "55.3 kB (54 KiB)",
        "500 x 500",
        "image/jpeg",
    ]
    # Tooltip must always include details
    assert box.cover_art.toolTip() == "<br/>".join(expected_lines)

    # Label content depends on toggle
    if show_details:
        assert box.cover_art_info_label.text() == lines_to_text(expected_lines)
    else:
        assert box.cover_art_info_label.text() == ""


# --- New tests for child options and UI wiring ---


@pytest.fixture
def _restore_cover_details_options() -> Iterator[None]:
    """Restore details-related options after each test to avoid cross-test leakage."""
    config = get_config()
    keys = [
        "show_cover_art_details",
        "show_cover_art_details_type",
        "show_cover_art_details_filesize",
        "show_cover_art_details_dimensions",
        "show_cover_art_details_mimetype",
    ]
    backup: dict[str, object] = {k: config.setting.get(k) for k in keys}
    try:
        yield
    finally:
        for k, v in backup.items():
            config.setting[k] = v


def test_child_option_defaults() -> None:
    assert Option.get('setting', "show_cover_art_details_type").default is True
    assert Option.get('setting', "show_cover_art_details_filesize").default is True
    assert Option.get('setting', "show_cover_art_details_dimensions").default is True
    assert Option.get('setting', "show_cover_art_details_mimetype").default is True


def _set_details_config(
    *,
    parent: bool,
    type_on: bool,
    size_on: bool,
    dims_on: bool,
    mime_on: bool,
) -> None:
    config = get_config()
    config.setting['show_cover_art_details'] = parent
    config.setting['show_cover_art_details_type'] = type_on
    config.setting['show_cover_art_details_filesize'] = size_on
    config.setting['show_cover_art_details_dimensions'] = dims_on
    config.setting['show_cover_art_details_mimetype'] = mime_on


@pytest.mark.skip(reason="This test fails if ran in parallel")
def test_options_page_children_enable_disable_and_save(_restore_cover_details_options: None) -> None:
    from picard.ui.options.cover import CoverOptionsPage

    # Ensure parent starts unchecked for this test
    get_config().setting['show_cover_art_details'] = False

    page = CoverOptionsPage()
    page.load()
    # Initially parent unchecked, children should be disabled (greyed out)
    assert page.ui.cb_show_cover_art_details.isChecked() is False
    for child in (
        page.ui.cb_show_cover_art_details_type,
        page.ui.cb_show_cover_art_details_filesize,
        page.ui.cb_show_cover_art_details_dimensions,
        page.ui.cb_show_cover_art_details_mimetype,
    ):
        assert isinstance(child, QtWidgets.QCheckBox)
        assert child.isEnabled() is False

    # Toggle parent, children become enabled
    page.ui.cb_show_cover_art_details.setChecked(True)
    for child in (
        page.ui.cb_show_cover_art_details_type,
        page.ui.cb_show_cover_art_details_filesize,
        page.ui.cb_show_cover_art_details_dimensions,
        page.ui.cb_show_cover_art_details_mimetype,
    ):
        assert child.isEnabled() is True

    # Change children and save
    page.ui.cb_show_cover_art_details_type.setChecked(False)
    page.ui.cb_show_cover_art_details_mimetype.setChecked(False)
    page.save()

    config = get_config()
    assert config.setting['show_cover_art_details'] is True
    assert config.setting['show_cover_art_details_type'] is False
    assert config.setting['show_cover_art_details_filesize'] is True
    assert config.setting['show_cover_art_details_dimensions'] is True
    assert config.setting['show_cover_art_details_mimetype'] is False


@pytest.mark.parametrize(
    "type_on,size_on,dims_on,mime_on,expected",
    [
        (True, True, True, True, ["Front", "55.3 kB (54 KiB)", "500 x 500", "image/jpeg"]),
        (False, True, True, True, ["55.3 kB (54 KiB)", "500 x 500", "image/jpeg"]),
        (True, False, True, True, ["Front", "500 x 500", "image/jpeg"]),
        (True, True, False, True, ["Front", "55.3 kB (54 KiB)", "image/jpeg"]),
        (True, True, True, False, ["Front", "55.3 kB (54 KiB)", "500 x 500"]),
        (False, False, False, False, []),
    ],
)
def test_coverartbox_child_filtering(
    box: CoverArtBoxLite,
    _restore_cover_details_options: None,
    type_on: bool,
    size_on: bool,
    dims_on: bool,
    mime_on: bool,
    expected: list[str],
) -> None:
    # Configure options
    _set_details_config(parent=True, type_on=type_on, size_on=size_on, dims_on=dims_on, mime_on=mime_on)

    # Provide one image on the new/current thumbnail
    img = DummyImage("Front", 55300, 500, 500, "image/jpeg")
    box.cover_art.related_images = [img]
    box.orig_cover_art.related_images = []

    # Update and assert
    box.update_display(force=True)
    assert box.cover_art_info_label.text() == lines_to_text(expected)
    # Tooltip remains full
    full = ["Front", "55.3 kB (54 KiB)", "500 x 500", "image/jpeg"]
    assert box.cover_art.toolTip() == "<br/>".join(full)


def test_coverartbox_missing_dimensions_mimetype(box: CoverArtBoxLite, _restore_cover_details_options: None) -> None:
    # Enable all
    _set_details_config(parent=True, type_on=True, size_on=True, dims_on=True, mime_on=True)
    # Missing dims and mimetype
    img = DummyImage("Front", 55300, None, None, None)
    box.cover_art.related_images = [img]
    box.orig_cover_art.related_images = []

    box.update_display(force=True)
    # Expected only type + size lines
    assert box.cover_art_info_label.text() == lines_to_text(["Front", "55.3 kB (54 KiB)"])
