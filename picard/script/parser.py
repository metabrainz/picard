# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2012 Lukáš Lalinský
# Copyright (C) 2007 Javier Kohen
# Copyright (C) 2008-2011, 2014-2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 stephen
# Copyright (C) 2012, 2014, 2017 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2016-2017 Ville Skyttä
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Calvin Walton
# Copyright (C) 2018 virusMac
# Copyright (C) 2020-2021 Bob Swift
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


from collections.abc import MutableSequence
from queue import LifoQueue
from typing import TYPE_CHECKING

from picard.extension_points import script_functions
from picard.metadata import (
    MULTI_VALUED_JOINER,
    Metadata,
)


if TYPE_CHECKING:
    from picard.file import File


class ScriptError(Exception):
    pass


class ScriptParseError(ScriptError):
    def __init__(self, stackitem, message):
        super().__init__(
            "{prefix:s}: {message:s}".format(
                prefix=str(stackitem),
                message=message,
            )
        )


class ScriptEndOfFile(ScriptParseError):
    def __init__(self, stackitem):
        super().__init__(
            stackitem,
            "Unexpected end of script",
        )


class ScriptSyntaxError(ScriptParseError):
    pass


class ScriptUnicodeError(ScriptSyntaxError):
    pass


class ScriptUnknownFunction(ScriptParseError):
    def __init__(self, stackitem):
        super().__init__(
            stackitem,
            "Unknown function '{name}'".format(name=stackitem.name),
        )


class ScriptRuntimeError(ScriptError):
    def __init__(self, stackitem, message='Unknown error'):
        super().__init__(
            "{prefix:s}: {message:s}".format(
                prefix=str(stackitem),
                message=message,
            ),
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
            return f"{self.line:d}:{self.column:d}"
        else:
            return f"{self.line:d}:{self.column:d}:{self.name}"


class ScriptText(str):
    def eval(self, state):
        return self


def normalize_tagname(name):
    if name.startswith('_'):
        return '~' + name[1:]
    return name


class ScriptVariable:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<ScriptVariable %%%s%%>" % self.name

    def eval(self, state):
        return state.context.get(normalize_tagname(self.name), "")


class ScriptFunction:
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
                        "Wrong number of arguments for $%s: Expected %s, got %i" % (name, expected, argcount),
                    )
        except KeyError:
            raise ScriptUnknownFunction(self.stackitem) from None

        self.name = name
        self.args = args

    def __repr__(self):
        return "<ScriptFunction $%s(%r)>" % (self.name, self.args)

    def eval(self, parser):
        try:
            function_registry_item = parser.functions[self.name]
        except KeyError:
            raise ScriptUnknownFunction(self.stackitem) from None

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
        return "".join(item.eval(state) for item in self)


def isidentif(ch):
    return ch.isalnum() or ch == '_'


class ScriptParser:
    r"""Tagger script parser.

    Grammar:
      unicodechar ::= '\u' [a-fA-F0-9]{4}
      text        ::= [^$%] | '\$' | '\%' | '\(' | '\)' | '\,' | unicodechar
      argtext     ::= [^$%(),] | '\$' | '\%' | '\(' | '\)' | '\,' | unicodechar
      identifier  ::= [a-zA-Z0-9_]
      variable    ::= '%' (identifier | ':')+ '%'
      function    ::= '$' (identifier)+ '(' (argument (',' argument)*)? ')'
      expression  ::= (variable | function | text)*
      argument    ::= (variable | function | argtext)*
    """

    _cache = {}

    def __init__(self):
        self._function_stack = LifoQueue()

    def __raise_eof(self):
        raise ScriptEndOfFile(StackItem(line=self._y, column=self._x))

    def __raise_char(self, ch):
        raise ScriptSyntaxError(StackItem(line=self._y, column=self._x), "Unexpected character '%s'" % ch)

    def __raise_unicode(self, ch):
        raise ScriptUnicodeError(StackItem(line=self._y, column=self._x), "Invalid unicode character '\\u%s'" % ch)

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

    def read_multi(self, count):
        text = ch = self.read()
        if not ch:
            self.__raise_eof()
        count -= 1
        while ch and count:
            ch = self.read()
            if not ch:
                self.__raise_eof()
            text += ch
            count -= 1
        return text

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
        column = self._x - 2  # Set x position to start of function name ($)
        line = self._y
        while True:
            ch = self.read()
            if ch == '(':
                name = self._text[start : self._pos - 1]
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
                return ScriptVariable(self._text[begin : self._pos - 1])
            elif ch is None:
                self.__raise_eof()
            elif not isidentif(ch) and ch != ':':
                self.__raise_char(ch)

    def parse_text(self, top):
        text = []
        while True:
            ch = self.read()
            if ch == "\\":
                text.append(self.parse_escape_sequence())
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

    def parse_escape_sequence(self):
        ch = self.read()
        if ch == 'n':
            return '\n'
        elif ch == 't':
            return '\t'
        elif ch == 'u':
            codepoint = self.read_multi(4)
            try:
                return chr(int(codepoint, 16))
            except (TypeError, ValueError):
                self.__raise_unicode(codepoint)
        elif ch is None:
            self.__raise_eof()
        elif ch not in "$%(),\\":
            self.__raise_char(ch)
        else:
            return ch

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
        self.functions = dict(script_functions.ext_point_script_functions)

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

    def eval(self, script: str, context: Metadata | None = None, file: 'File | None' = None):
        """Parse and evaluate the script."""
        self.context: Metadata = context if context is not None else Metadata()
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
        if self.separator == MULTI_VALUED_JOINER and len(multi) == 1 and isinstance(multi[0], ScriptVariable):
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
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.parser, self._multi, self.separator)

    def __str__(self):
        return self.separator.join(x for x in self if x)
