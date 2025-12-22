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

from pathlib import Path
import re
import shutil
import tempfile

from picard import log
from picard.git.ops import GitOperations
from picard.git.utils import get_local_repository_path
from picard.plugin3.installable import LocalInstallablePlugin, UrlInstallablePlugin
from picard.plugin3.plugin import (
    Plugin,
    PluginSourceGit,
    PluginState,
    hash_string,
)
from picard.plugin3.plugin_metadata import PluginMetadata
from picard.plugin3.validation import PluginValidation


def get_plugin_directory_name(manifest) -> str:
    """Get plugin directory name from manifest (sanitized name + full UUID).

    Args:
        manifest: PluginManifest instance

    Returns:
        Directory name: <sanitized_name>_<uuid>
        Example: my_plugin_f8bf81d7-c5e2-472b-ba96-62140cefc9e1
    """
    # Sanitize name: lowercase, alphanumeric + underscore
    name = manifest.name()
    sanitized = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    sanitized = sanitized[:50] if sanitized else 'plugin'

    uuid_str = manifest.uuid if manifest.uuid else 'no_uuid'
    return f'{sanitized}_{uuid_str}'


class PluginInstaller:
    """Handles plugin installation operations."""

    def __init__(self, manager):
        self.manager = manager

    def install_plugin(
        self, url, ref=None, reinstall=False, force_blacklisted=False, discard_changes=False, enable_after_install=False
    ):
        """Install a plugin from a git URL or local directory."""
        # Check if url is a local directory
        local_path = get_local_repository_path(url)

        # Initial blacklist check
        if not force_blacklisted:
            self._check_blacklist_initial(url, ref, local_path)

        # Install from local directory or remote URL
        if local_path:
            return self._install_from_local_directory(
                local_path, reinstall, force_blacklisted, ref, discard_changes, enable_after_install
            )

        return self._install_from_remote_url(
            url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install
        )

    def _check_blacklist_initial(self, url, ref, local_path):
        """Perform initial blacklist check before installation."""
        if local_path:
            plugin = LocalInstallablePlugin(str(local_path), ref, self.manager._registry)
        else:
            plugin = UrlInstallablePlugin(url, ref, self.manager._registry)

        is_blacklisted, blacklist_reason = plugin.is_blacklisted()
        if is_blacklisted:
            from picard.plugin3.manager import PluginBlacklistedError

            raise PluginBlacklistedError(url, blacklist_reason)

    def _check_blacklist_with_uuid(self, url, ref, manifest):
        """Check blacklist with actual UUID from manifest."""
        plugin = UrlInstallablePlugin(url, ref, self.manager._registry)
        plugin.plugin_uuid = manifest.uuid
        is_blacklisted, blacklist_reason = plugin.is_blacklisted()
        if is_blacklisted:
            from picard.plugin3.manager import PluginBlacklistedError

            raise PluginBlacklistedError(url, blacklist_reason, manifest.uuid)

    def _check_uuid_conflict(self, manifest, source_url, reinstall):
        """Check for UUID conflicts with existing plugins."""
        has_conflict, existing_plugin = self.manager._check_uuid_conflict(manifest, source_url)
        if has_conflict and not reinstall:
            existing_metadata = self.manager._metadata.get_plugin_metadata(existing_plugin.uuid)
            existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)

            from picard.plugin3.manager import PluginUUIDConflictError

            raise PluginUUIDConflictError(manifest.uuid, existing_plugin.plugin_id, existing_source, source_url)

    def _sync_plugin_source(self, source_url, ref, is_local=False):
        """Sync plugin source to temporary directory and return sync info."""
        url_hash = hash_string(str(source_url))

        if is_local:
            temp_path = Path(tempfile.gettempdir()) / f'picard-plugin-{url_hash}'
        else:
            temp_path = self.manager._primary_plugin_dir / f'.tmp-plugin-{url_hash}'
            # Reuse temp dir if it's already a git repo, otherwise remove it
            if temp_path.exists() and not (temp_path / '.git').exists():
                shutil.rmtree(temp_path)

        try:
            source = PluginSourceGit(str(source_url), ref)
            commit_id = source.sync(temp_path, single_branch=True)
            return temp_path, source, commit_id
        except Exception as e:
            # For reinstalls with preserved ref, try fallback to default
            if ref and not is_local:
                log.warning('Failed to sync with preserved ref "%s": %s. Falling back to default ref.', ref, e)
                source = PluginSourceGit(str(source_url), None)
                commit_id = source.sync(temp_path, single_branch=True)
                return temp_path, source, commit_id
            else:
                self.manager._safe_remove_directory(temp_path, "temp directory after sync failure")
                raise

    def _finalize_installation(self, temp_path, final_path, plugin_name, manifest, source, commit_id, source_url):
        """Complete plugin installation after validation."""
        # Atomic move from temp to final location
        if temp_path != final_path:
            try:
                if temp_path.is_dir():
                    temp_path.rename(final_path)
                else:
                    shutil.move(str(temp_path), str(final_path))
            except OSError:
                # Cross-filesystem move - use shutil.move as fallback
                shutil.move(str(temp_path), str(final_path))

        # Store plugin metadata
        self.manager._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin_name,
                url=str(source_url),
                ref=source.resolved_ref,
                commit=commit_id,
                uuid=manifest.uuid,
                ref_type=source.resolved_ref_type,
            )
        )

        return plugin_name

    def _create_and_register_plugin(self, plugin_name, manifest, enable_after_install):
        """Create plugin instance and register it with manager."""
        plugin = Plugin(self.manager._primary_plugin_dir, plugin_name, uuid=manifest.uuid)
        self.manager._plugins.append(plugin)
        self.manager.plugin_installed.emit(plugin)

        if enable_after_install:
            try:
                self.manager.enable_plugin(plugin)
            except Exception as e:
                log.error('Plugin installation failed during enable due to manifest error: %s', e)
                final_path = self.manager._primary_plugin_dir / plugin_name
                self.manager._cleanup_failed_plugin_install(plugin, plugin_name, final_path)
                raise

        return plugin

    def _check_already_installed(self, final_path, plugin_name, source_url, reinstall, discard_changes):
        """Check if plugin is already installed and handle reinstall."""
        if final_path.exists():
            if not reinstall:
                from picard.plugin3.manager import PluginAlreadyInstalledError

                raise PluginAlreadyInstalledError(plugin_name, source_url)
            self._handle_existing_plugin_reinstall(final_path, plugin_name, discard_changes)

    def _install_common(
        self, source_url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install, is_local=False
    ):
        """Common installation logic for both remote and local sources."""
        # Preserve original ref if reinstalling and no ref specified
        ref = self.manager._preserve_original_ref_if_needed(source_url, ref, reinstall)

        # Handle local-specific pre-sync operations
        if is_local:
            local_path = Path(source_url)
            # All plugins must be git repositories
            if not (local_path / '.git').exists():
                raise ValueError(
                    f"Plugin directory {local_path} is not a git repository. All plugins must be git repositories."
                )

            # Check source repository status and get current ref if needed
            try:

                def check_status(source_repo):
                    if source_repo.get_status():
                        log.warning('Installing from local repository with uncommitted changes: %s', local_path)
                    # If no ref specified, use the current branch
                    if not ref and not source_repo.is_head_detached():
                        current_ref = source_repo.get_head_shorthand()
                        log.debug('Using current branch from local repo: %s', current_ref)
                        return current_ref
                    return ref

                ref = self.manager._with_plugin_repo(local_path, check_status)
            except Exception as e:
                log.debug("Failed to check local repository status: %s", e)
                # Ignore errors checking status

        try:
            # Sync plugin source to temporary location
            temp_path, source, commit_id = self._sync_plugin_source(source_url, ref, is_local=is_local)

            # Read and validate manifest
            manifest = PluginValidation.read_and_validate_manifest(temp_path, source_url)
            plugin_name = get_plugin_directory_name(manifest)

            # Perform validation checks
            if not force_blacklisted and not is_local:  # Only check blacklist for remote sources
                self._check_blacklist_with_uuid(source_url, ref, manifest)
            self._check_uuid_conflict(manifest, str(source_url), reinstall)

            final_path = self.manager._primary_plugin_dir / plugin_name

            # Handle existing installation (different logic for local vs remote)
            if is_local:
                self._handle_local_existing_installation(
                    final_path, plugin_name, source_url, reinstall, discard_changes
                )
            else:
                self._check_already_installed(final_path, plugin_name, source_url, reinstall, discard_changes)

            # Complete installation
            self._finalize_installation(temp_path, final_path, plugin_name, manifest, source, commit_id, source_url)
            self._create_and_register_plugin(plugin_name, manifest, enable_after_install)

            if is_local:
                log.info('Plugin %s installed from local directory %s', plugin_name, source_url)
            return plugin_name

        except Exception:
            # Clean up temp directory on failure
            if 'temp_path' in locals():
                self.manager._safe_remove_directory(temp_path, "temp directory after installation failure")
            raise

    def _handle_local_existing_installation(self, final_path, plugin_name, source_url, reinstall, discard_changes):
        """Handle existing installation for local directories (checks for dirty working dir)."""
        if final_path.exists():
            if not reinstall:
                from picard.plugin3.manager import PluginAlreadyInstalledError

                raise PluginAlreadyInstalledError(plugin_name, source_url)

            # Check for uncommitted changes before removing
            if not discard_changes:
                changes = GitOperations.check_dirty_working_dir(final_path)
                if changes:
                    from picard.plugin3.manager import PluginDirtyError

                    raise PluginDirtyError(plugin_name, changes)

            self.manager._safe_remove_directory(final_path, f"existing plugin directory for {plugin_name}")

    def _install_from_remote_url(self, url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install):
        """Install a plugin from a remote git URL."""
        return self._install_common(
            url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install, is_local=False
        )

    def _install_from_local_directory(
        self,
        local_path: Path,
        reinstall=False,
        force_blacklisted=False,
        ref=None,
        discard_changes=False,
        enable_after_install=False,
    ):
        """Install a plugin from a local directory."""
        return self._install_common(
            local_path, ref, reinstall, force_blacklisted, discard_changes, enable_after_install, is_local=True
        )

    def _handle_existing_plugin_reinstall(self, final_path, plugin_name, discard_changes):
        """Handle reinstalling over existing plugin."""
        # Find and unload existing plugin before reinstall
        existing_plugin = None
        for plugin in self.manager._plugins:
            if plugin.local_path == final_path:
                existing_plugin = plugin
                break

        if existing_plugin:
            # Force disable the plugin to ensure all extensions are unregistered
            # This is needed even if plugin is not in enabled list
            try:
                if existing_plugin.state != PluginState.DISABLED:
                    existing_plugin.disable()
            except Exception as e:
                # If disable fails, continue anyway
                log.debug("Failed to disable existing plugin during reinstall: %s", e)
                pass

            # Remove from enabled plugins list if present
            if existing_plugin.plugin_id in self.manager._enabled_plugins:
                self.manager._enabled_plugins.discard(existing_plugin.plugin_id)

            # Remove plugin from plugins list
            if existing_plugin in self.manager.plugins:
                self.manager.plugins.remove(existing_plugin)

        # Check for uncommitted changes before removing
        if not discard_changes:
            changes = GitOperations.check_dirty_working_dir(final_path)
            if changes:
                from picard.plugin3.manager import PluginDirtyError

                raise PluginDirtyError(plugin_name, changes)

        self.manager._safe_remove_directory(final_path, f"existing plugin directory for {plugin_name}")
