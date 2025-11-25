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


class ExitCode(IntEnum):
    """Exit codes for plugin CLI commands."""

    SUCCESS = 0
    ERROR = 1
    NOT_FOUND = 2
    CANCELLED = 130


class PluginCLI:
    """Command line interface for managing plugins."""

    def __init__(self, tagger, args, output=None):
        self._manager = tagger.pluginmanager3
        self._args = args
        self._out = output or PluginOutput()

    def run(self):
        """Run the CLI command and return exit code."""
        try:
            if self._args.list:
                return self._list_plugins()
            elif self._args.info:
                return self._show_info(self._args.info)
            elif self._args.enable:
                return self._enable_plugins(self._args.enable)
            elif self._args.disable:
                return self._disable_plugins(self._args.disable)
            elif self._args.install:
                return self._install_plugins(self._args.install)
            elif self._args.uninstall:
                return self._uninstall_plugins(self._args.uninstall)
            else:
                self._out.error('No action specified')
                return ExitCode.ERROR
        except KeyboardInterrupt:
            self._out.error('\nOperation cancelled by user')
            return ExitCode.CANCELLED
        except Exception as e:
            self._out.error(f'Error: {e}')
            return ExitCode.ERROR

    def _list_plugins(self):
        """List all installed plugins with details."""
        if not self._manager.plugins:
            self._out.print('No plugins installed')
            return ExitCode.SUCCESS

        self._out.print('Installed plugins:\n')
        for plugin in self._manager.plugins:
            status = 'enabled' if plugin.name in self._manager._enabled_plugins else 'disabled'
            self._out.print(f'  {plugin.name} ({status})')

            if hasattr(plugin, 'manifest') and plugin.manifest:
                self._out.info(f'Version: {plugin.manifest.version}')
                self._out.info(f'API: {", ".join(str(v) for v in plugin.manifest.api_versions)}')
                self._out.info(f'Path: {plugin.local_path}')
                desc = plugin.manifest.description()
                if desc:
                    self._out.info(f'Description: {desc}')
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
        self._out.print(f'Plugin: {plugin.manifest.name}')
        self._out.print(f'Status: {status}')
        self._out.print(f'Version: {plugin.manifest.version}')
        self._out.print(f'Author: {plugin.manifest.author}')
        self._out.print(f'API Versions: {", ".join(str(v) for v in plugin.manifest.api_versions)}')
        self._out.print(f'License: {plugin.manifest.license}')
        self._out.print(f'License URL: {plugin.manifest.license_url}')
        self._out.print(f'Path: {plugin.local_path}')

        desc = plugin.manifest.description()
        if desc:
            self._out.print(f'\nDescription:\n  {desc}')

        return ExitCode.SUCCESS

    def _install_plugins(self, plugin_urls):
        """Install plugins from URLs."""
        for url in plugin_urls:
            try:
                self._out.print(f'Installing plugin from {url}...')
                self._manager.install_plugin(url)
                self._out.success('Plugin installed successfully')
                self._out.info('Restart Picard to load the plugin')
            except Exception as e:
                self._out.error(f'Failed to install plugin: {e}')
                return ExitCode.ERROR
        return ExitCode.SUCCESS

    def _uninstall_plugins(self, plugin_names):
        """Uninstall plugins with confirmation."""
        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                self._out.error(f'Plugin "{plugin_name}" not found')
                return ExitCode.NOT_FOUND

            # Confirmation prompt unless --yes flag
            if not getattr(self._args, 'yes', False):
                response = input(f'Uninstall plugin "{plugin.name}"? [y/N] ')
                if response.lower() != 'y':
                    self._out.print('Cancelled')
                    continue

            try:
                self._out.print(f'Uninstalling {plugin.name}...')
                self._manager.uninstall_plugin(plugin)
                self._out.success('Plugin uninstalled successfully')
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

    def _find_plugin(self, plugin_name):
        """Find a plugin by name."""
        for plugin in self._manager.plugins:
            if plugin.name == plugin_name:
                return plugin
        return None
