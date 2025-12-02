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

from functools import lru_cache
import json
import os
from pathlib import Path
import re
import time
import urllib.error
from urllib.request import urlopen

from picard import log
from picard.const.defaults import DEFAULT_PLUGIN_REGISTRY_URLS
from picard.plugin3.plugin import hash_string


# Retry configuration for registry fetch operations
REGISTRY_FETCH_MAX_RETRIES = 3
REGISTRY_FETCH_INITIAL_TIMEOUT = 10  # seconds
REGISTRY_FETCH_TIMEOUT_MULTIPLIER = 2  # exponential backoff for timeout
REGISTRY_FETCH_RETRY_DELAY_BASE = 2  # exponential backoff for retry delay


class RegistryError(Exception):
    """Base exception for registry errors."""

    pass


class RegistryFetchError(RegistryError):
    """Raised when registry cannot be fetched from URL."""

    def __init__(self, url, original_error):
        self.url = url
        self.original_error = original_error
        super().__init__(f"Failed to fetch registry from {url}: {original_error}")


class RegistryParseError(RegistryError):
    """Raised when registry JSON cannot be parsed."""

    def __init__(self, url, original_error):
        self.url = url
        self.original_error = original_error
        super().__init__(f"Failed to parse registry from {url}: {original_error}")


class RegistryCacheError(RegistryError):
    """Raised when registry cache cannot be read or written."""

    def __init__(self, cache_path, operation, original_error):
        self.cache_path = cache_path
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"Failed to {operation} registry cache {cache_path}: {original_error}")


@lru_cache(maxsize=256)
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
            registry_url: Registry URL or list of URLs to try (defaults to DEFAULT_PLUGIN_REGISTRY_URLS or PICARD_PLUGIN_REGISTRY_URL env var)
            cache_dir: Directory for cache files (cache filename will be URL-specific)
        """
        # Priority: passed parameter > environment variable > default list
        if registry_url:
            # If single URL passed, convert to list
            self.registry_urls = [registry_url] if isinstance(registry_url, str) else registry_url
        else:
            env_url = os.environ.get('PICARD_PLUGIN_REGISTRY_URL')
            if env_url:
                # Environment variable takes precedence, try it first then fallback to defaults
                self.registry_urls = [env_url] + DEFAULT_PLUGIN_REGISTRY_URLS
            else:
                self.registry_urls = DEFAULT_PLUGIN_REGISTRY_URLS

        # Use first URL for cache path (primary URL)
        self.registry_url = self.registry_urls[0]

        # Create URL-specific cache path using SHA1 hash
        if cache_dir:
            url_hash = hash_string(self.registry_url)
            self.cache_path = Path(cache_dir) / f'plugin_registry_{url_hash}.json'
        else:
            self.cache_path = None

        self._registry_data = None
        self._fetch_failed = False  # Track permanent fetch failures

    def _ensure_registry_loaded(self, operation_name='operation'):
        """Ensure registry data is loaded, with error handling.

        Args:
            operation_name: Name of the operation for logging

        Returns:
            bool: True if registry is loaded, False if loading failed
        """
        # Don't retry if we already know fetch failed permanently
        if self._fetch_failed:
            return False

        if not self._registry_data:
            try:
                self.fetch_registry()
            except (RegistryFetchError, RegistryParseError) as e:
                log.warning('Failed to fetch registry for %s: %s', operation_name, e)
                self._fetch_failed = True  # Mark as permanently failed
                return False
        return True

    def fetch_registry(self, use_cache=True):
        """Fetch registry from URL or cache.

        Tries multiple registry URLs in order until one succeeds.

        Args:
            use_cache: If True, try to load from cache first

        Raises:
            RegistryFetchError: If registry cannot be fetched from any URL
            RegistryParseError: If registry JSON cannot be parsed
            RegistryCacheError: If cache cannot be read (only if use_cache=True and no fallback)
        """
        # Try cache first if requested
        if use_cache and self.cache_path and Path(self.cache_path).exists():
            try:
                with open(self.cache_path, 'r') as f:
                    self._registry_data = json.load(f)
                    log.debug('Loaded registry from cache: %s', self.cache_path)
                    return
            except json.JSONDecodeError as e:
                # Cache corrupted, will fetch from URL
                log.warning('Registry cache corrupted, fetching from URL: %s', e)
            except Exception as e:
                # Cache read error, will fetch from URL
                log.warning('Failed to load registry cache, fetching from URL: %s', e)

        # Try each registry URL in order
        last_error = None
        for url_index, url in enumerate(self.registry_urls):
            try:
                log.debug('Fetching registry from %s (URL %d/%d)', url, url_index + 1, len(self.registry_urls))

                # Check if url is a local file path
                registry_path = Path(url)
                if registry_path.exists() and registry_path.is_file():
                    log.debug('Loading registry from local file: %s', url)
                    try:
                        with open(registry_path, 'r') as f:
                            self._registry_data = json.load(f)
                            self.registry_url = url  # Update to successful URL
                            break  # Success!
                    except json.JSONDecodeError as e:
                        raise RegistryParseError(url, e) from e
                    except Exception as e:
                        raise RegistryFetchError(url, e) from e
                else:
                    # Fetch from remote URL with retry logic
                    for attempt in range(REGISTRY_FETCH_MAX_RETRIES):
                        try:
                            timeout = REGISTRY_FETCH_INITIAL_TIMEOUT * (REGISTRY_FETCH_TIMEOUT_MULTIPLIER**attempt)
                            with urlopen(url, timeout=timeout) as response:
                                data = response.read()
                                self._registry_data = json.loads(data)
                                self.registry_url = url  # Update to successful URL
                                break  # Success!
                        except json.JSONDecodeError as e:
                            raise RegistryParseError(url, e) from e
                        except urllib.error.HTTPError as e:
                            # Don't retry 4xx client errors (except 404 which might mean intentional removal)
                            if 400 <= e.code < 500 and e.code != 404:
                                raise RegistryFetchError(url, e) from e
                            # For 404 or 5xx, retry or try next URL
                            if attempt < REGISTRY_FETCH_MAX_RETRIES - 1:
                                wait = REGISTRY_FETCH_RETRY_DELAY_BASE**attempt
                                log.warning(
                                    'Registry fetch failed (attempt %d/%d): %s',
                                    attempt + 1,
                                    REGISTRY_FETCH_MAX_RETRIES,
                                    e,
                                )
                                log.info('Retrying in %d seconds...', wait)
                                time.sleep(wait)
                            else:
                                raise RegistryFetchError(url, e) from e
                        except Exception as e:
                            # Retry network errors
                            if attempt < REGISTRY_FETCH_MAX_RETRIES - 1:
                                wait = REGISTRY_FETCH_RETRY_DELAY_BASE**attempt
                                log.warning(
                                    'Registry fetch failed (attempt %d/%d): %s',
                                    attempt + 1,
                                    REGISTRY_FETCH_MAX_RETRIES,
                                    e,
                                )
                                log.info('Retrying in %d seconds...', wait)
                                time.sleep(wait)
                            else:
                                raise RegistryFetchError(url, e) from e

                    # If we got here without breaking, the retries succeeded
                    if self._registry_data:
                        break  # Success!

            except (RegistryFetchError, RegistryParseError) as e:
                last_error = e
                log.warning('Failed to fetch registry from %s: %s', url, e)
                # Try next URL
                continue

        # If we exhausted all URLs without success, raise the last error
        if not self._registry_data:
            if last_error:
                raise last_error
            else:
                raise RegistryFetchError(
                    self.registry_urls[0], Exception('All registry URLs failed without specific error')
                )

        # Save to cache
        if self.cache_path:
            try:
                Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_path, 'w') as f:
                    json.dump(self._registry_data, f)
                log.debug('Saved registry to cache: %s', self.cache_path)
            except Exception as e:
                # Cache write failure is not critical, just log warning
                log.warning('Failed to save registry cache: %s', e)

    def is_blacklisted(self, url, plugin_uuid=None):
        """Check if a plugin URL or UUID is blacklisted.

        Args:
            url: Plugin repository URL
            plugin_uuid: Plugin UUID from MANIFEST

        Returns:
            tuple: (is_blacklisted, reason)
        """
        if not self._ensure_registry_loaded('blacklist check'):
            # Fail safe: if we can't fetch registry, don't block installation
            return False, None

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

    def get_blacklist_types(self):
        """Get set of blacklist entry types in the registry.

        Returns:
            set: Set of blacklist types present (e.g. {'url', 'uuid', 'url_regex'})
        """
        if not self._ensure_registry_loaded('get blacklist types'):
            return set()

        blacklist = self._registry_data.get('blacklist', [])
        types = set()
        for entry in blacklist:
            if 'uuid' in entry:
                types.add('uuid')
            if 'url' in entry:
                types.add('url')
            if 'url_regex' in entry:
                types.add('url_regex')
        return types

    def get_registry_info(self):
        """Get registry metadata.

        Returns:
            dict: Registry info with plugin_count, api_version, registry_url

        Raises:
            RuntimeError: If registry data not loaded
        """
        if not self._registry_data:
            raise RuntimeError("Registry not loaded")

        return {
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
        if not self._ensure_registry_loaded('trust level check'):
            # Fail safe: if we can't fetch registry, treat as unregistered
            return 'unregistered'

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
        if not self._ensure_registry_loaded('plugin search'):
            # Fail safe: if we can't fetch registry, return None
            return None

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

    def get_registry_id(self, url=None, uuid=None):
        """Get registry ID for a plugin by URL or UUID.

        Args:
            url: Git URL to search for
            uuid: Plugin UUID to search for

        Returns:
            str: Registry ID or None if not found
        """
        plugin = self.find_plugin(url=url, uuid=uuid)
        return plugin.get('id') if plugin else None

    def list_plugins(self, category=None, trust_level=None):
        """List plugins from registry, optionally filtered.

        Args:
            category: Filter by category (e.g., 'metadata', 'coverart')
            trust_level: Filter by trust level (e.g., 'official', 'trusted')

        Returns:
            list: List of plugin dicts
        """
        if not self._ensure_registry_loaded('plugin listing'):
            # Fail safe: if we can't fetch registry, return empty list
            return []

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
