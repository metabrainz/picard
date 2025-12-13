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
import time
import urllib.error
from urllib.request import urlopen

from picard import log
from picard.const.defaults import DEFAULT_PLUGIN_REGISTRY_URLS
from picard.git.utils import (
    normalize_git_url,
)
from picard.plugin3.installable import InstallablePlugin
from picard.plugin3.plugin import hash_string


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


# Retry configuration for registry fetch operations
REGISTRY_FETCH_MAX_RETRIES = 3
REGISTRY_FETCH_INITIAL_TIMEOUT = 10  # seconds
REGISTRY_FETCH_TIMEOUT_MULTIPLIER = 2  # exponential backoff for timeout

REGISTRY_CACHE_VERSION = 1  # Increment when cache format changes
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
        self._plugins = []  # List of RegistryPlugin objects
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

        # Process plugins if not already done
        if self._registry_data and not self._plugins:
            self._process_plugins()

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
                    data = json.load(f)
                    # Check cache version (missing version = old cache before versioning)
                    if data.get('version') != REGISTRY_CACHE_VERSION:
                        log.debug('Registry cache version mismatch or missing, fetching from URL')
                    else:
                        self._registry_data = data.get('data', {})
                        log.debug('Loaded registry from cache: %s', self.cache_path)
                        return
            except Exception as e:
                # Corrupted or old format cache - fetch from URL
                log.debug('Failed to load registry cache (corrupted or old format): %s', e)

        # Try each registry URL in order
        last_error = None
        for url_index, url in enumerate(self.registry_urls):
            try:
                log.debug('Fetching registry from %s (URL %d/%d)', url, url_index + 1, len(self.registry_urls))

                # Check if url is a local file path or file:// URL
                file_path = url
                if url.startswith('file://'):
                    file_path = url[7:]  # Remove file:// prefix

                registry_path = Path(file_path)
                if registry_path.exists() and registry_path.is_file():
                    log.debug('Loading registry from local file: %s', file_path)
                    try:
                        with open(registry_path, 'rb') as f:
                            self._registry_data = tomllib.load(f)
                        self.registry_url = url  # Update to successful URL
                        break  # Success!
                    except tomllib.TOMLDecodeError as e:
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
                                self._registry_data = tomllib.loads(data.decode('utf-8'))
                                self.registry_url = url  # Update to successful URL
                                break  # Success!
                        except tomllib.TOMLDecodeError as e:
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
                # Wrap registry data with version
                data = {'version': REGISTRY_CACHE_VERSION, 'data': self._registry_data}
                with open(self.cache_path, 'w') as f:
                    json.dump(data, f)
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
            'plugin_count': len(self._plugins),
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

        for plugin in self._plugins:
            plugin_url = normalize_git_url(plugin.git_url or '')
            if plugin_url == normalized_url:
                return plugin.trust_level

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

        # First pass: search by current values (fast path)
        for plugin in self._plugins:
            if plugin_id and plugin.id == plugin_id:
                return plugin
            if uuid and plugin.uuid == uuid:
                return plugin
            if normalized_url:
                plugin_url = normalize_git_url(plugin.git_url or '')
                if plugin_url == normalized_url:
                    return plugin

        # Second pass: search redirects (only if not found above)
        if normalized_url or uuid:
            for plugin in self._plugins:
                # Check URL redirects
                if normalized_url and plugin.redirect_from:
                    for old_url in plugin.redirect_from:
                        old_url_normalized = normalize_git_url(old_url)
                        if old_url_normalized == normalized_url:
                            log.info('Found plugin via URL redirect: %s -> %s', url, plugin.git_url)
                            return plugin

                # Check UUID redirects
                if uuid and plugin.redirect_from_uuid:
                    if uuid in plugin.redirect_from_uuid:
                        log.info('Found plugin via UUID redirect: %s -> %s', uuid, plugin.uuid)
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
        return plugin.id if plugin else None

    def list_plugins(self, category=None, trust_level=None):
        """List plugins from registry, optionally filtered.

        Args:
            category: Filter by category (e.g., 'metadata', 'coverart')
            trust_level: Filter by trust level (e.g., 'official', 'trusted')

        Returns:
            list: List of RegistryPlugin objects
        """
        if not self._ensure_registry_loaded('plugin listing'):
            # Fail safe: if we can't fetch registry, return empty list
            return []

        result = []

        for plugin in self._plugins:
            # Filter by trust level
            if trust_level and plugin.trust_level != trust_level:
                continue

            # Filter by category
            if category:
                if category not in plugin.categories:
                    continue

            result.append(plugin)

        return result

    @property
    def plugins(self):
        """Get list of all RegistryPlugin objects."""
        if not self._ensure_registry_loaded('plugin access'):
            return []
        return self._plugins

    def _process_plugins(self):
        """Process raw plugin data into RegistryPlugin objects."""
        self._plugins = []
        if self._registry_data and 'plugins' in self._registry_data:
            for plugin_data in self._registry_data['plugins']:
                try:
                    self._plugins.append(RegistryPlugin(plugin_data))
                except Exception as e:
                    log.warning('Failed to process plugin %s: %s', plugin_data.get('id', 'unknown'), e)


class RegistryPlugin(InstallablePlugin):
    """Wrapper for registry plugin data with i18n support."""

    def __init__(self, data):
        self._data = data
        # Call parent constructor with basic values
        super().__init__(source_url=data.get('git_url'), plugin_uuid=data.get('uuid'), name=data.get('name', ''))

    def get_display_name(self):
        """Get display name for this plugin."""
        return self.name_i18n() or self.id

    def get_install_url(self):
        """Get URL to install this plugin from."""
        return self.source_url

    def _get_current_locale(self):
        """Get current locale from Picard's UI language setting or system locale."""
        from picard.config import get_config

        config = get_config()
        if config is None:
            return 'en'  # Default fallback
        locale = config.setting['ui_language']
        if not locale:
            try:
                from PyQt6 import QtCore

                locale = QtCore.QLocale.system().name()
            except ImportError:
                locale = 'en'  # Fallback if PyQt6 not available
        return locale

    def name_i18n(self, locale=None):
        """Get plugin name with automatic locale detection."""
        if locale is None:
            locale = self._get_current_locale()

        i18n = self._data.get('name_i18n') or {}
        if locale in i18n:
            return i18n[locale]
        # Try language without region
        lang = locale.split('_')[0]
        if lang in i18n:
            return i18n[lang]
        return self._data.get('name', '')

    def description_i18n(self, locale=None):
        """Get description with automatic locale detection."""
        if locale is None:
            locale = self._get_current_locale()

        i18n = self._data.get('description_i18n') or {}
        if locale in i18n:
            return i18n[locale]
        # Try language without region
        lang = locale.split('_')[0]
        if lang in i18n:
            return i18n[lang]
        return self._data.get('description', '')

    @property
    def categories(self):
        """Get plugin categories."""
        return self._data.get('categories', [])

    @property
    def trust_level(self):
        """Get plugin trust level."""
        return self._data.get('trust_level', 'community')

    @property
    def uuid(self):
        """Get plugin UUID."""
        return self._data.get('uuid')

    @property
    def id(self):
        """Get plugin ID."""
        return self._data.get('id', '')

    @property
    def git_url(self):
        """Get plugin git URL."""
        return self._data.get('git_url')

    @property
    def versioning_scheme(self):
        """Get plugin versioning scheme."""
        return self._data.get('versioning_scheme')

    @property
    def refs(self):
        """Get plugin refs."""
        return self._data.get('refs', [{'name': 'main'}])

    @property
    def authors(self):
        """Get plugin authors."""
        return self._data.get('authors', [])

    @property
    def maintainers(self):
        """Get plugin maintainers."""
        return self._data.get('maintainers', [])

    @property
    def added_at(self):
        """Get plugin added timestamp."""
        return self._data.get('added_at')

    @property
    def updated_at(self):
        """Get plugin updated timestamp."""
        return self._data.get('updated_at')

    @property
    def redirect_from(self):
        """Get plugin redirect URLs."""
        return self._data.get('redirect_from', [])

    @property
    def redirect_from_uuid(self):
        """Get plugin redirect UUIDs."""
        return self._data.get('redirect_from_uuid', [])

    def get(self, key, default=None):
        """Delegate to underlying data dict."""
        return self._data.get(key, default)
