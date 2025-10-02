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

"""Shared pytest fixtures for script_text_edit tests.

Provides common fixtures used across all test files in this directory
to avoid code duplication and follow DRY principles.
"""

from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def _fake_script_config(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide minimal config so script parser can load functions without KeyError."""

    class _FakeSetting(dict):
        def raw_value(self, name, qtype=None):
            return self.get(name)

        def key(self, name):
            return name

    cfg = SimpleNamespace(setting=_FakeSetting({'enabled_plugins': []}), sync=lambda: None)
    import picard.config as picard_config_mod
    import picard.extension_points as ext_points_mod

    monkeypatch.setattr(picard_config_mod, 'get_config', lambda: cfg, raising=True)
    monkeypatch.setattr(ext_points_mod, 'get_config', lambda: cfg, raising=True)
    return cfg
