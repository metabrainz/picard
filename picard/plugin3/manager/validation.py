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

from picard import log
from picard.plugin3.validation import PluginValidation


class PluginValidationManager:
    """Handles plugin validation operations."""

    def __init__(self, manager):
        self.manager = manager

    def _check_uuid_conflict(self, manifest, source_url):
        """Check if plugin UUID conflicts with existing plugin from different source.

        Args:
            manifest: Plugin manifest to check
            source_url: Source URL of the plugin being installed

        Returns:
            tuple: (has_conflict: bool, existing_plugin: Plugin|None)
        """
        if not manifest.uuid:
            return False, None

        # Normalize source URL for comparison
        source_url = str(source_url).rstrip('/')

        for existing_plugin in self.manager._plugins:
            if existing_plugin.uuid and str(existing_plugin.uuid).lower() == str(manifest.uuid).lower():
                # Get existing plugin's source URL
                existing_metadata = self.manager._metadata.get_plugin_metadata(existing_plugin.uuid)
                existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)
                existing_source = str(existing_source).rstrip('/')

                # Same UUID + same source = no conflict (reinstall case)
                if existing_source.lower() == source_url.lower():
                    return False, None

                # Same UUID + different source = conflict
                return True, existing_plugin

        return False, None

    def _validate_manifest_or_rollback(self, plugin, old_commit, was_enabled):
        """Validate plugin manifest after git operations, rollback on failure.

        Args:
            plugin: Plugin to validate
            old_commit: Commit ID to rollback to on failure
            was_enabled: Whether plugin was enabled before operation

        Raises:
            PluginManifestInvalidError, PluginManifestReadError: If manifest validation fails
        """
        try:
            plugin.read_manifest()
        except Exception as e:
            # Rollback to previous commit on manifest validation failure
            log.error('Plugin operation failed due to invalid manifest: %s', e)
            try:
                self.manager._rollback_plugin_to_commit(plugin, old_commit)
                log.info('Successfully rolled back plugin %s to previous version', plugin.plugin_id)
            except Exception as rollback_error:
                log.error('Failed to rollback plugin %s: %s', plugin.plugin_id, rollback_error)
                # If rollback fails, remove the broken plugin to prevent it from disappearing
                try:
                    log.warning('Removing broken plugin %s after failed rollback', plugin.plugin_id)
                    if plugin in self.manager._plugins:
                        self.manager._plugins.remove(plugin)
                    self.manager._safe_remove_directory(
                        plugin.local_path, f"broken plugin directory for {plugin.plugin_id}"
                    )
                except Exception as cleanup_error:
                    log.error('Failed to cleanup broken plugin %s: %s', plugin.plugin_id, cleanup_error)
                # Raise rollback error instead of original error since rollback failed
                raise rollback_error

            # Re-enable plugin if it was enabled before rollback
            if was_enabled:
                try:
                    self.manager.enable_plugin(plugin)
                except Exception as enable_error:
                    log.error('Failed to re-enable plugin %s after rollback: %s', plugin.plugin_id, enable_error)

            # Re-raise the original manifest error
            raise

    def _read_and_validate_manifest(self, path, source_description):
        """Read and validate manifest."""
        return PluginValidation.read_and_validate_manifest(path, source_description)
