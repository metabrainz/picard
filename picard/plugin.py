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

from PyQt5 import QtCore
from collections import defaultdict
from functools import partial
import json
import imp
import os.path
import shutil
import picard.plugins
import tempfile
import traceback
import zipfile
import zipimport
from picard import (config,
                    log,
                    version_from_string,
                    version_to_string,
                    VersionError)
from picard.const import USER_PLUGIN_DIR, PLUGINS_API, PLUGIN_ACTION_UPDATE
from picard.util import load_json

_suffixes = [s[0] for s in imp.get_suffixes()]
_package_entries = ["__init__.py", "__init__.pyc", "__init__.pyo"]
_extension_points = []
_PLUGIN_MODULE_PREFIX = "picard.plugins."
_PLUGIN_MODULE_PREFIX_LEN = len(_PLUGIN_MODULE_PREFIX)
_PLUGIN_PACKAGE_SUFFIX = ".picard"
_PLUGIN_PACKAGE_SUFFIX_LEN = len(_PLUGIN_PACKAGE_SUFFIX)


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


def load_manifest(archive_path):
    archive = zipfile.ZipFile(archive_path)
    manifest_data = None
    with archive.open('MANIFEST.json') as f:
        manifest_data = json.loads(str(f.read().decode()))
    return manifest_data


def zip_import(path):
    splitext = os.path.splitext(path)
    if (not os.path.isfile(path)
        or not splitext[1] == '.zip'):
        return (None, None, None)
    try:
        importer = zipimport.zipimporter(path)
        basename = os.path.basename(splitext[0])
        manifest_data = None
        if basename.endswith(_PLUGIN_PACKAGE_SUFFIX):
            basename = basename[:-_PLUGIN_PACKAGE_SUFFIX_LEN]
            try:
                manifest_data = load_manifest(path)
            except Exception:
                pass
        return (importer, basename, manifest_data)
    except zipimport.ZipImportError:
        return (None, None, None)


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
        self.__items = [item for item in self.__items if item[0] != name]

    def __iter__(self):
        enabled_plugins = config.setting["enabled_plugins"]
        for module, item in self.__items:
            if module is None or module in enabled_plugins:
                yield item


class PluginShared(object):

    def __init__(self):
        super().__init__()
        self.new_version = ""
        self.enabled = False
        self.can_be_updated = False
        self.can_be_downloaded = False
        self.marked_for_update = False
        self.is_uninstalled = False


class PluginWrapper(PluginShared):

    def __init__(self, module, plugindir, file=None, manifest_data=None):
        super().__init__()
        self.module = module
        self.compatible = False
        self.dir = plugindir
        self._file = file
        self.data = manifest_data or self.module.__dict__

    @property
    def name(self):
        try:
            return self.data['PLUGIN_NAME']
        except KeyError:
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
            return self.data['PLUGIN_AUTHOR']
        except KeyError:
            return ""

    @property
    def description(self):
        try:
            return self.data['PLUGIN_DESCRIPTION']
        except KeyError:
            return ""

    @property
    def version(self):
        try:
            return self.data['PLUGIN_VERSION']
        except KeyError:
            return ""

    @property
    def api_versions(self):
        try:
            return self.data['PLUGIN_API_VERSIONS']
        except KeyError:
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
            return self.data['PLUGIN_LICENSE']
        except KeyError:
            return ""

    @property
    def license_url(self):
        try:
            return self.data['PLUGIN_LICENSE_URL']
        except KeyError:
            return ""

    @property
    def files_list(self):
        return self.file[len(self.dir)+1:]


class PluginData(PluginShared):

    """Used to store plugin data from JSON API"""
    def __init__(self, d, module_name):
        self.__dict__ = d
        super().__init__()
        self.module_name = module_name

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            log.debug('Attribute %r not found for plugin %r', name, self.module_name)
            return None

    @property
    def files_list(self):
        return ", ".join(self.files.keys())


class PluginManager(QtCore.QObject):

    plugin_installed = QtCore.pyqtSignal(PluginWrapper, bool)
    plugin_updated = QtCore.pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.plugins = []
        self._api_versions = set([version_from_string(v) for v in picard.api_versions])
        self._available_plugins = {}

    @property
    def available_plugins(self):
        return self._available_plugins

    def load_plugindir(self, plugindir):
        plugindir = os.path.normpath(plugindir)
        if not os.path.isdir(plugindir):
            log.info("Plugin directory %r doesn't exist", plugindir)
            return
        # first, handle eventual plugin updates
        for updatepath in [os.path.join(plugindir, file) for file in
                     os.listdir(plugindir) if file.endswith('.update')]:
            path = os.path.splitext(updatepath)[0]
            name = is_zip(path)
            if not name:
                name = _plugin_name_from_path(path)
            if name:
                self.remove_plugin(name)
                os.rename(updatepath, path)
                log.debug('Updating plugin %r (%r))', name, path)
            else:
                log.error('Cannot get plugin name from %r', updatepath)
        # now load found plugins
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
            try:
                self.load_plugin(name, plugindir)
            except Exception as e:
                log.error('Unable to load plugin: %s.\nError occured: %s', name, e)

    def load_plugin(self, name, plugindir):
        module_file = None
        (importer, module_name, manifest_data) = zip_import(os.path.join(plugindir, name))
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
                    log.warning("Module %r conflict: unregistering previously"
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
            plugin = PluginWrapper(plugin_module, plugindir,
                                   file=module_pathname, manifest_data=manifest_data)
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

    def _get_existing_paths(self, plugin_name):
        dirpath = os.path.join(USER_PLUGIN_DIR, plugin_name)
        if not os.path.isdir(dirpath):
            dirpath = None
        fileexts = ['.py', '.pyc', '.pyo', '.zip']
        filepaths = [os.path.join(USER_PLUGIN_DIR, f)
                      for f in os.listdir(USER_PLUGIN_DIR)
                      if f in [plugin_name + ext for ext in fileexts]
                    ]
        return (dirpath, filepaths)

    def remove_plugin(self, plugin_name):
        if plugin_name.endswith('.zip'):
            plugin_name = os.path.splitext(plugin_name)[0]
        log.debug("Remove plugin files and dirs : %r", plugin_name)
        dirpath, filepaths = self._get_existing_paths(plugin_name)
        if dirpath:
            if os.path.islink(dirpath):
                log.debug("Removing symlink %r", dirpath)
                os.remove(dirpath)
            elif os.path.isdir(dirpath):
                log.debug("Removing directory %r", dirpath)
                shutil.rmtree(dirpath)
        if filepaths:
            for filepath in filepaths:
                log.debug("Removing file %r", filepath)
                os.remove(filepath)

    def install_plugin(self, path, action, overwrite_confirm=None, plugin_name=None,
                       plugin_data=None):
        """
            path is either:
                1) /some/dir/name.py
                2) /some/dir/name (directory containing __init__.py)
                3) /some/dir/name.zip (containing either 1 or 2)

        """
        zip_plugin = False
        if not plugin_name:
            zip_plugin = is_zip(path)
            if not zip_plugin:
                plugin_name = _plugin_name_from_path(path)
            else:
                plugin_name = os.path.splitext(zip_plugin)[0]
        if plugin_name:
            try:
                if plugin_data and plugin_name:
                    # zipped module from download
                    zip_plugin = plugin_name + '.zip'
                    dst = os.path.join(USER_PLUGIN_DIR, zip_plugin)
                    if action == PLUGIN_ACTION_UPDATE:
                        dst += '.update'
                        if os.path.isfile(dst):
                            os.remove(dst)
                    ziptmp = tempfile.NamedTemporaryFile(delete=False,
                                                         dir=USER_PLUGIN_DIR).name
                    try:
                        with open(ziptmp, "wb") as zipfile:
                            zipfile.write(plugin_data)
                            zipfile.flush()
                            os.fsync(zipfile.fileno())
                        os.rename(ziptmp, dst)
                        log.debug("Plugin saved to %r", dst)
                    except:
                        try:
                            os.remove(ziptmp)
                        except (IOError, OSError):
                            pass
                        raise
                elif os.path.isfile(path):
                    dst = os.path.join(USER_PLUGIN_DIR, os.path.basename(path))
                    if action == PLUGIN_ACTION_UPDATE:
                        dst += '.update'
                        if os.path.isfile(dst):
                            os.remove(dst)
                    shutil.copy2(path, dst)
                elif os.path.isdir(path):
                    dst = os.path.join(USER_PLUGIN_DIR, plugin_name)
                    if action == PLUGIN_ACTION_UPDATE:
                        dst += '.update'
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                    shutil.copytree(path, dst)
                if action != PLUGIN_ACTION_UPDATE:
                    try:
                        installed_plugin = self.load_plugin(zip_plugin or plugin_name, USER_PLUGIN_DIR)
                    except Exception as e:
                        log.error('Unable to load plugin: %s.\nError occured: %s', name, e)
                        installed_plugin = None

                    if installed_plugin is not None:
                        self.plugin_installed.emit(installed_plugin, False)
                else:
                    self.plugin_updated.emit(plugin_name, False)
            except (OSError, IOError):
                log.warning("Unable to copy %s to plugin folder %s" % (path, USER_PLUGIN_DIR))

    def query_available_plugins(self, callback=None):
        self.tagger.webservice.get(
            PLUGINS_API['host'],
            PLUGINS_API['port'],
            PLUGINS_API['endpoint']['plugins'],
            partial(self._plugins_json_loaded, callback=callback),
            parse_response_type=None,
            priority=True,
            important=True
        )

    def _plugins_json_loaded(self, response, reply, error, callback=None):
        if error:
            self.tagger.window.set_statusbar_message(
                N_("Error loading plugins list: %(error)s"),
                {'error': reply.errorString()},
                echo=log.error
            )
        else:
            self._available_plugins = [PluginData(data, key) for key, data in
                                       load_json(response)['plugins'].items()]
        if callback:
            callback()

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
        for priority, functions in sorted(self.functions.items(),
                                          key=lambda i: i[0],
                                          reverse=True):
            for function in functions:
                function(*args, **kwargs)
