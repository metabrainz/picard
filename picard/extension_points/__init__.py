# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2014, 2017-2021, 2023, 2025 Philipp Wolfer
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

from picard import log
from picard.config import get_config


PLUGIN_MODULE_PREFIX = "picard.plugins."
PLUGIN_MODULE_PREFIX_LEN = len(PLUGIN_MODULE_PREFIX)

_extension_points = []


class ExtensionPoint:

    def __init__(self, label=None):
        if label is None:
            import uuid
            self.label = uuid.uuid4()
        else:
            self.label = label
        self.__dict = defaultdict(list)
        _extension_points.append(self)

    def register(self, module, item):
        if module.startswith(PLUGIN_MODULE_PREFIX):
            name = module[PLUGIN_MODULE_PREFIX_LEN:]
            log.debug("ExtensionPoint: %s register <- plugin=%r item=%r", self.label, name, item)
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
        enabled_plugins = config.setting['enabled_plugins'] if config else []
        for name in self.__dict:
            if name is None or name in enabled_plugins:
                yield from self.__dict[name]

    def __repr__(self):
        return f"ExtensionPoint(label='{self.label}')"


def unregister_module_extensions(module):
    for ep in _extension_points:
        ep.unregister_module(module)
