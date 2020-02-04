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

from collections import namedtuple
import datetime
from functools import reduce
from inspect import getfullargspec
import operator
import re
import unicodedata

from picard import config
from picard.metadata import (
    MULTI_VALUED_JOINER,
    Metadata,
)
from picard.plugin import ExtensionPoint
from picard.util import uniqify


class ScriptError(Exception):
    pass


class ScriptParseError(ScriptError):
    pass


class ScriptEndOfFile(ScriptParseError):
    pass


class ScriptSyntaxError(ScriptParseError):
    pass


class ScriptUnknownFunction(ScriptError):
    pass


class ScriptText(str):

    def eval(self, state):
        return self


def normalize_tagname(name):
    if name.startswith('_'):
        return "~" + name[1:]
    return name


class ScriptVariable(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<ScriptVariable %%%s%%>' % self.name

    def eval(self, state):
        return state.context.get(normalize_tagname(self.name), "")


FunctionRegistryItem = namedtuple("FunctionRegistryItem",
                                  ["function", "eval_args",
                                   "argcount"])
Bound = namedtuple("Bound", ["lower", "upper"])


class ScriptFunction(object):

    def __init__(self, name, args, parser):
        try:
            argnum_bound = parser.functions[name].argcount
            argcount = len(args)
            if argnum_bound:
                too_few_args = argcount < argnum_bound.lower
                if argnum_bound.upper is not None:
                    if argnum_bound.lower == argnum_bound.upper:
                        expected = "exactly %i" % argnum_bound.lower
                    else:
                        expected = "between %i and %i" % (argnum_bound.lower, argnum_bound.upper)
                    too_many_args = argcount > argnum_bound.upper
                else:
                    expected = "at least %i" % argnum_bound.lower
                    too_many_args = False

                if too_few_args or too_many_args:
                    raise ScriptError(
                        "Wrong number of arguments for $%s: Expected %s, got %i at position %i, line %i"
                        % (name, expected, argcount, parser._x, parser._y)
                    )
        except KeyError:
            raise ScriptUnknownFunction("Unknown function '%s'" % name)

        self.name = name
        self.args = args

    def __repr__(self):
        return "<ScriptFunction $%s(%r)>" % (self.name, self.args)

    def eval(self, parser):
        try:
            function, eval_args, num_args = parser.functions[self.name]
        except KeyError:
            raise ScriptUnknownFunction("Unknown function '%s'" % self.name)

        if eval_args:
            args = [arg.eval(parser) for arg in self.args]
        else:
            args = self.args
        return function(parser, *args)


class ScriptExpression(list):

    def eval(self, state):
        return "".join([item.eval(state) for item in self])


def isidentif(ch):
    return ch.isalnum() or ch == '_'


class ScriptParser(object):

    r"""Tagger script parser.

Grammar:
  text       ::= [^$%] | '\$' | '\%' | '\(' | '\)' | '\,'
  argtext    ::= [^$%(),] | '\$' | '\%' | '\(' | '\)' | '\,'
  identifier ::= [a-zA-Z0-9_]
  variable   ::= '%' identifier '%'
  function   ::= '$' identifier '(' (argument (',' argument)*)? ')'
  expression ::= (variable | function | text)*
  argument   ::= (variable | function | argtext)*
"""

    _function_registry = ExtensionPoint(label='function_registry')
    _cache = {}

    def __raise_eof(self):
        raise ScriptEndOfFile("Unexpected end of script at position %d, line %d" % (self._x, self._y))

    def __raise_char(self, ch):
        #line = self._text[self._line:].split("\n", 1)[0]
        #cursor = " " * (self._pos - self._line - 1) + "^"
        #raise ScriptSyntaxError("Unexpected character '%s' at position %d, line %d\n%s\n%s" % (ch, self._x, self._y, line, cursor))
        raise ScriptSyntaxError("Unexpected character '%s' at position %d, line %d" % (ch, self._x, self._y))

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
                # Only an empty expression as first argument
                # is the same as no argument given.
                if len(results) == 1 and results[0] == []:
                    return []
                return results

    def parse_function(self):
        start = self._pos
        while True:
            ch = self.read()
            if ch == '(':
                name = self._text[start:self._pos-1]
                if name not in self.functions:
                    raise ScriptUnknownFunction("Unknown function '%s'" % name)
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
        for name, item in ScriptParser._function_registry:
            self.functions[name] = item

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


def enabled_tagger_scripts_texts():
    """Returns an iterator over the enabled tagger scripts.
    For each script, you'll get a tuple consisting of the script name and text"""
    if not config.setting["enable_tagger_scripts"]:
        return []
    return [(s_name, s_text) for _s_pos, s_name, s_enabled, s_text in config.setting["list_of_scripts"] if s_enabled and s_text]


def register_script_function(function, name=None, eval_args=True,
                             check_argcount=True):
    """Registers a script function. If ``name`` is ``None``,
    ``function.__name__`` will be used.
    If ``eval_args`` is ``False``, the arguments will not be evaluated before being
    passed to ``function``.
    If ``check_argcount`` is ``False`` the number of arguments passed to the
    function will not be verified."""

    args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = getfullargspec(function)

    required_kwonlyargs = len(kwonlyargs)
    if kwonlydefaults is not None:
        required_kwonlyargs -= len(kwonlydefaults.keys())
    if required_kwonlyargs:
        raise TypeError("Functions with required keyword-only parameters are not supported")

    args = len(args) - 1  # -1 for the parser
    varargs = varargs is not None
    defaults = len(defaults) if defaults else 0

    argcount = Bound(args - defaults, args if not varargs else None)

    if name is None:
        name = function.__name__
    ScriptParser._function_registry.register(function.__module__,
        (name, FunctionRegistryItem(
            function, eval_args,
            argcount if argcount and check_argcount else False)
         )
    )


def script_function(name=None, eval_args=True, check_argcount=True, prefix='func_'):
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
            sname = fname[len(prefix):]
        else:
            sname = name
        register_script_function(func, name=sname, eval_args=eval_args, check_argcount=check_argcount)
        return func
    return script_function_decorator


def _compute_int(operation, *args):
    return str(reduce(operation, map(int, args)))


def _compute_logic(operation, *args):
    return operation(args)


def _get_multi_values(parser, multi, separator):
    if isinstance(separator, ScriptExpression):
        separator = separator.eval(parser)

    if separator == MULTI_VALUED_JOINER:
        # Convert ScriptExpression containing only a single variable into variable
        if (isinstance(multi, ScriptExpression)
            and len(multi) == 1
            and isinstance(multi[0], ScriptVariable)):
            multi = multi[0]

        # If a variable, return multi-values
        if isinstance(multi, ScriptVariable):
            return parser.context.getall(normalize_tagname(multi.name))

    # Fall-back to converting to a string and splitting if haystack is an expression
    # or user has overridden the separator character.
    multi = multi.eval(parser)
    return multi.split(separator) if separator else [multi]


@script_function(eval_args=False)
def func_if(parser, _if, _then, _else=None):
    """If ``if`` is not empty, it returns ``then``, otherwise it returns ``else``."""
    if _if.eval(parser):
        return _then.eval(parser)
    elif _else:
        return _else.eval(parser)
    return ''


@script_function(eval_args=False)
def func_if2(parser, *args):
    """Returns first non empty argument."""
    for arg in args:
        arg = arg.eval(parser)
        if arg:
            return arg
    return ''


@script_function(eval_args=False)
def func_noop(parser, *args):
    """Does nothing :)"""
    return ''


@script_function()
def func_left(parser, text, length):
    """Returns first ``num`` characters from ``text``."""
    try:
        return text[:int(length)]
    except ValueError:
        return ""


@script_function()
def func_right(parser, text, length):
    """Returns last ``num`` characters from ``text``."""
    try:
        return text[-int(length):]
    except ValueError:
        return ""


@script_function()
def func_lower(parser, text):
    """Returns ``text`` in lower case."""
    return text.lower()


@script_function()
def func_upper(parser, text):
    """Returns ``text`` in upper case."""
    return text.upper()


@script_function()
def func_pad(parser, text, length, char):
    try:
        return char * (int(length) - len(text)) + text
    except ValueError:
        return ""


@script_function()
def func_strip(parser, text):
    return re.sub(r"\s+", " ", text).strip()


@script_function()
def func_replace(parser, text, old, new):
    return text.replace(old, new)


@script_function()
def func_in(parser, text, needle):
    if needle in text:
        return "1"
    else:
        return ""


@script_function(eval_args=False)
def func_inmulti(parser, haystack, needle, separator=MULTI_VALUED_JOINER):
    """Searches for ``needle`` in ``haystack``, supporting a list variable for
       ``haystack``. If a string is used instead, then a ``separator`` can be
       used to split it. In both cases, it returns true if the resulting list
       contains exactly ``needle`` as a member."""

    needle = needle.eval(parser)
    return func_in(parser, _get_multi_values(parser, haystack, separator), needle)


@script_function()
def func_rreplace(parser, text, old, new):
    try:
        return re.sub(old, new, text)
    except re.error:
        return text


@script_function()
def func_rsearch(parser, text, pattern):
    try:
        match = re.search(pattern, text)
    except re.error:
        return ""
    if match:
        try:
            return match.group(1)
        except IndexError:
            return match.group(0)
    return ""


@script_function()
def func_num(parser, text, length):
    try:
        format_ = "%%0%dd" % min(int(length), 20)
    except ValueError:
        return ""
    try:
        value = int(text)
    except ValueError:
        value = 0
    return format_ % value


@script_function()
def func_unset(parser, name):
    """Unsets the variable ``name``."""
    name = normalize_tagname(name)
    # Allow wild-card unset for certain keys
    if name in ('performer:*', 'comment:*', 'lyrics:*'):
        name = name[:-1]
        for key in list(parser.context.keys()):
            if key.startswith(name):
                parser.context.unset(key)
        return ""
    try:
        parser.context.unset(name)
    except KeyError:
        pass
    return ""


@script_function()
def func_delete(parser, name):
    """
    Deletes the variable ``name``.
    This will unset the tag with the given name and also mark the tag for
    deletion on save.
    """
    parser.context.delete(normalize_tagname(name))
    return ""


@script_function()
def func_set(parser, name, value):
    """Sets the variable ``name`` to ``value``."""
    if value:
        parser.context[normalize_tagname(name)] = value
    else:
        func_unset(parser, name)
    return ""


@script_function()
def func_setmulti(parser, name, value, separator=MULTI_VALUED_JOINER):
    """Sets the variable ``name`` to ``value`` as a list; splitting by the passed string, or "; " otherwise."""
    return func_set(parser, name, value.split(separator) if value and separator else value)


@script_function()
def func_get(parser, name):
    """Returns the variable ``name`` (equivalent to ``%name%``)."""
    return parser.context.get(normalize_tagname(name), "")


@script_function()
def func_copy(parser, new, old):
    """Copies content of variable ``old`` to variable ``new``."""
    new = normalize_tagname(new)
    old = normalize_tagname(old)
    parser.context[new] = parser.context.getall(old)[:]
    return ""


@script_function()
def func_copymerge(parser, new, old):
    """Copies content of variable ``old`` and appends it into variable ``new``, removing duplicates. This is normally
    used to merge a multi-valued variable into another, existing multi-valued variable."""
    new = normalize_tagname(new)
    old = normalize_tagname(old)
    newvals = parser.context.getall(new)
    oldvals = parser.context.getall(old)
    parser.context[new] = uniqify(newvals + oldvals)
    return ""


@script_function()
def func_trim(parser, text, char=None):
    """Trims all leading and trailing whitespaces from ``text``. The optional
       second parameter specifies the character to trim."""
    if char:
        return text.strip(char)
    else:
        return text.strip()


@script_function()
def func_add(parser, x, y, *args):
    """Adds ``y`` to ``x``.
       Can be used with an arbitrary number of arguments.
       Eg: $add(x, y, z) = ((x + y) + z)
    """
    try:
        return _compute_int(operator.add, x, y, *args)
    except ValueError:
        return ""


@script_function()
def func_sub(parser, x, y, *args):
    """Subtracts ``y`` from ``x``.
       Can be used with an arbitrary number of arguments.
       Eg: $sub(x, y, z) = ((x - y) - z)
    """
    try:
        return _compute_int(operator.sub, x, y, *args)
    except ValueError:
        return ""


@script_function()
def func_div(parser, x, y, *args):
    """Divides ``x`` by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $div(x, y, z) = ((x / y) / z)
    """
    try:
        return _compute_int(operator.floordiv, x, y, *args)
    except ValueError:
        return ""


@script_function()
def func_mod(parser, x, y, *args):
    """Returns the remainder of ``x`` divided by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $mod(x, y, z) = ((x % y) % z)
    """
    try:
        return _compute_int(operator.mod, x, y, *args)
    except ValueError:
        return ""


@script_function()
def func_mul(parser, x, y, *args):
    """Multiplies ``x`` by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $mul(x, y, z) = ((x * y) * z)
    """
    try:
        return _compute_int(operator.mul, x, y, *args)
    except ValueError:
        return ""


@script_function()
def func_or(parser, x, y, *args):
    """Returns true, if either ``x`` or ``y`` not empty.
       Can be used with an arbitrary number of arguments. The result is
       true if ANY of the arguments is not empty.
    """
    if _compute_logic(any, x, y, *args):
        return "1"
    else:
        return ""


@script_function()
def func_and(parser, x, y, *args):
    """Returns true, if both ``x`` and ``y`` are not empty.
       Can be used with an arbitrary number of arguments. The result is
       true if ALL of the arguments are not empty.
    """
    if _compute_logic(all, x, y, *args):
        return "1"
    else:
        return ""


@script_function()
def func_not(parser, x):
    """Returns true, if ``x`` is empty."""
    if not x:
        return "1"
    else:
        return ""


@script_function()
def func_eq(parser, x, y):
    """Returns true, if ``x`` equals ``y``."""
    if x == y:
        return "1"
    else:
        return ""


@script_function()
def func_ne(parser, x, y):
    """Returns true, if ``x`` not equals ``y``."""
    if x != y:
        return "1"
    else:
        return ""


@script_function()
def func_lt(parser, x, y):
    """Returns true, if ``x`` is lower than ``y``."""
    try:
        if int(x) < int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function()
def func_lte(parser, x, y):
    """Returns true, if ``x`` is lower than or equals ``y``."""
    try:
        if int(x) <= int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function()
def func_gt(parser, x, y):
    """Returns true, if ``x`` is greater than ``y``."""
    try:
        if int(x) > int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function()
def func_gte(parser, x, y):
    """Returns true, if ``x`` is greater than or equals ``y``."""
    try:
        if int(x) >= int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function()
def func_len(parser, text=""):
    return str(len(text))


@script_function(eval_args=False)
def func_lenmulti(parser, multi, separator=MULTI_VALUED_JOINER):
    return func_len(parser, _get_multi_values(parser, multi, separator))


@script_function()
def func_performer(parser, pattern="", join=", "):
    values = []
    for name, value in parser.context.items():
        if name.startswith("performer:") and pattern in name:
            values.append(value)
    return join.join(values)


@script_function(eval_args=False)
def func_matchedtracks(parser, *args):
    # only works in file naming scripts, always returns zero in tagging scripts
    file = parser.file
    if file and file.parent and hasattr(file.parent, 'album'):
        return str(parser.file.parent.album.get_num_matched_tracks())
    return "0"


@script_function()
def func_is_complete(parser):
    # only works in file naming scripts, always returns zero in tagging scripts
    file = parser.file
    if (file and file.parent and hasattr(file.parent, 'album')
            and file.parent.album.is_complete()):
        return "1"
    return ""


@script_function()
def func_firstalphachar(parser, text="", nonalpha="#"):
    if len(text) == 0:
        return nonalpha
    firstchar = text[0]
    if firstchar.isalpha():
        return firstchar.upper()
    else:
        return nonalpha


@script_function()
def func_initials(parser, text=""):
    return "".join(a[:1] for a in text.split(" ") if a[:1].isalpha())


@script_function()
def func_firstwords(parser, text, length):
    try:
        length = int(length)
    except ValueError:
        length = 0
    if len(text) <= length:
        return text
    else:
        if text[length] == ' ':
            return text[:length]
        return text[:length].rsplit(' ', 1)[0]


@script_function()
def func_startswith(parser, text, prefix):
    if text.startswith(prefix):
        return "1"
    return ""


@script_function()
def func_endswith(parser, text, suffix):
    if text.endswith(suffix):
        return "1"
    return ""


@script_function()
def func_truncate(parser, text, length):
    try:
        length = int(length)
    except ValueError:
        length = None
    return text[:length].rstrip()


@script_function(check_argcount=False)
def func_swapprefix(parser, text, *prefixes):
    """
    Moves the specified prefixes to the end of text.
    If no prefix is specified 'A' and 'The' are taken as default.
    """
    # Inspired by the swapprefix plugin by Philipp Wolfer.

    text, prefix = _delete_prefix(parser, text, *prefixes)
    if prefix != '':
        return text + ', ' + prefix
    return text


@script_function(check_argcount=False)
def func_delprefix(parser, text, *prefixes):
    """
    Deletes the specified prefixes.
    If no prefix is specified 'A' and 'The' are taken as default.
    """
    # Inspired by the swapprefix plugin by Philipp Wolfer.

    return _delete_prefix(parser, text, *prefixes)[0]


def _delete_prefix(parser, text, *prefixes):
    """
    Worker function to deletes the specified prefixes.
    Returns remaining string and deleted part separately.
    If no prefix is specified 'A' and 'The' used.
    """
    # Inspired by the swapprefix plugin by Philipp Wolfer.

    if not prefixes:
        prefixes = ('A', 'The')
    text = text.strip()
    rx = '(' + r'\s+)|('.join(map(re.escape, prefixes)) + r'\s+)'
    match = re.match(rx, text)
    if match:
        pref = match.group()
        return text[len(pref):], pref.strip()
    return text, ''


@script_function(check_argcount=False)
def func_eq_any(parser, x, *args):
    """
    Return True if one string matches any of one or more other strings.
    $eq_any(a,b,c ...) is functionally equivalent to $or($eq(a,b),$eq(a,c) ...)
    Example: $if($eq_any(%artist%,foo,bar,baz),$set(engineer,test))
    """
    # Inspired by the eq2 plugin by Brian Schweitzer.
    return '1' if x in args else ''


@script_function(check_argcount=False)
def func_ne_all(parser, x, *args):
    """
    Return True if one string doesn't match all of one or more other strings.
    $ne_all(a,b,c ...) is functionally equivalent to $and($ne(a,b),$ne(a,c) ...)
    Example: $if($ne_all(%artist%,foo,bar,baz),$set(engineer,test))
    """
    # Inspired by the ne2 plugin by Brian Schweitzer.
    return '1' if x not in args else ''


@script_function(check_argcount=False)
def func_eq_all(parser, x, *args):
    """
    Return True if all string are equal.
    $eq_all(a,b,c ...) is functionally equivalent to $and($eq(a,b),$eq(a,c) ...)
    Example: $if($eq_all(%albumartist%,%artist%,Justin Bieber),$set(engineer,Meat Loaf))
    """
    for i in args:
        if x != i:
            return ''
    return '1'


@script_function(check_argcount=False)
def func_ne_any(parser, x, *args):
    """
    Return True if all strings are not equal.
    $ne_any(a,b,c ...) is functionally equivalent to $or($ne(a,b),$ne(a,c) ...)
    Example: $if($ne_any(%albumartist%,%trackartist%,%composer%),$set(lyricist,%composer%))
    """
    return func_not(parser, func_eq_all(parser, x, *args))


@script_function()
def func_title(parser, text):
    # GPL 2.0 licensed code by Javier Kohen, Sambhav Kothari
    # from https://github.com/metabrainz/picard-plugins/blob/2.0/plugins/titlecase/titlecase.py
    """
    Title-case a text - capitalizes first letter of every word
    like: from "Lost in the Supermarket" to "Lost In The Supermarket"
    Example: $set(album,$title(%album%))
    """
    if not text:
        return ""
    capitalized = text[0].capitalize()
    capital = False
    for i in range(1, len(text)):
        t = text[i]
        if t in "’'" and text[i-1].isalpha():
            capital = False
        elif iswbound(t):
            capital = True
        elif capital and t.isalpha():
            capital = False
            t = t.capitalize()
        else:
            capital = False
        capitalized += t
    return capitalized


def iswbound(char):
    # GPL 2.0 licensed code by Javier Kohen, Sambhav Kothari
    # from https://github.com/metabrainz/picard-plugins/blob/2.0/plugins/titlecase/titlecase.py
    """ Checks whether the given character is a word boundary """
    category = unicodedata.category(char)
    return "Zs" == category or "Sk" == category or "P" == category[0]


@script_function()
def func_is_audio(parser):
    """Returns true, if the file processed is an audio file."""
    if func_is_video(parser) == "1":
        return ""
    else:
        return "1"


@script_function()
def func_is_video(parser):
    """Returns true, if the file processed is a video file."""
    if parser.context['~video'] and parser.context['~video'] != '0':
        return "1"
    else:
        return ""


@script_function()
def func_find(parser, haystack, needle):
    """Find the location of the first occurrence of one string within another.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        haystack: The string to search.
        needle: The substring to find.

    Returns:
        The zero-based index of the first occurrance of needle in haystack, or -1 if needle was not found.
    """
    return str(haystack.find(needle))


@script_function()
def func_reverse(parser, text):
    """Returns 'text' in reverse order.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        text: String to be processed.

    Returns:
        Text in reverse order.
    """
    return text[::-1]


@script_function()
def func_substr(parser, text, start_index, end_index):
    """Extract a specified portion of a string.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        text: The string from which the extract will be made.
        start_index: Integer index of the first character to extract.
        end_index: Integer index of the first character that will not be extracted.

    Returns:
        Returns the substring beginning with the character at the start index,
        up to (but not including) the character at the end index.  The first
        character is at index number 0.  If the start index is left blank, it
        defaults to the first character in the string.  If the end index is
        left blank, it defaults to the number of characters in the string.
        If either index is negative, it is subtracted from the total number of
        characters in the string to provide the index used.
    """
    try:
        start = int(start_index) if start_index else None
    except ValueError:
        start = None
    try:
        end = int(end_index) if end_index else None
    except ValueError:
        end = None
    return text[start:end]


@script_function(eval_args=False)
def func_getmulti(parser, multi, item_index, separator=MULTI_VALUED_JOINER):
    """Returns value of the item at the specified index in the multi-value variable.  Index values are zero-based.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        multi: The multi-value from which the item is to be retrieved.
        item_index: The zero-based integer index of the item to be retrieved.
        separator: String used to separate the elements in the multi-value.

    Returns:
        Returns the value of the item at the specified index in the multi-value variable.
    """
    if not item_index:
        return ''
    try:
        index = int(item_index.eval(parser))
        multi_var = _get_multi_values(parser, multi, separator)
        return str(multi_var[index])
    except (ValueError, IndexError):
        return ''


@script_function(eval_args=False)
def func_foreach(parser, multi, loop_code, separator=MULTI_VALUED_JOINER):
    """Iterates over each element found in the specified multi-value variable.

    Iterates over each element found in the specified multi-value variable, executing the specified code.
    For each loop, the element value is first stored in the tag specified by _loop_value and the count is
    stored in the tag specified by _loop_count.  This allows the element or count value to be accessed within
    the code script.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        multi: The multi-value to be iterated.
        loop_code: String of script code to be processed on each iteration.
        separator: String used to separate the elements in the multi-value.
    """
    multi_value = _get_multi_values(parser, multi, separator)
    for loop_count, value in enumerate(multi_value, 1):
        func_set(parser, '_loop_count', str(loop_count))
        func_set(parser, '_loop_value', str(value))
        loop_code.eval(parser)
    func_unset(parser, '_loop_count')
    func_unset(parser, '_loop_value')
    return ''


@script_function(eval_args=False)
def func_while(parser, condition, loop_code):
    """Standard 'while' loop.  Also includes a runaway check to limit the maximum number of iterations.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        condition: String of script code to check before each iteration through the loop.
        loop_code: String of script code to be processed on each iteration.
    """
    if condition and loop_code:
        runaway_check = 1000
        loop_count = 0
        while condition.eval(parser) and loop_count < runaway_check:
            loop_count += 1
            func_set(parser, '_loop_count', str(loop_count))
            loop_code.eval(parser)
        func_unset(parser, '_loop_count')
    return ''


@script_function(eval_args=False)
def func_map(parser, multi, loop_code, separator=MULTI_VALUED_JOINER):
    """Iterates over each element found in the specified multi-value variable and updates the value.

    Iterates over each element found in the specified multi-value variable and updates the value of the
    element to the value returned by the specified code. For each loop, the element value is first stored in
    the tag specified by _loop_value and the count is stored in the tag specified by _loop_count.  This
    allows the element or count value to be accessed within the code script.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        multi: The multi-value to be iterated.
        loop_code: String of script code to be processed on each iteration that yields the new value for
            the multi-value element.
        separator: String used to separate the elements in the multi-value.

    Returns the updated multi-value variable.
    """
    multi_value = _get_multi_values(parser, multi, separator)
    for loop_count, value in enumerate(multi_value, 1):
        func_set(parser, '_loop_count', str(loop_count))
        func_set(parser, '_loop_value', str(value))
        multi_value[loop_count - 1] = str(loop_code.eval(parser))
    func_unset(parser, '_loop_count')
    func_unset(parser, '_loop_value')
    if not isinstance(separator, str):
        separator = separator.eval(parser)
    return separator.join(multi_value)


@script_function(eval_args=False)
def func_join(parser, multi, join_phrase, separator=MULTI_VALUED_JOINER):
    """Joins all elements in the specified multi-value variable, placing the join_phrase between each element.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        multi: The ScriptVariable/Function that evaluates to a multi-value whose
            elements are to be joined.
        join_phrase: The ScriptVariable/Function that evaluates to a string which
            will be placed between each of the elements.
        separator: A string or the ScriptVariable/Function that evaluates to the
            string used to separate the elements in the multi-value.

    Returns a string with the elements joined.
    """
    join_phrase = str(join_phrase.eval(parser))
    multi_value = _get_multi_values(parser, multi, separator)
    return join_phrase.join(multi_value)


@script_function(eval_args=False)
def func_slice(parser, multi, start_index, end_index, separator=MULTI_VALUED_JOINER):
    """Returns a multi-value containing a slice of the supplied multi-value.  Index values are zero-based.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        multi: The ScriptVariable/Function that evaluates to a multi-value from
            which the slice is to be retrieved.
        start_index: The ScriptVariable/Function that evaluates to a zero-based integer
            index of the first item included in the slice.
        end_index: The ScriptVariable/Function that evaluates to a zero-based integer
            index of the first item not included in the slice.
        separator: A string or the ScriptVariable/Function that evaluates to the
            string used to separate the elements in the multi-value.

    Returns:
        Returns a multi-value variable containing the specified slice.
    """
    try:
        start = int(start_index.eval(parser)) if start_index else None
    except ValueError:
        start = None
    try:
        end = int(end_index.eval(parser)) if end_index else None
    except ValueError:
        end = None
    try:
        multi_var = _get_multi_values(parser, multi, separator)
        if not isinstance(separator, str):
            separator = separator.eval(parser)
        return separator.join(multi_var[start:end])
    except IndexError:
        return ''


@script_function()
def func_datetime(parser, format=None):
    """Return the current date and time as a string.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        format: A string or the ScriptVariable/Function that evaluates to the
            string used to format the output.  Default is '%Y-%m-%d %H:%M:%S'
            if blank.  Uses strftime() format.

    Returns:
        Returns the current date and time as a string.
    """
    # local_tz required for Python 3.5 which does not allow setting astimezone()
    # on a naive datetime.datetime object.  This provides timezone information to
    # allow the use of %Z and %z in the output format.
    local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

    # Handle case where format evaluates to ''
    if not format:
        format = '%Y-%m-%d %H:%M:%S'

    return datetime.datetime.now(tz=local_tz).strftime(format)
