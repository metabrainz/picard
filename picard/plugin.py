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
# Copyright (C) 2017 Frederik "Freso" S. Olesen
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

from collections import namedtuple
from functools import partial

from picard.config import (
    Option,
    get_config,
)
from picard.extension_points import (
    PLUGIN_MODULE_PREFIX,
    ExtensionPoint,
)
from picard.i18n import _


PluginInformation = namedtuple(
    'PluginInformation',
    (
        'key',
        'plugin_name',
        'plugin_description',
        'processor',
        'function_name',
        'function_description',
        'priority',
    ),
)


class PluginFunctions:
    """
    Store ExtensionPoint in a defaultdict with priority as key
    run() method will execute entries with higher priority value first
    """

    def __init__(self, label: str = None):
        self.functions = ExtensionPoint(label=label)
        self.priorities = {}
        self.config_priorities = {}
        self.processor_type = label.split('_')[0]
        Option.add_if_missing('setting', 'plugins3_exec_order', dict())

    def make_exec_order_key(self, function):
        """Make the plugin key based on the module name"""
        key = f"{function.__module__}:{self.processor_type}:{function.__name__}"
        return key

    def get_priority(self, function):
        key = self.make_exec_order_key(function)
        if key in self.config_priorities:
            return self.config_priorities[key]
        elif key in self.priorities:
            return self.priorities[key]
        return 0  # Default priority

    def register(self, module, item, priority=0):
        key = self.make_exec_order_key(item)
        self.priorities[key] = priority
        self.functions.register(module, item)
        if key.startswith(PLUGIN_MODULE_PREFIX):
            config = get_config()
            config_priorities = config.setting['plugins3_exec_order']
            config_priorities[key] = config_priorities[key] if key in config_priorities else priority

    def get_plugin_function_information(self, order_dict: dict = None):
        """Returns registered functions for manually setting execution order"""
        if order_dict is None:
            config = get_config()
            self.config_priorities = dict(config.setting['plugins3_exec_order'])
        else:
            self.config_priorities = dict(order_dict)

        for function in sorted(self.functions, key=lambda i: self.get_priority(i), reverse=True):
            key = self.make_exec_order_key(function)
            if not key.startswith(PLUGIN_MODULE_PREFIX):
                continue
            if isinstance(function, partial):
                api = function.args[0]
                plugin_name = api.manifest.name()
                plugin_description = api.manifest.description() or _("No plugin description available.")
            else:
                plugin_name = _("Unknown Plugin")
                plugin_description = plugin_name
            if self.processor_type == 'album':
                processor = _("Album")
            elif self.processor_type == 'track':
                processor = _("Track")
            else:
                processor = _("Unknown")
            yield PluginInformation(
                key=key,
                plugin_name=plugin_name,
                plugin_description=plugin_description,
                processor=processor,
                function_name=function.__name__,
                function_description=getattr(function, '__doc__', None) or _("No function description available."),
                priority=self.get_priority(function),
            )

    def _get_functions(self):
        """Returns registered functions by order of priority (highest first) and registration"""
        config = get_config()
        self.config_priorities = dict(config.setting['plugins3_exec_order'])
        yield from sorted(self.functions, key=lambda i: self.get_priority(i), reverse=True)

    def run(self, *args, **kwargs):
        """Execute registered functions with passed parameters honouring priority"""
        for function in self._get_functions():
            function(*args, **kwargs)
