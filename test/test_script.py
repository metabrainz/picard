import unittest
from picard import config
from picard.script import ScriptParser, ScriptError, register_script_function
from picard.metadata import Metadata
from picard.ui.options.renaming import _DEFAULT_FILE_NAMING_FORMAT


class ScriptParserTest(unittest.TestCase):

    def setUp(self):
        config.setting = {
            'enabled_plugins': '',
        }

        self.parser = ScriptParser()

        def func_noargstest(parser):
            return ""

        register_script_function(func_noargstest, "noargstest")

    def assertScriptResultEquals(self, script, expected, context=None):
        """Asserts that evaluating `script` returns `expected`.


        Args:
            script: The tagger script
            expected: The expected result
            context: A Metadata object with pre-set tags or None
        """
        actual = self.parser.eval(script, context=context)
        self.assertEqual(actual,
                         expected,
                         "'%s' evaluated to '%s', expected '%s'"
                         % (script, actual, expected))

    def test_cmd_noop(self):
        self.assertScriptResultEquals("$noop()", "")
        self.assertScriptResultEquals("$noop(abcdefg)", "")

    def test_cmd_if(self):
        self.assertScriptResultEquals("$if(1,a,b)", "a")
        self.assertScriptResultEquals("$if(,a,b)", "b")

    def test_cmd_if2(self):
        self.assertScriptResultEquals("$if2(,a,b)", "a")
        self.assertScriptResultEquals("$if2($noop(),b)", "b")

    def test_cmd_left(self):
        self.assertScriptResultEquals("$left(abcd,2)", "ab")

    def test_cmd_right(self):
        self.assertScriptResultEquals("$right(abcd,2)", "cd")

    def test_cmd_set(self):
        self.assertScriptResultEquals("$set(test,aaa)%test%", "aaa")

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

    def test_cmd_setmulti_will_remove_empty_items(self):
        context = Metadata()
        context["source"] = ["", "multi", ""]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context))  # no return value
        self.assertEqual(["multi"], context.getall("test"))

    def test_cmd_setmulti_custom_splitter_string(self):
        context = Metadata()
        self.assertEqual("", self.parser.eval("$setmulti(test,multi##valued##test##,##)", context))  # no return value
        self.assertEqual(["multi", "valued", "test"], context.getall("test"))

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

    def test_cmd_add(self):
        self.assertScriptResultEquals("$add(1,2)", "3")
        self.assertScriptResultEquals("$add(1,2,3)", "6")

    def test_cmd_sub(self):
        self.assertScriptResultEquals("$sub(1,2)", "-1")
        self.assertScriptResultEquals("$sub(2,1)", "1")
        self.assertScriptResultEquals("$sub(4,2,1)", "1")

    def test_cmd_div(self):
        self.assertScriptResultEquals("$div(9,3)", "3")
        self.assertScriptResultEquals("$div(10,3)", "3")
        self.assertScriptResultEquals("$div(30,3,3)", "3")

    def test_cmd_mod(self):
        self.assertScriptResultEquals("$mod(9,3)", "0")
        self.assertScriptResultEquals("$mod(10,3)", "1")
        self.assertScriptResultEquals("$mod(10,6,3)", "1")

    def test_cmd_mul(self):
        self.assertScriptResultEquals("$mul(9,3)", "27")
        self.assertScriptResultEquals("$mul(10,3)", "30")
        self.assertScriptResultEquals("$mul(2,5,3)", "30")

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

    def test_cmd_rreplace(self):
        self.assertScriptResultEquals(r'''$rreplace(test \(disc 1\),\\s\\\(disc \\d+\\\),)''', "test")

    def test_cmd_rsearch(self):
        self.assertScriptResultEquals(r"$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\))", "1")

    def test_arguments(self):
        self.assertTrue(
            self.parser.eval(
                r"$set(bleh,$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\)))) $set(wer,1)"))

    def test_cmd_gt(self):
        self.assertScriptResultEquals("$gt(10,4)", "1")
        self.assertScriptResultEquals("$gt(6,4)", "1")

    def test_cmd_gte(self):
        self.assertScriptResultEquals("$gte(10,10)", "1")
        self.assertScriptResultEquals("$gte(10,4)", "1")
        self.assertScriptResultEquals("$gte(6,4)", "1")

    def test_cmd_lt(self):
        self.assertScriptResultEquals("$lt(4,10)", "1")
        self.assertScriptResultEquals("$lt(4,6)", "1")

    def test_cmd_lte(self):
        self.assertScriptResultEquals("$lte(10,10)", "1")
        self.assertScriptResultEquals("$lte(4,10)", "1")
        self.assertScriptResultEquals("$lte(4,6)", "1")

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

    def test_cmd_startswith(self):
        self.assertScriptResultEquals("$startswith(abc,a)", "1")
        self.assertScriptResultEquals("$startswith(abc,abc)", "1")
        self.assertScriptResultEquals("$startswith(abc,)", "1")
        self.assertScriptResultEquals("$startswith(abc,b)", "0")
        self.assertScriptResultEquals("$startswith(abc,Ab)", "0")

    def test_cmd_endswith(self):
        self.assertScriptResultEquals("$endswith(abc,c)", "1")
        self.assertScriptResultEquals("$endswith(abc,abc)", "1")
        self.assertScriptResultEquals("$endswith(abc,)", "1")
        self.assertScriptResultEquals("$endswith(abc,b)", "0")
        self.assertScriptResultEquals("$endswith(abc,bC)", "0")

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
        context['albumartist'] = u'albumartist'
        context['artist'] = u'artist'
        context['album'] = u'album'
        context['totaldiscs'] = 2
        context['discnumber'] = 1
        context['tracknumber'] = 8
        context['title'] = u'title'
        result = self.parser.eval(_DEFAULT_FILE_NAMING_FORMAT, context)
        self.assertEqual(result, u'albumartist/album/1-08 title')
        context['~multiartist'] = '1'
        result = self.parser.eval(_DEFAULT_FILE_NAMING_FORMAT, context)
        self.assertEqual(result, u'albumartist/album/1-08 artist - title')

    def test_default_NAT_filenaming(self):
        context = Metadata()
        context['artist'] = u'artist'
        context['album'] = u'[non-album tracks]'
        context['title'] = u'title'
        result = self.parser.eval(_DEFAULT_FILE_NAMING_FORMAT, context)
        self.assertEqual(result, u'artist/title')

    def test_cmd_with_not_arguments(self):
        try:
            self.parser.eval("$noargstest()")
        except ScriptError:
            self.fail("Function noargs raised ScriptError unexpectedly.")

    def test_cmd_unset_simple(self):
        context = Metadata()
        context['title'] = u'Foo'
        context['album'] = u'Foo'
        context['artist'] = u'Foo'
        self.parser.eval("$unset(album)", context)
        self.assertNotIn('album', context)

    def test_cmd_unset_prefix(self):
        context = Metadata()
        context['title'] = u'Foo'
        context['~rating'] = u'4'
        self.parser.eval("$unset(_rating)", context)
        self.assertNotIn('~rating', context)

    def test_cmd_unset_multi(self):
        context = Metadata()
        context['performer:foo'] = u'Foo'
        context['performer:bar'] = u'Foo'
        self.parser.eval("$unset(performer:*)", context)
        self.assertNotIn('performer:bar', context)
        self.assertNotIn('performer:foo', context)

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

    def test_required_kwonly_parameters(self):
        def func(a, *, required_kwarg):
            pass

        with self.assertRaises(TypeError,
                               msg="Functions with required keyword-only parameters are not supported"):
            register_script_function(func)

    def test_optional_kwonly_parameters(self):
        def func(a, *, optional_kwarg=1):
            pass

        register_script_function(func)
