#!/usr/bin/env python

import glob
import os.path
import sys
from distutils import log
from distutils.command.build import build
from distutils.command.config import config
from distutils.core import setup, Command, Extension
from distutils.dep_util import newer
from distutils.dist import Distribution
from picard import __version__

if sys.version_info < (2, 4):
    print "*** You need Python 2.4 or higher to use Picard."

if __version__.endswith('dev'):
    import time
    __version__ = __version__ + time.strftime('%Y%m%d')

ext_modules = [
    Extension('picard.util.astrcmp', sources=['picard/util/astrcmp.cpp']),
]

# libofa
if sys.platform == 'win32':
    ofa_library_name = 'libofa'
else:
    ofa_library_name = 'ofa'
ofa_ext = Extension('picard.musicdns.ofa', sources=['picard/musicdns/ofa.c'],
                    libraries=[ofa_library_name])
ext_modules.append(ofa_ext)

# DirectShow
if sys.platform == "win32":
    directshow_ext = Extension('picard.musicdns.directshow',
                               sources=['picard/musicdns/directshow.cpp'],
                               libraries=['strmiids', 'libofa'])
    ext_modules.append(directshow_ext)

# QuickTime
if sys.platform == "darwin":
    quicktime_ext = Extension('picard.musicdns.quicktime',
                               sources=['picard/musicdns/quicktime.c'],
                               libraries=[])
    ext_modules.append(quicktime_ext)

# GStreamer
if sys.platform != "win32" and sys.platform != "darwin":
    pkgcfg = os.popen('pkg-config --cflags gstreamer-0.10')
    cflags = pkgcfg.readline().strip().split()
    pkgcfg.close()
    pkgcfg = os.popen('pkg-config --libs gstreamer-0.10')
    libs = pkgcfg.readline().strip().split()
    pkgcfg.close()
    gstreamer_ext = Extension('picard.musicdns.gstreamer',
                               sources=['picard/musicdns/gstreamer.c'],
                               libraries=[],
                               extra_compile_args=cflags,
                               extra_link_args=libs,
                               )
    ext_modules.append(gstreamer_ext)
    
    pkgcfg = os.popen('pkg-config --cflags libavcodec libavformat')
    cflags = pkgcfg.readline().strip().split()
    pkgcfg.close()
    pkgcfg = os.popen('pkg-config --libs libavcodec libavformat')
    libs = pkgcfg.readline().strip().split()
    pkgcfg.close()
    avcodec_ext = Extension('picard.musicdns.avcodec',
                               sources=['picard/musicdns/avcodec.c'],
                               libraries=[],
                               extra_compile_args=cflags,
                               extra_link_args=libs
                               )
    ext_modules.append(avcodec_ext)

args = {
    'name': 'picard',
    'version': __version__,
    'description': 'The next generation MusicBrainz tagger',
    'url': 'http://wiki.musicbrainz.org/PicardTagger',
    'package_dir': {'picard': 'picard'},
    'packages': ('picard', 'picard.browser', 'picard.musicdns',
                 'picard.plugins', 'picard.formats',
                 'picard.formats.mutagenext', 'picard.ui',
                 'picard.ui.options', 'picard.util'),
    'locales': [('picard', os.path.split(po)[1][:-3], po) for po in glob.glob('po/*.po')],
    'ext_modules': ext_modules,
    'data_files': [],
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
                uic.compileUi(uifile, file(pyfile, "w"), gettext=True)
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

#class cmd_config(config):
#
#    user_options = config.user_options + [
#        ("ofa-include-dirs=", None,
#         "directories to search for OFA header files"),
#        ("ofa-library-dirs=", None,
#         "directories to search for OFA library files"),
#        ]
#
#    def initialize_options (self):
#        config.initialize_options(self)
#        self.ofa_include_dirs = None
#        self.ofa_library_dirs = None
#
#    def run(self):
#        have_ofa = self.check_lib("libofa", self.ofa_library_dirs,
#                                  ["ofa1/ofa.h"], self.ofa_include_dirs)

args['cmdclass'] = {
    'test': cmd_test,
    'build': cmd_build,
    'build_locales': cmd_build_locales,
    'build_ui': cmd_build_ui,
    'clean_ui': cmd_clean_ui,
#    'config': cmd_config,
}

def generate_file(infilename, outfilename, variables):
    f = file(infilename, "rt")
    content = f.read()
    f.close()
    content = content % variables
    f = file(outfilename, "wt")
    f.write(content)
    f.close() 
    
try:
    from py2exe.build_exe import py2exe
    class bdist_nsis(py2exe):
        def run(self):
            generate_file('scripts/picard.py2exe.in', 'scripts/picard', {})
            self.distribution.data_files.append(
                ("", ["discid.dll", "libfftw3-3.dll", "libofa.dll"]))

            py2exe.run(self)
            
            print "*** creating the NSIS setup script ***"
            pathname = "installer/picard-setup.nsi"
            generate_file(pathname + ".in", pathname, 
                          {'name': 'MusicBrainz Picard',
                           'version': __version__})
        
            print "*** compiling the NSIS setup script ***"
            from ctypes import windll
            windll.shell32.ShellExecuteA(0, "compile", pathname, None, None, 0)

    args['cmdclass']['bdist_nsis'] = bdist_nsis
    args['windows'] = [{
        'script': 'scripts/picard',
        'icon_resources': [(1, 'picard.ico')],
    }]

except ImportError:
    pass

setup(**args)
