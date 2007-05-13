# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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

import re
from picard.plugin import ExtensionPoint

class ScriptError(Exception): pass
class ParseError(ScriptError): pass
class EndOfFile(ParseError): pass
class SyntaxError(ParseError): pass
class UnknownFunction(ScriptError): pass

class ScriptText(unicode):

    def eval(self, state):
        return self


class ScriptVariable(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<ScriptVariable %%%s%%>' % self.name

    def eval(self, state):
        name = self.name
        if name.startswith(u"_"):
            name = u"~" + name[1:]
        return state.context.get(name, u"")


class ScriptFunction(object):

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return "<ScriptFunction $%s(%r)>" % (self.name, self.args)

    def eval(self, parser):
        try:
            function, eval_args = parser.functions[self.name]
            if eval_args:
                args = [arg.eval(parser) for arg in self.args]
            else:
                args = self.args
            return function(parser, *args)
        except KeyError:
            raise UnknownFunction("Unknown function '%s'" % self.name)


class ScriptExpression(list):

    def eval(self, state):
        result = []
        for item in self:
            result.append(item.eval(state))
        return "".join(result)


def isidentif(ch):
    return ch.isalnum() or ch == '_'


class ScriptParser(object):
    """Tagger script parser.

Grammar:
  text       ::= [^$%] | '\$' | '\%' | '\(' | '\)' | '\,'
  argtext    ::= [^$%(),] | '\$' | '\%' | '\(' | '\)' | '\,'
  identifier ::= [a-zA-Z0-9_]
  variable   ::= '%' identifier '%'
  function   ::= '$' identifier '(' (argument (',' argument)*)? ')'
  expression ::= (variable | function | text)*
  argument   ::= (variable | function | argtext)*
"""

    _function_registry = ExtensionPoint()
    _cache = {}

    def __raise_eof(self):
        raise EndOfFile("Unexpected end of script at position %d, line %d" % (self._x, self._y))

    def __raise_char(self, ch):
        #line = self._text[self._line:].split("\n", 1)[0]
        #cursor = " " * (self._pos - self._line - 1) + "^"
        #raise SyntaxError("Unexpected character '%s' at position %d, line %d\n%s\n%s" % (ch, self._x, self._y, line, cursor))
        raise SyntaxError("Unexpected character '%s' at position %d, line %d" % (ch, self._x, self._y))

    def read(self):
        try:
            ch = self._text[self._pos]
        except IndexError:
            return None
        else:
            self._pos += 1
            self._px = self._x
            self._py = self._y
            if ch == '\n':
                self._line = self._pos
                self._x = 1
                self._y += 1
            else:
                self._x += 1
        return ch

    def unread(self):
        self._pos -= 1
        self._x = self._px
        self._y = self._py

    def parse_arguments(self):
        results = []
        while True:
            result, ch = self.parse_expression(False)
            results.append(result)
            if ch == ')':
                return results

    def parse_function(self):
        start = self._pos
        while True:
            ch = self.read()
            if ch == '(':
                name = self._text[start:self._pos-1]
                if name not in self.functions:
                    raise UnknownFunction("Unknown function '%s'" % name)
                return ScriptFunction(name, self.parse_arguments())
            elif ch is None:
                self.__raise_eof()
            elif not isidentif(ch):
                self.__raise_char(ch)

    def parse_variable(self):
        begin = self._pos
        while True:
            ch = self.read()
            if ch == '%':
                return ScriptVariable(self._text[begin:self._pos-1])
            elif ch is None:
                self.__raise_eof()
            elif not isidentif(ch):
                self.__raise_char(ch)

    def parse_text(self, top):
        text = []
        while True:
            ch = self.read()
            if ch == "\\":
                ch = self.read()
                if ch not in "$%(),\\":
                    self.__raise_char(ch)
                else:
                    text.append(ch)
            elif ch is None:
                break
            elif not top and ch == '(':
                self.__raise_char(ch)
            elif ch in '$%' or (not top and ch in ',)'):
                self.unread()
                break
            else:
                text.append(ch)
        return ScriptText("".join(text))

    def parse_expression(self, top):
        tokens = ScriptExpression()
        while True:
            ch = self.read()
            if ch is None:
                if top:
                    break
                else:
                    self.__raise_eof()
            elif not top and ch in ',)':
                break
            elif ch == '$':
                tokens.append(self.parse_function())
            elif ch == '%':
                tokens.append(self.parse_variable())
            else:
                self.unread()
                tokens.append(self.parse_text(top))
        return (tokens, ch)

    def load_functions(self):
        self.functions = {}
        for name, function, eval_args in ScriptParser._function_registry:
            self.functions[name] = (function, eval_args)

    def parse(self, script, functions=False):
        """Parse the script."""
        self._text = script
        self._pos = 0
        self._px = self._x = 1
        self._py = self._y = 1
        self._line = 0
        if not functions:
            self.load_functions()
        return self.parse_expression(True)[0]

    def eval(self, script, context={}):
        """Parse and evaluate the script."""
        self.context = context
        self.load_functions()
        key = hash(script)
        if key not in ScriptParser._cache:
            ScriptParser._cache[key] = self.parse(script, True)
        return ScriptParser._cache[key].eval(self)


def register_script_function(function, name=None, eval_args=True):
    if name is None:
        name = function.__name__
    ScriptParser._function_registry.register(function.__module__, (name, function, eval_args))


def func_if(parser, *args):
    """If ``if`` is not empty, it returns ``then``, otherwise it returns
       ``else``."""
    if args[0].eval(parser):
        return args[1].eval(parser)
    if len(args) == 3:
        return args[2].eval(parser)
    return ''

def func_if2(parser, *args):
    """Returns first non empty argument."""
    for arg in args:
        arg = arg.eval(parser)
        if arg:
            return arg
    return ''

def func_noop(parser, *args):
    """Does nothing :)"""
    return ''

def func_left(parser, text, length):
    """Returns first ``num`` characters from ``text``."""
    return text[:int(length)]

def func_right(parser, text, length):
    """Returns last ``num`` characters from ``text``."""
    return text[-int(length):]

def func_lower(parser, text):
    """Returns ``text`` in lower case."""
    return text.lower()

def func_upper(parser, text):
    """Returns ``text`` in upper case."""
    return text.upper()

def func_pad(parser, text, length, char):
    return char * (int(length) - len(text)) + text

def func_strip(parser, text):
    return re.sub("\s+", " ", text).strip()

def func_replace(parser, text, old, new):
    return text.replace(old, new)

def func_in(parser, text, needle):
    if needle in text:
        return "1"
    else:
        return ""

def func_rreplace(parser, text, old, new):
    return re.sub(old, new, text)

def func_rsearch(parser, text, pattern):
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return u""

def func_num(parser, text, length):
    format = "%%0%dd" % int(length)
    try:
        value = int(text)
    except ValueError:
        value = 0
    return format % value

def func_unset(parser, name):
    """Unsets the variable ``name``."""
    name = name.replace("_", "~")
    try:
        del parser.context[name]
    except KeyError:
        pass
    return ""

def func_set(parser, name, value):
    """Sets the variable ``name`` to ``value``."""
    name = name.replace("_", "~")
    parser.context[name] = value
    return ""

def func_get(parser, name):
    """Returns the variable ``name`` (equivalent to ``%name%``)."""
    name = name.replace("_", "~")
    return parser.context.get(name, u"")

def func_copy(parser, new, old):
    """Copies content of variable ``old`` to variable ``new``."""
    new = new.replace("_", "~")
    old = old.replace("_", "~")
    parser.context[new] = parser.context.getall(old)[:]
    return ""

def func_trim(parser, text, char=None):
    """Trims all leading and trailing whitespaces from ``text``. The optional
       second parameter specifies the character to trim."""
    if char:
        return text.strip(char)
    else:
        return text.strip()

def func_add(parser, x, y):
    """Add ``y`` to ``x``."""
    return str(int(x) + int(y))

def func_sub(parser, x, y):
    """Substracts ``y`` from ``x``."""
    return str(int(x) - int(y))

def func_div(parser, x, y):
    """Divides ``x`` by ``y``."""
    return str(int(x) / int(y))

def func_mod(parser, x, y):
    """Returns the remainder of ``x`` divided by ``y``."""
    return str(int(x) % int(y))

def func_mul(parser, x, y):
    """Multiplies ``x`` by ``y``."""
    return str(int(x) * int(y))

def func_or(parser, x, y):
    """Returns true, if either ``x`` or ``y`` not empty."""
    if x or y:
        return "1"
    else:
        return ""

def func_and(parser, x, y):
    """Returns true, if both ``x`` and ``y`` are not empty."""
    if x and y:
        return "1"
    else:
        return ""

def func_not(parser, x):
    """Returns true, if ``x`` is empty."""
    if not x:
        return "1"
    else:
        return ""

def func_eq(parser, x, y):
    """Returns true, if ``x`` equals ``y``."""
    if x == y:
        return "1"
    else:
        return ""

def func_ne(parser, x, y):
    """Returns true, if ``x`` not equals ``y``."""
    if x != y:
        return "1"
    else:
        return ""

def func_lt(parser, x, y):
    """Returns true, if ``x`` is lower than ``y``."""
    if x < y:
        return "1"
    else:
        return ""

def func_lte(parser, x, y):
    """Returns true, if ``x`` is lower than or equals ``y``."""
    if x <= y:
        return "1"
    else:
        return ""

def func_gt(parser, x, y):
    """Returns true, if ``x`` is greater than ``y``."""
    if x > y:
        return "1"
    else:
        return ""

def func_gte(parser, x, y):
    """Returns true, if ``x`` is greater than or equals ``y``."""
    if x >= y:
        return "1"
    else:
        return ""

def func_len(parser, text):
    return str(len(text))

register_script_function(func_if, "if", eval_args=False)
register_script_function(func_if2, "if2", eval_args=False)
register_script_function(func_noop, "noop", eval_args=False)
register_script_function(func_left, "left")
register_script_function(func_right, "right")
register_script_function(func_lower, "lower")
register_script_function(func_upper, "upper")
register_script_function(func_pad, "pad")
register_script_function(func_strip, "strip")
register_script_function(func_replace, "replace")
register_script_function(func_rreplace, "rreplace")
register_script_function(func_rsearch, "rsearch")
register_script_function(func_num, "num")
register_script_function(func_unset, "unset")
register_script_function(func_set, "set")
register_script_function(func_get, "get")
register_script_function(func_trim, "trim")
register_script_function(func_add, "add")
register_script_function(func_sub, "sub")
register_script_function(func_div, "div")
register_script_function(func_mod, "mod")
register_script_function(func_mul, "mul")
register_script_function(func_or, "or")
register_script_function(func_and, "and")
register_script_function(func_not, "not")
register_script_function(func_eq, "eq")
register_script_function(func_ne, "ne")
register_script_function(func_lt, "lt")
register_script_function(func_lte, "lte")
register_script_function(func_gt, "gt")
register_script_function(func_gte, "gte")
register_script_function(func_in, "in")
register_script_function(func_copy, "copy")
register_script_function(func_len, "len")
