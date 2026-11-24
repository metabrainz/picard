# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard import config as picard_config

import pytest

import picard.ui.dialogs.donotshowagainmessagebox as dnsa
from picard.ui.dialogs.installconfirm import PLUGIN_TRUST_WARNING
from picard.ui.dialogs.pluginnotes import PluginNotesDialog


@pytest.fixture(autouse=True)
def fake_config(monkeypatch, qapp):
    """Make the module use the fake config installed by conftest.py (also provides QApplication)."""
    monkeypatch.setattr(dnsa, 'get_config', lambda: picard_config.config)


def test_dialog_content_and_hiding():
    dialog = PluginNotesDialog(None)

    assert dialog.icon() == QtWidgets.QMessageBox.Icon.Warning
    assert dialog.text().count('<p>') == 3
    assert dialog.text().endswith(f'<strong>{PLUGIN_TRUST_WARNING}</strong></p>')

    assert not PluginNotesDialog.is_hidden()
    dialog._checkbox.setChecked(True)
    assert PluginNotesDialog.is_hidden()


@pytest.mark.parametrize('direction', [QtCore.Qt.LayoutDirection.LeftToRight, QtCore.Qt.LayoutDirection.RightToLeft])
def test_dialog_follows_application_layout_direction(qapp, direction):
    qapp.setLayoutDirection(direction)
    try:
        assert PluginNotesDialog(None).layoutDirection() == direction
    finally:
        qapp.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
