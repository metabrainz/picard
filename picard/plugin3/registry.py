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

from PyQt6 import QtCore
from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkRequest

from picard import log
from picard.config import get_config
from picard.const.defaults import DEFAULT_PLUGIN_REGISTRY_URLS
from picard.git.utils import normalize_git_url
from picard.i18n import sort_key
from picard.plugin3.installable import InstallablePlugin
from picard.plugin3.plugin import hash_string


try:
    import tomllib  # type: ignore[unresolved-import]
except (ImportError, ModuleNotFoundError):
    import tomli as tomllib  # type: ignore[no-redef]


REGISTRY_CACHE_VERSION = 1  # Increment when cache format changes


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

        Note: This loads from cache or local files (synchronous only).
        For remote fetching, use fetch_registry() with a callback.

        Args:
            operation_name: Name of the operation for logging

        Returns:
            bool: True if registry is loaded, False if loading failed
        """
        # Don't retry if we already know fetch failed permanently
        if self._fetch_failed:
            return False

        if not self._registry_data:
            # Try loading from cache first
            if self._load_from_cache():
                return True

            # Try loading from local file if URL is local
            if not self._load_from_local_file(self.registry_urls[0]):
                log.debug('Registry not loaded for %s (no cache or local file available)', operation_name)
                return False

        # Process plugins if not already done
        if self._registry_data and not self._plugins:
            self._process_plugins()

        return True

    def _load_from_local_file(self, url):
        """Load registry from local file if URL is a file path.

        Args:
            url: URL to check and load from

        Returns:
            bool: True if loaded from local file, False otherwise
        """
        file_path = url[7:] if url.startswith('file://') else url
        registry_path = Path(file_path)

        if not registry_path.exists() or not registry_path.is_file():
            return False

        try:
            with open(registry_path, 'rb') as f:
                self._registry_data = tomllib.load(f)
            self.registry_url = url
            self._process_plugins()
            log.debug('Loaded registry from local file: %s', file_path)
            return True
        except Exception as e:
            log.debug('Failed to load registry from local file %s: %s', file_path, e)
            return False

    def _load_from_cache(self):
        """Load registry from cache if available.

        Returns:
            bool: True if loaded from cache, False otherwise
        """
        if not self.cache_path or not Path(self.cache_path).exists():
            return False

        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
                # Check cache version (missing version = old cache before versioning)
                if data.get('version') == REGISTRY_CACHE_VERSION:
                    self._registry_data = data.get('data', {})
                    self._process_plugins()
                    log.debug('Loaded registry from cache: %s', self.cache_path)
                    return True
        except Exception as e:
            # Corrupted or old format cache - fetch from URL
            log.debug('Failed to load registry cache: %s', e)

        return False

    def fetch_registry(self, use_cache=True, callback=None):
        """Fetch registry from URL or cache.

        Args:
            use_cache: If True, try to load from cache first
            callback: Optional callback(success, error) called when complete.
                     If None, raises exceptions on error (sync mode, local files only)

        Raises:
            RegistryFetchError: If registry cannot be fetched (sync mode only)
            RegistryParseError: If registry cannot be parsed (sync mode only)
        """
        # Try cache first if requested
        if use_cache and self._load_from_cache():
            if callback:
                callback(True, None)
            return

        # Try each registry URL in order
        self._try_next_url(0, callback)

    def _try_next_url(self, url_index, callback, last_error=None):
        """Try fetching from the next URL in the list.

        Args:
            url_index: Index of URL to try
            callback: Callback to call when done
            last_error: Last error encountered (for final error message)
        """
        if url_index >= len(self.registry_urls):
            # All URLs failed - use last error if available
            if last_error:
                error = last_error
            else:
                error = RegistryFetchError(self.registry_urls[0], Exception('All registry URLs failed'))
            if callback:
                callback(False, error)
            return

        url = self.registry_urls[url_index]
        log.debug('Trying registry URL %d/%d: %s', url_index + 1, len(self.registry_urls), url)

        # Try local file first
        if self._load_from_local_file(url):
            if callback:
                callback(True, None)
            return

        # Remote URL - use WebService (async)
        def on_fetch_complete(success, error):
            if success:
                if callback:
                    callback(True, None)
            else:
                # Parse errors are fatal - don't try next URL
                if isinstance(error, RegistryParseError):
                    if callback:
                        callback(False, error)
                else:
                    log.warning('Failed to fetch registry from %s: %s', url, error)
                    # Try next URL for network errors, passing along the error
                    self._try_next_url(url_index + 1, callback, last_error=error)

        self._fetch_remote_registry(url, on_fetch_complete)

    def _fetch_remote_registry(self, url, callback):
        """Fetch registry from remote URL using WebService.

        Args:
            url: URL to fetch from
            callback: callback(success, error) called when complete
        """
        tagger = QtCore.QCoreApplication.instance()
        if not tagger or not hasattr(tagger, 'webservice'):
            error = RegistryFetchError(url, Exception('WebService not available'))
            if callback:
                callback(False, error)
            return

        def handler(response, reply, error):
            if error:
                fetch_error = RegistryFetchError(url, error)
                if callback:
                    callback(False, fetch_error)
            else:
                try:
                    self._registry_data = tomllib.loads(response.decode('utf-8'))
                    self.registry_url = url
                    self._process_plugins()
                    self._save_cache()
                    if callback:
                        callback(True, None)
                except tomllib.TOMLDecodeError as e:
                    parse_error = RegistryParseError(url, e)
                    if callback:
                        callback(False, parse_error)
                except Exception as e:
                    fetch_error = RegistryFetchError(url, e)
                    if callback:
                        callback(False, fetch_error)

        tagger.webservice.get_url(
            url=QUrl(url),
            handler=handler,
            cacheloadcontrol=QNetworkRequest.CacheLoadControl.PreferCache,
            parse_response_type=None,  # Don't parse, we'll handle TOML ourselves
        )

    def _save_cache(self):
        """Save registry data to cache file."""
        if self.cache_path and self._registry_data:
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

        # Additional safety check
        if not self._registry_data:
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
        if not self._registry_data:
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

    def is_registry_loaded(self):
        """Check if registry data is loaded."""
        return bool(self._registry_data)

    def get_raw_registry_data(self):
        """Get raw registry data for async operations."""
        return self._registry_data

    def set_raw_registry_data(self, data):
        """Set raw registry data and process plugins."""
        self._registry_data = data
        self._process_plugins()

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

    def __getitem__(self, key):
        """Prevent dict-style access to enforce object-oriented interface."""
        raise TypeError(f"Use property access instead of dict access. Use .{key} instead of ['{key}']")

    def get_display_name(self):
        """Get display name for this plugin."""
        return self.name_i18n() or self.id

    def get_install_url(self):
        """Get URL to install this plugin from."""
        return self.source_url

    def _get_current_locale(self):
        """Get current locale from Picard's UI language setting or system locale."""
        config = get_config()
        if config is None:
            return 'en'  # Default fallback
        locale = config.setting['ui_language']
        if not locale:
            locale = QtCore.QLocale.system().name()
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

    def __lt__(self, other):
        return sort_key(self.name_i18n()) < sort_key(other.name_i18n())
