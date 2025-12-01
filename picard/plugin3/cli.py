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

from enum import IntEnum

from picard import log
from picard.plugin3.output import PluginOutput
from picard.plugin3.plugin import short_commit_id


class ExitCode(IntEnum):
    """Exit codes for plugin CLI commands."""

    SUCCESS = 0
    ERROR = 1
    NOT_FOUND = 2
    CANCELLED = 130


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


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
            import traceback

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
        if result.old_ref and result.new_ref and result.old_ref != result.new_ref:
            version_info = (
                f'{self._out.d_version(result.old_ref)} ({self._out.d_commit_old(short_commit_id(result.old_commit))}) '
                f'{self._out.d_arrow()} '
                f'{self._out.d_version(result.new_ref)} ({self._out.d_commit_new(short_commit_id(result.new_commit))})'
            )
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
        # Just show commits
        else:
            version_info = (
                f'{self._out.d_commit_old(short_commit_id(result.old_commit))} '
                f'{self._out.d_arrow()} '
                f'{self._out.d_commit_new(short_commit_id(result.new_commit))}'
            )

        # Append date if available
        if hasattr(result, 'commit_date'):
            from datetime import datetime

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
            # Validate that --ref is only used with --install or --validate
            ref = getattr(self._args, 'ref', None)
            if ref:
                valid_with_ref = self._args.install or (hasattr(self._args, 'validate') and self._args.validate)
                if not valid_with_ref:
                    self._out.error('--ref can only be used with --install or --validate')
                    return ExitCode.ERROR

            if self._args.list:
                return self._list_plugins()
            elif self._args.info:
                return self._show_info(self._args.info)
            elif self._args.status:
                return self._show_status(self._args.status)
            elif self._args.enable:
                return self._enable_plugins(self._args.enable)
            elif self._args.disable:
                return self._disable_plugins(self._args.disable)
            elif self._args.install:
                return self._install_plugins(self._args.install)
            elif self._args.uninstall:
                return self._uninstall_plugins(self._args.uninstall)
            elif self._args.update:
                return self._update_plugins(self._args.update)
            elif self._args.update_all:
                return self._update_all_plugins()
            elif self._args.check_updates:
                return self._check_updates()
            elif hasattr(self._args, 'browse') and self._args.browse:
                return self._browse_plugins()
            elif hasattr(self._args, 'search') and self._args.search:
                return self._search_plugins(self._args.search)
            elif hasattr(self._args, 'check_blacklist') and self._args.check_blacklist:
                return self._check_blacklist(self._args.check_blacklist)
            elif hasattr(self._args, 'refresh_registry') and self._args.refresh_registry:
                return self._refresh_registry()
            elif hasattr(self._args, 'switch_ref') and self._args.switch_ref:
                return self._switch_ref(self._args.switch_ref[0], self._args.switch_ref[1])
            elif hasattr(self._args, 'clean_config') and self._args.clean_config:
                return self._clean_config(self._args.clean_config)
            elif hasattr(self._args, 'validate') and self._args.validate:
                return self._validate_plugin(self._args.validate, ref)
            elif hasattr(self._args, 'manifest') and self._args.manifest is not None:
                return self._show_manifest(self._args.manifest)
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

    def _format_git_info(self, metadata):
        """Format git ref and commit info compactly.

        Returns string like "(ref @commit)" or "(@commit)" if ref is a commit hash.
        Returns empty string if no metadata.
        """
        if not metadata:
            return ''

        ref = metadata.get('ref', '')
        commit = metadata.get('commit', '')

        if not commit:
            return ''

        commit_short = short_commit_id(commit)
        # Skip ref if it's a commit hash (same as or starts with the commit short ID)
        if ref and not ref.startswith(commit_short):
            return f' ({ref} @{commit_short})'
        return f' (@{commit_short})'

    def _select_ref_for_plugin(self, plugin):
        """Select appropriate ref for plugin based on versioning scheme or Picard API version.

        Args:
            plugin: Plugin data from registry

        Returns:
            str: Selected ref name, or None if no refs specified
        """
        # Check for versioning_scheme first
        versioning_scheme = plugin.get('versioning_scheme')
        if versioning_scheme:
            url = plugin.get('git_url')
            if url:
                tags = self._manager._fetch_version_tags(url, versioning_scheme)
                if tags:
                    # Return latest tag
                    return tags[0]
                else:
                    log.warning('No version tags found for %s with scheme %s', url, versioning_scheme)
                    # Fall through to ref selection

        # Original ref selection logic
        from picard import api_versions_tuple

        refs = plugin.get('refs')
        if not refs:
            return None

        # Get current Picard API version as string (e.g., "3.0")
        current_api = '.'.join(map(str, api_versions_tuple[:2]))

        # Find first compatible ref
        for ref in refs:
            min_api = ref.get('min_api_version')
            max_api = ref.get('max_api_version')

            # Skip if below minimum
            if min_api and current_api < min_api:
                continue

            # Skip if above maximum
            if max_api and current_api > max_api:
                continue

            # Compatible ref found
            return ref['name']

        # No compatible ref found, use first (default)
        return refs[0]['name']

    def _list_plugins(self):
        """List all installed plugins with details."""
        if not self._manager.plugins:
            if not self._manager._failed_plugins:
                self._out.print('No plugins installed')
                return ExitCode.SUCCESS
            # Only failed plugins, skip to showing them
        else:
            self._out.print('Installed plugins:')
            self._out.nl()
            # Sort plugins by display name
            sorted_plugins = sorted(
                self._manager.plugins,
                key=lambda p: (p.manifest.name() if p.manifest else p.plugin_id).lower(),
            )
            for plugin in sorted_plugins:
                # Get plugin UUID for checking enabled state
                plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
                is_enabled = plugin_uuid and plugin_uuid in self._manager._enabled_plugins

                # Show manifest name (human-readable) instead of directory name
                display_name = plugin.manifest.name() if plugin.manifest else plugin.plugin_id

                # Display with semantic methods
                if is_enabled:
                    status = self._out.d_status_enabled()
                else:
                    status = self._out.d_status_disabled()

                self._out.print(f'  {self._out.d_name(display_name)} ({status})')

                if hasattr(plugin, 'manifest') and plugin.manifest:
                    desc = plugin.manifest.description()
                    if desc:
                        self._out.info(f'  {desc}')
                    metadata = self._manager._get_plugin_metadata(plugin_uuid) if plugin_uuid else {}
                    git_info = self._format_git_info(metadata)
                    version = plugin.manifest._data.get('version', '')
                    if git_info:
                        self._out.info(f'  Version: {self._out.d_version(version)}{self._out.d_git_info(git_info)}')
                    else:
                        self._out.info(f'  Version: {self._out.d_version(version)}')
                    self._out.info(f'  Path: {self._out.d_path(plugin.local_path)}')
                self._out.print()

            total = len(self._manager.plugins)
            enabled = sum(
                1 for p in self._manager.plugins if p.manifest and p.manifest.uuid in self._manager._enabled_plugins
            )
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
                from pathlib import Path

                full_path = Path(plugin_dir) / plugin_name
                self._out.print(f'  • {plugin_name}')
                self._out.print(f'    Error: {error_msg}')
                self._out.print(f'    Path: {full_path}')
                self._out.nl()

        return ExitCode.SUCCESS

    def _show_info(self, plugin_name):
        """Show detailed information about a plugin."""
        plugin, error = self._find_plugin_or_error(plugin_name)
        if error:
            return error

        plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
        is_enabled = plugin_uuid and plugin_uuid in self._manager._enabled_plugins
        metadata = self._manager._get_plugin_metadata(plugin_uuid) if plugin_uuid else {}
        git_info = self._format_git_info(metadata)

        self._out.print(f'Plugin: {self._out.d_name(plugin.manifest.name())}')

        # Show short description on one line (required field)
        desc = plugin.manifest.description()
        if desc:
            self._out.print(f'Description: {desc}')

        self._out.print(f'UUID: {self._out.d_uuid(plugin_uuid)}')

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

        # Version
        version = plugin.manifest._data.get('version', '')
        if git_info:
            self._out.print(f'Version: {self._out.d_version(version)}{self._out.d_git_info(git_info)}')
        else:
            self._out.print(f'Version: {self._out.d_version(version)}')

        # Show source URL if available
        if metadata and metadata.get('url'):
            self._out.print(f'Source: {self._out.d_url(metadata["url"])}')

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

    def _show_status(self, plugin_name):
        """Show detailed status information about a plugin."""
        plugin, error = self._find_plugin_or_error(plugin_name)
        if error:
            return error

        self._out.print(f'Plugin: {self._out.d_id(plugin.plugin_id)}')
        self._out.print(f'State: {plugin.state.value}')

        if plugin.manifest:
            version = plugin.manifest._data.get('version', '')
            self._out.print(f'Version: {self._out.d_version(version)}')
            api_versions = plugin.manifest._data.get('api', [])
            self._out.print(f'API Versions: {", ".join(api_versions)}')

        enabled_status = 'yes' if plugin.plugin_id in self._manager._enabled_plugins else 'no'
        self._out.print(f'Enabled in config: {enabled_status}')

        metadata = self._manager._get_plugin_metadata(plugin.plugin_id)
        if metadata:
            self._out.print(f'Source URL: {self._out.d_url(metadata.get("url", "N/A"))}')
            self._out.print(f'Git ref: {metadata.get("ref", "N/A")}')
            commit = metadata.get('commit', 'N/A')
            if commit != 'N/A':
                commit = short_commit_id(commit)
            self._out.print(f'Commit: {self._out.d_commit_old(commit)}')

        return ExitCode.SUCCESS

    def _install_plugins(self, plugin_urls):
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
                    # Try to find in registry
                    plugin = self._manager._registry.find_plugin(plugin_id=url_or_id)
                    if plugin:
                        url = plugin['git_url']

                        # Auto-select ref if not explicitly specified
                        if not explicit_ref:
                            selected_ref = self._select_ref_for_plugin(plugin)
                            if selected_ref:
                                ref = selected_ref
                                self._out.print(f'Found {plugin["name"]} in registry (using ref: {ref})')
                            else:
                                self._out.print(f'Found {plugin["name"]} in registry')
                        else:
                            self._out.print(f'Found {plugin["name"]} in registry')
                    else:
                        self._out.error(f'Plugin "{url_or_id}" not found in registry')

                        # Suggest similar plugin IDs
                        all_plugins = self._manager._registry.list_plugins()
                        matches = [p for p in all_plugins if url_or_id.lower() in p['id'].lower()]

                        # Only show suggestions if we have a reasonable number
                        if 1 <= len(matches) <= 10:
                            self._out.print('\nDid you mean one of these?')
                            for match in matches:
                                self._out.print(f'  {self._out.d_id(match["id"])} - {match["name"]}')

                        return ExitCode.NOT_FOUND
                else:
                    url = url_or_id

                    # Warn if this URL is in the registry
                    registry_plugin = self._manager._registry.find_plugin(url=url)
                    if registry_plugin:
                        plugin_id = registry_plugin['id']
                        self._out.warning(f'This URL is available in the registry as {self._out.d_id(plugin_id)}')
                        install_cmd = f'picard plugins --install {plugin_id}'
                        self._out.warning(
                            f'Consider using {self._out.d_command(install_cmd)} '
                            f'for automatic ref selection and trust verification'
                        )

                    # Check if already installed first (unless reinstalling)
                    if not reinstall:
                        existing_plugin = self._manager._find_plugin_by_url(url)
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
                        is_blacklisted, reason = self._manager._registry.is_blacklisted(url)
                        if is_blacklisted:
                            self._out.error(f'Plugin is blacklisted: {reason}')
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
                from picard.plugin3.registry import get_local_repository_path

                local_path = get_local_repository_path(url)
                if local_path:
                    try:
                        import pygit2

                        repo = pygit2.Repository(str(local_path))
                        if repo.status():
                            self._out.warning('Local repository has uncommitted changes')
                    except Exception:
                        pass  # Ignore errors checking status

                plugin_id = self._manager.install_plugin(url, ref, reinstall, force_blacklisted)
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
                        e, lambda **kw: self._manager.install_plugin(url, ref, reinstall, force_blacklisted, **kw)
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
                    self._out.error(f'Failed to install plugin: {e}')
                    return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _uninstall_plugins(self, plugin_names):
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
                    purge_this = self._out.yesno('Delete plugin configuration?')
                else:
                    purge_this = purge
            else:
                purge_this = purge

            try:
                self._out.print(f'Uninstalling {self._out.d_id(plugin.plugin_id)}...')

                if is_failed:
                    # For failed plugins, just remove the directory
                    from pathlib import Path
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
                self._out.error(f'Failed to uninstall plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _enable_plugins(self, plugin_names):
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
                    self._out.error(f'Failed to enable plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _disable_plugins(self, plugin_names):
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
                    self._out.error(f'Failed to disable plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _update_plugins(self, plugin_names):
        """Update specific plugins."""
        self._out.print('Updating plugin...')
        for plugin_name in plugin_names:
            plugin, error = self._find_plugin_or_error(plugin_name)
            if error:
                return error

            try:
                # Check if plugin is pinned to immutable ref
                try:
                    uuid = self._manager._get_plugin_uuid(plugin)
                    metadata = self._manager._get_plugin_metadata(uuid)
                    ref = metadata.get('ref') if metadata else None
                    is_immutable, ref_type = self._manager._is_immutable_ref(ref)
                except Exception:
                    is_immutable, ref_type, ref = False, None, None

                # Prevent updating if pinned to a specific commit (tags can update to newer tags)
                if is_immutable and ref and ref_type == 'commit':
                    self._out.warning(f'Plugin is pinned to commit {self._out.d_commit_old(ref)}')
                    self._out.info(
                        f'To update to a different version, use: {self._out.d_command(f"picard plugins --switch-ref {plugin.plugin_id} <branch-or-tag>")}'
                    )
                    continue

                result = self._manager.update_plugin(plugin)

                if result.old_commit == result.new_commit:
                    self._out.info(f'{self._out.d_name(plugin.plugin_id)}: Already up to date ({result.new_version})')
                else:
                    version_info = self._format_version_info(result)
                    self._out.success(f'{self._out.d_name(plugin.plugin_id)}: {version_info}')
                    self._out.info('Restart Picard to load the updated plugin')
            except Exception as e:
                from picard.plugin3.manager import (
                    PluginDirtyError,
                    PluginManifestInvalidError,
                    PluginNoSourceError,
                )

                if isinstance(e, PluginDirtyError):
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
                    self._out.error(f'Failed to update plugin: {e}')
                    return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _update_all_plugins(self):
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
                if r.result.old_commit == r.result.new_commit:
                    self._out.info(f'{self._out.d_name(r.plugin_id)}: Already up to date ({r.result.new_version})')
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

    def _check_updates(self):
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
            for update in updates:
                version_info = self._format_version_info(update)
                self._out.info(f'{self._out.d_name(update.plugin_id)}: {version_info}')
            self._out.nl()
            self._out.print(f'Run with {self._out.d_command("--update-all")} to update all plugins')

        return ExitCode.SUCCESS

    def _switch_ref(self, plugin_name, ref):
        """Switch plugin to a different git ref."""
        plugin, error = self._find_plugin_or_error(plugin_name)
        if error:
            return error

        try:
            self._out.print(f'Switching {self._out.d_id(plugin.plugin_id)} to ref: {ref}...')
            old_ref, new_ref, old_commit, new_commit = self._manager.switch_ref(plugin, ref)

            self._out.success(f'Switched: {old_ref} {self._out.d_arrow()} {new_ref}')
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
                old_ref, new_ref, old_commit, new_commit = result
                self._out.success(f'Switched: {old_ref} {self._out.d_arrow()} {new_ref}')
                self._out.info(
                    f'Commit: {self._out.d_commit_old(short_commit_id(old_commit))} {self._out.d_arrow()} {self._out.d_commit_new(short_commit_id(new_commit))}'
                )
                self._out.info('Restart Picard to load the updated plugin')
            elif isinstance(e, PluginRefNotFoundError):
                self._out.error(f"Ref '{ref}' not found")
                self._out.print('')
                # Ensure available_refs is a list before checking
                available_refs = e.available_refs if isinstance(e.available_refs, list) else []
                if available_refs:
                    self._out.print('Available refs:')
                    for r in available_refs:
                        desc = f" - {r['description']}" if r.get('description') else ''
                        self._out.print(f"  {r['name']}{desc}")
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
            else:
                self._handle_exception(e, 'Failed to switch ref')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _clean_config(self, plugin_name):
        """Clean configuration for a plugin."""
        yes = getattr(self._args, 'yes', False)

        if not yes:
            if not self._out.yesno(f'Delete configuration for "{plugin_name}"?'):
                self._out.print('Cancelled')
                return ExitCode.SUCCESS

        try:
            self._manager._clean_plugin_config(plugin_name)
            self._out.success(f'Configuration for {plugin_name} deleted')
        except Exception as e:
            self._out.error(f'Failed to clean config: {e}')
            return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _find_plugin(self, identifier):
        """Find a plugin by Plugin ID, display name, UUID, registry ID, or any prefix.

        Args:
            identifier: Plugin ID, display name, UUID, registry ID, or prefix of any

        Returns:
            Plugin object, None if not found, or 'multiple' if ambiguous
        """
        identifier_lower = identifier.lower()
        exact_matches = []
        prefix_matches = []

        for plugin in self._manager.plugins:
            # Collect all possible identifiers for this plugin
            identifiers = []

            # Plugin ID (case-insensitive)
            identifiers.append(plugin.plugin_id.lower())

            # UUID (case-insensitive)
            if plugin.manifest and plugin.manifest.uuid:
                identifiers.append(plugin.manifest.uuid.lower())

            # Display name (case-insensitive)
            if plugin.manifest:
                identifiers.append(plugin.manifest.name().lower())

            # Registry ID (case-insensitive) - lookup dynamically from current registry
            try:
                registry_id = self._manager.get_plugin_registry_id(plugin)
                if registry_id:
                    identifiers.append(registry_id.lower())
            except Exception:
                pass

            # Check for exact or prefix match
            for id_value in identifiers:
                if id_value == identifier_lower:
                    exact_matches.append(plugin)
                    break  # One exact match is enough
                elif id_value.startswith(identifier_lower):
                    prefix_matches.append(plugin)
                    break  # One prefix match is enough

        # Exact matches take priority
        if len(exact_matches) == 1:
            return exact_matches[0]
        elif len(exact_matches) > 1:
            return 'multiple'

        # Fall back to prefix matches
        if len(prefix_matches) == 1:
            return prefix_matches[0]
        elif len(prefix_matches) > 1:
            return 'multiple'

        return None

    def _find_plugin_or_error(self, identifier):
        """Find plugin and handle errors (not found or ambiguous).

        Returns:
            (plugin, error_code) - plugin is None if error, error_code is None if success
        """
        result = self._find_plugin(identifier)

        if result == 'multiple':
            # Find all matches to show to user
            identifier_lower = identifier.lower()
            matches = [p for p in self._manager.plugins if p.manifest and p.manifest.name().lower() == identifier_lower]

            self._out.error(f'Multiple plugins found with name "{identifier}":')
            for plugin in matches:
                self._out.error(
                    f'  - {self._out.d_id(plugin.plugin_id)} (UUID: {self._out.d_uuid(plugin.manifest.uuid)})'
                )
            self._out.error('Please use the Plugin ID or UUID to be more specific')
            return None, ExitCode.ERROR

        if not result:
            # Check if it's a failed plugin directory name
            for plugin_dir, plugin_name, _ in self._manager._failed_plugins:
                if plugin_name == identifier or str(plugin_dir).endswith(identifier):
                    # Return a minimal plugin-like object with just the path
                    from pathlib import Path
                    from types import SimpleNamespace

                    actual_path = Path(plugin_dir) / plugin_name
                    failed_plugin = SimpleNamespace(local_path=actual_path, plugin_id=plugin_name, manifest=None)
                    return failed_plugin, None

            self._out.error(f'Plugin "{identifier}" not found')
            return None, ExitCode.NOT_FOUND

        return result, None

    def _validate_plugin(self, url, ref=None):
        """Validate a plugin from git URL or local directory."""
        from pathlib import Path
        import shutil
        import tempfile

        from picard.plugin3.plugin import PluginSourceGit

        self._out.print(f'Validating plugin from: {url}')

        # Check if url is a local directory
        from picard.plugin3.registry import get_local_repository_path

        local_path = get_local_repository_path(url)
        if local_path:
            # Validate local directory directly
            self._out.success('MANIFEST.toml found')

            try:
                # Read and validate manifest using manager method
                from picard.plugin3.manager import (
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
            except Exception as e:
                self._out.error(f'Validation error: {e}')
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
            self._out.error(f'Validation error: {e}')
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

    def _browse_plugins(self):
        """Browse plugins from registry."""
        category = getattr(self._args, 'category', None)
        trust_level = getattr(self._args, 'trust', None)

        try:
            plugins = self._manager._registry.list_plugins(category=category, trust_level=trust_level)

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

            # Sort plugins by name
            sorted_plugins = sorted(plugins, key=lambda p: p.get('name', '').lower())

            # Show plugins
            for plugin in sorted_plugins:
                trust_badge = self._get_trust_badge(plugin.get('trust_level', 'community'))
                self._out.print(f'{trust_badge} {self._out.d_name(plugin["name"])}')
                self._out.info(f'  {plugin.get("description", "")}')
                categories = plugin.get('categories', [])
                if categories:
                    self._out.info(f'  Categories: {", ".join(categories)}')
                self._out.info(f'  Registry ID: {self._out.d_id(plugin["id"])}')
                self._out.print('')

            self._out.print(f'Total: {self._out.d_number(len(plugins))} plugin(s)')
            self._out.nl()
            self._out.print(f'Install with: {self._out.d_command("picard plugins --install <registry-id>")}')

            return ExitCode.SUCCESS

        except Exception as e:
            self._out.error(f'Failed to browse plugins: {e}')
            return ExitCode.ERROR

    def _search_plugins(self, query):
        """Search plugins in registry."""
        category = getattr(self._args, 'category', None)
        trust_level = getattr(self._args, 'trust', None)

        try:
            plugins = self._manager._registry.list_plugins(category=category, trust_level=trust_level)

            # Filter by query (case-insensitive search in name and description)
            query_lower = query.lower()
            results = []
            for plugin in plugins:
                name = plugin.get('name', '').lower()
                description = plugin.get('description', '').lower()
                plugin_id = plugin.get('id', '').lower()

                if query_lower in name or query_lower in description or query_lower in plugin_id:
                    results.append(plugin)

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

            for plugin in sorted_results:
                trust_badge = self._get_trust_badge(plugin.get('trust_level', 'community'))
                self._out.print(f'{trust_badge} {self._out.d_name(plugin["name"])}')
                self._out.info(f'  {plugin.get("description", "")}')
                categories = plugin.get('categories', [])
                if categories:
                    self._out.info(f'  Categories: {", ".join(categories)}')
                self._out.info(f'  Registry ID: {self._out.d_id(plugin["id"])}')
                self._out.print('')

            self._out.print('Install with: {}'.format(self._out.d_command("picard plugins --install <registry-id>")))

            return ExitCode.SUCCESS

        except Exception as e:
            self._out.error(f'Failed to search plugins: {e}')
            return ExitCode.ERROR

    def _check_blacklist(self, url):
        """Check if a URL is blacklisted."""
        try:
            is_blacklisted, reason = self._manager._registry.is_blacklisted(url)

            if is_blacklisted:
                self._out.error(f'URL is blacklisted: {reason}')
                return ExitCode.ERROR
            else:
                self._out.success('URL is not blacklisted')
                return ExitCode.SUCCESS

        except Exception as e:
            self._out.error(f'Failed to check blacklist: {e}')
            return ExitCode.ERROR

    def _refresh_registry(self):
        """Force refresh of plugin registry cache."""
        from picard.plugin3.registry import (
            RegistryFetchError,
            RegistryParseError,
        )

        try:
            self._out.print('Refreshing plugin registry...')

            self._manager._registry.fetch_registry(use_cache=False)

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
            self._out.error(f'Failed to refresh registry: {e}')
            return ExitCode.ERROR

    def _show_manifest(self, target):
        """Show MANIFEST.toml template or from plugin."""
        # No argument - show template
        if not target:
            import uuid

            generated_uuid = str(uuid.uuid4())
            template = f'''# MANIFEST.toml Template
# See https://picard-docs.musicbrainz.org/en/extending/plugins.html

# Required fields
uuid = "{generated_uuid}"  # Generated UUID - keep this value
name = "My Plugin Name"
version = "1.0.0"
description = "Short one-line description (1-200 characters)"
api = ["3.0"]
authors = ["Your Name"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"

# Optional fields
# long_description = """
# Detailed multi-line description (1-2000 characters).
# Explain features, requirements, usage notes, etc.
# """
# categories = ["metadata", "coverart", "ui", "scripting", "formats", "other"]
# homepage = "https://github.com/username/plugin-name"
# min_python_version = "3.9"

# Translation tables (optional)
# [name_i18n]
# de = "Mein Plugin Name"
# fr = "Mon nom de plugin"

# [description_i18n]
# de = "Kurze einzeilige Beschreibung"
# fr = "Courte description sur une ligne"

# [long_description_i18n]
# de = """
# Detaillierte mehrzeilige Beschreibung...
# """
# fr = """
# Description détaillée sur plusieurs lignes...
# """
'''
            self._out.print(template)
            return ExitCode.SUCCESS

        # Check if it's an installed plugin
        plugin = self._find_plugin(target)
        if plugin:
            manifest_path = plugin.local_path / 'MANIFEST.toml'
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    self._out.print(f.read())
                return ExitCode.SUCCESS
            else:
                self._out.error(f'MANIFEST.toml not found for plugin {target}')
                return ExitCode.ERROR

        # Check if it's a local directory
        from picard.plugin3.registry import get_local_repository_path

        local_path = get_local_repository_path(target)
        if local_path:
            manifest_path = local_path / 'MANIFEST.toml'
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    self._out.print(f.read())
                return ExitCode.SUCCESS
            else:
                self._out.error(f'MANIFEST.toml not found in {target}')
                return ExitCode.ERROR

        # Treat as git URL
        from pathlib import Path
        import tempfile

        temp_path = Path(tempfile.mkdtemp(prefix='picard-manifest-'))

        try:
            from picard.plugin3.plugin import PluginSourceGit

            self._out.print(f'Fetching from {target}...')
            source = PluginSourceGit(target, None)
            # Remove temp dir so git can create it
            import shutil

            shutil.rmtree(temp_path)
            source.sync(temp_path, shallow=True)

            manifest_path = temp_path / 'MANIFEST.toml'
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    self._out.print(f.read())
                return ExitCode.SUCCESS
            else:
                self._out.error('MANIFEST.toml not found in repository')
                return ExitCode.ERROR

        except Exception as e:
            self._out.error(f'Failed to fetch manifest: {e}')
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
