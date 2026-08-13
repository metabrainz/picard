# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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

from unittest.mock import MagicMock

from picard.config import get_config

import pytest

from picard.ui.options.cover import CoverOptionsPage


@pytest.fixture(autouse=True)
def _patch_tagger_instance(monkeypatch):
    import picard.ui.options as options_module

    monkeypatch.setattr(options_module, 'tagger_instance', lambda: MagicMock())


def test_save_forces_remove_images_from_tags_false_when_save_to_files_disabled():
    page = CoverOptionsPage()
    page.load()

    # remove_images_from_tags is checked, but save_images_to_files is not
    page.ui.save_images_to_files.setChecked(False)
    page.ui.remove_images_from_tags.setChecked(True)
    page.save()

    config = get_config()
    assert config.setting['save_images_to_files'] is False
    assert config.setting['remove_images_from_tags'] is False


def test_save_keeps_remove_images_from_tags_true_when_save_to_files_enabled():
    page = CoverOptionsPage()
    page.load()

    page.ui.save_images_to_files.setChecked(True)
    page.ui.remove_images_from_tags.setChecked(True)
    page.save()

    config = get_config()
    assert config.setting['save_images_to_files'] is True
    assert config.setting['remove_images_from_tags'] is True
