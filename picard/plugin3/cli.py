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

from picard.const.appdirs import plugin_folder
from picard.plugin3.manager import PluginManager


class PluginCLI:
    """Command line interface for managing plugins."""

    def __init__(self, tagger, args):
        self._manager = tagger.pluginmanager3
        self._args = args

    def run(self):
        if self._args.list:
            self._list_plugins()
        elif self._args.enable:
            self._enable_plugins(self._args.enable)
        elif self._args.disable:
            self._disable_plugins(self._args.disable)
        elif self._args.install:
            self._install_plugins(self._args.install)
        elif self._args.uninstall:
            self._uninstall_plugins(self._args.uninstall)
        else:
            print('No action specified')
            return 1
        return 0

    def _list_plugins(self):
        for plugin in self._manager.plugins:
            print(plugin.name, plugin.local_path)

    def _install_plugins(self, plugin_urls):
        for url in plugin_urls:
            print("Installing plugin from %s", url)
            self._manager.install_plugin(url)

    def _uninstall_plugins(self, plugin_names):
        for plugin in self._manager.plugins:
            if plugin.name in plugin_names:
                print("Uninstalling %s" % plugin.name)
                self._manager.uninstall_plugin(plugin)

    def _enable_plugins(self, plugin_names):
        for plugin in self._manager.plugins:
            if plugin.name in plugin_names:
                print("Enabling %s" % plugin.name)
                self._manager.enable_plugin(plugin)

    def _disable_plugins(self, plugin_names):
        for plugin in self._manager.plugins:
            if plugin.name in plugin_names:
                print("Disabling %s" % plugin.name)
                self._manager.disable_plugin(plugin)

