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

"""Shared fixtures for the UI tests."""

from picard import config as picard_config

import pytest

import picard.ui.util as ui_util


@pytest.fixture()
def config(monkeypatch):
    """Fake config (see test/conftest.py) made visible to `picard.ui.util`."""
    cfg = picard_config.get_config()
    # picard.ui.util imported get_config before the test config was installed
    monkeypatch.setattr(ui_util, 'get_config', lambda: cfg)
    cfg.setting['starting_directory'] = False
    cfg.persist['file_dialog_directories'] = {}
    return cfg
