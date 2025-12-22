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

from picard import log
from picard.config import get_config


class PluginCleanupManager:
    """Handles plugin cleanup operations."""

    def __init__(self, manager):
        self.manager = manager

    def get_orphaned_plugin_configs(self):
        """Get list of plugin configs that don't have corresponding installed plugins.

        Returns:
            list: List of plugin UUIDs that have config but no installed plugin
        """
        config = get_config()
        installed_uuids = {p.uuid for p in self.manager.plugins if p.uuid}

        orphaned = []
        for group in config.childGroups():
            if group.startswith('plugin.'):
                plugin_uuid = group[7:]  # Remove 'plugin.' prefix
                if plugin_uuid not in installed_uuids:
                    config.beginGroup(group)
                    if config.childKeys():  # Only include if it has settings
                        orphaned.append(plugin_uuid)
                    config.endGroup()

        return sorted(orphaned)

    def _clean_plugin_config(self, plugin_uuid):
        """Delete plugin configuration."""
        config = get_config()
        config_key = f'plugin.{plugin_uuid}'
        config.beginGroup(config_key)
        for key in config.childKeys():
            config.remove(key)
        config.endGroup()
        config.sync()
        log.info('Deleted configuration for plugin %s', plugin_uuid)
