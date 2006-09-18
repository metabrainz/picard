#!/usr/bin/env python

import glob
import os.path
from distutils import log
from distutils.command.build import build
from distutils.core import setup, Command
from distutils.dep_util import newer
from distutils.dist import Distribution

args = {
    'name': 'picard',
    'version': '1.0',
    'description': 'The next generation MusicBrainz tagger',
    'url': 'http://wiki.musicbrainz.org/PicardTagger',
    'package_dir': {'picard': 'picard'},
    'packages': ('picard', 'picard.ui', 'picard.ui.options', 'picard.browser'),
    'locales': [('picard', os.path.split(po)[1][:-3], po) for po in glob.glob('po/*.po')]
}


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


class cmd_build_locales(Command):
    description = 'build locale files'
    user_options = [
        ('build-dir=', 'd', "directory to build to"),
        ('inplace', 'i', "ignore build-lib and put compiled locales into the 'locale' directory"),
    ]

    def initialize_options(self):
        self.build_dir = None
        self.inplace = 0

    def finalize_options (self):
        self.set_undefined_options('build', ('build_locales', 'build_dir'))
        self.locales = self.distribution.locales

    def run(self):
        for domain, locale, po in self.locales:
            if self.inplace:
                path = os.path.join('locale', locale, 'LC_MESSAGES')
            else:
                path = os.path.join(self.build_dir, locale, 'LC_MESSAGES')
            mo = os.path.join(path, '%s.mo' % domain)
            self.mkpath(path)
            self.spawn(['msgfmt', '-o', mo, po]) 

Distribution.locales = None 


class cmd_build(build):

    user_options = build.user_options + [
        ('build-locales=', 'd', "build directory for locale files"),
    ]

    sub_commands = build.sub_commands + [
        ('build_locales', None),
    ]
    
    def initialize_options(self):
        build.initialize_options(self)
        self.build_locales = None
    
    def finalize_options(self):
        build.finalize_options(self)
        if self.build_locales is None:
            self.build_locales = os.path.join(self.build_base, 'locale') 


class cmd_build_ui(Command):
    description = "build Qt UI files and resources"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from PyQt4 import uic
        for uifile in glob.glob("ui/*.ui"):
            pyfile = "ui_%s.py" % os.path.splitext(os.path.basename(uifile))[0]
            pyfile = os.path.join("picard", "ui", pyfile)
            if newer(uifile, pyfile):
                log.info("compiling %s -> %s", uifile, pyfile)
                uic.compileUi(uifile, file(pyfile, "w"), translator="_")
        qrcfile = os.path.join("resources", "picard.qrc")
        pyfile = os.path.join("picard", "resources.py")
        build_resources = False
        if newer("resources/picard.qrc", pyfile):
            build_resources = True
        for datafile in glob.glob("resources/images/*.*"):
            if newer(datafile, pyfile):
                build_resources = True
                break
        if build_resources:
            log.info("compiling %s -> %s", qrcfile, pyfile)
            os.system("pyrcc4 %s -o %s" % (qrcfile, pyfile))


class cmd_clean_ui(Command):
    description = "clean up compiled Qt UI files and resources"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from PyQt4 import uic
        for uifile in glob.glob("ui/*.ui"):
            pyfile = "ui_%s.py" % os.path.splitext(os.path.basename(uifile))[0]
            pyfile = os.path.join("picard", "ui", pyfile)
            try:
                os.unlink(pyfile)
                log.info("removing %s", pyfile)
            except OSError:
                log.warn("'%s' does not exist -- can't clean it", pyfile)
        pyfile = os.path.join("picard", "resources.py")
        try:
            os.unlink(pyfile)
            log.info("removing %s", pyfile)
        except OSError:
            log.warn("'%s' does not exist -- can't clean it", pyfile)


args['cmdclass'] = {
    'test': cmd_test,
    'build': cmd_build,
    'build_locales': cmd_build_locales,
    'build_ui': cmd_build_ui,
    'clean_ui': cmd_clean_ui,
}

setup(**args)

