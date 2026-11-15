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

"""Start directory of the Add Files and Add Folder dialogs."""

from unittest.mock import MagicMock

from PyQt6 import (
    QtCore,
    QtWidgets,
)

import pytest

import picard.ui.mainwindow as mainwindow_mod
from picard.ui.mainwindow import MainWindow
from picard.ui.util import set_file_dialog_directory


@pytest.fixture()
def home(monkeypatch, config, tmp_path):
    # picard.ui.mainwindow imported get_config before the test config was installed
    monkeypatch.setattr(mainwindow_mod, 'get_config', lambda: config)
    config.setting['allow_multi_dirs_selection'] = False
    path = tmp_path / 'home'
    path.mkdir()
    monkeypatch.setattr(QtCore.QDir, 'homePath', staticmethod(lambda: str(path)))
    return path


@pytest.fixture()
def remembered(tmp_path):
    path = tmp_path / 'remembered'
    path.mkdir()
    set_file_dialog_directory('add_files', str(path))
    set_file_dialog_directory('add_directory', str(path))
    return path


@pytest.fixture()
def fixed(config, tmp_path):
    path = tmp_path / 'fixed'
    path.mkdir()
    config.setting['starting_directory'] = True
    config.setting['starting_directory_path'] = str(path)
    return path


def open_dialog(monkeypatch, action):
    """Run the Add Files or Add Folder action, return the directory its dialog starts in."""
    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs)
        return ([], '') if action == 'add_files' else ''

    method = 'getOpenFileNames' if action == 'add_files' else 'getExistingDirectory'
    monkeypatch.setattr(QtWidgets.QFileDialog, method, fake)
    window = MagicMock()
    window.tagger.format_registry.supported_formats.return_value = []
    getattr(MainWindow, action)(window)
    return seen['directory']


@pytest.mark.parametrize('action', ['add_files', 'add_directory'])
def test_starts_in_home_directory_first(monkeypatch, home, action):
    assert open_dialog(monkeypatch, action) == str(home)


@pytest.mark.parametrize('action', ['add_files', 'add_directory'])
def test_starts_in_remembered_directory(monkeypatch, home, remembered, action):
    assert open_dialog(monkeypatch, action) == str(remembered)


@pytest.mark.parametrize('action', ['add_files', 'add_directory'])
def test_fixed_starting_directory_wins_over_history(monkeypatch, home, remembered, fixed, action):
    assert open_dialog(monkeypatch, action) == str(fixed)
