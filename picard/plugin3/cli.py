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

import sys


class PluginCLI:
    """Command line interface for managing plugins."""

    def __init__(self, tagger, args):
        self._manager = tagger.pluginmanager3
        self._args = args

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
                print('No action specified', file=sys.stderr)
                return 1
        except KeyboardInterrupt:
            print('\nOperation cancelled by user', file=sys.stderr)
            return 130
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            return 1

    def _list_plugins(self):
        """List all installed plugins with details."""
        if not self._manager.plugins:
            print('No plugins installed')
            return 0

        print('Installed plugins:\n')
        for plugin in self._manager.plugins:
            status = 'enabled' if plugin.name in self._manager._enabled_plugins else 'disabled'
            print(f'  {plugin.name} ({status})')

            if hasattr(plugin, 'manifest') and plugin.manifest:
                print(f'    Version: {plugin.manifest.version}')
                print(f'    API: {", ".join(str(v) for v in plugin.manifest.api_versions)}')
                print(f'    Path: {plugin.local_path}')
                desc = plugin.manifest.description()
                if desc:
                    print(f'    Description: {desc}')
            print()

        total = len(self._manager.plugins)
        enabled = len(self._manager._enabled_plugins)
        print(f'Total: {total} plugin{"s" if total != 1 else ""} ({enabled} enabled, {total - enabled} disabled)')
        return 0

    def _show_info(self, plugin_name):
        """Show detailed information about a plugin."""
        plugin = self._find_plugin(plugin_name)
        if not plugin:
            print(f'Plugin "{plugin_name}" not found', file=sys.stderr)
            return 2

        status = 'enabled' if plugin.name in self._manager._enabled_plugins else 'disabled'
        print(f'Plugin: {plugin.manifest.name}')
        print(f'Status: {status}')
        print(f'Version: {plugin.manifest.version}')
        print(f'Author: {plugin.manifest.author}')
        print(f'API Versions: {", ".join(str(v) for v in plugin.manifest.api_versions)}')
        print(f'License: {plugin.manifest.license}')
        print(f'License URL: {plugin.manifest.license_url}')
        print(f'Path: {plugin.local_path}')

        desc = plugin.manifest.description()
        if desc:
            print(f'\nDescription:\n  {desc}')

        return 0

    def _install_plugins(self, plugin_urls):
        """Install plugins from URLs."""
        for url in plugin_urls:
            try:
                print(f'Installing plugin from {url}...')
                self._manager.install_plugin(url)
                print('✓ Plugin installed successfully')
                print('  Restart Picard to load the plugin')
            except Exception as e:
                print(f'✗ Failed to install plugin: {e}', file=sys.stderr)
                return 1
        return 0

    def _uninstall_plugins(self, plugin_names):
        """Uninstall plugins with confirmation."""
        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                print(f'Plugin "{plugin_name}" not found', file=sys.stderr)
                return 2

            # Confirmation prompt unless --yes flag
            if not getattr(self._args, 'yes', False):
                response = input(f'Uninstall plugin "{plugin.name}"? [y/N] ')
                if response.lower() != 'y':
                    print('Cancelled')
                    continue

            try:
                print(f'Uninstalling {plugin.name}...')
                self._manager.uninstall_plugin(plugin)
                print('✓ Plugin uninstalled successfully')
            except Exception as e:
                print(f'✗ Failed to uninstall plugin: {e}', file=sys.stderr)
                return 1
        return 0

    def _enable_plugins(self, plugin_names):
        """Enable plugins."""
        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                print(f'Plugin "{plugin_name}" not found', file=sys.stderr)
                return 2

            try:
                print(f'Enabling {plugin.name}...')
                self._manager.enable_plugin(plugin)
                print('✓ Plugin enabled')
                print('  Restart Picard to load the plugin')
            except Exception as e:
                print(f'✗ Failed to enable plugin: {e}', file=sys.stderr)
                return 1
        return 0

    def _disable_plugins(self, plugin_names):
        """Disable plugins."""
        for plugin_name in plugin_names:
            plugin = self._find_plugin(plugin_name)
            if not plugin:
                print(f'Plugin "{plugin_name}" not found', file=sys.stderr)
                return 2

            try:
                print(f'Disabling {plugin.name}...')
                self._manager.disable_plugin(plugin)
                print('✓ Plugin disabled')
                print('  Restart Picard for changes to take effect')
            except Exception as e:
                print(f'✗ Failed to disable plugin: {e}', file=sys.stderr)
                return 1
        return 0

    def _find_plugin(self, plugin_name):
        """Find a plugin by name."""
        for plugin in self._manager.plugins:
            if plugin.name == plugin_name:
                return plugin
        return None
