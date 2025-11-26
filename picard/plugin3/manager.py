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

import os
from pathlib import Path
import re
import shutil
from typing import List

from picard import (
    api_versions_tuple,
    log,
)
from picard.plugin3.plugin import (
    Plugin,
    PluginSourceGit,
    short_commit_id,
)


def sanitize_plugin_name(name: str) -> str:
    """Sanitize plugin name for use in directory name.

    Args:
        name: Plugin name from MANIFEST

    Returns:
        Sanitized name (lowercase, alphanumeric + underscore)
    """
    # Convert to lowercase and replace non-alphanumeric with underscore
    sanitized = re.sub(r'[^a-z0-9]+', '_', name.lower())
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Limit length
    return sanitized[:50] if sanitized else 'plugin'


def get_plugin_directory_name(manifest) -> str:
    """Get plugin directory name from manifest (sanitized name + UUID prefix).

    Args:
        manifest: PluginManifest instance

    Returns:
        Directory name: <sanitized_name>_<uuid_prefix>
    """
    sanitized_name = sanitize_plugin_name(manifest.name())
    uuid_prefix = manifest.uuid[:8] if manifest.uuid else 'no_uuid'
    return f'{sanitized_name}_{uuid_prefix}'


class PluginManager:
    """Installs, loads and updates plugins from multiple plugin directories."""

    _primary_plugin_dir: Path = None
    _plugin_dirs: List[Path] = []
    _plugins: List[Plugin] = []

    def __init__(self, tagger=None):
        from picard.tagger import Tagger

        self._tagger: Tagger | None = tagger
        self._enabled_plugins = set()
        self._load_config()

        # Initialize registry for blacklist checking
        from picard.plugin3.registry import PluginRegistry

        cache_path = None
        if self._primary_plugin_dir:
            cache_path = self._primary_plugin_dir.parent / 'registry_cache.json'
        self._registry = PluginRegistry(cache_path=cache_path)

    @property
    def plugins(self):
        return self._plugins

    def add_directory(self, dir_path: str, primary: bool = False) -> None:
        dir_path = Path(os.path.normpath(dir_path))
        if dir_path in self._plugin_dirs:
            log.warning('Plugin directory %s already registered', dir_path)
            return

        log.debug('Registering plugin directory %s', dir_path)
        if not dir_path.exists():
            os.makedirs(dir_path)

        for entry in dir_path.iterdir():
            if entry.is_dir():
                plugin = self._load_plugin(dir_path, entry.name)
                if plugin:
                    log.debug('Found plugin %s in %s', plugin.name, plugin.local_path)
                    self._plugins.append(plugin)

        self._plugin_dirs.append(dir_path)
        if primary:
            self._primary_plugin_dir = dir_path

    def install_plugin(self, url, ref=None, reinstall=False, force_blacklisted=False):
        """Install a plugin from a git URL or local directory.

        Args:
            url: Git repository URL or local directory path
            ref: Git ref (branch/tag/commit) to checkout (ignored for local paths)
            reinstall: If True, reinstall even if already exists
            force_blacklisted: If True, bypass blacklist check (dangerous!)
        """
        from pathlib import Path
        import shutil
        import tempfile

        from picard.plugin3.registry import get_local_repository_path

        # Check blacklist before installing
        if not force_blacklisted:
            is_blacklisted, reason = self._registry.is_blacklisted(url)
            if is_blacklisted:
                raise ValueError(f'Plugin is blacklisted: {reason}')

        # Check if url is a local directory
        local_path = get_local_repository_path(url)
        if local_path:
            return self._install_from_local_directory(local_path, reinstall, force_blacklisted, ref)

        # Handle git URL
        # Use shorter temp name to avoid truncation
        import hashlib

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        temp_path = Path(tempfile.gettempdir()) / f'picard-plugin-{url_hash}'

        try:
            # Clone to temporary location
            source = PluginSourceGit(url, ref)
            commit_id = source.sync(temp_path)

            # Read MANIFEST to get plugin ID
            manifest_path = temp_path / 'MANIFEST.toml'
            if not manifest_path.exists():
                raise ValueError(f'No MANIFEST.toml found in {url}')

            with open(manifest_path, 'rb') as f:
                from picard.plugin3.manifest import PluginManifest

                manifest = PluginManifest('temp', f)

            # Validate manifest
            errors = manifest.validate()
            if errors:
                if isinstance(errors, list):
                    error_list = '\n  '.join(errors)
                else:
                    error_list = str(errors)
                raise ValueError(f'Invalid MANIFEST.toml:\n  {error_list}')

            # Generate plugin directory name from sanitized name + UUID
            plugin_id = get_plugin_directory_name(manifest)

            # Check blacklist again with UUID
            if not force_blacklisted:
                is_blacklisted, reason = self._registry.is_blacklisted(url, manifest.uuid)
                if is_blacklisted:
                    raise ValueError(f'Plugin is blacklisted: {reason}')

            final_path = self._primary_plugin_dir / plugin_id

            # Check if already installed
            if final_path.exists() and not reinstall:
                raise ValueError(f'Plugin {plugin_id} is already installed. Use --reinstall to force.')

            # Remove existing if reinstalling
            if final_path.exists():
                import shutil

                shutil.rmtree(final_path)

            # Move from temp to final location
            import shutil

            shutil.move(str(temp_path), str(final_path))

            # Store plugin metadata
            self._save_plugin_metadata(plugin_id, url, source.resolved_ref, commit_id)

            # Add newly installed plugin to the plugins list
            plugin = Plugin(self._primary_plugin_dir, plugin_id)
            self._plugins.append(plugin)

            return plugin_id

        except Exception:
            # Clean up temp directory on failure
            if temp_path.exists():
                import gc
                import shutil

                # Force garbage collection to release file handles on Windows
                gc.collect()
                shutil.rmtree(temp_path, ignore_errors=True)
            raise

    def _install_from_local_directory(self, local_path: Path, reinstall=False, force_blacklisted=False, ref=None):
        """Install a plugin from a local directory.

        Args:
            local_path: Path to local plugin directory
            reinstall: If True, reinstall even if already exists
            force_blacklisted: If True, bypass blacklist check (dangerous!)
            ref: Git ref to checkout if local_path is a git repository

        Returns:
            str: Plugin ID
        """
        import hashlib
        import shutil
        import tempfile

        # Check if local directory is a git repository
        is_git_repo = (local_path / '.git').exists()

        if is_git_repo:
            # Check if source repository has uncommitted changes
            try:
                import pygit2

                source_repo = pygit2.Repository(str(local_path))
                if source_repo.status():
                    log.warning('Installing from local repository with uncommitted changes: %s', local_path)
            except Exception:
                pass  # Ignore errors checking status

            # Use git operations to get ref and commit info
            url_hash = hashlib.md5(str(local_path).encode()).hexdigest()[:8]
            temp_path = Path(tempfile.gettempdir()) / f'picard-plugin-{url_hash}'

            try:
                source = PluginSourceGit(str(local_path), ref)
                commit_id = source.sync(temp_path)
                install_path = temp_path
                ref_to_save = source.resolved_ref
                commit_to_save = commit_id
            except Exception:
                # Clean up temp directory on failure
                if temp_path.exists():
                    import gc

                    gc.collect()
                    shutil.rmtree(temp_path, ignore_errors=True)
                raise
        else:
            # Direct copy for non-git directories
            install_path = local_path
            ref_to_save = ''
            commit_to_save = ''

        # Read MANIFEST to get plugin ID
        manifest_path = install_path / 'MANIFEST.toml'
        if not manifest_path.exists():
            raise ValueError(f'No MANIFEST.toml found in {local_path}')

        with open(manifest_path, 'rb') as f:
            from picard.plugin3.manifest import PluginManifest

            manifest = PluginManifest('temp', f)

        # Validate manifest
        errors = manifest.validate()
        if errors:
            if isinstance(errors, list):
                error_list = '\n  '.join(errors)
            else:
                error_list = str(errors)
            raise ValueError(f'Invalid MANIFEST.toml:\n  {error_list}')

        # Generate plugin directory name from sanitized name + UUID
        plugin_id = get_plugin_directory_name(manifest)
        final_path = self._primary_plugin_dir / plugin_id

        # Check if already installed
        if final_path.exists() and not reinstall:
            raise ValueError(f'Plugin {plugin_id} is already installed. Use --reinstall to force.')

        # Remove existing if reinstalling
        if final_path.exists():
            shutil.rmtree(final_path)

        # Copy to plugin directory
        if is_git_repo:
            # Move from temp location (git repo was cloned to temp)
            shutil.move(str(install_path), str(final_path))
        else:
            # Copy from local directory (non-git)
            shutil.copytree(install_path, final_path)

        # Store metadata
        self._save_plugin_metadata(plugin_id, str(local_path), ref_to_save, commit_to_save)

        # Add newly installed plugin to the plugins list
        plugin = Plugin(self._primary_plugin_dir, plugin_id)
        self._plugins.append(plugin)

        log.info('Plugin %s installed from local directory %s', plugin_id, local_path)
        return plugin_id

    def switch_ref(self, plugin: Plugin, ref: str):
        """Switch plugin to a different git ref (branch/tag/commit)."""
        metadata = self._get_plugin_metadata(plugin.name)
        if not metadata or 'url' not in metadata:
            raise ValueError(f'Plugin {plugin.name} has no stored URL, cannot switch ref')

        old_ref = metadata.get('ref', 'main')
        old_commit = metadata.get('commit', 'unknown')

        source = PluginSourceGit(metadata['url'], ref)
        new_commit = source.sync(plugin.local_path)

        # Reload manifest to get potentially new version
        plugin.read_manifest()

        # Update metadata with new ref
        self._save_plugin_metadata(plugin.name, metadata['url'], ref, new_commit)

        return old_ref, ref, old_commit, new_commit

    def update_plugin(self, plugin: Plugin):
        """Update a single plugin to latest version."""
        metadata = self._get_plugin_metadata(plugin.name)
        if not metadata or 'url' not in metadata:
            raise ValueError(f'Plugin {plugin.name} has no stored URL, cannot update')

        old_version = plugin.manifest.version if plugin.manifest else 'unknown'

        source = PluginSourceGit(metadata['url'], metadata.get('ref'))
        old_commit, new_commit = source.update(plugin.local_path)

        # Reload manifest to get new version
        plugin.read_manifest()
        new_version = plugin.manifest.version if plugin.manifest else 'unknown'

        # Update metadata
        self._save_plugin_metadata(plugin.name, metadata['url'], metadata.get('ref'), new_commit)

        return old_version, new_version, old_commit, new_commit

    def update_all_plugins(self):
        """Update all installed plugins."""
        results = []
        for plugin in self._plugins:
            try:
                old_ver, new_ver, old_commit, new_commit = self.update_plugin(plugin)
                results.append((plugin.name, True, old_ver, new_ver, old_commit, new_commit, None))
            except Exception as e:
                results.append((plugin.name, False, None, None, None, None, str(e)))
        return results

    def check_updates(self):
        """Check which plugins have updates available without installing."""
        updates = []
        for plugin in self._plugins:
            metadata = self._get_plugin_metadata(plugin.name)
            if not metadata or 'url' not in metadata:
                continue

            try:
                import pygit2

                repo = pygit2.Repository(plugin.local_path.absolute())
                current_commit = str(repo.head.target)

                # Fetch without updating
                for remote in repo.remotes:
                    from picard.plugin3.plugin import GitRemoteCallbacks

                    remote.fetch(callbacks=GitRemoteCallbacks())

                ref = metadata.get('ref', 'main')
                latest_commit = str(repo.revparse_single(ref).id)
                repo.free()

                if current_commit != latest_commit:
                    updates.append((plugin.name, short_commit_id(current_commit), short_commit_id(latest_commit)))
            except Exception:
                pass

        return updates

    def uninstall_plugin(self, plugin: Plugin, purge=False):
        """Uninstall a plugin.

        Args:
            plugin: Plugin to uninstall
            purge: If True, also remove plugin configuration
        """
        self.disable_plugin(plugin)
        plugin_path = plugin.local_path
        if plugin_path.is_relative_to(self._primary_plugin_dir):
            if os.path.islink(plugin_path):
                log.debug("Removing symlink %r", plugin_path)
                os.remove(plugin_path)
            elif os.path.isdir(plugin_path):
                log.debug("Removing directory %r", plugin_path)
                shutil.rmtree(plugin_path)

        # Remove metadata
        from picard.config import get_config

        config = get_config()
        if 'plugins3' in config.setting and 'metadata' in config.setting['plugins3']:
            config.setting['plugins3']['metadata'].pop(plugin.name, None)

        # Remove plugin config if purge requested
        if purge:
            self._clean_plugin_config(plugin.name)

    def _clean_plugin_config(self, plugin_name: str):
        """Remove plugin-specific configuration."""
        from picard.config import get_config

        config = get_config()
        # Remove plugin section if it exists
        if plugin_name in config.setting:
            del config.setting[plugin_name]
            log.debug('Removed configuration for plugin %s', plugin_name)

    def init_plugins(self):
        """Initialize and enable plugins that are enabled in configuration."""
        # Check for blacklisted plugins on startup
        self._check_blacklisted_plugins()

        for plugin in self._plugins:
            if plugin.name in self._enabled_plugins:
                try:
                    plugin.load_module()
                    plugin.enable(self._tagger)
                except Exception as ex:
                    log.error('Failed initializing plugin %s from %s', plugin.name, plugin.local_path, exc_info=ex)

    def _check_blacklisted_plugins(self):
        """Check installed plugins against blacklist and disable if needed."""
        blacklisted_plugins = []

        for plugin in self._plugins:
            metadata = self._get_plugin_metadata(plugin.name)
            url = metadata.get('url') if metadata else None

            # Get UUID from plugin manifest
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None

            is_blacklisted, reason = self._registry.is_blacklisted(url, plugin_uuid)
            if is_blacklisted:
                log.warning('Plugin %s is blacklisted: %s', plugin.name, reason)
                blacklisted_plugins.append((plugin.name, reason))

                if plugin.name in self._enabled_plugins:
                    log.warning('Disabling blacklisted plugin %s', plugin.name)
                    self._enabled_plugins.discard(plugin.name)
                    self._save_config()

        # Show warning to user if any plugins were blacklisted
        if blacklisted_plugins:
            self._show_blacklist_warning(blacklisted_plugins)

    def _show_blacklist_warning(self, blacklisted_plugins):
        """Show warning dialog to user about blacklisted plugins."""
        # Skip GUI warning if no tagger (CLI mode)
        if not self._tagger:
            return

        from PyQt6.QtWidgets import QMessageBox

        plugin_list = '\n'.join([f'• {name}: {reason}' for name, reason in blacklisted_plugins])
        message = (
            f'The following plugins have been blacklisted and disabled:\n\n'
            f'{plugin_list}\n\n'
            f'These plugins may contain security vulnerabilities or malicious code. '
            f'They have been automatically disabled for your protection.'
        )

        QMessageBox.warning(
            self._tagger.window if hasattr(self._tagger, 'window') else None, 'Blacklisted Plugins Detected', message
        )
        log.info('Showed blacklist warning for %d plugin(s)', len(blacklisted_plugins))

    def enable_plugin(self, plugin: Plugin):
        """Enable a plugin and save to config."""
        log.debug('Enabling plugin %s (current state: %s)', plugin.name, plugin.state.value)

        if self._tagger:
            plugin.load_module()
            plugin.enable(self._tagger)

        self._enabled_plugins.add(plugin.name)
        self._save_config()
        log.info('Plugin %s enabled (state: %s)', plugin.name, plugin.state.value)

    def disable_plugin(self, plugin: Plugin):
        """Disable a plugin and save to config."""

        log.debug('Disabling plugin %s (current state: %s)', plugin.name, plugin.state.value)
        plugin.disable()
        self._enabled_plugins.discard(plugin.name)
        self._save_config()
        log.info('Plugin %s disabled (state: %s)', plugin.name, plugin.state.value)

    def _load_config(self):
        """Load enabled plugins list from config."""
        from picard.config import get_config

        config = get_config()
        # config.setting['plugins3'] returns a dict with plugin settings
        plugins3_config = config.setting['plugins3']
        enabled = plugins3_config.get('enabled_plugins', [])
        self._enabled_plugins = set(enabled)
        log.debug('Loaded enabled plugins from config: %r', self._enabled_plugins)

    def _save_config(self):
        """Save enabled plugins list to config."""
        from picard.config import get_config

        config = get_config()
        plugins3_config = config.setting['plugins3']
        if not isinstance(plugins3_config, dict):
            plugins3_config = {}
        plugins3_config['enabled_plugins'] = list(self._enabled_plugins)
        config.setting['plugins3'] = plugins3_config
        log.debug('Saved enabled plugins to config: %r', self._enabled_plugins)

    def _get_plugin_metadata(self, plugin_name: str):
        """Get stored metadata for a plugin."""
        from picard.config import get_config

        config = get_config()
        if 'plugins3' not in config.setting:
            return {}
        plugins3 = config.setting['plugins3']
        if 'metadata' not in plugins3:
            return {}
        metadata = plugins3['metadata']
        return metadata.get(plugin_name, {})

    def _save_plugin_metadata(self, plugin_name: str, url: str, ref: str, commit_id: str):
        """Save plugin metadata to config."""
        from picard.config import get_config

        config = get_config()
        plugins3 = config.setting['plugins3'] if 'plugins3' in config.setting else {}
        if 'metadata' not in plugins3:
            plugins3['metadata'] = {}

        plugins3['metadata'][plugin_name] = {'url': url, 'ref': ref, 'commit': commit_id}
        config.setting['plugins3'] = plugins3  # Reassign to persist
        log.debug(
            'Saved metadata for plugin %s: url=%s, ref=%s, commit=%s',
            plugin_name,
            url,
            ref,
            short_commit_id(commit_id) if commit_id else None,
        )

    def _load_plugin(self, plugin_dir: Path, plugin_name: str):
        """Load a plugin and check API version compatibility.

        Returns:
            Plugin object if compatible, None otherwise
        """
        plugin = Plugin(plugin_dir, plugin_name)
        try:
            plugin.read_manifest()
            compatible_versions = _compatible_api_versions(plugin.manifest.api_versions)
            if compatible_versions:
                log.debug(
                    'Plugin "%s" is compatible (requires API %s, Picard supports %s)',
                    plugin.name,
                    plugin.manifest.api_versions,
                    api_versions_tuple,
                )
                return plugin
            else:
                log.warning(
                    'Plugin "%s" from "%s" is not compatible with this version of Picard. '
                    'Plugin requires API versions %s, but Picard supports %s.',
                    plugin.name,
                    plugin.local_path,
                    plugin.manifest.api_versions,
                    api_versions_tuple,
                )
                return None
        except Exception as ex:
            log.warning('Could not read plugin manifest from %r', plugin_dir.joinpath(plugin_name), exc_info=ex)
            return None


def _compatible_api_versions(api_versions):
    return set(api_versions) & set(api_versions_tuple)
