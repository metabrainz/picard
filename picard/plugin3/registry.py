# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

import json
from pathlib import Path
import re
from urllib.request import urlopen

from picard import log


DEFAULT_REGISTRY_URL = 'https://picard.musicbrainz.org/api/v3/plugins/registry.json'


class PluginRegistry:
    """Manages plugin registry with blacklist checking."""

    def __init__(self, registry_url=None, cache_path=None):
        self.registry_url = registry_url or DEFAULT_REGISTRY_URL
        self.cache_path = cache_path
        self._registry_data = None

    def fetch_registry(self, use_cache=True):
        """Fetch registry from URL or cache."""
        if use_cache and self.cache_path and Path(self.cache_path).exists():
            try:
                with open(self.cache_path, 'r') as f:
                    self._registry_data = json.load(f)
                    log.debug('Loaded registry from cache: %s', self.cache_path)
                    return
            except Exception as e:
                log.warning('Failed to load registry cache: %s', e)

        try:
            log.debug('Fetching registry from %s', self.registry_url)
            with urlopen(self.registry_url, timeout=10) as response:
                data = response.read()
                self._registry_data = json.loads(data)

            # Save to cache
            if self.cache_path:
                try:
                    Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(self.cache_path, 'w') as f:
                        json.dump(self._registry_data, f)
                    log.debug('Saved registry to cache: %s', self.cache_path)
                except Exception as e:
                    log.warning('Failed to save registry cache: %s', e)

        except Exception as e:
            log.error('Failed to fetch registry: %s', e)
            self._registry_data = {'blacklist': []}

    def is_blacklisted(self, url, plugin_id=None):
        """Check if a plugin URL or ID is blacklisted.

        Args:
            url: Plugin repository URL
            plugin_id: Plugin ID from MANIFEST

        Returns:
            tuple: (is_blacklisted, reason)
        """
        if not self._registry_data:
            self.fetch_registry()

        blacklist = self._registry_data.get('blacklist', [])

        for entry in blacklist:
            # Check exact URL match
            if 'url' in entry and url == entry['url']:
                reason = entry.get('reason', 'Plugin is blacklisted')
                return True, reason

            # Check URL pattern match
            if 'url_pattern' in entry:
                try:
                    if re.match(entry['url_pattern'], url):
                        reason = entry.get('reason', 'Plugin matches blacklisted pattern')
                        return True, reason
                except re.error:
                    log.warning('Invalid regex pattern in blacklist: %s', entry['url_pattern'])

            # Check plugin ID match
            if plugin_id and 'plugin_id' in entry and plugin_id == entry['plugin_id']:
                reason = entry.get('reason', 'Plugin ID is blacklisted')
                return True, reason

        return False, None

    def get_trust_level(self, url):
        """Get trust level for plugin by git URL.

        Args:
            url: Plugin repository URL

        Returns:
            str: Trust level ('official', 'trusted', 'community', or 'unregistered')
        """
        if not self._registry_data:
            self.fetch_registry()

        plugins = self._registry_data.get('plugins', [])
        for plugin in plugins:
            if plugin.get('git_url') == url:
                return plugin.get('trust_level', 'community')

        return 'unregistered'

    def find_plugin(self, plugin_id=None, url=None):
        """Find plugin in registry by ID or URL.

        Args:
            plugin_id: Plugin ID to search for
            url: Git URL to search for

        Returns:
            dict: Plugin data or None if not found
        """
        if not self._registry_data:
            self.fetch_registry()

        plugins = self._registry_data.get('plugins', [])
        for plugin in plugins:
            if plugin_id and plugin.get('id') == plugin_id:
                return plugin
            if url and plugin.get('git_url') == url:
                return plugin

        return None

    def list_plugins(self, category=None, trust_level=None):
        """List plugins from registry, optionally filtered.

        Args:
            category: Filter by category (e.g., 'metadata', 'coverart')
            trust_level: Filter by trust level (e.g., 'official', 'trusted')

        Returns:
            list: List of plugin dicts
        """
        if not self._registry_data:
            self.fetch_registry()

        plugins = self._registry_data.get('plugins', [])
        result = []

        for plugin in plugins:
            # Filter by trust level
            if trust_level and plugin.get('trust_level') != trust_level:
                continue

            # Filter by category
            if category:
                plugin_categories = plugin.get('categories', [])
                if category not in plugin_categories:
                    continue

            result.append(plugin)

        return result
