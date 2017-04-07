import unittest
import picard
from PyQt5 import QtCore
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

    def test_cmd_noop(self):
        self.assertEqual(self.parser.eval("$noop()"), "")
        self.assertEqual(self.parser.eval("$noop(abcdefg)"), "")

    def test_cmd_if(self):
        self.assertEqual(self.parser.eval("$if(1,a,b)"), "a")
        self.assertEqual(self.parser.eval("$if(,a,b)"), "b")

    def test_cmd_if2(self):
        self.assertEqual(self.parser.eval("$if2(,a,b)"), "a")
        self.assertEqual(self.parser.eval("$if2($noop(),b)"), "b")

    def test_cmd_left(self):
        self.assertEqual(self.parser.eval("$left(abcd,2)"), "ab")

    def test_cmd_right(self):
        self.assertEqual(self.parser.eval("$right(abcd,2)"), "cd")

    def test_cmd_set(self):
        self.assertEqual(self.parser.eval("$set(test,aaa)%test%"), "aaa")

    def test_cmd_set_empty(self):
        self.assertEqual(self.parser.eval("$set(test,)%test%"), "")

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
        self.assertEqual(self.parser.eval("$get(test)", context), "aaa")
        context["test2"] = ["multi", "valued"]
        self.assertEqual(self.parser.eval("$get(test2)", context), "multi; valued")

    def test_cmd_num(self):
        self.assertEqual(self.parser.eval("$num(3,3)"), "003")
        self.assertEqual(self.parser.eval("$num(03,3)"), "003")
        self.assertEqual(self.parser.eval("$num(123,2)"), "123")

    def test_cmd_or(self):
        self.assertEqual(self.parser.eval("$or(,)"), "")
        self.assertEqual(self.parser.eval("$or(,,)"), "")
        self.assertEqual(self.parser.eval("$or(,q)"), "1")
        self.assertEqual(self.parser.eval("$or(q,)"), "1")
        self.assertEqual(self.parser.eval("$or(q,q)"), "1")
        self.assertEqual(self.parser.eval("$or(q,,)"), "1")

    def test_cmd_and(self):
        self.assertEqual(self.parser.eval("$and(,)"), "")
        self.assertEqual(self.parser.eval("$and(,q)"), "")
        self.assertEqual(self.parser.eval("$and(q,)"), "")
        self.assertEqual(self.parser.eval("$and(q,q,)"), "")
        self.assertEqual(self.parser.eval("$and(q,q)"), "1")
        self.assertEqual(self.parser.eval("$and(q,q,q)"), "1")

    def test_cmd_not(self):
        self.assertEqual(self.parser.eval("$not($noop())"), "1")
        self.assertEqual(self.parser.eval("$not(q)"), "")

    def test_cmd_add(self):
        self.assertEqual(self.parser.eval("$add(1,2)"), "3")
        self.assertEqual(self.parser.eval("$add(1,2,3)"), "6")

    def test_cmd_sub(self):
        self.assertEqual(self.parser.eval("$sub(1,2)"), "-1")
        self.assertEqual(self.parser.eval("$sub(2,1)"), "1")
        self.assertEqual(self.parser.eval("$sub(4,2,1)"), "1")

    def test_cmd_div(self):
        self.assertEqual(self.parser.eval("$div(9,3)"), "3")
        self.assertEqual(self.parser.eval("$div(10,3)"), "3")
        self.assertEqual(self.parser.eval("$div(30,3,3)"), "3")

    def test_cmd_mod(self):
        self.assertEqual(self.parser.eval("$mod(9,3)"), "0")
        self.assertEqual(self.parser.eval("$mod(10,3)"), "1")
        self.assertEqual(self.parser.eval("$mod(10,6,3)"), "1")

    def test_cmd_mul(self):
        self.assertEqual(self.parser.eval("$mul(9,3)"), "27")
        self.assertEqual(self.parser.eval("$mul(10,3)"), "30")
        self.assertEqual(self.parser.eval("$mul(2,5,3)"), "30")

    def test_cmd_eq(self):
        self.assertEqual(self.parser.eval("$eq(,)"), "1")
        self.assertEqual(self.parser.eval("$eq(,$noop())"), "1")
        self.assertEqual(self.parser.eval("$eq(,q)"), "")
        self.assertEqual(self.parser.eval("$eq(q,q)"), "1")
        self.assertEqual(self.parser.eval("$eq(q,)"), "")

    def test_cmd_ne(self):
        self.assertEqual(self.parser.eval("$ne(,)"), "")
        self.assertEqual(self.parser.eval("$ne(,$noop())"), "")
        self.assertEqual(self.parser.eval("$ne(,q)"), "1")
        self.assertEqual(self.parser.eval("$ne(q,q)"), "")
        self.assertEqual(self.parser.eval("$ne(q,)"), "1")

    def test_cmd_lower(self):
        self.assertEqual(self.parser.eval("$lower(AbeCeDA)"), "abeceda")

    def test_cmd_upper(self):
        self.assertEqual(self.parser.eval("$upper(AbeCeDA)"), "ABECEDA")

    def test_cmd_rreplace(self):
        self.assertEqual(
            self.parser.eval(r'''$rreplace(test \(disc 1\),\\s\\\(disc \\d+\\\),)'''),
            "test"
        )

    def test_cmd_rsearch(self):
        self.assertEqual(
            self.parser.eval(r"$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\))"),
            "1"
        )

    def test_arguments(self):
        self.assertTrue(
            self.parser.eval(
                r"$set(bleh,$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\)))) $set(wer,1)"))

    def test_cmd_gt(self):
        self.assertEqual(self.parser.eval("$gt(10,4)"), "1")
        self.assertEqual(self.parser.eval("$gt(6,4)"), "1")

    def test_cmd_gte(self):
        self.assertEqual(self.parser.eval("$gte(10,10)"), "1")
        self.assertEqual(self.parser.eval("$gte(10,4)"), "1")
        self.assertEqual(self.parser.eval("$gte(6,4)"), "1")

    def test_cmd_lt(self):
        self.assertEqual(self.parser.eval("$lt(4,10)"), "1")
        self.assertEqual(self.parser.eval("$lt(4,6)"), "1")

    def test_cmd_lte(self):
        self.assertEqual(self.parser.eval("$lte(10,10)"), "1")
        self.assertEqual(self.parser.eval("$lte(4,10)"), "1")
        self.assertEqual(self.parser.eval("$lte(4,6)"), "1")

    def test_cmd_len(self):
        self.assertEqual(self.parser.eval("$len(abcdefg)"), "7")
        self.assertEqual(self.parser.eval("$len(0)"), "1")
        self.assertEqual(self.parser.eval("$len()"), "0")

    def test_cmd_firstalphachar(self):
        self.assertEqual(self.parser.eval("$firstalphachar(abc)"), "A")
        self.assertEqual(self.parser.eval("$firstalphachar(Abc)"), "A")
        self.assertEqual(self.parser.eval("$firstalphachar(1abc)"), "#")
        self.assertEqual(self.parser.eval("$firstalphachar(...abc)"), "#")
        self.assertEqual(self.parser.eval("$firstalphachar(1abc,_)"), "_")
        self.assertEqual(self.parser.eval("$firstalphachar(...abc,_)"), "_")
        self.assertEqual(self.parser.eval("$firstalphachar()"), "#")
        self.assertEqual(self.parser.eval("$firstalphachar(,_)"), "_")
        self.assertEqual(self.parser.eval("$firstalphachar( abc)"), "#")

    def test_cmd_initials(self):
        self.assertEqual(self.parser.eval("$initials(Abc def Ghi)"), "AdG")
        self.assertEqual(self.parser.eval("$initials(Abc #def Ghi)"), "AG")
        self.assertEqual(self.parser.eval("$initials(Abc 1def Ghi)"), "AG")
        self.assertEqual(self.parser.eval("$initials(Abc)"), "A")
        self.assertEqual(self.parser.eval("$initials()"), "")

    def test_cmd_firstwords(self):
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,11)"), "Abc Def Ghi")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,12)"), "Abc Def Ghi")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,7)"), "Abc Def")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,8)"), "Abc Def")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,6)"), "Abc")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,0)"), "")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,NaN)"), "")
        self.assertEqual(self.parser.eval("$firstwords(Abc Def Ghi,)"), "")

    def test_cmd_startswith(self):
        self.assertEqual(self.parser.eval("$startswith(abc,a)"), "1")
        self.assertEqual(self.parser.eval("$startswith(abc,abc)"), "1")
        self.assertEqual(self.parser.eval("$startswith(abc,)"), "1")
        self.assertEqual(self.parser.eval("$startswith(abc,b)"), "0")
        self.assertEqual(self.parser.eval("$startswith(abc,Ab)"), "0")

    def test_cmd_endswith(self):
        self.assertEqual(self.parser.eval("$endswith(abc,c)"), "1")
        self.assertEqual(self.parser.eval("$endswith(abc,abc)"), "1")
        self.assertEqual(self.parser.eval("$endswith(abc,)"), "1")
        self.assertEqual(self.parser.eval("$endswith(abc,b)"), "0")
        self.assertEqual(self.parser.eval("$endswith(abc,bC)"), "0")

    def test_cmd_truncate(self):
        self.assertEqual(self.parser.eval("$truncate(abcdefg,0)"), "")
        self.assertEqual(self.parser.eval("$truncate(abcdefg,7)"), "abcdefg")
        self.assertEqual(self.parser.eval("$truncate(abcdefg,3)"), "abc")
        self.assertEqual(self.parser.eval("$truncate(abcdefg,10)"), "abcdefg")
        self.assertEqual(self.parser.eval("$truncate(abcdefg,)"), "abcdefg")
        self.assertEqual(self.parser.eval("$truncate(abcdefg,NaN)"), "abcdefg")

    def test_cmd_copy(self):
        context = Metadata()
        tagsToCopy = ["tag1", "tag2"]
        context["source"] = tagsToCopy
        context["target"] = ["will", "be", "overwritten"]
        self.parser.eval("$copy(target,source)", context)
        self.assertEqual(self.parser.context.getall("target"), tagsToCopy)

    def _eval_and_check_copymerge(self, context, expected):
        self.parser.eval("$copymerge(target,source)", context)
        self.assertEqual(sorted(self.parser.context.getall("target")), sorted(expected))

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
        context["target"] = ["tag1", "tag2"]
        context["source"] = ["tag2", "tag3"]
        self._eval_and_check_copymerge(context, ["tag1", "tag2", "tag3"])

    def test_cmd_copymerge_nonlist(self):
        context = Metadata()
        context["target"] = "targetval"
        context["source"] = "sourceval"
        self._eval_and_check_copymerge(context, ["targetval", "sourceval"])

    def test_cmd_eq_any(self):
        self.assertEqual(self.parser.eval("$eq_any(abc,def,ghi,jkl)"), "")
        self.assertEqual(self.parser.eval("$eq_any(abc,def,ghi,jkl,abc)"), "1")

    def test_cmd_ne_all(self):
        self.assertEqual(self.parser.eval("$ne_all(abc,def,ghi,jkl)"), "1")
        self.assertEqual(self.parser.eval("$ne_all(abc,def,ghi,jkl,abc)"), "")

    def test_cmd_eq_all(self):
        self.assertEqual(self.parser.eval("$eq_all(abc,abc,abc,abc)"), "1")
        self.assertEqual(self.parser.eval("$eq_all(abc,abc,def,ghi)"), "")

    def test_cmd_ne_any(self):
        self.assertEqual(self.parser.eval("$ne_any(abc,abc,abc,abc)"), "")
        self.assertEqual(self.parser.eval("$ne_any(abc,abc,def,ghi)"), "1")

    def test_cmd_swapprefix(self):
        self.assertEqual(self.parser.eval("$swapprefix(A stitch in time)"), "stitch in time, A")
        self.assertEqual(self.parser.eval("$swapprefix(The quick brown fox)"), "quick brown fox, The")
        self.assertEqual(self.parser.eval("$swapprefix(How now brown cow)"), "How now brown cow")
        self.assertEqual(self.parser.eval("$swapprefix(When the red red robin)"), "When the red red robin")
        self.assertEqual(self.parser.eval("$swapprefix(A stitch in time,How,When,Who)"), "A stitch in time")
        self.assertEqual(self.parser.eval("$swapprefix(The quick brown fox,How,When,Who)"), "The quick brown fox")
        self.assertEqual(self.parser.eval("$swapprefix(How now brown cow,How,When,Who)"), "now brown cow, How")
        self.assertEqual(self.parser.eval("$swapprefix(When the red red robin,How,When,Who)"), "the red red robin, When")

    def test_cmd_delprefix(self):
        self.assertEqual(self.parser.eval("$delprefix(A stitch in time)"), "stitch in time")
        self.assertEqual(self.parser.eval("$delprefix(The quick brown fox)"), "quick brown fox")
        self.assertEqual(self.parser.eval("$delprefix(How now brown cow)"), "How now brown cow")
        self.assertEqual(self.parser.eval("$delprefix(When the red red robin)"), "When the red red robin")
        self.assertEqual(self.parser.eval("$delprefix(A stitch in time,How,When,Who)"), "A stitch in time")
        self.assertEqual(self.parser.eval("$delprefix(The quick brown fox,How,When,Who)"), "The quick brown fox")
        self.assertEqual(self.parser.eval("$delprefix(How now brown cow,How,When,Who)"), "now brown cow")
        self.assertEqual(self.parser.eval("$delprefix(When the red red robin,How,When,Who)"), "the red red robin")

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
