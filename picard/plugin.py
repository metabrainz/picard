# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2015 Laurent Monin
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
import json
import os.path
import shutil
import picard.plugins
import traceback
import zipimport
from picard import (config,
                    log,
                    version_from_string,
                    version_to_string,
                    VersionError)
from picard.const import USER_PLUGIN_DIR, PLUGINS_API


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


def is_zip(path):
    if os.path.splitext(path)[1] == '.zip':
        return os.path.basename(path)
    return False

def zip_import(path):
    splitext = os.path.splitext(path)
    if (not os.path.isfile(path)
        or not splitext[1] == '.zip'):
        return (None, None)
    try:
        importer = zipimport.zipimporter(path)
        basename = os.path.basename(splitext[0])
        return (importer, basename)
    except zipimport.ZipImportError:
        return (None, None)


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


class PluginFlags(object):
    NONE = 0
    ENABLED = 1
    CAN_BE_UPDATED = 2
    CAN_BE_DOWNLOADED = 4


class PluginShared(object):

    def __init__(self):
        super(PluginShared, self).__init__()
        self.new_version = False
        self.flags = PluginFlags.NONE


class PluginWrapper(PluginShared):

    def __init__(self, module, plugindir, file=None):
        super(PluginWrapper, self).__init__()
        self.module = module
        self.compatible = False
        self.dir = plugindir
        self._file = file

    @property
    def name(self):
        try:
            return self.module.PLUGIN_NAME
        except AttributeError:
            return self.module_name

    @property
    def module_name(self):
        name = self.module.__name__
        if name.startswith(_PLUGIN_MODULE_PREFIX):
            name = name[_PLUGIN_MODULE_PREFIX_LEN:]
        return name

    @property
    def author(self):
        try:
            return self.module.PLUGIN_AUTHOR
        except AttributeError:
            return ""

    @property
    def description(self):
        try:
            return self.module.PLUGIN_DESCRIPTION
        except AttributeError:
            return ""

    @property
    def version(self):
        try:
            return self.module.PLUGIN_VERSION
        except AttributeError:
            return ""

    @property
    def api_versions(self):
        try:
            return self.module.PLUGIN_API_VERSIONS
        except AttributeError:
            return []

    @property
    def file(self):
        if not self._file:
            return self.module.__file__
        else:
            return self._file

    @property
    def license(self):
        try:
            return self.module.PLUGIN_LICENSE
        except AttributeError:
            return ""

    @property
    def license_url(self):
        try:
            return self.module.PLUGIN_LICENSE_URL
        except AttributeError:
            return ""

    @property
    def files_list(self):
        return self.file[len(self.dir)+1:]


class PluginData(PluginShared):

    """Used to store plugin data from JSON API"""
    def __init__(self, d, module_name):
        self.__dict__ = d
        super(PluginData, self).__init__()
        self.module_name = module_name

    @property
    def files_list(self):
        return ", ".join(self.files.keys())


class PluginManager(QtCore.QObject):

    plugin_installed = QtCore.pyqtSignal(PluginWrapper, bool)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.plugins = []
        self._api_versions = set([version_from_string(v) for v in picard.api_versions])
        self._available_plugins = {}

    @property
    def available_plugins(self):
        return self._available_plugins

    def load_plugindir(self, plugindir):
        plugindir = os.path.normpath(plugindir)
        if not os.path.isdir(plugindir):
            log.warning("Plugin directory %r doesn't exist", plugindir)
            return
        names = set()
        for path in [os.path.join(plugindir, file) for file in os.listdir(plugindir)]:
            name = is_zip(path)
            if not name:
                name = _plugin_name_from_path(path)
            if name:
                names.add(name)
        log.debug("Looking for plugins in directory %r, %d names found",
                  plugindir,
                  len(names))
        for name in sorted(names):
            self.load_plugin(name, plugindir)

    def load_plugin(self, name, plugindir):
        module_file = None
        (importer, module_name) = zip_import(os.path.join(plugindir, name))
        if importer:
            name = module_name
            if not importer.find_module(name):
                log.error("Failed loading zipped plugin %r", name)
                return None
            module_pathname = importer.get_filename(name)
        else:
            try:
                info = imp.find_module(name, [plugindir])
                module_file = info[0]
                module_pathname = info[1]
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
            if not importer:
                plugin_module = imp.load_module(_PLUGIN_MODULE_PREFIX + name, *info)
            else:
                plugin_module = importer.load_module(_PLUGIN_MODULE_PREFIX + name)
            plugin = PluginWrapper(plugin_module, plugindir, file=module_pathname)
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
        if module_file is not None:
            module_file.close()
        return plugin

    def install_plugin(self, path, overwrite_confirm=None):
        """
            path is either:
                1) /some/dir/name.py
                2) /some/dir/name (directory containing __init__.py)
                3) /some/dir/name.zip (containing either 1 or 2)

        """
        zip_plugin = is_zip(path)
        if not zip_plugin:
            plugin_name = _plugin_name_from_path(path)
        else:
            plugin_name = os.path.splitext(zip_plugin)[0]
        if plugin_name:
            try:
                dirpath = os.path.join(USER_PLUGIN_DIR, plugin_name)
                filepaths = [ os.path.join(USER_PLUGIN_DIR, f)
                              for f in os.listdir(USER_PLUGIN_DIR)
                              if f in [plugin_name + '.py',
                                       plugin_name + '.pyc',
                                       plugin_name + '.pyo',
                                       plugin_name + '.zip',
                                      ]]

                dir_exists = os.path.isdir(dirpath)
                files_exist = len(filepaths) > 0
                skip = False
                if dir_exists or files_exist:
                    skip = (overwrite_confirm and not
                            overwrite_confirm(plugin_name))
                    if not skip:
                        if dir_exists:
                            shutil.rmtree(dirpath)
                        if files_exist:
                            for filepath in filepaths:
                                os.remove(filepath)
                if not skip:
                    if os.path.isfile(path):
                        shutil.copy2(path, os.path.join(USER_PLUGIN_DIR,
                                                        os.path.basename(path)))
                    elif os.path.isdir(path):
                        shutil.copytree(path, os.path.join(USER_PLUGIN_DIR,
                                                           plugin_name))
                    plugin = self.load_plugin(zip_plugin or plugin_name, USER_PLUGIN_DIR)
                    if plugin is not None:
                        self.plugin_installed.emit(plugin, False)
            except (OSError, IOError):
                log.warning("Unable to copy %s to plugin folder %s" % (path, USER_PLUGIN_DIR))

    def query_available_plugins(self):
        self.tagger.xmlws.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['plugins'],
            self._plugins_json_loaded,
            xml=False,
            priority=True,
            important=True
        )

    def _plugins_json_loaded(self, response, reply, error):
        if error:
            self.tagger.window.set_statusbar_message(
                N_("Error loading plugins list: %(error)s"),
                {'error': unicode(error)},
                echo=log.error
            )
        else:
            self._available_plugins = [PluginData(data, key) for key, data in
                                       json.loads(response)['plugins'].items()]

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
                                          key=lambda i: i[0],
                                          reverse=True):
            for function in functions:
                function(*args, **kwargs)
