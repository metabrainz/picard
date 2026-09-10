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


from picard.config import get_config

import pytest

from picard.ui.options.metadata import MetadataOptionsPage


@pytest.fixture()
def metadata_options_page(qapp, patch_tagger_instance):
    patch_tagger_instance('picard.ui.options')
    return MetadataOptionsPage()


def test_load_with_known_locale(metadata_options_page):
    config = get_config()
    config.setting['translation_locales'] = ['en']
    metadata_options_page.load()
    assert metadata_options_page.current_locales == ['en']


def test_load_with_unknown_locale_does_not_crash(metadata_options_page):
    # A config carried over from an older Picard/CLDR version (or a corrupted
    # value) may contain a locale code that no longer exists in ALIAS_LOCALES.
    # Loading the page must not raise (which would disable the Metadata options
    # page in the dialog).
    config = get_config()
    config.setting['translation_locales'] = ['en', 'zz_DOES_NOT_EXIST', 'de']
    metadata_options_page.load()
    # Unknown locales are dropped from the display text but valid ones remain.
    assert 'zz_DOES_NOT_EXIST' not in metadata_options_page.ui.selected_locales.text()


def test_load_drops_unknown_locale_from_current_locales(metadata_options_page):
    # Invalid entries must be removed from current_locales so a later save()
    # does not re-persist them; valid entries keep their order.
    config = get_config()
    config.setting['translation_locales'] = ['en', 'zz_DOES_NOT_EXIST', 'de']
    metadata_options_page.load()
    assert metadata_options_page.current_locales == ['en', 'de']


def test_load_falls_back_to_default_when_all_locales_unknown(metadata_options_page):
    # If no valid locale remains (e.g. a fully corrupted value), fall back to
    # the option default instead of leaving an empty locale list.
    config = get_config()
    config.setting['translation_locales'] = ['\x85n', 'zz_DOES_NOT_EXIST']
    metadata_options_page.load()
    assert metadata_options_page.current_locales == ['en']


def test_save_after_sanitizing_persists_clean_locales(metadata_options_page):
    # After load() sanitizes the value, save() must write back only valid
    # locales, not the original corrupted list.
    config = get_config()
    config.setting['translation_locales'] = ['en', 'zz_DOES_NOT_EXIST']
    metadata_options_page.load()
    metadata_options_page.save()
    assert config.setting['translation_locales'] == ['en']
