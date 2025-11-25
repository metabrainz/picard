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
import shutil
from typing import List

from picard import (
    api_versions_tuple,
    log,
)
from picard.plugin3.plugin import (
    Plugin,
    PluginSourceGit,
)


class PluginManager:
    """Installs, loads and updates plugins from multiple plugin directories."""

    _primary_plugin_dir: Path = None
    _plugin_dirs: List[Path] = []
    _plugins: List[Plugin] = []

    def __init__(self, tagger):
        from picard.tagger import Tagger

        self._tagger: Tagger = tagger
        self._enabled_plugins = set()
        self._load_config()

    @property
    def plugins(self):
        return self._plugins

    def add_directory(self, dir_path: str, primary: bool = False) -> None:
        dir_path = Path(os.path.normpath(dir_path))
        if dir_path in self._plugin_dirs:
            log.warning('Plugin directory %s already registered', dir_path)
            return

        log.debug('Registering plugin directory %s', dir_path)
        if not dir_path.exists():
            os.makedirs(dir_path)

        for entry in dir_path.iterdir():
            if entry.is_dir():
                plugin = self._load_plugin(dir_path, entry.name)
                if plugin:
                    log.debug('Found plugin %s in %s', plugin.name, plugin.local_path)
                    self._plugins.append(plugin)

        self._plugin_dirs.append(dir_path)
        if primary:
            self._primary_plugin_dir = dir_path

    def install_plugin(self, url):
        source = PluginSourceGit(url)
        dirname = os.path.basename(url)
        source.sync(self._primary_plugin_dir.joinpath(dirname))

    def uninstall_plugin(self, plugin: Plugin):
        self.disable_plugin(plugin)
        plugin_path = plugin.local_path
        if plugin_path.is_relative_to(self._primary_plugin_dir):
            if os.path.islink(plugin_path):
                log.debug("Removing symlink %r", plugin_path)
                os.remove(plugin_path)
            elif os.path.isdir(plugin_path):
                log.debug("Removing directory %r", plugin_path)
                shutil.rmtree(plugin_path)

    def init_plugins(self):
        """Initialize and enable plugins that are enabled in configuration."""
        for plugin in self._plugins:
            if plugin.name in self._enabled_plugins:
                try:
                    plugin.load_module()
                    plugin.enable(self._tagger)
                except Exception as ex:
                    log.error('Failed initializing plugin %s from %s', plugin.name, plugin.local_path, exc_info=ex)

    def enable_plugin(self, plugin: Plugin):
        """Enable a plugin and save to config."""
        plugin.load_module()
        plugin.enable(self._tagger)
        self._enabled_plugins.add(plugin.name)
        self._save_config()

    def disable_plugin(self, plugin: Plugin):
        """Disable a plugin and save to config."""
        plugin.disable()
        self._enabled_plugins.discard(plugin.name)
        self._save_config()

    def _load_config(self):
        """Load enabled plugins list from config."""
        from picard.config import get_config

        config = get_config()
        enabled = config.setting.get('plugins3', {}).get('enabled_plugins', [])
        self._enabled_plugins = set(enabled)
        log.debug('Loaded enabled plugins from config: %r', self._enabled_plugins)

    def _save_config(self):
        """Save enabled plugins list to config."""
        from picard.config import get_config

        config = get_config()
        if 'plugins3' not in config.setting:
            config.setting['plugins3'] = {}
        config.setting['plugins3']['enabled_plugins'] = list(self._enabled_plugins)
        log.debug('Saved enabled plugins to config: %r', self._enabled_plugins)

    def _load_plugin(self, plugin_dir: Path, plugin_name: str):
        plugin = Plugin(plugin_dir, plugin_name)
        try:
            plugin.read_manifest()
            # TODO: Check version compatibility
            compatible_versions = _compatible_api_versions(plugin.manifest.api_versions)
            if compatible_versions:
                return plugin
            else:
                log.warning(
                    'Plugin "%s" from "%s" is not compatible with this version of Picard.',
                    plugin.name,
                    plugin.local_path,
                )
        except Exception as ex:
            log.warning('Could not read plugin manifest from %r', plugin_dir.joinpath(plugin_name), exc_info=ex)
            return None


def _compatible_api_versions(api_versions):
    return set(api_versions) & set(api_versions_tuple)
