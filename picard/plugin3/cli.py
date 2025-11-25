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

from picard.plugin3.output import PluginOutput
from picard.plugin3.plugin import short_commit_id


class ExitCode(IntEnum):
    """Exit codes for plugin CLI commands."""

    SUCCESS = 0
    ERROR = 1
    NOT_FOUND = 2
    CANCELLED = 130


class PluginCLI:
    """Command line interface for managing plugins."""

    def __init__(self, manager, args, output=None, parser=None):
        self._manager = manager
        self._args = args
        self._out = output or PluginOutput()
        self._parser = parser

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
            self._out.error(f'Error: {e}')
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

    def _list_plugins(self):
        """List all installed plugins with details."""
        if not self._manager.plugins:
            self._out.print('No plugins installed')
            return ExitCode.SUCCESS

        self._out.print('Installed plugins:')
        self._out.nl()
        for plugin in self._manager.plugins:
            # Check config for enabled state (not just loaded state)
            status = 'enabled' if plugin.name in self._manager._enabled_plugins else 'disabled'
            self._out.print(f'  {plugin.name} ({status})')

            if hasattr(plugin, 'manifest') and plugin.manifest:
                desc = plugin.manifest.description()
                if desc:
                    self._out.info(f'  {desc}')
                metadata = self._manager._get_plugin_metadata(plugin.name)
                git_info = self._format_git_info(metadata)
                version = plugin.manifest._data.get('version', '')
                self._out.info(f'  Version: {version}{git_info}')
                self._out.info(f'  Path: {plugin.local_path}')
            self._out.print()

        total = len(self._manager.plugins)
        enabled = len(self._manager._enabled_plugins)
        self._out.print(
            f'Total: {total} plugin{"s" if total != 1 else ""} ({enabled} enabled, {total - enabled} disabled)'
        )
        return ExitCode.SUCCESS

    def _show_info(self, plugin_name):
        """Show detailed information about a plugin."""
        plugin = self._find_plugin(plugin_name)
        if not plugin:
            self._out.error(f'Plugin "{plugin_name}" not found')
            return ExitCode.NOT_FOUND

        status = 'enabled' if plugin.name in self._manager._enabled_plugins else 'disabled'
        metadata = self._manager._get_plugin_metadata(plugin.name)
        git_info = self._format_git_info(metadata)

        self._out.print(f'Plugin: {plugin.manifest.name()}')

        # Show short description on one line (required field)
        desc = plugin.manifest.description()
        if desc:
            self._out.print(f'Description: {desc}')

        self._out.print(f'Status: {status}')
        version = plugin.manifest._data.get('version', '')
        self._out.print(f'Version: {version}{git_info}')

        # Show source URL if available
        if metadata and metadata.get('url'):
            self._out.print(f'Source: {metadata["url"]}')

        self._out.print(f'Authors: {", ".join(plugin.manifest.authors)}')
        api_versions = plugin.manifest._data.get('api', [])
        self._out.print(f'API Versions: {", ".join(api_versions)}')
        self._out.print(f'License: {plugin.manifest.license}')
        self._out.print(f'License URL: {plugin.manifest.license_url}')
        self._out.print(f'Path: {plugin.local_path}')

        # Show long description at the end if available
        long_desc = plugin.manifest.long_description()
        if long_desc:
            self._out.nl()
            self._out.print(long_desc)

        return ExitCode.SUCCESS

    def _show_status(self, plugin_name):
        """Show detailed status information about a plugin."""
        plugin = self._find_plugin(plugin_name)
        if not plugin:
            self._out.error(f'Plugin "{plugin_name}" not found')
            return ExitCode.NOT_FOUND

        self._out.print(f'Plugin: {plugin.name}')
        self._out.print(f'State: {plugin.state.value}')

        if plugin.manifest:
            version = plugin.manifest._data.get('version', '')
            self._out.print(f'Version: {version}')
            api_versions = plugin.manifest._data.get('api', [])
            self._out.print(f'API Versions: {", ".join(api_versions)}')

        enabled_status = 'yes' if plugin.name in self._manager._enabled_plugins else 'no'
        self._out.print(f'Enabled in config: {enabled_status}')

        metadata = self._manager._get_plugin_metadata(plugin.name)
        if metadata:
            self._out.print(f'Source URL: {metadata.get("url", "N/A")}')
            self._out.print(f'Git ref: {metadata.get("ref", "N/A")}')
            commit = metadata.get('commit', 'N/A')
            if commit != 'N/A':
                commit = short_commit_id(commit)
            self._out.print(f'Commit: {commit}')

        return ExitCode.SUCCESS

    def _install_plugins(self, plugin_urls):
        """Install plugins from URLs or plugin IDs."""
        ref = getattr(self._args, 'ref', None)
        reinstall = getattr(self._args, 'reinstall', False)
        force_blacklisted = getattr(self._args, 'force_blacklisted', False)
        yes = getattr(self._args, 'yes', False)

        if force_blacklisted:
            self._out.warning('WARNING: Bypassing blacklist check - this may be dangerous!')

        for url_or_id in plugin_urls:
            try:
                # Check if it's a plugin ID (no slashes, no protocol)
                if '/' not in url_or_id and '://' not in url_or_id:
                    # Try to find in registry
                    plugin = self._manager._registry.find_plugin(plugin_id=url_or_id)
                    if plugin:
                        url = plugin['git_url']
                        self._out.print(f'Found {plugin["name"]} in registry')
                        self._out.print(f'Installing from {url}...')
                    else:
                        self._out.error(f'Plugin "{url_or_id}" not found in registry')
                        return ExitCode.NOT_FOUND
                else:
                    url = url_or_id
                    # Check trust level for unregistered plugins
                    trust_level = self._manager._registry.get_trust_level(url)
                    if trust_level == 'unregistered':
                        self._out.warning('WARNING: This plugin is not in the official registry')
                        self._out.warning('  Installing unregistered plugins may pose security risks')
                        self._out.warning('  Only install plugins from sources you trust')

                        if not yes:
                            response = input('Do you want to continue? [y/N]: ').strip().lower()
                            if response not in ('y', 'yes'):
                                self._out.print('Installation cancelled')
                                return ExitCode.CANCELLED

                if ref:
                    self._out.print(f'Installing plugin from {url} (ref: {ref})...')
                else:
                    self._out.print(f'Installing plugin from {url}...')

                plugin_id = self._manager.install_plugin(url, ref, reinstall, force_blacklisted)
                self._out.success(f'Plugin {plugin_id} installed successfully')
                self._out.info('Restart Picard to load the plugin')
            except Exception as e:
                self._out.error(f'Failed to install plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _uninstall_plugins(self, plugin_names):
        """Uninstall plugins with confirmation."""
        purge = getattr(self._args, 'purge', False)
        yes = getattr(self._args, 'yes', False)

        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                self._out.error(f'Plugin "{plugin_name}" not found')
                return ExitCode.NOT_FOUND

            # Confirmation prompt unless --yes flag
            if not yes:
                response = input(f'Uninstall plugin "{plugin.name}"? [y/N] ')
                if response.lower() != 'y':
                    self._out.print('Cancelled')
                    continue

                # Ask about config cleanup if not using --purge
                if not purge:
                    response = input('Delete plugin configuration? [y/N] ')
                    purge_this = response.lower() == 'y'
                else:
                    purge_this = True
            else:
                purge_this = purge

            try:
                self._out.print(f'Uninstalling {plugin.name}...')
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
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                self._out.error(f'Plugin "{plugin_name}" not found')
                return ExitCode.NOT_FOUND

            try:
                self._out.print(f'Enabling {plugin.name}...')
                self._manager.enable_plugin(plugin)
                self._out.success('Plugin enabled')
                self._out.info('Restart Picard to load the plugin')
            except Exception as e:
                self._out.error(f'Failed to enable plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _disable_plugins(self, plugin_names):
        """Disable plugins."""
        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                self._out.error(f'Plugin "{plugin_name}" not found')
                return ExitCode.NOT_FOUND

            try:
                self._out.print(f'Disabling {plugin.name}...')
                self._manager.disable_plugin(plugin)
                self._out.success('Plugin disabled')
                self._out.info('Restart Picard for changes to take effect')
            except Exception as e:
                self._out.error(f'Failed to disable plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _update_plugins(self, plugin_names):
        """Update specific plugins."""
        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                self._out.error(f'Plugin "{plugin_name}" not found')
                return ExitCode.NOT_FOUND

            try:
                self._out.print(f'Updating {plugin.name}...')
                old_ver, new_ver, old_commit, new_commit = self._manager.update_plugin(plugin)

                if old_commit == new_commit:
                    self._out.info(f'Already up to date (version {new_ver})')
                else:
                    self._out.success(f'Updated: {old_ver} → {new_ver}')
                    self._out.info(f'Commit: {short_commit_id(old_commit)} → {short_commit_id(new_commit)}')
                    self._out.info('Restart Picard to load the updated plugin')
            except Exception as e:
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

        for name, success, old_ver, new_ver, old_commit, new_commit, error in results:
            if success:
                if old_commit == new_commit:
                    self._out.info(f'{name}: Already up to date ({new_ver})')
                    unchanged += 1
                else:
                    self._out.success(
                        f'{name}: {old_ver} → {new_ver} ({short_commit_id(old_commit)} → {short_commit_id(new_commit)})'
                    )
                    updated += 1
            else:
                self._out.error(f'{name}: {error}')
                failed += 1

        self._out.nl()
        self._out.print(f'Summary: {updated} updated, {unchanged} unchanged, {failed} failed')
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
            for name, current, latest in updates:
                self._out.info(f'{name}: {current} → {latest}')
            self._out.nl()
            self._out.print('Run with --update-all to update all plugins')

        return ExitCode.SUCCESS

    def _switch_ref(self, plugin_name, ref):
        """Switch plugin to a different git ref."""
        plugin = self._find_plugin(plugin_name)
        if not plugin:
            self._out.error(f'Plugin "{plugin_name}" not found')
            return ExitCode.NOT_FOUND

        try:
            self._out.print(f'Switching {plugin.name} to ref: {ref}...')
            old_ref, new_ref, old_commit, new_commit = self._manager.switch_ref(plugin, ref)

            self._out.success(f'Switched: {old_ref} → {new_ref}')
            self._out.info(f'Commit: {short_commit_id(old_commit)} → {short_commit_id(new_commit)}')
            self._out.info('Restart Picard to load the updated plugin')
        except Exception as e:
            self._out.error(f'Failed to switch ref: {e}')
            return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _clean_config(self, plugin_name):
        """Clean configuration for a plugin."""
        yes = getattr(self._args, 'yes', False)

        if not yes:
            response = input(f'Delete configuration for "{plugin_name}"? [y/N] ')
            if response.lower() != 'y':
                self._out.print('Cancelled')
                return ExitCode.SUCCESS

        try:
            self._manager._clean_plugin_config(plugin_name)
            self._out.success(f'Configuration for {plugin_name} deleted')
        except Exception as e:
            self._out.error(f'Failed to clean config: {e}')
            return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _find_plugin(self, plugin_name):
        """Find a plugin by name."""
        for plugin in self._manager.plugins:
            if plugin.name == plugin_name:
                return plugin
        return None

    def _validate_plugin(self, url, ref=None):
        """Validate a plugin from git URL or local directory."""
        from pathlib import Path
        import shutil
        import tempfile

        from picard.plugin3.manifest import PluginManifest
        from picard.plugin3.plugin import PluginSourceGit

        self._out.print(f'Validating plugin from: {url}')

        # Check if url is a local directory
        local_path = Path(url)
        if local_path.is_dir():
            # Validate local directory directly
            manifest_path = local_path / 'MANIFEST.toml'
            if not manifest_path.exists():
                self._out.error('No MANIFEST.toml found')
                return ExitCode.ERROR

            self._out.success('MANIFEST.toml found')

            try:
                # Read and validate manifest
                with open(manifest_path, 'rb') as f:
                    manifest = PluginManifest('temp', f)

                errors = manifest.validate()

                if errors:
                    self._out.nl()
                    self._out.error(f'Validation failed with {len(errors)} error(s):')
                    self._out.nl()
                    for error in errors:
                        self._out.error(f'  • {error}')
                    return ExitCode.ERROR

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
                self._out.info(f'  Authors: {", ".join(manifest.authors)}')
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
                self._out.info(f'  License: {manifest.license}')

                # Show license URL if available
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
            source.sync(temp_path)

            # Check for MANIFEST.toml
            manifest_path = temp_path / 'MANIFEST.toml'
            if not manifest_path.exists():
                self._out.error('No MANIFEST.toml found')
                return ExitCode.ERROR

            self._out.success('MANIFEST.toml found')

            # Read and validate manifest
            with open(manifest_path, 'rb') as f:
                manifest = PluginManifest('temp', f)

            errors = manifest.validate()

            if errors:
                self._out.nl()
                self._out.error(f'Validation failed with {len(errors)} error(s):')
                self._out.nl()
                for error in errors:
                    self._out.error(f'  • {error}')
                return ExitCode.ERROR

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
            self._out.info(f'  Authors: {", ".join(manifest.authors)}')
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
            self._out.info(f'  License: {manifest.license}')

            # Show license URL if available
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

        except Exception as e:
            self._out.error(f'Validation error: {e}')
            return ExitCode.ERROR
        finally:
            # Cleanup
            import shutil

            shutil.rmtree(temp_path, ignore_errors=True)

    def _browse_plugins(self):
        """Browse plugins from registry."""
        category = getattr(self._args, 'category', None)
        trust_level = getattr(self._args, 'trust', None)

        try:
            plugins = self._manager._registry.list_plugins(category=category, trust_level=trust_level)

            if not plugins:
                self._out.print('No plugins found in registry')
                return ExitCode.SUCCESS

            # Show header
            filters = []
            if category:
                filters.append(f'category: {category}')
            if trust_level:
                filters.append(f'trust: {trust_level}')

            if filters:
                self._out.print(f'Registry plugins ({", ".join(filters)}):')
                self._out.nl()
            else:
                self._out.print('Registry plugins:')
                self._out.nl()

            # Show plugins
            for plugin in plugins:
                trust_badge = self._get_trust_badge(plugin.get('trust_level', 'community'))
                self._out.print(f'{trust_badge} {plugin["id"]} - {plugin["name"]}')
                self._out.info(f'  {plugin.get("description", "")}')
                categories = plugin.get('categories', [])
                if categories:
                    self._out.info(f'  Categories: {", ".join(categories)}')
                self._out.print('')

            self._out.print(f'Total: {len(plugins)} plugin(s)')
            self._out.nl()
            self._out.print('Install with: picard plugins --install <plugin-id>')

            return ExitCode.SUCCESS

        except Exception as e:
            self._out.error(f'Failed to browse plugins: {e}')
            return ExitCode.ERROR

    def _search_plugins(self, query):
        """Search plugins in registry."""
        try:
            plugins = self._manager._registry.list_plugins()

            # Filter by query (case-insensitive search in name and description)
            query_lower = query.lower()
            results = []
            for plugin in plugins:
                name = plugin.get('name', '').lower()
                description = plugin.get('description', '').lower()
                plugin_id = plugin.get('id', '').lower()

                if query_lower in name or query_lower in description or query_lower in plugin_id:
                    results.append(plugin)

            if not results:
                self._out.print(f'No plugins found matching "{query}"')
                return ExitCode.SUCCESS

            self._out.print(f'Found {len(results)} plugin(s) matching "{query}":')
            self._out.nl()

            for plugin in results:
                trust_badge = self._get_trust_badge(plugin.get('trust_level', 'community'))
                self._out.print(f'{trust_badge} {plugin["id"]} - {plugin["name"]}')
                self._out.info(f'  {plugin.get("description", "")}')
                self._out.print('')

            self._out.print('Install with: picard plugins --install <plugin-id>')

            return ExitCode.SUCCESS

        except Exception as e:
            self._out.error(f'Failed to search plugins: {e}')
            return ExitCode.ERROR

    def _show_manifest(self, target):
        """Show MANIFEST.toml template or from plugin."""
        # No argument - show template
        if not target:
            template = '''# MANIFEST.toml Template
# See https://picard-docs.musicbrainz.org/en/extending/plugins.html

# Required fields
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
        from pathlib import Path

        local_path = Path(target)
        if local_path.is_dir():
            manifest_path = local_path / 'MANIFEST.toml'
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    self._out.print(f.read())
                return ExitCode.SUCCESS
            else:
                self._out.error(f'MANIFEST.toml not found in {target}')
                return ExitCode.ERROR

        # Treat as git URL
        import tempfile

        temp_path = Path(tempfile.mkdtemp(prefix='picard-manifest-'))

        try:
            from picard.plugin3.plugin import PluginSourceGit

            self._out.print(f'Fetching from {target}...')
            source = PluginSourceGit(target, None)
            source.sync(temp_path)

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
