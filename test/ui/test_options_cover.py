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


from PyQt6.QtCore import Qt

from picard.config import get_config
from picard.coverart.providers.provider import CoverArtProvider
from picard.extension_points import (
    set_plugin_uuid,
    unset_plugin_uuid,
)
from picard.extension_points.cover_art_providers import (
    ext_point_cover_art_providers,
)

import pytest

from picard.ui.options.cover import CoverOptionsPage
from picard.ui.util import qlistwidget_items


@pytest.fixture()
def cover_options_page(qapp, patch_tagger_instance):
    patch_tagger_instance('picard.ui.options')

    page = CoverOptionsPage()
    page.load()
    return page


# Module path that mimics a v3 plugin so the extension point applies the
# plugins3_enabled_plugins gating (see ExtensionPoint.__iter__).
_PLUGIN_MODULE = 'picard.plugins.fake_ca_provider'
_PLUGIN_NAME = 'fake_ca_provider'
_PLUGIN_UUID = 'fake-ca-provider-uuid'


class _FakePluginProvider(CoverArtProvider):
    NAME = 'FakePluginProvider'
    TITLE = 'Fake Plugin Provider'
    __module__ = _PLUGIN_MODULE

    def queue_images(self):
        return self.QueueState.FINISHED


@pytest.fixture()
def plugin_ca_provider():
    """Register a fake plugin-provided cover art provider.

    Yields a controller exposing enable()/disable() to simulate the plugin
    being toggled in Options > Plugins (which registers/unregisters the
    provider and flips plugins3_enabled_plugins).
    """
    set_plugin_uuid(_PLUGIN_UUID, _PLUGIN_NAME)
    config = get_config()

    class _Controller:
        def enable(self):
            ext_point_cover_art_providers.unregister(_PLUGIN_MODULE, lambda item: item is _FakePluginProvider)
            ext_point_cover_art_providers.register(_PLUGIN_MODULE, _FakePluginProvider)
            enabled = list(config.setting['plugins3_enabled_plugins'])
            if _PLUGIN_UUID not in enabled:
                enabled.append(_PLUGIN_UUID)
            config.setting['plugins3_enabled_plugins'] = enabled

        def disable(self):
            config.setting['plugins3_enabled_plugins'] = [
                u for u in config.setting['plugins3_enabled_plugins'] if u != _PLUGIN_UUID
            ]

    try:
        yield _Controller()
    finally:
        ext_point_cover_art_providers.unregister_module(_PLUGIN_NAME)
        unset_plugin_uuid(_PLUGIN_UUID)


def test_disabling_plugin_preserves_ca_provider_config(cover_options_page, plugin_ca_provider):
    """PICARD-3498: a disabled plugin's cover art provider config must survive save().

    Reproduces the bug where disabling a plugin and saving Options purges its
    provider entry from ca_providers, losing the user's position and enabled
    state when the plugin is later re-enabled.
    """
    config = get_config()

    # 1. Plugin enabled, provider configured at the top of the list, enabled.
    plugin_ca_provider.enable()
    config.setting['ca_providers'] = [
        ('FakePluginProvider', True),
        ('CaaReleaseGroup', True),
        ('Cover Art Archive', True),
        ('UrlRelationships', True),
        ('Local', False),
    ]

    # 2. User disables the plugin, then opens and saves Options.
    plugin_ca_provider.disable()
    cover_options_page.load()
    cover_options_page.save()

    saved = dict(config.setting['ca_providers'])
    assert 'FakePluginProvider' in saved, "disabled plugin provider was purged from ca_providers"
    assert saved['FakePluginProvider'] is True, "disabled plugin provider lost its enabled state"

    # 3. Re-enable the plugin and confirm position + enabled state are restored.
    plugin_ca_provider.enable()
    cover_options_page.load()

    rows = [
        (item.data(Qt.ItemDataRole.UserRole), item.checked)
        for item in qlistwidget_items(cover_options_page.ui.ca_providers_list)
    ]
    names = [name for name, _checked in rows]
    assert names[0] == 'FakePluginProvider', f"provider lost its position, order is {names}"
    assert dict(rows)['FakePluginProvider'] is True, "provider lost its enabled state after re-enable"


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
