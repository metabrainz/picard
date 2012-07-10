# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2007 Javier Kohen
# Copyright (C) 2008 Philipp Wolfer
#
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
from picard.metadata import Metadata
from picard.metadata import MULTI_VALUED_JOINER
from picard.plugin import ExtensionPoint
from inspect import getargspec

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

    def __init__(self, name, args, parser):
        try:
            expected_args = parser.functions[name][2]
            if expected_args and (len(args) not in expected_args):
                raise ScriptError(
                "Wrong number of arguments for $%s: Expected %s, got %i at position %i, line %i"
                    % (name,
                       str(expected_args[0])
                            if len(expected_args) == 1
                            else
                                "%i - %i" % (min(expected_args), max(expected_args)),
                       len(args),
                       parser._x,
                       parser._y))
        except KeyError:
            raise UnknownFunction("Unknown function '%s'" % name)

        self.name = name
        self.args = args

    def __repr__(self):
        return "<ScriptFunction $%s(%r)>" % (self.name, self.args)

    def eval(self, parser):
        function, eval_args, num_args = parser.functions[self.name]
        if eval_args:
            args = [arg.eval(parser) for arg in self.args]
        else:
            args = self.args
        return function(parser, *args)


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
                return ScriptFunction(name, self.parse_arguments(), self)
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
            elif not isidentif(ch) and ch != ':':
                self.__raise_char(ch)

    def parse_text(self, top):
        text = []
        while True:
            ch = self.read()
            if ch == "\\":
                ch = self.read()
                if ch == 'n':
                    text.append('\n')
                elif ch == 't':
                    text.append('\t')
                elif ch not in "$%(),\\":
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
        for name, function, eval_args, num_args in ScriptParser._function_registry:
            self.functions[name] = (function, eval_args, num_args)

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

    def eval(self, script, context=None, file=None):
        """Parse and evaluate the script."""
        self.context = context if context is not None else Metadata()
        self.file = file
        self.load_functions()
        key = hash(script)
        if key not in ScriptParser._cache:
            ScriptParser._cache[key] = self.parse(script, True)
        return ScriptParser._cache[key].eval(self)


def register_script_function(function, name=None, eval_args=True,
        check_argcount=True):
    """Registers a script function. If ``name`` is ``None``,
    ``function.__name__`` will be used.
    If ``eval_args`` is ``False``, the arguments will not be evaluated before being
    passed to ``function``.
    If ``check_argcount`` is ``False`` the number of arguments passed to the
    function will not be verified."""

    argspec = getargspec(function)
    argcount = (len(argspec[0]) - 1,) # -1 for the parser

    if argspec[3] is not None:
        argcount = range(argcount[0] - len(argspec[3]), argcount[0] + 1)

    if name is None:
        name = function.__name__
    ScriptParser._function_registry.register(function.__module__,
        (name, function, eval_args,
            argcount if argcount and check_argcount else False)
        )

def func_if(parser, _if, _then, _else=None):
    """If ``if`` is not empty, it returns ``then``, otherwise it returns ``else``."""
    if _if.eval(parser):
        return _then.eval(parser)
    elif _else:
        return _else.eval(parser)
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

def func_inmulti(parser, text, value, separator=MULTI_VALUED_JOINER):
    """Splits ``text`` by ``separator``, and returns true if the resulting list contains ``value``."""
    return func_in(parser, text.split(separator) if separator else [text], value)

def func_rreplace(parser, text, old, new):
    return re.sub(old, new, text)

def func_rsearch(parser, text, pattern):
    match = re.search(pattern, text)
    if match:
        try:
            return match.group(1)
        except IndexError:
            return match.group(0)
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
    if name.startswith("_"):
        name = "~" + name[1:]
    try:
        del parser.context[name]
    except KeyError:
        pass
    return ""

def func_set(parser, name, value):
    """Sets the variable ``name`` to ``value``."""
    if value:
        if name.startswith("_"):
            name = "~" + name[1:]
        parser.context[name] = value
    else:
        func_unset(parser, name)
    return ""

def func_setmulti(parser, name, value, separator=MULTI_VALUED_JOINER):
    """Sets the variable ``name`` to ``value`` as a list; splitting by the passed string, or "; " otherwise."""
    return func_set(parser, name, value.split(separator) if value and separator else value)

def func_get(parser, name):
    """Returns the variable ``name`` (equivalent to ``%name%``)."""
    if name.startswith("_"):
        name = "~" + name[1:]
    return parser.context.get(name, u"")

def func_copy(parser, new, old):
    """Copies content of variable ``old`` to variable ``new``."""
    if new.startswith("_"):
        new = "~" + new[1:]
    if old.startswith("_"):
        old = "~" + old[1:]
    parser.context[new] = parser.context.getall(old)[:]
    return ""

def func_copymerge(parser, new, old):
    """Copies content of variable ``old`` and appends it into variable ``new``, removing duplicates. This is normally
    used to merge a multi-valued variable into another, existing multi-valued variable."""
    if new.startswith("_"):
        new = "~" + new[1:]
    if old.startswith("_"):
        old = "~" + old[1:]
    newvals = parser.context.getall(new)
    oldvals = parser.context.getall(old)
    parser.context[new] = newvals + list(set(oldvals) - set(newvals))
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
    try:
        return str(int(x) + int(y))
    except ValueError:
        return ""

def func_sub(parser, x, y):
    """Substracts ``y`` from ``x``."""
    try:
        return str(int(x) - int(y))
    except ValueError:
        return ""

def func_div(parser, x, y):
    """Divides ``x`` by ``y``."""
    try:
        return str(int(x) / int(y))
    except ValueError:
        return ""

def func_mod(parser, x, y):
    """Returns the remainder of ``x`` divided by ``y``."""
    try:
        return str(int(x) % int(y))
    except ValueError:
        return ""

def func_mul(parser, x, y):
    """Multiplies ``x`` by ``y``."""
    try:
        return str(int(x) * int(y))
    except ValueError:
        return ""

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
    try:
        if int(x) < int(y):
            return "1"
    except ValueError:
        pass
    return ""

def func_lte(parser, x, y):
    """Returns true, if ``x`` is lower than or equals ``y``."""
    try:
        if int(x) <= int(y):
            return "1"
    except ValueError:
        pass
    return ""

def func_gt(parser, x, y):
    """Returns true, if ``x`` is greater than ``y``."""
    try:
        if int(x) > int(y):
            return "1"
    except ValueError:
        pass
    return ""

def func_gte(parser, x, y):
    """Returns true, if ``x`` is greater than or equals ``y``."""
    try:
        if int(x) >= int(y):
            return "1"
    except ValueError:
        pass
    return ""

def func_len(parser, text):
    return str(len(text))

def func_performer(parser, pattern="", join=", "):
    values = []
    for name, value in parser.context.items():
        if name.startswith("performer:") and pattern in name:
            values.append(value)
    return join.join(values)

def func_matchedtracks(parser, arg):
    if parser.file:
        if parser.file.parent:
            return str(parser.file.parent.album.get_num_matched_tracks())
    return "0"

def func_firstalphachar(parser, text, nonalpha="#"):
    if len(text) == 0:
        return nonalpha
    firstchar = text[0]
    if firstchar.isalpha():
        return firstchar.upper()
    else:
        return nonalpha

def func_initials(parser, text):
    return "".join(a[:1] for a in text.split(" ") if a[:1].isalpha())

def func_firstwords(parser, text, length):
    try:
        length = int(length)
    except ValueError, e:
        length = 0
    if len(text) <= length:
        return text
    else:
        if text[length] == ' ':
            return text[:length]
        return text[:length].rsplit(' ', 1)[0]

def func_truncate(parser, text, length):
    try:
        length = int(length)
    except ValueError, e:
        length = None
    return text[:length].rstrip()

register_script_function(func_if, "if", eval_args=False)
register_script_function(func_if2, "if2", eval_args=False, check_argcount=False)
register_script_function(func_noop, "noop", eval_args=False, check_argcount=False)
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
register_script_function(func_setmulti, "setmulti")
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
register_script_function(func_inmulti, "inmulti")
register_script_function(func_copy, "copy")
register_script_function(func_copymerge, "copymerge")
register_script_function(func_len, "len")
register_script_function(func_performer, "performer")
register_script_function(func_matchedtracks, "matchedtracks")
register_script_function(func_firstalphachar, "firstalphachar")
register_script_function(func_initials, "initials")
register_script_function(func_firstwords, "firstwords")
register_script_function(func_truncate, "truncate")
