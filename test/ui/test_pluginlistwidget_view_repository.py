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

"""Regression tests for PluginListWidget._view_repository (PICARD-3494).

A plugin source may be a local filesystem path (e.g. a local git repo such as
``D:\\git\\my-plugin``). Passing such a path directly to ``QtCore.QUrl`` makes
Qt treat the Windows drive letter as the URL scheme, so
``QDesktopServices.openUrl`` silently fails. Local paths must instead be opened
via ``open_local_path`` (``QUrl.fromLocalFile``).
"""

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from picard.ui.widgets.pluginlistwidget import PluginListWidget


class _StubWidget:
    """Minimal stand-in exposing just what ``_view_repository`` needs."""

    def __init__(self, remote_url):
        self._remote_url = remote_url

    def _get_plugin_remote_url(self, plugin):
        return self._remote_url

    # Reuse the real implementation under test.
    _view_repository = PluginListWidget._view_repository


def _call_view_repository(remote_url):
    """Invoke _view_repository and return (open_local_path_arg, openurl_called)."""
    widget = _StubWidget(remote_url)
    with (
        patch('picard.ui.widgets.pluginlistwidget.open_local_path') as mock_open_local,
        patch('picard.ui.widgets.pluginlistwidget.QtGui.QDesktopServices.openUrl') as mock_open_url,
    ):
        widget._view_repository(plugin=SimpleNamespace())
    local_arg = mock_open_local.call_args[0][0] if mock_open_local.called else None
    return local_arg, mock_open_url.called


@pytest.mark.parametrize(
    'remote_url',
    [
        'https://github.com/user/plugin',
        'http://example.com/repo.git',
        'git://example.com/repo.git',
        'ssh://git@example.com/repo.git',
        'git@github.com:user/repo.git',
    ],
)
def test_view_repository_remote_url_uses_openurl(remote_url):
    local_arg, open_url_called = _call_view_repository(remote_url)
    assert open_url_called is True
    assert local_arg is None


@pytest.mark.parametrize(
    'remote_url',
    [
        '/home/user/git/my-plugin',
        '~/git/my-plugin',
        './my-plugin',
        'file:///home/user/git/my-plugin',
    ],
)
def test_view_repository_local_path_uses_open_local_path(remote_url):
    local_arg, open_url_called = _call_view_repository(remote_url)
    assert open_url_called is False
    assert local_arg is not None
    # Path is normalized to an absolute path.
    assert os.path.isabs(local_arg)


def test_view_repository_windows_drive_path_uses_open_local_path():
    # The core PICARD-3494 case: a Windows drive-letter path must not be
    # treated as a URL with scheme "d:".
    local_arg, open_url_called = _call_view_repository('D:/git/my-plugin')
    assert open_url_called is False
    assert local_arg is not None


def test_view_repository_no_remote_url_does_nothing():
    local_arg, open_url_called = _call_view_repository(None)
    assert open_url_called is False
    assert local_arg is None
