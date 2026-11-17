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
import picard.script.functions  # noqa: F401  # registers the core functions


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
