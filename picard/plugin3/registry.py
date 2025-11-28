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


def get_local_repository_path(url):
    """Get local repository path if URL is local git directory, None otherwise.

    Args:
        url: Git URL or local path

    Returns:
        Path: Normalized local git directory path if exists, None otherwise
    """
    local_path = get_local_path(url)
    if local_path and local_path.is_dir() and (local_path / '.git').exists():
        return local_path
    return None


class PluginRegistry:
    """Manages plugin registry with blacklist checking."""

    def __init__(self, registry_url=None, cache_dir=None):
        """Initialize plugin registry.

        Args:
            registry_url: Registry URL (defaults to DEFAULT_PLUGIN_REGISTRY_URL or PICARD_PLUGIN_REGISTRY_URL env var)
            cache_dir: Directory for cache files (cache filename will be URL-specific)
        """
        # Priority: passed parameter > environment variable > default
        if registry_url:
            self.registry_url = registry_url
        else:
            import os

            self.registry_url = os.environ.get('PICARD_PLUGIN_REGISTRY_URL', DEFAULT_PLUGIN_REGISTRY_URL)

        # Create URL-specific cache path using SHA1 hash
        if cache_dir:
            import hashlib

            url_hash = hashlib.sha1(self.registry_url.encode()).hexdigest()[:16]
            self.cache_path = Path(cache_dir) / f'plugin_registry_{url_hash}.json'
        else:
            self.cache_path = None

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
            log.debug('Failed to fetch registry: %s', e)
            self._registry_data = {'blacklist': []}

    def is_blacklisted(self, url, plugin_uuid=None):
        """Check if a plugin URL or UUID is blacklisted.

        Args:
            url: Plugin repository URL
            plugin_uuid: Plugin UUID from MANIFEST

        Returns:
            tuple: (is_blacklisted, reason)
        """
        if not self._registry_data:
            self.fetch_registry()

        # Normalize URL for comparison
        normalized_url = normalize_git_url(url) if url else None

        blacklist = self._registry_data.get('blacklist', [])

        for entry in blacklist:
            # Check UUID + URL combination (most specific - blocks specific fork)
            if 'uuid' in entry and 'url' in entry:
                if plugin_uuid and plugin_uuid == entry['uuid']:
                    blacklist_url = normalize_git_url(entry['url'])
                    if normalized_url == blacklist_url:
                        reason = entry.get('reason', 'Plugin is blacklisted')
                        return True, reason

            # Check UUID only (blocks all sources)
            elif 'uuid' in entry:
                if plugin_uuid and plugin_uuid == entry['uuid']:
                    reason = entry.get('reason', 'Plugin UUID is blacklisted')
                    return True, reason

            # Check exact URL match
            elif 'url' in entry:
                if normalized_url:
                    blacklist_url = normalize_git_url(entry['url'])
                    if normalized_url == blacklist_url:
                        reason = entry.get('reason', 'Plugin is blacklisted')
                        return True, reason

            # Check URL regex match
            elif 'url_regex' in entry:
                if normalized_url:
                    try:
                        if re.match(entry['url_regex'], normalized_url):
                            reason = entry.get('reason', 'Plugin matches blacklisted pattern')
                            return True, reason
                    except re.error:
                        log.warning('Invalid regex pattern in blacklist: %s', entry['url_regex'])

        return False, None

    def get_registry_info(self):
        """Get registry metadata.

        Returns:
            dict: Registry info with last_updated, plugin_count, api_version, registry_url

        Raises:
            RuntimeError: If registry data not loaded
        """
        if not self._registry_data:
            raise RuntimeError("Registry not loaded")

        return {
            'last_updated': self._registry_data.get('last_updated'),
            'plugin_count': len(self._registry_data.get('plugins', [])),
            'api_version': self._registry_data.get('api_version'),
            'registry_url': self.registry_url,
        }

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

    def find_plugin(self, plugin_id=None, url=None, uuid=None):
        """Find plugin in registry by ID, URL, or UUID (with redirect support).

        Args:
            plugin_id: Plugin ID to search for
            url: Git URL to search for
            uuid: Plugin UUID to search for

        Returns:
            dict: Plugin data or None if not found
        """
        if not self._registry_data:
            self.fetch_registry()

        # Normalize URL for comparison if provided
        normalized_url = normalize_git_url(url) if url else None

        plugins = self._registry_data.get('plugins', [])

        # First pass: search by current values (fast path)
        for plugin in plugins:
            if plugin_id and plugin.get('id') == plugin_id:
                return plugin
            if uuid and plugin.get('uuid') == uuid:
                return plugin
            if normalized_url:
                plugin_url = normalize_git_url(plugin.get('git_url', ''))
                if plugin_url == normalized_url:
                    return plugin

        # Second pass: search redirects (only if not found above)
        if normalized_url or uuid:
            for plugin in plugins:
                # Check URL redirects
                if normalized_url and 'redirect_from' in plugin:
                    for old_url in plugin['redirect_from']:
                        old_url_normalized = normalize_git_url(old_url)
                        if old_url_normalized == normalized_url:
                            log.info('Found plugin via URL redirect: %s -> %s', url, plugin.get('git_url'))
                            return plugin

                # Check UUID redirects
                if uuid and 'redirect_from_uuid' in plugin:
                    if uuid in plugin['redirect_from_uuid']:
                        log.info('Found plugin via UUID redirect: %s -> %s', uuid, plugin.get('uuid'))
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
