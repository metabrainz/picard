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
from picard.ui.util import set_file_dialog_directory


@pytest.fixture()
def make_dialog(qapp, monkeypatch):
    monkeypatch.setattr(picard.ui, 'tagger_instance', MagicMock())
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
    set_file_dialog_directory('plugin_directory', str(plugin_dir))
    dialog = make_dialog()
    assert dialog.path_edit.text() == ''


@pytest.mark.parametrize(
    ('typed', 'expected'),
    [
        ('', 'remembered'),
        ('{plugin}', 'typed'),
        ('{plugin}/MANIFEST.toml', 'remembered'),
        ('{tmp}/missing', 'remembered'),
    ],
)
def test_browse_start_directory(config, make_dialog, monkeypatch, plugin_dir, tmp_path, typed, expected):
    """Browsing starts at the typed path if it is a directory, else at the remembered directory."""
    set_file_dialog_directory('plugin_directory', str(tmp_path))
    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs)
        return ''

    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory', fake)
    dialog = make_dialog()
    dialog.path_edit.setText(typed.format(plugin=plugin_dir, tmp=tmp_path))
    dialog._browse_directory()
    assert seen['directory'] == str(plugin_dir if expected == 'typed' else tmp_path)


def test_browse_remembers_selected_directory(config, make_dialog, monkeypatch, plugin_dir):
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory', lambda *a, **k: str(plugin_dir))
    dialog = make_dialog()
    dialog._browse_directory()
    assert dialog.path_edit.text() == str(plugin_dir)
    assert config.persist['file_dialog_directories'] == {'plugin_directory': str(plugin_dir.parent)}
