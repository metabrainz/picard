# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
# Copyright (C) 2024 Philipp Wolfer
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

import importlib.util
import os
import sys

from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest

import pygit2


class GitRemoteCallbacks(pygit2.RemoteCallbacks):

    def transfer_progress(self, stats):
        print(f'{stats.indexed_objects}/{stats.total_objects}')


class PluginSourceSyncError(Exception):
    pass


class PluginSource:
    """Abstract class for plugin sources"""

    def sync(self, target_directory: str):
        raise NotImplementedError


class PluginSourceGit(PluginSource):
    """Plugin is stored in a git repository, local or remote"""
    def __init__(self, url: str, ref: str = None):
        super().__init__()
        # Note: url can be a local directory
        self.url = url
        self.ref = ref or 'main'

    def sync(self, target_directory: str):
        if os.path.isdir(target_directory):
            print(f'{target_directory} exists, fetch changes')
            repo = pygit2.Repository(target_directory)
            for remote in repo.remotes:
                remote.fetch(callbacks=GitRemoteCallbacks())
        else:
            print(f'Cloning {self.url} to {target_directory}')
            repo = pygit2.clone_repository(self.url, target_directory, callbacks=GitRemoteCallbacks())
            print(list(repo.references))
            print(list(repo.branches))
            print(list(repo.remotes))

        if self.ref:
            commit = repo.revparse_single(self.ref)
        else:
            commit = repo.revparse_single('HEAD')

        print(commit)
        print(commit.message)
        # hard reset to passed ref or HEAD
        repo.reset(commit.id, pygit2.enums.ResetMode.HARD)


class PluginSourceLocal(PluginSource):
    """Plugin is stored in a local directory, but is not a git repo"""

    def sync(self, target_directory: str):
        # TODO: copy tree to plugin directory (?)
        pass


class Plugin:
    local_path: str = None
    remote_url: str = None
    ref = None
    plugin_name: str = None
    module_name: str = None
    manifest: PluginManifest = None
    _module = None

    def __init__(self, plugins_dir: str, plugin_name: str):
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
        self.plugins_dir = plugins_dir
        self.plugin_name = plugin_name
        self.module_name = f'picard.plugins.{self.plugin_name}'
        self.local_path = os.path.join(self.plugins_dir, self.plugin_name)

    def sync(self, plugin_source: PluginSource = None):
        """Sync plugin source
        """
        if plugin_source:
            try:
                plugin_source.sync(self.local_path)
            except Exception as e:
                raise PluginSourceSyncError(e)

    def read_manifest(self):
        """Reads metadata for the plugin from the plugin's MANIFEST.toml
        """
        manifest_path = os.path.join(self.local_path, 'MANIFEST.toml')
        with open(manifest_path, 'rb') as manifest_file:
            self.manifest = PluginManifest(self.plugin_name, manifest_file)

    def load_module(self):
        """Load corresponding module from source path"""
        module_file = os.path.join(self.local_path, '__init__.py')
        spec = importlib.util.spec_from_file_location(self.module_name, module_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_name] = module
        spec.loader.exec_module(module)
        self._module = module
        return module

    def enable(self, tagger) -> None:
        """Enable the plugin"""
        api = PluginApi(self.manifest, tagger)
        self._module.enable(api)

    def disable(self) -> None:
        """Disable the plugin"""
        self._module.disable()
