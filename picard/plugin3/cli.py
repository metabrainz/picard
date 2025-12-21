# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025 Laurent Monin
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

import argparse
from datetime import datetime
from enum import IntEnum
import logging
from pathlib import Path

# Additional imports for CLI operations
import sys
import tempfile
import traceback

from PyQt6 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
    PICARD_ORG_NAME,
    log,
)
from picard.config import (
    get_config,
    setup_config,
)
from picard.const import USER_PLUGIN_DIR
from picard.debug_opts import DebugOpt
from picard.git.factory import has_git_backend
from picard.git.utils import (
    check_local_repo_dirty,
    get_local_repository_path,
)
from picard.options import init_options
from picard.plugin3.installable import UrlInstallablePlugin
from picard.plugin3.manager import (
    PluginManager,
)
from picard.plugin3.manifest import generate_manifest_template
from picard.plugin3.output import PluginOutput
from picard.plugin3.plugin import (
    PluginSourceGit,
    short_commit_id,
)
from picard.plugin3.registry import (
    RegistryFetchError,
    RegistryParseError,
)
from picard.util import (
    cli,
    versions,
)


def get_display_locale(args):
    """Get locale for displaying plugin information.

    Args:
        args: CLI arguments object

    Returns:
        str: Locale string from --locale option, or 'en' as default
    """
    return getattr(args, 'locale', 'en')


def get_localized_registry_field(plugin, field, locale='en'):
    """Get localized field from registry plugin data.

    Args:
        plugin: RegistryPlugin object
        field: Field name ('name', 'description', 'long_description')
        locale: Locale string (e.g., 'en_US', 'de_DE')

    Returns:
        str: Localized field value, or base field value if translation not found
    """
    if field == 'name':
        return plugin.name_i18n(locale)
    elif field == 'description':
        return plugin.description_i18n(locale)
    else:
        # For other fields, return the base field
        return getattr(plugin, field, '')


class ExitCode(IntEnum):
    """Exit codes for plugin CLI commands."""

    SUCCESS = 0
    ERROR = 1
    NOT_FOUND = 2
    CANCELLED = 130


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_VERSIONS = 20


class PluginCLI:
    """Command line interface for managing plugins."""

    def __init__(self, manager, args, output=None, parser=None):
        self._manager = manager
        self._args = args
        self._out = output or PluginOutput()
        self._parser = parser

    def _is_debug_mode(self):
        """Check if debug mode is enabled."""
        return getattr(self._args, 'debug', False)

    def _handle_exception(self, e, message=None):
        """Handle exception with optional traceback in debug mode.

        Args:
            e: Exception to handle
            message: Optional custom error message prefix
        """
        if message:
            self._out.error(f'{message}: {e}')
        else:
            self._out.error(f'Error: {e}')

        if self._is_debug_mode():
            self._out.nl()
            self._out.error('Traceback:')
            for line in traceback.format_exc().splitlines():
                self._out.error(f'  {line}')

    def _format_version_info(self, result):
        """Format version info with tags and commits for display.

        Args:
            result: UpdateResult or UpdateCheck with old_commit, new_commit, old_ref, new_ref
                   (and optionally old_version, new_version, commit_date)
        """
        # Show tag with commit ID if available
        old_ref_item = getattr(result, 'old_ref_item', None)
        new_ref_item = getattr(result, 'new_ref_item', None)

        if old_ref_item and new_ref_item and old_ref_item.shortname != new_ref_item.shortname:
            old_short = short_commit_id(result.old_commit)
            new_short = short_commit_id(result.new_commit)

            # Use RefItem.format() for consistent display
            old_display = old_ref_item.format(
                ref_formatter=self._out.d_version, commit_formatter=self._out.d_commit_old
            )
            new_display = new_ref_item.format(
                ref_formatter=self._out.d_version, commit_formatter=self._out.d_commit_new
            )

            version_info = f'{old_display} {self._out.d_arrow()} {new_display}'
        # Show version with commit ID if version changed
        elif (
            hasattr(result, 'old_version')
            and hasattr(result, 'new_version')
            and result.old_version != result.new_version
        ):
            version_info = (
                f'{self._out.d_version(result.old_version)} ({self._out.d_commit_old(short_commit_id(result.old_commit))}) '
                f'{self._out.d_arrow()} '
                f'{self._out.d_version(result.new_version)} ({self._out.d_commit_new(short_commit_id(result.new_commit))})'
            )
        # Show commits (but check if they're actually the same)
        else:
            old_short = short_commit_id(result.old_commit)
            new_short = short_commit_id(result.new_commit)

            # If commits are the same, just show the ref change or "already up to date"
            if old_short == new_short:
                old_ref_item = getattr(result, 'old_ref_item', None)
                new_ref_item = getattr(result, 'new_ref_item', None)

                if old_ref_item and new_ref_item and old_ref_item.shortname != new_ref_item.shortname:
                    version_info = f'{old_ref_item.shortname} {self._out.d_arrow()} {new_ref_item.shortname} ({self._out.d_commit_new(new_short)})'
                else:
                    version_info = f'{self._out.d_commit_new(new_short)}'
            else:
                version_info = (
                    f'{self._out.d_commit_old(old_short)} {self._out.d_arrow()} {self._out.d_commit_new(new_short)}'
                )

        # Append date if available
        if hasattr(result, 'commit_date'):
            date_str = datetime.fromtimestamp(result.commit_date).strftime(DATETIME_FORMAT)
            version_info = f'{version_info} {self._out.d_date(f"({date_str})")}'

        return version_info

    def _handle_dirty_error(self, error, action_callback):
        """Handle PluginDirtyError with user prompt or error.

        Args:
            error: PluginDirtyError exception
            action_callback: Function to call if user confirms (should accept discard_changes=True)

        Returns:
            tuple: (success: bool, result: any) - result is callback return value if success
        """
        self._out.warning(f'Plugin {error.plugin_name} has been modified:')
        for file in error.changes[:5]:
            self._out.warning(f'  - {file}')
        if len(error.changes) > 5:
            self._out.warning(f'  ... and {len(error.changes) - 5} more')

        # With --reinstall --yes, automatically discard changes
        reinstall = getattr(self._args, 'reinstall', False)
        if self._args.yes:
            if reinstall:
                self._out.warning('Discarding changes (--reinstall --yes)')
                result = action_callback(discard_changes=True)
                return True, result
            else:
                self._out.error('Cannot modify plugin with uncommitted changes in non-interactive mode')
                return False, None
        else:
            if self._out.yesno('Discard changes and continue?'):
                result = action_callback(discard_changes=True)
                return True, result
            else:
                self._out.print('Operation cancelled')
                return False, None

    def run(self):
        """Run the CLI command and return exit code."""
        try:
            # Handle --refresh-registry first if specified
            if hasattr(self._args, 'refresh_registry') and self._args.refresh_registry:
                result = self._cmd_refresh_registry()
                # If refresh failed, return error
                if result != ExitCode.SUCCESS:
                    return result
                # Continue to execute other command if specified

            # Validate that --ref is only used with --install or --validate
            ref = getattr(self._args, 'ref', None)
            if ref:
                valid_with_ref = self._args.install or (hasattr(self._args, 'validate') and self._args.validate)
                if not valid_with_ref:
                    self._out.error('--ref can only be used with --install or --validate')
                    return ExitCode.ERROR

            if self._args.list:
                return self._cmd_list()
            elif self._args.info:
                return self._cmd_info(self._args.info)
            elif self._args.list_refs:
                return self._cmd_list_refs(self._args.list_refs)
            elif self._args.enable:
                return self._cmd_enable(self._args.enable)
            elif self._args.disable:
                return self._cmd_disable(self._args.disable)
            elif self._args.install:
                return self._cmd_install(self._args.install)
            elif self._args.remove:
                print(self._args.remove)
                return self._cmd_remove(self._args.remove)
            elif self._args.update:
                return self._cmd_update(self._args.update)
            elif self._args.update_all:
                return self._cmd_update_all()
            elif self._args.check_updates:
                return self._cmd_check_updates()
            elif hasattr(self._args, 'browse') and self._args.browse:
                return self._cmd_browse()
            elif hasattr(self._args, 'search') and self._args.search:
                return self._cmd_search(self._args.search)
            elif hasattr(self._args, 'check_blacklist') and self._args.check_blacklist:
                return self._cmd_check_blacklist(self._args.check_blacklist)
            elif hasattr(self._args, 'refresh_registry') and self._args.refresh_registry:
                # Already handled at the start, just return success
                return ExitCode.SUCCESS
            elif hasattr(self._args, 'switch_ref') and self._args.switch_ref:
                return self._cmd_switch_ref(self._args.switch_ref[0], self._args.switch_ref[1])
            elif hasattr(self._args, 'clean_config') and self._args.clean_config is not None:
                return self._cmd_clean_config(self._args.clean_config)
            elif hasattr(self._args, 'validate') and self._args.validate:
                return self._cmd_validate(self._args.validate, ref)
            elif hasattr(self._args, 'manifest') and self._args.manifest is not None:
                return self._cmd_manifest(self._args.manifest)
            else:
                if self._parser:
                    self._parser.print_help()
                    return ExitCode.SUCCESS
                else:
                    self._out.error('No action specified')
                    return ExitCode.ERROR
        except KeyboardInterrupt:
            self._out.nl()
            self._out.error('Operation cancelled by user')
            return ExitCode.CANCELLED
        except Exception as e:
            self._handle_exception(e)
            return ExitCode.ERROR

    def _get_registry_plugin_version(self, plugin_data):
        """Get latest version tag for a registry plugin.

        Args:
            plugin_data: Plugin dict from registry

        Returns:
            Version string (latest tag or empty string)
        """
        return self._manager.get_registry_plugin_latest_version(plugin_data)

    def _get_version_display(self, plugin_uuid, manifest_version=''):
        """Get version string for display, preferring git tag over manifest version.

        Args:
            plugin_uuid: Plugin UUID to look up metadata
            manifest_version: Fallback version from manifest

        Returns:
            Version string (tag or manifest version)
        """
        return self._manager.get_preferred_version(plugin_uuid, manifest_version)

    def _format_git_info(self, metadata):
        """Format git ref and commit info compactly.

        Returns string like "(@commit)" for commit info only.
        Returns empty string if no metadata.
        """
        if not metadata:
            return ''

        git_ref = metadata.get_git_ref()
        # Only format if we have both ref and commit
        if git_ref.shortname and git_ref.target:
            # Convert GitRef to RefItem for formatting
            from picard.plugin3.ref_item import RefItem

            ref_item = RefItem.from_git_ref(git_ref)
            formatted = ref_item.format()
            return f' ({formatted})' if formatted else ''

        return ''

    def _select_ref_for_plugin(self, plugin):
        """Select appropriate ref for plugin based on versioning scheme or Picard API version.

        Args:
            plugin: Plugin data from registry

        Returns:
            str: Selected ref name, or None if no refs specified
        """
        return self._manager.select_ref_for_plugin(plugin)

    def _cmd_list(self):
        """List all installed plugins with details."""
        if not self._manager.plugins:
            if not self._manager._failed_plugins:
                self._out.print('No plugins installed')
                return ExitCode.SUCCESS
            # Only failed plugins, skip to showing them
        else:
            self._out.print('Installed plugins:')
            self._out.nl()

            # Get system locale for displaying localized plugin info
            locale_str = get_display_locale(self._args)

            # Sort plugins by display name
            sorted_plugins = sorted(
                self._manager.plugins,
                key=lambda p: (p.manifest.name(locale_str) if p.manifest else p.plugin_id).lower(),
            )
            for plugin in sorted_plugins:
                # Get plugin UUID for checking enabled state
                is_enabled = plugin.uuid and plugin.uuid in self._manager._enabled_plugins

                # Show manifest name (human-readable) with localization
                display_name = plugin.manifest.name(locale_str) if plugin.manifest else plugin.plugin_id

                # Display with semantic methods
                if is_enabled:
                    status = self._out.d_status_enabled()
                else:
                    status = self._out.d_status_disabled()

                self._out.print(f'  {self._out.d_name(display_name)} ({status})')

                if hasattr(plugin, 'manifest') and plugin.manifest:
                    desc = plugin.manifest.description(locale_str)
                    if desc:
                        self._out.info(f'  {desc}')

                    # UUID
                    self._out.info(f'  UUID: {self._out.d_uuid(plugin.uuid)}')

                    # Registry ID if available
                    registry_id = self._manager.get_plugin_registry_id(plugin)
                    if registry_id:
                        self._out.info(f'  Registry ID: {self._out.d_id(registry_id)}')

                    # State
                    self._out.info(f'  State: {plugin.state.value}')

                    # Version with git info
                    metadata = self._manager._get_plugin_metadata(plugin.uuid) if plugin.uuid else {}
                    if metadata:
                        git_ref = metadata.get_git_ref()
                        if git_ref.shortname and git_ref.target:
                            # Convert GitRef to RefItem for formatting
                            from picard.plugin3.ref_item import RefItem

                            ref_item = RefItem.from_git_ref(git_ref)
                            version_display = ref_item.format(
                                ref_formatter=self._out.d_version, commit_formatter=self._out.d_commit_old
                            )
                            self._out.info(f'  Version: {version_display}')
                        else:
                            # Fallback to manifest version
                            version = plugin.manifest._data.get('version', '')
                            self._out.info(f'  Version: {self._out.d_version(version)}')
                    else:
                        # No metadata, use manifest version
                        version = plugin.manifest._data.get('version', '')
                        self._out.info(f'  Version: {self._out.d_version(version)}')

                    # Source URL if available
                    if metadata and metadata.url:
                        self._out.info(f'  Source: {self._out.d_url(metadata.url)}')

                    self._out.info(f'  Path: {self._out.d_path(plugin.local_path)}')
                self._out.print()

            total = len(self._manager.plugins)
            enabled = sum(1 for p in self._manager.plugins if p.uuid and p.uuid in self._manager._enabled_plugins)
            disabled = total - enabled
            self._out.print(
                f'Total: {self._out.d_number(total)} plugin{"s" if total != 1 else ""} '
                f'({self._out.d_status_enabled(str(enabled))} enabled, '
                f'{self._out.d_status_disabled(str(disabled))} disabled)'
            )

        # Show failed plugins if any
        if self._manager._failed_plugins:
            self._out.nl()
            self._out.error(f'Failed to load {len(self._manager._failed_plugins)} plugin(s):')
            self._out.nl()
            for plugin_dir, plugin_name, error_msg in self._manager._failed_plugins:
                full_path = Path(plugin_dir) / plugin_name
                self._out.print(f'  • {plugin_name}')
                self._out.print(f'    Error: {error_msg}')
                self._out.print(f'    Path: {full_path}')
                self._out.nl()

        return ExitCode.SUCCESS

    def _cmd_info(self, plugin_name):
        """Show detailed information about a plugin."""
        plugin, error = self._find_plugin_or_error(plugin_name)
        if error:
            return error

        is_enabled = plugin.uuid and plugin.uuid in self._manager._enabled_plugins
        metadata = self._manager._get_plugin_metadata(plugin.uuid) if plugin.uuid else {}

        self._out.print(f'Plugin: {self._out.d_name(plugin.manifest.name())}')

        # Show short description on one line (required field)
        desc = plugin.manifest.description()
        if desc:
            self._out.print(f'Description: {desc}')

        self._out.print(f'UUID: {self._out.d_uuid(plugin.uuid)}')

        # Show registry ID if available (lookup dynamically from current registry)
        registry_id = self._manager.get_plugin_registry_id(plugin)
        if registry_id:
            self._out.print(f'Registry ID: {self._out.d_id(registry_id)}')

        # Status
        if is_enabled:
            status = self._out.d_status_enabled()
        else:
            status = self._out.d_status_disabled()
        self._out.print(f'Status: {status}')
        self._out.print(f'State: {plugin.state.value}')

        # Version
        if metadata:
            git_ref = metadata.get_git_ref()
            if git_ref.shortname and git_ref.target:
                # Convert GitRef to RefItem for formatting
                from picard.plugin3.ref_item import RefItem

                ref_item = RefItem.from_git_ref(git_ref)
                version_display = ref_item.format(
                    ref_formatter=self._out.d_version, commit_formatter=self._out.d_commit_old
                )
                self._out.print(f'Version: {version_display}')
            else:
                # Fallback to manifest version
                version = plugin.manifest._data.get('version', '')
                self._out.print(f'Version: {self._out.d_version(version)}')
        else:
            # No metadata, use manifest version
            version = plugin.manifest._data.get('version', '')
            self._out.print(f'Version: {self._out.d_version(version)}')

        # Show source URL if available
        if metadata and metadata.url:
            self._out.print(f'Source: {self._out.d_url(metadata.url)}')

        # Optional fields - only show if present
        if plugin.manifest.authors:
            self._out.print(f'Authors: {", ".join(plugin.manifest.authors)}')

        if plugin.manifest.maintainers:
            self._out.print(f'Maintainers: {", ".join(plugin.manifest.maintainers)}')

        api_versions = plugin.manifest._data.get('api', [])
        self._out.print(f'API Versions: {", ".join(api_versions)}')

        if plugin.manifest.license:
            self._out.print(f'License: {plugin.manifest.license}')

        if plugin.manifest.license_url:
            self._out.print(f'License URL: {self._out.d_url(plugin.manifest.license_url)}')

        # Optional fields
        categories = plugin.manifest._data.get('categories', [])
        if categories:
            self._out.print(f'Categories: {", ".join(categories)}')

        homepage = plugin.manifest._data.get('homepage')
        if homepage:
            self._out.print(f'Homepage: {self._out.d_url(homepage)}')

        min_python = plugin.manifest._data.get('min_python_version')
        if min_python:
            self._out.print(f'Min Python: {min_python}')

        self._out.print(f'Path: {self._out.d_path(plugin.local_path)}')

        # Show long description at the end if available
        long_desc = plugin.manifest.long_description()
        if long_desc:
            self._out.nl()
            self._out.print(long_desc)

        return ExitCode.SUCCESS

    def _cmd_list_refs(self, identifier):
        """List available git refs (branches/tags) for a plugin.

        Args:
            identifier: Plugin name, registry ID, or git URL
        """
        # Get plugin info using smart detection
        info = self._manager.get_plugin_refs_info(identifier)
        if not info:
            self._out.error(f'Plugin "{identifier}" not found (not installed and not in registry)')
            return ExitCode.NOT_FOUND

        url = info['url']
        current_ref = info['current_ref']
        current_commit = info['current_commit']
        current_ref_type = info['current_ref_type']
        registry_id = info['registry_id']
        plugin = info['plugin']
        registry_plugin = info['registry_plugin']

        # Display header
        if plugin:
            self._out.print(f'Plugin: {self._out.d_name(plugin.manifest.name())}')
        else:
            self._out.print(f'Plugin: {self._out.d_id(registry_id or url)}')

        self._out.print(f'Source: {self._out.d_url(url)}')

        if current_ref:
            commit_short = short_commit_id(current_commit) if current_commit else ''
            if current_ref_type == 'commit':
                # For commit pins, show as commit hash
                self._out.print(f'Current: commit {self._out.d_commit_new(commit_short)}')
            else:
                # For branches and tags, show the ref name
                self._out.print(
                    f'Current: {self._out.d_version(current_ref)} (@{self._out.d_commit_new(commit_short)})'
                )

        self._out.nl()

        # Show registry refs if available
        if registry_plugin:
            refs = registry_plugin.refs
            if refs:
                self._out.print('Registry Refs:')
                for ref in refs:
                    name = ref['name']
                    desc = ref.get('description', '')
                    min_api = ref.get('min_api_version')
                    max_api = ref.get('max_api_version')

                    is_current = current_ref == name
                    marker = ' (current)' if is_current else ''

                    api_info = ''
                    if min_api and max_api:
                        api_info = f' (API {min_api}-{max_api})'
                    elif min_api:
                        api_info = f' (API {min_api}+)'
                    elif max_api:
                        api_info = f' (API ≤{max_api})'

                    if desc:
                        self._out.print(f'  {self._out.d_version(name)}{marker} - {desc}{api_info}')
                    else:
                        self._out.print(f'  {self._out.d_version(name)}{marker}{api_info}')

                self._out.nl()

            # Show version tags if versioning_scheme exists
            versioning_scheme = registry_plugin.versioning_scheme
            if versioning_scheme:
                try:
                    version_tags = self._manager._fetch_version_tags(url, versioning_scheme)
                    if version_tags:
                        self._out.print(f'Released Versions ({versioning_scheme}):')
                        for tag in version_tags[:MAX_VERSIONS]:  # Limit to most recent
                            is_current = current_ref == tag
                            marker = ' (current)' if is_current else ''
                            self._out.print(f'  {self._out.d_version(tag)}{marker}')

                        if len(version_tags) > MAX_VERSIONS:
                            self._out.print(f'  ... and {len(version_tags) - MAX_VERSIONS} more')

                        self._out.nl()
                except Exception as e:
                    self._out.warning(f'Failed to fetch version tags: {e}')

        # Fetch all branches and tags from git
        git_refs = self._manager.fetch_all_git_refs(url)
        if not git_refs:
            self._out.error('Failed to fetch refs from git')
            if self._is_debug_mode():
                self._out.nl()
                self._out.error('Traceback:')
                for line in traceback.format_exc().splitlines():
                    self._out.error(f'  {line}')
            return ExitCode.ERROR

        branches = git_refs['branches']
        tags = git_refs['tags']

        # Show branches
        if branches:
            self._out.print('Branches:')
            for branch in branches:
                name = branch['name']
                commit = short_commit_id(branch['commit']) if branch.get('commit') else ''
                is_current = current_ref == name
                # Use green for current commit, old color otherwise
                commit_color = self._out.d_commit_new if is_current else self._out.d_commit_old
                commit_display = f' @{commit_color(commit)}' if commit else ''
                self._out.print(f'  {name}{commit_display}')
            self._out.nl()

        # Show tags
        if tags:
            self._out.print('Tags:')
            for tag in tags:
                name = tag['name']
                commit = short_commit_id(tag['commit']) if tag.get('commit') else ''
                is_current = current_ref == name
                # Use green for current commit, old color otherwise
                commit_color = self._out.d_commit_new if is_current else self._out.d_commit_old
                commit_display = f' @{commit_color(commit)}' if commit else ''
                self._out.print(f'  {name}{commit_display}')

        return ExitCode.SUCCESS

    def _cmd_install(self, plugin_urls):
        """Install plugins from URLs or plugin IDs."""
        explicit_ref = getattr(self._args, 'ref', None)
        reinstall = getattr(self._args, 'reinstall', False)
        force_blacklisted = getattr(self._args, 'force_blacklisted', False)
        yes = getattr(self._args, 'yes', False)

        if force_blacklisted:
            self._out.warning(self._out.d_warning('WARNING: Bypassing blacklist check - this may be dangerous!'))

        # Warn if using --ref with multiple plugins
        if explicit_ref and len(plugin_urls) > 1:
            self._out.warning(f'Using ref "{explicit_ref}" for all {len(plugin_urls)} plugins')
            if not yes:
                if not self._out.yesno('Continue?'):
                    self._out.print('Installation cancelled')
                    return ExitCode.SUCCESS

        for url_or_id in plugin_urls:
            # Use explicit ref if provided, otherwise may auto-select per plugin
            ref = explicit_ref

            try:
                # Check if it's a plugin ID (no slashes, no protocol)
                if '/' not in url_or_id and '://' not in url_or_id:
                    # If reinstalling, check if it's an installed plugin identifier
                    if reinstall:
                        installed_plugin = self._manager.find_plugin(url_or_id)
                        if installed_plugin and installed_plugin != 'multiple':
                            # Get the plugin's registry ID or URL
                            registry_id = self._manager.get_plugin_registry_id(installed_plugin)
                            if registry_id:
                                url_or_id = registry_id
                            else:
                                # Get URL from metadata
                                uuid = self._manager._get_plugin_uuid(installed_plugin)
                                metadata = self._manager._metadata.get_plugin_metadata(uuid)
                                if metadata and metadata.url:
                                    # Use URL directly, skip registry lookup
                                    url = metadata.url
                                    self._out.print(f'Reinstalling {installed_plugin.plugin_id} from {url}')
                                    url_or_id = None  # Skip registry lookup

                    # Try to find in registry (if we didn't already get URL from installed plugin)
                    if url_or_id:
                        plugin = self._manager._registry.find_plugin(plugin_id=url_or_id)
                        if plugin:
                            url = plugin.git_url

                            # Auto-select ref if not explicitly specified
                            if not explicit_ref:
                                selected_ref = self._select_ref_for_plugin(plugin)
                                if selected_ref:
                                    ref = selected_ref
                                    self._out.print(f'Found {plugin.name} in registry (using ref: {ref})')
                                else:
                                    self._out.print(f'Found {plugin.name} in registry')
                            else:
                                self._out.print(f'Found {plugin.name} in registry')
                        else:
                            self._out.error(f'Plugin "{url_or_id}" not found in registry')

                            # Suggest similar plugin IDs
                            matches = self._manager.find_similar_plugin_ids(url_or_id)

                            if matches:
                                self._out.print('\nDid you mean one of these?')
                                for match in matches:
                                    self._out.print(f'  {self._out.d_id(match["id"])} - {match["name"]}')

                            return ExitCode.NOT_FOUND
                else:
                    url = url_or_id

                    # Warn if this URL is in the registry
                    registry_plugin = self._manager._registry.find_plugin(url=url)
                    if registry_plugin:
                        plugin_id = registry_plugin.id
                        self._out.warning(f'This URL is available in the registry as {self._out.d_id(plugin_id)}')
                        install_cmd = f'picard plugins --install {plugin_id}'
                        self._out.warning(
                            f'Consider using {self._out.d_command(install_cmd)} '
                            f'for automatic ref selection and trust verification'
                        )

                    # Check if already installed first (unless reinstalling)
                    if not reinstall:
                        # Check if any loaded plugin has this URL
                        existing_plugin = None
                        for plugin in self._manager.plugins:
                            try:
                                uuid = self._manager._get_plugin_uuid(plugin)
                                metadata = self._manager._metadata.get_plugin_metadata(uuid)
                                if metadata and metadata.url == url:
                                    existing_plugin = plugin
                                    break
                            except Exception:
                                continue

                        if existing_plugin:
                            self._out.info(
                                f'Plugin {self._out.d_id(existing_plugin.plugin_id)} is already installed from this URL'
                            )
                            self._out.info(
                                f'Use {self._out.d_command("--reinstall")} to reinstall: '
                                f'{self._out.d_command(f"picard plugins --install {url_or_id} --reinstall")}'
                            )
                            continue

                    # Check blacklist by URL (before prompting user)
                    # UUID-based blacklist will be checked during install after cloning
                    if not force_blacklisted:
                        plugin = UrlInstallablePlugin(url, ref, self._manager._registry)
                        is_blacklisted, blacklist_reason = plugin.is_blacklisted()
                        if is_blacklisted:
                            self._out.error(f'Plugin is blacklisted: {blacklist_reason}')
                            return ExitCode.ERROR

                    # Check trust level and show appropriate warnings
                    trust_level = self._manager._registry.get_trust_level(url)
                    trust_community = getattr(self._args, 'trust_community', False)

                    if trust_level == 'community' and not trust_community:
                        self._out.warning(self._out.d_warning('WARNING: This is a community plugin'))
                        self._out.warning(
                            self._out.d_warning('  Community plugins are not reviewed by the Picard team')
                        )
                        self._out.warning(self._out.d_warning('  Only install plugins from sources you trust'))

                        if not yes:
                            if not self._out.yesno('Do you want to continue?'):
                                self._out.print('Installation cancelled')
                                return ExitCode.CANCELLED

                    elif trust_level == 'unregistered':
                        self._out.warning(self._out.d_warning('WARNING: This plugin is not in the official registry'))
                        self._out.warning(
                            self._out.d_warning('  Installing unregistered plugins may pose security risks')
                        )
                        self._out.warning(self._out.d_warning('  Only install plugins from sources you trust'))

                        if not yes:
                            if not self._out.yesno('Do you want to continue?'):
                                self._out.print('Installation cancelled')
                                return ExitCode.CANCELLED

                if ref:
                    self._out.print(f'Installing plugin from {url} (ref: {ref})...')
                else:
                    self._out.print(f'Installing plugin from {url}...')

                # Check if installing from dirty local git repository
                if check_local_repo_dirty(url):
                    self._out.warning('Local repository has uncommitted changes')

                plugin_id = self._manager.install_plugin(
                    url, ref, reinstall, force_blacklisted, enable_after_install=True
                )
                self._out.success(f'Plugin {self._out.d_id(plugin_id)} installed successfully')
                self._out.info('Restart Picard to load the plugin')
            except Exception as e:
                from picard.plugin3.manager import (
                    PluginAlreadyInstalledError,
                    PluginBlacklistedError,
                    PluginDirtyError,
                    PluginManifestInvalidError,
                    PluginManifestNotFoundError,
                )

                if isinstance(e, PluginAlreadyInstalledError):
                    self._out.info(f'Plugin {self._out.d_id(e.plugin_name)} is already installed from this URL')
                    self._out.info(
                        f'Use {self._out.d_command("--reinstall")} to reinstall: '
                        f'{self._out.d_command(f"picard plugins --install {url_or_id} --reinstall")}'
                    )
                    continue
                elif isinstance(e, PluginDirtyError):
                    success, result = self._handle_dirty_error(
                        e,
                        lambda **kw: self._manager.install_plugin(
                            url, ref, reinstall, force_blacklisted, enable_after_install=True, **kw
                        ),
                    )
                    if not success:
                        return ExitCode.ERROR if yes else ExitCode.SUCCESS
                    plugin_id = result
                    self._out.success(f'Plugin {self._out.d_id(plugin_id)} installed successfully')
                    self._out.info('Restart Picard to load the plugin')
                elif isinstance(e, PluginBlacklistedError):
                    self._out.error(f'Plugin is blacklisted: {e.reason}')
                    self._out.info(
                        f'Use {self._out.d_command("--force-blacklisted")} to install anyway (not recommended)'
                    )
                    return ExitCode.ERROR
                elif isinstance(e, PluginManifestNotFoundError):
                    self._out.error(f'No MANIFEST.toml found in {e.source}')
                    return ExitCode.ERROR
                elif isinstance(e, PluginManifestInvalidError):
                    self._out.error('Invalid MANIFEST.toml:')
                    for error in e.errors:
                        self._out.error(f'  {error}')
                    return ExitCode.ERROR
                else:
                    self._handle_exception(e, 'Failed to install plugin')
                    return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _cmd_remove(self, plugin_names):
        """Uninstall plugins with confirmation."""
        purge = getattr(self._args, 'purge', False)
        yes = getattr(self._args, 'yes', False)

        for plugin_name in plugin_names:
            plugin, error = self._find_plugin_or_error(plugin_name)
            if error:
                return error

            # Check if this is a failed plugin (no manifest)
            is_failed = plugin.manifest is None

            # Confirmation prompt unless --yes flag
            if not yes:
                if not self._out.yesno(f'Uninstall plugin {self._out.d_id(plugin.plugin_id)}?'):
                    self._out.print('Cancelled')
                    continue

                # Ask about config cleanup if not using --purge (skip for failed plugins)
                if not purge and not is_failed:
                    # Only ask if plugin has saved options
                    if self._manager.plugin_has_saved_options(plugin):
                        purge_this = self._out.yesno('Delete plugin saved options?')
                    else:
                        purge_this = False
                else:
                    purge_this = purge
            else:
                purge_this = purge

            try:
                self._out.print(f'Uninstalling {self._out.d_id(plugin.plugin_id)}...')

                if is_failed:
                    # For failed plugins, just remove the directory
                    import shutil

                    plugin_path = Path(plugin.local_path)
                    plugins_dir = Path(self._manager._primary_plugin_dir)

                    # Safety check: ensure we're removing a subdirectory of plugins directory
                    if not plugin_path.is_relative_to(plugins_dir) or plugin_path == plugins_dir:
                        self._out.error(f'Invalid plugin path: {plugin_path}')
                        return ExitCode.ERROR

                    shutil.rmtree(plugin_path)
                    self._out.success('Failed plugin directory removed')
                else:
                    self._manager.uninstall_plugin(plugin, purge_this)
                    if purge_this:
                        self._out.success('Plugin and configuration removed')
                    else:
                        self._out.success('Plugin uninstalled (configuration kept)')
            except Exception as e:
                self._handle_exception(e, 'Failed to uninstall plugin')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _cmd_enable(self, plugin_names):
        """Enable plugins."""
        for plugin_name in plugin_names:
            plugin, error = self._find_plugin_or_error(plugin_name)
            if error:
                return error

            try:
                self._out.print(f'Enabling {self._out.d_id(plugin.plugin_id)}...')
                self._manager.enable_plugin(plugin)
                self._out.success(f'Plugin {self._out.d_status_enabled("enabled")}')
                self._out.info('Restart Picard to load the plugin')
            except Exception as e:
                from picard.plugin3.manager import PluginNoUUIDError
                from picard.plugin3.plugin import PluginAlreadyEnabledError

                if isinstance(e, PluginAlreadyEnabledError):
                    self._out.info(f'Plugin {self._out.d_id(e.plugin_id)} is already enabled')
                    return ExitCode.SUCCESS
                elif isinstance(e, PluginNoUUIDError):
                    self._out.error(f'Plugin {self._out.d_id(e.plugin_id)} has no UUID in manifest')
                else:
                    self._handle_exception(e, 'Failed to enable plugin')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _cmd_disable(self, plugin_names):
        """Disable plugins."""
        for plugin_name in plugin_names:
            plugin, error = self._find_plugin_or_error(plugin_name)
            if error:
                return error

            try:
                self._out.print(f'Disabling {self._out.d_id(plugin.plugin_id)}...')
                self._manager.disable_plugin(plugin)
                self._out.success(f'Plugin {self._out.d_status_disabled("disabled")}')
                self._out.info('Restart Picard for changes to take effect')
            except Exception as e:
                from picard.plugin3.manager import PluginNoUUIDError
                from picard.plugin3.plugin import PluginAlreadyDisabledError

                if isinstance(e, PluginAlreadyDisabledError):
                    self._out.info(f'Plugin {self._out.d_id(e.plugin_id)} is already disabled')
                    return ExitCode.SUCCESS
                elif isinstance(e, PluginNoUUIDError):
                    self._out.error(f'Plugin {self._out.d_id(e.plugin_id)} has no UUID in manifest')
                else:
                    self._handle_exception(e, 'Failed to disable plugin')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _cmd_update(self, plugin_names):
        """Update specific plugins."""
        self._out.print('Updating plugin...')
        for plugin_name in plugin_names:
            plugin, error = self._find_plugin_or_error(plugin_name)
            if error:
                return error

            try:
                result = self._manager.update_plugin(plugin)

                if result.old_commit == result.new_commit:
                    if result.new_version:
                        self._out.info(
                            f'{self._out.d_name(plugin.plugin_id)}: Already up to date ({result.new_version})'
                        )
                    else:
                        self._out.info(f'{self._out.d_name(plugin.plugin_id)}: Already up to date')
                else:
                    version_info = self._format_version_info(result)
                    self._out.success(f'{self._out.d_name(plugin.plugin_id)}: {version_info}')
                    self._out.info('Restart Picard to load the updated plugin')
            except Exception as e:
                from picard.plugin3.manager import (
                    PluginCommitPinnedError,
                    PluginDirtyError,
                    PluginManifestInvalidError,
                    PluginNoSourceError,
                )

                if isinstance(e, PluginCommitPinnedError):
                    self._out.warning(f'Plugin is pinned to commit {self._out.d_commit_old(e.commit)}')
                    self._out.info(
                        f'To update to a different version, use: {self._out.d_command(f"picard plugins --switch-ref {plugin.plugin_id} <branch-or-tag>")}'
                    )
                    continue
                elif isinstance(e, PluginDirtyError):
                    success, result = self._handle_dirty_error(
                        e, lambda **kw: self._manager.update_plugin(plugin, **kw)
                    )
                    if not success:
                        return ExitCode.ERROR if self._args.yes else ExitCode.SUCCESS
                    if result.old_commit != result.new_commit:
                        version_info = self._format_version_info(result)
                        self._out.success(f'{self._out.d_name(plugin.plugin_id)}: {version_info}')
                        self._out.info('Restart Picard to load the updated plugin')
                elif isinstance(e, PluginNoSourceError):
                    self._out.error(f'Plugin {self._out.d_id(e.plugin_id)} has no stored URL, cannot update')
                    self._out.info('This plugin may have been installed from a local directory')
                    return ExitCode.ERROR
                elif isinstance(e, PluginManifestInvalidError):
                    self._out.error('Invalid MANIFEST.toml after update:')
                    for error in e.errors:
                        self._out.error(f'  {error}')
                    return ExitCode.ERROR
                else:
                    self._handle_exception(e, 'Failed to update plugin')
                    return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _cmd_update_all(self):
        """Update all installed plugins."""
        if not self._manager.plugins:
            self._out.print('No plugins installed')
            return ExitCode.SUCCESS

        self._out.print('Updating all plugins...')
        self._out.nl()
        results = self._manager.update_all_plugins()

        updated = 0
        unchanged = 0
        failed = 0

        for r in results:
            if r.success:
                if r.result is None:
                    # Commit-pinned plugin (skipped)
                    self._out.info(f'{self._out.d_name(r.plugin_id)}: {r.error}')
                    unchanged += 1
                elif r.result.old_commit == r.result.new_commit:
                    if r.result.new_version:
                        self._out.info(f'{self._out.d_name(r.plugin_id)}: Already up to date ({r.result.new_version})')
                    else:
                        self._out.info(f'{self._out.d_name(r.plugin_id)}: Already up to date')
                    unchanged += 1
                else:
                    version_info = self._format_version_info(r.result)
                    self._out.success(f'{self._out.d_name(r.plugin_id)}: {version_info}')
                    updated += 1
            else:
                self._out.error(f'{self._out.d_name(r.plugin_id)}: {r.error}')
                failed += 1

        self._out.nl()
        # Build summary with semantic display methods
        summary_parts = []
        if updated > 0:
            summary_parts.append(f'{self._out.d_number(updated)} {self._out.d_status_enabled("updated")}')
        else:
            summary_parts.append(f'{updated} updated')

        if unchanged > 0:
            summary_parts.append(f'{self._out.d_number(unchanged)} {self._out.d_status_disabled("unchanged")}')
        else:
            summary_parts.append(f'{unchanged} unchanged')

        if failed > 0:
            summary_parts.append(f'{self._out.d_number(failed)} {self._out.red("failed")}')
        else:
            summary_parts.append(f'{failed} failed')

        self._out.print(f'Summary: {", ".join(summary_parts)}')
        if updated > 0:
            self._out.info('Restart Picard to load updated plugins')

        return ExitCode.SUCCESS if failed == 0 else ExitCode.ERROR

    def _cmd_check_updates(self):
        """Check for available updates without installing."""
        if not self._manager.plugins:
            self._out.print('No plugins installed')
            return ExitCode.SUCCESS

        self._out.print('Checking for updates...')
        self._out.nl()
        updates = self._manager.check_updates()

        if not updates:
            self._out.success('All plugins are up to date')
        else:
            self._out.print('Updates available:')
            self._out.nl()
            for update in updates.values():
                version_info = self._format_version_info(update)
                self._out.info(f'{self._out.d_name(update.plugin_id)}: {version_info}')
            self._out.nl()
            self._out.print(f'Run with {self._out.d_command("--update-all")} to update all plugins')

        return ExitCode.SUCCESS

    def _cmd_switch_ref(self, plugin_name, ref):
        """Switch plugin to a different git ref."""
        plugin, error = self._find_plugin_or_error(plugin_name)
        if error:
            return error

        try:
            self._out.print(f'Switching {self._out.d_id(plugin.plugin_id)} to ref: {ref}...')
            old_git_ref, new_git_ref, old_commit, new_commit = self._manager.switch_ref(plugin, ref)

            self._out.success(f'Switched: {old_git_ref.shortname} {self._out.d_arrow()} {new_git_ref.shortname}')
            self._out.info(
                f'Commit: {self._out.d_commit_old(short_commit_id(old_commit))} {self._out.d_arrow()} {self._out.d_commit_new(short_commit_id(new_commit))}'
            )
            self._out.info('Restart Picard to load the updated plugin')
        except Exception as e:
            from picard.plugin3.manager import (
                PluginDirtyError,
                PluginManifestInvalidError,
                PluginNoSourceError,
                PluginRefNotFoundError,
                PluginRefSwitchError,
            )

            if isinstance(e, PluginDirtyError):
                success, result = self._handle_dirty_error(e, lambda **kw: self._manager.switch_ref(plugin, ref, **kw))
                if not success:
                    return ExitCode.ERROR if self._args.yes else ExitCode.SUCCESS
                old_git_ref, new_git_ref, old_commit, new_commit = result
                self._out.success(f'Switched: {old_git_ref.shortname} {self._out.d_arrow()} {new_git_ref.shortname}')
                self._out.info(
                    f'Commit: {self._out.d_commit_old(short_commit_id(old_commit))} {self._out.d_arrow()} {self._out.d_commit_new(short_commit_id(new_commit))}'
                )
                self._out.info('Restart Picard to load the updated plugin')
            elif isinstance(e, PluginRefNotFoundError):
                self._out.error(f"Ref '{ref}' not found")
                self._out.info(
                    f'Use {self._out.d_command(f"picard plugins --list-refs {plugin.plugin_id}")} to see available refs'
                )
                return ExitCode.ERROR
            elif isinstance(e, PluginNoSourceError):
                self._out.error(f'Plugin {self._out.d_id(e.plugin_id)} has no stored URL, cannot switch ref')
                self._out.info('This plugin may have been installed from a local directory')
                return ExitCode.ERROR
            elif isinstance(e, PluginRefSwitchError):
                self._out.error(f'Cannot switch to ref {ref}: {e.original_error}')
                return ExitCode.ERROR
            elif isinstance(e, PluginManifestInvalidError):
                self._out.error('Invalid MANIFEST.toml after switching ref:')
                for error in e.errors:
                    self._out.error(f'  {error}')
                return ExitCode.ERROR
            elif isinstance(e, ValueError) and 'not found' in str(e):
                self._out.error(f"Ref '{ref}' not found")
                self._out.info(
                    f'Use {self._out.d_command(f"picard plugins --list-refs {plugin.plugin_id}")} to see available refs'
                )
                return ExitCode.ERROR
            else:
                self._handle_exception(e, 'Failed to switch ref')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _cmd_clean_config(self, plugin_identifier):
        """Clean saved options for a plugin or list orphaned configs."""
        # If no plugin identifier provided, list orphaned configs
        if not plugin_identifier:
            orphaned = self._manager.get_orphaned_plugin_configs()
            if not orphaned:
                self._out.print('No orphaned plugin configurations found')
                return ExitCode.SUCCESS

            self._out.print('Orphaned plugin configurations (no plugin installed):')
            for plugin_uuid in orphaned:
                self._out.print(f'  • {self._out.d_uuid(plugin_uuid)}')
            self._out.nl()
            self._out.print(f'Clean with: {self._out.d_command("picard plugins --clean-config <uuid>")}')
            return ExitCode.SUCCESS

        yes = getattr(self._args, 'yes', False)

        # Try to find the plugin first (don't show error yet)
        plugin = self._manager.find_plugin(plugin_identifier)
        if plugin == 'multiple':
            # Find all matches to show to user
            identifier_lower = plugin_identifier.lower()
            matches = [p for p in self._manager.plugins if p.manifest and p.manifest.name().lower() == identifier_lower]
            self._out.error(f'Multiple plugins found with name "{plugin_identifier}":')
            for p in matches:
                self._out.error(f'  - {self._out.d_id(p.plugin_id)} (UUID: {self._out.d_uuid(p.uuid)})')
            self._out.error('Please use the Plugin ID or UUID to be more specific')
            return ExitCode.ERROR

        if plugin and plugin.uuid:
            # Plugin is installed, use its UUID
            plugin_uuid = plugin.uuid
            display_name = plugin.plugin_id
        else:
            # Not installed, assume identifier is a UUID
            plugin_uuid = plugin_identifier
            display_name = plugin_uuid

        # Check if plugin config exists
        config = self._manager._config if hasattr(self._manager, '_config') else get_config()
        config_key = f'plugin.{plugin_uuid}'
        config.beginGroup(config_key)
        has_config = len(config.childKeys()) > 0
        config.endGroup()

        if not has_config:
            self._out.print(f'No saved options found for "{display_name}"')

            # Show orphaned configs
            orphaned = self._manager.get_orphaned_plugin_configs()
            if orphaned:
                self._out.nl()
                self._out.print('Orphaned plugin configurations (no plugin installed):')
                for uuid in orphaned:
                    self._out.print(f'  • {self._out.d_uuid(uuid)}')
                self._out.nl()
                self._out.print(f'Clean with: {self._out.d_command("picard plugins --clean-config <uuid>")}')
            return ExitCode.SUCCESS

        if not yes:
            if not self._out.yesno(f'Delete saved options for "{display_name}"?'):
                self._out.print('Cancelled')
                return ExitCode.SUCCESS

        try:
            self._manager._clean_plugin_config(plugin_uuid)
            self._out.success(f'Saved options for {display_name} deleted')
        except Exception as e:
            self._handle_exception(e, 'Failed to clean saved options')
            return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _find_plugin_or_error(self, identifier):
        """Find plugin and handle errors (not found or ambiguous).

        Returns:
            (plugin, error_code) - plugin is None if error, error_code is None if success
        """
        result = self._manager.find_plugin(identifier)

        if result == 'multiple':
            # Find all matches to show to user
            identifier_lower = identifier.lower()
            matches = [p for p in self._manager.plugins if p.manifest and p.manifest.name().lower() == identifier_lower]

            self._out.error(f'Multiple plugins found with name "{identifier}":')
            for plugin in matches:
                self._out.error(f'  - {self._out.d_id(plugin.plugin_id)} (UUID: {self._out.d_uuid(plugin.uuid)})')
            self._out.error('Please use the Plugin ID or UUID to be more specific')
            return None, ExitCode.ERROR

        if not result:
            # Check if it's a failed plugin directory name
            for plugin_dir, plugin_name, _ in self._manager._failed_plugins:
                if plugin_name == identifier or str(plugin_dir).endswith(identifier):
                    # Return a minimal plugin-like object with just the path
                    from types import SimpleNamespace

                    actual_path = Path(plugin_dir) / plugin_name
                    failed_plugin = SimpleNamespace(local_path=actual_path, plugin_id=plugin_name, manifest=None)
                    return failed_plugin, None

            self._out.error(f'Plugin "{identifier}" not found')
            return None, ExitCode.NOT_FOUND

        return result, None

    def _cmd_validate(self, url, ref=None):
        """Validate a plugin from git URL or local directory."""

        self._out.print(f'Validating plugin from: {url}')

        # Check if url is a local directory
        local_path = get_local_repository_path(url)
        if local_path:
            # Validate local directory directly
            self._out.success('MANIFEST.toml found')

            try:
                # Read and validate manifest using manager method
                from picard.plugin3.manager import (
                    PluginManifestError,
                    PluginManifestInvalidError,
                    PluginManifestNotFoundError,
                )

                manifest = self._manager._read_and_validate_manifest(local_path, str(local_path))

                # If we get here, validation passed

                # Show plugin info
                self._out.success('Validation passed')
                self._out.nl()
                self._out.print('Plugin Information:')
                self._out.info(f'  Name: {manifest.name()}')

                # Show available name translations
                name_i18n = manifest._data.get('name_i18n', {})
                if name_i18n:
                    self._out.info(f'  Name_i18n: {", ".join(sorted(name_i18n.keys()))}')

                self._out.info(f'  Version: {manifest._data.get("version", "")}')

                # Optional fields - only show if present
                if manifest.authors:
                    self._out.info(f'  Authors: {", ".join(manifest.authors)}')

                if manifest.maintainers:
                    self._out.info(f'  Maintainers: {", ".join(manifest.maintainers)}')

                self._out.info(f'  Description: {manifest.description()}')

                # Show available description translations
                desc_i18n = manifest._data.get('description_i18n', {})
                if desc_i18n:
                    self._out.info(f'  Description_i18n: {", ".join(sorted(desc_i18n.keys()))}')

                # Show long description if available
                long_desc = manifest.long_description()
                if long_desc:
                    self._out.info(f'  Long description: {long_desc}')

                    # Show available long description translations
                    long_desc_i18n = manifest._data.get('long_description_i18n', {})
                    if long_desc_i18n:
                        self._out.info(f'  Long_description_i18n: {", ".join(sorted(long_desc_i18n.keys()))}')

                api_versions = manifest._data.get('api', [])
                self._out.info(f'  API versions: {", ".join(api_versions)}')

                # Show license fields if present
                if manifest.license:
                    self._out.info(f'  License: {manifest.license}')

                if manifest.license_url:
                    self._out.info(f'  License URL: {manifest.license_url}')

                # Show optional fields
                categories = manifest._data.get('categories', [])
                if categories:
                    self._out.info(f'  Categories: {", ".join(categories)}')

                homepage = manifest._data.get('homepage')
                if homepage:
                    self._out.info(f'  Homepage: {homepage}')

                min_python = manifest._data.get('min_python_version')
                if min_python:
                    self._out.info(f'  Min Python version: {min_python}')

                return ExitCode.SUCCESS

            except PluginManifestNotFoundError:
                self._out.error('No MANIFEST.toml found')
                return ExitCode.ERROR
            except PluginManifestInvalidError as e:
                self._out.nl()
                self._out.error('Validation failed:')
                self._out.nl()
                self._out.error(f'  • {e}')
                return ExitCode.ERROR
            except PluginManifestError as e:
                self._out.error(f'Manifest error: {e}')
                return ExitCode.ERROR
            except Exception as e:
                self._handle_exception(e, 'Validation error')
                return ExitCode.ERROR

        # Handle git URL
        if ref:
            self._out.print(f'Using ref: {ref}')

        temp_path = Path(tempfile.mkdtemp(prefix='picard-validate-'))

        try:
            # Clone repository
            self._out.print('Cloning repository...')
            source = PluginSourceGit(url, ref)
            # Remove the temp directory so git clone can create it
            import shutil

            shutil.rmtree(temp_path)
            source.sync(temp_path, shallow=True)

            # Check for MANIFEST.toml and validate using manager method
            self._out.success('MANIFEST.toml found')

            from picard.plugin3.manager import (
                PluginManifestError,
                PluginManifestInvalidError,
                PluginManifestNotFoundError,
            )

            try:
                manifest = self._manager._read_and_validate_manifest(temp_path, url)
            except PluginManifestNotFoundError:
                self._out.error('No MANIFEST.toml found')
                return ExitCode.ERROR
            except PluginManifestInvalidError as e:
                self._out.nl()
                self._out.error('Validation failed:')
                self._out.nl()
                self._out.error(f'  • {e}')
                return ExitCode.ERROR
            except PluginManifestError as e:
                self._out.error(f'Manifest error: {e}')
                return ExitCode.ERROR

            # Show plugin info
            self._out.success('Validation passed')
            self._out.nl()
            self._out.print('Plugin Information:')
            self._out.info(f'  Name: {self._out.d_name(manifest.name())}')

            # Show available name translations
            name_i18n = manifest._data.get('name_i18n', {})
            if name_i18n:
                self._out.info(f'  Name_i18n: {", ".join(sorted(name_i18n.keys()))}')

            self._out.info(f'  Version: {self._out.d_version(manifest._data.get("version", ""))}')

            # Optional fields - only show if present
            if manifest.authors:
                self._out.info(f'  Authors: {", ".join(manifest.authors)}')

            if manifest.maintainers:
                self._out.info(f'  Maintainers: {", ".join(manifest.maintainers)}')

            self._out.info(f'  Description: {manifest.description()}')

            # Show available description translations
            desc_i18n = manifest._data.get('description_i18n', {})
            if desc_i18n:
                self._out.info(f'  Description_i18n: {", ".join(sorted(desc_i18n.keys()))}')

            # Show long description if available
            long_desc = manifest.long_description()
            if long_desc:
                self._out.info(f'  Long description: {long_desc}')

                # Show available long description translations
                long_desc_i18n = manifest._data.get('long_description_i18n', {})
                if long_desc_i18n:
                    self._out.info(f'  Long_description_i18n: {", ".join(sorted(long_desc_i18n.keys()))}')

            api_versions = manifest._data.get('api', [])
            self._out.info(f'  API versions: {", ".join(api_versions)}')

            # Show license fields if present
            if manifest.license:
                self._out.info(f'  License: {manifest.license}')

            if manifest.license_url:
                self._out.info(f'  License URL: {self._out.d_url(manifest.license_url)}')

            # Show optional fields
            categories = manifest._data.get('categories', [])
            if categories:
                self._out.info(f'  Categories: {", ".join(categories)}')

            homepage = manifest._data.get('homepage')
            if homepage:
                self._out.info(f'  Homepage: {self._out.d_url(homepage)}')

            min_python = manifest._data.get('min_python_version')
            if min_python:
                self._out.info(f'  Min Python version: {min_python}')

            return ExitCode.SUCCESS

        except Exception as e:
            self._handle_exception(e, 'Validation error')
            return ExitCode.ERROR
        finally:
            # Cleanup
            import shutil

            shutil.rmtree(temp_path, ignore_errors=True)

    def _build_filter_description(self, category=None, trust_level=None, query=None):
        """Build filter description for display.

        Returns:
            list: List of filter strings (e.g. ['query: "test"', 'category: ui'])
        """
        filters = []
        if query:
            filters.append(f'query: "{query}"')
        if category:
            filters.append(f'category: {category}')
        if trust_level:
            filters.append(f'trust: {trust_level}')
        return filters

    def _cmd_browse(self):
        """Browse plugins from registry."""
        category = getattr(self._args, 'category', None)
        trust_level = getattr(self._args, 'trust', None)

        try:
            plugins = self._manager.search_registry_plugins(category=category, trust_level=trust_level)

            filters = self._build_filter_description(category=category, trust_level=trust_level)

            if not plugins:
                if filters:
                    self._out.print(f'No plugins found ({", ".join(filters)})')
                else:
                    self._out.print('No plugins found in registry')
                return ExitCode.SUCCESS

            # Show header
            if filters:
                self._out.print(f'Registry plugins ({", ".join(filters)}):')
                self._out.nl()
            else:
                self._out.print('Registry plugins:')
                self._out.nl()

            # Get system locale for displaying localized plugin info
            locale_str = get_display_locale(self._args)

            # Sort plugins by name
            sorted_plugins = sorted(plugins, key=lambda p: p.name.lower())

            # Show plugins
            for plugin in sorted_plugins:
                trust_badge = self._get_trust_badge(plugin.trust_level)
                name = get_localized_registry_field(plugin, 'name', locale_str)
                description = get_localized_registry_field(plugin, 'description', locale_str)

                self._out.print(f'{trust_badge} {self._out.d_name(name)}')
                self._out.info(f'  {description}')

                # Show version if available
                version = self._get_registry_plugin_version(plugin)
                if version:
                    self._out.info(f'  Latest version: {self._out.d_version(version)}')

                categories = plugin.categories
                if categories:
                    self._out.info(f'  Categories: {", ".join(categories)}')
                self._out.info(f'  Registry ID: {self._out.d_id(plugin.id)}')
                self._out.print('')

            self._out.print(f'Total: {self._out.d_number(len(plugins))} plugin(s)')
            self._out.nl()
            self._out.print(f'Install with: {self._out.d_command("picard plugins --install <registry-id>")}')

            return ExitCode.SUCCESS

        except Exception as e:
            self._handle_exception(e, 'Failed to browse plugins')
            return ExitCode.ERROR

    def _cmd_search(self, query):
        """Search plugins in registry."""
        category = getattr(self._args, 'category', None)
        trust_level = getattr(self._args, 'trust', None)

        try:
            results = self._manager.search_registry_plugins(query=query, category=category, trust_level=trust_level)

            # Build filter description
            filters = self._build_filter_description(category=category, trust_level=trust_level, query=query)

            if not results:
                self._out.print(f'No plugins found ({", ".join(filters)})')
                return ExitCode.SUCCESS

            # Sort results by name
            sorted_results = sorted(results, key=lambda p: p.get('name', '').lower())

            # Show header with filters
            self._out.print(f'Found {self._out.d_number(len(sorted_results))} plugin(s) ({", ".join(filters)}):')
            self._out.nl()

            # Get system locale for displaying localized plugin info
            locale_str = get_display_locale(self._args)

            for plugin in sorted_results:
                trust_badge = self._get_trust_badge(plugin.trust_level)
                name = get_localized_registry_field(plugin, 'name', locale_str)
                description = get_localized_registry_field(plugin, 'description', locale_str)

                self._out.print(f'{trust_badge} {self._out.d_name(name)}')
                self._out.info(f'  {description}')

                # Show version if available
                version = self._get_registry_plugin_version(plugin)
                if version:
                    self._out.info(f'  Latest version: {self._out.d_version(version)}')

                categories = plugin.categories
                if categories:
                    self._out.info(f'  Categories: {", ".join(categories)}')
                self._out.info(f'  Registry ID: {self._out.d_id(plugin.id)}')
                self._out.print('')

            self._out.print('Install with: {}'.format(self._out.d_command("picard plugins --install <registry-id>")))

            return ExitCode.SUCCESS

        except Exception as e:
            self._handle_exception(e, 'Failed to search plugins')
            return ExitCode.ERROR

    def _cmd_check_blacklist(self, url):
        """Check if a URL is blacklisted."""
        try:
            plugin = UrlInstallablePlugin(url, registry=self._manager._registry)

            is_blacklisted, blacklist_reason = plugin.is_blacklisted()
            if is_blacklisted:
                self._out.error(f'URL is blacklisted: {blacklist_reason}')
                return ExitCode.ERROR
            else:
                self._out.success('URL is not blacklisted')
                return ExitCode.SUCCESS

        except Exception as e:
            self._handle_exception(e, 'Failed to check blacklist')
            return ExitCode.ERROR

    def _cmd_refresh_registry(self):
        """Force refresh of plugin registry cache."""
        try:
            self._out.print('Refreshing plugin registry...')

            self._manager.refresh_registry_and_caches()

            info = self._manager._registry.get_registry_info()
            self._out.success('Registry refreshed successfully')
            self._out.print(f'Registry URL: {info["registry_url"]}')
            self._out.print(f'Plugins available: {info["plugin_count"]}')

            return ExitCode.SUCCESS

        except RegistryFetchError as e:
            self._out.error(f'Failed to fetch registry from {e.url}')
            self._out.error(f'Error: {e.original_error}')
            return ExitCode.ERROR
        except RegistryParseError as e:
            self._out.error(f'Failed to parse registry from {e.url}')
            self._out.error(f'Error: {e.original_error}')
            return ExitCode.ERROR
        except Exception as e:
            self._handle_exception(e, 'Failed to refresh registry')
            return ExitCode.ERROR

    def _read_manifest(self, path):
        """Read and return manifest content from path."""
        try:
            with open(path / 'MANIFEST.toml', 'rb') as f:
                return f.read().decode('utf-8')
        except FileNotFoundError:
            return None

    def _cmd_manifest(self, target):
        """Show MANIFEST.toml template or from plugin."""
        # No argument - show template
        if not target:
            template = generate_manifest_template()
            self._out.print(template)
            return ExitCode.SUCCESS

        # Check if it's an installed plugin
        plugin = self._manager.find_plugin(target)
        if plugin:
            content = self._read_manifest(plugin.local_path)
            if content is not None:
                self._out.print(content)
                return ExitCode.SUCCESS
            self._out.error(f'MANIFEST.toml not found for plugin {target}')
            return ExitCode.ERROR

        # Check if it's a local directory
        local_path = get_local_repository_path(target)
        if local_path:
            content = self._read_manifest(local_path)
            if content is not None:
                self._out.print(content)
                return ExitCode.SUCCESS
            self._out.error(f'MANIFEST.toml not found in {target}')
            return ExitCode.ERROR

        # Treat as git URL
        temp_path = Path(tempfile.mkdtemp(prefix='picard-manifest-'))

        try:
            self._out.print(f'Fetching from {target}...')
            source = PluginSourceGit(target, None)
            # Remove temp dir so git can create it
            import shutil

            shutil.rmtree(temp_path)
            source.sync(temp_path, shallow=True)

            content = self._read_manifest(temp_path)
            if content is not None:
                self._out.print(content)
                return ExitCode.SUCCESS
            self._out.error('MANIFEST.toml not found in repository')
            return ExitCode.ERROR

        except Exception as e:
            self._handle_exception(e, 'Failed to fetch manifest')
            return ExitCode.ERROR
        finally:
            import shutil

            shutil.rmtree(temp_path, ignore_errors=True)

    def _get_trust_badge(self, trust_level):
        """Get badge emoji for trust level."""
        badges = {
            'official': '🛡️',
            'trusted': '✓',
            'community': '⚠️',
            'unregistered': '🔓',
        }
        return badges.get(trust_level, '?')


def process_cmdline_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    # Picard specific arguments
    parser.add_argument('-c', '--config-file', action='store', default=None, help="location of the configuration file")
    parser.add_argument('--debug', action='store_true', help="enable debug-level logging")
    parser.add_argument('-v', '--version', action='store_true', help="display version information and exit")
    parser.add_argument('-V', '--long-version', action='store_true', help="display long version information and exit")
    parser.add_argument(
        '--debug-opts',
        action='store',
        default=None,
        help="comma-separated list of debug options to enable: %s" % DebugOpt.opt_names(),
    )
    parser.add_argument('--yes', '-y', action='store_true', help="skip confirmation prompts")
    parser.add_argument('--no-color', action='store_true', help="disable colored output")

    group_management = parser.add_argument_group("Plugin Management")
    group_management.add_argument('-l', '--list', action='store_true', help="list all installed plugins with details")
    group_management.add_argument(
        '-i', '--install', nargs='+', metavar='URL', help="install plugin(s) from git URL(s) or by name"
    )
    group_management.add_argument('-r', '--remove', nargs='+', metavar='PLUGIN', help="uninstall plugin(s)")
    group_management.add_argument('-e', '--enable', nargs='+', metavar='PLUGIN', help="enable plugin(s)")
    group_management.add_argument('-d', '--disable', nargs='+', metavar='PLUGIN', help="disable plugin(s)")
    group_management.add_argument(
        '-u', '--update', nargs='+', metavar='PLUGIN', help="update plugin(s) to latest version"
    )
    group_management.add_argument('--update-all', action='store_true', help="update all installed plugins")
    group_management.add_argument('--info', metavar='PLUGIN', help="show detailed plugin information")
    group_management.add_argument('--validate', metavar='URL', help="validate plugin MANIFEST from git URL")
    group_management.add_argument(
        '--clean-config',
        nargs='?',
        const='',
        metavar='PLUGIN',
        help="delete saved options for a plugin (list orphaned configs if no plugin specified)",
    )
    group_management.add_argument(
        '--manifest', nargs='?', const='', metavar='PLUGIN', help="show MANIFEST.toml (template if no argument)"
    )

    group_git = parser.add_argument_group("Git Version Control")
    group_git.add_argument('--list-refs', metavar='PLUGIN', help="list available git refs (branches/tags) for plugin")
    group_git.add_argument(
        '--ref', metavar='REF', help="git ref (branch/tag/commit) to use with --install or --validate"
    )
    group_git.add_argument(
        '--switch-ref', nargs=2, metavar=('PLUGIN', 'REF'), help="switch plugin to different git ref"
    )

    group_discover = parser.add_argument_group("Plugin Discovery")
    group_discover.add_argument('--browse', action='store_true', help="browse plugins from registry")
    group_discover.add_argument('--search', metavar='QUERY', help="search plugins in registry")
    group_discover.add_argument('--check-blacklist', metavar='URL', help="check if URL is blacklisted")

    group_registry = parser.add_argument_group("Registry")
    group_registry.add_argument(
        '--refresh-registry', action='store_true', help="force refresh of plugin registry cache"
    )
    group_registry.add_argument('--check-updates', action='store_true', help="check for available updates")

    group_advanced = parser.add_argument_group("Advanced Options")
    group_advanced.add_argument('--reinstall', action='store_true', help="force reinstall when used with --install")
    group_advanced.add_argument('--force-blacklisted', action='store_true', help="bypass blacklist check (dangerous!)")
    group_advanced.add_argument('--trust-community', action='store_true', help="skip warnings for community plugins")
    group_advanced.add_argument('--trust', metavar='LEVEL', help="filter by trust level (official, trusted, community)")
    group_advanced.add_argument(
        '--category', metavar='CATEGORY', help="filter by category (metadata, coverart, ui, etc.)"
    )
    group_advanced.add_argument('--purge', action='store_true', help="delete plugin saved options on uninstall")
    group_advanced.add_argument(
        '--locale', metavar='LOCALE', default='en', help="locale for displaying plugin info (e.g., 'fr', 'de', 'en')"
    )

    # Additional information
    parser.description = "Manage Picard plugins (install, update, enable, disable)"
    parser.epilog = (
        "Trust Levels:\n"
        "  🛡️ official: Reviewed by Picard team (highest trust)\n"
        "  ✓ trusted: Known authors, not reviewed (high trust)\n"
        "  ⚠️ community: Other authors, not reviewed (use caution)\n"
        "  🔓 unregistered: Not in registry (local/unknown source - lowest trust)\n"
        "\nFor more information, visit: https://picard.musicbrainz.org/docs/plugins/"
    )

    args = parser.parse_args()
    args.remote_commands_help = False

    return args, parser


def minimal_init(config_file=None):
    """Minimal initialization for CLI commands without GUI.

    Returns a QCoreApplication instance with config initialized.
    """
    QtCore.QCoreApplication.setApplicationName(PICARD_APP_NAME)
    QtCore.QCoreApplication.setOrganizationName(PICARD_ORG_NAME)

    app = QtCore.QCoreApplication(sys.argv)

    init_options()
    setup_config(app=app, filename=config_file)

    return app


def main():
    try:
        if not has_git_backend():
            cli.print_message_and_exit("git backend not available", status=1)
    except ImportError as err:
        cli.print_message_and_exit("failed importing git backend", str(err), status=1)

    cmdline_args, parser = process_cmdline_args()

    app = minimal_init(cmdline_args.config_file)  # noqa: F841 - app must stay alive for QCoreApplication

    if cmdline_args.long_version:
        cli.print_message_and_exit(versions.as_string())
    if cmdline_args.version:
        cli.print_message_and_exit(f"{PICARD_ORG_NAME} {PICARD_APP_NAME} {PICARD_FANCY_VERSION_STR}")

    log.enable_console_handler()

    # Suppress INFO logs for cleaner CLI output unless in debug mode or debug options are enabled
    if not cmdline_args.debug and not cmdline_args.debug_opts:
        log.set_verbosity(logging.WARNING)
    elif cmdline_args.debug or cmdline_args.debug_opts:
        # Ensure DEBUG level is enabled when requested or debug options are used
        log.set_verbosity(logging.DEBUG)

    # Initialize debug options for CLI
    if cmdline_args.debug_opts:
        DebugOpt.from_string(cmdline_args.debug_opts)

    manager = PluginManager()
    manager.add_directory(USER_PLUGIN_DIR, primary=True)

    # Create output with color setting from args
    color = not getattr(cmdline_args, 'no_color', False)
    output = PluginOutput(color=color)

    exit_code = PluginCLI(manager, cmdline_args, output=output, parser=parser).run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
