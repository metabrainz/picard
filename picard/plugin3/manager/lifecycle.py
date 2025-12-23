# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024-2025 Philipp Wolfer
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

import os
from pathlib import Path

from picard import (
    api_versions_tuple,
    log,
)
from picard.config import get_config
from picard.extension_points import (
    set_plugin_uuid,
    unset_plugin_uuid,
)
from picard.plugin3.installable import UrlInstallablePlugin
from picard.plugin3.plugin import (
    Plugin,
    PluginState,
)


class PluginLifecycleManager:
    """Handles plugin lifecycle operations: enable, disable, uninstall, load."""

    def __init__(self, manager):
        self.manager = manager

    def uninstall_plugin(self, plugin: Plugin, purge=False):
        """Uninstall a plugin."""
        self.manager.disable_plugin(plugin)
        plugin_path = plugin.local_path

        # Safety check: ensure plugin_path is a child of primary plugin dir, not the dir itself
        assert self.manager._primary_plugin_dir is not None
        assert plugin_path is not None
        if (
            not plugin_path.is_relative_to(self.manager._primary_plugin_dir)
            or plugin_path == self.manager._primary_plugin_dir
        ):
            raise ValueError(f'Plugin path must be a subdirectory of {self.manager._primary_plugin_dir}: {plugin_path}')

        if os.path.islink(plugin_path):
            log.debug("Removing symlink %r", plugin_path)
            os.remove(plugin_path)
        elif os.path.isdir(plugin_path):
            log.debug("Removing directory %r", plugin_path)
            self.manager._safe_remove_directory(plugin_path, f"plugin directory for {plugin.plugin_id}")

        # Remove metadata
        config = get_config()
        # Remove metadata by UUID if available
        if plugin.uuid:
            config.setting['plugins3_metadata'].pop(plugin.uuid, None)

        # Unregister UUID mapping
        if plugin.uuid:
            unset_plugin_uuid(plugin.uuid)

        # Remove plugin config if purge requested
        if purge and plugin.uuid:
            self.manager._clean_plugin_config(plugin.uuid)

        # Remove plugin from plugins list
        if plugin in self.manager.plugins:
            self.manager.plugins.remove(plugin)

        self.manager.plugin_uninstalled.emit(plugin)

    def enable_plugin(self, plugin: Plugin):
        """Enable a plugin and save to config."""
        uuid, metadata = self.manager._get_plugin_uuid_and_metadata(plugin)
        assert plugin.state is not None
        log.debug('Enabling plugin %s (UUID %s, current state: %s)', plugin.plugin_id, uuid, plugin.state.value)

        got_enabled = False
        if self.manager._tagger:
            plugin.load_module()
            # Only enable if not already enabled
            if plugin.state != PluginState.ENABLED:
                try:
                    plugin.enable(self.manager._tagger)
                    got_enabled = True
                except Exception:
                    # If enable fails, ensure plugin is in disabled state
                    if plugin.state == PluginState.LOADED:
                        try:
                            plugin.disable()
                        except Exception:
                            # If disable also fails, force state to disabled
                            plugin.state = PluginState.DISABLED
                    raise

        # Ensure UUID mapping is set for extension points
        if plugin.uuid:
            set_plugin_uuid(plugin.uuid, plugin.plugin_id)

        self.manager._enabled_plugins.add(uuid)
        self.manager._save_config()
        log.info('Plugin %s enabled (state: %s)', plugin.plugin_id, plugin.state.value)

        # Only trigger signal, if plugin wasn't already enabled
        if got_enabled:
            self.manager.plugin_enabled.emit(plugin)
            self.manager.plugin_state_changed.emit(plugin)

    def disable_plugin(self, plugin: Plugin):
        """Disable a plugin and save to config."""
        uuid, metadata = self.manager._get_plugin_uuid_and_metadata(plugin)
        assert plugin.state is not None
        log.debug('Disabling plugin %s (UUID %s, current state: %s)', plugin.plugin_id, uuid, plugin.state.value)

        # Only disable if not already disabled
        got_disabled = False
        if plugin.state != PluginState.DISABLED:
            try:
                plugin.disable()
                got_disabled = True
            except Exception:
                # If disable fails, force plugin to disabled state
                plugin.state = PluginState.DISABLED
                got_disabled = True
                raise

        self.manager._enabled_plugins.discard(uuid)
        self.manager._save_config()
        log.info('Plugin %s disabled (state: %s)', plugin.plugin_id, plugin.state.value)

        # Only trigger signal, if plugin wasn't already disabled
        if got_disabled:
            self.manager.plugin_disabled.emit(plugin)
            self.manager.plugin_state_changed.emit(plugin)

    def _load_plugin(self, plugin_dir: Path, plugin_name: str):
        """Load a plugin and check API version compatibility."""
        plugin = Plugin(plugin_dir, plugin_name)
        try:
            plugin.read_manifest()

            # Register UUID mapping early so extension points can find enabled plugins
            if plugin.uuid:
                set_plugin_uuid(plugin.uuid, plugin.plugin_id)

            assert plugin.manifest is not None
            compatible_versions = _compatible_api_versions(plugin.manifest.api_versions)
            if compatible_versions:
                log.debug(
                    'Plugin "%s" is compatible (requires API %s, Picard supports %s)',
                    plugin.plugin_id,
                    plugin.manifest.api_versions,
                    api_versions_tuple,
                )
                return plugin
            else:
                log.warning(
                    'Plugin "%s" from "%s" is not compatible with this version of Picard. '
                    'Plugin requires API versions %s, but Picard supports %s.',
                    plugin.plugin_id,
                    plugin.local_path,
                    plugin.manifest.api_versions,
                    api_versions_tuple,
                )
                return None
        except Exception as ex:
            error_msg = str(ex)
            log.warning('Could not read plugin manifest from %r', plugin_dir.joinpath(plugin_name), exc_info=ex)
            self.manager._failed_plugins.append((plugin_dir, plugin_name, error_msg))
            return None

    def plugin_has_saved_options(self, plugin: Plugin) -> bool:
        """Check if a plugin has any saved options."""
        if not plugin.uuid:
            return False
        config = get_config()
        config_key = f'plugin.{plugin.uuid}'
        config.beginGroup(config_key)
        has_options = len(config.childKeys()) > 0
        config.endGroup()
        return has_options

    def _check_blacklisted_plugins(self):
        """Check installed plugins against blacklist and disable if needed."""
        blacklisted_plugins = []

        for plugin in self.manager._plugins:
            # Get UUID from plugin manifest
            if not plugin.uuid:
                continue

            metadata = self.manager._metadata.get_plugin_metadata(plugin.uuid)
            url = metadata.url if metadata else None

            # Create InstallablePlugin for blacklist checking
            installable_plugin = UrlInstallablePlugin(url, registry=self.manager._registry)
            installable_plugin.plugin_uuid = plugin.uuid

            is_blacklisted, reason = installable_plugin.is_blacklisted()
            if is_blacklisted:
                log.warning('Plugin %s is blacklisted: %s', plugin.plugin_id, reason)
                blacklisted_plugins.append((plugin.plugin_id, reason))

                if plugin.uuid in self.manager._enabled_plugins:
                    log.warning('Disabling blacklisted plugin %s', plugin.plugin_id)
                    self.manager._enabled_plugins.discard(plugin.uuid)
                    self.manager._save_config()

        return blacklisted_plugins

    def init_plugins(self):
        """Initialize and enable plugins that are enabled in configuration."""
        # Check for blacklisted plugins on startup
        blacklisted_plugins = self._check_blacklisted_plugins()

        enabled_count = 0
        for plugin in self.manager._plugins:
            if plugin.uuid and plugin.uuid in self.manager._enabled_plugins:
                try:
                    log.info('Loading plugin: %s', plugin.manifest.name() if plugin.manifest else plugin.plugin_id)
                    plugin.load_module()
                    plugin.enable(self.manager._tagger)
                    enabled_count += 1
                except Exception as ex:
                    log.error('Failed initializing plugin %s from %s', plugin.plugin_id, plugin.local_path, exc_info=ex)

        log.info('Loaded %d plugin%s', enabled_count, 's' if enabled_count != 1 else '')
        return blacklisted_plugins

    def _load_config(self):
        """Load enabled plugins list from config."""
        config = get_config()
        if config is None:
            # Config not initialized (e.g., in tests)
            self.manager._enabled_plugins = set()
            return
        enabled = config.setting['plugins3_enabled_plugins']
        self.manager._enabled_plugins = set(enabled)
        log.debug('Loaded enabled plugins from config: %r', self.manager._enabled_plugins)

    def _save_config(self):
        """Save enabled plugins list to config."""
        config = get_config()
        if config is None:
            # Config not initialized (e.g., in tests)
            return
        config.setting['plugins3_enabled_plugins'] = list(self.manager._enabled_plugins)
        if hasattr(config, 'sync'):
            config.sync()
        log.debug('Saved enabled plugins to config: %r', self.manager._enabled_plugins)


def _compatible_api_versions(api_versions):
    return set(api_versions) & set(api_versions_tuple)
