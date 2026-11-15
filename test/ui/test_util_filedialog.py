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

from PyQt6 import (
    QtCore,
    QtWidgets,
)

import pytest

from picard.ui.util import (
    FileDialog,
    get_file_dialog_directory,
    set_file_dialog_directory,
)


@pytest.fixture()
def start_dir(monkeypatch, config, tmp_path):
    """The home directory, used by `find_starting_directory()` by default."""
    path = tmp_path / 'start'
    path.mkdir()
    monkeypatch.setattr(QtCore.QDir, 'homePath', staticmethod(lambda: str(path)))
    return path


def test_directory_defaults_to_default_directory(start_dir):
    assert get_file_dialog_directory('some_key') == ''
    assert get_file_dialog_directory('some_key', default_directory=str(start_dir)) == str(start_dir)


def test_directory_is_remembered_per_key(start_dir, tmp_path):
    logs = tmp_path / 'logs'
    logs.mkdir()
    set_file_dialog_directory('logs', str(logs))
    assert get_file_dialog_directory('logs') == str(logs)
    assert get_file_dialog_directory('other') == ''


def test_missing_directory_falls_back_to_closest_existing(start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path / 'gone' / 'deeper'))
    assert get_file_dialog_directory('logs') == str(tmp_path)


def test_fixed_starting_directory_does_not_override_history(config, start_dir, tmp_path):
    fixed = tmp_path / 'fixed'
    fixed.mkdir()
    config.setting['starting_directory'] = True
    config.setting['starting_directory_path'] = str(fixed)
    set_file_dialog_directory('logs', str(tmp_path))
    assert get_file_dialog_directory('logs') == str(tmp_path)


@pytest.mark.parametrize(
    ('directory', 'history_key', 'remembered', 'expected'),
    [
        ('/explicit', 'k', True, '/explicit'),
        ('', 'k', True, '{remembered}'),
        ('', 'k', False, '/default'),
        ('', None, True, '/default'),
    ],
)
def test_dialog_start_directory_priority(
    monkeypatch, start_dir, tmp_path, directory, history_key, remembered, expected
):
    """Explicit directory first, then the remembered one, then the default one."""
    if remembered:
        set_file_dialog_directory('k', str(tmp_path))
    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs)
        return ''

    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory', fake)
    FileDialog.getExistingDirectory(directory=directory, history_key=history_key, default_directory='/default')
    assert seen['directory'] == expected.format(remembered=tmp_path)


def test_dialog_starts_in_remembered_directory(start_dir, tmp_path):
    set_file_dialog_directory('logs', str(tmp_path))
    dialog = FileDialog(history_key='logs')
    assert os.path.samefile(dialog.directory().absolutePath(), tmp_path)


def test_dialog_starts_in_default_directory_without_history(start_dir, tmp_path):
    dialog = FileDialog(history_key='logs', default_directory=str(tmp_path))
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
    getattr(FileDialog, method)(history_key='k', default_directory=str(start_dir))
    assert seen['directory'] == str(start_dir)
    assert config.persist['file_dialog_directories'] == {'k': os.path.normpath(fmt(selected))}


def test_static_method_cancelled_keeps_history(monkeypatch, config, start_dir):
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', lambda *a, **k: ('', ''))
    FileDialog.getOpenFileName(history_key='k')
    assert config.persist['file_dialog_directories'] == {}
