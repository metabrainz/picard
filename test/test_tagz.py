import unittest
from picard.tagz import Tagz
from picard.component import ComponentManager

class MiscModelTest(unittest.TestCase):

    def setUp(self):
        self.tagz = Tagz(ComponentManager())

    def test_cmd_noop(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$noop()"), "")

    def test_cmd_if(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$if(1,a,b)"), "a")
        self.failUnlessEqual(self.tagz.evaluate_script("$if(,a,b)"), "b")

    def test_cmd_if2(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$if2(,a,b)"), "a")
        self.failUnlessEqual(self.tagz.evaluate_script("$if2($noop(),b)"), "b")

    def test_cmd_left(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$left(abcd,2)"), "ab")

    def test_cmd_right(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$right(abcd,2)"), "cd")

    def test_cmd_set(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$set(test,aaa)%test%"), "aaa")

    def test_cmd_get(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$get(test)", {"test": "aaa"}), "aaa")

    def test_cmd_num(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$num(3,3)"), "003")
        self.failUnlessEqual(self.tagz.evaluate_script("$num(03,3)"), "003")
        self.failUnlessEqual(self.tagz.evaluate_script("$num(123,2)"), "123")

    def test_cmd_or(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$or(,)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$or(,q)"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$or(q,)"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$or(q,q)"), "1")

    def test_cmd_and(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$and(,)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$and(,q)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$and(q,)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$and(q,q)"), "1")

    def test_cmd_not(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$not($noop())"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$not(q)"), "")

    def test_cmd_add(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$add(1,2)"), "3")

    def test_cmd_sub(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$sub(1,2)"), "-1")
        self.failUnlessEqual(self.tagz.evaluate_script("$sub(2,1)"), "1")

    def test_cmd_div(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$div(9,3)"), "3")
        self.failUnlessEqual(self.tagz.evaluate_script("$div(10,3)"), "3")

    def test_cmd_mod(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$mod(9,3)"), "0")
        self.failUnlessEqual(self.tagz.evaluate_script("$mod(10,3)"), "1")

    def test_cmd_mul(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$mul(9,3)"), "27")
        self.failUnlessEqual(self.tagz.evaluate_script("$mul(10,3)"), "30")

    def test_cmd_eq(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$eq(,)"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$eq(,$noop())"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$eq(,q)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$eq(q,q)"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$eq(q,)"), "")

    def test_cmd_ne(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$ne(,)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$ne(,$noop())"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$ne(,q)"), "1")
        self.failUnlessEqual(self.tagz.evaluate_script("$ne(q,q)"), "")
        self.failUnlessEqual(self.tagz.evaluate_script("$ne(q,)"), "1")

    def test_cmd_lower(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$lower(AbeCeDA)"), "abeceda")

    def test_cmd_upper(self):
        self.failUnlessEqual(self.tagz.evaluate_script("$upper(AbeCeDA)"), "ABECEDA")

    def test_cmd_rreplace(self):
        self.failUnlessEqual(
            self.tagz.evaluate_script(r"$rreplace(test \(disc 1\),\\s\\(disc \d+\\),)"),
            "test"
            )

    def test_cmd_rsearch(self):
        self.failUnlessEqual(
            self.tagz.evaluate_script(r"$rsearch(test \(disc 1\),\\(disc \(\d+\)\\))"),
            "1"
            )


class TagzParserTest(unittest.TestCase):

    def setUp(self):
        self.tagz = Tagz(ComponentManager())

    def test_arguments(self):
        self.failUnlessEqual(
            self.tagz.evaluate_script(r"$rreplace(test \(disc 1\),\\s\\(disc \d+\\),)"),
            "test"
            )
