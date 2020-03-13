# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2012 Lukáš Lalinský
# Copyright (C) 2007 Javier Kohen
# Copyright (C) 2008-2011, 2014-2015, 2018-2020 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 stephen
# Copyright (C) 2012, 2014, 2017 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2020 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Ville Skyttä
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Calvin Walton
# Copyright (C) 2018 virusMac
# Copyright (C) 2020 Bob Swift
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
from collections.abc import MutableSequence
import datetime
from functools import reduce
from inspect import getfullargspec
import operator
from queue import LifoQueue
import re
import unicodedata

from picard import config
from picard.metadata import (
    MULTI_VALUED_JOINER,
    Metadata,
)
from picard.plugin import ExtensionPoint
from picard.util import uniqify


try:
    from markdown import markdown
except ImportError:
    markdown = None


class ScriptError(Exception):
    pass


class ScriptParseError(ScriptError):
    def __init__(self, stackitem, message):
        super().__init__(
            "{prefix:s}: {message:s}".format(
                prefix=str(stackitem),
                message=message
            )
        )


class ScriptEndOfFile(ScriptParseError):
    def __init__(self, stackitem):
        super().__init__(
            stackitem,
            "Unexpected end of script"
        )


class ScriptSyntaxError(ScriptParseError):
    pass


class ScriptUnknownFunction(ScriptParseError):
    def __init__(self, stackitem):
        super().__init__(
            stackitem,
            "Unknown function '{name}'".format(name=stackitem.name)
        )


class ScriptRuntimeError(ScriptError):
    def __init__(self, stackitem, message='Unknown error'):
        super().__init__(
            "{prefix:s}: {message:s}".format(
                prefix=str(stackitem),
                message=message
            )
        )


class StackItem:
    def __init__(self, line, column, name=None):
        self.line = line
        self.column = column
        if name is None:
            self.name = None
        else:
            self.name = '$' + name

    def __str__(self):
        if self.name is None:
            return '{line:d}:{column:d}'.format(
                line=self.line,
                column=self.column
            )
        else:
            return '{line:d}:{column:d}:{name}'.format(
                line=self.line,
                column=self.column,
                name=self.name
            )


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


class FunctionRegistryItem:
    def __init__(self, function, eval_args, argcount, documentation=None,
                 name=None, module=None):
        self.function = function
        self.eval_args = eval_args
        self.argcount = argcount
        self.documentation = documentation
        self.name = name
        self.module = module

    def __repr__(self):
        return '{classname}({me.function}, {me.eval_args}, {me.argcount}, {doc})'.format(
            classname=self.__class__.__name__,
            me=self,
            doc='"""{0}"""'.format(self.documentation) if self.documentation else None
        )

    def _preprocess(self, data, preprocessor):
        if preprocessor is not None:
            data = preprocessor(data, function=self)
        return data

    def markdowndoc(self, preprocessor=None):
        if self.documentation is not None:
            ret = _(self.documentation)
        else:
            ret = ''
        return self._preprocess(ret, preprocessor)

    def htmldoc(self, preprocessor=None):
        if self.documentation is not None and markdown is not None:
            ret = markdown(_(self.documentation))
        else:
            ret = ''
        return self._preprocess(ret, preprocessor)


class ScriptFunctionDocError(Exception):
    pass


def script_function_documentation(name, fmt, functions=None, preprocessor=None):
    if functions is None:
        functions = dict(ScriptParser._function_registry)
    if name not in functions:
        raise ScriptFunctionDocError("no such function: %s (known functions: %r)" % (name, [name for name in functions]))

    if fmt == 'html':
        return functions[name].htmldoc(preprocessor)
    elif fmt == 'markdown':
        return functions[name].markdowndoc(preprocessor)
    else:
        raise ScriptFunctionDocError("no such documentation format: %s (known formats: html, markdown)" % fmt)


def script_function_names(functions=None):
    if functions is None:
        functions = dict(ScriptParser._function_registry)
    for name in sorted(functions):
        yield name


def script_function_documentation_all(fmt='markdown', pre='',
                                      post='', preprocessor=None):
    functions = dict(ScriptParser._function_registry)
    doc_elements = []
    for name in script_function_names(functions):
        doc_element = script_function_documentation(name, fmt,
                                                    functions=functions,
                                                    preprocessor=preprocessor)
        if doc_element:
            doc_elements.append(pre + doc_element + post)
    return "\n".join(doc_elements)


Bound = namedtuple("Bound", ["lower", "upper"])


class ScriptFunction(object):

    def __init__(self, name, args, parser, column=0, line=0):
        self.stackitem = StackItem(line, column, name)
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
                    raise ScriptSyntaxError(
                        self.stackitem,
                        "Wrong number of arguments for $%s: Expected %s, got %i"
                        % (name, expected, argcount)
                    )
        except KeyError:
            raise ScriptUnknownFunction(self.stackitem)

        self.name = name
        self.args = args

    def __repr__(self):
        return "<ScriptFunction $%s(%r)>" % (self.name, self.args)

    def eval(self, parser):
        try:
            function_registry_item = parser.functions[self.name]
        except KeyError:
            raise ScriptUnknownFunction(self.stackitem)

        if function_registry_item.eval_args:
            args = [arg.eval(parser) for arg in self.args]
        else:
            args = self.args
        parser._function_stack.put(self.stackitem)
        # Save return value to allow removing function from the stack on successful completion
        return_value = function_registry_item.function(parser, *args)
        parser._function_stack.get()
        return return_value


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

    def __init__(self):
        self._function_stack = LifoQueue()

    def __raise_eof(self):
        raise ScriptEndOfFile(StackItem(line=self._y, column=self._x))

    def __raise_char(self, ch):
        raise ScriptSyntaxError(StackItem(line=self._y, column=self._x), "Unexpected character '%s'" % ch)

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
        column = self._x - 2     # Set x position to start of function name ($)
        line = self._y
        while True:
            ch = self.read()
            if ch == '(':
                name = self._text[start:self._pos-1]
                if name not in self.functions:
                    raise ScriptUnknownFunction(StackItem(line, column, name))
                return ScriptFunction(name, self.parse_arguments(), self, column, line)
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


class MultiValue(MutableSequence):
    def __init__(self, parser, multi, separator):
        self.parser = parser
        if isinstance(separator, ScriptExpression):
            self.separator = separator.eval(self.parser)
        else:
            self.separator = separator
        if (self.separator == MULTI_VALUED_JOINER
            and len(multi) == 1
            and isinstance(multi[0], ScriptVariable)):
            # Convert ScriptExpression containing only a single variable into variable
            self._multi = self.parser.context.getall(normalize_tagname(multi[0].name))
        else:
            # Fall-back to converting to a string and splitting if haystack is an expression
            # or user has overridden the separator character.
            evaluated_multi = multi.eval(self.parser)
            if not evaluated_multi:
                self._multi = []
            elif self.separator:
                self._multi = evaluated_multi.split(self.separator)
            else:
                self._multi = [evaluated_multi]

    def __len__(self):
        return len(self._multi)

    def __getitem__(self, key):
        return self._multi[key]

    def __setitem__(self, key, value):
        self._multi[key] = value

    def __delitem__(self, key):
        del self._multi[key]

    def insert(self, index, value):
        return self._multi.insert(index, value)

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__, self.parser, self._multi, self.separator)

    def __str__(self):
        return self.separator.join(self)


def enabled_tagger_scripts_texts():
    """Returns an iterator over the enabled tagger scripts.
    For each script, you'll get a tuple consisting of the script name and text"""
    if not config.setting["enable_tagger_scripts"]:
        return []
    return [(s_name, s_text) for _s_pos, s_name, s_enabled, s_text in config.setting["list_of_scripts"] if s_enabled and s_text]


def register_script_function(function, name=None, eval_args=True,
                             check_argcount=True, documentation=None):
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
    ScriptParser._function_registry.register(
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
            )
        )
    )


def script_function(name=None, eval_args=True, check_argcount=True, prefix='func_', documentation=None):
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
        register_script_function(
            func,
            name=sname,
            eval_args=eval_args,
            check_argcount=check_argcount,
            documentation=documentation
        )
        return func
    return script_function_decorator


def _compute_int(operation, *args):
    return str(reduce(operation, map(int, args)))


def _compute_logic(operation, *args):
    return operation(args)


@script_function(eval_args=False, documentation=N_(
    """`$if(if,then,else)`

If `if` is not empty, it returns `then`, otherwise it returns `else`."""
))
def func_if(parser, _if, _then, _else=None):
    if _if.eval(parser):
        return _then.eval(parser)
    elif _else:
        return _else.eval(parser)
    return ''


@script_function(eval_args=False, documentation=N_(
    """`$if2(a1,a2,a3,...)`

Returns first non empty argument."""
))
def func_if2(parser, *args):
    for arg in args:
        arg = arg.eval(parser)
        if arg:
            return arg
    return ''


@script_function(eval_args=False, documentation=N_(
    """`$noop(...)`

Does nothing (useful for comments or disabling a block of code)."""
))
def func_noop(parser, *args):
    return ''


@script_function(documentation=N_(
    """`$left(text,num)`

Returns the first `num` characters from `text`."""
))
def func_left(parser, text, length):
    try:
        return text[:int(length)]
    except ValueError:
        return ""


@script_function(documentation=N_(
    """`$right(text,num)`

Returns the last `num` characters from `text`."""
))
def func_right(parser, text, length):
    try:
        return text[-int(length):]
    except ValueError:
        return ""


@script_function(documentation=N_(
    """`$lower(text)`

Returns text in lower case."""
))
def func_lower(parser, text):
    return text.lower()


@script_function(documentation=N_(
    """`$upper(text)`

Returns `text` in upper case."""
))
def func_upper(parser, text):
    return text.upper()


@script_function(documentation=N_(
    """`$pad(text,length,char)`

Pads the `text` to the `length` provided by adding as many copies of `char` as
    needed to the **beginning** of the string."""
))
def func_pad(parser, text, length, char):
    try:
        return char * (int(length) - len(text)) + text
    except ValueError:
        return ""


@script_function(documentation=N_(
    """`$strip(text)`

Replaces all whitespace in `text` with a single space, and removes leading and trailing spaces.
Whitespace characters include multiple consecutive spaces, and various other unicode characters."""
))
def func_strip(parser, text):
    return re.sub(r"\s+", " ", text).strip()


@script_function(documentation=N_(
    """`$replace(text,search,replace)`

Replaces occurrences of `search` in `text` with value of `replace` and returns the resulting string."""
))
def func_replace(parser, text, old, new):
    return text.replace(old, new)


@script_function(documentation=N_(
    """`$in(x,y)`

Returns true, if `x` contains `y`."""
))
def func_in(parser, text, needle):
    if needle in text:
        return "1"
    else:
        return ""


@script_function(eval_args=False, documentation=N_(
    """`$inmulti(%x%,y)`

Returns true if multi-value variable `x` contains exactly `y` as one of its values.

_Since Picard 1.0_"""
))
def func_inmulti(parser, haystack, needle, separator=MULTI_VALUED_JOINER):
    """Searches for ``needle`` in ``haystack``, supporting a list variable for
       ``haystack``. If a string is used instead, then a ``separator`` can be
       used to split it. In both cases, it returns true if the resulting list
       contains exactly ``needle`` as a member."""

    needle = needle.eval(parser)
    return func_in(parser, MultiValue(parser, haystack, separator), needle)


@script_function(documentation=N_(
    """`$rreplace(text,pattern,replace)`

[Regular expression](https://docs.python.org/3/library/re.html#regular-expression-syntax) replace."""
))
def func_rreplace(parser, text, old, new):
    try:
        return re.sub(old, new, text)
    except re.error:
        return text


@script_function(documentation=N_(
    """`$rsearch(text,pattern)`

[Regular expression](https://docs.python.org/3/library/re.html#regular-expression-syntax) search.
    This function will return the first matching group."""
))
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


@script_function(documentation=N_(
    """`$num(num,len)`

Returns `num` formatted to `len` digits, where `len` cannot be greater than `20`."""
))
def func_num(parser, text, length):
    try:
        format_ = "%%0%dd" % max(0, min(int(length), 20))
    except ValueError:
        return ""
    try:
        value = int(text)
    except ValueError:
        value = 0
    return format_ % value


@script_function(documentation=N_(
    """`$unset(name)`

Unsets the variable `name`.
Allows for wildcards to unset certain tags (works with 'performer:*', 'comment:*', and 'lyrics:*').
i.e. `$unset(performer:*)` would unset all performer tags."""
))
def func_unset(parser, name):
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


@script_function(documentation=N_(
    """`$delete(name)`

Unsets the variable `name` and marks the tag for deletion.
This is similar to `$unset(name)` but also marks the tag for deletion. E.g.
    running `$delete(genre)` will actually remove the genre tag from a file when
    saving.

_Since Picard 2.1_"""
))
def func_delete(parser, name):
    parser.context.delete(normalize_tagname(name))
    return ""


@script_function(documentation=N_(
    """`$set(name,value)`

Sets the variable `name` to `value`.
Note: To create a variable which can be used for the file naming string, but
    which will not be written as a tag in the file, prefix the variable name
    with an underscore. `%something%` will create a "something" tag;
    `%_something%` will not."""
))
def func_set(parser, name, value):
    if value:
        parser.context[normalize_tagname(name)] = value
    else:
        func_unset(parser, name)
    return ""


@script_function(documentation=N_(
    """`$setmulti(name,value,separator="; ")`

Sets the variable `name` to `value`, using the separator (or "; " if not passed)
    to coerce the value back into a proper multi-valued tag. This can be used to
    operate on multi-valued tags as a string, and then set them back as proper
    multi-valued tags, e.g `$setmulti(genre,$lower(%genre%))`

_Since Picard 1.0_"""
))
def func_setmulti(parser, name, value, separator=MULTI_VALUED_JOINER):
    return func_set(parser, name, value.split(separator) if value and separator else value)


@script_function(documentation=N_(
    """`$get(name)`

Returns the variable `name` (equivalent to `%name%`)."""
))
def func_get(parser, name):
    """Returns the variable ``name`` (equivalent to ``%name%``)."""
    return parser.context.get(normalize_tagname(name), "")


@script_function(documentation=N_(
    """`$copy(new,old)`

Copies metadata from variable `old` to `new`.
The difference between `$set(new,%old%)` is that `$copy(new,old)` copies
    multi-value variables without flattening them.

_Since Picard 0.9_"""
))
def func_copy(parser, new, old):
    new = normalize_tagname(new)
    old = normalize_tagname(old)
    parser.context[new] = parser.context.getall(old)[:]
    return ""


@script_function(documentation=N_(
    """`$copymerge(new,old)`

Merges metadata from variable `old` into `new`, removing duplicates and
    appending to the end, so retaining the original ordering. Like `$copy`, this
    will also copy multi-valued variables without flattening them.

_Since Picard 1.0_"""
))
def func_copymerge(parser, new, old):
    new = normalize_tagname(new)
    old = normalize_tagname(old)
    newvals = parser.context.getall(new)
    oldvals = parser.context.getall(old)
    parser.context[new] = uniqify(newvals + oldvals)
    return ""


@script_function(documentation=N_(
    """`$trim(text[,char])`

Trims all leading and trailing whitespaces from `text`.
    The optional second parameter specifies the character to trim."""
))
def func_trim(parser, text, char=None):
    if char:
        return text.strip(char)
    else:
        return text.strip()


@script_function(documentation=N_(
    """`$add(x,y,*args)`

Add `y` to `x`.
Can be used with an arbitrary number of arguments.
i.e. `$add(x,y,z) = ((x + y) + z)`"""
))
def func_add(parser, x, y, *args):
    try:
        return _compute_int(operator.add, x, y, *args)
    except ValueError:
        return ""


@script_function(documentation=N_(
    """`$sub(x,y,*args)`

Subtracts `y` from `x`.
Can be used with an arbitrary number of arguments.
i.e. `$sub(x,y,z) = ((x - y) - z)`"""
))
def func_sub(parser, x, y, *args):
    try:
        return _compute_int(operator.sub, x, y, *args)
    except ValueError:
        return ""


@script_function(documentation=N_(
    """`$div(x,y,*args)`

Divides `x` by `y`.
Can be used with an arbitrary number of arguments.

i.e. `$div(x,y,z) = ((x / y) / z)`"""
))
def func_div(parser, x, y, *args):
    """Divides ``x`` by ``y``.
       Can be used with an arbitrary number of arguments.
       Eg: $div(x, y, z) = ((x / y) / z)
    """
    try:
        return _compute_int(operator.floordiv, x, y, *args)
    except ValueError:
        return ""
    except ZeroDivisionError:
        return ""


@script_function(documentation=N_(
    """`$mod(x,y,*args)`

Returns the remainder of `x` divided by `y`.
Can be used with an arbitrary number of arguments.

i.e. `$mod(x,y,z) = ((x % y) % z)`"""
))
def func_mod(parser, x, y, *args):
    try:
        return _compute_int(operator.mod, x, y, *args)
    except (ValueError, ZeroDivisionError):
        return ""


@script_function(documentation=N_(
    """`$mul(x,y,*args)`

Multiplies `x` by `y`.
Can be used with an arbitrary number of arguments.
    i.e. `$mul(x,y,z) = ((x * y) * z)`"""
))
def func_mul(parser, x, y, *args):
    try:
        return _compute_int(operator.mul, x, y, *args)
    except ValueError:
        return ""


@script_function(documentation=N_(
    """`$or(x,y,*args)`

Returns true if either `x` or `y` not empty.
    Can be used with an arbitrary number of arguments.
    The result is true if ANY of the arguments is not empty."""
))
def func_or(parser, x, y, *args):
    """Returns true, if either ``x`` or ``y`` not empty.
       Can be used with an arbitrary number of arguments. The result is
       true if ANY of the arguments is not empty.
    """
    if _compute_logic(any, x, y, *args):
        return "1"
    else:
        return ""


@script_function(documentation=N_(
    """`$and(x,y,*args)`

Returns true if both `x` and `y` are not empty.
    Can be used with an arbitrary number of arguments.
    The result is true if ALL of the arguments are not empty."""
))
def func_and(parser, x, y, *args):
    if _compute_logic(all, x, y, *args):
        return "1"
    else:
        return ""


@script_function(documentation=N_(
    """`$not(x)`

Returns true if `x` is empty."""
))
def func_not(parser, x):
    if not x:
        return "1"
    else:
        return ""


@script_function(documentation=N_(
    """`$eq(x,y)`

Returns true if `x` equals `y`."""
))
def func_eq(parser, x, y):
    if x == y:
        return "1"
    else:
        return ""


@script_function(documentation=N_(
    """`$ne(x,y)`

Returns true if `x` does not equal `y`."""
))
def func_ne(parser, x, y):
    if x != y:
        return "1"
    else:
        return ""


@script_function(documentation=N_(
    """`$lt(x,y)`

Returns true if `x` is less than `y`."""
))
def func_lt(parser, x, y):
    try:
        if int(x) < int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function(documentation=N_(
    """`$lte(x,y)`

Returns true if `x` is less than or equal to `y`."""
))
def func_lte(parser, x, y):
    try:
        if int(x) <= int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function(documentation=N_(
    """`$gt(x,y)`

Returns true if `x` is greater than `y`."""
))
def func_gt(parser, x, y):
    try:
        if int(x) > int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function(documentation=N_(
    """`$gte(x,y)`

Returns true if `x` is greater than or equal to `y`."""
))
def func_gte(parser, x, y):
    try:
        if int(x) >= int(y):
            return "1"
    except ValueError:
        pass
    return ""


@script_function(documentation=N_(
    """`$len(text)`

Returns the number of characters in `text`."""
))
def func_len(parser, text=""):
    return str(len(text))


@script_function(eval_args=False, documentation=N_(
    """`$lenmulti(name,separator="; ")`

Returns the number of elements in the multi-value tag `name`. A literal value
    representing a multi-value can be substituted for `name`, using the
    `separator` (or "; " if not passed) to coerce the value into a proper
    multi-valued tag.

For example, the following will return the value "3".
    `$lenmulti(One; Two; Three)`"""
))
def func_lenmulti(parser, multi, separator=MULTI_VALUED_JOINER):
    return str(len(MultiValue(parser, multi, separator)))


@script_function(documentation=N_(
    """`$performer(pattern="",join=", ")`

Returns the performers where the performance type (e.g. "vocal") matches `pattern`, joined by `join`.

_Since Picard 0.10_"""
))
def func_performer(parser, pattern="", join=", "):
    values = []
    for name, value in parser.context.items():
        if name.startswith("performer:") and pattern in name:
            values.append(value)
    return join.join(values)


@script_function(eval_args=False, documentation=N_(
    """`$matchedtracks()`

Returns the number of matched tracks within a release.
    **Only works in File Naming scripts.**

_Since Picard 0.12_"""
))
def func_matchedtracks(parser, *args):
    # only works in file naming scripts, always returns zero in tagging scripts
    file = parser.file
    if file and file.parent and hasattr(file.parent, 'album'):
        return str(parser.file.parent.album.get_num_matched_tracks())
    return "0"


@script_function(documentation=N_(
    """`$is_complete()`

Returns true if every track in the album is matched to a single file.
**Only works in File Naming scripts.**"""
))
def func_is_complete(parser):
    # only works in file naming scripts, always returns zero in tagging scripts
    file = parser.file
    if (file and file.parent and hasattr(file.parent, 'album')
            and file.parent.album.is_complete()):
        return "1"
    return ""


@script_function(documentation=N_(
    """`$firstalphachar(text,nonalpha="#")`

Returns the first character of `text`. If `text` is not an alphabetic character `nonalpha` is returned instead.

_Since Picard 0.12_"""
))
def func_firstalphachar(parser, text="", nonalpha="#"):
    if len(text) == 0:
        return nonalpha
    firstchar = text[0]
    if firstchar.isalpha():
        return firstchar.upper()
    else:
        return nonalpha


@script_function(documentation=N_(
    """`$initials(text)`

Returns the first character of each word in `text`, if it is an alphabetic character.

_Since Picard 0.12_"""
))
def func_initials(parser, text=""):
    return "".join(a[:1] for a in text.split(" ") if a[:1].isalpha())


@script_function(documentation=N_(
    """`$firstwords(text,length)`

Like `$truncate` except that it will only return the complete words from `text` which fit within `length` characters.

_Since Picard 0.12_"""
))
def func_firstwords(parser, text, length):
    try:
        length = int(length)
    except ValueError:
        length = 0
    if len(text) <= length:
        return text
    else:
        try:
            if text[length] == ' ':
                return text[:length]
            return text[:length].rsplit(' ', 1)[0]
        except IndexError:
            return ''


@script_function(documentation=N_(
    """`$startswith(text,prefix)`

Returns true if `text` starts with `prefix`.

_Since Picard 1.4_"""
))
def func_startswith(parser, text, prefix):
    if text.startswith(prefix):
        return "1"
    return ""


@script_function(documentation=N_(
    """`$endswith(text,suffix)`

Returns true if `text` ends with `suffix`.

_Since Picard 1.4_"""
))
def func_endswith(parser, text, suffix):
    if text.endswith(suffix):
        return "1"
    return ""


@script_function(documentation=N_(
    """`$truncate(text,length)`

Truncate `text` to `length`.

_Since Picard 0.12_"""
))
def func_truncate(parser, text, length):
    try:
        length = int(length)
    except ValueError:
        length = None
    return text[:length].rstrip()


@script_function(check_argcount=False, documentation=N_(
    """`$swapprefix(text,*prefixes="a","the")`

Moves the specified prefixes from the beginning to the end of text. If no prefix is specified 'A' and 'The' are used by default.
`$swapprefix(%albumartist%,A,An,The,Le)`

_Since Picard 1.3, previously as a plugin since Picard 0.13_"""
))
def func_swapprefix(parser, text, *prefixes):
    # Inspired by the swapprefix plugin by Philipp Wolfer.

    text, prefix = _delete_prefix(parser, text, *prefixes)
    if prefix != '':
        return text + ', ' + prefix
    return text


@script_function(check_argcount=False, documentation=N_(
    """`$delprefix(text,*prefixes="a","the")`

Deletes the specified prefixes from the beginning of text. If no prefix is specified 'A' and 'The' are used by default.

_Since Picard 1.3_"""
))
def func_delprefix(parser, text, *prefixes):
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


@script_function(check_argcount=False, documentation=N_(
    """`$eq_any(x,a1,a2...)`

Returns true if `x` equals `a1` or `a2` or ...
Functionally equivalent to `$or($eq(x,a1),$eq(x,a2) ...)`.
Functionally equivalent to the eq2 plugin."""
))
def func_eq_any(parser, x, *args):
    """
    Return True if one string matches any of one or more other strings.
    $eq_any(a,b,c ...) is functionally equivalent to $or($eq(a,b),$eq(a,c) ...)
    Example: $if($eq_any(%artist%,foo,bar,baz),$set(engineer,test))
    """
    # Inspired by the eq2 plugin by Brian Schweitzer.
    return '1' if x in args else ''


@script_function(check_argcount=False, documentation=N_(
    """`$ne_all(x,a1,a2...)`

Returns true if `x` does not equal `a1` and `a2` and ...
Functionally equivalent to `$and($ne(x,a1),$ne(x,a2) ...)`.
Functionally equivalent to the ne2 plugin."""
))
def func_ne_all(parser, x, *args):
    """
    Return True if one string doesn't match all of one or more other strings.
    $ne_all(a,b,c ...) is functionally equivalent to $and($ne(a,b),$ne(a,c) ...)
    Example: $if($ne_all(%artist%,foo,bar,baz),$set(engineer,test))
    """
    # Inspired by the ne2 plugin by Brian Schweitzer.
    return '1' if x not in args else ''


@script_function(check_argcount=False, documentation=N_(
    """`$eq_all(x,a1,a2...)`

Returns true if `x` equals `a1` and `a2` and ...
Functionally equivalent to `$and($eq(x,a1),$eq(x,a2) ...)`."""
))
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


@script_function(check_argcount=False, documentation=N_(
    """`$ne_any(x,a1,a2...)`

Returns true if `x` does not equal `a1` or `a2` or ...
Functionally equivalent to `$or($ne(x,a1),$ne(x,a2) ...)`."""
))
def func_ne_any(parser, x, *args):
    """
    Return True if all strings are not equal.
    $ne_any(a,b,c ...) is functionally equivalent to $or($ne(a,b),$ne(a,c) ...)
    Example: $if($ne_any(%albumartist%,%trackartist%,%composer%),$set(lyricist,%composer%))
    """
    return func_not(parser, func_eq_all(parser, x, *args))


@script_function(documentation=N_(
    """`$title(text)`

Returns `text` in title case (first character in every word capitalized).

_Since Picard 2.1_"""
))
def func_title(parser, text):
    # GPL 2.0 licensed code by Javier Kohen, Sambhav Kothari
    # from https://github.com/metabrainz/picard-plugins/blob/2.0/plugins/titlecase/titlecase.py
    """
    Title-case a text - capitalizes first letter of every word
    like: from "Lost in the Supermarket" to "Lost In The Supermarket"
    Example: $set(album,$title(%album%))
    """
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


@script_function(documentation=N_(
    """`$is_audio()`

Returns true, if the file processed is an audio file.

_Since Picard 2.2_"""
))
def func_is_audio(parser):
    if func_is_video(parser) == "1":
        return ""
    else:
        return "1"


@script_function(documentation=N_(
    """`$is_video()`

Returns true, if the file processed is an video file.

_Since Picard 2.2_"""
))
def func_is_video(parser):
    if parser.context['~video'] and parser.context['~video'] != '0':
        return "1"
    else:
        return ""


@script_function(documentation=N_(
    """`$find(haystack,needle)`

Finds the location of one string within another.
    Returns the index of the first occurrance of `needle` in `haystack`, or -1 if `needle` was not found."""
))
def func_find(parser, haystack, needle):
    """Find the location of the first occurrence of one string within another.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        haystack: The string to search.
        needle: The substring to find.

    Returns:
        The zero-based index of the first occurrence of needle in haystack, or "" if needle was not found.
    """
    index = haystack.find(needle)
    if index < 0:
        return ''
    return str(index)


@script_function(documentation=N_(
    """`$reverse(text)`

Returns `text` in reverse order."""
))
def func_reverse(parser, text):
    """Returns 'text' in reverse order.

    Arguments:
        parser: The ScriptParser object used to parse the script.
        text: String to be processed.

    Returns:
        Text in reverse order.
    """
    return text[::-1]


@script_function(documentation=N_(
    """`$substr(text,start,end)`

Returns the substring beginning with the character at the `start` index, up to
    (but not including) the character at the `end` index. Indexes are
    zero-based. Negative numbers will be counted back from the end of the
    string. If the `start` or `end` indexes are left blank, they will default to
    the start and end of the string respectively."""
))
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


@script_function(eval_args=False, documentation=N_(
    """`$getmulti(name,index,separator="; ")`

Gets the element at `index` from the multi-value tag `name`. A literal value
    representing a multi-value can be substituted for `name`, using the
    separator (or "; " if not passed) to coerce the value into a proper
    multi-valued tag."""
))
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
        multi_value = MultiValue(parser, multi, separator)
        return str(multi_value[index])
    except (ValueError, IndexError):
        return ''


@script_function(eval_args=False, documentation=N_(
    """`$foreach(name,code,separator="; ")`

Iterates over each element found in the multi-value tag `name`, executing
    `code`. For each loop, the element value is first stored in the tag
    `_loop_value` and the count is stored in the tag `_loop_count`. This allows
    the element or count value to be accessed within the `code` script. A
    literal value representing a multi-value can be substituted for `name`,
    using the separator (or "; " if not passed) to coerce the value into a
    proper multi-valued tag."""
))
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
    multi_value = MultiValue(parser, multi, separator)
    for loop_count, value in enumerate(multi_value, 1):
        func_set(parser, '_loop_count', str(loop_count))
        func_set(parser, '_loop_value', str(value))
        loop_code.eval(parser)
    func_unset(parser, '_loop_count')
    func_unset(parser, '_loop_value')
    return ''


@script_function(eval_args=False, documentation=N_(
    """`$while(condition,code)`

Standard 'while' loop. Executes `code` repeatedly until `condition` no longer
    evaluates to `True`. For each loop, the count is stored in the tag
    `_loop_count`. This allows the count value to be accessed within the `code`
    script. The function limites the maximum number of iterations to 1000 as a
    safeguard against accidentally creating an infinite loop."""
))
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


@script_function(eval_args=False, documentation=N_(
    """`$map(name,code,separator="; ")`

Iterates over each element found in the multi-value tag `name` and updates the
    value of the element to the value returned by `code`, returning the updated
    multi-value tag. For each loop, the element value is first stored in the tag
    `_loop_value` and the count is stored in the tag `_loop_count`. This allows
    the element or count value to be accessed within the `code` script."""
))
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
    multi_value = MultiValue(parser, multi, separator)
    for loop_count, value in enumerate(multi_value, 1):
        func_set(parser, '_loop_count', str(loop_count))
        func_set(parser, '_loop_value', str(value))
        multi_value[loop_count - 1] = str(loop_code.eval(parser))
    func_unset(parser, '_loop_count')
    func_unset(parser, '_loop_value')
    return str(multi_value)


@script_function(eval_args=False, documentation=N_(
    """`$join(name,text,separator="; ")`

Joins all elements in `name`, placing `text` between each element, and returns the result as a string."""
))
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
    multi_value = MultiValue(parser, multi, separator)
    return join_phrase.join(multi_value)


@script_function(eval_args=False, documentation=N_(
    """`$slice(name,start,end,separator="; ")`

Returns a multi-value variable containing the elements between the `start` and
    `end` indexes from the multi-value tag `name`. A literal value representing
    a multi-value can be substituted for `name`, using the separator (or "; " if
    not passed) to coerce the value into a proper multi-valued tag. Indexes are
    zero based. Negative numbers will be counted back from the end of the list.
    If the `start` or `end` indexes are left blank, they will default to the
    start and end of the list respectively.
For example, the following will create a multi-value variable with all artists
    in `%artists%` except the first, which can be used to create a "feat." list.
    `$setmulti(supporting_artists,$slice(%artists%,1,))`"""
))
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
    multi_value = MultiValue(parser, multi, separator)
    return multi_value.separator.join(multi_value[start:end])


@script_function(documentation=N_(
    """`$datetime(format="%Y-%m-%d %H:%M:%S")`

Returns the current date and time in the specified `format`, which is based on
    the standard Python `strftime` [format codes](https://strftime.org/). If no
    `format` is specified the date/time will be returned in the form
    `2020-02-05 14:26:32`.
Note: Platform-specific formatting codes should be avoided to help ensure the
    portability of scripts across the different platforms.  These codes include:
    remove zero-padding (e.g. `%-d` and `%-m` on Linux or macOS, and their
    equivalent `%#d` and `%#m` on Windows); element length specifiers (e.g.
    `%3Y`); and hanging '%' at the end of the format string."""
))
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
    try:
        return datetime.datetime.now(tz=local_tz).strftime(format)
    except ValueError:
        stackitem = parser._function_stack.get()
        raise ScriptRuntimeError(stackitem, "Unsupported format code")


@script_function(eval_args=False, documentation=N_(
    """`$sortmulti(name,separator="; ")`

Returns a copy of the multi-value tag `name` with the elements sorted in ascending order."""
))
def func_sortmulti(parser, multi, separator=MULTI_VALUED_JOINER):
    """Returns the supplied multi-value sorted in ascending order.

        parser: The ScriptParser object used to parse the script.
        multi: The ScriptVariable/Function that evaluates to a multi-value to be
            sorted.
        separator: A string or the ScriptVariable/Function that evaluates to the
            string used to separate the elements in the multi-value.

    Returns:
        Returns the supplied multi-value sorted in ascending order.
    """
    multi_value = MultiValue(parser, multi, separator)
    return multi_value.separator.join(sorted(multi_value))


@script_function(eval_args=False, documentation=N_(
    """`$reversemulti(name,separator="; ")`

Returns a copy of the multi-value tag `name` with the elements in reverse order.
    This can be used in conjunction with the `$sortmulti` function to sort in
    descending order."""
))
def func_reversemulti(parser, multi, separator=MULTI_VALUED_JOINER):
    """Returns the supplied multi-value in reverse order.

        parser: The ScriptParser object used to parse the script.
        multi: The ScriptVariable/Function that evaluates to a multi-value to be
            reversed.
        separator: A string or the ScriptVariable/Function that evaluates to the
            string used to separate the elements in the multi-value.

    Returns:
        Returns the supplied multi-value in reverse order.
    """
    multi_value = MultiValue(parser, multi, separator)
    return multi_value.separator.join(reversed(multi_value))
