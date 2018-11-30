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
            if argnum_bound and not (argnum_bound.lower <= argcount
                                     and (argnum_bound.upper is None
                                          or len(args) <= argnum_bound.upper)):
                raise ScriptError(
                    "Wrong number of arguments for $%s: Expected %s, got %i at position %i, line %i"
                    % (name,
                       str(argnum_bound.lower)
                        if argnum_bound.upper is None
                        else "%i - %i" % (argnum_bound.lower, argnum_bound.upper),
                       argcount,
                       parser._x,
                       parser._y))
        except KeyError:
            raise ScriptUnknownFunction("Unknown function '%s'" % name)

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

    _function_registry = ExtensionPoint()
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


def _compute_int(operation, *args):
    return str(reduce(operation, map(int, args)))


def _compute_logic(operation, *args):
    return operation(args)


def _get_multi_values(parser, multi, separator):
    if isinstance(separator, ScriptExpression):
        separator = separator.eval(parser)

    if separator == MULTI_VALUED_JOINER:
        # Convert ScriptExpression containing only a single variable into variable
        if (isinstance(multi, ScriptExpression) and
                len(multi) == 1 and
                isinstance(multi[0], ScriptVariable)):
            multi = multi[0]

        # If a variable, return multi-values
        if isinstance(multi, ScriptVariable):
            return parser.context.getall(normalize_tagname(multi.name))

    # Fall-back to converting to a string and splitting if haystack is an expression
    # or user has overridden the separator character.
    multi = multi.eval(parser)
    return multi.split(separator) if separator else [multi]


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
    try:
        return text[:int(length)]
    except ValueError:
        return ""


def func_right(parser, text, length):
    """Returns last ``num`` characters from ``text``."""
    try:
        return text[-int(length):]
    except ValueError:
        return ""


def func_lower(parser, text):
    """Returns ``text`` in lower case."""
    return text.lower()


def func_upper(parser, text):
    """Returns ``text`` in upper case."""
    return text.upper()


def func_pad(parser, text, length, char):
    try:
        return char * (int(length) - len(text)) + text
    except ValueError:
        return ""


def func_strip(parser, text):
    return re.sub(r"\s+", " ", text).strip()


def func_replace(parser, text, old, new):
    return text.replace(old, new)


def func_in(parser, text, needle):
    if needle in text:
        return "1"
    else:
        return ""


def func_inmulti(parser, haystack, needle, separator=MULTI_VALUED_JOINER):
    """Searches for ``needle`` in ``haystack``, supporting a list variable for
       ``haystack``. If a string is used instead, then a ``separator`` can be
       used to split it. In both cases, it returns true if the resulting list
       contains exactly ``needle`` as a member."""

    needle = needle.eval(parser)
    return func_in(parser, _get_multi_values(parser, haystack, separator), needle)


def func_rreplace(parser, text, old, new):
    try:
        return re.sub(old, new, text)
    except re.error:
        return text


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


def func_unset(parser, name):
    """Unsets the variable ``name``."""
    name = normalize_tagname(name)
    # Allow wild-card unset for certain keys
    if name in ('performer:*', 'comment:*', 'lyrics:*'):
        name = name[:-1]
        for key in list(parser.context.keys()):
            if key.startswith(name):
                del parser.context[key]
        return ""
    try:
        del parser.context[name]
    except KeyError:
        pass
    return ""


def func_delete(parser, name):
    """
    Deletes the variable ``name``.
    This will unset the tag with the given name and also mark the tag for
    deletion on save.
    """
    parser.context.delete(normalize_tagname(name))
    return ""


def func_set(parser, name, value):
    """Sets the variable ``name`` to ``value``."""
    if value:
        parser.context[normalize_tagname(name)] = value
    else:
        func_unset(parser, name)
    return ""


def func_setmulti(parser, name, value, separator=MULTI_VALUED_JOINER):
    """Sets the variable ``name`` to ``value`` as a list; splitting by the passed string, or "; " otherwise."""
    return func_set(parser, name, value.split(separator) if value and separator else value)


def func_get(parser, name):
    """Returns the variable ``name`` (equivalent to ``%name%``)."""
    return parser.context.get(normalize_tagname(name), "")


def func_copy(parser, new, old):
    """Copies content of variable ``old`` to variable ``new``."""
    new = normalize_tagname(new)
    old = normalize_tagname(old)
    parser.context[new] = parser.context.getall(old)[:]
    return ""


def func_copymerge(parser, new, old):
    """Copies content of variable ``old`` and appends it into variable ``new``, removing duplicates. This is normally
    used to merge a multi-valued variable into another, existing multi-valued variable."""
    new = normalize_tagname(new)
    old = normalize_tagname(old)
    newvals = parser.context.getall(new)
    oldvals = parser.context.getall(old)
    parser.context[new] = uniqify(newvals + oldvals)
    return ""


def func_trim(parser, text, char=None):
    """Trims all leading and trailing whitespaces from ``text``. The optional
       second parameter specifies the character to trim."""
    if char:
        return text.strip(char)
    else:
        return text.strip()


def func_add(parser, x, y, *args):
    """Adds ``y`` to ``x``.
       Can be used with an arbitrary number of arguments.
       Eg: $add(x, y, z) = ((x + y) + z)
    """
    try:
        return _compute_int(operator.add, x, y, *args)
    except ValueError:
        return ""


def func_sub(parser, x, y, *args):
    """Subtracts ``y`` from ``x``.
       Can be used with an arbitrary number of arguments.
       Eg: $sub(x, y, z) = ((x - y) - z)
    """
    try:
        return _compute_int(operator.sub, x, y, *args)
    except ValueError:
        return ""


def func_div(parser, x, y, *args):
    """Divides ``x`` by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $div(x, y, z) = ((x / y) / z)
    """
    try:
        return _compute_int(operator.floordiv, x, y, *args)
    except ValueError:
        return ""


def func_mod(parser, x, y, *args):
    """Returns the remainder of ``x`` divided by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $mod(x, y, z) = ((x % y) % z)
    """
    try:
        return _compute_int(operator.mod, x, y, *args)
    except ValueError:
        return ""


def func_mul(parser, x, y, *args):
    """Multiplies ``x`` by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $mul(x, y, z) = ((x * y) * z)
    """
    try:
        return _compute_int(operator.mul, x, y, *args)
    except ValueError:
        return ""


def func_or(parser, x, y, *args):
    """Returns true, if either ``x`` or ``y`` not empty.
       Can be used with an arbitrary number of arguments. The result is
       true if ANY of the arguments is not empty.
    """
    if _compute_logic(any, x, y, *args):
        return "1"
    else:
        return ""


def func_and(parser, x, y, *args):
    """Returns true, if both ``x`` and ``y`` are not empty.
       Can be used with an arbitrary number of arguments. The result is
       true if ALL of the arguments are not empty.
    """
    if _compute_logic(all, x, y, *args):
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


def func_len(parser, text=""):
    return str(len(text))


def func_lenmulti(parser, multi, separator=MULTI_VALUED_JOINER):
    return func_len(parser, _get_multi_values(parser, multi, separator))


def func_performer(parser, pattern="", join=", "):
    values = []
    for name, value in parser.context.items():
        if name.startswith("performer:") and pattern in name:
            values.append(value)
    return join.join(values)


def func_matchedtracks(parser, *args):
    # only works in file naming scripts, always returns zero in tagging scripts
    if parser.file and parser.file.parent:
        return str(parser.file.parent.album.get_num_matched_tracks())
    return "0"


def func_is_complete(parser):
    if (parser.file and parser.file.parent
            and parser.file.parent.album.is_complete()):
        return "1"
    return "0"


def func_firstalphachar(parser, text="", nonalpha="#"):
    if len(text) == 0:
        return nonalpha
    firstchar = text[0]
    if firstchar.isalpha():
        return firstchar.upper()
    else:
        return nonalpha


def func_initials(parser, text=""):
    return "".join(a[:1] for a in text.split(" ") if a[:1].isalpha())


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


def func_startswith(parser, text, prefix):
    if text.startswith(prefix):
        return "1"
    return "0"


def func_endswith(parser, text, suffix):
    if text.endswith(suffix):
        return "1"
    return "0"


def func_truncate(parser, text, length):
    try:
        length = int(length)
    except ValueError as e:
        length = None
    return text[:length].rstrip()


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


def func_eq_any(parser, x, *args):
    """
    Return True if one string matches any of one or more other strings.
    $eq_any(a,b,c ...) is functionally equivalent to $or($eq(a,b),$eq(a,c) ...)
    Example: $if($eq_any(%artist%,foo,bar,baz),$set(engineer,test))
    """
    # Inspired by the eq2 plugin by Brian Schweitzer.
    return '1' if x in args else ''


def func_ne_all(parser, x, *args):
    """
    Return True if one string doesn't match all of one or more other strings.
    $ne_all(a,b,c ...) is functionally equivalent to $and($ne(a,b),$ne(a,c) ...)
    Example: $if($ne_all(%artist%,foo,bar,baz),$set(engineer,test))
    """
    # Inspired by the ne2 plugin by Brian Schweitzer.
    return '1' if x not in args else ''


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


def func_ne_any(parser, x, *args):
    """
    Return True if all strings are not equal.
    $ne_any(a,b,c ...) is functionally equivalent to $or($ne(a,b),$ne(a,c) ...)
    Example: $if($ne_any(%albumartist%,%trackartist%,%composer%),$set(lyricist,%composer%))
    """
    return func_not(parser, func_eq_all(parser, x, *args))


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
    return "Zs" == unicodedata.category(char) or "Sk" == unicodedata.category(char) or "P" == unicodedata.category(char)[0]


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
register_script_function(func_delete, "delete")
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
register_script_function(func_inmulti, "inmulti", eval_args=False)
register_script_function(func_copy, "copy")
register_script_function(func_copymerge, "copymerge")
register_script_function(func_len, "len")
register_script_function(func_lenmulti, "lenmulti", eval_args=False)
register_script_function(func_performer, "performer")
register_script_function(func_matchedtracks, "matchedtracks", eval_args=False)
register_script_function(func_is_complete, "is_complete")
register_script_function(func_firstalphachar, "firstalphachar")
register_script_function(func_initials, "initials")
register_script_function(func_firstwords, "firstwords")
register_script_function(func_startswith, "startswith")
register_script_function(func_endswith, "endswith")
register_script_function(func_truncate, "truncate")
register_script_function(func_swapprefix, "swapprefix", check_argcount=False)
register_script_function(func_delprefix, "delprefix", check_argcount=False)
register_script_function(func_eq_any, "eq_any", check_argcount=False)
register_script_function(func_ne_all, "ne_all", check_argcount=False)
register_script_function(func_eq_all, "eq_all", check_argcount=False)
register_script_function(func_ne_any, "ne_any", check_argcount=False)
register_script_function(func_title, "title")
