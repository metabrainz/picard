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

from operator import itemgetter
from PyQt5 import QtCore
from picard import (PICARD_APP_NAME, PICARD_ORG_NAME, PICARD_VERSION,
                    version_to_string, version_from_string)
from picard.util import LockableObject


class ConfigUpgradeError(Exception):
    pass


class ConfigSection(LockableObject):

    """Configuration section."""

    def __init__(self, config, name):
        super().__init__()
        self.__config = config
        self.__name = name

    def __getitem__(self, name):
        opt = Option.get(self.__name, name)
        if opt is None:
            return None
        return self.value(name, opt, opt.default)

    def __setitem__(self, name, value):
        self.lock_for_write()
        try:
            self.__config.setValue("%s/%s" % (self.__name, name), value)
        finally:
            self.unlock()

    def __contains__(self, key):
        key = "%s/%s" % (self.__name, key)
        return self.__config.contains(key)

    def remove(self, key):
        key = "%s/%s" % (self.__name, key)
        if self.__config.contains(key):
            self.__config.remove(key)

    def raw_value(self, key):
        """Return an option value without any type conversion."""
        value = self.__config.value("%s/%s" % (self.__name, key))
        return value

    def value(self, name, option_type, default=None):
        """Return an option value converted to the given Option type."""
        key = "%s/%s" % (self.__name, name)
        self.lock_for_read()
        try:
            if self.__config.contains(key):
                return option_type.convert(self.raw_value(name))
            return default
        except:
            return default
        finally:
            self.unlock()


class Config(QtCore.QSettings):

    """Configuration."""

    def __init__(self):
        pass

    def __initialize(self):
        """Common initializer method for :meth:`from_app` and
        :meth:`from_file`."""

        # If there are no settings, copy existing settings from old format
        # (registry on windows systems)
        if not self.allKeys():
            oldFormat = QtCore.QSettings(PICARD_ORG_NAME, PICARD_APP_NAME)
            for k in oldFormat.allKeys():
                self.setValue(k, oldFormat.value(k))
            self.sync()

        self.application = ConfigSection(self, "application")
        self.setting = ConfigSection(self, "setting")
        self.persist = ConfigSection(self, "persist")
        self.profile = ConfigSection(self, "profile/default")
        self.current_preset = "default"

        TextOption("application", "version", '0.0.0dev0')
        self._version = version_from_string(self.application["version"])
        self._upgrade_hooks = dict()

    @classmethod
    def from_app(cls, parent):
        """Build a Config object using the default configuration file
        location."""
        this = cls()
        QtCore.QSettings.__init__(this, QtCore.QSettings.IniFormat,
                                  QtCore.QSettings.UserScope, PICARD_ORG_NAME,
                                  PICARD_APP_NAME, parent)
        this.__initialize()
        return this

    @classmethod
    def from_file(cls, parent, filename):
        """Build a Config object using a user-provided configuration file
        path."""
        this = cls()
        QtCore.QSettings.__init__(this, filename, QtCore.QSettings.IniFormat,
                                  parent)
        this.__initialize()
        return this

    def switchProfile(self, profilename):
        """Sets the current profile."""
        key = "profile/%s" % (profilename,)
        if self.contains(key):
            self.profile.name = key
        else:
            raise KeyError("Unknown profile '%s'" % (profilename,))

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
        super().__init__()
        self.section = section
        self.name = name
        self.default = default
        if not hasattr(self, "convert"):
            self.convert = type(default)
        self.registry[(self.section, self.name)] = self

    @classmethod
    def get(cls, section, name):
        return cls.registry.get((section, name))


class TextOption(Option):

    convert = str


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
    def convert(values):
        return list(map(int, values))


config = None
setting = None
persist = None


def _setup(app, filename=None):
    global config, setting, persist
    if filename is None:
        config = Config.from_app(app)
    else:
        config = Config.from_file(app, filename)
    setting = config.setting
    persist = config.persist
