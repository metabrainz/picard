# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2010, 2014, 2018-2022 Philipp Wolfer
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013, 2017-2021 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017-2018, 2021 Wieland Hoffmann
# Copyright (C) 2018 virusMac
# Copyright (C) 2020-2022 Bob Swift
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


import datetime
import re
import unittest
from unittest import mock
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.cluster import Cluster
from picard.const.defaults import DEFAULT_FILE_NAMING_FORMAT
from picard.extension_points.script_functions import (
    FunctionRegistryItem,
    register_script_function,
    script_function,
)
from picard.metadata import (
    MULTI_VALUED_JOINER,
    Metadata,
)
from picard.plugin import ExtensionPoint
from picard.script import (
    MultiValue,
    ScriptEndOfFile,
    ScriptError,
    ScriptExpression,
    ScriptFunction,
    ScriptFunctionDocError,
    ScriptParser,
    ScriptRuntimeError,
    ScriptSyntaxError,
    ScriptUnicodeError,
    ScriptUnknownFunction,
    script_function_documentation,
    script_function_documentation_all,
)


try:
    from markdown import markdown
except ImportError:
    markdown = None


class _TestTimezone(datetime.tzinfo):
    def utcoffset(self, dt):
        # Set to GMT+2
        return datetime.timedelta(hours=2) + self.dst(dt)

    def dst(self, dt):
        d = datetime.datetime(dt.year, 4, 1)
        self.dston = d - datetime.timedelta(days=d.weekday() + 1)
        d = datetime.datetime(dt.year, 11, 1)
        self.dstoff = d - datetime.timedelta(days=d.weekday() + 1)
        if self.dston <= dt.replace(tzinfo=None) < self.dstoff:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(0)

    def tzname(self, dt):
        return "TZ Test"


class _DateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime.datetime(2020, 1, 2, hour=12, minute=34, second=56, microsecond=789, tzinfo=tz)

    def astimezone(self, tz=None):
        # Ignore tz passed to the method and force use of test timezone.
        tz = _TestTimezone()
        utc = (self - self.utcoffset()).replace(tzinfo=tz)
        # Convert from UTC to tz's local time.
        return tz.fromutc(utc)


class ScriptParserTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values({
            'enabled_plugins': '',
        })

        self.parser = ScriptParser()

        # ensure we start on clean registry
        ScriptParser._cache = {}

    def assertScriptResultEquals(self, script, expected, context=None, file=None):
        """Asserts that evaluating `script` returns `expected`.


        Args:
            script: The tagger script
            expected: The expected result
            context: A Metadata object with pre-set tags or None
        """
        actual = self.parser.eval(script, context=context, file=file)
        self.assertEqual(actual,
                         expected,
                         "'%s' evaluated to '%s', expected '%s'"
                         % (script, actual, expected))

    def test_function_registry_item(self):
        def somefunc():
            return 'x'
        item = FunctionRegistryItem(somefunc, 'x', 'y', 'doc')
        self.assertEqual(item.function, somefunc)
        self.assertEqual(item.eval_args, 'x')
        self.assertEqual(item.argcount, 'y')
        self.assertEqual(item.documentation, 'doc')

        regex = r'^'\
                + re.escape(r'FunctionRegistryItem(<function ')\
                + r'[^ ]+'\
                + re.escape(r'.somefunc at ')\
                + r'[^>]+'\
                + re.escape(r'>, x, y, """doc""")')\
                + r'$'

        self.assertRegex(repr(item), regex)

    def test_script_unicode_char(self):
        self.assertScriptResultEquals("\\u6e56", "湖")
        self.assertScriptResultEquals("foo\\u6e56bar", "foo湖bar")
        self.assertScriptResultEquals("\\uFFFF", "\uffff")

    def test_script_unicode_char_eof(self):
        areg = r"^\d+:\d+: Unexpected end of script"
        with self.assertRaisesRegex(ScriptEndOfFile, areg):
            self.parser.eval("\\u")
        with self.assertRaisesRegex(ScriptEndOfFile, areg):
            self.parser.eval("\\uaff")

    def test_script_unicode_char_err(self):
        areg = r"^\d+:\d+: Invalid unicode character '\\ufffg'"
        with self.assertRaisesRegex(ScriptUnicodeError, areg):
            self.parser.eval("\\ufffg")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_default(self):
        # test default decorator and default prefix
        @script_function()
        def func_somefunc(parser):
            return "x"
        self.assertScriptResultEquals("$somefunc()", "x")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_no_prefix(self):
        # function without prefix
        @script_function()
        def somefunc(parser):
            return "x"
        self.assertScriptResultEquals("$somefunc()", "x")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_arg(self):
        # function with argument
        @script_function()
        def somefunc(parser, arg):
            return arg

        @script_function()
        def title(parser, arg):
            return arg.upper()

        self.assertScriptResultEquals("$somefunc($title(x))", "X")
        areg = r"^\d+:\d+:\$somefunc: Wrong number of arguments for \$somefunc: Expected exactly 1"
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$somefunc()")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_argcount(self):
        # ignore argument count
        @script_function(check_argcount=False)
        def somefunc(parser, *arg):
            return str(len(arg))
        self.assertScriptResultEquals("$somefunc(a,b,c)", "3")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_altname(self):
        # alternative name
        @script_function(name="otherfunc")
        def somefunc4(parser):
            return "x"
        self.assertScriptResultEquals("$otherfunc()", "x")
        areg = r"^\d+:\d+:\$somefunc: Unknown function '\$somefunc'"
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$somefunc()")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_altprefix(self):
        # alternative prefix
        @script_function(prefix='theprefix_')
        def theprefix_somefunc(parser):
            return "x"
        self.assertScriptResultEquals("$somefunc()", "x")

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_decorator_eval_args(self):
        # disable argument evaluation
        @script_function(eval_args=False)
        def somefunc(parser, arg):
            return arg.eval(parser)

        @script_function()
        def title(parser, arg):
            return arg.upper()

        self.assertScriptResultEquals("$somefunc($title(x))", "X")

    @staticmethod
    def assertStartswith(text, expect):
        if not text.startswith(expect):
            raise AssertionError("do not start with %r but with %r" % (expect, text[:len(expect)]))

    @staticmethod
    def assertEndswith(text, expect):
        if not text.endswith(expect):
            raise AssertionError("do not end with %r but with %r" % (expect, text[-len(expect):]))

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_documentation_nodoc(self):
        """test script_function_documentation() with a function without documentation"""
        @script_function()
        def func_nodocfunc(parser):
            return ""

        doc = script_function_documentation('nodocfunc', 'markdown')
        self.assertEqual(doc, '')
        doc = script_function_documentation('nodocfunc', 'html')
        self.assertEqual(doc, '')

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_documentation(self):
        """test script_function_documentation() with a function with documentation"""
        # the documentation used to test includes backquotes
        testdoc = '`$somefunc()`'

        @script_function(documentation=testdoc)
        def func_somefunc(parser):
            return "x"

        doc = script_function_documentation('somefunc', 'markdown')
        self.assertEqual(doc, testdoc)
        areg = r"^no such documentation format: unknownformat"
        with self.assertRaisesRegex(ScriptFunctionDocError, areg):
            script_function_documentation('somefunc', 'unknownformat')

    @unittest.skipUnless(markdown, "markdown module missing")
    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_documentation_html(self):
        """test script_function_documentation() with a function with documentation"""
        # get html code as generated by markdown
        pre, post = markdown('`XXX`').split('XXX')

        # the documentation used to test includes backquotes
        testdoc = '`$somefunc()`'

        @script_function(documentation=testdoc)
        def func_somefunc(parser):
            return "x"

        doc = script_function_documentation('somefunc', 'html')
        self.assertEqual(doc, pre + '$somefunc()' + post)

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_documentation_unknown_function(self):
        """test script_function_documentation() with an unknown function"""
        areg = r"^no such function: unknownfunc"
        with self.assertRaisesRegex(ScriptFunctionDocError, areg):
            script_function_documentation('unknownfunc', 'html')

    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_documentation_all(self):
        """test script_function_documentation_all() with markdown format"""
        @script_function(documentation='somedoc2')
        def func_somefunc2(parser):
            return "x"

        @script_function(documentation='somedoc1')
        def func_somefunc1(parser):
            return "x"

        docall = script_function_documentation_all()
        self.assertEqual(docall, 'somedoc1\nsomedoc2')

    @unittest.skipUnless(markdown, "markdown module missing")
    @patch('picard.extension_points.script_functions.ext_point_script_functions', ExtensionPoint(label='test_script'))
    def test_script_function_documentation_all_html(self):
        """test script_function_documentation_all() with html format"""
        # get html code as generated by markdown
        pre, post = markdown('XXX').split('XXX')

        @script_function(documentation='somedoc')
        def func_somefunc(parser):
            return "x"

        def postprocessor(data, function):
            return 'w' + data + function.name + 'y'

        docall = script_function_documentation_all(
            fmt='html',
            pre='<div id="test">',
            post="</div>\n",
            postprocessor=postprocessor,
        )

        self.assertStartswith(docall, '<div id="test">w' + pre)
        self.assertEndswith(docall, post + 'somefuncy</div>\n')

    def test_unknown_function(self):
        areg = r"^\d+:\d+:\$unknownfunction: Unknown function '\$unknownfunction'"
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$unknownfunction()")

    def test_noname_function(self):
        areg = r"^\d+:\d+:\$: Unknown function '\$'"
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$()")

    def test_unexpected_end_of_script(self):
        areg = r"^\d+:\d+: Unexpected end of script"
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$noop(")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$")

    def test_unexpected_character(self):
        areg = r"^\d+:\d+: Unexpected character '\^'"
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$^noop()")

    def test_scriptfunction_unknown(self):
        parser = ScriptParser()
        parser.parse('')
        areg = r"^\d+:\d+:\$x: Unknown function '\$x'"
        with self.assertRaisesRegex(ScriptError, areg):
            ScriptFunction('x', '', parser)
        areg = r"^\d+:\d+:\$noop: Unknown function '\$noop'"
        with self.assertRaisesRegex(ScriptError, areg):
            f = ScriptFunction('noop', '', parser)
            del parser.functions['noop']
            f.eval(parser)

    def test_cmd_noop(self):
        self.assertScriptResultEquals("$noop()", "")
        self.assertScriptResultEquals("$noop(abcdefg)", "")

    def test_cmd_if(self):
        self.assertScriptResultEquals("$if(1,a,b)", "a")
        self.assertScriptResultEquals("$if(,a,b)", "b")

    def test_cmd_if2(self):
        self.assertScriptResultEquals("$if2(,a,b)", "a")
        self.assertScriptResultEquals("$if2($noop(),b)", "b")
        self.assertScriptResultEquals("$if2()", "")
        self.assertScriptResultEquals("$if2(,)", "")

    def test_cmd_left(self):
        self.assertScriptResultEquals("$left(abcd,2)", "ab")
        self.assertScriptResultEquals("$left(abcd,x)", "")

    def test_cmd_right(self):
        self.assertScriptResultEquals("$right(abcd,2)", "cd")
        self.assertScriptResultEquals("$right(abcd,x)", "")

    def test_cmd_set(self):
        context = Metadata()
        self.assertScriptResultEquals("$set(test,aaa)%test%", "aaa", context)
        self.assertEqual(context['test'], 'aaa')

    def test_cmd_set_empty(self):
        self.assertScriptResultEquals("$set(test,)%test%", "")

    def test_cmd_set_multi_valued(self):
        context = Metadata()
        context["source"] = ["multi", "valued"]
        self.parser.eval("$set(test,%source%)", context)
        self.assertEqual(context.getall("test"), ["multi; valued"])  # list has only a single value

    def test_cmd_setmulti_multi_valued(self):
        context = Metadata()
        context["source"] = ["multi", "valued"]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context))  # no return value
        self.assertEqual(context.getall("source"), context.getall("test"))

    def test_cmd_setmulti_multi_valued_wth_spaces(self):
        context = Metadata()
        context["source"] = ["multi, multi", "valued, multi"]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context))  # no return value
        self.assertEqual(context.getall("source"), context.getall("test"))

    def test_cmd_setmulti_not_multi_valued(self):
        context = Metadata()
        context["source"] = "multi, multi"
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context))  # no return value
        self.assertEqual(context.getall("source"), context.getall("test"))

    def test_cmd_setmulti_will_keep_empty_items(self):
        context = Metadata()
        context["source"] = ["", "multi", ""]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context))  # no return value
        self.assertEqual(["", "multi", ""], context.getall("test"))

    def test_cmd_setmulti_custom_splitter_string(self):
        context = Metadata()
        self.assertEqual("", self.parser.eval("$setmulti(test,multi##valued##test##,##)", context))  # no return value
        self.assertEqual(["multi", "valued", "test", ""], context.getall("test"))

    def test_cmd_setmulti_empty_splitter_does_nothing(self):
        context = Metadata()
        self.assertEqual("", self.parser.eval("$setmulti(test,multi; valued,)", context))  # no return value
        self.assertEqual(["multi; valued"], context.getall("test"))

    def test_cmd_get(self):
        context = Metadata()
        context["test"] = "aaa"
        self.assertScriptResultEquals("$get(test)", "aaa", context)
        context["test2"] = ["multi", "valued"]
        self.assertScriptResultEquals("$get(test2)", "multi; valued", context)

    def test_cmd_num(self):
        self.assertScriptResultEquals("$num(3,3)", "003")
        self.assertScriptResultEquals("$num(03,3)", "003")
        self.assertScriptResultEquals("$num(123,2)", "123")
        self.assertScriptResultEquals("$num(123,a)", "")
        self.assertScriptResultEquals("$num(a,2)", "00")
        self.assertScriptResultEquals("$num(123,-1)", "123")
        self.assertScriptResultEquals("$num(123,35)", "00000000000000000123")

    def test_cmd_or(self):
        self.assertScriptResultEquals("$or(,)", "")
        self.assertScriptResultEquals("$or(,,)", "")
        self.assertScriptResultEquals("$or(,q)", "1")
        self.assertScriptResultEquals("$or(q,)", "1")
        self.assertScriptResultEquals("$or(q,q)", "1")
        self.assertScriptResultEquals("$or(q,,)", "1")

    def test_cmd_and(self):
        self.assertScriptResultEquals("$and(,)", "")
        self.assertScriptResultEquals("$and(,q)", "")
        self.assertScriptResultEquals("$and(q,)", "")
        self.assertScriptResultEquals("$and(q,q,)", "")
        self.assertScriptResultEquals("$and(q,q)", "1")
        self.assertScriptResultEquals("$and(q,q,q)", "1")

    def test_cmd_not(self):
        self.assertScriptResultEquals("$not($noop())", "1")
        self.assertScriptResultEquals("$not(q)", "")

    def test_cmd_trim(self):
        self.assertScriptResultEquals("$trim( \\t test \\n )", "test")
        self.assertScriptResultEquals("$trim(test,t)", "es")
        self.assertScriptResultEquals("$trim(test,ts)", "e")

    def test_cmd_add(self):
        self.assertScriptResultEquals("$add(1,2)", "3")
        self.assertScriptResultEquals("$add(1,2,3)", "6")
        self.assertScriptResultEquals("$add(a,2)", "")
        self.assertScriptResultEquals("$add(2,a)", "")

    def test_cmd_sub(self):
        self.assertScriptResultEquals("$sub(1,2)", "-1")
        self.assertScriptResultEquals("$sub(2,1)", "1")
        self.assertScriptResultEquals("$sub(4,2,1)", "1")
        self.assertScriptResultEquals("$sub(a,2)", "")
        self.assertScriptResultEquals("$sub(2,a)", "")

    def test_cmd_div(self):
        self.assertScriptResultEquals("$div(9,3)", "3")
        self.assertScriptResultEquals("$div(10,3)", "3")
        self.assertScriptResultEquals("$div(30,3,3)", "3")
        self.assertScriptResultEquals("$div(30,0)", "")
        self.assertScriptResultEquals("$div(30,a)", "")

    def test_cmd_mod(self):
        self.assertScriptResultEquals("$mod(9,3)", "0")
        self.assertScriptResultEquals("$mod(10,3)", "1")
        self.assertScriptResultEquals("$mod(10,6,3)", "1")
        self.assertScriptResultEquals("$mod(a,3)", "")
        self.assertScriptResultEquals("$mod(10,a)", "")
        self.assertScriptResultEquals("$mod(10,0)", "")

    def test_cmd_mul(self):
        self.assertScriptResultEquals("$mul(9,3)", "27")
        self.assertScriptResultEquals("$mul(10,3)", "30")
        self.assertScriptResultEquals("$mul(2,5,3)", "30")
        self.assertScriptResultEquals("$mul(2,a)", "")
        self.assertScriptResultEquals("$mul(2,5,a)", "")

    def test_cmd_eq(self):
        self.assertScriptResultEquals("$eq(,)", "1")
        self.assertScriptResultEquals("$eq(,$noop())", "1")
        self.assertScriptResultEquals("$eq(,q)", "")
        self.assertScriptResultEquals("$eq(q,q)", "1")
        self.assertScriptResultEquals("$eq(q,)", "")

    def test_cmd_ne(self):
        self.assertScriptResultEquals("$ne(,)", "")
        self.assertScriptResultEquals("$ne(,$noop())", "")
        self.assertScriptResultEquals("$ne(,q)", "1")
        self.assertScriptResultEquals("$ne(q,q)", "")
        self.assertScriptResultEquals("$ne(q,)", "1")

    def test_cmd_lower(self):
        self.assertScriptResultEquals("$lower(AbeCeDA)", "abeceda")

    def test_cmd_upper(self):
        self.assertScriptResultEquals("$upper(AbeCeDA)", "ABECEDA")

    def test_cmd_pad(self):
        self.assertScriptResultEquals("$pad(abc de,10,-)", "----abc de")
        self.assertScriptResultEquals("$pad(abc de,e,-)", "")
        self.assertScriptResultEquals("$pad(abc de,6,-)", "abc de")
        self.assertScriptResultEquals("$pad(abc de,3,-)", "abc de")
        self.assertScriptResultEquals("$pad(abc de,0,-)", "abc de")
        self.assertScriptResultEquals("$pad(abc de,-3,-)", "abc de")

    def test_cmd_replace(self):
        self.assertScriptResultEquals("$replace(abc ab abd a,ab,test)", "testc test testd a")

    def test_cmd_replacemulti(self):
        context = Metadata()
        context["genre"] = ["Electronic", "Idm", "Techno"]
        self.assertScriptResultEquals("$replacemulti(%genre%,Idm,IDM)", "Electronic; IDM; Techno", context)

        context["genre"] = ["Electronic", "Jungle", "Bardcore"]
        self.assertScriptResultEquals("$replacemulti(%genre%,Bardcore,Hardcore)", "Electronic; Jungle; Hardcore", context)

        context["test"] = ["One", "Two", "Three"]
        self.assertScriptResultEquals("$replacemulti(%test%,Two,)", "One; Three", context)

        context["test"] = ["One", "Two", "Three"]
        self.assertScriptResultEquals("$replacemulti(%test%,Four,Five)", "One; Two; Three", context)

        context["test"] = ["Four", "Five", "Six"]
        self.assertScriptResultEquals("$replacemulti(%test%,Five,)", "Four; Six", context)

        self.assertScriptResultEquals("$replacemulti(a; b,,,)", "a; b")
        self.assertScriptResultEquals("$setmulti(foo,a; b)$replacemulti(%foo%,,,)", "a; b")

    def test_cmd_strip(self):
        self.assertScriptResultEquals("$strip(  \t abc  de \n f  )", "abc de f")

    def test_cmd_rreplace(self):
        self.assertScriptResultEquals(r'''$rreplace(test \(disc 1\),\\s\\\(disc \\d+\\\),)''', "test")
        self.assertScriptResultEquals(r'''$rreplace(test,[t,)''', "test")

    def test_cmd_rsearch(self):
        self.assertScriptResultEquals(r"$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\))", "1")
        self.assertScriptResultEquals(r"$rsearch(test \(disc 1\),\\\(disc \\d+\\\))", "(disc 1)")
        self.assertScriptResultEquals(r"$rsearch(test,x)", "")
        self.assertScriptResultEquals(r'''$rsearch(test,[t)''', "")

    def test_arguments(self):
        self.assertTrue(
            self.parser.eval(
                r"$set(bleh,$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\)))) $set(wer,1)"))

    def test_cmd_gt(self):
        # Test with default processing
        self.assertScriptResultEquals("$gt(10,4)", "1")
        self.assertScriptResultEquals("$gt(6,6)", "")
        self.assertScriptResultEquals("$gt(6,7)", "")
        self.assertScriptResultEquals("$gt(6.5,4)", "1")
        self.assertScriptResultEquals("$gt(6.5,4.5)", "1")
        self.assertScriptResultEquals("$gt(6.5,6.5)", "")
        self.assertScriptResultEquals("$gt(a,b)", "")
        self.assertScriptResultEquals("$gt(b,a)", "1")
        self.assertScriptResultEquals("$gt(a,6)", "1")
        self.assertScriptResultEquals("$gt(a,6.5)", "1")
        self.assertScriptResultEquals("$gt(6,a)", "")
        self.assertScriptResultEquals("$gt(6.5,a)", "")

        # Test with "int" processing
        self.assertScriptResultEquals("$gt(10,4,int)", "1")
        self.assertScriptResultEquals("$gt(6,4,int)", "1")
        self.assertScriptResultEquals("$gt(6.5,4,int)", "")
        self.assertScriptResultEquals("$gt(6,7,int)", "")
        self.assertScriptResultEquals("$gt(6,6,int)", "")
        self.assertScriptResultEquals("$gt(a,b,int)", "")

        # Test with "float" processing
        self.assertScriptResultEquals("$gt(1.2,1,float)", "1")
        self.assertScriptResultEquals("$gt(1.2,1.1,float)", "1")
        self.assertScriptResultEquals("$gt(1.2,1.3,float)", "")
        self.assertScriptResultEquals("$gt(1.2,1.2,float)", "")
        self.assertScriptResultEquals("$gt(a,b,float)", "")

        # Test date type arguments with "text" processing
        self.assertScriptResultEquals("$gt(2020-01-01,2020-01-02,text)", "")
        self.assertScriptResultEquals("$gt(2020-01-02,2020-01-01,text)", "1")
        self.assertScriptResultEquals("$gt(2020-01-01,2020-02,text)", "")
        self.assertScriptResultEquals("$gt(2020-02,2020-01-01,text)", "1")
        self.assertScriptResultEquals("$gt(2020-01-01,2020-01-01,text)", "")

        # Test text type arguments with "text" processing
        self.assertScriptResultEquals("$gt(abc,abcd,text)", "")
        self.assertScriptResultEquals("$gt(abcd,abc,text)", "1")
        self.assertScriptResultEquals("$gt(abc,ac,text)", "")
        self.assertScriptResultEquals("$gt(ac,abc,text)", "1")
        self.assertScriptResultEquals("$gt(abc,abc,text)", "")

        # Test with empty arguments (default processing)
        self.assertScriptResultEquals("$gt(,1)", "")
        self.assertScriptResultEquals("$gt(1,)", "1")
        self.assertScriptResultEquals("$gt(,)", "")

        # Test with empty arguments ("int" processing)
        self.assertScriptResultEquals("$gt(,1,int)", "")
        self.assertScriptResultEquals("$gt(1,,int)", "")
        self.assertScriptResultEquals("$gt(,,int)", "")

        # Test with empty arguments ("float" processing)
        self.assertScriptResultEquals("$gt(,1.1,float)", "")
        self.assertScriptResultEquals("$gt(1.1,float)", "")
        self.assertScriptResultEquals("$gt(,,float)", "")

        # Test with empty arguments ("text" processing)
        self.assertScriptResultEquals("$gt(,a,text)", "")
        self.assertScriptResultEquals("$gt(a,,text)", "1")
        self.assertScriptResultEquals("$gt(,,text)", "")

        # Test case sensitive arguments ("text" processing)
        self.assertScriptResultEquals("$gt(A,a,text)", "")
        self.assertScriptResultEquals("$gt(a,A,text)", "1")

        # Test case insensitive arguments ("nocase" processing)
        self.assertScriptResultEquals("$gt(a,B,nocase)", "")
        self.assertScriptResultEquals("$gt(A,b,nocase)", "")
        self.assertScriptResultEquals("$gt(B,a,nocase)", "1")
        self.assertScriptResultEquals("$gt(b,A,nocase)", "1")

        # Test unknown processing type
        self.assertScriptResultEquals("$gt(2,1,unknown)", "")

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$gt: Wrong number of arguments for \$gt: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$gt()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$gt(1)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$gt(foo,bar,text,)")

    def test_cmd_gte(self):
        # Test with default processing
        self.assertScriptResultEquals("$gte(10,9)", "1")
        self.assertScriptResultEquals("$gte(10,10)", "1")
        self.assertScriptResultEquals("$gte(10,11)", "")
        self.assertScriptResultEquals("$gte(10.1,10)", "1")
        self.assertScriptResultEquals("$gte(10.1,10.1)", "1")
        self.assertScriptResultEquals("$gte(10.1,10.2)", "")
        self.assertScriptResultEquals("$gte(a,b)", "")
        self.assertScriptResultEquals("$gte(b,a)", "1")
        self.assertScriptResultEquals("$gte(a,a)", "1")
        self.assertScriptResultEquals("$gte(a,6)", "1")
        self.assertScriptResultEquals("$gte(a,6.5)", "1")
        self.assertScriptResultEquals("$gte(6,a)", "")
        self.assertScriptResultEquals("$gte(6.5,a)", "")

        # Test with "int" processing
        self.assertScriptResultEquals("$gte(10,10.1,int)", "")
        self.assertScriptResultEquals("$gte(10,10,int)", "1")
        self.assertScriptResultEquals("$gte(10,4,int)", "1")
        self.assertScriptResultEquals("$gte(6,4,int)", "1")
        self.assertScriptResultEquals("$gte(6,7,int)", "")
        self.assertScriptResultEquals("$gte(a,b,int)", "")

        # Test with "float" processing
        self.assertScriptResultEquals("$gte(10.2,10.1,float)", "1")
        self.assertScriptResultEquals("$gte(10.2,10.2,float)", "1")
        self.assertScriptResultEquals("$gte(6,4,float)", "1")
        self.assertScriptResultEquals("$gte(10,10.1,float)", "")
        self.assertScriptResultEquals("$gte(10.2,10.3,float)", "")
        self.assertScriptResultEquals("$gte(6,7,float)", "")
        self.assertScriptResultEquals("$gte(a,b,float)", "")

        # Test date type arguments ("text" processing)
        self.assertScriptResultEquals("$gte(2020-01-01,2020-01-02,text)", "")
        self.assertScriptResultEquals("$gte(2020-01-02,2020-01-01,text)", "1")
        self.assertScriptResultEquals("$gte(2020-01-01,2020-02,text)", "")
        self.assertScriptResultEquals("$gte(2020-02,2020-01-01,text)", "1")
        self.assertScriptResultEquals("$gte(2020-01-01,2020-01-01,text)", "1")

        # Test text type arguments ("text" processing)
        self.assertScriptResultEquals("$gte(abc,abcd,text)", "")
        self.assertScriptResultEquals("$gte(abcd,abc,text)", "1")
        self.assertScriptResultEquals("$gte(abc,ac,text)", "")
        self.assertScriptResultEquals("$gte(ac,abc,text)", "1")
        self.assertScriptResultEquals("$gte(abc,abc,text)", "1")

        # Test with empty arguments (default processing)
        self.assertScriptResultEquals("$gte(,1)", "")
        self.assertScriptResultEquals("$gte(1,)", "1")
        self.assertScriptResultEquals("$gte(,)", "1")

        # Test with empty arguments ("int" processing)
        self.assertScriptResultEquals("$gte(,1,int)", "")
        self.assertScriptResultEquals("$gte(1,,int)", "")
        self.assertScriptResultEquals("$gte(,,int)", "")

        # Test with empty arguments ("float" processing)
        self.assertScriptResultEquals("$gte(,1,float)", "")
        self.assertScriptResultEquals("$gte(1,float)", "")
        self.assertScriptResultEquals("$gte(,,float)", "")

        # Test with empty arguments ("text" processing)
        self.assertScriptResultEquals("$gte(,a,text)", "")
        self.assertScriptResultEquals("$gte(a,,text)", "1")
        self.assertScriptResultEquals("$gte(,,text)", "1")

        # Test case sensitive arguments ("text" processing)
        self.assertScriptResultEquals("$gte(A,a,text)", "")
        self.assertScriptResultEquals("$gte(a,A,text)", "1")

        # Test case insensitive arguments ("nocase" processing)
        self.assertScriptResultEquals("$gte(a,B,nocase)", "")
        self.assertScriptResultEquals("$gte(A,b,nocase)", "")
        self.assertScriptResultEquals("$gte(B,a,nocase)", "1")
        self.assertScriptResultEquals("$gte(b,A,nocase)", "1")
        self.assertScriptResultEquals("$gte(a,A,nocase)", "1")
        self.assertScriptResultEquals("$gte(A,a,nocase)", "1")

        # Test unknown processing type
        self.assertScriptResultEquals("$gte(2,1,unknown)", "")

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$gte: Wrong number of arguments for \$gte: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$gte()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$gte(1)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$gte(foo,bar,text,)")

    def test_cmd_lt(self):
        # Test with default processing
        self.assertScriptResultEquals("$lt(10,4)", "")
        self.assertScriptResultEquals("$lt(6,6)", "")
        self.assertScriptResultEquals("$lt(6,7)", "1")
        self.assertScriptResultEquals("$lt(6.5,4)", "")
        self.assertScriptResultEquals("$lt(6.5,4.5)", "")
        self.assertScriptResultEquals("$lt(6.5,6.5)", "")
        self.assertScriptResultEquals("$lt(6.5,6.6)", "1")
        self.assertScriptResultEquals("$lt(a,b)", "1")
        self.assertScriptResultEquals("$lt(b,a)", "")
        self.assertScriptResultEquals("$lt(a,6)", "")
        self.assertScriptResultEquals("$lt(a,6.5)", "")
        self.assertScriptResultEquals("$lt(6,a)", "1")
        self.assertScriptResultEquals("$lt(6.5,a)", "1")

        # Test with "int" processing
        self.assertScriptResultEquals("$lt(4,6,int)", "1")
        self.assertScriptResultEquals("$lt(4,6.1,int)", "")
        self.assertScriptResultEquals("$lt(4,3,int)", "")
        self.assertScriptResultEquals("$lt(4,4.1,int)", "")
        self.assertScriptResultEquals("$lt(4.1,4.2,int)", "")
        self.assertScriptResultEquals("$lt(4,4,int)", "")
        self.assertScriptResultEquals("$lt(a,b,int)", "")

        # Test with "float" processing
        self.assertScriptResultEquals("$lt(4,4.1,float)", "1")
        self.assertScriptResultEquals("$lt(4.1,4.2,float)", "1")
        self.assertScriptResultEquals("$lt(4,6,float)", "1")
        self.assertScriptResultEquals("$lt(4.2,4.1,float)", "")
        self.assertScriptResultEquals("$lt(4.1,4.1,float)", "")
        self.assertScriptResultEquals("$lt(a,b,float)", "")

        # Test date type arguments ("text" processing)
        self.assertScriptResultEquals("$lt(2020-01-01,2020-01-02,text)", "1")
        self.assertScriptResultEquals("$lt(2020-01-02,2020-01-01,text)", "")
        self.assertScriptResultEquals("$lt(2020-01-01,2020-02,text)", "1")
        self.assertScriptResultEquals("$lt(2020-02,2020-01-01,text)", "")
        self.assertScriptResultEquals("$lt(2020-01-01,2020-01-01,text)", "")

        # Test text type arguments ("text" processing)
        self.assertScriptResultEquals("$lt(abc,abcd,text)", "1")
        self.assertScriptResultEquals("$lt(abcd,abc,text)", "")
        self.assertScriptResultEquals("$lt(abc,ac,text)", "1")
        self.assertScriptResultEquals("$lt(ac,abc,text)", "")
        self.assertScriptResultEquals("$lt(abc,abc,text)", "")

        # Test with empty arguments (default processing)
        self.assertScriptResultEquals("$lt(,1)", "1")
        self.assertScriptResultEquals("$lt(1,)", "")
        self.assertScriptResultEquals("$lt(,)", "")

        # Test with empty arguments ("int" processing)
        self.assertScriptResultEquals("$lt(,1,int)", "")
        self.assertScriptResultEquals("$lt(1,,int)", "")
        self.assertScriptResultEquals("$lt(,,int)", "")

        # Test with empty arguments ("float" processing)
        self.assertScriptResultEquals("$lt(,1,float)", "")
        self.assertScriptResultEquals("$lt(1,,float)", "")
        self.assertScriptResultEquals("$lt(,,float)", "")

        # Test with empty arguments ("text" processing)
        self.assertScriptResultEquals("$lt(,a,text)", "1")
        self.assertScriptResultEquals("$lt(a,,text)", "")
        self.assertScriptResultEquals("$lt(,,text)", "")

        # Test case sensitive arguments ("text" processing)
        self.assertScriptResultEquals("$lt(A,a,text)", "1")
        self.assertScriptResultEquals("$lt(a,A,text)", "")

        # Test case insensitive arguments ("nocase" processing)
        self.assertScriptResultEquals("$lt(a,B,nocase)", "1")
        self.assertScriptResultEquals("$lt(A,b,nocase)", "1")
        self.assertScriptResultEquals("$lt(B,a,nocase)", "")
        self.assertScriptResultEquals("$lt(b,A,nocase)", "")

        # Test unknown processing type
        self.assertScriptResultEquals("$lt(1,2,unknown)", "")

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$lt: Wrong number of arguments for \$lt: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$lt()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$lt(1)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$lt(foo,bar,text,)")

    def test_cmd_lte(self):
        # Test with default processing
        self.assertScriptResultEquals("$lte(10,4)", "")
        self.assertScriptResultEquals("$lte(6,6)", "1")
        self.assertScriptResultEquals("$lte(6,7)", "1")
        self.assertScriptResultEquals("$lte(6.5,4)", "")
        self.assertScriptResultEquals("$lte(6.5,4.5)", "")
        self.assertScriptResultEquals("$lte(6.5,6.5)", "1")
        self.assertScriptResultEquals("$lte(6.5,6.6)", "1")
        self.assertScriptResultEquals("$lte(a,b)", "1")
        self.assertScriptResultEquals("$lte(a,a)", "1")
        self.assertScriptResultEquals("$lte(b,a)", "")
        self.assertScriptResultEquals("$lte(a,6)", "")
        self.assertScriptResultEquals("$lte(a,6.5)", "")
        self.assertScriptResultEquals("$lte(6,a)", "1")
        self.assertScriptResultEquals("$lte(6.5,a)", "1")

        # Test with "int" processing
        self.assertScriptResultEquals("$lte(10,10,int)", "1")
        self.assertScriptResultEquals("$lte(10.1,10.2,int)", "")
        self.assertScriptResultEquals("$lte(4,10,int)", "1")
        self.assertScriptResultEquals("$lte(4,3,int)", "")
        self.assertScriptResultEquals("$lte(a,b,int)", "")

        # Test with "float" processing
        self.assertScriptResultEquals("$lte(10,10,float)", "1")
        self.assertScriptResultEquals("$lte(10.1,10.1,float)", "1")
        self.assertScriptResultEquals("$lte(10.1,10.2,float)", "1")
        self.assertScriptResultEquals("$lte(10.2,10.1,float)", "")
        self.assertScriptResultEquals("$lte(4,3,float)", "")
        self.assertScriptResultEquals("$lte(a,b,float)", "")

        # Test date type arguments ("text" processing)
        self.assertScriptResultEquals("$lte(2020-01-01,2020-01-02,text)", "1")
        self.assertScriptResultEquals("$lte(2020-01-02,2020-01-01,text)", "")
        self.assertScriptResultEquals("$lte(2020-01-01,2020-02,text)", "1")
        self.assertScriptResultEquals("$lte(2020-02,2020-01-01,text)", "")
        self.assertScriptResultEquals("$lte(2020-01-01,2020-01-01,text)", "1")

        # Test text type arguments ("text" processing)
        self.assertScriptResultEquals("$lte(abc,abcd,text)", "1")
        self.assertScriptResultEquals("$lte(abcd,abc,text)", "")
        self.assertScriptResultEquals("$lte(abc,ac,text)", "1")
        self.assertScriptResultEquals("$lte(ac,abc,text)", "")
        self.assertScriptResultEquals("$lte(abc,abc,text)", "1")

        # Test with empty arguments (default processing)
        self.assertScriptResultEquals("$lte(,1)", "1")
        self.assertScriptResultEquals("$lte(1,)", "")
        self.assertScriptResultEquals("$lte(,)", "1")

        # Test with empty arguments ("int" processing)
        self.assertScriptResultEquals("$lte(,1,int)", "")
        self.assertScriptResultEquals("$lte(1,,int)", "")
        self.assertScriptResultEquals("$lte(,,int)", "")

        # Test with empty arguments ("float" processing)
        self.assertScriptResultEquals("$lte(,1,float)", "")
        self.assertScriptResultEquals("$lte(1,,float)", "")
        self.assertScriptResultEquals("$lte(,,float)", "")

        # Test with empty arguments ("text" processing)
        self.assertScriptResultEquals("$lte(,a,text)", "1")
        self.assertScriptResultEquals("$lte(a,,text)", "")
        self.assertScriptResultEquals("$lte(,,text)", "1")

        # Test case sensitive arguments ("text" processing)
        self.assertScriptResultEquals("$lte(A,a,text)", "1")
        self.assertScriptResultEquals("$lte(a,A,text)", "")

        # Test case insensitive arguments ("nocase" processing)
        self.assertScriptResultEquals("$lte(a,B,nocase)", "1")
        self.assertScriptResultEquals("$lte(A,b,nocase)", "1")
        self.assertScriptResultEquals("$lte(B,a,nocase)", "")
        self.assertScriptResultEquals("$lte(b,A,nocase)", "")
        self.assertScriptResultEquals("$lte(a,A,nocase)", "1")
        self.assertScriptResultEquals("$lte(A,a,nocase)", "1")

        # Test unknown processing type
        self.assertScriptResultEquals("$lte(1,2,unknown)", "")

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$lte: Wrong number of arguments for \$lte: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$lte()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$lte(1)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$lte(foo,bar,text,)")

    def test_cmd_len(self):
        self.assertScriptResultEquals("$len(abcdefg)", "7")
        self.assertScriptResultEquals("$len(0)", "1")
        self.assertScriptResultEquals("$len()", "0")

    def test_cmd_firstalphachar(self):
        self.assertScriptResultEquals("$firstalphachar(abc)", "A")
        self.assertScriptResultEquals("$firstalphachar(Abc)", "A")
        self.assertScriptResultEquals("$firstalphachar(1abc)", "#")
        self.assertScriptResultEquals("$firstalphachar(...abc)", "#")
        self.assertScriptResultEquals("$firstalphachar(1abc,_)", "_")
        self.assertScriptResultEquals("$firstalphachar(...abc,_)", "_")
        self.assertScriptResultEquals("$firstalphachar()", "#")
        self.assertScriptResultEquals("$firstalphachar(,_)", "_")
        self.assertScriptResultEquals("$firstalphachar( abc)", "#")

    def test_cmd_initials(self):
        self.assertScriptResultEquals("$initials(Abc def Ghi)", "AdG")
        self.assertScriptResultEquals("$initials(Abc #def Ghi)", "AG")
        self.assertScriptResultEquals("$initials(Abc 1def Ghi)", "AG")
        self.assertScriptResultEquals("$initials(Abc)", "A")
        self.assertScriptResultEquals("$initials()", "")

    def test_cmd_firstwords(self):
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,11)", "Abc Def Ghi")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,12)", "Abc Def Ghi")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,7)", "Abc Def")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,8)", "Abc Def")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,6)", "Abc")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,0)", "")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,NaN)", "")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,)", "")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,-2)", "Abc Def")
        self.assertScriptResultEquals("$firstwords(Abc Def Ghi,-50)", "")

    def test_cmd_startswith(self):
        self.assertScriptResultEquals("$startswith(abc,a)", "1")
        self.assertScriptResultEquals("$startswith(abc,abc)", "1")
        self.assertScriptResultEquals("$startswith(abc,)", "1")
        self.assertScriptResultEquals("$startswith(abc,b)", "")
        self.assertScriptResultEquals("$startswith(abc,Ab)", "")

    def test_cmd_endswith(self):
        self.assertScriptResultEquals("$endswith(abc,c)", "1")
        self.assertScriptResultEquals("$endswith(abc,abc)", "1")
        self.assertScriptResultEquals("$endswith(abc,)", "1")
        self.assertScriptResultEquals("$endswith(abc,b)", "")
        self.assertScriptResultEquals("$endswith(abc,bC)", "")

    def test_cmd_truncate(self):
        self.assertScriptResultEquals("$truncate(abcdefg,0)", "")
        self.assertScriptResultEquals("$truncate(abcdefg,7)", "abcdefg")
        self.assertScriptResultEquals("$truncate(abcdefg,3)", "abc")
        self.assertScriptResultEquals("$truncate(abcdefg,10)", "abcdefg")
        self.assertScriptResultEquals("$truncate(abcdefg,)", "abcdefg")
        self.assertScriptResultEquals("$truncate(abcdefg,NaN)", "abcdefg")

    def test_cmd_copy(self):
        context = Metadata()
        tagsToCopy = ["tag1", "tag2"]
        context["source"] = tagsToCopy
        context["target"] = ["will", "be", "overwritten"]
        self.parser.eval("$copy(target,source)", context)
        self.assertEqual(self.parser.context.getall("target"), tagsToCopy)

    def _eval_and_check_copymerge(self, context, expected):
        self.parser.eval("$copymerge(target,source)", context)
        self.assertEqual(self.parser.context.getall("target"), expected)

    def test_cmd_copymerge_notarget(self):
        context = Metadata()
        tagsToCopy = ["tag1", "tag2"]
        context["source"] = tagsToCopy
        self._eval_and_check_copymerge(context, tagsToCopy)

    def test_cmd_copymerge_nosource(self):
        context = Metadata()
        target = ["tag1", "tag2"]
        context["target"] = target
        self._eval_and_check_copymerge(context, target)

    def test_cmd_copymerge_removedupes(self):
        context = Metadata()
        context["target"] = ["tag1", "tag2", "tag1"]
        context["source"] = ["tag2", "tag3", "tag2"]
        self._eval_and_check_copymerge(context, ["tag1", "tag2", "tag3"])

    def test_cmd_copymerge_nonlist(self):
        context = Metadata()
        context["target"] = "targetval"
        context["source"] = "sourceval"
        self._eval_and_check_copymerge(context, ["targetval", "sourceval"])

    def test_cmd_copymerge_empty_keepdupes(self):
        context = Metadata()
        context["target"] = ["tag1", "tag2", "tag1"]
        context["source"] = ["tag2", "tag3", "tag2"]
        self.parser.eval("$copymerge(target,source,)", context)
        self.assertEqual(self.parser.context.getall("target"), ["tag1", "tag2", "tag3"])

    def test_cmd_copymerge_keepdupes(self):
        context = Metadata()
        context["target"] = ["tag1", "tag2", "tag1"]
        context["source"] = ["tag2", "tag3", "tag2"]
        self.parser.eval("$copymerge(target,source,keep)", context)
        self.assertEqual(self.parser.context.getall("target"), ["tag1", "tag2", "tag1", "tag2", "tag3", "tag2"])

    def test_cmd_copymerge_nonlist_keepdupes(self):
        context = Metadata()
        context["target"] = "targetval"
        context["source"] = "targetval"
        self.parser.eval("$copymerge(target,source,keep)", context)
        self.assertEqual(self.parser.context.getall("target"), ["targetval", "targetval"])

    def test_cmd_eq_any(self):
        self.assertScriptResultEquals("$eq_any(abc,def,ghi,jkl)", "")
        self.assertScriptResultEquals("$eq_any(abc,def,ghi,jkl,abc)", "1")

    def test_cmd_ne_all(self):
        self.assertScriptResultEquals("$ne_all(abc,def,ghi,jkl)", "1")
        self.assertScriptResultEquals("$ne_all(abc,def,ghi,jkl,abc)", "")

    def test_cmd_eq_all(self):
        self.assertScriptResultEquals("$eq_all(abc,abc,abc,abc)", "1")
        self.assertScriptResultEquals("$eq_all(abc,abc,def,ghi)", "")

    def test_cmd_ne_any(self):
        self.assertScriptResultEquals("$ne_any(abc,abc,abc,abc)", "")
        self.assertScriptResultEquals("$ne_any(abc,abc,def,ghi)", "1")

    def test_cmd_title(self):
        self.assertScriptResultEquals("$title(abc Def g)", "Abc Def G")
        self.assertScriptResultEquals("$title(Abc Def G)", "Abc Def G")
        self.assertScriptResultEquals("$title(abc def g)", "Abc Def G")
        self.assertScriptResultEquals("$title(#1abc 4def - g)", "#1abc 4def - G")
        self.assertScriptResultEquals(r"$title(abcd \(efg hi jkl mno\))", "Abcd (Efg Hi Jkl Mno)")
        self.assertScriptResultEquals("$title(...abcd)", "...Abcd")
        self.assertScriptResultEquals("$title(a)", "A")
        self.assertScriptResultEquals("$title(’a)", "’a")
        self.assertScriptResultEquals("$title('a)", "'a")
        self.assertScriptResultEquals("$title(l'a)", "L'a")
        self.assertScriptResultEquals("$title(2'a)", "2'A")
        self.assertScriptResultEquals(r"$title(%empty%)", "")
        # Tests wrong number of arguments
        areg = r"^\d+:\d+:\$title: Wrong number of arguments for \$title: Expected exactly 1, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$title()")

    def test_cmd_swapprefix(self):
        self.assertScriptResultEquals("$swapprefix(A stitch in time)", "stitch in time, A")
        self.assertScriptResultEquals("$swapprefix(The quick brown fox)", "quick brown fox, The")
        self.assertScriptResultEquals("$swapprefix(How now brown cow)", "How now brown cow")
        self.assertScriptResultEquals("$swapprefix(When the red red robin)", "When the red red robin")
        self.assertScriptResultEquals("$swapprefix(A stitch in time,How,When,Who)", "A stitch in time")
        self.assertScriptResultEquals("$swapprefix(The quick brown fox,How,When,Who)", "The quick brown fox")
        self.assertScriptResultEquals("$swapprefix(How now brown cow,How,When,Who)", "now brown cow, How")
        self.assertScriptResultEquals("$swapprefix(When the red red robin,How,When,Who)", "the red red robin, When")

    def test_cmd_delprefix(self):
        self.assertScriptResultEquals("$delprefix(A stitch in time)", "stitch in time")
        self.assertScriptResultEquals("$delprefix(The quick brown fox)", "quick brown fox")
        self.assertScriptResultEquals("$delprefix(How now brown cow)", "How now brown cow")
        self.assertScriptResultEquals("$delprefix(When the red red robin)", "When the red red robin")
        self.assertScriptResultEquals("$delprefix(A stitch in time,How,When,Who)", "A stitch in time")
        self.assertScriptResultEquals("$delprefix(The quick brown fox,How,When,Who)", "The quick brown fox")
        self.assertScriptResultEquals("$delprefix(How now brown cow,How,When,Who)", "now brown cow")
        self.assertScriptResultEquals("$delprefix(When the red red robin,How,When,Who)", "the red red robin")

    def test_default_filenaming(self):
        context = Metadata()
        context['albumartist'] = 'albumartist'
        context['artist'] = 'artist'
        context['album'] = 'album'
        context['totaldiscs'] = 2
        context['discnumber'] = 1
        context['tracknumber'] = 8
        context['title'] = 'title'
        result = self.parser.eval(DEFAULT_FILE_NAMING_FORMAT, context)
        self.assertEqual(result, 'albumartist/\nalbum/\n1-08 title')
        context['~multiartist'] = '1'
        result = self.parser.eval(DEFAULT_FILE_NAMING_FORMAT, context)
        self.assertEqual(result, 'albumartist/\nalbum/\n1-08 artist - title')

    def test_default_NAT_filenaming(self):
        context = Metadata()
        context['artist'] = 'artist'
        context['album'] = '[standalone recordings]'
        context['title'] = 'title'
        result = self.parser.eval(DEFAULT_FILE_NAMING_FORMAT, context)
        self.assertEqual(result, 'artist/\n\ntitle')

    def test_cmd_with_not_arguments(self):
        def func_noargstest(parser):
            return ""

        register_script_function(func_noargstest, "noargstest")
        self.parser.eval("$noargstest()")

    def test_cmd_with_wrong_argcount_or(self):
        # $or() requires at least 2 arguments
        areg = r"^\d+:\d+:\$or: Wrong number of arguments for \$or: Expected at least 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval('$or(0)')

    def test_cmd_with_wrong_argcount_eq(self):
        # $eq() requires exactly 2 arguments
        areg = r"^\d+:\d+:\$eq: Wrong number of arguments for \$eq: Expected exactly 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval('$eq(0)')
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval('$eq(0,0,0)')

    def test_cmd_with_wrong_argcount_if(self):
        areg = r"^\d+:\d+:\$if: Wrong number of arguments for \$if: Expected between 2 and 3, "
        # $if() requires 2 or 3 arguments
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval('$if(1)')
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval('$if(1,a,b,c)')

    def test_cmd_unset_simple(self):
        context = Metadata()
        context['title'] = 'Foo'
        context['album'] = 'Foo'
        context['artist'] = 'Foo'
        self.parser.eval("$unset(album)", context)
        self.assertNotIn('album', context)

    def test_cmd_unset_prefix(self):
        context = Metadata()
        context['title'] = 'Foo'
        context['~rating'] = '4'
        self.parser.eval("$unset(_rating)", context)
        self.assertNotIn('~rating', context)

    def test_cmd_unset_multi(self):
        context = Metadata()
        context['performer:foo'] = 'Foo'
        context['performer:bar'] = 'Foo'
        self.parser.eval("$unset(performer:*)", context)
        self.assertNotIn('performer:bar', context)
        self.assertNotIn('performer:foo', context)

    def test_cmd_unset(self):
        context = Metadata()
        context['title'] = 'Foo'
        self.parser.eval("$unset(title)", context)
        self.assertNotIn('title', context)
        self.assertNotIn('title', context.deleted_tags)

    def test_cmd_delete(self):
        context = Metadata()
        context['title'] = 'Foo'
        self.parser.eval("$delete(title)", context)
        self.assertNotIn('title', context)
        self.assertIn('title', context.deleted_tags)

    def test_cmd_inmulti(self):
        context = Metadata()

        # Test with single-value string
        context["foo"] = "First:A; Second:B; Third:C"
        # Tests with $in for comparison purposes
        self.assertScriptResultEquals("$in(%foo%,Second:B)", "1", context)
        self.assertScriptResultEquals("$in(%foo%,irst:A; Second:B; Thi)", "1", context)
        self.assertScriptResultEquals("$in(%foo%,First:A; Second:B; Third:C)", "1", context)
        # Base $inmulti tests
        self.assertScriptResultEquals("$inmulti(%foo%,Second:B)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,irst:A; Second:B; Thi)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,First:A; Second:B; Third:C)", "1", context)
        # Test separator override but with existing separator - results should be same as base
        self.assertScriptResultEquals("$inmulti(%foo%,Second:B,; )", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,irst:A; Second:B; Thi,; )", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,First:A; Second:B; Third:C,; )", "1", context)
        # Test separator override
        self.assertScriptResultEquals("$inmulti(%foo%,First:A,:)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,Second:B,:)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,Third:C,:)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,First,:)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,A; Second,:)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,B; Third,:)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,C,:)", "1", context)
        # Test no separator
        self.assertScriptResultEquals("$inmulti(%foo%,First:A; Second:B; Third:C,)", "1", context)

        # Test with multi-values
        context["foo"] = ["First:A", "Second:B", "Third:C"]
        # Tests with $in for comparison purposes
        self.assertScriptResultEquals("$in(%foo%,Second:B)", "1", context)
        self.assertScriptResultEquals("$in(%foo%,irst:A; Second:B; Thi)", "1", context)
        self.assertScriptResultEquals("$in(%foo%,First:A; Second:B; Third:C)", "1", context)
        # Base $inmulti tests
        self.assertScriptResultEquals("$inmulti(%foo%,Second:B)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,irst:A; Second:B; Thi)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,First:A; Second:B; Third:C)", "", context)
        # Test separator override but with existing separator - results should be same as base
        self.assertScriptResultEquals("$inmulti(%foo%,Second:B,; )", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,irst:A; Second:B; Thi,; )", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,First:A; Second:B; Third:C,; )", "", context)
        # Test separator override
        self.assertScriptResultEquals("$inmulti(%foo%,First:A,:)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,Second:B,:)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,Third:C,:)", "", context)
        self.assertScriptResultEquals("$inmulti(%foo%,First,:)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,A; Second,:)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,B; Third,:)", "1", context)
        self.assertScriptResultEquals("$inmulti(%foo%,C,:)", "1", context)
        # Test no separator
        self.assertScriptResultEquals("$inmulti(%foo%,First:A; Second:B; Third:C,)", "1", context)

    def test_cmd_lenmulti(self):
        context = Metadata()
        context["foo"] = "First:A; Second:B; Third:C"
        context["bar"] = ["First:A", "Second:B", "Third:C"]
        # Tests with $len for comparison purposes
        self.assertScriptResultEquals("$len(%foo%)", "26", context)
        self.assertScriptResultEquals("$len(%bar%)", "26", context)
        # Base $lenmulti tests
        self.assertScriptResultEquals("$lenmulti(%foo%)", "1", context)
        self.assertScriptResultEquals("$lenmulti(%bar%)", "3", context)
        self.assertScriptResultEquals("$lenmulti(%foo%.)", "3", context)
        # Test separator override but with existing separator - results should be same as base
        self.assertScriptResultEquals("$lenmulti(%foo%,; )", "1", context)
        self.assertScriptResultEquals("$lenmulti(%bar%,; )", "3", context)
        self.assertScriptResultEquals("$lenmulti(%foo%.,; )", "3", context)
        # Test separator override
        self.assertScriptResultEquals("$lenmulti(%foo%,:)", "4", context)
        self.assertScriptResultEquals("$lenmulti(%bar%,:)", "4", context)
        self.assertScriptResultEquals("$lenmulti(%foo%.,:)", "4", context)
        # Test no separator
        self.assertScriptResultEquals("$lenmulti(%foo%,)", "1", context)
        self.assertScriptResultEquals("$lenmulti(%bar%,)", "1", context)
        # Test blank name
        context["baz"] = ""
        self.assertScriptResultEquals("$lenmulti(%baz%)", "0", context)
        self.assertScriptResultEquals("$lenmulti(%baz%,:)", "0", context)
        # Test empty multi-value
        context["baz"] = []
        self.assertScriptResultEquals("$lenmulti(%baz%)", "0", context)
        self.assertScriptResultEquals("$lenmulti(%baz%,:)", "0", context)
        # Test empty multi-value elements
        context["baz"] = ["one", "", "three"]
        self.assertScriptResultEquals("$lenmulti(%baz%)", "3", context)
        # Test missing name
        self.assertScriptResultEquals("$lenmulti(,)", "0", context)
        self.assertScriptResultEquals("$lenmulti(,:)", "0", context)

    def test_cmd_performer(self):
        context = Metadata()
        context['performer:guitar'] = 'Foo1'
        context['performer:rhythm-guitar'] = ['Foo2', 'Foo3']
        context['performer:drums'] = 'Drummer'
        # Matches pattern
        result = self.parser.eval("$performer(guitar)", context=context)
        self.assertEqual({'Foo1', 'Foo2', 'Foo3'}, set(result.split(', ')))
        # Empty pattern returns all performers
        result = self.parser.eval("$performer()", context=context)
        self.assertEqual({'Foo1', 'Foo2', 'Foo3', 'Drummer'}, set(result.split(', ')))
        self.assertScriptResultEquals("$performer(perf)", "", context)

    def test_cmd_performer_regex(self):
        context = Metadata()
        context['performer:guitar'] = 'Foo1'
        context['performer:guitars'] = 'Foo2'
        context['performer:rhythm-guitar'] = 'Foo3'
        context['performer:drums (drum kit)'] = 'Drummer'
        result = self.parser.eval(r"$performer(/^guitar/)", context=context)
        self.assertEqual({'Foo1', 'Foo2'}, set(result.split(', ')))
        result = self.parser.eval(r"$performer(/^guitar\$/)", context=context)
        self.assertEqual({'Foo1'}, set(result.split(', ')))

    def test_cmd_performer_regex_invalid(self):
        context = Metadata()
        context['performer:drums (drum kit)'] = 'Drummer'
        self.assertScriptResultEquals(r"$performer(/drums \(/)", "", context)
        self.assertScriptResultEquals(r"$performer(drums \()", "Drummer", context)

    def test_cmd_performer_regex_ignore_case(self):
        context = Metadata()
        context['performer:guitar'] = 'Foo1'
        context['performer:GUITARS'] = 'Foo2'
        context['performer:rhythm-guitar'] = 'Foo3'
        result = self.parser.eval(r"$performer(/^guitars?/i)", context=context)
        self.assertEqual({'Foo1', 'Foo2'}, set(result.split(', ')))

    def test_cmd_performer_custom_join(self):
        context = Metadata()
        context['performer:guitar'] = 'Foo1'
        context['performer:rhythm-guitar'] = 'Foo2'
        context['performer:drums'] = 'Drummer'
        result = self.parser.eval("$performer(guitar, / )", context=context)
        self.assertEqual({'Foo1', 'Foo2'}, set(result.split(' / ')))

    def test_cmd_performer_multi_colons(self):
        context = Metadata()
        context['performer:CV:松井栞里'] = '仁奈(CV:大出千夏)'
        result = self.parser.eval("$performer(CV:松井栞里)", context=context)
        self.assertEqual('仁奈(CV:大出千夏)', result)

    def test_cmd_matchedtracks(self):
        file = MagicMock()
        file.parent_item.album.get_num_matched_tracks.return_value = 42
        self.assertScriptResultEquals("$matchedtracks()", "42", file=file)
        self.assertScriptResultEquals("$matchedtracks()", "0")
        # The following only is possible for backward compatibility, arg is unused
        self.assertScriptResultEquals("$matchedtracks(arg)", "0")

    def test_cmd_matchedtracks_with_cluster(self):
        file = MagicMock()
        cluster = Cluster(name="Test")
        cluster.files.append(file)
        file.parent_item = cluster
        self.assertScriptResultEquals("$matchedtracks()", "0", file=file)

    def test_cmd_is_complete(self):
        file = MagicMock()
        file.parent_item.album.is_complete.return_value = True
        self.assertScriptResultEquals("$is_complete()", "1", file=file)
        file.parent_item.album.is_complete.return_value = False
        self.assertScriptResultEquals("$is_complete()", "", file=file)
        self.assertScriptResultEquals("$is_complete()", "")

    def test_cmd_is_complete_with_cluster(self):
        file = MagicMock()
        cluster = Cluster(name="Test")
        cluster.files.append(file)
        file.parent_item = cluster
        self.assertScriptResultEquals("$is_complete()", "", file=file)

    def test_cmd_is_video(self):
        context = Metadata({'~video': '1'})
        self.assertScriptResultEquals("$is_video()", "1", context=context)
        context = Metadata({'~video': '0'})
        self.assertScriptResultEquals("$is_video()", "", context=context)
        self.assertScriptResultEquals("$is_video()", "")

    def test_cmd_is_audio(self):
        context = Metadata({'~video': '1'})
        self.assertScriptResultEquals("$is_audio()", "", context=context)
        context = Metadata({'~video': '0'})
        self.assertScriptResultEquals("$is_audio()", "1", context=context)
        self.assertScriptResultEquals("$is_audio()", "1")

    def test_required_kwonly_parameters(self):
        def func(a, *, required_kwarg):
            pass

        with self.assertRaises(TypeError,
                               msg="Functions with required keyword-only parameters are not supported"):
            register_script_function(func)

    @staticmethod
    def test_optional_kwonly_parameters():
        def func(a, *, optional_kwarg=1):
            pass
        register_script_function(func)

    def test_char_escape(self):
        self.assertScriptResultEquals(r"\n\t\$\%\(\)\,\\", "\n\t$%(),\\")

    def test_char_escape_unexpected_char(self):
        self.assertRaises(ScriptSyntaxError, self.parser.eval, r'\x')

    def test_char_escape_end_of_file(self):
        self.assertRaises(ScriptEndOfFile, self.parser.eval, 'foo\\')

    def test_raise_unknown_function(self):
        self.assertRaises(ScriptUnknownFunction, self.parser.eval, '$unknownfn()')

    def test_raise_end_of_file(self):
        self.assertRaises(ScriptEndOfFile, self.parser.eval, '$noop(')
        self.assertRaises(ScriptEndOfFile, self.parser.eval, '%var')

    def test_raise_syntax_error(self):
        self.assertRaises(ScriptSyntaxError, self.parser.eval, '%var()%')
        self.assertRaises(ScriptSyntaxError, self.parser.eval, '$noop(()')
        self.assertRaises(ScriptSyntaxError, self.parser.eval, r'\x')

    def test_cmd_find(self):
        context = Metadata()
        context["foo"] = "First:A; Second:B; Third:C"
        context["bar"] = ["First:A", "Second:B", "Third:C"]
        context["baz"] = "Second"
        context["err"] = "Forth"
        # Tests with context
        self.assertScriptResultEquals("$find(%foo%,%baz%)", "9", context)
        self.assertScriptResultEquals("$find(%bar%,%baz%)", "9", context)
        self.assertScriptResultEquals("$find(%foo%,%bar%)", "0", context)
        self.assertScriptResultEquals("$find(%bar%,%foo%)", "0", context)
        self.assertScriptResultEquals("$find(%foo%,%err%)", "", context)
        # Tests with static input
        self.assertScriptResultEquals("$find(abcdef,c)", "2", context)
        self.assertScriptResultEquals("$find(abcdef,cd)", "2", context)
        self.assertScriptResultEquals("$find(abcdef,g)", "", context)
        # Tests ends of string
        self.assertScriptResultEquals("$find(abcdef,a)", "0", context)
        self.assertScriptResultEquals("$find(abcdef,ab)", "0", context)
        self.assertScriptResultEquals("$find(abcdef,f)", "5", context)
        self.assertScriptResultEquals("$find(abcdef,ef)", "4", context)
        # Tests case sensitivity
        self.assertScriptResultEquals("$find(abcdef,C)", "", context)
        # Tests no characters processed as wildcards
        self.assertScriptResultEquals("$find(abcdef,.f)", "", context)
        self.assertScriptResultEquals("$find(abcdef,?f)", "", context)
        self.assertScriptResultEquals("$find(abcdef,*f)", "", context)
        self.assertScriptResultEquals("$find(abc.ef,cde)", "", context)
        self.assertScriptResultEquals("$find(abc?ef,cde)", "", context)
        self.assertScriptResultEquals("$find(abc*ef,cde)", "", context)
        # Tests missing inputs
        self.assertScriptResultEquals("$find(,c)", "", context)
        self.assertScriptResultEquals("$find(abcdef,)", "0", context)
        # Tests wrong number of arguments
        areg = r"^\d+:\d+:\$find: Wrong number of arguments for \$find: Expected exactly 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$find(abcdef)")

    def test_cmd_reverse(self):
        context = Metadata()
        context["foo"] = "One; Two; Three"
        context["bar"] = ["One", "Two", "Three"]
        # Tests with context
        self.assertScriptResultEquals("$reverse(%foo%)", "eerhT ;owT ;enO", context)
        self.assertScriptResultEquals("$reverse(%bar%)", "eerhT ;owT ;enO", context)
        # Tests with static input
        self.assertScriptResultEquals("$reverse(One; Two; Three)", "eerhT ;owT ;enO", context)
        # Tests with missing input
        areg = r"^\d+:\d+:\$reverse: Wrong number of arguments for \$reverse: Expected exactly 1, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$reverse()")

    def test_cmd_substr(self):
        context = Metadata()
        context["foo"] = "One; Two; Three"
        context["bar"] = ["One", "Two", "Three"]
        context["start"] = '5'
        context["end"] = '9'
        # Tests with context
        self.assertScriptResultEquals("$substr(%foo%,%start%,%end%)", "Two;", context)
        self.assertScriptResultEquals("$substr(%bar%,%start%,%end%)", "Two;", context)
        # Tests with static input
        self.assertScriptResultEquals("$substr(One; Two; Three,5,9)", "Two;", context)
        # Tests ends of string
        self.assertScriptResultEquals("$substr(One; Two; Three,0,4)", "One;", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,10,15)", "Three", context)
        # Tests negative index inputs
        self.assertScriptResultEquals("$substr(One; Two; Three,-15,4)", "One;", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,-5,15)", "Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,-10,8)", "Two", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,5,-7)", "Two", context)
        # Tests overrun ends of string
        self.assertScriptResultEquals("$substr(One; Two; Three,10,25)", "Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,-25,4)", "One;", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,-5,25)", "Three", context)
        # Tests invalid ranges (end < start, end = start)
        self.assertScriptResultEquals("$substr(One; Two; Three,10,9)", "", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,10,10)", "", context)
        # Tests invalid index inputs
        self.assertScriptResultEquals("$substr(One; Two; Three,10-1,4)", "One;", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,10,4+2)", "Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,10-1,4+2)", "One; Two; Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,a,4)", "One;", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,0,b)", "One; Two; Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,a,b)", "One; Two; Three", context)
        # # Tests with missing input
        self.assertScriptResultEquals("$substr(One; Two; Three,,4)", "One;", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,10)", "Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,10,)", "Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,)", "One; Two; Three", context)
        self.assertScriptResultEquals("$substr(One; Two; Three,,)", "One; Two; Three", context)
        # Tests with missing input
        areg = r"^\d+:\d+:\$substr: Wrong number of arguments for \$substr: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$substr()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$substr(abc)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$substr(abc,0,,)")

    def test_cmd_getmulti(self):
        context = Metadata()
        context["foo"] = ["First:A", "Second:B", "Third:C"]
        context["index"] = "1"
        # Tests with context
        self.assertScriptResultEquals("$getmulti(%foo%,%index%)", "Second:B", context)
        # Tests with static inputs
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,0)", "First:A", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,1)", "Second:B", context)
        # Tests separator override
        self.assertScriptResultEquals("$getmulti(%foo%,1,:)", "A; Second", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,1,:)", "A; Second", context)
        # Tests negative index values
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,-1)", "Third:C", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,-2)", "Second:B", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,-3)", "First:A", context)
        # Tests out of range index values
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,10)", "", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,-4)", "", context)
        # Tests invalid index values
        self.assertScriptResultEquals("$getmulti(,0)", "", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,)", "", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,10+1)", "", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,a)", "", context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$getmulti(,0)", "", context)
        self.assertScriptResultEquals("$getmulti(First:A; Second:B; Third:C,)", "", context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$getmulti: Wrong number of arguments for \$getmulti: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$getmulti()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$getmulti(abc)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$getmulti(abc,0,; ,extra)")

    def test_cmd_foreach(self):
        context = Metadata()
        context["foo"] = "First:A; Second:B; Third:C"
        context["bar"] = ["First:A", "Second:B", "Third:C"]
        foo_output = "Output: 1=First:A; Second:B; Third:C"
        loop_output = "Output: 1=First:A 2=Second:B 3=Third:C"
        alternate_output = "Output: 1=First 2=A; Second 3=B; Third 4=C"
        # Tests with context
        context["output"] = "Output:"
        self.assertScriptResultEquals("$foreach(%foo%,$set(output,%output% %_loop_count%=%_loop_value%))%output%", foo_output, context)
        context["output"] = "Output:"
        self.assertScriptResultEquals("$foreach(%bar%,$set(output,%output% %_loop_count%=%_loop_value%))%output%", loop_output, context)
        # Tests with static inputs
        context["output"] = "Output:"
        self.assertScriptResultEquals("$foreach(First:A; Second:B; Third:C,$set(output,%output% %_loop_count%=%_loop_value%))%output%", loop_output, context)
        # Tests with missing inputs
        context["output"] = "Output:"
        self.assertScriptResultEquals("$foreach(,$set(output,%output% %_loop_count%=%_loop_value%))%output%", "Output:", context)
        context["output"] = "Output:"
        self.assertScriptResultEquals("$foreach(First:A; Second:B; Third:C,)%output%", "Output:", context)
        # Tests with separator override
        context["output"] = "Output:"
        self.assertScriptResultEquals("$foreach(First:A; Second:B; Third:C,$set(output,%output% %_loop_count%=%_loop_value%),:)%output%", alternate_output, context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$foreach: Wrong number of arguments for \$foreach: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$foreach()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$foreach(abc;def)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$foreach(abc:def,$noop(),:,extra)")

    def test_cmd_while(self):
        context = Metadata()
        context["max_value"] = '5'
        loop_output = "Output: 1 2 3 4 5"
        # Tests with context
        context["output"] = "Output:"
        self.assertScriptResultEquals("$set(_loop_count,1)$while($lt(%_loop_count%,%max_value%,int),$set(output,%output% %_loop_count%))%output%", loop_output, context)
        # Tests with static inputs
        context["output"] = "Output:"
        self.assertScriptResultEquals("$set(_loop_count,1)$while($lt(%_loop_count%,5,int),$set(output,%output% %_loop_count%))%output%", loop_output, context)
        # Tests with invalid conditional input
        context["output"] = "Output:"
        self.assertScriptResultEquals("$while($lt(%_loop_count%,5,int),$set(output,%output% %_loop_count%))%output%", "Output:", context)
        # Tests with forced conditional (runaway condition)
        context["output"] = "Output:"
        self.assertScriptResultEquals("$while(1,$set(output,%output% %_loop_count%))$right(%output%,4)", "1000", context)
        context["output"] = "Output:"
        self.assertScriptResultEquals("$while(0,$set(output,%output% %_loop_count%))$right(%output%,4)", "1000", context)
        # Tests with missing inputs
        context["output"] = "Output:"
        self.assertScriptResultEquals("$while($lt(%_loop_count%,5,int),)%output%", "Output:", context)
        context["output"] = "Output:"
        self.assertScriptResultEquals("$while(,$set(output,%output% %_loop_count%))%output%", "Output:", context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$while: Wrong number of arguments for \$while: Expected exactly 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$while()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$while(a)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$while(a,$noop(),extra)")

    def test_cmd_map(self):
        context = Metadata()
        foo_output = "1=FIRST:A; SECOND:B; THIRD:C"
        loop_output = "1=FIRST:A; 2=SECOND:B; 3=THIRD:C"
        alternate_output = "1=FIRST:2=A; SECOND:3=B; THIRD:4=C"
        # Tests with context
        context["foo"] = "First:A; Second:B; Third:C"
        self.assertScriptResultEquals("$map(%foo%,$upper(%_loop_count%=%_loop_value%))", foo_output, context)
        context["bar"] = ["First:A", "Second:B", "Third:C"]
        self.assertScriptResultEquals("$map(%bar%,$upper(%_loop_count%=%_loop_value%))", loop_output, context)
        # Tests with static inputs
        self.assertScriptResultEquals("$map(First:A; Second:B; Third:C,$upper(%_loop_count%=%_loop_value%))", loop_output, context)
        # Tests for removing empty elements
        context["baz"] = ["First:A", "Second:B", "Remove", "Third:C"]
        test_output = "1=FIRST:A; 2=SECOND:B; 4=THIRD:C"
        self.assertScriptResultEquals("$lenmulti(%baz%)", "4", context)
        self.assertScriptResultEquals("$map(%baz%,$if($eq(%_loop_count%,3),,$upper(%_loop_count%=%_loop_value%)))", test_output, context)
        context["baz"] = ["First:A", "Second:B", "Remove", "Third:C"]
        self.assertScriptResultEquals("$setmulti(baz,$map(%baz%,$if($eq(%_loop_count%,3),,$upper(%_loop_count%=%_loop_value%))))%baz%", test_output, context)
        self.assertScriptResultEquals("$lenmulti(%baz%)", "3", context)
        self.assertScriptResultEquals("%baz%", test_output, context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$map(,$upper(%_loop_count%=%_loop_value%))", "", context)
        self.assertScriptResultEquals("$map(First:A; Second:B; Third:C,)", "", context)
        # Tests with separator override
        self.assertScriptResultEquals("$map(First:A; Second:B; Third:C,$upper(%_loop_count%=%_loop_value%),:)", alternate_output, context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$map: Wrong number of arguments for \$map: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$map()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$map(abc; def)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$map(abc:def,$noop(),:,extra)")

    def test_cmd_joinmulti(self):
        context = Metadata()
        context["foo"] = "First:A; Second:B; Third:C"
        context["bar"] = ["First:A", "Second:B", "Third:C"]
        context["joiner"] = " ==> "
        foo_output = "First:A; Second:B; Third:C"
        bar_output = "First:A ==> Second:B ==> Third:C"
        alternate_output = "First ==> A; Second ==> B; Third ==> C"
        # Tests with context
        self.assertScriptResultEquals("$join(%foo%,%joiner%)", foo_output, context)
        self.assertScriptResultEquals("$join(%bar%,%joiner%)", bar_output, context)
        # Tests with static inputs
        self.assertScriptResultEquals("$join(First:A; Second:B; Third:C, ==> )", bar_output, context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$join(, ==> )", "", context)
        self.assertScriptResultEquals("$join(First:A; Second:B; Third:C,)", "First:ASecond:BThird:C", context)
        # Tests with separator override
        self.assertScriptResultEquals("$join(First:A; Second:B; Third:C, ==> ,:)", alternate_output, context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$join: Wrong number of arguments for \$join: Expected between 2 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$join()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$join(abc; def)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$join(abc:def, ==> ,:,extra)")

    def test_cmd_slice(self):
        context = Metadata()
        context["foo"] = "First:A; Second:B; Third:C"
        context["bar"] = ["First:A", "Second:B", "Third:C"]
        context["zero"] = '0'
        context["one"] = '1'
        context["two"] = '2'
        context["three"] = '3'
        output_0_1 = "First:A"
        output_0_2 = "First:A; Second:B"
        output_0_3 = "First:A; Second:B; Third:C"
        output_1_2 = "Second:B"
        output_1_3 = "Second:B; Third:C"
        output_2_3 = "Third:C"
        alternate_output = "A; Second:B; Third"
        # Tests with context
        self.assertScriptResultEquals("$slice(%foo%,%zero%,%one%)", output_0_3, context)
        self.assertScriptResultEquals("$slice(%bar%,%zero%,%one%)", output_0_1, context)
        self.assertScriptResultEquals("$slice(%bar%,%zero%,%two%)", output_0_2, context)
        self.assertScriptResultEquals("$slice(%bar%,%zero%,%three%)", output_0_3, context)
        # Tests with static inputs
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,0,1)", output_0_1, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,0,2)", output_0_2, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,0,3)", output_0_3, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1,2)", output_1_2, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1,3)", output_1_3, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,2,3)", output_2_3, context)
        # Tests with negative inputs
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,-3,1)", output_0_1, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,0,-1)", output_0_2, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,-2,2)", output_1_2, context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,,1)", output_0_1, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1)", output_1_3, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1,)", output_1_3, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,,)", output_0_3, context)
        # Tests with invalid inputs (end < start)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1,0)", "", context)
        # Tests with invalid inputs (non-numeric end and/or start)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,a,1)", output_0_1, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1,b)", output_1_3, context)
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,a,b)", output_0_3, context)
        # Tests with separator override
        self.assertScriptResultEquals("$slice(First:A; Second:B; Third:C,1,3,:)", alternate_output, context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$slice: Wrong number of arguments for \$slice: Expected between 2 and 4, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$slice()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$slice(abc; def)")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$slice(abc; def),0,1,:,extra")

    def test_cmd_datetime(self):
        # Save original datetime object and substitute one returning
        # a fixed now() value for testing.
        original_datetime = datetime.datetime
        datetime.datetime = _DateTime

        try:
            context = Metadata()
            context["foo"] = "%Y%m%d%H%M%S.%f"
            # Tests with context
            self.assertScriptResultEquals("$datetime(%foo%)", "20200102123456.000789", context)
            self.assertScriptResultEquals("$datetime($initials())", "2020-01-02 12:34:56", context)
            # Tests with static input
            self.assertScriptResultEquals(r"$datetime(\%Y\%m\%d\%H\%M\%S.\%f)", "20200102123456.000789", context)
            # Tests with timezones
            self.assertScriptResultEquals(r"$datetime(\%H\%M\%S \%z \%Z)", "123456 +0200 TZ Test", context)
            # Tests with missing input
            self.assertScriptResultEquals("$datetime()", "2020-01-02 12:34:56", context)
            # Tests with invalid format
            self.assertScriptResultEquals("$datetime(xxx)", "xxx", context)
            # Tests with invalid number of arguments
            areg = r"^\d+:\d+:\$datetime: Wrong number of arguments for \$datetime: Expected between 0 and 1, "
            with self.assertRaisesRegex(ScriptError, areg):
                self.parser.eval("$datetime(abc,def)")
        finally:
            # Restore original datetime object
            datetime.datetime = original_datetime

    def test_cmd_datetime_platform_dependent(self):
        # Platform dependent testing because different platforms (both os and Python version)
        # support some format arguments differently.
        possible_tests = (
            '%',    # Hanging % at end of format
            '%-d',  # Non zero-padded day
            '%-m',  # Non zero-padded month
            '%3Y',  # Length specifier shorter than string
        )
        tests_to_run = []
        # Get list of tests for unsupported format codes
        for test_case in possible_tests:
            try:
                datetime.datetime.now().strftime(test_case)
            except ValueError:
                tests_to_run.append(test_case)
        if not tests_to_run:
            self.skipTest('datetime module supports all test cases')
        # Save original datetime object and substitute one returning
        # a fixed now() value for testing.
        original_datetime = datetime.datetime
        datetime.datetime = _DateTime

        try:
            areg = r"^\d+:\d+:\$datetime: Unsupported format code"
            # Tests with invalid format code (platform dependent tests)
            for test_case in tests_to_run:
                with self.assertRaisesRegex(ScriptRuntimeError, areg):
                    self.parser.eval(r'$datetime(\{0})'.format(test_case))
        finally:
            # Restore original datetime object
            datetime.datetime = original_datetime

    def test_scriptruntimeerror(self):
        # Platform dependent testing because different platforms (both os and Python version)
        # support some format arguments differently.  Use $datetime function to generate exceptions.
        possible_tests = (
            '%',    # Hanging % at end of format
            '%-d',  # Non zero-padded day
            '%-m',  # Non zero-padded month
            '%3Y',  # Length specifier shorter than string
        )
        test_to_run = ''
        # Get list of tests for unsupported format codes
        for test_case in possible_tests:
            try:
                datetime.datetime.now().strftime(test_case)
            except ValueError:
                test_to_run = test_case
                break
        if not test_to_run:
            self.skipTest('no test found to generate ScriptRuntimeError')
        # Save original datetime object and substitute one returning
        # a fixed now() value for testing.
        original_datetime = datetime.datetime
        datetime.datetime = _DateTime

        try:
            # Test that the correct position number is passed
            areg = r"^\d+:7:\$datetime: Unsupported format code"
            with self.assertRaisesRegex(ScriptRuntimeError, areg):
                self.parser.eval(r'$noop()$datetime(\{0})'.format(test_to_run))
            # Test that the function stack is returning the correct name (nested functions)
            areg = r"^\d+:\d+:\$datetime: Unsupported format code"
            with self.assertRaisesRegex(ScriptRuntimeError, areg):
                self.parser.eval(r'$set(foo,$datetime($if(,,\{0})))'.format(test_to_run))
            # Test that the correct line number is passed
            areg = r"^2:\d+:\$datetime: Unsupported format code"
            with self.assertRaisesRegex(ScriptRuntimeError, areg):
                self.parser.eval('$noop(\n)$datetime($if(,,\\{0})))'.format(test_to_run))
        finally:
            # Restore original datetime object
            datetime.datetime = original_datetime

    def test_multivalue_1(self):
        self.parser.context = Metadata({'foo': ':', 'bar': 'x:yz', 'empty': ''})
        expr = self.parser.parse('a:bc; d:ef')
        self.assertIsInstance(expr, ScriptExpression)

        mv = MultiValue(self.parser, expr, MULTI_VALUED_JOINER)
        self.assertEqual(mv._multi, ['a:bc', 'd:ef'])
        self.assertEqual(mv.separator, MULTI_VALUED_JOINER)
        self.assertEqual(len(mv), 2)
        del mv[0]
        self.assertEqual(len(mv), 1)
        mv.insert(0, 'x')
        self.assertEqual(mv[0], 'x')
        mv[0] = 'y'
        self.assertEqual(mv[0], 'y')
        self.assertEqual(str(mv), 'y; d:ef')
        self.assertTrue(repr(mv).startswith('MultiValue('))

        mv = MultiValue(self.parser, expr, ':')
        self.assertEqual(mv._multi, ['a', 'bc; d', 'ef'])
        self.assertEqual(mv.separator, ':')

        expr = self.parser.parse('a:bc; d:ef')
        self.assertIsInstance(expr, ScriptExpression)
        sep = self.parser.parse('%foo%')
        self.assertIsInstance(sep, ScriptExpression)
        mv = MultiValue(self.parser, expr, sep)
        self.assertEqual(mv._multi, ['a', 'bc; d', 'ef'])

        expr = self.parser.parse('%bar%; d:ef')
        self.assertIsInstance(expr, ScriptExpression)
        sep = self.parser.parse('%foo%')
        self.assertIsInstance(sep, ScriptExpression)
        mv = MultiValue(self.parser, expr, sep)
        self.assertEqual(mv._multi, ['x', 'yz; d', 'ef'])

        expr = self.parser.parse('%bar%')
        self.assertIsInstance(expr, ScriptExpression)
        mv = MultiValue(self.parser, expr, MULTI_VALUED_JOINER)
        self.assertEqual(mv._multi, ['x:yz'])

        expr = self.parser.parse('%bar%; d:ef')
        self.assertIsInstance(expr, ScriptExpression)
        sep = self.parser.parse('%empty%')
        self.assertIsInstance(sep, ScriptExpression)
        mv = MultiValue(self.parser, expr, sep)
        self.assertEqual(mv._multi, ['x:yz; d:ef'])

        expr = self.parser.parse('')
        self.assertIsInstance(expr, ScriptExpression)
        mv = MultiValue(self.parser, expr, MULTI_VALUED_JOINER)
        self.assertEqual(mv._multi, [])

    def test_cmd_sortmulti(self):
        context = Metadata()
        context["foo"] = ['B', 'D', 'E', 'A', 'C']
        context["bar"] = ['B:AB', 'D:C', 'E:D', 'A:A', 'C:X']
        context['baz'] = "B; D; E; A; C"
        # Tests with context
        self.assertScriptResultEquals("$sortmulti(%foo%)", "A; B; C; D; E", context)
        self.assertScriptResultEquals("$sortmulti(%bar%)", "A:A; B:AB; C:X; D:C; E:D", context)
        self.assertScriptResultEquals("$sortmulti(%baz%)", "B; D; E; A; C", context)
        # Tests with static inputs
        self.assertScriptResultEquals("$sortmulti(B; D; E; A; C)", "A; B; C; D; E", context)
        self.assertScriptResultEquals("$sortmulti(B:AB; D:C; E:D; A:A; C:X)", "A:A; B:AB; C:X; D:C; E:D", context)
        # Tests with separator override
        self.assertScriptResultEquals("$sortmulti(B:AB; D:C; E:D; A:A; C:X,:)", "A; C:AB; D:B:C; E:D; A:X", context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$sortmulti(,)", "", context)
        self.assertScriptResultEquals("$sortmulti(,:)", "", context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$sortmulti: Wrong number of arguments for \$sortmulti: Expected between 1 and 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$sortmulti()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$sortmulti(B:AB; D:C; E:D; A:A; C:X,:,extra)")

    def test_cmd_reversemulti(self):
        context = Metadata()
        context["foo"] = ['B', 'D', 'E', 'A', 'C']
        context["bar"] = ['B:AB', 'D:C', 'E:D', 'A:A', 'C:X']
        context['baz'] = "B; D; E; A; C"
        # Tests with context
        self.assertScriptResultEquals("$reversemulti(%foo%)", "C; A; E; D; B", context)
        self.assertScriptResultEquals("$reversemulti(%bar%)", "C:X; A:A; E:D; D:C; B:AB", context)
        self.assertScriptResultEquals("$reversemulti(%baz%)", "B; D; E; A; C", context)
        # Tests with static inputs
        self.assertScriptResultEquals("$reversemulti(B; D; E; A; C)", "C; A; E; D; B", context)
        self.assertScriptResultEquals("$reversemulti(B:AB; D:C; E:D; A:A; C:X)", "C:X; A:A; E:D; D:C; B:AB", context)
        # Tests with separator override
        self.assertScriptResultEquals("$reversemulti(B:AB; D:C; E:D; A:A; C:X,:)", "X:A; C:D; A:C; E:AB; D:B", context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$reversemulti(,)", "", context)
        self.assertScriptResultEquals("$reversemulti(,:)", "", context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$reversemulti: Wrong number of arguments for \$reversemulti: Expected between 1 and 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$reversemulti()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$reversemulti(B:AB; D:C; E:D; A:A; C:X,:,extra)")

    def test_cmd_unique(self):
        context = Metadata()
        context["foo"] = ['a', 'A', 'B', 'b', 'cd', 'Cd', 'cD', 'CD', 'a', 'A', 'b']
        context["bar"] = "a; A; B; b; cd; Cd; cD; CD; a; A; b"
        # Tests with context
        self.assertScriptResultEquals("$unique(%foo%)", "A; CD; b", context)
        self.assertScriptResultEquals("$unique(%bar%)", "a; A; B; b; cd; Cd; cD; CD; a; A; b", context)
        # Tests with static inputs
        self.assertScriptResultEquals("$unique(a; A; B; b; cd; Cd; cD; CD; a; A; b)", "A; CD; b", context)
        # Tests with separator override
        self.assertScriptResultEquals("$unique(a: A: B: b: cd: Cd: cD: CD: a: A: b,,: )", "A: CD: b", context)
        # Tests with case-sensitive comparison
        self.assertScriptResultEquals("$unique(%foo%,1)", "A; B; CD; Cd; a; b; cD; cd", context)
        # Tests with missing inputs
        self.assertScriptResultEquals("$unique(,)", "", context)
        self.assertScriptResultEquals("$unique(,,)", "", context)
        self.assertScriptResultEquals("$unique(,:)", "", context)
        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$unique: Wrong number of arguments for \$unique: Expected between 1 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$unique()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$unique(B:AB; D:C; E:D; A:A; C:X,1,:,extra)")

    def test_cmd_countryname(self):
        context = Metadata()
        context["foo"] = "ca"
        context["bar"] = ""
        context["baz"] = "INVALID"

        # Mock function to simulate English locale.
        def mock_gettext_countries_en(arg):
            return arg

        # Mock function to simulate Russian locale.
        def mock_gettext_countries_ru(arg):
            return "Канада" if arg == 'Canada' else arg

        # Test with Russian locale
        with mock.patch('picard.script.functions.gettext_countries', mock_gettext_countries_ru):
            self.assertScriptResultEquals("$countryname(ca)", "Canada", context)
            self.assertScriptResultEquals("$countryname(ca,)", "Canada", context)
            self.assertScriptResultEquals("$countryname(ca, )", "Канада", context)
            self.assertScriptResultEquals("$countryname(ca,yes)", "Канада", context)
            self.assertScriptResultEquals("$countryname(INVALID,yes)", "", context)
            # Test for unknown translation of correct code
            self.assertScriptResultEquals("$countryname(fr,yes)", "France", context)

        # Reset locale to English for remaining tests
        with mock.patch('picard.script.functions.gettext_countries', mock_gettext_countries_en):
            self.assertScriptResultEquals("$countryname(ca,)", "Canada", context)
            self.assertScriptResultEquals("$countryname(ca,yes)", "Canada", context)
            self.assertScriptResultEquals("$countryname(ca)", "Canada", context)
            self.assertScriptResultEquals("$countryname(CA)", "Canada", context)
            self.assertScriptResultEquals("$countryname(%foo%)", "Canada", context)
            self.assertScriptResultEquals("$countryname(%bar%)", "", context)
            self.assertScriptResultEquals("$countryname(%baz%)", "", context)
            self.assertScriptResultEquals("$countryname(INVALID)", "", context)

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$countryname: Wrong number of arguments for \$countryname: Expected between 1 and 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$countryname()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$countryname(CA,,Extra)")

    def test_cmd_year(self):
        context = Metadata()
        context["foo"] = "07.21.2021"
        context["bar"] = "mdy"

        # Test with default values
        self.assertScriptResultEquals("$year(2021 07 21)", "2021", context)
        self.assertScriptResultEquals("$year(2021.07.21)", "2021", context)
        self.assertScriptResultEquals("$year(2021-07-21)", "2021", context)
        self.assertScriptResultEquals("$year(21-07-21)", "21", context)

        # Test with overrides specified
        self.assertScriptResultEquals("$year(%foo%,%bar%)", "2021", context)

        # Test with invalid overrides
        self.assertScriptResultEquals("$year(2021-07-21,myd)", "2021", context)

        # Test missing elements
        self.assertScriptResultEquals("$year(,)", "", context)
        self.assertScriptResultEquals("$year(07-21,mdy)", "", context)
        self.assertScriptResultEquals("$year(21-07,dmy)", "", context)

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$year: Wrong number of arguments for \$year: Expected between 1 and 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$year()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$year(2021-07-21,,)")

    def test_cmd_month(self):
        context = Metadata()
        context["foo"] = "07.21.2021"
        context["bar"] = "mdy"

        # Test with default values
        self.assertScriptResultEquals("$month(2021 07 21)", "07", context)
        self.assertScriptResultEquals("$month(2021.07.21)", "07", context)
        self.assertScriptResultEquals("$month(2021-07-21)", "07", context)
        self.assertScriptResultEquals("$month(2021-7-21)", "7", context)

        # Test with overrides specified
        self.assertScriptResultEquals("$month(%foo%,%bar%)", "07", context)

        # Test with invalid overrides
        self.assertScriptResultEquals("$month(2021-07-21,myd)", "07", context)

        # Test missing elements
        self.assertScriptResultEquals("$month(,)", "", context)
        self.assertScriptResultEquals("$month(-21-2021,mdy)", "", context)

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$month: Wrong number of arguments for \$month: Expected between 1 and 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$month()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$month(2021-07-21,,)")

    def test_cmd_day(self):
        context = Metadata()
        context["foo"] = "07.21.2021"
        context["bar"] = "mdy"

        # Test with default values
        self.assertScriptResultEquals("$day(2021 07 21)", "21", context)
        self.assertScriptResultEquals("$day(2021.07.21)", "21", context)
        self.assertScriptResultEquals("$day(2021-07-21)", "21", context)
        self.assertScriptResultEquals("$day(2021-07-2)", "2", context)

        # Test with overrides specified
        self.assertScriptResultEquals("$day(%foo%,%bar%)", "21", context)

        # Test with invalid overrides
        self.assertScriptResultEquals("$day(2021-07-21,myd)", "21", context)

        # Test missing elements
        self.assertScriptResultEquals("$day(,)", "", context)
        self.assertScriptResultEquals("$day(-07-2021,dmy)", "", context)

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$day: Wrong number of arguments for \$day: Expected between 1 and 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$day()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$day(2021-07-21,,)")

    def test_cmd_dateformat(self):
        context = Metadata()
        context["foo"] = "07.21.2021"
        context["bar"] = "mdy"
        context["format"] = "%Y.%m.%d"

        # Test with default values
        self.assertScriptResultEquals("$dateformat(2021 07 21)", "2021-07-21", context)
        self.assertScriptResultEquals("$dateformat(2021.07.21)", "2021-07-21", context)
        self.assertScriptResultEquals("$dateformat(2021-07-21)", "2021-07-21", context)
        self.assertScriptResultEquals("$dateformat(2021-7-21)", "2021-07-21", context)

        # Test with overrides specified
        self.assertScriptResultEquals("$dateformat(%foo%,%format%,%bar%)", "2021.07.21", context)

        # Test with invalid overrides
        self.assertScriptResultEquals("$dateformat(2021-07-21,,myd)", "2021-07-21", context)
        self.assertScriptResultEquals("$dateformat(2021-07-21,,dmy)", "", context)
        self.assertScriptResultEquals("$dateformat(2021-07-21,,mdy)", "", context)
        self.assertScriptResultEquals("$dateformat(2021-July-21)", "", context)
        self.assertScriptResultEquals("$dateformat(2021)", "", context)
        self.assertScriptResultEquals("$dateformat(2021-07)", "", context)

        # Test missing elements
        self.assertScriptResultEquals("$dateformat(,)", "", context)

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$dateformat: Wrong number of arguments for \$dateformat: Expected between 1 and 3, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$dateformat()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$dateformat(2021-07-21,,,)")

    def test_cmd_is_multi(self):
        context = Metadata()
        context["foo"] = "a; b; c"
        context["bar"] = ""

        self.assertScriptResultEquals("$is_multi(%foo%)", "", context)
        self.assertScriptResultEquals("$is_multi(%bar%)", "", context)
        self.assertScriptResultEquals("$setmulti(baz,a)$is_multi(%baz%)", "", context)
        self.assertScriptResultEquals("$setmulti(baz,a; b; c)$is_multi(%baz%)", "1", context)
        self.assertScriptResultEquals("$is_multi(a; b; c)", "1", context)
        self.assertScriptResultEquals("$is_multi(a)", "", context)

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$is_multi: Wrong number of arguments for \$is_multi: Expected exactly 1, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$is_multi()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$is_multi(a,)")

    def test_cmd_cleanmulti(self):
        context = Metadata()
        context["foo"] = ["", "one", "two"]
        context["bar"] = ["one", "", "two"]
        context["baz"] = ["one", "two", ""]

        # Confirm initial values
        self.assertScriptResultEquals("%foo%", "; one; two", context)
        self.assertScriptResultEquals("%bar%", "one; ; two", context)
        self.assertScriptResultEquals("%baz%", "one; two; ", context)
        # Test cleaned values
        self.assertScriptResultEquals("$cleanmulti(foo)%foo%", "one; two", context)
        self.assertScriptResultEquals("$cleanmulti(bar)%bar%", "one; two", context)
        self.assertScriptResultEquals("$cleanmulti(baz)%baz%", "one; two", context)

    def test_cmd_cleanmulti_with_hidden_var(self):
        context = Metadata()
        context["~foo"] = ["one", "", "two"]

        # Confirm initial values
        self.assertScriptResultEquals("%_foo%", "one; ; two", context)
        # Test cleaned values
        self.assertScriptResultEquals("$cleanmulti(_foo)%_foo%", "one; two", context)

    def test_cmd_cleanmulti_only_empty_strings(self):
        context = Metadata()
        context["foo"] = ["", "", ""]

        # Confirm initial values
        self.assertScriptResultEquals("%foo%", "; ; ", context)
        # Test cleaned values
        self.assertScriptResultEquals("$cleanmulti(foo)%foo%", "", context)

    def test_cmd_cleanmulti_indirect_argument(self):
        context = Metadata()
        context["foo"] = ["", "one", "two"]
        context["bar"] = "foo"

        # Confirm initial values
        self.assertScriptResultEquals("%foo%", "; one; two", context)
        # Test cleaned values
        self.assertScriptResultEquals("$cleanmulti(%bar%)%foo%", "one; two", context)

    def test_cmd_cleanmulti_non_multi_argument(self):
        context = Metadata()
        context["foo"] = "one"
        context["bar"] = "one; ; two"
        context["baz"] = ""

        # Confirm initial values
        self.assertScriptResultEquals("%foo%", "one", context)
        self.assertScriptResultEquals("%bar%", "one; ; two", context)
        self.assertScriptResultEquals("%baz%", "", context)
        # Test cleaned values
        self.assertScriptResultEquals("$cleanmulti(foo)%foo%", "one", context)
        self.assertScriptResultEquals("$cleanmulti(bar)%bar%", "one; ; two", context)
        self.assertScriptResultEquals("$cleanmulti(baz)%baz%", "", context)

    def test_cmd_cleanmulti_invalid_number_of_arguments(self):
        areg = r"^\d+:\d+:\$cleanmulti: Wrong number of arguments for \$cleanmulti: Expected exactly 1, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$cleanmulti()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$cleanmulti(foo,)")

    def test_cmd_min(self):
        # Test "text" processing
        self.assertScriptResultEquals("$min(text,abc)", "abc")
        self.assertScriptResultEquals("$min(text,abc,abcd,ac)", "abc")
        self.assertScriptResultEquals("$min(text,ac,abcd,abc)", "abc")
        self.assertScriptResultEquals("$min(text,,a)", "")
        self.assertScriptResultEquals("$min(text,a,)", "")
        self.assertScriptResultEquals("$min(text,,)", "")

        # Test date type arguments using "text" processing
        self.assertScriptResultEquals("$min(text,2020-01-01)", "2020-01-01")
        self.assertScriptResultEquals("$min(text,2020-01-01,2020-01-02,2020-02)", "2020-01-01")
        self.assertScriptResultEquals("$min(text,2020-02,2020-01-02,2020-01-01)", "2020-01-01")

        # Test "int" processing
        self.assertScriptResultEquals("$min(int,1)", "1")
        self.assertScriptResultEquals("$min(int,2,3)", "2")
        self.assertScriptResultEquals("$min(int,2,1,3)", "1")
        self.assertScriptResultEquals("$min(int,2,1,3.1)", "")
        self.assertScriptResultEquals("$min(int,2,1,a)", "")
        self.assertScriptResultEquals("$min(int,2,,1)", "")
        self.assertScriptResultEquals("$min(int,2,1,)", "")

        # Test "float" processing
        self.assertScriptResultEquals("$min(float,1)", "1.0")
        self.assertScriptResultEquals("$min(float,2,3)", "2.0")
        self.assertScriptResultEquals("$min(float,2,1,3)", "1.0")
        self.assertScriptResultEquals("$min(float,2,1.1,3)", "1.1")
        self.assertScriptResultEquals("$min(float,1.11,1.1,1.111)", "1.1")
        self.assertScriptResultEquals("$min(float,2,1,a)", "")
        self.assertScriptResultEquals("$min(float,2,,1)", "")
        self.assertScriptResultEquals("$min(float,2,1,)", "")

        # Test 'nocase' processing
        self.assertScriptResultEquals("$min(nocase,a,B)", "a")
        self.assertScriptResultEquals("$min(nocase,c,A,b)", "A")

        # Test case sensitive arguments with 'text' processing
        self.assertScriptResultEquals("$min(text,A,a)", "A")
        self.assertScriptResultEquals("$min(text,a,B)", "B")

        # Test multi-value arguments
        context = Metadata()
        context['mv'] = ['y', 'z', 'x']
        self.assertScriptResultEquals("$min(text,%mv%)", "x", context)
        self.assertScriptResultEquals("$min(text,a,%mv%)", "a", context)
        self.assertScriptResultEquals("$min(text,y; z; x)", "x")
        self.assertScriptResultEquals("$min(text,a,y; z; x)", "a")
        self.assertScriptResultEquals("$min(int,5,4; 6; 3)", "3")
        self.assertScriptResultEquals("$min(float,5.9,4.2; 6; 3.35)", "3.35")

        # Test 'auto' processing
        self.assertScriptResultEquals("$min(,1,2)", "1")
        self.assertScriptResultEquals("$min(,2,1)", "1")
        self.assertScriptResultEquals("$min(auto,1,2)", "1")
        self.assertScriptResultEquals("$min(auto,2,1)", "1")
        self.assertScriptResultEquals("$min(,1,2.1)", "1.0")
        self.assertScriptResultEquals("$min(,2.1,1)", "1.0")
        self.assertScriptResultEquals("$min(auto,1,2.1)", "1.0")
        self.assertScriptResultEquals("$min(auto,2.1,1)", "1.0")
        self.assertScriptResultEquals("$min(,2.1,1,a)", "1")
        self.assertScriptResultEquals("$min(auto,2.1,1,a)", "1")
        self.assertScriptResultEquals("$min(,a,A)", "A")
        self.assertScriptResultEquals("$min(,A,a)", "A")
        self.assertScriptResultEquals("$min(auto,a,A)", "A")
        self.assertScriptResultEquals("$min(auto,A,a)", "A")

        # Test invalid processing types
        self.assertScriptResultEquals("$min(unknown,a,B)", "")

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$min: Wrong number of arguments for \$min: Expected at least 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$min()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$min(text)")

    def test_cmd_max(self):
        # Test "text" processing
        self.assertScriptResultEquals("$max(text,abc)", "abc")
        self.assertScriptResultEquals("$max(text,abc,abcd,ac)", "ac")
        self.assertScriptResultEquals("$max(text,ac,abcd,abc)", "ac")
        self.assertScriptResultEquals("$max(text,,a)", "a")
        self.assertScriptResultEquals("$max(text,a,)", "a")
        self.assertScriptResultEquals("$max(text,,)", "")

        # Test date type arguments using "text" processing
        self.assertScriptResultEquals("$max(text,2020-01-01)", "2020-01-01")
        self.assertScriptResultEquals("$max(text,2020-01-01,2020-01-02,2020-02)", "2020-02")
        self.assertScriptResultEquals("$max(text,2020-02,2020-01-02,2020-01-01)", "2020-02")

        # Test "int" processing
        self.assertScriptResultEquals("$max(int,1)", "1")
        self.assertScriptResultEquals("$max(int,2,3)", "3")
        self.assertScriptResultEquals("$max(int,2,1,3)", "3")
        self.assertScriptResultEquals("$max(int,2,1,3.1)", "")
        self.assertScriptResultEquals("$max(int,2,1,a)", "")
        self.assertScriptResultEquals("$max(int,2,,1)", "")
        self.assertScriptResultEquals("$max(int,2,1,)", "")

        # Test "float" processing
        self.assertScriptResultEquals("$max(float,1)", "1.0")
        self.assertScriptResultEquals("$max(float,2,3)", "3.0")
        self.assertScriptResultEquals("$max(float,2,1.1,3)", "3.0")
        self.assertScriptResultEquals("$max(float,2,1,3.1)", "3.1")
        self.assertScriptResultEquals("$max(float,2.1,2.11,2.111)", "2.111")
        self.assertScriptResultEquals("$max(float,2,1,a)", "")
        self.assertScriptResultEquals("$max(float,2,,1)", "")
        self.assertScriptResultEquals("$max(float,2,1,)", "")

        # Test 'nocase' processing
        self.assertScriptResultEquals("$max(nocase,a,B)", "B")
        self.assertScriptResultEquals("$max(nocase,c,a,B)", "c")

        # Test case sensitive arguments with 'text' processing
        self.assertScriptResultEquals("$max(text,A,a)", "a")
        self.assertScriptResultEquals("$max(text,a,B)", "a")

        # Test multi-value arguments
        context = Metadata()
        context['mv'] = ['y', 'z', 'x']
        self.assertScriptResultEquals("$max(text,%mv%)", "z", context)
        self.assertScriptResultEquals("$max(text,a,%mv%)", "z", context)
        self.assertScriptResultEquals("$max(text,y; z; x)", "z")
        self.assertScriptResultEquals("$max(text,a,y; z; x)", "z")
        self.assertScriptResultEquals("$max(int,5,4; 6; 3)", "6")
        self.assertScriptResultEquals("$max(float,5.9,4.2; 6; 3.35)", "6.0")

        # Test 'auto' processing
        self.assertScriptResultEquals("$max(,1,2)", "2")
        self.assertScriptResultEquals("$max(,2,1)", "2")
        self.assertScriptResultEquals("$max(auto,1,2)", "2")
        self.assertScriptResultEquals("$max(auto,2,1)", "2")
        self.assertScriptResultEquals("$max(,1.1,2)", "2.0")
        self.assertScriptResultEquals("$max(,2,1.1)", "2.0")
        self.assertScriptResultEquals("$max(auto,1.1,2)", "2.0")
        self.assertScriptResultEquals("$max(auto,2,1.1)", "2.0")
        self.assertScriptResultEquals("$max(,2.1,1,a)", "a")
        self.assertScriptResultEquals("$max(auto,2.1,1,a)", "a")
        self.assertScriptResultEquals("$max(,a,A)", "a")
        self.assertScriptResultEquals("$max(,A,a)", "a")
        self.assertScriptResultEquals("$max(auto,a,A)", "a")
        self.assertScriptResultEquals("$max(auto,A,a)", "a")

        # Test invalid processing types
        self.assertScriptResultEquals("$max(unknown,a,B)", "")

        # Tests with invalid number of arguments
        areg = r"^\d+:\d+:\$max: Wrong number of arguments for \$max: Expected at least 2, "
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$max()")
        with self.assertRaisesRegex(ScriptError, areg):
            self.parser.eval("$max(text)")
