# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

import re
from operator import itemgetter
from PyQt4 import QtCore
from picard import (PICARD_APP_NAME, PICARD_ORG_NAME, PICARD_VERSION,
                    version_to_string, version_from_string)
from picard.util import LockableObject, rot13


class ConfigUpgradeError(Exception):
    pass


def _safe_section_name(name):
    # https://qt-project.org/doc/qt-4.7/qsettings.html
    # Section and Key Syntax
    #
    # Setting keys can contain any Unicode characters.
    # The Windows registry and INI files use case-insensitive keys,
    # whereas the Carbon Preferences API on Mac OS X uses case-sensitive keys.
    # To avoid portability problems, follow these simple rules:
    #
    # - Always refer to the same key using the same case.
    # - Avoid key names that are identical except for the case.
    # - Do not use slashes ('/' and '\') in section or key names;
    #   the backslash character is used to separate sub keys (see below).
    #   On windows '\' are converted by QSettings to '/', which makes them identical.
    if not isinstance(name, unicode):
        name = unicode(name)
    return name.lower().replace(u'/', u'_').replace(u'\\', u'_')


class ConfigSection(LockableObject):

    """Configuration section."""

    def __init__(self, config, name):
        LockableObject.__init__(self)
        self.__config = config
        self.__name = name

    def __getitem__(self, name):
        opt = Option.get(self.__name, name)
        if opt is None:
            return None
        self.lock_for_read()
        try:
            if self.__config.contains(self._key(name)):
                return opt.convert(self.raw_value(name))
            return opt.default
        except:
            return opt.default
        finally:
            self.unlock()

    def __setitem__(self, name, value):
        self.lock_for_write()
        try:
            self.__config.setValue(self._key(name), value)
        finally:
            self.unlock()

    def __contains__(self, key):
        return self.__config.contains(self._key(key))

    def remove(self, key):
        key = self._key(key)
        if self.__config.contains(key):
            self.__config.remove(key)

    def raw_value(self, key):
        """Return an option value without any type conversion."""
        value = self.__config.value(self._key(key))

        # XXX QPyNullVariant does not exist in all PyQt versions, and was
        # removed entirely in PyQt5. See:
        # http://pyqt.sourceforge.net/Docs/PyQt5/pyqt_qvariant.html
        if str(type(value)) == "<class 'PyQt4.QtCore.QPyNullVariant'>":
            return ""

        return value

    def _key(self, key):
        return "%s/%s" % (self._name(), key)

    def _name(self):
        profile = self.__config.profile()
        if profile is None:
            return self.__name
        else:
            return "%s%s%s" % (profile, self.__config._PROFILE_SEPARATOR, self.__name)


class Config(QtCore.QSettings):

    """Configuration."""

    _PROFILE_SEPARATOR = u'-'

    def __init__(self):
        """Initializes the configuration."""
        QtCore.QSettings.__init__(self, PICARD_ORG_NAME, PICARD_APP_NAME)
        self.application = ConfigSection(self, "application")
        self.setting = ConfigSection(self, "setting")
        self.persist = ConfigSection(self, "persist")
        self._current_profile = None

        TextOption("application", "version", '0.0.0dev0')
        self._version = version_from_string(self.application["version"])
        self._upgrade_hooks = dict()

    def use_profile(self, profile=None):
        if profile:
            self._current_profile = _safe_section_name(profile).replace(self._PROFILE_SEPARATOR, u'_')
        else:
            profile = None

    def profile(self):
        return self._current_profile

    def register_upgrade_hook(self, func, *args):
        """Register a function to upgrade from one config version to another"""
        to_version = version_from_string(func.__name__)
        assert to_version <= PICARD_VERSION, "%r > %r !!!" % (to_version, PICARD_VERSION)
        self._upgrade_hooks[to_version] = {
            'func': func,
            'args': args,
            'done': False
        }

    def run_upgrade_hooks(self, outputfunc=None):
        """Executes registered functions to upgrade config version to the latest"""
        if not self._upgrade_hooks:
            return
        if self._version >= PICARD_VERSION:
            if self._version > PICARD_VERSION:
                print("Warning: config file %s was created by a more recent "
                      "version of Picard (current is %s)" % (
                          version_to_string(self._version),
                          version_to_string(PICARD_VERSION)
                      ))
            return
        for version in sorted(self._upgrade_hooks):
            hook = self._upgrade_hooks[version]
            if self._version < version:
                try:
                    if outputfunc and hook['func'].__doc__:
                        outputfunc("Config upgrade %s -> %s: %s" % (
                                   version_to_string(self._version),
                                   version_to_string(version),
                                   hook['func'].__doc__.strip()))
                    hook['func'](*hook['args'])
                except:
                    import traceback
                    raise ConfigUpgradeError(
                        "Error during config upgrade from version %s to %s "
                        "using %s():\n%s" % (
                            version_to_string(self._version),
                            version_to_string(version),
                            hook['func'].__name__,
                            traceback.format_exc()
                        ))
                else:
                    hook['done'] = True
                    self._version = version
                    self._write_version()
            else:
                # hook is not applicable, mark as done
                hook['done'] = True

        if all(map(itemgetter("done"), self._upgrade_hooks.values())):
            # all hooks were executed, ensure config is marked with latest version
            self._version = PICARD_VERSION
            self._write_version()

    def _write_version(self):
        self.application["version"] = version_to_string(self._version)
        self.sync()


class Option(QtCore.QObject):

    """Generic option."""

    registry = {}

    def __init__(self, section, name, default):
        self.section = section
        self.name = name
        self.default = default
        if not hasattr(self, "convert"):
            self.convert = type(default)
        self.registry[(self.section, self.name)] = self

    @classmethod
    def get(cls, section, name):
        return cls.registry.get((section, name))


class PasswordOption(Option):

    """Super l33t h3ckery!"""

    convert = staticmethod(rot13)


class TextOption(Option):

    convert = unicode


class BoolOption(Option):

    @staticmethod
    def convert(value):
        # The QSettings IniFormat saves boolean values as the strings "true"
        # and "false". Thus, explicit boolean and string comparisons are used
        # to determine the value. NOTE: In PyQt >= 4.8.3, QSettings.value has
        # an optional "type" parameter that avoids this. But we still support
        # PyQt >= 4.5, so that is not used.
        return value is True or value == "true"


class IntOption(Option):

    convert = int


class FloatOption(Option):

    convert = float


class ListOption(Option):

    convert = list


class IntListOption(Option):

    @staticmethod
    def convert(value):
        return map(int, value)


_config = Config()

setting = _config.setting
persist = _config.persist
use_profile = _config.use_profile
profile = _config.profile
