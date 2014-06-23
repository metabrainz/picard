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
from collections import defaultdict
import imp
import os.path
import shutil
import picard.plugins
import traceback
from picard import (config,
                    log,
                    version_from_string,
                    version_to_string,
                    VersionError)
from picard.const import USER_PLUGIN_DIR
from picard.util import os_path_samefile


_suffixes = [s[0] for s in imp.get_suffixes()]
_package_entries = ["__init__.py", "__init__.pyc", "__init__.pyo"]
_extension_points = []
_PLUGIN_MODULE_PREFIX = "picard.plugins."
_PLUGIN_MODULE_PREFIX_LEN = len(_PLUGIN_MODULE_PREFIX)


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


class ExtensionPoint(object):

    def __init__(self):
        self.__items = []
        _extension_points.append(self)

    def register(self, module, item):
        if module.startswith(_PLUGIN_MODULE_PREFIX):
            module = module[_PLUGIN_MODULE_PREFIX_LEN:]
        else:
            module = None
        self.__items.append((module, item))

    def unregister_module(self, name):
        self.__items = filter(lambda i: i[0] != name, self.__items)

    def __iter__(self):
        enabled_plugins = config.setting["enabled_plugins"]
        for module, item in self.__items:
            if module is None or module in enabled_plugins:
                yield item


class PluginWrapper(object):

    def __init__(self, module, plugindir, file=None):
        self.module = module
        self.compatible = False
        self.dir = plugindir
        self._file = file

    def __get_name(self):
        try:
            return self.module.PLUGIN_NAME
        except AttributeError:
            return self.module_name
    name = property(__get_name)

    def __get_module_name(self):
        name = self.module.__name__
        if name.startswith(_PLUGIN_MODULE_PREFIX):
            name = name[_PLUGIN_MODULE_PREFIX_LEN:]
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
        if not self._file:
            return self.module.__file__
        else:
            return self._file
    file = property(__get_file)


class PluginManager(QtCore.QObject):

    plugin_installed = QtCore.pyqtSignal(PluginWrapper, bool)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.plugins = []
        self._api_versions = set([version_from_string(v) for v in picard.api_versions])

    def load_plugindir(self, plugindir):
        plugindir = os.path.normpath(plugindir)
        if not os.path.isdir(plugindir):
            log.warning("Plugin directory %r doesn't exist", plugindir)
            return
        names = set()
        for path in [os.path.join(plugindir, file) for file in os.listdir(plugindir)]:
            name = _plugin_name_from_path(path)
            if name:
                names.add(name)
        log.debug("Looking for plugins in directory %r, %d names found",
                  plugindir,
                  len(names))
        for name in sorted(names):
            self.load_plugin(name, plugindir)

    def load_plugin(self, name, plugindir):
        try:
            info = imp.find_module(name, [plugindir])
        except ImportError:
            log.error("Failed loading plugin %r", name)
            return None

        plugin = None
        try:
            index = None
            for i, p in enumerate(self.plugins):
                if name == p.module_name:
                    log.warning("Module %r conflict: unregistering previously" \
                              " loaded %r version %s from %r",
                              p.module_name,
                              p.name,
                              p.version,
                              p.file)
                    _unregister_module_extensions(name)
                    index = i
                    break
            plugin_module = imp.load_module(_PLUGIN_MODULE_PREFIX + name, *info)
            plugin = PluginWrapper(plugin_module, plugindir, file=info[1])
            versions = [version_from_string(v) for v in
                        list(plugin.api_versions)]
            compatible_versions = list(set(versions) & self._api_versions)
            if compatible_versions:
                log.debug("Loading plugin %r version %s, compatible with API: %s",
                          plugin.name,
                          plugin.version,
                          ", ".join([version_to_string(v, short=True) for v in
                                     sorted(compatible_versions)]))
                plugin.compatible = True
                setattr(picard.plugins, name, plugin_module)
                if index is not None:
                    self.plugins[index] = plugin
                else:
                    self.plugins.append(plugin)
            else:
                log.warning("Plugin '%s' from '%s' is not compatible"
                            " with this version of Picard."
                            % (plugin.name, plugin.file))
        except VersionError as e:
            log.error("Plugin %r has an invalid API version string : %s", name, e)
        except:
            log.error("Plugin %r : %s", name, traceback.format_exc())
        if info[0] is not None:
            info[0].close()
        return plugin

    def install_plugin(self, path, dest):
        plugin_name = _plugin_name_from_path(path)
        if plugin_name:
            try:
                dest_exists = os.path.exists(dest)
                same_file = os_path_samefile(path, dest) if dest_exists else False
                if os.path.isfile(path) and not (dest_exists and same_file):
                    shutil.copy(path, dest)
                elif os.path.isdir(path) and not same_file:
                    if dest_exists:
                        shutil.rmtree(dest)
                    shutil.copytree(path, dest)
                plugin = self.load_plugin(plugin_name, USER_PLUGIN_DIR)
                if plugin is not None:
                    self.plugin_installed.emit(plugin, False)
            except (OSError, IOError):
                log.warning("Unable to copy %s to plugin folder %s" % (path, USER_PLUGIN_DIR))

    def enabled(self, name):
        return True


class PluginPriority:

    """
    Define few priority values for plugin functions execution order
    Those with higher values are executed first
    Default priority is PluginPriority.NORMAL
    """
    HIGH = 100
    NORMAL = 0
    LOW = -100


class PluginFunctions:

    """
    Store ExtensionPoint in a defaultdict with priority as key
    run() method will execute entries with higher priority value first
    """

    def __init__(self):
        self.functions = defaultdict(ExtensionPoint)

    def register(self, module, item, priority=PluginPriority.NORMAL):
        self.functions[priority].register(module, item)

    def run(self, *args, **kwargs):
        "Execute registered functions with passed parameters honouring priority"
        for priority, functions in sorted(self.functions.iteritems(),
                                          key=lambda (k, v): k,
                                          reverse=True):
            for function in functions:
                function(*args, **kwargs)
