# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2015-2021, 2023-2024 Laurent Monin
# Copyright (C) 2019 Wieland Hoffmann
# Copyright (C) 2019-2020, 2022-2023 Philipp Wolfer
# Copyright (C) 2022 skelly37
# Copyright (C) 2023 Bob Swift
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


from functools import partial
import importlib
from importlib.abc import MetaPathFinder
import json
import os.path
import shutil
import sys
import tempfile
import zipfile
import zipimport

from PyQt6 import QtCore

from picard import log
from picard.const import (
    PLUGINS_API,
    USER_PLUGIN_DIR,
)
from picard.const.sys import IS_FROZEN
from picard.plugin import (
    _PLUGIN_MODULE_PREFIX,
    PluginData,
    PluginWrapper,
    _unregister_module_extensions,
)
import picard.plugins
from picard.version import (
    Version,
    VersionError,
)


_SUFFIXES = tuple(importlib.machinery.all_suffixes())
_PACKAGE_ENTRIES = ("__init__.py", "__init__.pyc", "__init__.pyo")
_PLUGIN_PACKAGE_SUFFIX = ".picard"
_PLUGIN_PACKAGE_SUFFIX_LEN = len(_PLUGIN_PACKAGE_SUFFIX)
_FILEEXTS = ('.py', '.pyc', '.pyo', '.zip')
_UPDATE_SUFFIX = '.update'
_UPDATE_SUFFIX_LEN = len(_UPDATE_SUFFIX)


_extension_points = []


def is_update(path):
    return path.endswith(_UPDATE_SUFFIX)


def strip_update_suffix(path):
    if not is_update(path):
        return path
    return path[:-_UPDATE_SUFFIX_LEN]


def is_zip(path):
    return path.endswith('.zip')


def strip_zip_suffix(path):
    if not is_zip(path):
        return path
    return path[:-4]


def is_package(path):
    return path.endswith(_PLUGIN_PACKAGE_SUFFIX)


def strip_package_suffix(path):
    if not is_package(path):
        return path
    return path[:-_PLUGIN_PACKAGE_SUFFIX_LEN]


def is_zipped_package(path):
    return path.endswith(_PLUGIN_PACKAGE_SUFFIX + '.zip')


def _plugin_name_from_path(path):
    path = os.path.normpath(path)
    if is_zip(path):
        name = os.path.basename(strip_zip_suffix(path))
        if is_package(name):
            return strip_package_suffix(name)
        else:
            return name
    elif os.path.isdir(path):
        for entry in _PACKAGE_ENTRIES:
            if os.path.isfile(os.path.join(path, entry)):
                return os.path.basename(path)
    else:
        file = os.path.basename(path)
        if file in _PACKAGE_ENTRIES:
            return None
        name, ext = os.path.splitext(file)
        if ext in _SUFFIXES:
            return name
        return None


def load_zip_manifest(archive_path):
    if is_zipped_package(archive_path):
        try:
            archive = zipfile.ZipFile(archive_path)
            with archive.open('MANIFEST.json') as f:
                return json.loads(str(f.read().decode()))
        except Exception as why:
            log.warning("Failed to load manifest data from json: %s", why)
            return None


def zip_import(path):
    if (not is_zip(path) or not os.path.isfile(path)):
        return None
    try:
        return zipimport.zipimporter(path)
    except zipimport.ZipImportError as why:
        log.error("ZIP import error: %s", why)
        return None


def _compatible_api_versions(api_versions):
    versions = [Version.from_string(v) for v in list(api_versions)]
    return set(versions) & set(picard.api_versions_tuple)


_plugin_dirs = []


def plugin_dirs():
    yield from _plugin_dirs


def init_default_plugin_dirs():
    # Add user plugin dir first
    if not os.path.exists(USER_PLUGIN_DIR):
        os.makedirs(USER_PLUGIN_DIR)
    register_plugin_dir(USER_PLUGIN_DIR)

    # Register system wide plugin dir
    if IS_FROZEN:
        toppath = sys.argv[0]
    else:
        toppath = os.path.abspath(__file__)

    topdir = os.path.dirname(toppath)
    plugin_dir = os.path.join(topdir, "plugins")
    register_plugin_dir(plugin_dir)


def register_plugin_dir(path):
    if path not in _plugin_dirs:
        _plugin_dirs.append(path)


def plugin_dir_for_path(path):
    for plugin_dir in plugin_dirs():
        try:
            if os.path.commonpath((path, plugin_dir)) == plugin_dir:
                return plugin_dir
        except ValueError:
            pass
    return path


class PluginManager(QtCore.QObject):

    plugin_installed = QtCore.pyqtSignal(PluginWrapper, bool)
    plugin_updated = QtCore.pyqtSignal(str, bool)
    plugin_removed = QtCore.pyqtSignal(str, bool)
    plugin_errored = QtCore.pyqtSignal(str, str, bool)
    updates_available = QtCore.pyqtSignal(list)

    def __init__(self, plugins_directory=None):
        super().__init__()
        self.plugins = []
        self._available_plugins = None  # None=never loaded, [] = empty
        if plugins_directory is None:
            plugins_directory = USER_PLUGIN_DIR
        self.plugins_directory = os.path.normpath(plugins_directory)
        init_default_plugin_dirs()

    @property
    def available_plugins(self):
        return self._available_plugins

    def plugin_error(self, name, error, *args, **kwargs):
        """Log a plugin loading error for the plugin `name` and signal the
        error via the `plugin_errored` signal.

        A string consisting of all `args` interpolated into `error` will be
        passed to the function given via the `log_func` keyword argument
        (default: log.error) and as the error message to the `plugin_errored`
        signal.

        Instead of using `args` the interpolation parameters can also be passed
        with the `params` keyword parameter. This is specifically useful to
        pass a dictionary when using named placeholders."""
        params = kwargs.get('params', args)
        if params:
            error = error % params
        log_func = kwargs.get('log_func', log.error)
        log_func(error)
        self.plugin_errored.emit(name, error, False)

    def _marked_for_update(self):
        for file in os.listdir(self.plugins_directory):
            if file.endswith(_UPDATE_SUFFIX):
                source_path = os.path.join(self.plugins_directory, file)
                target_path = strip_update_suffix(source_path)
                plugin_name = _plugin_name_from_path(target_path)
                if plugin_name:
                    yield (source_path, target_path, plugin_name)
                else:
                    log.error('Cannot get plugin name from %r', source_path)

    def handle_plugin_updates(self):
        for source_path, target_path, plugin_name in self._marked_for_update():
            self._remove_plugin(plugin_name)
            os.rename(source_path, target_path)
            log.debug("Updating plugin %r (%r))", plugin_name, target_path)

    def load_plugins_from_directory(self, plugindir):
        plugindir = os.path.normpath(plugindir)
        if not os.path.isdir(plugindir):
            log.info("Plugin directory %r doesn't exist", plugindir)
            return
        if plugindir == self.plugins_directory:
            # .update trick is only for plugins installed through the Picard UI
            # and only for plugins in plugins_directory (USER_PLUGIN_DIR by default)
            self.handle_plugin_updates()
        # now load found plugins
        names = set()
        for path in (os.path.join(plugindir, file) for file in os.listdir(plugindir)):
            name = _plugin_name_from_path(path)
            if name:
                names.add(name)
        log.debug("Looking for plugins in directory %r, %d names found",
                  plugindir,
                  len(names))
        for name in sorted(names):
            try:
                self._load_plugin(name)
            except Exception:
                self.plugin_error(name, _("Unable to load plugin '%s'"), name, log_func=log.exception)

    def _get_plugin_index_by_name(self, name):
        for index, plugin in enumerate(self.plugins):
            if name == plugin.module_name:
                return (plugin, index)
        return (None, None)

    def _load_plugin(self, name):
        existing_plugin, existing_plugin_index = self._get_plugin_index_by_name(name)
        if existing_plugin:
            log.debug("Ignoring already loaded plugin %r (version %r at %r)",
                existing_plugin.module_name,
                existing_plugin.version,
                existing_plugin.file)
            return

        spec = None
        module_pathname = None
        zip_importer = None
        manifest_data = None
        full_module_name = _PLUGIN_MODULE_PREFIX + name

        # Legacy loading of ZIP plugins. In Python >= 3.10 this is all handled
        # by PluginMetaPathFinder. Remove once Python 3.9 is no longer supported.
        if not hasattr(zipimport.zipimporter, 'find_spec'):
            (zip_importer, plugin_dir, module_pathname, manifest_data) = self._legacy_load_zip_plugin(name)

        if not module_pathname:
            spec = PluginMetaPathFinder().find_spec(full_module_name, [])
            if not spec or not spec.loader:
                errorfmt = _('Failed loading plugin "%(plugin)s"')
                self.plugin_error(name, errorfmt, params={
                    'plugin': name,
                })
                return None

            module_pathname = spec.origin
            if isinstance(spec.loader, zipimport.zipimporter):
                manifest_data = load_zip_manifest(spec.loader.archive)
            if os.path.basename(module_pathname) == '__init__.py':
                module_pathname = os.path.dirname(module_pathname)
            plugin_dir = plugin_dir_for_path(module_pathname)

        plugin = None
        try:
            if zip_importer:  # Legacy ZIP import for Python < 3.10
                plugin_module = zip_importer.load_module(full_module_name)
            else:
                plugin_module = importlib.util.module_from_spec(spec)
                # This is kind of a hack. The module will be in sys.modules
                # after exec_module has run. But if inside of the loaded plugin
                # there are relative imports it would load the same plugin
                # module twice. This executes the plugins code twice and leads
                # to potential side effects.
                sys.modules[full_module_name] = plugin_module
                try:
                    spec.loader.exec_module(plugin_module)
                except:  # noqa: E722
                    del sys.modules[full_module_name]
                    raise

            plugin = PluginWrapper(plugin_module, plugin_dir,
                                   file=module_pathname, manifest_data=manifest_data)
            compatible_versions = _compatible_api_versions(plugin.api_versions)
            if compatible_versions:
                log.debug("Loading plugin %r version %s, compatible with API: %s",
                          plugin.name,
                          plugin.version,
                          ", ".join([v.short_str() for v in
                                     sorted(compatible_versions)]))
                plugin.compatible = True
                setattr(picard.plugins, name, plugin_module)
                if existing_plugin:
                    self.plugins[existing_plugin_index] = plugin
                else:
                    self.plugins.append(plugin)
            else:
                errorfmt = _('Plugin "%(plugin)s" from "%(filename)s" is not '
                             'compatible with this version of Picard.')
                params = {'plugin': plugin.name, 'filename': plugin.file}
                self.plugin_error(plugin.name, errorfmt, params=params, log_func=log.warning)
        except VersionError as e:
            errorfmt = _('Plugin "%(plugin)s" has an invalid API version string: %(error)s')
            self.plugin_error(name, errorfmt, params={
                'plugin': name,
                'error': e,
            })
        except BaseException:
            errorfmt = _('Plugin "%(plugin)s"')
            self.plugin_error(name, errorfmt, log_func=log.exception,
                              params={'plugin': name})
        return plugin

    def _legacy_load_zip_plugin(self, name):
        for plugin_dir in plugin_dirs():
            zipfilename = os.path.join(plugin_dir, name + '.zip')
            zip_importer = zip_import(zipfilename)
            if zip_importer:
                if not zip_importer.find_module(name):
                    errorfmt = _('Failed loading zipped plugin "%(plugin)s" from "%(filename)s"')
                    self.plugin_error(name, errorfmt, params={
                        'plugin': name,
                        'filename': zipfilename,
                    })
                    return (None, None, None, None)
                module_pathname = zip_importer.get_filename(name)
                manifest_data = load_zip_manifest(zip_importer.archive)
                return (zip_importer, plugin_dir, module_pathname, manifest_data)
        return (None, None, None, None)

    def _get_existing_paths(self, plugin_name, fileexts):
        dirpath = os.path.join(self.plugins_directory, plugin_name)
        if not os.path.isdir(dirpath):
            dirpath = None
        filenames = {plugin_name + ext for ext in fileexts}
        filepaths = [os.path.join(self.plugins_directory, f)
                     for f in os.listdir(self.plugins_directory)
                     if f in filenames
                     ]
        return (dirpath, filepaths)

    def _remove_plugin_files(self, plugin_name, with_update=False):
        plugin_name = strip_zip_suffix(plugin_name)
        log.debug("Remove plugin files and dirs : %r", plugin_name)
        dirpath, filepaths = self._get_existing_paths(plugin_name, _FILEEXTS)
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
                if with_update:
                    update = filepath + _UPDATE_SUFFIX
                    if os.path.isfile(update):
                        log.debug("Removing file %r", update)
                        os.remove(update)

    def _remove_plugin(self, plugin_name, with_update=False):
        self._remove_plugin_files(plugin_name, with_update)
        _unregister_module_extensions(plugin_name)
        self.plugins = [p for p in self.plugins if p.module_name != plugin_name]

    def remove_plugin(self, plugin_name, with_update=False):
        self._remove_plugin(plugin_name, with_update=with_update)
        self.plugin_removed.emit(plugin_name, False)

    def _install_plugin_zip(self, plugin_name, plugin_data, update=False):
        # zipped module from download
        zip_plugin = plugin_name + '.zip'
        dst = os.path.join(self.plugins_directory, zip_plugin)
        if update:
            dst += _UPDATE_SUFFIX
            if os.path.isfile(dst):
                os.remove(dst)
        with tempfile.NamedTemporaryFile(dir=self.plugins_directory) as zipfile:
            zipfile.write(plugin_data)
            zipfile.flush()
            os.fsync(zipfile.fileno())
            try:
                os.link(zipfile.name, dst)
            except OSError:
                with open(dst, 'wb') as dstfile:
                    zipfile.seek(0)
                    shutil.copyfileobj(zipfile, dstfile)
            log.debug("Plugin (zipped) saved to %r", dst)

    def _install_plugin_file(self, path, update=False):
        dst = os.path.join(self.plugins_directory, os.path.basename(path))
        if update:
            dst += _UPDATE_SUFFIX
            if os.path.isfile(dst):
                os.remove(dst)
        shutil.copy2(path, dst)
        log.debug("Plugin (file) saved to %r", dst)

    def _install_plugin_dir(self, plugin_name, path, update=False):
        dst = os.path.join(self.plugins_directory, plugin_name)
        if update:
            dst += _UPDATE_SUFFIX
            if os.path.isdir(dst):
                shutil.rmtree(dst)
        shutil.copytree(path, dst)
        log.debug("Plugin (directory) saved to %r", dst)

    def install_plugin(self, path, update=False, plugin_name=None, plugin_data=None):
        """
            path is either:
                1) /some/dir/name.py
                2) /some/dir/name (directory containing __init__.py)
                3) /some/dir/name.zip (containing either 1 or 2)

        """
        assert path or plugin_name, "path is required if plugin_name is empty"

        if not plugin_name:
            plugin_name = _plugin_name_from_path(path)
        if plugin_name:
            try:
                if plugin_data:
                    self._install_plugin_zip(plugin_name, plugin_data, update=update)
                elif os.path.isfile(path):
                    self._install_plugin_file(path, update=update)
                elif os.path.isdir(path):
                    self._install_plugin_dir(plugin_name, path, update=update)
            except OSError as why:
                log.error("Unable to copy plugin '%s' to %r: %s", plugin_name, self.plugins_directory, why)
                return

            if not update:
                try:
                    installed_plugin = self._load_plugin(plugin_name)
                    if not installed_plugin:
                        raise RuntimeError("Failed loading newly installed plugin %s" % plugin_name)
                except Exception as e:
                    log.error("Unable to load plugin '%s': %s", plugin_name, e)
                    self._remove_plugin(plugin_name)
                else:
                    self.plugin_installed.emit(installed_plugin, False)
            else:
                self.plugin_updated.emit(plugin_name, False)

    def query_available_plugins(self, callback=None):
        self.tagger.webservice.get_url(
            url=PLUGINS_API['urls']['plugins'],
            handler=partial(self._plugins_json_loaded, callback=callback),
            priority=True,
            important=True,
        )

    def is_available(self, plugin_name):
        return any(p.module_name == plugin_name for p in self._available_plugins)

    def _plugins_json_loaded(self, response, reply, error, callback=None):
        if error:
            self.tagger.window.set_statusbar_message(
                N_("Error loading plugins list: %(error)s"),
                {'error': reply.errorString()},
                echo=log.error
            )
            self._available_plugins = []
        else:
            try:
                self._available_plugins = [PluginData(data, key) for key, data in
                                           response['plugins'].items()
                                           if _compatible_api_versions(data['api_versions'])]
            except (AttributeError, KeyError, TypeError):
                self._available_plugins = []
        if callback:
            callback()

    # pylint: disable=no-self-use
    def enabled(self, name):
        return True

    def _plugins_have_new_versions(self):
        """Compare available plugins versions with installed plugins ones
        and yield plugin names of plugins that have new versions"""
        if self.available_plugins is not None:
            available_versions = {p.module_name: p.version for p in self.available_plugins}
            for plugin in self.plugins:
                if plugin.module_name not in available_versions:
                    continue
                if available_versions[plugin.module_name] > plugin.version:
                    yield plugin.name

    def check_update(self):
        if self.available_plugins is None:
            self.query_available_plugins(self._notify_updates)
        else:
            self._notify_updates()

    def _notify_updates(self):
        plugins_with_updates = list(self._plugins_have_new_versions())
        if plugins_with_updates:
            self.updates_available.emit(plugins_with_updates)


class PluginMetaPathFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(_PLUGIN_MODULE_PREFIX):
            return None
        plugin_name = fullname[len(_PLUGIN_MODULE_PREFIX):]
        for plugin_dir in plugin_dirs():
            for file_path in self._plugin_file_paths(plugin_dir, plugin_name):
                if os.path.exists(file_path):
                    spec = self._spec_from_path(fullname, file_path)
                    if spec and spec.loader:
                        return spec

    def _spec_from_path(self, fullname, file_path):
        if file_path.endswith('.zip'):
            return self._spec_from_zip(fullname, file_path)
        else:
            return importlib.util.spec_from_file_location(fullname, file_path)

    def _spec_from_zip(self, fullname, file_path):
        zip_importer = zip_import(file_path)
        if zip_importer:
            return zip_importer.find_spec(fullname)

    @staticmethod
    def _plugin_file_paths(plugin_dir, plugin_name):
        for entry in _PACKAGE_ENTRIES:
            yield os.path.join(plugin_dir, plugin_name, entry)
        for ext in _FILEEXTS:
            # On Python < 3.10 ZIP file loading is handled in PluginManager._load_plugin
            if ext == '.zip' and not hasattr(zipimport.zipimporter, 'find_spec'):
                continue
            yield os.path.join(plugin_dir, plugin_name + ext)


sys.meta_path.append(PluginMetaPathFinder())
