# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bryan Roessler
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from picard.config import get_config

import pytest

from picard.ui.options.cover import CoverOptionsPage


@pytest.fixture()
def cover_options_page(qapp, patch_tagger_instance):
    patch_tagger_instance('picard.ui.options')

    page = CoverOptionsPage()
    page.load()
    return page


def test_save_preserves_remove_even_without_save_to_files(cover_options_page):
    # The checkbox state is persisted as-is; the runtime guards against
    # removing images when save_images_to_files is disabled.
    cover_options_page.ui.save_images_to_files.setChecked(False)
    cover_options_page.ui.remove_images_from_tags.setChecked(True)
    cover_options_page.save()

    config = get_config()
    assert config.setting['save_images_to_files'] is False
    assert config.setting['remove_images_from_tags'] is True


def test_save_keep_remove_images_true(cover_options_page):
    cover_options_page.ui.save_images_to_tags.setChecked(False)
    cover_options_page.ui.save_images_to_files.setChecked(True)
    cover_options_page.ui.remove_images_from_tags.setChecked(True)
    cover_options_page.save()

    config = get_config()
    assert config.setting['save_images_to_files'] is True
    assert config.setting['remove_images_from_tags'] is True


def test_embed_and_remove_are_mutually_exclusive(cover_options_page):
    cover_options_page.ui.save_images_to_files.setChecked(True)
    cover_options_page.ui.save_images_to_tags.setChecked(False)
    cover_options_page.ui.remove_images_from_tags.setChecked(True)
    assert cover_options_page.ui.remove_images_from_tags.isEnabled()

    # Enabling embed disables remove but preserves the checked state,
    # so it's restored when embedding is turned off again.
    cover_options_page.ui.save_images_to_tags.setChecked(True)
    assert not cover_options_page.ui.remove_images_from_tags.isEnabled()
    assert cover_options_page.ui.remove_images_from_tags.isChecked()

    # Saving with embed active persists the checkbox state (True), since
    # the runtime code already guards against the incompatible combination.
    cover_options_page.save()
    config = get_config()
    assert config.setting['save_images_to_tags'] is True
    assert config.setting['remove_images_from_tags'] is True

    # Turning embed off re-enables the checkbox with its prior state intact
    cover_options_page.ui.save_images_to_tags.setChecked(False)
    assert cover_options_page.ui.remove_images_from_tags.isEnabled()
    assert cover_options_page.ui.remove_images_from_tags.isChecked()


def test_load_disables_remove_when_embed_enabled(cover_options_page):
    cover_options_page.ui.save_images_to_tags.setChecked(True)
    assert not cover_options_page.ui.remove_images_from_tags.isEnabled()

    cover_options_page.ui.save_images_to_tags.setChecked(False)
    assert cover_options_page.ui.remove_images_from_tags.isEnabled()
