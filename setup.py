#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2014, 2017 Lukáš Lalinský
# Copyright (C) 2007 Santiago M. Mola
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008-2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2011-2012, 2014, 2016-2018 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012, 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014 Johannes Dewender
# Copyright (C) 2013-2015, 2017-2020 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Ville Skyttä
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2018 Abhinav Ohri
# Copyright (C) 2018 Kartik Ohri
# Copyright (C) 2018 virusMac
# Copyright (C) 2019 Kurt Mosiejczuk
# Copyright (C) 2020 Jason E. Hale
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import datetime
import glob
from io import StringIO
import logging as log
import os
import re
import stat
import sys
import tempfile

from setuptools import (
    Command,
    Extension,
    setup,
)
from setuptools.command.install import install
from setuptools.dist import Distribution


try:
    from setuptools.command.build import build
except ImportError:
    from distutils.command.build import build

# required for PEP 517
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))


from picard import (  # noqa: E402
    PICARD_APP_ID,
    PICARD_APP_NAME,
    PICARD_DESKTOP_NAME,
    PICARD_DISPLAY_NAME,
    PICARD_VERSION,
    PICARD_VERSION_STR_SHORT,
)


if sys.version_info < (3, 9):
    sys.exit("ERROR: You need Python 3.9 or higher to use Picard.")

PACKAGE_NAME = "picard"
APPDATA_FILE = PICARD_APP_ID + '.appdata.xml'
APPDATA_FILE_TEMPLATE = APPDATA_FILE + '.in'
DESKTOP_FILE = PICARD_APP_ID + '.desktop'
DESKTOP_FILE_TEMPLATE = DESKTOP_FILE + '.in'

ext_modules = [
    Extension('picard.util._astrcmp', sources=['picard/util/_astrcmp.c']),
]


def newer(source, target):
    """Return true if 'source' exists and is more recently modified than
    'target', or if 'source' exists and 'target' doesn't.  Return false if
    both exist and 'target' is the same age or younger than 'source'.
    Raise FileNotFoundError if 'source' does not exist.
    """
    if not os.path.exists(source):
        raise FileNotFoundError('file "%s" does not exist' % os.path.abspath(source))
    if not os.path.exists(target):
        return True
    return os.path.getmtime(source) > os.path.getmtime(target)


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
        for filename in glob.glob("test/**/test_*.py", recursive=True):
            modules = os.path.splitext(filename)[0].split(os.sep)
            name = '.'.join(modules[1:])
            if not self.tests or name in self.tests:
                names.append('test.' + name)

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
        ('build-number=', None, 'build number (integer)'),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.build_number = 0
        self.build_locales = None
        self.localedir = None
        self.disable_autoupdate = None
        self.disable_locales = None

    def finalize_options(self):
        super().finalize_options()
        try:
            self.build_number = int(self.build_number)
        except ValueError:
            self.build_number = 0
        if self.build_locales is None:
            self.build_locales = os.path.join(self.build_base, 'locale')
        if self.localedir is None:
            self.localedir = '/usr/share/locale'
        if self.disable_autoupdate is None:
            self.disable_autoupdate = False
        if self.disable_locales is None:
            self.sub_commands.append(('build_locales', None))

    def run(self):
        params = {'localedir': self.localedir, 'autoupdate': not self.disable_autoupdate}
        generate_file('tagger.py.in', 'tagger.py', params)
        make_executable('tagger.py')
        generate_file('scripts/picard.in', 'scripts/' + PACKAGE_NAME, params)
        if sys.platform == 'win32':
            file_version = PICARD_VERSION[0:3] + (self.build_number,)
            file_version_str = '.'.join(str(v) for v in file_version)

            installer_args = {
                'display-name': PICARD_DISPLAY_NAME,
                'file-version': file_version_str,
            }
            if os.path.isfile('installer/picard-setup.nsi.in'):
                generate_file('installer/picard-setup.nsi.in', 'installer/picard-setup.nsi', {**args, **installer_args})
                log.info('generating NSIS translation files')
                self.spawn(['python', 'installer/i18n/json2nsh.py'])

            version_args = {
                'filevers': str(file_version),
                'prodvers': str(file_version),
            }
            generate_file('win-version-info.txt.in', 'win-version-info.txt', {**args, **version_args})

            default_publisher = 'CN=Metabrainz Foundation Inc., O=Metabrainz Foundation Inc., L=San Luis Obispo, S=California, C=US'
            # Combine patch version with build number. As Windows store apps require continuously
            # growing version numbers we combine the patch version with a build number set by the
            # build script.
            store_version = (PICARD_VERSION.major, PICARD_VERSION.minor, PICARD_VERSION.patch * 1000 + min(self.build_number, 999), 0)
            generate_file('appxmanifest.xml.in', 'appxmanifest.xml', {
                'app-id': "MetaBrainzFoundationInc." + PICARD_APP_ID,
                'display-name': PICARD_DISPLAY_NAME,
                'short-name': PICARD_APP_NAME,
                'publisher': os.environ.get('PICARD_APPX_PUBLISHER', default_publisher),
                'version': '.'.join(str(v) for v in store_version),
            })
        elif sys.platform not in {'darwin', 'haiku1', 'win32'}:
            self.run_command('build_appdata')
            self.run_command('build_desktop_file')
        super().run()


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
                    log.warn('ignoring %r (cannot extract base name)', f)
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
                        log.warn('ignoring %r', f)
            self.files = files

    def run(self):
        from PyQt6 import uic

        _translate_re = (
            (re.compile(r'(\s+_translate = QtCore\.QCoreApplication\.translate)'), r''),
            (re.compile(
                r'QtGui\.QApplication.translate\(.*?, (.*?), None, '
                r'QtGui\.QApplication\.UnicodeUTF8\)'), r'_(\1)'),
            (re.compile(r'\b_translate\(.*?, (.*?)(?:, None)?\)'), r'_(\1)'),
        )

        def compile_ui(uifile, pyfile):
            tmp = StringIO()
            log.info("compiling %s -> %s", uifile, pyfile)
            uic.compileUi(uifile, tmp)
            source = tmp.getvalue()

            # replace QT translations stuff by ours
            for matcher, replacement in _translate_re:
                source = matcher.sub(replacement, source)

            # replace headers
            rc = re.compile(r'\n# WARNING.*?(?=\nclass )', re.MULTILINE | re.DOTALL)

            command = _get_option_name(self)
            new_header = f"""
# Automatically generated - do not edit.
# Use `python setup.py {command}` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _

"""
            source = rc.sub(new_header, source)

            # save to final file
            with open(pyfile, "w") as f:
                f.write(source)

        if self.files:
            for uifile, pyfile in self.files:
                compile_ui(uifile, pyfile)
        else:
            for uifile, pyfile in ui_files():
                if newer(uifile, pyfile):
                    compile_ui(uifile, pyfile)

        from resources import (
            compile,
            makeqrc,
        )
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

    re_release = re.compile(r'^# Version (?P<version>\d+(?:\.\d+){1,2}) - (?P<date>\d{4}-\d{2}-\d{2})', re.MULTILINE)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with tempfile.NamedTemporaryFile(suffix=APPDATA_FILE) as tmp_file:
            self.spawn([
                'msgfmt', '--xml',
                '--template=%s' % APPDATA_FILE_TEMPLATE,
                '-d', 'po/appstream',
                '-o', tmp_file.name,
            ])
            self.add_release_list(tmp_file.name)

    def add_release_list(self, source_file):
        template = '<release date="{date}" version="{version}"/>'
        with open('NEWS.md', 'r') as newsfile:
            news = newsfile.read()
            releases = [template.format(**m.groupdict()) for m in self.re_release.finditer(news)]
            args = {
                'app-id': PICARD_APP_ID,
                'desktop-id': PICARD_DESKTOP_NAME,
                'releases': '\n    '.join(releases)
            }
            generate_file(source_file, APPDATA_FILE, args)


class picard_build_desktop_file(Command):
    description = 'Build XDG desktop file'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.spawn([
            'msgfmt', '--desktop',
            '--template=%s' % DESKTOP_FILE_TEMPLATE,
            '-d', 'po/appstream',
            '-o', DESKTOP_FILE,
        ])


class picard_regen_appdata_pot_file(Command):
    description = 'Regenerate translations from appdata metadata and XDG desktop file templates'
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
            APPDATA_FILE_TEMPLATE,
        ])
        self.spawn([
            'xgettext',
            '--output', pot_file,
            '--language=desktop',
            '--join-existing',
            DESKTOP_FILE_TEMPLATE,
        ])
        for filepath in glob.glob(os.path.join(output_dir, '*.po')):
            self.spawn([
                'msgmerge',
                '--update',
                filepath,
                pot_file
            ])


_regen_pot_description = "Regenerate po/picard.pot, parsing source tree for new or updated strings"
_regen_constants_pot_description = "Regenerate po/constants/constants.pot, parsing source tree for new or updated strings"
try:
    from babel.messages import frontend as babel

    class picard_regen_pot_file(babel.extract_messages):
        description = _regen_pot_description

        def initialize_options(self):
            super().initialize_options()
            self.output_file = 'po/picard.pot'
            self.input_dirs = 'picard'
            self.ignore_dirs = ('const',)

    class picard_regen_constants_pot_file(babel.extract_messages):
        description = _regen_constants_pot_description

        def initialize_options(self):
            super().initialize_options()
            self.output_file = 'po/constants/constants.pot'
            self.input_dirs = 'picard/const'

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

    class picard_regen_constants_pot_file(picard_regen_pot_file):
        description = _regen_constants_pot_description


def _get_option_name(obj):
    """Returns the name of the option for specified Command object"""
    for name, klass in obj.distribution.cmdclass.items():
        if obj.__class__ == klass:
            return name
    raise Exception("No such command class")


class picard_update_constants(Command):
    description = "Regenerate attributes.py and countries.py"
    user_options = [
        ('skip-pull', None, "skip the translation pull step"),
        ('weblate-key=', None, "Weblate API key"),
    ]
    boolean_options = ['skip-pull']

    def initialize_options(self):
        self.skip_pull = None
        self.weblate_key = None

    def finalize_options(self):
        self.locales = self.distribution.locales

    def run(self):
        from babel.messages import pofile

        if not self.skip_pull:
            cmd = [
                os.path.join(os.path.dirname(__file__), 'scripts', 'tools', 'pull-shared-translations.py'),
            ]
            if self.weblate_key:
                cmd.append('--key')
                cmd.append(self.weblate_key)
            self.spawn(cmd)

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
            'DB:release_status/name',
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
        line = "    '{code}': '{name}',\n"
        footer = "}}\n"
        filename = os.path.join('picard', 'const', 'countries.py')
        with open(filename, 'w', encoding='utf-8') as countries_py:
            def write(s, **kwargs):
                countries_py.write(s.format(**kwargs))

            write(header, option=_get_option_name(self))
            for code, name in sorted(countries.items(), key=lambda t: t[0]):
                write(line, code=code, name=name.replace("'", "\\'"))
            write(footer)
            log.info("%s was rewritten (%d countries)", filename, len(countries))

    def attributes_py_file(self, attributes):
        header = ("# -*- coding: utf-8 -*-\n"
                  "# Automatically generated - don't edit.\n"
                  "# Use `python setup.py {option}` to update it.\n"
                  "\n"
                  "MB_ATTRIBUTES = {{\n")
        line = "    '{key}': '{value}',\n"
        footer = "}}\n"
        filename = os.path.join('picard', 'const', 'attributes.py')
        with open(filename, 'w', encoding='utf-8') as attributes_py:
            def write(s, **kwargs):
                attributes_py.write(s.format(**kwargs))

            write(header, option=_get_option_name(self))
            for key, value in sorted(attributes.items(), key=lambda i: i[0]):
                write(line, key=key, value=value.replace("'", "\\'"))
            write(footer)
            log.info("%s was rewritten (%d attributes)", filename, len(attributes))


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
            build = self.platform + '.' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
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
    domain_path = {
        'picard': 'po',
        'picard-attributes': os.path.join('po', 'attributes'),
        'picard-constants': os.path.join('po', 'constants'),
        'picard-countries': os.path.join('po', 'countries'),
    }
    for domain, path in domain_path.items():
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


this_directory = os.path.abspath(os.path.dirname(__file__))


def _get_description():
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        return f.read()


def _get_requirements():
    with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
        return f.readlines()


args = {
    'name': PACKAGE_NAME,
    'version': PICARD_VERSION_STR_SHORT,
    'description': 'The next generation MusicBrainz tagger',
    'keywords': 'MusicBrainz metadata tagger picard',
    'long_description': _get_description(),
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
        'build_desktop_file': picard_build_desktop_file,
        'install': picard_install,
        'install_locales': picard_install_locales,
        'update_constants': picard_update_constants,
        'regen_pot_file': picard_regen_pot_file,
        'regen_constants_pot_file': picard_regen_constants_pot_file,
        'patch_version': picard_patch_version,
    },
    'scripts': ['scripts/' + PACKAGE_NAME],
    'install_requires': _get_requirements(),
    'python_requires': '~=3.9',
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Development Status :: 5 - Production/Stable',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
        'Intended Audience :: End Users/Desktop',
    ]
}


def generate_file(infilename, outfilename, variables):
    log.info('generating %s from %s', outfilename, infilename)
    with open(infilename, "rt") as f_in:
        with open(outfilename, "wt") as f_out:
            f_out.write(f_in.read() % variables)


def make_executable(filename):
    os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)


def find_file_in_path(filename):
    for include_path in sys.path:
        file_path = os.path.join(include_path, filename)
        if os.path.exists(file_path):
            return file_path


if sys.platform not in {'darwin', 'haiku1', 'win32'}:
    args['data_files'].append(('share/applications', [PICARD_DESKTOP_NAME]))
    args['data_files'].append(('share/icons/hicolor/scalable/apps', ['resources/%s.svg' % PICARD_APP_ID]))
    for size in (16, 24, 32, 48, 128, 256):
        args['data_files'].append((
            'share/icons/hicolor/{size}x{size}/apps'.format(size=size),
            ['resources/images/{size}x{size}/{app_id}.png'.format(size=size, app_id=PICARD_APP_ID)]
        ))
    args['data_files'].append(('share/metainfo', [APPDATA_FILE]))

if sys.platform == 'win32':
    args['entry_points'] = {
        'gui_scripts': [
            'picard = picard.tagger:main'
        ]
    }

setup(**args)
