#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from distutils import log
from distutils.command.build import build
from distutils.command.install import install as install
from distutils.dep_util import newer
from distutils.spawn import find_executable
import glob
from io import StringIO
import os
from os import path
import re
import sys
import tempfile

from setuptools import (
    Command,
    Extension,
    setup,
)
from setuptools.dist import Distribution

from picard import (
    PICARD_VERSION,
    __version__,
)
from picard.const.sys import (
    IS_LINUX,
    IS_WIN,
)


if sys.version_info < (3, 5):
    sys.exit("ERROR: You need Python 3.5 or higher to use Picard.")

PACKAGE_NAME = "picard"

ext_modules = [
    Extension('picard.util._astrcmp', sources=['picard/util/_astrcmp.c']),
]

tx_executable = find_executable('tx')


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
        # In case the verbosity flag is used, verbosity is None
        if not self.verbosity:
            self.verbosity = 2
        # Convert to appropriate verbosity if passed by --verbosity option
        self.verbosity = int(self.verbosity)

    def run(self):
        import unittest

        names = []
        for filename in glob.glob("test/test_*.py"):
            name = os.path.splitext(os.path.basename(filename))[0]
            if not self.tests or name in self.tests:
                names.append("test." + name)

        tests = unittest.defaultTestLoader.loadTestsFromNames(names)
        t = unittest.TextTestRunner(verbosity=self.verbosity)
        testresult = t.run(tests)
        if not testresult.wasSuccessful():
            sys.exit("At least one test failed.")


class picard_build_locales(Command):
    description = 'build locale files'
    user_options = [
        ('build-dir=', 'd', "directory to build to"),
        ('inplace', 'i', "ignore build-lib and put compiled locales into the 'locale' directory"),
    ]

    def initialize_options(self):
        self.build_dir = None
        self.inplace = 0

    def finalize_options(self):
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
        ('build-dir=', 'b', "build directory (where to install from)"),
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
        ('disable-autoupdate', None, 'disable update checking and hide settings for it'),
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
            self.install_locales = os.path.join(self.install_data, 'share', 'locale')
            if self.root and self.install_locales.startswith(self.root):
                self.install_locales = self.install_locales[len(self.root):]
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
        ('disable-autoupdate', None, 'disable update checking and hide settings for it'),
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
        log.info('generating scripts/%s from scripts/picard.in', PACKAGE_NAME)
        generate_file('scripts/picard.in', 'scripts/' + PACKAGE_NAME, {'localedir': self.localedir, 'autoupdate': not self.disable_autoupdate})
        if IS_WIN:
            # Temporarily setting it to this value to generate a nice name for Windows app
            args['name'] = 'MusicBrainz Picard'
            file_version = PICARD_VERSION[0:3] + PICARD_VERSION[4:]
            args['file_version'] = '.'.join([str(v) for v in file_version])
            generate_file('installer/picard-setup.nsi.in', 'installer/picard-setup.nsi', args)
            version_args = {
                'filevers': str(file_version),
                'prodvers': str(file_version),
            }
            generate_file('win-version-info.txt.in', 'win-version-info.txt', {**args, **version_args})
            args['name'] = 'picard'
        elif IS_LINUX:
            self.run_command('build_appdata')
        build.run(self)


def py_from_ui(uifile):
    return "ui_%s.py" % os.path.splitext(os.path.basename(uifile))[0]


def py_from_ui_with_defaultdir(uifile):
    return os.path.join("picard", "ui", py_from_ui(uifile))


def ui_files():
    for uifile in glob.glob("ui/*.ui"):
        yield (uifile, py_from_ui_with_defaultdir(uifile))


class picard_build_ui(Command):
    description = "build Qt UI files and resources"
    user_options = [
        ("files=", None, "comma-separated list of files to rebuild"),
    ]

    def initialize_options(self):
        self.files = []

    def finalize_options(self):
        if self.files:
            files = []
            for f in self.files.split(","):
                head, tail = os.path.split(f)
                m = re.match(r'(?:ui_)?([^.]+)', tail)
                if m:
                    name = m.group(1)
                else:
                    log.warn('ignoring %r (cannot extract base name)' % f)
                    continue
                uiname = name + '.ui'
                uifile = os.path.join(head, uiname)
                if os.path.isfile(uifile):
                    pyfile = os.path.join(os.path.dirname(uifile),
                                          py_from_ui(uifile))
                    files.append((uifile, pyfile))
                else:
                    uifile = os.path.join('ui', uiname)
                    if os.path.isfile(uifile):
                        files.append((uifile,
                                      py_from_ui_with_defaultdir(uifile)))
                    else:
                        log.warn('ignoring %r' % f)
            self.files = files

    def run(self):
        from PyQt5 import uic
        _translate_re = (
            re.compile(
                r'QtGui\.QApplication.translate\(.*?, (.*?), None, '
                r'QtGui\.QApplication\.UnicodeUTF8\)'),
            re.compile(
                r'\b_translate\(.*?, (.*?)(?:, None)?\)')
        )

        def compile_ui(uifile, pyfile):
            log.info("compiling %s -> %s", uifile, pyfile)
            tmp = StringIO()
            uic.compileUi(uifile, tmp)
            source = tmp.getvalue()
            rc = re.compile(r'\n\n#.*?(?=\n\n)', re.MULTILINE | re.DOTALL)
            comment = ("\n\n# Automatically generated - don't edit.\n"
                       "# Use `python setup.py %s` to update it."
                       % _get_option_name(self))
            for r in list(_translate_re):
                source = r.sub(r'_(\1)', source)
                source = rc.sub(comment, source)
            f = open(pyfile, "w")
            f.write(source)
            f.close()

        if self.files:
            for uifile, pyfile in self.files:
                compile_ui(uifile, pyfile)
        else:
            for uifile, pyfile in ui_files():
                if newer(uifile, pyfile):
                    compile_ui(uifile, pyfile)

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
        for uifile, pyfile in ui_files():
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


class picard_build_appdata(Command):
    description = 'Build appdata metadata file'
    user_options = []

    re_release = re.compile('Version (?P<version>\d+(?:\.\d+){1,2}) - (?P<date>\d{4}-\d{2}-\d{2})')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with tempfile.NamedTemporaryFile(prefix='org.musicbrainz.Picard.appdata.',
                                         suffix='.xml') as tmp_file:
            self.spawn([
                'msgfmt', '--xml',
                '--template=org.musicbrainz.Picard.appdata.xml.in',
                '-d', 'po/appstream',
                '-o', tmp_file.name,
            ])
            self.add_release_list(tmp_file.name)

    def add_release_list(self, source_file):
        template = '<release date="{date}" version="{version}"/>'
        with open('NEWS.txt', 'r') as newsfile:
            news = newsfile.read()
            releases = [template.format(**m.groupdict()) for m in self.re_release.finditer(news)]
            args = {'releases': '\n    '.join(releases)}
            generate_file(source_file, 'org.musicbrainz.Picard.appdata.xml', args)


class picard_regen_appdata_pot_file(Command):
    description = 'Regenerate translations from appdata metadata template'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        output_dir = 'po/appstream/'
        pot_file = os.path.join(output_dir, 'picard-appstream.pot')
        self.spawn([
            'xgettext',
            '--output', pot_file,
            '--language=appdata',
            'org.musicbrainz.Picard.appdata.xml.in',
        ])
        for filepath in glob.glob(os.path.join(output_dir, '*.po')):
            self.spawn([
                'msgmerge',
                '--update',
                filepath,
                pot_file
            ])


class picard_get_po_files(Command):
    description = "Retrieve po files from transifex"
    minimum_perc_default = 5
    user_options = [
        ('minimum-perc=', 'm',
         "Specify the minimum acceptable percentage of a translation (default: %d)" % minimum_perc_default)
    ]

    def initialize_options(self):
        self.minimum_perc = self.minimum_perc_default

    def finalize_options(self):
        self.minimum_perc = int(self.minimum_perc)

    def run(self):
        if tx_executable is None:
            sys.exit('Transifex client executable (tx) not found.')
        txpull_cmd = [
            tx_executable,
            'pull',
            '--force',
            '--all',
            '--minimum-perc=%d' % self.minimum_perc
        ]
        self.spawn(txpull_cmd)


_regen_pot_description = "Regenerate po/picard.pot, parsing source tree for new or updated strings"
try:
    from babel import __version__ as babel_version
    from babel.messages import frontend as babel

    def versiontuple(v):
        return tuple(map(int, (v.split("."))))

    # input_dirs are incorrectly handled in babel versions < 1.0
    # http://babel.edgewall.org/ticket/232
    input_dirs_workaround = versiontuple(babel_version) < (1, 0, 0)

    class picard_regen_pot_file(babel.extract_messages):
        description = _regen_pot_description

        def initialize_options(self):
            # cannot use super() with old-style parent class
            babel.extract_messages.initialize_options(self)
            self.output_file = 'po/picard.pot'
            self.input_dirs = 'picard'
            if self.input_dirs and input_dirs_workaround:
                self._input_dirs = self.input_dirs

        def finalize_options(self):
            babel.extract_messages.finalize_options(self)
            if input_dirs_workaround and self._input_dirs:
                self.input_dirs = re.split(r',\s*', self._input_dirs)

except ImportError:
    class picard_regen_pot_file(Command):
        description = _regen_pot_description
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            sys.exit("Babel is required to use this command (see po/README.md)")


def _get_option_name(obj):
    """Returns the name of the option for specified Command object"""
    for name, klass in obj.distribution.cmdclass.items():
        if obj.__class__ == klass:
            return name
    raise Exception("No such command class")


class picard_update_constants(Command):
    description = "Regenerate attributes.py and countries.py"
    user_options = [
        ('skip-pull', None, "skip the tx pull steps"),
    ]
    boolean_options = ['skip-pull']

    def initialize_options(self):
        self.skip_pull = None

    def finalize_options(self):
        self.locales = self.distribution.locales

    def run(self):
        if tx_executable is None:
            sys.exit('Transifex client executable (tx) not found.')

        from babel.messages import pofile

        if not self.skip_pull:
            txpull_cmd = [
                tx_executable,
                'pull',
                '--force',
                '--resource=musicbrainz.attributes,musicbrainz.countries',
                '--source',
                '--language=none',
            ]
            self.spawn(txpull_cmd)

        countries = dict()
        countries_potfile = os.path.join('po', 'countries', 'countries.pot')
        isocode_comment = 'iso.code:'
        with open(countries_potfile, 'rb') as f:
            log.info('Parsing %s' % countries_potfile)
            po = pofile.read_po(f)
            for message in po:
                if not message.id or not isinstance(message.id, str):
                    continue
                for comment in message.auto_comments:
                    if comment.startswith(isocode_comment):
                        code = comment.replace(isocode_comment, '')
                        countries[code] = message.id
            if countries:
                self.countries_py_file(countries)
            else:
                sys.exit('Failed to extract any country code/name !')

        attributes = dict()
        attributes_potfile = os.path.join('po', 'attributes', 'attributes.pot')
        extract_attributes = (
            'DB:cover_art_archive.art_type/name',
            'DB:medium_format/name',
            'DB:release_group_primary_type/name',
            'DB:release_group_secondary_type/name',
        )
        with open(attributes_potfile, 'rb') as f:
            log.info('Parsing %s' % attributes_potfile)
            po = pofile.read_po(f)
            for message in po:
                if not message.id or not isinstance(message.id, str):
                    continue
                for loc, pos in message.locations:
                    if loc in extract_attributes:
                        attributes["%s:%03d" % (loc, pos)] = message.id
            if attributes:
                self.attributes_py_file(attributes)
            else:
                sys.exit('Failed to extract any attribute !')

    def countries_py_file(self, countries):
        header = ("# -*- coding: utf-8 -*-\n"
                  "# Automatically generated - don't edit.\n"
                  "# Use `python setup.py {option}` to update it.\n"
                  "\n"
                  "RELEASE_COUNTRIES = {{\n")
        line   =  "    '{code}': '{name}',\n"
        footer =  "}}\n"
        filename = os.path.join('picard', 'const', 'countries.py')
        with open(filename, 'w') as countries_py:
            def write(s, **kwargs):
                countries_py.write(s.format(**kwargs))

            write(header, option=_get_option_name(self))
            for code, name in sorted(countries.items(), key=lambda t: t[0]):
                write(line, code=code, name=name.replace("'", "\\'"))
            write(footer)
            log.info("%s was rewritten (%d countries)" % (filename,
                                                          len(countries)))

    def attributes_py_file(self, attributes):
        header = ("# -*- coding: utf-8 -*-\n"
                  "# Automatically generated - don't edit.\n"
                  "# Use `python setup.py {option}` to update it.\n"
                  "\n"
                  "MB_ATTRIBUTES = {{\n")
        line   =  "    '{key}': '{value}',\n"
        footer =  "}}\n"
        filename = os.path.join('picard', 'const', 'attributes.py')
        with open(filename, 'w') as attributes_py:
            def write(s, **kwargs):
                attributes_py.write(s.format(**kwargs))

            write(header, option=_get_option_name(self))
            for key, value in sorted(attributes.items(), key=lambda i: i[0]):
                write(line, key=key, value=value.replace("'", "\\'"))
            write(footer)
            log.info("%s was rewritten (%d attributes)" % (filename,
                                                           len(attributes)))


class picard_patch_version(Command):
    description = "Update PICARD_BUILD_VERSION_STR for daily builds"
    user_options = [
        ('platform=', 'p', "platform for the build version, ie. osx or win"),
    ]

    def initialize_options(self):
        self.platform = sys.platform

    def finalize_options(self):
        pass

    def run(self):
        self.patch_version('picard/__init__.py')

    def patch_version(self, filename):
        regex = re.compile(r'^PICARD_BUILD_VERSION_STR\s*=.*$', re.MULTILINE)
        with open(filename, 'r+b') as f:
            source = (f.read()).decode()
            build = self.platform + '_' + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
            patched_source = regex.sub('PICARD_BUILD_VERSION_STR = "%s"' % build, source).encode()
            f.seek(0)
            f.write(patched_source)
            f.truncate()


def cflags_to_include_dirs(cflags):
    cflags = cflags.split()
    include_dirs = []
    for cflag in cflags:
        if cflag.startswith('-I'):
            include_dirs.append(cflag[2:])
    return include_dirs


def _picard_get_locale_files():
    locales = []
    path_domain = {
        'po': 'picard',
        os.path.join('po', 'countries'): 'picard-countries',
        os.path.join('po', 'attributes'): 'picard-attributes',
    }
    for path, domain in path_domain.items():
        for filepath in glob.glob(os.path.join(path, '*.po')):
            filename = os.path.basename(filepath)
            locale = os.path.splitext(filename)[0]
            locales.append((domain, locale, filepath))
    return locales


def _explode_path(path):
    """Return a list of components of the path (ie. "/a/b" -> ["a", "b"])"""
    components = []
    while True:
        (path, tail) = os.path.split(path)
        if tail == "":
            components.reverse()
            return components
        components.append(tail)


def _picard_packages():
    """Build a tuple containing each module under picard/"""
    packages = []
    for subdir, dirs, files in os.walk("picard"):
        packages.append(".".join(_explode_path(subdir)))
    return tuple(sorted(packages))


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

args = {
    'name': PACKAGE_NAME,
    'version': __version__,
    'description': 'The next generation MusicBrainz tagger',
    'keywords': 'MusicBrainz metadata tagger picard',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'url': 'https://picard.musicbrainz.org/',
    'package_dir': {'picard': 'picard'},
    'packages': _picard_packages(),
    'locales': _picard_get_locale_files(),
    'ext_modules': ext_modules,
    'data_files': [],
    'cmdclass': {
        'test': picard_test,
        'build': picard_build,
        'build_locales': picard_build_locales,
        'build_ui': picard_build_ui,
        'clean_ui': picard_clean_ui,
        'build_appdata': picard_build_appdata,
        'regen_appdata_pot_file': picard_regen_appdata_pot_file,
        'install': picard_install,
        'install_locales': picard_install_locales,
        'update_constants': picard_update_constants,
        'get_po_files': picard_get_po_files,
        'regen_pot_file': picard_regen_pot_file,
        'patch_version': picard_patch_version,
    },
    'scripts': ['scripts/' + PACKAGE_NAME],
    'install_requires': ['PyQt5', 'mutagen'],
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis'
    ]
}


def generate_file(infilename, outfilename, variables):
    with open(infilename, "rt") as f_in:
        with open(outfilename, "wt") as f_out:
            f_out.write(f_in.read() % variables)


def find_file_in_path(filename):
    for include_path in sys.path:
        file_path = os.path.join(include_path, filename)
        if os.path.exists(file_path):
            return file_path


args['data_files'] = [
    ('share/icons/hicolor/16x16/apps', ['resources/images/16x16/org.musicbrainz.Picard.png']),
    ('share/icons/hicolor/24x24/apps', ['resources/images/24x24/org.musicbrainz.Picard.png']),
    ('share/icons/hicolor/32x32/apps', ['resources/images/32x32/org.musicbrainz.Picard.png']),
    ('share/icons/hicolor/48x48/apps', ['resources/images/48x48/org.musicbrainz.Picard.png']),
    ('share/icons/hicolor/128x128/apps', ['resources/images/128x128/org.musicbrainz.Picard.png']),
    ('share/icons/hicolor/256x256/apps', ['resources/images/256x256/org.musicbrainz.Picard.png']),
    ('share/icons/hicolor/scalable/apps', ['resources/img-src/org.musicbrainz.Picard.svg']),
    ('share/applications', ('org.musicbrainz.Picard.desktop',)),
]

if IS_LINUX:
    args['data_files'].append(('share/metainfo', ['org.musicbrainz.Picard.appdata.xml']))

setup(**args)
