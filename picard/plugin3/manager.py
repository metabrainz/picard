# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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
from typing import List

from picard import (
    api_versions_tuple,
    log,
)
from picard.plugin3.plugin import Plugin


class PluginManager:
    """Installs, loads and updates plugins from multiple plugin directories.
    """
    _primary_plugin_dir: str = None
    _plugin_dirs: List[str] = []
    _plugins: List[Plugin] = []

    def __init__(self, tagger):
        from picard.tagger import Tagger
        self._tagger: Tagger = tagger

    def add_directory(self, dir_path: str, primary: bool = False) -> None:
        log.debug('Registering plugin directory %s', dir_path)
        dir_path = os.path.normpath(dir_path)

        for entry in os.scandir(dir_path):
            if entry.is_dir():
                plugin = self._load_plugin(dir_path, entry.name)
                if plugin:
                    log.debug('Found plugin %s in %s', plugin.plugin_name, plugin.local_path)
                    self._plugins.append(plugin)

        self._plugin_dirs.append(dir_path)
        if primary:
            self._primary_plugin_dir = dir_path

    def init_plugins(self):
        # TODO: Only load and enable plugins enabled in configuration
        for plugin in self._plugins:
            try:
                plugin.load_module()
                plugin.enable(self._tagger)
            except Exception as ex:
                log.error('Failed initializing plugin %s from %s',
                          plugin.plugin_name, plugin.local_path, exc_info=ex)

    def _load_plugin(self, plugin_dir: str, plugin_name: str):
        plugin = Plugin(plugin_dir, plugin_name)
        try:
            plugin.read_manifest()
            # TODO: Check version compatibility
            compatible_versions = _compatible_api_versions(plugin.manifest.api_versions)
            if compatible_versions:
                return plugin
            else:
                log.warning('Plugin "%s" from "%s" is not compatible with this version of Picard.',
                            plugin.plugin_name, plugin.local_path)
        except Exception as ex:
            log.warning('Could not read plugin manifest from %r',
                        os.path.join(plugin_dir, plugin_name), exc_info=ex)
            return None


def _compatible_api_versions(api_versions):
    return set(api_versions) & set(api_versions_tuple)
