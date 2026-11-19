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

"""Directory selection in the Local tab of the plugin install dialog."""

from unittest.mock import MagicMock

from PyQt6 import QtWidgets

import pytest

import picard.ui
from picard.ui.dialogs.installplugin import InstallPluginDialog
import picard.ui.util as ui_util
from picard.ui.util import (
    FileDialogHistoryKey,
    set_file_dialog_directory,
)


@pytest.fixture()
def config(monkeypatch):
    import picard.config as cfg_mod

    cfg = cfg_mod.get_config()
    # picard.ui.util imported get_config before the test config was installed
    monkeypatch.setattr(ui_util, 'get_config', lambda: cfg)
    cfg.setting['starting_directory'] = False
    cfg.persist['file_dialog_directories'] = {}
    return cfg


@pytest.fixture()
def make_dialog(qapp, monkeypatch):
    monkeypatch.setattr(picard.ui, 'tagger_instance', MagicMock)
    dialogs = []

    def make():
        dialog = InstallPluginDialog()
        dialogs.append(dialog)
        return dialog

    yield make
    for dialog in dialogs:
        dialog.deleteLater()


@pytest.fixture()
def plugin_dir(tmp_path):
    path = tmp_path / 'myplugin'
    path.mkdir()
    (path / 'MANIFEST.toml').write_text('')
    return path


def test_path_is_not_prefilled_from_history(config, make_dialog, plugin_dir):
    set_file_dialog_directory(FileDialogHistoryKey.PLUGIN_DIRECTORY, str(plugin_dir))
    dialog = make_dialog()
    assert dialog.path_edit.text() == ''


def test_browse_starts_in_remembered_directory_when_path_is_empty(config, make_dialog, monkeypatch, tmp_path):
    set_file_dialog_directory(FileDialogHistoryKey.PLUGIN_DIRECTORY, str(tmp_path))
    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs)
        return ''

    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory', fake)
    dialog = make_dialog()
    dialog._browse_directory()
    assert seen['directory'] == str(tmp_path)


def test_browse_starts_in_path_field(config, make_dialog, monkeypatch, plugin_dir, tmp_path):
    set_file_dialog_directory(FileDialogHistoryKey.PLUGIN_DIRECTORY, str(tmp_path))
    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs)
        return ''

    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory', fake)
    dialog = make_dialog()
    dialog.path_edit.setText(str(plugin_dir))
    dialog._browse_directory()
    assert seen['directory'] == str(plugin_dir)


def test_browse_remembers_selected_directory(config, make_dialog, monkeypatch, plugin_dir):
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory', lambda *a, **k: str(plugin_dir))
    dialog = make_dialog()
    dialog._browse_directory()
    assert dialog.path_edit.text() == str(plugin_dir)
    assert config.persist['file_dialog_directories'] == {'plugin_directory': str(plugin_dir.parent)}
