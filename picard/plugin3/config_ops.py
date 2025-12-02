# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer, Laurent Monin
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

"""Plugin configuration operations."""


class ConfigOperations:
    """Handles plugin configuration operations."""

    @staticmethod
    def get_config_value(*keys, default=None):
        """Get nested config value by keys.

        Args:
            *keys: Nested keys to traverse
            default: Default value if key path doesn't exist

        Returns:
            Config value or default
        """
        from picard.config import get_config

        config = get_config()
        value = config.setting
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    @staticmethod
    def set_config_value(*keys, value):
        """Set nested config value by keys.

        Args:
            *keys: Nested keys to traverse
            value: Value to set
        """
        from picard.config import get_config

        if not keys:
            return

        config = get_config()
        current = config.setting

        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value
        current[keys[-1]] = value

    @staticmethod
    def clean_plugin_config(plugin_name: str):
        """Delete plugin configuration.

        Args:
            plugin_name: Name of plugin to clean config for
        """
        from picard import log
        from picard.config import get_config

        config = get_config()
        setting = config.setting

        if 'plugins3' in setting and plugin_name in setting['plugins3']:
            del setting['plugins3'][plugin_name]
            log.info('Deleted configuration for plugin %s', plugin_name)
