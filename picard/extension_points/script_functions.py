# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2012 Lukáš Lalinský
# Copyright (C) 2007 Javier Kohen
# Copyright (C) 2008-2011, 2014-2015, 2018-2021, 2023 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 stephen
# Copyright (C) 2012, 2014, 2017, 2021 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2024 Laurent Monin
# Copyright (C) 2014, 2017, 2021 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Ville Skyttä
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Calvin Walton
# Copyright (C) 2018 virusMac
# Copyright (C) 2020-2023 Bob Swift
# Copyright (C) 2021 Adam James
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
from inspect import (
    FullArgSpec,
    getfullargspec,
)


try:
    from markdown import markdown  # type: ignore[unresolved-import]
except ImportError:
    markdown = None

from picard.extension_points import (
    PLUGIN_MODULE_PREFIX,
    PLUGIN_MODULE_PREFIX_LEN,
)
from picard.i18n import gettext as _
from picard.plugin import ExtensionPoint


ext_point_script_functions = ExtensionPoint(label='script_functions')


Bound = namedtuple('Bound', ['lower', 'upper'])


class FunctionRegistryItem:
    def __init__(self, function, eval_args, argcount, documentation=None, name=None, module=None, signature=None):
        self.function = function
        self.eval_args = eval_args
        self.argcount = argcount
        self.documentation = documentation
        self.name = name
        self.module = module
        self.signature = signature
        self.plugin_id = None
        if module and module.startswith(PLUGIN_MODULE_PREFIX):
            self.plugin_id = module[PLUGIN_MODULE_PREFIX_LEN:]

    def __repr__(self):
        return '{classname}({me.function}, {me.eval_args}, {me.argcount}, {me.signature}, {doc}, {me.name}, {me.module})'.format(
            classname=self.__class__.__name__,
            me=self,
            doc='"""{}"""'.format(self.documentation) if self.documentation else None,
        )

    def _postprocess(self, data, postprocessor):
        if postprocessor is not None:
            data = postprocessor(data, function=self)
        return data

    def markdowndoc(self, postprocessor=None):
        ret = ''
        if self.signature:
            ret = f'`{_(self.signature)}`\n\n'
        if self.documentation:
            ret += _(self.documentation)
        return self._postprocess(ret.strip(), postprocessor)

    def htmldoc(self, postprocessor=None):
        if markdown is not None:
            ret = markdown(self.markdowndoc())
        else:
            ret = ''
        return self._postprocess(ret, postprocessor)


def register_script_function(
    function, name=None, eval_args=True, check_argcount=True, documentation=None, signature=None
):
    """Registers a script function. If ``name`` is ``None``,
    ``function.__name__`` will be used.
    If ``eval_args`` is ``False``, the arguments will not be evaluated before being
    passed to ``function``.
    If ``check_argcount`` is ``False`` the number of arguments passed to the
    function will not be verified.
    If ``documentation`` is ``None``, ``function.__doc__`` will be used."""

    argspec = getfullargspec(function)

    required_kwonlyargs = len(argspec.kwonlyargs)
    if argspec.kwonlydefaults is not None:
        required_kwonlyargs -= len(argspec.kwonlydefaults.keys())
    if required_kwonlyargs:
        raise TypeError("Functions with required keyword-only parameters are not supported")

    args = len(argspec.args) - 1  # -1 for the parser
    varargs = argspec.varargs is not None
    defaults = len(argspec.defaults) if argspec.defaults else 0

    argcount = Bound(args - defaults, args if not varargs else None)

    if not documentation:
        documentation = function.__doc__

    if name is None:
        name = function.__name__

    if not signature:
        signature = generate_function_signature(name, argspec)

    ext_point_script_functions.register(
        function.__module__,
        (
            name,
            FunctionRegistryItem(
                function,
                eval_args,
                argcount if argcount and check_argcount else False,
                documentation=documentation,
                name=name,
                module=function.__module__,
                signature=signature,
            ),
        ),
    )


def script_function(name=None, eval_args=True, check_argcount=True, prefix='func_', documentation=None, signature=None):
    """Decorator helper to register script functions

    It calls ``register_script_function()`` and share same arguments
    Extra optional arguments:
        ``prefix``: define the prefix to be removed from defined function to name script function
                    By default, ``func_foo`` will create ``foo`` script function

    Example:
        @script_function(eval_args=False)
        def func_myscriptfunc():
            ...
    """

    def script_function_decorator(func):
        fname = func.__name__
        if name is None and prefix and fname.startswith(prefix):
            sname = fname[len(prefix) :]
        else:
            sname = name
        register_script_function(
            func,
            name=sname,
            eval_args=eval_args,
            check_argcount=check_argcount,
            documentation=documentation,
            signature=signature,
        )
        return func

    return script_function_decorator


class ParamSpec:
    class EmptyDefault:
        """Represents an empty script function parameter"""

        pass

    def __init__(self):
        self._params = []

    def append(self, name, default=None):
        self._params.append((name, default))

    def __str__(self):
        spec = ''

        default_depth = 0
        for i, (arg, default) in enumerate(self._params):
            if default:
                default_depth += 1
                spec += '['
            if i > 0:
                spec += ','
            spec += arg
            if default and not isinstance(default, ParamSpec.EmptyDefault):
                spec += f'={str(default)}'

        spec += ']' * default_depth
        return spec


def generate_function_signature(name: str, argspec: FullArgSpec) -> str:
    """Takes a callable and generates a description of the script function signature"""
    params = ParamSpec()
    if argspec.args:
        args = argspec.args[1:]  # ignore the first argument, it's the ScriptParser
        defaults = argspec.defaults
        default_count = len(defaults) if defaults else 0
        for arg in args[:-default_count] if default_count else args:
            params.append(arg)
        if defaults:
            for arg, default in zip(args[-default_count:], defaults, strict=True):
                params.append(arg, default or ParamSpec.EmptyDefault())
    if argspec.varargs:
        params.append('…')

    return f"${name}({str(params)})"
