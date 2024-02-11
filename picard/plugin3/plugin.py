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

    def sync(self, url: str = None, ref: str = None):
        """Sync plugin source
        Use remote url or local path, and sets the repository to ref
        """
        if url:
            self.remote_url = url
        if os.path.isdir(self.local_path):
            print(f'{self.local_path} exists, fetch changes')
            repo = pygit2.Repository(self.local_path)
            for remote in repo.remotes:
                remote.fetch(callbacks=GitRemoteCallbacks())
        else:
            print(f'Cloning {url} to {self.local_path}')
            repo = pygit2.clone_repository(url, self.local_path, callbacks=GitRemoteCallbacks())

            print(list(repo.references))
            print(list(repo.branches))
            print(list(repo.remotes))

        if ref:
            commit = repo.revparse_single(ref)
        else:
            commit = repo.revparse_single('HEAD')

        print(commit)
        print(commit.message)
        # hard reset to passed ref or HEAD
        repo.reset(commit.id, pygit2.enums.ResetMode.HARD)

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
