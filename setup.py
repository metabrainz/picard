#!/usr/bin/env python

from distutils.core import setup, Command

class cmd_test(Command):
    description = "run automated tests"
    user_options = [
        ("tests=", None, "list of tests to run (default all)"), 
        ("verbosity=", "v", "verbosity"), 
        ]

    def initialize_options(self):
        self.tests = []
        self.verbosity = 1

    def finalize_options(self):
        if self.tests: 
            self.tests = self.tests.split(",")
        if self.verbosity:
            self.verbosity = int(self.verbosity)

    def run(self):
        import os.path
        import glob
        import unittest

        names = []
        for filename in glob.glob("test/test_*.py"):
            name = os.path.splitext(os.path.basename(filename))[0]
            if not self.tests or name in self.tests:
                names.append("test." + name)

        tests = unittest.defaultTestLoader.loadTestsFromNames(names)
        t = unittest.TextTestRunner(verbosity=self.verbosity)
        t.run(tests)


setup(cmdclass={'test': cmd_test})

