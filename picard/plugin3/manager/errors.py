# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024-2026 Laurent Monin
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


class PluginManagerError(Exception):
    """Base exception for plugin manager errors."""

    pass


class PluginDirtyError(PluginManagerError):
    """Raised when installed plugin directory has uncommitted changes."""

    def __init__(self, plugin_name, changes):
        self.plugin_name = plugin_name
        self.changes = changes
        super().__init__(f"Plugin {plugin_name} has uncommitted changes")


class PluginAlreadyInstalledError(PluginManagerError):
    """Raised when trying to install a plugin that's already installed."""

    def __init__(self, plugin_name, url):
        self.plugin_name = plugin_name
        self.url = url
        super().__init__(f"Plugin {plugin_name} is already installed")


class PluginBlacklistedError(PluginManagerError):
    """Raised when trying to install a blacklisted plugin."""

    def __init__(self, url, reason, uuid=None):
        self.url = url
        self.reason = reason
        self.uuid = uuid
        super().__init__(f"Plugin is blacklisted: {reason}")


class PluginManifestError(PluginManagerError):
    """Base class for plugin manifest-related errors."""

    pass


class PluginManifestNotFoundError(PluginManifestError):
    """Raised when MANIFEST.toml is not found in plugin source."""

    def __init__(self, source):
        self.source = source
        super().__init__(f"No MANIFEST.toml found in {source}")


class PluginManifestReadError(PluginManifestError):
    """Raised when MANIFEST.toml cannot be read."""

    def __init__(self, e, source):
        self.source = source
        super().__init__(f"Failed to read MANIFEST.toml in {source}: {e}")


class PluginManifestInvalidError(PluginManifestError):
    """Raised when MANIFEST.toml validation fails."""

    def __init__(self, errors):
        self.errors = errors
        error_list = '\n  '.join(errors) if isinstance(errors, list) else str(errors)
        super().__init__(f"Invalid MANIFEST.toml:\n  {error_list}")


class PluginNoSourceError(PluginManagerError):
    """Raised when plugin has no stored source URL for update/switch-ref."""

    def __init__(self, plugin_id, operation):
        self.plugin_id = plugin_id
        self.operation = operation
        super().__init__(f"Plugin {plugin_id} has no stored URL, cannot {operation}")


class PluginRefSwitchError(PluginManagerError):
    """Raised when switching to a git ref fails."""

    def __init__(self, plugin_id, ref, original_error):
        self.plugin_id = plugin_id
        self.ref = ref
        self.original_error = original_error
        super().__init__(f"Cannot switch to ref {ref}: {original_error}")


class PluginRefNotFoundError(PluginManagerError):
    """Raised when requested ref is not found or not available."""

    def __init__(self, plugin_id, ref):
        self.plugin_id = plugin_id
        self.ref = ref
        super().__init__(f"Ref '{ref}' not found for plugin {plugin_id}")


class PluginNoUUIDError(PluginManifestError):
    """Raised when plugin has no UUID in manifest."""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id
        super().__init__(f"Plugin {plugin_id} has no UUID")


class PluginCommitPinnedError(PluginManagerError):
    """Raised when trying to update a commit-pinned plugin."""

    def __init__(self, plugin_id, commit):
        self.plugin_id = plugin_id
        self.commit = commit
        super().__init__(f'Plugin is pinned to commit "{commit}" and cannot be updated')


class PluginUUIDConflictError(PluginManagerError):
    """Raised when trying to install plugin with conflicting UUID."""

    def __init__(self, uuid, existing_plugin_id, existing_source, new_source):
        self.uuid = uuid
        self.existing_plugin_id = existing_plugin_id
        self.existing_source = existing_source
        self.new_source = new_source
        super().__init__(
            f'Plugin UUID {uuid} already exists in plugin "{existing_plugin_id}" '
            f'from source "{existing_source}". Cannot install from different source "{new_source}".'
        )
