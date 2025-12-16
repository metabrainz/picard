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

"""Async wrapper for PluginManager operations."""

from picard.plugin3.asyncops.callbacks import ProgressUpdate
from picard.plugin3.asyncops.utils import run_async
from picard.plugin3.manager import PluginManager
from picard.util.thread import to_main


class AsyncPluginManager:
    """Async wrapper for PluginManager operations."""

    def __init__(self, manager: PluginManager):
        self._manager = manager

    def install_plugin(self, url, ref=None, reinstall=False, progress_callback=None, callback=None):
        """Install plugin asynchronously.

        Args:
            url: Plugin URL or registry ID
            ref: Optional git ref (RefItem, string, or None)
            reinstall: Whether to reinstall if exists
            progress_callback: Optional callback for progress updates
            callback: Called with OperationResult on completion
        """

        def _install():
            if progress_callback:
                to_main(
                    progress_callback,
                    ProgressUpdate(operation='install', message=f'Installing from {url}...', percent=0),
                )

            plugin_id = self._manager.install_plugin(url, ref, reinstall, enable_after_install=True)

            if progress_callback:
                to_main(
                    progress_callback,
                    ProgressUpdate(
                        operation='install', plugin_id=plugin_id, message='Installation complete', percent=100
                    ),
                )

            return plugin_id

        run_async(_install, callback, progress_callback)

    def update_plugin(self, plugin, progress_callback=None, callback=None):
        """Update plugin asynchronously."""

        def _update():
            if progress_callback:
                to_main(
                    progress_callback,
                    ProgressUpdate(
                        operation='update',
                        plugin_id=plugin.plugin_id,
                        message=f'Updating {plugin.plugin_id}...',
                        percent=0,
                    ),
                )

            result = self._manager.update_plugin(plugin)

            if progress_callback:
                to_main(
                    progress_callback,
                    ProgressUpdate(
                        operation='update', plugin_id=plugin.plugin_id, message='Update complete', percent=100
                    ),
                )

            return result

        run_async(_update, callback, progress_callback)

    def update_all_plugins(self, progress_callback=None, callback=None):
        """Update all plugins asynchronously."""

        def _update_all():
            plugins = self._manager.plugins
            total = len(plugins)

            results = []
            for i, plugin in enumerate(plugins):
                if progress_callback:
                    to_main(
                        progress_callback,
                        ProgressUpdate(
                            operation='update_all',
                            plugin_id=plugin.plugin_id,
                            message=f'Updating {plugin.plugin_id}...',
                            percent=int((i / total) * 100),
                            current=i + 1,
                            total=total,
                        ),
                    )

                try:
                    result = self._manager.update_plugin(plugin)
                    results.append((plugin.plugin_id, result, None))
                except Exception as e:
                    results.append((plugin.plugin_id, None, e))

            if progress_callback:
                to_main(
                    progress_callback,
                    ProgressUpdate(operation='update_all', message='All updates complete', percent=100),
                )

            return results

        run_async(_update_all, callback, progress_callback)

    def uninstall_plugin(self, plugin, purge=False, callback=None):
        """Uninstall plugin asynchronously."""

        def _uninstall():
            self._manager.uninstall_plugin(plugin, purge)
            return plugin.plugin_id

        run_async(_uninstall, callback)

    def switch_ref(self, plugin, ref, callback=None):
        """Switch plugin ref asynchronously.

        Args:
            plugin: Plugin to switch
            ref: Git ref to switch to (RefItem, string, or None)
            callback: Called with OperationResult on completion
        """

        def _switch_ref():
            self._manager.switch_ref(plugin, ref)
            return plugin.plugin_id

        run_async(_switch_ref, callback)

    # Synchronous operations (fast, no need for async)
    def enable_plugin(self, plugin):
        """Enable plugin (synchronous - fast)."""
        return self._manager.enable_plugin(plugin)

    def disable_plugin(self, plugin):
        """Disable plugin (synchronous - fast)."""
        return self._manager.disable_plugin(plugin)

    def find_plugin(self, identifier):
        """Find plugin (synchronous - fast)."""
        return self._manager.find_plugin(identifier)

    @property
    def plugins(self):
        """Get plugin list (synchronous)."""
        return self._manager.plugins
