#!/usr/bin/env python

import glob
import os.path
import sys
from ConfigParser import RawConfigParser
from distutils import log
from distutils.command.build import build
from distutils.command.config import config
from distutils.command.install import install as install
from distutils.core import setup, Command, Extension
from distutils.dep_util import newer
from distutils.dist import Distribution
from picard import __version__


if sys.version_info < (2, 4):
    print "*** You need Python 2.4 or higher to use Picard."


defaults = {
    'build': {
        'with-directshow': 'False',
        'with-avcodec': 'False',
        'with-gstreamer': 'False',
        'with-quicktime': 'False',
        'with-libofa': 'False',
    },
    'avcodec': {'cflags': '', 'libs': ''},
    'directshow': {'cflags': '', 'libs': ''},
    'gstreamer': {'cflags': '', 'libs': ''},
    'quicktime': {'cflags': '', 'libs': ''},
    'libofa': {'cflags': '', 'libs': ''},
}
cfg = RawConfigParser()
for section, values in defaults.items():
    cfg.add_section(section)
    for option, value in values.items():
        cfg.set(section, option, value)
cfg.read(['build.cfg'])


ext_modules = [
    Extension('picard.util.astrcmp', sources=['picard/util/astrcmp.cpp']),
]

if cfg.getboolean('build', 'with-libofa'):
    ext_modules.append(
        Extension('picard.musicdns.ofa', sources=['picard/musicdns/ofa.c'],
                  extra_compile_args=cfg.get('libofa', 'cflags').split(),
                  extra_link_args=cfg.get('libofa', 'libs').split()))

if cfg.getboolean('build', 'with-directshow'):
    ext_modules.append(
        Extension('picard.musicdns.directshow',
                  sources=['picard/musicdns/directshow.cpp'],
                  extra_compile_args=cfg.get('directshow', 'cflags').split(),
                  extra_link_args=cfg.get('directshow', 'libs').split()))

if cfg.getboolean('build', 'with-quicktime'):
    ext_modules.append(
        Extension('picard.musicdns.quicktime',
                  sources=['picard/musicdns/quicktime.c'],
                  extra_compile_args=cfg.get('quicktime', 'cflags').split(),
                  extra_link_args=cfg.get('quicktime', 'libs').split()))

if cfg.getboolean('build', 'with-avcodec'):
    ext_modules.append(
        Extension('picard.musicdns.avcodec',
                  sources=['picard/musicdns/avcodec.cpp'],
                  extra_compile_args=cfg.get('avcodec', 'cflags').split(),
                  extra_link_args=cfg.get('avcodec', 'libs').split()))

if cfg.getboolean('build', 'with-gstreamer'):
    ext_modules.append(
        Extension('picard.musicdns.gstreamer',
                  sources=['picard/musicdns/gstreamer.c'],
                  extra_compile_args=cfg.get('gstreamer', 'cflags').split(),
                  extra_link_args=cfg.get('gstreamer', 'libs').split()))


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
    description = 'install locale files'

    def initialize_options(self):
        pass

    def finalize_options (self):
        pass

    def run(self):
        self.run_command('build_locales')
        # TODO install them


class picard_install(install):

    user_options = install.user_options + [
        ('install-locales=', None,
         "installation directory for locales"),
        ('localedir=', None, ''),
    ]

    sub_commands = install.sub_commands + [
        ('install_locales', None),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.install_locales = None
        self.localedir = None

    def finalize_options(self):
        install.finalize_options(self)
        if self.install_locales is None:
            self.install_locales = '$base/share/locale'
            self._expand_attrs(['install_locales'])
        self.install_locales = os.path.normpath(self.install_locales)
        self.localedir = self.install_locales
        # can't use set_undefined_options :/
        self.distribution.get_command_obj('build').localedir = self.localedir
        if self.root is not None:
            self.change_roots('locales')

    def run(self):
        install.run(self)


class picard_build(build):

    user_options = build.user_options + [
        ('build-locales=', 'd', "build directory for locale files"),
    ]

    sub_commands = build.sub_commands + [
        ('build_locales', None),
    ]

    def initialize_options(self):
        build.initialize_options(self)
        self.build_locales = None
        self.localedir = None

    def finalize_options(self):
        build.finalize_options(self)
        if self.build_locales is None:
            self.build_locales = os.path.join(self.build_base, 'locale')

    def run(self):
        log.info('generating scripts/picard from scripts/picard.in')
        generate_file('scripts/picard.in', 'scripts/picard', {'localedir': self.localedir})
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


class picard_config(config):

    def run(self):
        print 'checking for pkg-cfg...',
        have_pkgconfig = False
        if os.system('pkg-config --version >%s 2>%s' % (os.path.devnull, os.path.devnull)) == 0:
            print 'yes'
            have_pkgconfig = True
        else:
            print 'no'

        print 'checking for libofa...',
        if have_pkgconfig:
            self.pkgconfig_check_module('libofa', 'libofa')
        else:
            self.check_lib('libofa', 'ofa_create_print', ['ofa1/ofa.h'], [['ofa'], ['libofa']])

        print 'checking for libavcodec/libavformat...',
        if have_pkgconfig:
            self.pkgconfig_check_module('avcodec', 'libavcodec libavformat')
        else:
            self.check_lib('avcodec', 'av_open_input_file', ['avcodec.h', 'avformat.h'], [['avcodec', 'avformat'], ['avcodec-51', 'avformat-51']])

        print 'checking for gstreamer-0.10...',
        if have_pkgconfig:
            self.pkgconfig_check_module('gstreamer', 'gstreamer-0.10')
        else:
            print 'no (FIXME: add non-pkg-config check)'
            cfg.set('build', 'with-gstreamer', False)

        print 'checking for directshow...',
        if sys.platform == 'win32':
            print 'yes'
            cfg.set('build', 'with-directshow', True)
            cfg.set('directshow', 'cflags', '')
            cfg.set('directshow', 'libs', 'strmiids.lib')
        else:
            print 'no'
            cfg.set('build', 'with-directshow', False)

        print 'saving build.cfg'
        cfg.write(file('build.cfg', 'wt'))


    def pkgconfig_exists(self, module):
        if os.system('pkg-config --exists %s' % module) == 0:
            return True

    def pkgconfig_cflags(self, module):
        pkgcfg = os.popen('pkg-config --cflags %s' % module)
        ret = pkgcfg.readline().strip()
        pkgcfg.close()
        return ret

    def pkgconfig_libs(self, module):
        pkgcfg = os.popen('pkg-config --libs %s' % module)
        ret = pkgcfg.readline().strip()
        pkgcfg.close()
        return ret

    def pkgconfig_check_module(self, name, module):
        print '(pkg-config)',
        if self.pkgconfig_exists(module):
            print 'yes'
            cfg.set('build', 'with-' + name, True)
            cfg.set(name, 'cflags', self.pkgconfig_cflags(module))
            cfg.set(name, 'libs', self.pkgconfig_libs(module))
        else:
            print 'no'
            cfg.set('build', 'with-' + name, False)

    def check_lib(self, name, function, includes, libraries):
        for libs in libraries:
            res = self.try_link(
                "%s\nvoid main() { void *tmp = (void *)%s; }" % (
                    "\n".join('#include <%s>' % i for i in includes),
                    function),
                libraries=libs, lang='c++')
            if res:
                print 'yes'
                cfg.set('build', 'with-' + name, True)
                cfg.set(name, 'cflags', '')
                # FIXME: gcc format?
                cfg.set(name, 'libs', ' '.join(l + '.lib' for l in libs))
                return
        print 'no'
        cfg.set('build', 'with-' + name, False)


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
    'cmdclass': {
        'test': picard_test,
        'build': picard_build,
        'build_locales': picard_build_locales,
        'build_ui': picard_build_ui,
        'clean_ui': picard_clean_ui,
        'config': picard_config,
        'install': picard_install,
        'install_locales': picard_install_locales,
    },
    'scripts': ['scripts/picard'],
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
            self.distribution.data_files.append(
                ("imageformats", ["C:\\Qt\\4.2.3\\plugins\\imageformats\\qjpeg1.dll"]))

            py2exe.run(self)
            print "*** creating the NSIS setup script ***"
            pathname = "installer/picard-setup.nsi"
            generate_file(pathname + ".in", pathname, 
                          {'name': 'MusicBrainz Picard',
                           'version': __version__})
            print "*** compiling the NSIS setup script ***"
            from ctypes import windll
            res = windll.shell32.ShellExecuteA(0, "compile", pathname, None, None, 0)
            if res < 32:
                raise RuntimeError, "ShellExecute failed, error %d" % res

    args['cmdclass']['bdist_nsis'] = bdist_nsis
    args['windows'] = [{
        'script': 'scripts/picard',
        'icon_resources': [(1, 'picard.ico')],
    }]
    args['options'] = {
        'bdist_nsis': {
            'includes': ['sip'] + [e.name for e in ext_modules],
        },
    }
except ImportError:
    py2exe = None


try:
    import py2app
    args['app'] = ['scripts/picard']
except ImportError:
    py2app = None


# FIXME: this should check for the actual command ('install' vs. 'bdist_nsis', 'py2app', ...), not installed libraries
if py2exe is None and py2app is None:
    args['data_files'].append(('share/icons', ('picard-16.png', 'picard-32.png')))
    args['data_files'].append(('share/applications', ('picard.desktop',)))


setup(**args)
