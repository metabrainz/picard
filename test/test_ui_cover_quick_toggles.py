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


"""Focused tests for cover art quick toggles in Options menu.

Covers only the newly added actions and handlers.
"""

from collections.abc import Callable, Iterator
from unittest.mock import patch

from PyQt6 import QtCore, QtGui

from test.picardtestcase import PicardTestCase

from picard.config import get_config

import pytest

from picard.ui.mainwindow.actions import (
    _create_enable_save_images_to_files_action,
    _create_enable_save_images_to_tags_action,
)


class _DummyParent(QtCore.QObject):
    def __init__(self, set_to_config_key: str | None = None) -> None:
        super().__init__()
        self.invoked_with: bool | None = None
        self._config_key = set_to_config_key

    def toggle_save_images_to_tags(self, checked: bool) -> None:
        self.invoked_with = checked
        if self._config_key:
            get_config().setting[self._config_key] = checked

    def toggle_save_images_to_files(self, checked: bool) -> None:
        self.invoked_with = checked
        if self._config_key:
            get_config().setting[self._config_key] = checked


class _FakeSignal:
    def __init__(self) -> None:
        self._slot: Callable[[bool], None] | None = None

    def connect(self, slot: Callable[[bool], None]) -> None:
        self._slot = slot


class _FakeAction:
    def __init__(self, _text: str, _parent: QtCore.QObject) -> None:
        self._checkable = False
        self._checked = False
        self.triggered = _FakeSignal()

    def setCheckable(self, value: bool) -> None:
        self._checkable = value

    def setChecked(self, value: bool) -> None:
        self._checked = value

    def isCheckable(self) -> bool:
        return self._checkable

    def isChecked(self) -> bool:
        return self._checked

    def trigger(self) -> None:
        if self.triggered._slot:
            self.triggered._slot(self._checked)


@pytest.fixture
def patch_qaction() -> Iterator[None]:
    p = patch('picard.ui.mainwindow.actions.QtGui.QAction', new=_FakeAction)
    p.start()
    try:
        yield None
    finally:
        p.stop()


@pytest.fixture
def setup_config() -> None:
    PicardTestCase.init_config()


@pytest.mark.parametrize(
    ('create_fn', 'key'),
    [
        (_create_enable_save_images_to_tags_action, "save_images_to_tags"),
        (_create_enable_save_images_to_files_action, "save_images_to_files"),
    ],
)
@pytest.mark.parametrize("initial", [False, True])
def test_action_toggle(
    create_fn: Callable[[QtCore.QObject], QtGui.QAction],
    key: str,
    initial: bool,
    patch_qaction: None,
    setup_config: None,
) -> None:
    get_config().setting[key] = initial
    parent = _DummyParent(set_to_config_key=key)

    action = create_fn(parent)

    assert action.isCheckable()
    assert action.isChecked() is initial

    action.setChecked(not initial)
    action.trigger()

    assert parent.invoked_with is (not initial)
    assert get_config().setting[key] is (not initial)


@pytest.mark.parametrize(
    ('method_name', 'key', 'value'),
    [
        ("toggle_save_images_to_tags", "save_images_to_tags", False),
        ("toggle_save_images_to_tags", "save_images_to_tags", True),
        ("toggle_save_images_to_files", "save_images_to_files", False),
        ("toggle_save_images_to_files", "save_images_to_files", True),
    ],
)
def test_toggle_updates_config(method_name: str, key: str, value: bool, setup_config: None) -> None:
    from picard.ui.mainwindow.__init__ import MainWindow as _MW

    # Methods don't use instance state; pass a dummy self
    getattr(_MW, method_name)(object(), value)
    assert get_config().setting[key] is value
