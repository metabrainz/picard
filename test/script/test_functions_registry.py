#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Consistency checks between the documented signature and the registered
argument count of every script function."""

import re

from test.picardtestcase import PicardTestCase

from picard.extension_points.script_functions import ext_point_script_functions
from picard.script.functions import (
    NOTE_MULTI,
    NOTE_MULTI_NO_SEPARATOR,
    NOTE_NAME,
    NOTE_NEW_OLD,
)


CORE_MODULE = 'picard.script.functions'


# Functions whose implementation accepts fewer arguments than the signature
# documents: the missing arguments default to an empty string.
LENIENT_MINIMUM = {'firstalphachar', 'initials', 'len'}

SIGNATURE_RE = re.compile(r'^\$(?P<name>\w+)\((?P<args>.*)\)$', re.DOTALL)
ELLIPSIS = {'…', '...'}


def parse_signature(signature):
    """Return (name, required, optional, variadic) from a function signature.

    Every ``[`` in the signature introduces one optional argument.
    """
    match = SIGNATURE_RE.match(signature)
    if not match:
        raise ValueError(f"Unparsable signature: {signature!r}")
    args = match.group('args')
    required_part = args.split('[')[0]
    names = [name.strip() for name in required_part.split(',') if name.strip()]
    required = len([name for name in names if name not in ELLIPSIS])
    variadic = any(ellipsis in args for ellipsis in ELLIPSIS)
    return match.group('name'), required, args.count('['), variadic


class FunctionSignatureTest(PicardTestCase):
    def _functions(self):
        # Other tests may register extra functions, only check the core ones
        return sorted((name, item) for name, item in ext_point_script_functions if item.module == CORE_MODULE)

    def test_all_functions_have_signature_and_documentation(self):
        for name, item in self._functions():
            with self.subTest(function=name):
                self.assertTrue(item.signature)
                self.assertTrue(item.documentation)

    def test_signature_name_matches_function_name(self):
        for name, item in self._functions():
            with self.subTest(function=name):
                self.assertEqual(name, parse_signature(item.signature)[0])

    def test_signature_matches_registered_argument_count(self):
        for name, item in self._functions():
            with self.subTest(function=name):
                self.assertIsNotNone(item.argcount, "argument count is not checked")
                _, required, optional, variadic = parse_signature(item.signature)
                if variadic:
                    # Names such as "a1,a2,…" are examples of repeated arguments,
                    # so only the upper bound can be checked reliably.
                    self.assertIsNone(item.argcount.upper)
                    self.assertLessEqual(item.argcount.lower, required)
                    continue
                if name not in LENIENT_MINIMUM:
                    self.assertEqual(required, item.argcount.lower)
                self.assertEqual(required + optional, item.argcount.upper)


class FunctionArgumentNamingTest(PicardTestCase):
    """Argument names in signatures follow one convention, explained by a note.

    - `name`: a bare variable name, written without percent signs
    - `new`, `old`: bare variable names
    - `multi`: a multi-value, a variable (`%name%`) or a literal value
    """

    @staticmethod
    def _functions():
        return sorted((name, item) for name, item in ext_point_script_functions if item.module == CORE_MODULE)

    @staticmethod
    def _arguments(signature):
        args = SIGNATURE_RE.match(signature).group('args')
        return [arg.split('=')[0].strip(' ]') for arg in re.split(r'[\[,]', args) if arg.strip(' ]')]

    def test_signatures_do_not_contain_variables(self):
        # strftime formats such as %Y are fine, variables such as %x% are not
        for name, item in self._functions():
            with self.subTest(function=name):
                self.assertNotRegex(item.signature, r'%\w+%')

    def test_multi_argument_has_note(self):
        for name, item in self._functions():
            if 'multi' in self._arguments(item.signature):
                with self.subTest(function=name):
                    self.assertEqual(len(item.notes), 1)
                    self.assertIn(item.notes[0], {NOTE_MULTI, NOTE_MULTI_NO_SEPARATOR})
                    # The separator is only mentioned when there is one
                    self.assertEqual('separator' in self._arguments(item.signature), item.notes[0] == NOTE_MULTI)

    def test_name_argument_has_note(self):
        for name, item in self._functions():
            if 'name' in self._arguments(item.signature):
                with self.subTest(function=name):
                    self.assertEqual(item.notes, (NOTE_NAME,))

    def test_new_old_arguments_have_note(self):
        for name, item in self._functions():
            if {'new', 'old'}.issubset(self._arguments(item.signature)):
                with self.subTest(function=name):
                    self.assertEqual(item.notes, (NOTE_NEW_OLD,))

    def test_other_functions_have_no_note(self):
        for name, item in self._functions():
            if not {'name', 'multi', 'new', 'old'}.intersection(self._arguments(item.signature)):
                with self.subTest(function=name):
                    self.assertEqual(item.notes, ())
