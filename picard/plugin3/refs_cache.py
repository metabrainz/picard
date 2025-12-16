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

"""Git refs caching and version tag management."""

import json
from pathlib import Path
import re
import time

from picard import log
from picard.const.appdirs import cache_folder
from picard.git.factory import git_backend
from picard.version import Version


REFS_CACHE_FILE = 'plugin_refs_cache.json'
REFS_CACHE_TTL = 3600  # 1 hour in seconds
REFS_CACHE_VERSION = 2  # Increment when cache format changes


class RefsCache:
    """Manages caching of git refs and version tags."""

    def __init__(self, registry):
        self._registry = registry
        self._cache = None

    def get_cache_path(self):
        """Get path to refs cache file."""

        # Use same cache directory as registry
        if hasattr(self._registry, 'cache_path') and self._registry.cache_path:
            cache_dir = Path(self._registry.cache_path).parent
        else:
            # Fallback to default cache directory
            cache_dir = cache_folder()

        return cache_dir / REFS_CACHE_FILE

    def clear_cache(self):
        """Clear both in-memory and on-disk cache."""
        cache_path = self.get_cache_path()
        if cache_path.exists():
            try:
                cache_path.unlink()
                log.debug('Cleared refs cache file: %s', cache_path)
            except Exception as e:
                log.warning('Failed to delete refs cache file: %s', e)
        self._cache = None

    def load_cache(self):
        """Load refs cache from disk.

        Returns:
            dict: Cache data or empty dict if not found/invalid
        """
        if self._cache is not None:
            return self._cache

        cache_path = self.get_cache_path()
        if not cache_path.exists():
            self._cache = {}
            return self._cache

        try:
            with open(cache_path, encoding='utf-8') as f:
                data = json.load(f)
                # Check cache version (missing version = old cache before versioning)
                if data.get('version') != REFS_CACHE_VERSION:
                    log.debug('Refs cache version mismatch or missing, invalidating cache')
                    self._cache = {}
                    return self._cache
                self._cache = data.get('data', {})
                log.debug('Loaded refs cache from %s', cache_path)
                return self._cache
        except Exception as e:
            # Corrupted or old format cache - treat as invalid
            log.debug('Failed to load refs cache (corrupted or old format): %s', e)
            self._cache = {}
            return self._cache

    def save_cache(self, cache):
        """Save refs cache to disk.

        Args:
            cache: Cache data to save
        """
        cache_path = self.get_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Wrap cache data with version
            data = {'version': REFS_CACHE_VERSION, 'data': cache}
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self._cache = cache
            log.debug('Saved refs cache to %s', cache_path)
        except Exception as e:
            log.error('Failed to save refs cache: %s', e)

    def get_cached_tags(self, url, versioning_scheme, allow_expired=False):
        """Get cached tags if valid (not expired).

        Args:
            url: Git repository URL
            versioning_scheme: Versioning scheme
            allow_expired: If True, return expired cache as fallback

        Returns:
            list: Cached tags or None if cache miss/expired
        """

        cache = self.load_cache()

        if url not in cache:
            return None

        if versioning_scheme not in cache[url]:
            return None

        entry = cache[url][versioning_scheme]
        timestamp = entry.get('timestamp', 0)
        tags = entry.get('tags', [])

        # Check if expired
        is_expired = time.time() - timestamp > REFS_CACHE_TTL

        if is_expired and not allow_expired:
            return None

        if is_expired:
            log.debug('Using expired cache for %s (%s): %d tags', url, versioning_scheme, len(tags))
        else:
            log.debug('Using cached tags for %s (%s): %d tags', url, versioning_scheme, len(tags))

        return tags

    def cache_tags(self, url, versioning_scheme, tags):
        """Cache tags for url+scheme.

        Args:
            url: Git repository URL
            versioning_scheme: Versioning scheme
            tags: List of tags to cache
        """

        cache = self.load_cache()

        if url not in cache:
            cache[url] = {}

        cache[url][versioning_scheme] = {'tags': tags, 'timestamp': int(time.time())}

        self.save_cache(cache)
        log.debug('Cached %d tags for %s (%s)', len(tags), url, versioning_scheme)

    def get_cached_all_refs(self, url, allow_expired=False):
        """Get cached all refs (branches and tags) if valid.

        Args:
            url: Git repository URL
            allow_expired: If True, return expired cache

        Returns:
            dict with branches and tags, or None if not cached/expired
        """

        cache = self.load_cache()

        if url not in cache or 'all_refs' not in cache[url]:
            return None

        entry = cache[url]['all_refs']
        timestamp = entry.get('timestamp', 0)
        age = int(time.time()) - timestamp

        # Check if cache is expired
        if age > REFS_CACHE_TTL and not allow_expired:
            log.debug('Refs cache expired for %s (age: %d seconds)', url, age)
            return None

        refs = entry.get('refs')
        if refs:
            # Validate cache format - reject old format (list of strings)
            branches = refs.get('branches', [])
            tags = refs.get('tags', [])

            # Check if new format (list of dicts with 'name' and 'commit')
            if branches and isinstance(branches[0], str):
                log.debug('Refs cache has old format for %s, invalidating', url)
                return None
            if tags and isinstance(tags[0], str):
                log.debug('Refs cache has old format for %s, invalidating', url)
                return None

            log.debug(
                'Using cached refs for %s: %d branches, %d tags',
                url,
                len(branches),
                len(tags),
            )

        return refs

    def cache_all_refs(self, url, refs):
        """Cache all refs (branches and tags) for url.

        Args:
            url: Git repository URL
            refs: Dict with 'branches' and 'tags' lists
        """

        cache = self.load_cache()

        if url not in cache:
            cache[url] = {}

        cache[url]['all_refs'] = {'refs': refs, 'timestamp': int(time.time())}

        self.save_cache(cache)
        log.debug(
            'Cached refs for %s: %d branches, %d tags', url, len(refs.get('branches', [])), len(refs.get('tags', []))
        )

    def cleanup_cache(self):
        """Remove cache entries for URLs no longer in registry.

        This should be called after registry refresh to clean up entries
        for plugins that were removed or had their URLs changed.
        """
        cache = self.load_cache()
        if not cache:
            return

        # Get all URLs from registry
        registry_urls = set()
        for plugin in self._registry.list_plugins():
            url = plugin.git_url
            if url:
                registry_urls.add(url)

        # Remove entries not in registry
        urls_to_remove = []
        for url in cache:
            if url not in registry_urls:
                urls_to_remove.append(url)

        if urls_to_remove:
            for url in urls_to_remove:
                del cache[url]
            self.save_cache(cache)
            log.debug('Cleaned up %d stale cache entries', len(urls_to_remove))

    def parse_versioning_scheme(self, versioning_scheme):
        """Parse versioning scheme into compiled regex pattern.

        Args:
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            re.Pattern: Compiled regex pattern or None if unknown/invalid scheme
        """
        if versioning_scheme == 'semver':
            pattern = r'^\D*\d+\.\d+\.\d+$'
        elif versioning_scheme == 'calver':
            pattern = r'^\d{4}\.\d{2}\.\d{2}$'
        elif versioning_scheme.startswith('regex:'):
            pattern = versioning_scheme[6:]
        else:
            log.warning('Unknown versioning scheme: %s', versioning_scheme)
            return None

        try:
            return re.compile(pattern)
        except re.error as e:
            log.error('Invalid regex pattern in versioning scheme %s: %s', versioning_scheme, e)
            return None

    def filter_tags(self, ref_names, pattern):
        """Filter tag names by pattern.

        Args:
            ref_names: Iterator of ref names (e.g., 'refs/tags/v1.0.0')
            pattern: Compiled regex pattern to match

        Returns:
            list: Filtered tag names (without refs/tags/ prefix)
        """
        tags = []
        for ref_name in ref_names:
            # Handle both string refs and RemoteHead objects
            name = ref_name.name if hasattr(ref_name, 'name') else ref_name

            if name.startswith('refs/tags/'):
                tag = name[10:]
                if tag.endswith('^{}'):
                    continue
                if pattern.match(tag):
                    tags.append(tag)
        return tags

    def sort_tags(self, tags, versioning_scheme):
        """Sort tags based on versioning scheme.

        Args:
            tags: List of tag names
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            list: Sorted tags (newest first)
        """

        # Strip any non-digit prefix for version comparison
        def strip_prefix(tag):
            match = re.search(r'\d', tag)
            return tag[match.start() :] if match else tag

        if versioning_scheme == 'semver':
            # Use picard.version for proper semver sorting
            try:
                return sorted(tags, key=lambda t: Version.from_string(strip_prefix(t)), reverse=True)
            except Exception as e:
                log.warning('Failed to parse semver tags: %s', e)
                return sorted(tags, key=strip_prefix, reverse=True)
        elif versioning_scheme == 'calver':
            # CalVer: YYYY.MM.DD format, sort by stripped version (newest first)
            return sorted(tags, key=strip_prefix, reverse=True)
        else:
            # Custom regex: try version parsing, fall back to natural sort
            def sort_key(tag):
                stripped = strip_prefix(tag)
                try:
                    return (0, Version.from_string(stripped))
                except Exception:
                    # Natural sort: split into text and number parts
                    parts = []
                    for part in re.split(r'(\d+)', stripped):
                        if part.isdigit():
                            parts.append((0, int(part)))
                        else:
                            parts.append((1, part))
                    return (1, parts)

            return sorted(tags, key=sort_key, reverse=True)

    def update_cache_from_local_repo(self, repo_path, url, versioning_scheme):
        """Update version tag cache from local repository.

        Args:
            repo_path: Path to local git repository
            url: Git repository URL (for cache key)
            versioning_scheme: Versioning scheme to filter tags

        Returns:
            list: Filtered tags or empty list
        """
        # Parse versioning scheme
        pattern = self.parse_versioning_scheme(versioning_scheme)
        if not pattern:
            return []

        try:
            backend = git_backend()
            repo = backend.create_repository(repo_path)

            # Filter and sort tags
            tags = self.filter_tags(repo.get_references(), pattern)
            tags = self.sort_tags(tags, versioning_scheme)

            # Update cache
            if tags:
                self.cache_tags(url, versioning_scheme, tags)
                log.debug('Updated cache from local repo: %d tags for %s', len(tags), url)

            return tags

        except Exception as e:
            log.debug('Failed to update cache from local repo: %s', e)
            return []

    def cache_update_status(self, plugin_id, has_update, current_ref=None):
        """Cache update status for a plugin."""
        cache = self.load_cache()
        if 'update_status' not in cache:
            cache['update_status'] = {}

        cache['update_status'][plugin_id] = {
            'has_update': has_update,
            'current_ref': current_ref,
            'timestamp': time.time(),
        }
        self.save_cache(cache)

    def get_cached_update_status(self, plugin_id, current_ref=None, ttl=REFS_CACHE_TTL):
        """Get cached update status for a plugin."""
        cache = self.load_cache()
        update_cache = cache.get('update_status', {})

        if plugin_id not in update_cache:
            return None

        entry = update_cache[plugin_id]

        # Check if ref has changed (invalidates cache)
        if current_ref and entry.get('current_ref') != current_ref:
            return None

        if time.time() - entry['timestamp'] > ttl:
            return None  # Expired

        return entry['has_update']

    def cache_ref_items_for_commit(self, plugin_uuid, commit_id, ref_items):
        """Cache RefItems for a specific commit.

        Args:
            plugin_uuid: Plugin UUID
            commit_id: Full commit ID
            ref_items: List of RefItem objects for this commit
        """
        cache = self.load_cache()
        if 'ref_items' not in cache:
            cache['ref_items'] = {}
        if plugin_uuid not in cache['ref_items']:
            cache['ref_items'][plugin_uuid] = {}

        # Store RefItems as serializable dicts
        cache['ref_items'][plugin_uuid][commit_id] = [item.to_dict() for item in ref_items]
        self.save_cache(cache)

    def get_ref_items_for_commit(self, plugin_uuid, commit_id):
        """Get RefItems for a specific commit.

        Args:
            plugin_uuid: Plugin UUID
            commit_id: Full commit ID

        Returns:
            List of RefItem objects, or empty list if not found
        """
        from picard.git.utils import RefItem

        cache = self.load_cache()
        ref_items_cache = cache.get('ref_items', {})
        plugin_cache = ref_items_cache.get(plugin_uuid, {})

        if commit_id not in plugin_cache:
            return []

        # Reconstruct RefItem objects from cached data
        return [RefItem.from_dict(item) for item in plugin_cache[commit_id]]

    def add_ref_item_to_commit(self, plugin_uuid, commit_id, ref_item):
        """Add a single RefItem to a commit's cache.

        Args:
            plugin_uuid: Plugin UUID
            commit_id: Full commit ID
            ref_item: RefItem object to add
        """
        existing_items = self.get_ref_items_for_commit(plugin_uuid, commit_id)

        # Check if this RefItem already exists (by name)
        for existing in existing_items:
            if existing.name == ref_item.name:
                return  # Already exists

        existing_items.append(ref_item)
        self.cache_ref_items_for_commit(plugin_uuid, commit_id, existing_items)
