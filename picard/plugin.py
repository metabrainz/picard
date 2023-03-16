# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2014, 2017-2021 Philipp Wolfer
# Copyright (C) 2011 johnny64
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013 Sebastian Ramacher
# Copyright (C) 2013 Wieland Hoffmann
# Copyright (C) 2013 brainz34
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2014 Johannes Dewender
# Copyright (C) 2014 Shadab Zafar
# Copyright (C) 2014-2015, 2018-2021 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Vishal Choudhary
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
from picard.config import get_config
from picard.const import USER_PLUGIN_DIR
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

_PLUGIN_MODULE_PREFIX = "picard.plugins."
_PLUGIN_MODULE_PREFIX_LEN = len(_PLUGIN_MODULE_PREFIX)

_extension_points = []


def _unregister_module_extensions(module):
    for ep in _extension_points:
        ep.unregister_module(module)


class ExtensionPoint(object):

    def __init__(self, label=None):
        if label is None:
            import uuid
            label = uuid.uuid4()
        self.label = label
        self.__dict = defaultdict(list)
        _extension_points.append(self)

    def register(self, module, item):
        if module.startswith(_PLUGIN_MODULE_PREFIX):
            name = module[_PLUGIN_MODULE_PREFIX_LEN:]
            log.debug("ExtensionPoint: %s register <- plugin=%r item=%r" % (self.label, name, item))
        else:
            name = None
            # uncomment to debug internal extensions loaded at startup
            # print("ExtensionPoint: %s register <- item=%r" % (self.label, item))
        self.__dict[name].append(item)

    def unregister_module(self, name):
        try:
            del self.__dict[name]
        except KeyError:
            # NOTE: needed due to defaultdict behaviour:
            # >>> d = defaultdict(list)
            # >>> del d['a']
            # KeyError: 'a'
            # >>> d['a']
            # []
            # >>> del d['a']
            # >>> #^^ no exception, after first read
            pass

    def __iter__(self):
        config = get_config()
        enabled_plugins = config.setting["enabled_plugins"] if config else []
        for name in self.__dict:
            if name is None or name in enabled_plugins:
                yield from self.__dict[name]


class PluginShared(object):

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
            log.debug('Attribute %r not found for plugin %r', name, self.module_name)
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

    def __init__(self, label=None):
        self.functions = defaultdict(lambda: ExtensionPoint(label=label))

    def register(self, module, item, priority=PluginPriority.NORMAL):
        self.functions[priority].register(module, item)

    def run(self, *args, **kwargs):
        """Execute registered functions with passed parameters honouring priority"""
        for priority, functions in sorted(self.functions.items(),
                                          key=lambda i: i[0],
                                          reverse=True):
            for function in functions:
                function(*args, **kwargs)
