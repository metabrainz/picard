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

