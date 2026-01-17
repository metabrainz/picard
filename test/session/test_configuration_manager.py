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

"""Tests for ConfigurationManager."""

from unittest.mock import (
    Mock,
    patch,
)

import picard.config as picard_config
from picard.session.session_loader import ConfigurationManager


def test_configuration_manager_prepare_session(cfg_options) -> None:
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = True

    manager = ConfigurationManager()
    tagger = Mock()
    manager.prepare_session(tagger)

    tagger.clear_session.assert_called_once()
    assert tagger._restoring_session is True


def test_configuration_manager_prepare_session_safe_restore_disabled(cfg_options) -> None:
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = False

    manager = ConfigurationManager()
    tagger = Mock()
    manager.prepare_session(tagger)

    tagger.clear_session.assert_called_once()
    if hasattr(tagger, '_restoring_session'):
        assert tagger._restoring_session is not True


@patch("picard.session.session_loader.get_config")
def test_configuration_manager_restore_options_with_defaults(mock_get_config) -> None:
    config_mock = Mock()
    config_mock.setting = {
        'rename_files': False,
        'move_files': False,
        'enable_tag_saving': False,
    }
    mock_get_config.return_value = config_mock

    manager = ConfigurationManager()
    manager.restore_options({})

    assert config_mock.setting['rename_files'] is False
    assert config_mock.setting['move_files'] is False
    assert config_mock.setting['enable_tag_saving'] is False


def test_configuration_manager_restore_options(cfg_options) -> None:
    manager = ConfigurationManager()
    options = {
        'rename_files': True,
        'move_files': True,
        'enable_tag_saving': True,
    }
    manager.restore_options(options)
    cfg = picard_config.get_config()
    assert cfg.setting['rename_files'] is True
    assert cfg.setting['move_files'] is True
    assert cfg.setting['enable_tag_saving'] is True
