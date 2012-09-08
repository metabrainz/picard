# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

from PyQt4 import QtCore
import imp
import os.path
import shutil
import picard.plugins
import traceback

_suffixes = [s[0] for s in imp.get_suffixes()]
_package_entries = ["__init__.py", "__init__.pyc", "__init__.pyo"]
_extension_points = []


def _plugin_name_from_path(path):
    path = os.path.normpath(path)
    file = os.path.basename(path)
    if os.path.isdir(path):
        for entry in _package_entries:
            if os.path.isfile(os.path.join(path, entry)):
                return file
    else:
        if file in _package_entries:
            return None
        name, ext = os.path.splitext(file)
        if ext in _suffixes:
            return name
        return None


def _unregister_module_extensions(module):
    for ep in _extension_points:
        ep.unregister_module(module)


class ExtensionPoint(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.__items = []
        _extension_points.append(self)

    def register(self, module, item):
        if module.startswith("picard.plugins"):
            module = module[15:]
        else:
            module = None
        self.__items.append((module, item))

    def unregister_module(self, name):
        self.__items = filter(lambda i: i[0] != name, self.__items)

    def __iter__(self):
        enabled_plugins = self.config.setting["enabled_plugins"].split()
        for module, item in self.__items:
            if module is None or module in enabled_plugins:
                yield item


class PluginWrapper(object):

    def __init__(self, module, plugindir):
        self.module = module
        self.compatible = False
        self.dir = plugindir

    def __get_name(self):
        try:
            return self.module.PLUGIN_NAME
        except AttributeError:
            return self.module_name
    name = property(__get_name)

    def __get_module_name(self):
        name = self.module.__name__
        if name.startswith("picard.plugins"):
            name = name[15:]
        return name
    module_name = property(__get_module_name)

    def __get_author(self):
        try:
            return self.module.PLUGIN_AUTHOR
        except AttributeError:
            return ""
    author = property(__get_author)

    def __get_description(self):
        try:
            return self.module.PLUGIN_DESCRIPTION
        except AttributeError:
            return ""
    description = property(__get_description)

    def __get_version(self):
        try:
            return self.module.PLUGIN_VERSION
        except AttributeError:
            return ""
    version = property(__get_version)

    def __get_api_versions(self):
        try:
            return self.module.PLUGIN_API_VERSIONS
        except AttributeError:
            return []
    api_versions = property(__get_api_versions)

    def __get_file(self):
        return self.module.__file__
    file = property(__get_file)


class PluginManager(QtCore.QObject):

    plugin_installed = QtCore.pyqtSignal(PluginWrapper, bool)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.plugins = []

    def load_plugindir(self, plugindir):
        if not os.path.isdir(plugindir):
            self.log.debug("Plugin directory %r doesn't exist", plugindir)
            return
        names = set()
        for path in [os.path.join(plugindir, file) for file in os.listdir(plugindir)]:
            name = _plugin_name_from_path(path)
            if name:
                names.add(name)
        for name in names:
            self.load_plugin(name, plugindir)

    def load_plugin(self, name, plugindir):
        self.log.debug("Loading plugin %r", name)
        info = imp.find_module(name, [plugindir])
        plugin = None
        try:
            index = None
            for i, p in enumerate(self.plugins):
                if name == p.module_name:
                    _unregister_module_extensions(name)
                    index = i
                    break
            plugin_module = imp.load_module("picard.plugins." + name, *info)
            plugin = PluginWrapper(plugin_module, plugindir)
            for version in list(plugin.api_versions):
                for api_version in picard.api_versions:
                    if api_version.startswith(version):
                        plugin.compatible = True
                        setattr(picard.plugins, name, plugin_module)
                        if index:
                            self.plugins[index] = plugin
                        else:
                            self.plugins.append(plugin)
                        break
                else:
                    continue
                break
            else:
                self.log.info("Plugin '%s' from '%s' is not compatible"
                    " with this version of Picard." % (plugin.name, plugin.file))
        except:
            self.log.error(traceback.format_exc())
        if info[0] is not None:
            info[0].close()
        return plugin

    def install_plugin(self, path, dest):
        plugin_name = _plugin_name_from_path(path)
        plugin_dir = self.tagger.user_plugin_dir
        if plugin_name:
            try:
                dest_exists = os.path.exists(dest)
                same_file = os.path.samefile(path, dest) if dest_exists else False
                if os.path.isfile(path) and not (dest_exists and same_file):
                    shutil.copy(path, dest)
                elif os.path.isdir(path) and not same_file:
                    if dest_exists:
                        shutil.rmtree(dest)
                    shutil.copytree(path, dest)
                plugin = self.load_plugin(plugin_name, plugin_dir)
                if plugin is not None:
                    self.plugin_installed.emit(plugin, False)
            except OSError, IOError:
                self.tagger.log.debug("Unable to copy %s to plugin folder %s" % (path, plugin_dir))

    def enabled(self, name):
        return True
