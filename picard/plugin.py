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
import picard.plugins
import traceback


def plugin_name_from_module(module):
    name = module.__name__
    if name.startswith("picard.plugins"):
        return name[15:]
    else:
        return None


class ExtensionPoint(QtCore.QObject):

    def __init__(self):
        self.__items = []

    def register(self, module, item):
        if module.startswith("picard.plugins"):
            module = module[15:]
        else:
            module = None
        self.__items.append((module, item))

    def __iter__(self):
        enabled_plugins = self.config.setting["enabled_plugins"].split()
        for module, item in self.__items:
            if module is None or module in enabled_plugins:
                yield item


class PluginWrapper(object):

    def __init__(self, module):
        self.module = module

    def __get_name(self):
        try:
            return self.module.PLUGIN_NAME
        except AttributeError:
            return self.module.name
    name = property(__get_name)

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

    def __get_file(self):
        return self.module.__file__
    file = property(__get_file)


class PluginManager(QtCore.QObject):

    def __init__(self):
        self.plugins = []

    def load(self, plugindir):
        if not os.path.isdir(plugindir):
            self.log.info("Plugin directory '%s' doesn't exist", plugindir)
            return

        names = set()
        suffixes = [s[0] for s in imp.get_suffixes()]
        package_entries = ["__init__.py", "__init__.pyc", "__init__.pyo"]
        for name in os.listdir(plugindir):
            path = os.path.join(plugindir, name)
            if os.path.isdir(path):
                for entry in package_entries:
                    if os.path.isfile(os.path.join(path, entry)):
                        break
                else:
                    continue
            else:
                name, suffix = os.path.splitext(name)
                if suffix not in suffixes:
                    continue
            if hasattr(picard.plugins, name):
                self.log.info("Plugin %s already loaded!", name)
            else:
                names.add(name)

        for name in names:
            self.log.debug("Loading plugin %s", name)
            info = imp.find_module(name, [plugindir])
            try:
                plugin = imp.load_module('picard.plugins.' + name, *info)
                setattr(picard.plugins, name, plugin)
                self.plugins.append(PluginWrapper(plugin))
            except:
                self.log.error(traceback.format_exc())
            if info[0] is not None:
                info[0].close()

    def enabled(self, name):
        return True
