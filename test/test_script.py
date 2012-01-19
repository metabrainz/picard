import unittest
from PyQt4 import QtCore
from picard.script import ScriptParser
from picard.metadata import Metadata

class FakeConfig(object):
    def __init__(self):
        self.setting = {
            'enabled_plugins': '',
            }


class ScriptParserTest(unittest.TestCase):
    def setUp(self):
        QtCore.QObject.config = FakeConfig()
        self.parser = ScriptParser()

    def test_cmd_noop(self):
        self.assertEqual(self.parser.eval("$noop()"), "")

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
        self.assertEqual(context.getall("test"), ["multi; valued"]) # list has only a single value

    def test_cmd_setmulti_multi_valued(self):
        context = Metadata()
        context["source"] = ["multi", "valued"]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context)) # no return value
        self.assertEqual(context.getall("source"), context.getall("test"))

    def test_cmd_setmulti_multi_valued_wth_spaces(self):
        context = Metadata()
        context["source"] = ["multi, multi", "valued, multi"]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context)) # no return value
        self.assertEqual(context.getall("source"), context.getall("test"))

    def test_cmd_setmulti_not_multi_valued(self):
        context = Metadata()
        context["source"] = "multi, multi"
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context)) # no return value
        self.assertEqual(context.getall("source"), context.getall("test"))

    def test_cmd_setmulti_will_remove_empty_items(self):
        context = Metadata()
        context["source"] = ["", "multi", ""]
        self.assertEqual("", self.parser.eval("$setmulti(test,%source%)", context)) # no return value
        self.assertEqual(["multi"], context.getall("test"))

    def test_cmd_setmulti_custom_splitter_string(self):
        context = Metadata()
        self.assertEqual("", self.parser.eval("$setmulti(test,multi##valued##test##,##)", context)) # no return value
        self.assertEqual(["multi", "valued", "test"], context.getall("test"))

    def test_cmd_setmulti_empty_splitter_does_nothing(self):
        context = Metadata()
        self.assertEqual("", self.parser.eval("$setmulti(test,multi; valued,)", context)) # no return value
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
        self.assertEqual(self.parser.eval("$or(,q)"), "1")
        self.assertEqual(self.parser.eval("$or(q,)"), "1")
        self.assertEqual(self.parser.eval("$or(q,q)"), "1")

    def test_cmd_and(self):
        self.assertEqual(self.parser.eval("$and(,)"), "")
        self.assertEqual(self.parser.eval("$and(,q)"), "")
        self.assertEqual(self.parser.eval("$and(q,)"), "")
        self.assertEqual(self.parser.eval("$and(q,q)"), "1")

    def test_cmd_not(self):
        self.assertEqual(self.parser.eval("$not($noop())"), "1")
        self.assertEqual(self.parser.eval("$not(q)"), "")

    def test_cmd_add(self):
        self.assertEqual(self.parser.eval("$add(1,2)"), "3")

    def test_cmd_sub(self):
        self.assertEqual(self.parser.eval("$sub(1,2)"), "-1")
        self.assertEqual(self.parser.eval("$sub(2,1)"), "1")

    def test_cmd_div(self):
        self.assertEqual(self.parser.eval("$div(9,3)"), "3")
        self.assertEqual(self.parser.eval("$div(10,3)"), "3")

    def test_cmd_mod(self):
        self.assertEqual(self.parser.eval("$mod(9,3)"), "0")
        self.assertEqual(self.parser.eval("$mod(10,3)"), "1")

    def test_cmd_mul(self):
        self.assertEqual(self.parser.eval("$mul(9,3)"), "27")
        self.assertEqual(self.parser.eval("$mul(10,3)"), "30")

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
        context["target"] = ["tag1", "tag2"]
        context["source"] = ["tag2", "tag3"]
        self._eval_and_check_copymerge(context, ["tag1", "tag2", "tag3"])

    def test_cmd_copymerge_nonlist(self):
        context = Metadata()
        context["target"] = "targetval"
        context["source"] = "sourceval"
        self._eval_and_check_copymerge(context, ["targetval", "sourceval"])
