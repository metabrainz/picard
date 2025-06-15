# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2014, 2017-2021, 2023 Philipp Wolfer
# Copyright (C) 2011 johnny64
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013 Sebastian Ramacher
# Copyright (C) 2013 Wieland Hoffmann
# Copyright (C) 2013 brainz34
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2014 Johannes Dewender
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2014-2015, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2023 tuspar
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

from collections import defaultdict
import os.path

from picard import log
from picard.const import USER_PLUGIN_DIR
from picard.extension_points import (
    PLUGIN_MODULE_PREFIX,
    PLUGIN_MODULE_PREFIX_LEN,
    ExtensionPoint,
)
from picard.version import (
    Version,
    VersionError,
)


try:
    from markdown import markdown
except ImportError:
    def markdown(text):
        # Simple fallback, just make sure line breaks are applied
        if not text:
            return ''
        return text.strip().replace('\n', '<br>\n')


class PluginShared:

    def __init__(self):
        super().__init__()


class PluginWrapper(PluginShared):

    def __init__(self, module, plugindir, file=None, manifest_data=None):
        super().__init__()
        self.module = module
        self.compatible = False
        self.dir = os.path.normpath(plugindir)
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
        if name.startswith(PLUGIN_MODULE_PREFIX):
            name = name[PLUGIN_MODULE_PREFIX_LEN:]
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
            return markdown(self.data['PLUGIN_DESCRIPTION'])
        except KeyError:
            return ""

    @property
    def version(self):
        try:
            return Version.from_string(self.data['PLUGIN_VERSION'])
        except (KeyError, VersionError):
            return Version(0, 0, 0)

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
    def user_guide_url(self):
        try:
            return self.data['PLUGIN_USER_GUIDE_URL']
        except KeyError:
            return ""

    @property
    def files_list(self):
        return self.file[len(self.dir)+1:]

    @property
    def is_user_installed(self):
        return self.dir == USER_PLUGIN_DIR


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
            log.debug("Attribute %r not found for plugin %r", name, self.module_name)
            return None

    @property
    def version(self):
        try:
            return Version.from_string(self.__dict__['version'])
        except (KeyError, VersionError):
            return Version(0, 0, 0)

    @property
    def files_list(self):
        return ", ".join(self.files.keys())


class PluginFunctions:

    """
    Store ExtensionPoint in a defaultdict with priority as key
    run() method will execute entries with higher priority value first
    """

    def __init__(self, label=None):
        self.functions = defaultdict(lambda: ExtensionPoint(label=label))

    def register(self, module, item, priority=0):
        self.functions[priority].register(module, item)

    def _get_functions(self):
        """Returns registered functions by order of priority (highest first) and registration"""
        for _priority, functions in sorted(self.functions.items(),
                                          key=lambda i: i[0],
                                          reverse=True):
            yield from functions

    def run(self, *args, **kwargs):
        """Execute registered functions with passed parameters honouring priority"""
        for function in self._get_functions():
            function(*args, **kwargs)
