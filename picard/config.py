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
from PyQt4 import QtCore
from picard import (PICARD_APP_NAME, PICARD_ORG_NAME, PICARD_VERSION,
                    version_to_string, version_from_string, log)
from picard.util import LockableObject, rot13


class ConfigUpgradeError(Exception):
    pass


class ConfigSection(LockableObject):

    """Configuration section."""

    def __init__(self, config, name):
        LockableObject.__init__(self)
        self.__config = config
        self.__name = name

    def __getitem__(self, name):
        self.lock_for_read()
        key = "%s/%s" % (self.__name, name)
        try:
            opt = Option.get(self.__name, name)
            if self.__config.contains(key):
                return opt.convert(self.__config.value(key))
            return opt.default
        except KeyError:
            if self.__config.contains(key):
                return self.__config.value(key)
        finally:
            self.unlock()

    def __setitem__(self, name, value):
        self.lock_for_write()
        try:
            self.__config.setValue("%s/%s" % (self.__name, name),
                                   QtCore.QVariant(value))
        finally:
            self.unlock()

    def __contains__(self, key):
        key = "%s/%s" % (self.__name, key)
        return self.__config.contains(key)

    def remove(self, key):
        key = "%s/%s" % (self.__name, key)
        if self.__config.contains(key):
            self.__config.remove(key)


class Config(QtCore.QSettings):

    """Configuration."""

    def __init__(self):
        """Initializes the configuration."""
        QtCore.QSettings.__init__(self, PICARD_ORG_NAME, PICARD_APP_NAME)
        self.application = ConfigSection(self, "application")
        self.setting = ConfigSection(self, "setting")
        self.persist = ConfigSection(self, "persist")
        self.profile = ConfigSection(self, "profile/default")
        self.current_preset = "default"

        TextOption("application", "version", '0.0.0dev0')
        self._version = version_from_string(self.application["version"])
        self._upgrade_hooks = []

    def switchProfile(self, profilename):
        """Sets the current profile."""
        key = u"profile/%s" % (profilename,)
        if self.contains(key):
            self.profile.name = key
        else:
            raise KeyError("Unknown profile '%s'" % (profilename,))

    def register_upgrade_hook(self, to_version_str, func, *args):
        """Register a function to upgrade from one config version to another"""
        to_version = version_from_string(to_version_str)
        assert to_version <= PICARD_VERSION, "%r > %r !!!" % (to_version, PICARD_VERSION)
        hook = {
            'to': to_version,
            'func': func,
            'args': args,
            'done': False
        }
        self._upgrade_hooks.append(hook)

    def run_upgrade_hooks(self):
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
        # sort upgrade hooks by version
        self._upgrade_hooks.sort(key=itemgetter("to"))
        for hook in self._upgrade_hooks:
            if self._version < hook['to']:
                try:
                    hook['func'](*hook['args'])
                except Exception as e:
                    raise ConfigUpgradeError(
                        "Error during config upgrade from version %s to %s "
                        "using %s(): %s" % (
                            version_to_string(self._version),
                            version_to_string(hook['to']),
                            hook['func'].__name__, e
                        ))
                else:
                    hook['done'] = True
                    self._version = hook['to']
                    self._write_version()
            else:
                # hook is not applicable, mark as done
                hook['done'] = True

        if all(map(itemgetter("done"), self._upgrade_hooks)):
            # all hooks were executed, ensure config is marked with latest version
            self._version = PICARD_VERSION
            self._write_version()

    def _write_version(self):
        self.application["version"] = version_to_string(self._version)
        self.sync()


class Option(QtCore.QObject):

    """Generic option."""

    registry = {}

    def __init__(self, section, name, default, convert=None):
        self.section = section
        self.name = name
        self.default = default
        self.convert = convert
        if not self.convert:
            self.convert = type(self.default)
        self.registry[(self.section, self.name)] = self

    @classmethod
    def get(cls, section, name):
        try:
            return cls.registry[(section, name)]
        except KeyError:
            raise KeyError("Option %s.%s not found." % (section, name))


class TextOption(Option):

    """Option with a text value."""

    def __init__(self, section, name, default):
        def convert(value):
            return unicode(value.toString())
        Option.__init__(self, section, name, default, convert)


class BoolOption(Option):

    """Option with a boolean value."""

    def __init__(self, section, name, default):
        Option.__init__(self, section, name, default, QtCore.QVariant.toBool)


class IntOption(Option):

    """Option with an integer value."""

    def __init__(self, section, name, default):
        def convert(value):
            return value.toInt()[0]
        Option.__init__(self, section, name, default, convert)


class FloatOption(Option):

    """Option with a float value."""

    def __init__(self, section, name, default):
        def convert(value):
            return value.toDouble()[0]
        Option.__init__(self, section, name, default, convert)


class PasswordOption(Option):

    """Super l33t h3ckery!"""

    def __init__(self, section, name, default):
        def convert(value):
            return rot13(unicode(value.toString()))
        Option.__init__(self, section, name, default, convert)


_config = Config()

setting = _config.setting
persist = _config.persist
