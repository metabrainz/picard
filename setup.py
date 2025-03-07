#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2014, 2017 Lukáš Lalinský
# Copyright (C) 2007 Santiago M. Mola
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008-2009, 2018-2025 Philipp Wolfer
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
    setup,
)
from setuptools.command.build import build
from setuptools.command.install import install


# required for PEP 517
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))


from picard import (  # noqa: E402
    PICARD_APP_ID,
    PICARD_APP_NAME,
    PICARD_DESKTOP_NAME,
    PICARD_DISPLAY_NAME,
    PICARD_VERSION,
)


if sys.version_info < (3, 9):
    sys.exit("ERROR: You need Python 3.9 or higher to use Picard.")

PACKAGE_NAME = "picard"
APPDATA_FILE = PICARD_APP_ID + '.appdata.xml'
APPDATA_FILE_TEMPLATE = APPDATA_FILE + '.in'
DESKTOP_FILE = PICARD_APP_ID + '.desktop'
DESKTOP_FILE_TEMPLATE = DESKTOP_FILE + '.in'


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


class picard_build_locales(Command):
    description = 'build locale files'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # build_lib is only set when run as part of the "build" command.
        # When "build_locales" is run standalone this will not be set and
        # locales will be compiled in the local directory.
        build_lib = self.distribution.get_command_obj('build').build_lib

        for domain, locale, po in _picard_get_locale_files():
            path = os.path.join('picard', 'locale', locale, 'LC_MESSAGES')
            if build_lib:
                path = os.path.join(build_lib, path)
            mo = os.path.join(path, f'{domain}.mo')
            self.mkpath(path)
            self.spawn(['msgfmt', '-o', mo, po])


class picard_install(install):

    user_options = install.user_options + [
        ('disable-autoupdate', None, 'disable update checking and hide settings for it'),
    ]

    sub_commands = install.sub_commands

    def initialize_options(self):
        install.initialize_options(self)
        self.disable_autoupdate = None

    def finalize_options(self):
        install.finalize_options(self)
        self.distribution.get_command_obj('build').disable_autoupdate = self.disable_autoupdate

    def run(self):
        install.run(self)


class picard_build(build):

    user_options = build.user_options + [
        ('disable-autoupdate', None, 'disable update checking and hide settings for it'),
        ('build-number=', None, 'build number (integer)'),
        ('disable-locales', None, ''),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.build_number = 0
        self.disable_autoupdate = None
        self.disable_locales = None

    def finalize_options(self):
        super().finalize_options()
        try:
            self.build_number = int(self.build_number)
        except ValueError:
            self.build_number = 0
        if self.disable_autoupdate is None:
            # Support setting this option with an environment variable as
            # a workaround for https://tickets.metabrainz.org/browse/PICARD-3003
            env_autoupdate = os.environ.get('PICARD_DISABLE_AUTOUPDATE')
            self.disable_autoupdate = bool(env_autoupdate and env_autoupdate != '0')
        if not self.disable_locales:
            self.sub_commands.append(('build_locales', None))

    def run(self):
        params = {'autoupdate': not self.disable_autoupdate}
        generate_file('tagger.py.in', 'tagger.py', params)
        make_executable('tagger.py')
        generate_file('scripts/picard.in', 'scripts/' + PACKAGE_NAME, params)
        if sys.platform == 'win32':
            common_args = self._metadata()
            file_version = PICARD_VERSION[0:3] + (self.build_number,)
            file_version_str = '.'.join(str(v) for v in file_version)

            installer_args = {
                'display-name': PICARD_DISPLAY_NAME,
                'file-version': file_version_str,
            }
            if os.path.isfile('installer/picard-setup.nsi.in'):
                generate_file('installer/picard-setup.nsi.in', 'installer/picard-setup.nsi', {**common_args, **installer_args})
                log.info('generating NSIS translation files')
                self.spawn(['python', 'installer/i18n/json2nsh.py'])

            version_args = {
                'filevers': str(file_version),
                'prodvers': str(file_version),
            }
            generate_file('win-version-info.txt.in', 'win-version-info.txt', {**common_args, **version_args})

            default_publisher = 'CN=MetaBrainz Foundation Inc., O=MetaBrainz Foundation Inc., L=Covina, S=California, C=US'
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

    def _metadata(self):
        metadata = self.distribution.metadata
        return {
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'url': metadata.url,
        }


def py_from_ui(uifile):
    return "ui_%s.py" % os.path.splitext(os.path.basename(uifile))[0]


def py_from_ui_with_defaultdir(uifile):
    return os.path.join('picard', 'ui', 'forms', py_from_ui(uifile))


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
                    log.warning('ignoring %r (cannot extract base name)', f)
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
                        log.warning('ignoring %r', f)
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
        for _uifile, pyfile in ui_files():
            try:
                os.unlink(pyfile)
                log.info("removing %s", pyfile)
            except OSError:
                log.warning("'%s' does not exist -- can't clean it", pyfile)
        pyfile = os.path.join("picard", "resources.py")
        try:
            os.unlink(pyfile)
            log.info("removing %s", pyfile)
        except OSError:
            log.warning("'%s' does not exist -- can't clean it", pyfile)


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
    from babel.messages import (
        frontend as babel,
        pofile,
    )

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

    def _parse_pot_file(pot_file):
        with open(pot_file, 'rb') as f:
            log.info('Parsing %s' % pot_file)
            po = pofile.read_po(f)
            for message in po:
                if not message.id or not isinstance(message.id, str):
                    continue
                yield message

except ImportError:
    def _exit_babel_required():
        sys.exit("Babel is required to use this command (see po/README.md)")

    class picard_regen_pot_file(Command):
        description = _regen_pot_description
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            _exit_babel_required()

    class picard_regen_constants_pot_file(picard_regen_pot_file):
        description = _regen_constants_pot_description

    def _parse_pot_file(pot_file):
        _exit_babel_required()


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
        for message in _parse_pot_file(countries_potfile):
            for comment in message.auto_comments:
                if comment.startswith(isocode_comment):
                    code = comment.replace(isocode_comment, '')
                    countries[code] = message.id

        if countries:
            self._generate_constants_file('countries.py', 'RELEASE_COUNTRIES', countries)
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
        for message in _parse_pot_file(attributes_potfile):
            for loc, pos in message.locations:
                if loc in extract_attributes:
                    attributes["%s:%03d" % (loc, pos)] = message.id

        if attributes:
            self._generate_constants_file('attributes.py', 'MB_ATTRIBUTES', attributes)
        else:
            sys.exit('Failed to extract any attribute !')

    def _generate_constants_file(self, filename, varname, constants):
        infilename = os.path.join('scripts', 'package', 'constants.py.in')
        outfilename = os.path.join('picard', 'const', filename)

        def escape_str(s):
            return s.replace("'", "\\'")

        lines = [
            "    '%s': '%s'," % (escape_str(key), escape_str(value))
            for key, value
            in sorted(constants.items(), key=lambda i: i[0])
        ]
        generate_file(infilename, outfilename, {"varname": varname, "lines": "\n".join(lines)})
        log.info("%s was rewritten (%d constants)", filename, len(constants))


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


args = {
    'data_files': [],
    'cmdclass': {
        'build': picard_build,
        'build_locales': picard_build_locales,
        'build_ui': picard_build_ui,
        'clean_ui': picard_clean_ui,
        'build_appdata': picard_build_appdata,
        'regen_appdata_pot_file': picard_regen_appdata_pot_file,
        'build_desktop_file': picard_build_desktop_file,
        'install': picard_install,
        'update_constants': picard_update_constants,
        'regen_pot_file': picard_regen_pot_file,
        'regen_constants_pot_file': picard_regen_constants_pot_file,
        'patch_version': picard_patch_version,
    },
    'scripts': ['scripts/' + PACKAGE_NAME],
}


def generate_file(infilename, outfilename, variables):
    log.info('generating %s from %s', outfilename, infilename)
    with open(infilename, "rt") as f_in:
        with open(outfilename, "wt") as f_out:
            f_out.write(f_in.read() % variables)


def make_executable(filename):
    os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)


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
