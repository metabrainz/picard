import unittest
from PyQt4 import QtCore
from picard.script import ScriptParser

class FakeConfig():
    def __init__(self):
        self.setting = {
            'enabled_plugins': '',
        }


class ScriptParserTest(unittest.TestCase):

    def setUp(self):
        QtCore.QObject.config = FakeConfig()
        self.parser = ScriptParser()

    def test_cmd_noop(self):
        self.failUnlessEqual(self.parser.eval("$noop()"), "")

    def test_cmd_if(self):
        self.failUnlessEqual(self.parser.eval("$if(1,a,b)"), "a")
        self.failUnlessEqual(self.parser.eval("$if(,a,b)"), "b")

    def test_cmd_if2(self):
        self.failUnlessEqual(self.parser.eval("$if2(,a,b)"), "a")
        self.failUnlessEqual(self.parser.eval("$if2($noop(),b)"), "b")

    def test_cmd_left(self):
        self.failUnlessEqual(self.parser.eval("$left(abcd,2)"), "ab")

    def test_cmd_right(self):
        self.failUnlessEqual(self.parser.eval("$right(abcd,2)"), "cd")

    def test_cmd_set(self):
        self.failUnlessEqual(self.parser.eval("$set(test,aaa)%test%"), "aaa")

    def test_cmd_get(self):
        self.failUnlessEqual(self.parser.eval("$get(test)", {"test": "aaa"}), "aaa")

    def test_cmd_num(self):
        self.failUnlessEqual(self.parser.eval("$num(3,3)"), "003")
        self.failUnlessEqual(self.parser.eval("$num(03,3)"), "003")
        self.failUnlessEqual(self.parser.eval("$num(123,2)"), "123")

    def test_cmd_or(self):
        self.failUnlessEqual(self.parser.eval("$or(,)"), "")
        self.failUnlessEqual(self.parser.eval("$or(,q)"), "1")
        self.failUnlessEqual(self.parser.eval("$or(q,)"), "1")
        self.failUnlessEqual(self.parser.eval("$or(q,q)"), "1")

    def test_cmd_and(self):
        self.failUnlessEqual(self.parser.eval("$and(,)"), "")
        self.failUnlessEqual(self.parser.eval("$and(,q)"), "")
        self.failUnlessEqual(self.parser.eval("$and(q,)"), "")
        self.failUnlessEqual(self.parser.eval("$and(q,q)"), "1")

    def test_cmd_not(self):
        self.failUnlessEqual(self.parser.eval("$not($noop())"), "1")
        self.failUnlessEqual(self.parser.eval("$not(q)"), "")

    def test_cmd_add(self):
        self.failUnlessEqual(self.parser.eval("$add(1,2)"), "3")

    def test_cmd_sub(self):
        self.failUnlessEqual(self.parser.eval("$sub(1,2)"), "-1")
        self.failUnlessEqual(self.parser.eval("$sub(2,1)"), "1")

    def test_cmd_div(self):
        self.failUnlessEqual(self.parser.eval("$div(9,3)"), "3")
        self.failUnlessEqual(self.parser.eval("$div(10,3)"), "3")

    def test_cmd_mod(self):
        self.failUnlessEqual(self.parser.eval("$mod(9,3)"), "0")
        self.failUnlessEqual(self.parser.eval("$mod(10,3)"), "1")

    def test_cmd_mul(self):
        self.failUnlessEqual(self.parser.eval("$mul(9,3)"), "27")
        self.failUnlessEqual(self.parser.eval("$mul(10,3)"), "30")

    def test_cmd_eq(self):
        self.failUnlessEqual(self.parser.eval("$eq(,)"), "1")
        self.failUnlessEqual(self.parser.eval("$eq(,$noop())"), "1")
        self.failUnlessEqual(self.parser.eval("$eq(,q)"), "")
        self.failUnlessEqual(self.parser.eval("$eq(q,q)"), "1")
        self.failUnlessEqual(self.parser.eval("$eq(q,)"), "")

    def test_cmd_ne(self):
        self.failUnlessEqual(self.parser.eval("$ne(,)"), "")
        self.failUnlessEqual(self.parser.eval("$ne(,$noop())"), "")
        self.failUnlessEqual(self.parser.eval("$ne(,q)"), "1")
        self.failUnlessEqual(self.parser.eval("$ne(q,q)"), "")
        self.failUnlessEqual(self.parser.eval("$ne(q,)"), "1")

    def test_cmd_lower(self):
        self.failUnlessEqual(self.parser.eval("$lower(AbeCeDA)"), "abeceda")

    def test_cmd_upper(self):
        self.failUnlessEqual(self.parser.eval("$upper(AbeCeDA)"), "ABECEDA")

    def test_cmd_rreplace(self):
        self.failUnlessEqual(
            self.parser.eval(r'''$rreplace(test \(disc 1\),\\s\\\(disc \\d+\\\),)'''),
            "test"
            )

    def test_cmd_rsearch(self):
        self.failUnlessEqual(
            self.parser.eval(r"$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\))"),
            "1"
            )


class TagzParserTest(unittest.TestCase):

    def setUp(self):
        QtCore.QObject.config = FakeConfig()
        self.parser = ScriptParser()

    def test_arguments(self):
        self.failUnless(
            self.parser.eval(
              r"$set(bleh,$rsearch(test \(disc 1\),\\\(disc \(\\d+\)\\\)))) $set(wer,1)"))
