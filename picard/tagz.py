# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

"""Tagger script parser and evaluator."""

import re
import sys
try:
    from re import Scanner
except ImportError:
    from sre import Scanner
from picard.component import Component, ExtensionPoint, Interface, implements
from picard.api import ITaggerScript

_re_text = r"(?:\\.|[^%$])+"
_re_text2 = r"(?:\\.|[^%$,])+"
_re_args_sep = ","
_re_name = "\w+"
_re_var = r"%" + _re_name + r"%"
_re_func_args = no_parens = r"[^()]"
for i in range(10): # 10 levels must be enough for everybody ;)
   _re_func_args = r"(\(" + _re_func_args + r"\)|" + no_parens + r")*"
_re_func = r"\$" + _re_name + r"\(" + _re_func_args + r"\)"

def func_if(*args):
    if args[0]:
        return args[1]
    if len(args) == 3:
        return args[2]
    return ''


def func_if2(*args):
    for arg in args:
        if arg:
            return arg
    return args[-1]


def func_nop(arg):
    return arg


def func_left(text, length):
    return text[:int(length)]


def func_right(text, length):
    return text[-int(length):]


def func_lower(text):
    return text.lower()


def func_upper(text):
    return text.upper()


def func_pad(text, length, char):
    return char * (int(length) - len(text)) + text


def func_strip(text):
    return re.sub("\s+", " ", text).strip()

def func_replace(text, old, new):
    return text.replace(old, new)

def func_num(text, length):
    return ("%%0%dd" % int(length)) % int(text)

class TagzError(Exception):
    pass


class TagzParseError(TagzError):
    pass


class TagzUnknownFunction(TagzError):
    pass


class ITagzFunctionProvider(Interface):
    pass


class TagzBuiltins(Component):

    implements(ITagzFunctionProvider)

    _functions = {
        "nop": func_nop,
        "if": func_if,
        "if2": func_if2,
        "left": func_left,
        "right": func_right,
        "lower": func_lower,
        "upper": func_upper,
        "pad": func_pad,
        "strip": func_strip,
        "replace": func_replace,
        "num": func_num,
    }

    def get_functions(self):
        return self._functions 


class TagzParser(object):
    """Tagger script implementation similar to Foobar2000's titleformat."""

    def __init__(self, context, functions):
        self.context = context
        self.functions = functions

    def evaluate(self, text):
        """Parse and evaluate the script from ``text``."""
        scanner = Scanner([(_re_text, self.s_text),
                           (_re_var, self.s_variable),
                           (_re_func, self.s_func)])
        res = scanner.scan(text)
        if res[1]:
            raise TagzParseError()
        return "".join(res[0])

    def s_text(self, scanner, string):
        return string

    def s_variable(self, scanner, string):
        try:
            return self.context[string[1:-1].lower()]
        except KeyError:
            return ""

    def s_args_sep(self, scanner, string):
        return "\0"

    def s_func(self, scanner, string):
        args_begin = string.find("(")
        name = string[1:args_begin]
        args = string[args_begin+1:-1]

        scanner = Scanner([(_re_args_sep, self.s_args_sep),
                           (_re_text2, self.s_text),
                           (_re_var, self.s_variable),
                           (_re_func, self.s_func)])
        results, error = scanner.scan(args)
        if error:
            raise TagzParseError(string.rfind(error))

        args = []
        while results:
            j = 1
            for res in results:
                if res == "\0":
                    break
                j += 1
            args.append("".join(results[:j-1]))
            results = results[j:]

        try:
            return self.functions[name](*args)
        except KeyError:
            raise TagzUnknownFunction, "Unknown function $%s" % name


class Tagz(Component):

    implements(ITaggerScript)

    function_providers = ExtensionPoint(ITagzFunctionProvider)

    def __init__(self):
        self.functions = {}
        for prov in self.function_providers:
            self.functions.update(prov.get_functions())

    def evaluate_script(self, text, context={}):
        """Parse and evaluate the script from ``text``."""
        parser = TagzParser(context, self.functions)
        return parser.evaluate(text)


from picard.component import ComponentManager
cmpmgr = ComponentManager()
print Tagz(cmpmgr).evaluate_script(
"""$strip(
    %albumartist%
    $if(%disc%, - CD%disc%, [no disc])
    $replace(%albumartist%,es,AB)
    $num($if2(%discnumber%,1), 5)
)""", {"albumartist": "Test"})

