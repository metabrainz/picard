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
import os
from pathlib import Path
import re
from urllib.request import urlopen

from picard import log
from picard.const.defaults import DEFAULT_PLUGIN_REGISTRY_URL


def normalize_git_url(url):
    """Normalize git URL for comparison (expand local paths to absolute).

    Args:
        url: Git URL or local path

    Returns:
        str: Normalized URL
    """
    if not url:
        return url
    # Check if it's a local path (not a remote protocol)
    # Git supports many protocols: http://, https://, git://, ssh://, ftp://, ftps://, etc.
    # If it doesn't contain :// or starts with file://, treat as local path
    if '://' not in url or url.startswith('file://'):
        # Strip file:// prefix if present
        if url.startswith('file://'):
            url = url[7:]
        # Expand ~ and make absolute
        expanded = os.path.expanduser(url)
        return os.path.abspath(expanded)
    return url


def is_local_path(url):
    """Check if URL is a local path (not a remote git URL).

    Args:
        url: Git URL or local path

    Returns:
        bool: True if local path, False if remote URL

    Git supports several URL formats:
    - scheme://... (http, https, git, ssh, ftp, ftps, file, etc.)
    - user@host:path (scp-like syntax)
    - /absolute/path or ~/path or relative/path (local paths)
    """
    if not url:
        return False

    # If it has ://, it's a URL with a scheme (unless file://)
    if '://' in url:
        return url.startswith('file://')

    # Check for scp-like syntax: user@host:path
    # This has a colon but not :// and has @ before the colon
    if ':' in url and '@' in url:
        at_pos = url.find('@')
        colon_pos = url.find(':')
        # If @ comes before : and there's no /, it's scp-like syntax
        if at_pos < colon_pos and '/' not in url[:colon_pos]:
            return False

    # Everything else is a local path
    return True


def get_local_path(url):
    """Get normalized local path if URL is local, None otherwise.

    Args:
        url: Git URL or local path

    Returns:
        Path: Normalized local path if URL is local, None if remote
    """
    if not is_local_path(url):
        return None
    # Strip file:// prefix if present
    if url.startswith('file://'):
        url = url[7:]
    # Expand ~ and make absolute
    expanded = os.path.expanduser(url)
    return Path(os.path.abspath(expanded))


class PluginRegistry:
    """Manages plugin registry with blacklist checking."""

    def __init__(self, registry_url=None, cache_path=None):
        # Priority: passed parameter > environment variable > default
        if registry_url:
            self.registry_url = registry_url
        else:
            import os

            self.registry_url = os.environ.get('PICARD_PLUGIN_REGISTRY_URL', DEFAULT_PLUGIN_REGISTRY_URL)
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

            # Check if registry_url is a local file path
            registry_path = Path(self.registry_url)
            if registry_path.exists() and registry_path.is_file():
                log.debug('Loading registry from local file: %s', self.registry_url)
                with open(registry_path, 'r') as f:
                    self._registry_data = json.load(f)
            else:
                # Fetch from URL
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

        # Normalize URL for comparison
        normalized_url = normalize_git_url(url)

        blacklist = self._registry_data.get('blacklist', [])

        for entry in blacklist:
            # Check exact URL match
            if 'url' in entry:
                blacklist_url = normalize_git_url(entry['url'])
                if normalized_url == blacklist_url:
                    reason = entry.get('reason', 'Plugin is blacklisted')
                    return True, reason

            # Check URL pattern match
            if 'url_pattern' in entry:
                try:
                    if re.match(entry['url_pattern'], normalized_url):
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

        # Normalize URL for comparison
        normalized_url = normalize_git_url(url)

        plugins = self._registry_data.get('plugins', [])
        for plugin in plugins:
            plugin_url = normalize_git_url(plugin.get('git_url', ''))
            if plugin_url == normalized_url:
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

        # Normalize URL for comparison if provided
        normalized_url = normalize_git_url(url) if url else None

        plugins = self._registry_data.get('plugins', [])
        for plugin in plugins:
            if plugin_id and plugin.get('id') == plugin_id:
                return plugin
            if normalized_url:
                plugin_url = normalize_git_url(plugin.get('git_url', ''))
                if plugin_url == normalized_url:
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
