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
    import re

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

        # Check blacklist before installing
        if not force_blacklisted:
            # Create appropriate InstallablePlugin for blacklist checking
            if local_path:
                plugin = LocalInstallablePlugin(str(local_path), ref, self.manager._registry)
            else:
                plugin = UrlInstallablePlugin(url, ref, self.manager._registry)

            is_blacklisted, blacklist_reason = plugin.is_blacklisted()
            if is_blacklisted:
                from picard.plugin3.manager import PluginBlacklistedError

                raise PluginBlacklistedError(url, blacklist_reason)

        # Install from local directory or remote URL
        if local_path:
            return self._install_from_local_directory(
                local_path, reinstall, force_blacklisted, ref, discard_changes, enable_after_install
            )

        return self._install_from_remote_url(
            url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install
        )

    def _install_from_remote_url(self, url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install):
        """Install a plugin from a remote git URL."""
        # Preserve original ref if reinstalling and no ref specified
        ref = self.manager._preserve_original_ref_if_needed(url, ref, reinstall)

        # Handle git URL - use temp dir in plugin directory for atomic rename
        url_hash = hash_string(url)
        temp_path = self.manager._primary_plugin_dir / f'.tmp-plugin-{url_hash}'

        try:
            # Reuse temp dir if it's already a git repo, otherwise remove it
            if temp_path.exists():
                if not (temp_path / '.git').exists():
                    # Not a git repo, remove it
                    shutil.rmtree(temp_path)

            # Clone or update temporary location with single-branch optimization
            source = PluginSourceGit(url, ref)
            try:
                commit_id = source.sync(temp_path, single_branch=True)
            except Exception as e:
                # If sync fails and we're using a preserved ref, try fallback to default
                if ref and reinstall:
                    log.warning('Failed to sync with preserved ref "%s": %s. Falling back to default ref.', ref, e)
                    source = PluginSourceGit(url, None)  # Use default ref
                    commit_id = source.sync(temp_path, single_branch=True)
                else:
                    raise

            # Read MANIFEST to get plugin ID
            manifest = PluginValidation.read_and_validate_manifest(temp_path, url)

            # Generate plugin directory name from sanitized name + UUID
            plugin_name = get_plugin_directory_name(manifest)

            # Check blacklist again with UUID
            if not force_blacklisted:
                plugin = UrlInstallablePlugin(url, ref, self.manager._registry)
                plugin.plugin_uuid = manifest.uuid  # Update with actual UUID from manifest
                is_blacklisted, blacklist_reason = plugin.is_blacklisted()
                if is_blacklisted:
                    from picard.plugin3.manager import PluginBlacklistedError

                    raise PluginBlacklistedError(url, blacklist_reason, manifest.uuid)

            # Check for UUID conflicts with existing plugins from different sources
            has_conflict, existing_plugin = self.manager._check_uuid_conflict(manifest, url)
            if has_conflict and not reinstall:
                existing_metadata = self.manager._metadata.get_plugin_metadata(existing_plugin.uuid)
                existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)
                from picard.plugin3.manager import PluginUUIDConflictError

                raise PluginUUIDConflictError(manifest.uuid, existing_plugin.plugin_id, existing_source, url)

            final_path = self.manager._primary_plugin_dir / plugin_name

            # Check if already installed and handle reinstall
            if final_path.exists():
                if not reinstall:
                    from picard.plugin3.manager import PluginAlreadyInstalledError

                    raise PluginAlreadyInstalledError(plugin_name, url)

                self._handle_existing_plugin_reinstall(final_path, plugin_name, discard_changes)

            # Atomic rename from temp to final location
            temp_path.rename(final_path)

            # Store plugin metadata
            self.manager._metadata.save_plugin_metadata(
                PluginMetadata(
                    name=plugin_name,
                    url=url,
                    ref=source.resolved_ref,
                    commit=commit_id,
                    uuid=manifest.uuid,
                    ref_type=source.resolved_ref_type,
                )
            )

            # Add newly installed plugin to the plugins list
            plugin = Plugin(self.manager._primary_plugin_dir, plugin_name, uuid=manifest.uuid)
            self.manager._plugins.append(plugin)
            self.manager.plugin_installed.emit(plugin)

            # Enable plugin if requested
            if enable_after_install:
                try:
                    self.manager.enable_plugin(plugin)
                except Exception as e:
                    # Remove installed plugin on manifest validation failure during enable
                    log.error('Plugin installation failed during enable due to manifest error: %s', e)
                    self.manager._cleanup_failed_plugin_install(plugin, plugin_name, final_path)
                    # Re-raise the original error
                    raise

            return plugin_name

        except Exception:
            # Clean up temp directory on failure
            self.manager._safe_remove_directory(temp_path, "temp directory after installation failure")
            raise

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
        # Preserve original ref if reinstalling and no ref specified
        ref = self.manager._preserve_original_ref_if_needed(local_path, ref, reinstall)

        # Check if local directory is a git repository
        is_git_repo = (local_path / '.git').exists()

        if is_git_repo:
            # Check if source repository has uncommitted changes
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
            except Exception:
                pass  # Ignore errors checking status

            # Use git operations to get ref and commit info
            url_hash = hash_string(str(local_path))
            temp_path = Path(tempfile.gettempdir()) / f'picard-plugin-{url_hash}'

            try:
                source = PluginSourceGit(str(local_path), ref)
                commit_id = source.sync(temp_path, single_branch=True)
                install_path = temp_path
                ref_to_save = source.resolved_ref
                ref_type_to_save = source.resolved_ref_type
                commit_to_save = commit_id
            except Exception:
                # Clean up temp directory on failure
                self.manager._safe_remove_directory(temp_path, "temp directory after git sync failure")
                raise
        else:
            # All plugins must be git repositories
            raise ValueError(
                f"Plugin directory {local_path} is not a git repository. All plugins must be git repositories."
            )

        # Read MANIFEST to get plugin ID
        try:
            manifest = PluginValidation.read_and_validate_manifest(install_path, local_path)
        except Exception:
            # Clean up temp directory if manifest validation fails
            self.manager._safe_remove_directory(temp_path, "temp directory after manifest validation failure")
            raise

        # Check for UUID conflicts with existing plugins from different sources
        has_conflict, existing_plugin = self.manager._check_uuid_conflict(manifest, str(local_path))
        if has_conflict and not reinstall:
            existing_metadata = self.manager._metadata.get_plugin_metadata(existing_plugin.uuid)
            existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)
            from picard.plugin3.manager import PluginUUIDConflictError

            raise PluginUUIDConflictError(manifest.uuid, existing_plugin.plugin_id, existing_source, str(local_path))

        # Generate plugin directory name from sanitized name + UUID
        plugin_name = get_plugin_directory_name(manifest)
        assert self.manager._primary_plugin_dir is not None
        final_path = self.manager._primary_plugin_dir / plugin_name

        # Check if already installed and handle reinstall
        if final_path.exists():
            if not reinstall:
                from picard.plugin3.manager import PluginAlreadyInstalledError

                raise PluginAlreadyInstalledError(plugin_name, local_path)

            # Check for uncommitted changes before removing
            if not discard_changes:
                changes = GitOperations.check_dirty_working_dir(final_path)
                if changes:
                    from picard.plugin3.manager import PluginDirtyError

                    raise PluginDirtyError(plugin_name, changes)

            self.manager._safe_remove_directory(final_path, f"existing plugin directory for {plugin_name}")

        # Copy to plugin directory
        # Move from temp location (git repo was cloned to temp)
        shutil.move(str(install_path), str(final_path))

        # Store metadata
        self.manager._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin_name,
                url=str(local_path),
                ref=ref_to_save or '',
                commit=commit_to_save or '',
                uuid=manifest.uuid,
                ref_type=ref_type_to_save,
            )
        )

        # Add newly installed plugin to the plugins list
        plugin = Plugin(self.manager._primary_plugin_dir, plugin_name, uuid=manifest.uuid)
        self.manager._plugins.append(plugin)

        # Enable plugin if requested
        if enable_after_install:
            try:
                self.manager.enable_plugin(plugin)
            except Exception as e:
                # Remove installed plugin on manifest validation failure during enable
                log.error('Local plugin installation failed during enable due to manifest error: %s', e)
                self.manager._cleanup_failed_plugin_install(plugin, plugin_name, final_path)
                # Re-raise the original error
                raise

        log.info('Plugin %s installed from local directory %s', plugin_name, local_path)
        return plugin_name

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
            except Exception:
                # If disable fails, continue anyway
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
