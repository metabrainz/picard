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

"""Tests for FileDialog directory history (`history_key`)."""

import os

from PyQt6 import QtWidgets

import pytest

import picard.ui.util as ui_util
from picard.ui.util import (
    FileDialog,
    get_file_dialog_directory,
    set_file_dialog_directory,
)


@pytest.fixture()
def config(monkeypatch):
    import picard.config as cfg_mod

    cfg = cfg_mod.get_config()
    # picard.ui.util imported get_config before the test config was installed
    monkeypatch.setattr(ui_util, 'get_config', lambda: cfg)
    cfg.setting['starting_directory'] = False
    cfg.persist['current_directory'] = ''
    cfg.persist['file_dialog_directories'] = {}
    return cfg


@pytest.fixture()
def start_dir(config, tmp_path):
    """Directory used when nothing is remembered."""
    path = tmp_path / 'start'
    path.mkdir()
    config.persist['current_directory'] = str(path)
    return path


def test_directory_defaults_to_starting_directory(start_dir):
    assert get_file_dialog_directory('some_key') == str(start_dir)


def test_directory_is_remembered_per_key(start_dir, tmp_path):
    logs = tmp_path / 'logs'
    logs.mkdir()
    set_file_dialog_directory('logs', str(logs))
    assert get_file_dialog_directory('logs') == str(logs)
    assert get_file_dialog_directory('other') == str(start_dir)


def test_missing_directory_falls_back_to_closest_existing(start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path / 'gone' / 'deeper'))
    assert get_file_dialog_directory('logs') == str(tmp_path)


def test_remembering_does_not_modify_current_directory(config, start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path))
    assert config.persist['current_directory'] == str(start_dir)


def test_dialog_starts_in_remembered_directory(start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path))
    dialog = FileDialog(history_key='logs')
    assert os.path.samefile(dialog.directory().absolutePath(), tmp_path)


def test_dialog_explicit_directory_wins(start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path))
    dialog = FileDialog(directory=str(start_dir), history_key='logs')
    assert os.path.samefile(dialog.directory().absolutePath(), start_dir)


def test_dialog_without_key_does_not_use_history(start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path))
    dialog = FileDialog()
    assert not os.path.samefile(dialog.directory().absolutePath(), tmp_path)


def test_dialog_remembers_selection_when_accepted(config, start_dir, tmp_path):
    target = tmp_path / 'rips'
    target.mkdir()
    logfile = target / 'album.log'
    logfile.write_text('')
    dialog = FileDialog(history_key='logs')
    dialog.selectFile(str(logfile))
    dialog.done(QtWidgets.QDialog.DialogCode.Accepted)
    assert config.persist['file_dialog_directories'] == {'logs': str(target)}
    assert config.persist['current_directory'] == str(start_dir)


def test_directory_dialog_remembers_parent_of_selected_directory(config, start_dir, tmp_path):
    target = tmp_path / 'album'
    target.mkdir()
    dialog = FileDialog(history_key='dirs')
    dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
    dialog.selectFile(str(target))
    dialog.done(QtWidgets.QDialog.DialogCode.Accepted)
    assert config.persist['file_dialog_directories'] == {'dirs': str(tmp_path)}


def test_directory_dialog_remembers_parent_of_multiple_directories(monkeypatch, config, start_dir, tmp_path):
    first = tmp_path / 'a'
    second = tmp_path / 'b'
    first.mkdir()
    second.mkdir()
    dialog = FileDialog(history_key='dirs')
    dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
    monkeypatch.setattr(dialog, 'selectedFiles', lambda: [str(first), str(second)])
    dialog.done(QtWidgets.QDialog.DialogCode.Accepted)
    assert config.persist['file_dialog_directories'] == {'dirs': str(tmp_path)}


def test_dialog_does_not_remember_when_rejected(config, start_dir, tmp_path):
    dialog = FileDialog(history_key='logs')
    dialog.selectFile(str(tmp_path / 'album.log'))
    dialog.done(QtWidgets.QDialog.DialogCode.Rejected)
    assert config.persist['file_dialog_directories'] == {}


@pytest.mark.parametrize(
    ('method', 'result', 'selected'),
    [
        ('getOpenFileName', ('{p}/a/b.txt', ''), '{p}/a'),
        ('getSaveFileName', ('{p}/a/b.txt', ''), '{p}/a'),
        ('getOpenFileNames', (['{p}/a/b.txt', '{p}/c/d.txt'], ''), '{p}/a'),
        ('getExistingDirectory', '{p}/a/sub', '{p}/a'),
    ],
)
def test_static_methods_remember_selection(monkeypatch, config, start_dir, tmp_path, method, result, selected):
    def fmt(value):
        if isinstance(value, str):
            return value.format(p=tmp_path)
        if isinstance(value, list):
            return [fmt(v) for v in value]
        return tuple(fmt(v) for v in value)

    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs)
        return fmt(result)

    monkeypatch.setattr(QtWidgets.QFileDialog, method, fake)
    getattr(FileDialog, method)(history_key='k')
    assert seen['directory'] == str(start_dir)
    assert config.persist['file_dialog_directories'] == {'k': os.path.normpath(fmt(selected))}


def test_static_method_cancelled_keeps_history(monkeypatch, config, start_dir):
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', lambda *a, **k: ('', ''))
    FileDialog.getOpenFileName(history_key='k')
    assert config.persist['file_dialog_directories'] == {}
