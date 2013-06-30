#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob, re
import os
import sys
from StringIO import StringIO
from ConfigParser import RawConfigParser
from picard import __version__

from picard.const import UI_LANGUAGES


if sys.version_info < (2, 6):
    print "*** You need Python 2.6 or higher to use Picard."


args = {}


try:
    from py2app.build_app import py2app
    do_py2app = True
    args['app'] = ['tagger.py']
    args['name'] = 'Picard'
    args['options'] = { 'py2app' :
       {
          'optimize'       : 2,
          'argv_emulation' : True,
          'iconfile'       : 'picard.icns',
          'frameworks'     : ['libiconv.2.dylib', 'libdiscid.0.dylib'],
          'resources'      : ['locale'],
          'includes'       : ['json', 'sip', 'PyQt4', 'picard.util.astrcmp'],
          'excludes'       : ['pydoc', 'PyQt4.QtDeclarative', 'PyQt4.QtDesigner', 'PyQt4.QtHelp', 'PyQt4.QtMultimedia',
                              'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtScriptTools', 'PyQt4.QtSql', 'PyQt4.QtSvg',
                              'PyQt4.QtTest', 'PyQt4.QtWebKit', 'PyQt4.QtXml', 'PyQt4.QtXmlPatterns', 'PyQt4.phonon'],
          'plist'    : { 'CFBundleName' : 'MusicBrainz Picard',
                         'CFBundleGetInfoString' : 'Picard, the next generation MusicBrainz tagger (see http://musicbrainz.org/doc/MusicBrainz_Picard)',
                         'CFBundleIdentifier':'org.musicbrainz.picard',
                         'CFBundleShortVersionString':__version__,
                         'CFBundleVersion': 'Picard ' + __version__,
                         'LSMinimumSystemVersion':'10.4.3',
                         'LSMultipleInstancesProhibited':'true',
                         # RAK: It biffed when I tried to include your accented characters, luks. :-(
                         'NSHumanReadableCopyright':'Copyright 2008 Lukas Lalinsky, Robert Kaye',
                        },
          'qt_plugins': ['imageformats/libqgif.dylib',
                         'imageformats/libqjpeg.dylib',
                         'imageformats/libqtiff.dylib',
                         'accessible/libqtaccessiblewidgets.dylib']
       },
    }

except ImportError:
    do_py2app = False

# this must be imported *after* py2app, because py2app imports setuptools
# which "patches" (read: screws up) the Extension class
from distutils import log
from distutils.command.build import build
from distutils.command.install import install as install
from distutils.core import setup, Command, Extension
from distutils.dep_util import newer
from distutils.dist import Distribution



ext_modules = [
    Extension('picard.util.astrcmp', sources=['picard/util/astrcmp.c']),
]


class picard_test(Command):
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


class picard_build_locales(Command):
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


class picard_install_locales(Command):
    description = "install locale files"
    user_options = [
        ('install-dir=', 'd', "directory to install locale files to"),
        ('build-dir=','b', "build directory (where to install from)"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ('skip-build', None, "skip the build steps"),
    ]
    boolean_options = ['force', 'skip-build']

    def initialize_options(self):
        self.install_dir = None
        self.build_dir = None
        self.force = 0
        self.skip_build = None
        self.outfiles = []

    def finalize_options(self):
        self.set_undefined_options('build', ('build_locales', 'build_dir'))
        self.set_undefined_options('install',
                                   ('install_locales', 'install_dir'),
                                   ('force', 'force'),
                                   ('skip_build', 'skip_build'),
                                  )

    def run(self):
        if not self.skip_build:
            self.run_command('build_locales')
        self.outfiles = self.copy_tree(self.build_dir, self.install_dir)

    def get_inputs(self):
        return self.locales or []

    def get_outputs(self):
        return self.outfiles


class picard_install(install):

    user_options = install.user_options + [
        ('install-locales=', None,
         "installation directory for locales"),
        ('localedir=', None, ''),
        ('disable-autoupdate', None, ''),
        ('disable-locales', None, ''),
    ]

    sub_commands = install.sub_commands

    def initialize_options(self):
        install.initialize_options(self)
        self.install_locales = None
        self.localedir = None
        self.disable_autoupdate = None
        self.disable_locales = None

    def finalize_options(self):
        install.finalize_options(self)
        if self.install_locales is None:
            self.install_locales = '$base/share/locale'
            self._expand_attrs(['install_locales'])
        self.install_locales = os.path.normpath(self.install_locales)
        self.localedir = self.install_locales
        # can't use set_undefined_options :/
        self.distribution.get_command_obj('build').localedir = self.localedir
        self.distribution.get_command_obj('build').disable_autoupdate = self.disable_autoupdate
        if self.root is not None:
            self.change_roots('locales')
        if self.disable_locales is None:
            self.sub_commands.append(('install_locales', None))

    def run(self):
        install.run(self)


class picard_build(build):

    user_options = build.user_options + [
        ('build-locales=', 'd', "build directory for locale files"),
        ('localedir=', None, ''),
        ('disable-autoupdate', None, ''),
        ('disable-locales', None, ''),
    ]

    sub_commands = build.sub_commands

    def initialize_options(self):
        build.initialize_options(self)
        self.build_locales = None
        self.localedir = None
        self.disable_autoupdate = None
        self.disable_locales = None

    def finalize_options(self):
        build.finalize_options(self)
        if self.build_locales is None:
            self.build_locales = os.path.join(self.build_base, 'locale')
        if self.localedir is None:
            self.localedir = '/usr/share/locale'
        if self.disable_autoupdate is None:
            self.disable_autoupdate = False
        if self.disable_locales is None:
            self.sub_commands.append(('build_locales', None))

    def run(self):
        if 'bdist_nsis' not in sys.argv: # somebody shoot me please
            log.info('generating scripts/picard from scripts/picard.in')
            generate_file('scripts/picard.in', 'scripts/picard', {'localedir': self.localedir, 'autoupdate': not self.disable_autoupdate})
        build.run(self)


class picard_build_ui(Command):
    description = "build Qt UI files and resources"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from PyQt4 import uic
        _translate_re = (
            re.compile(
                r'QtGui\.QApplication.translate\(.*?, (.*?), None, '
                r'QtGui\.QApplication\.UnicodeUTF8\)'),
            re.compile(
                r'\b_translate\(.*?, (.*?), None\)')
        )

        for uifile in glob.glob("ui/*.ui"):
            pyfile = "ui_%s.py" % os.path.splitext(os.path.basename(uifile))[0]
            pyfile = os.path.join("picard", "ui", pyfile)
            if newer(uifile, pyfile):
                log.info("compiling %s -> %s", uifile, pyfile)
                tmp = StringIO()
                uic.compileUi(uifile, tmp)
                source = tmp.getvalue()
                for r in list(_translate_re):
                    source = r.sub(r'_(\1)', source)
                f = open(pyfile, "w")
                f.write(source)
                f.close()
        from resources import compile, makeqrc
        makeqrc.main()
        compile.main()


class picard_clean_ui(Command):
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


def cflags_to_include_dirs(cflags):
    cflags = cflags.split()
    include_dirs = []
    for cflag in cflags:
        if cflag.startswith('-I'):
            include_dirs.append(cflag[2:])
    return include_dirs


args2 = {
    'name': 'picard',
    'version': __version__,
    'description': 'The next generation MusicBrainz tagger',
    'url': 'http://musicbrainz.org/doc/MusicBrainz_Picard',
    'package_dir': {'picard': 'picard'},
    'packages': ('picard', 'picard.browser',
                 'picard.plugins', 'picard.formats',
                 'picard.formats.mutagenext', 'picard.ui',
                 'picard.ui.options', 'picard.util'),
    'locales': [('picard', lang[0], os.path.join('po', lang[0]+".po")) for lang in UI_LANGUAGES],
    'ext_modules': ext_modules,
    'data_files': [],
    'cmdclass': {
        'test': picard_test,
        'build': picard_build,
        'build_locales': picard_build_locales,
        'build_ui': picard_build_ui,
        'clean_ui': picard_clean_ui,
        'install': picard_install,
        'install_locales': picard_install_locales,
    },
    'scripts': ['scripts/picard'],
}
args.update(args2)


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
                ("", ["discid.dll", "fpcalc.exe", "msvcr90.dll", "msvcp90.dll"]))
            for locale in self.distribution.locales:
                self.distribution.data_files.append(
                    ("locale/" + locale[1] + "/LC_MESSAGES",
                     ["build/locale/" + locale[1] + "/LC_MESSAGES/" + locale[0] + ".mo"]))
            self.distribution.data_files.append(
                ("imageformats", [find_file_in_path("PyQt4/plugins/imageformats/qgif4.dll"),
                                  find_file_in_path("PyQt4/plugins/imageformats/qjpeg4.dll"),
                                  find_file_in_path("PyQt4/plugins/imageformats/qtiff4.dll")]))
            self.distribution.data_files.append(
                ("accessible", [find_file_in_path("PyQt4/plugins/accessible/qtaccessiblewidgets4.dll")]))
            self.distribution.data_files.append(
                ("plugins", ["contrib/plugins/discnumber.py",
                             "contrib/plugins/classicdiscnumber.py",
                             "contrib/plugins/titlecase.py",
                             "contrib/plugins/featartist.py"]))

            py2exe.run(self)
            print "*** creating the NSIS setup script ***"
            pathname = "installer\picard-setup.nsi"
            generate_file(pathname + ".in", pathname,
                          {'name': 'MusicBrainz Picard',
                           'version': __version__,
                           'description': 'The next generation MusicBrainz tagger.',
                           'url': 'http://musicbrainz.org/doc/MusicBrainz_Picard',})
            print "*** compiling the NSIS setup script ***"
            from ctypes import windll
            operation = 'compile'
            res = windll.shell32.ShellExecuteA(0, operation, pathname, None, None, 0)
            if res < 32:
                raise RuntimeError, 'ShellExecute failed executing "%s %s", error %d' % (
                    operation, pathname, res)

    args['cmdclass']['bdist_nsis'] = bdist_nsis
    args['windows'] = [{
        'script': 'scripts/picard',
        'icon_resources': [(1, 'picard.ico')],
    }]
    args['options'] = {
        'bdist_nsis': {
            'includes': ['json', 'sip'] + [e.name for e in ext_modules],
            'excludes': ['ssl', 'socket', 'bz2'],
            'optimize': 2,
        },
    }
except ImportError:
    py2exe = None

def find_file_in_path(filename):
    for include_path in sys.path:
        file_path = os.path.join(include_path, filename)
        if os.path.exists(file_path):
            return file_path

if do_py2app:
    from subprocess import call
    from py2app.util import copy_file, find_app
    from PyQt4 import QtCore

    class BuildAPP(py2app):
        def run(self):
            py2app.run(self)

            # XXX Find and bundle fpcalc, since py2app can't.
            fpcalc = find_app("fpcalc")
            if fpcalc:
                dest_fpcalc = os.path.abspath("dist/MusicBrainz Picard.app/Contents/MacOS/fpcalc")
                copy_file(fpcalc, dest_fpcalc)
                os.chmod(dest_fpcalc, 0755)

    args['scripts'] = ['tagger.py']
    args['cmdclass']['py2app'] = BuildAPP

# FIXME: this should check for the actual command ('install' vs. 'bdist_nsis', 'py2app', ...), not installed libraries
if py2exe is None and do_py2app is False:
    args['data_files'].append(('share/icons/hicolor/16x16/apps', ['resources/images/16x16/picard.png']))
    args['data_files'].append(('share/icons/hicolor/24x24/apps', ['resources/images/24x24/picard.png']))
    args['data_files'].append(('share/icons/hicolor/32x32/apps', ['resources/images/32x32/picard.png']))
    args['data_files'].append(('share/icons/hicolor/48x48/apps', ['resources/images/48x48/picard.png']))
    args['data_files'].append(('share/icons/hicolor/128x128/apps', ['resources/images/128x128/picard.png']))
    args['data_files'].append(('share/icons/hicolor/256x256/apps', ['resources/images/256x256/picard.png']))
    args['data_files'].append(('share/applications', ('picard.desktop',)))


setup(**args)
