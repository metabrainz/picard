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


from unittest.mock import (
    Mock,
    patch,
)

from PyQt6 import QtWidgets

from picard.plugin3.manager import PluginSignatureError

import pytest

from picard.ui.dialogs.installplugin import InstallPluginDialog


@pytest.fixture
def dialog():
    """An InstallPluginDialog shell without running its heavy __init__."""
    d = InstallPluginDialog.__new__(InstallPluginDialog)
    d.status_label = Mock()
    d._install_params = {
        'url': 'https://example/p.git',
        'ref': 'v1',
        'plugin': Mock(),
        'current_tab': 0,
        'no_git': False,
    }
    d._installing_plugin = Mock()
    d._proceed_with_install = Mock()
    d._enable_ui_after_installation = Mock()
    return d


def test_unverifiable_yes_retries_with_override(dialog):
    error = PluginSignatureError('https://example/p.git', 'unverifiable')
    with patch.object(QtWidgets.QMessageBox, 'warning', return_value=QtWidgets.QMessageBox.StandardButton.Yes):
        dialog._handle_signature_error(error)
    dialog._proceed_with_install.assert_called_once()
    # The retry must set allow_unverified=True and reuse the stored params.
    _, kwargs = dialog._proceed_with_install.call_args
    assert kwargs['allow_unverified'] is True
    assert kwargs['url'] == 'https://example/p.git'
    dialog._enable_ui_after_installation.assert_not_called()


def test_unverifiable_no_cancels(dialog):
    error = PluginSignatureError('https://example/p.git', 'unverifiable')
    with patch.object(QtWidgets.QMessageBox, 'warning', return_value=QtWidgets.QMessageBox.StandardButton.No):
        dialog._handle_signature_error(error)
    dialog._proceed_with_install.assert_not_called()
    dialog._enable_ui_after_installation.assert_called_once()


@pytest.mark.parametrize('reason', ['no_match', 'unsigned'])
def test_verified_bad_never_offers_override(dialog, reason):
    error = PluginSignatureError('https://example/p.git', reason)
    with (
        patch.object(QtWidgets.QMessageBox, 'warning') as mock_warning,
        patch('picard.ui.dialogs.installplugin.show_plugin_error') as mock_show_error,
    ):
        dialog._handle_signature_error(error)
    # No override prompt for wrong/missing signatures.
    mock_warning.assert_not_called()
    mock_show_error.assert_called_once()
    dialog._proceed_with_install.assert_not_called()
    dialog._enable_ui_after_installation.assert_called_once()
