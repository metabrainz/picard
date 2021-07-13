# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014, 2017 Lukáš Lalinský
# Copyright (C) 2008, 2014, 2019-2021 Philipp Wolfer
# Copyright (C) 2012, 2017 Wieland Hoffmann
# Copyright (C) 2012-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2021 Laurent Monin
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Bob Swift
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


from collections import defaultdict
import inspect
from operator import itemgetter
import os
import shutil
import threading

import fasteners

from PyQt5 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION,
    log,
)
from picard.profile import UserProfileGroups
from picard.version import Version


class Memovar:
    def __init__(self):
        self.dirty = True
        self.value = None


class ConfigUpgradeError(Exception):
    pass


class ConfigSection(QtCore.QObject):

    """Configuration section."""

    def __init__(self, config, name):
        super().__init__()
        self.__qt_config = config
        self.__name = name
        self.__prefix = self.__name + '/'
        self._memoization = defaultdict(Memovar)

    def key(self, name):
        return self.__prefix + name

    def __getitem__(self, name):
        opt = Option.get(self.__name, name)
        if opt is None:
            return None
        return self.value(name, opt, opt.default)

    def __setitem__(self, name, value):
        key = self.key(name)
        self.__qt_config.setValue(key, value)
        self._memoization[key].dirty = True

    def __contains__(self, name):
        return self.__qt_config.contains(self.key(name))

    def as_dict(self):
        return {key: self[key] for section, key in Option.registry if section == self.__name}

    def remove(self, name):
        key = self.key(name)
        config = self.__qt_config
        if config.contains(key):
            config.remove(key)
        try:
            del self._memoization[key]
        except KeyError:
            pass

    def raw_value(self, name, qtype=None):
        """Return an option value without any type conversion."""
        key = self.key(name)
        if qtype is not None:
            value = self.__qt_config.value(key, type=qtype)
        else:
            value = self.__qt_config.value(key)
        return value

    def value(self, name, option_type, default=None):
        """Return an option value converted to the given Option type."""
        if name in self:
            key = self.key(name)
            memovar = self._memoization[key]

            if memovar.dirty:
                try:
                    value = self.raw_value(name, qtype=option_type.qtype)
                    value = option_type.convert(value)
                    memovar.dirty = False
                    memovar.value = value
                except Exception as why:
                    log.error('Cannot read %s value: %s', self.key(name), why, exc_info=True)
                    value = default
                return value
            else:
                return memovar.value
        return default


class SettingConfigSection(ConfigSection):
    """Custom subclass to automatically accommodate saving and retrieving values based on user profile settings.
    """
    PROFILES_KEY = 'user_profiles'
    SETTINGS_KEY = 'user_profile_settings'

    @classmethod
    def init_profile_options(cls):
        ListOption.add_if_missing("profiles", cls.PROFILES_KEY, [])
        Option.add_if_missing("profiles", cls.SETTINGS_KEY, {})

    def __init__(self, config, name):
        super().__init__(config, name)
        self.__qt_config = config
        self.__name = name
        self.__prefix = self.__name + '/'
        self._memoization = defaultdict(Memovar)
        self.init_profile_options()
        self._selected_profile = None

    def _get_active_profile_ids(self):
        if self._selected_profile is not None:
            if self._selected_profile == "user_settings":
                return
            # Act as if the selected profile is the only active profile.
            yield self._selected_profile
        else:
            profiles = self.__qt_config.profiles[self.PROFILES_KEY]
            if profiles is None:
                return
            for profile in profiles:
                if profile['enabled']:
                    yield profile["id"]

    def _get_active_profile_settings(self):
        for id in self._get_active_profile_ids():
            yield id, self._get_profile_settings(id)

    def _get_profile_settings(self, id):
        profile_settings = self.__qt_config.profiles[self.SETTINGS_KEY][id]
        if profile_settings is None:
            log.error("Unable to find settings for user profile '%s'", id)
            return {}
        return profile_settings

    def __getitem__(self, name):
        # Don't process settings that are not profile-specific
        if name in UserProfileGroups.get_all_settings_list():
            for id, settings in self._get_active_profile_settings():
                if name in settings and settings[name] is not None:
                    return settings[name]
        opt = Option.get(self.__name, name)
        if opt is None:
            return None
        return self.value(name, opt, opt.default)

    def __setitem__(self, name, value):
        # Don't process settings that are not profile-specific
        if name in UserProfileGroups.get_all_settings_list():
            for id, settings in self._get_active_profile_settings():
                if name in settings:
                    self._save_profile_setting(id, name, value)
                    return
        if self._selected_profile is None or self._selected_profile == "user_settings":
            key = self.key(name)
            self.__qt_config.setValue(key, value)
            self._memoization[key].dirty = True

    def _save_profile_setting(self, profile_id, name, value):
        profile_settings = self.__qt_config.profiles[self.SETTINGS_KEY]
        profile_settings[profile_id][name] = value
        key = self.__qt_config.profiles.key(self.SETTINGS_KEY)
        self.__qt_config.setValue(key, profile_settings)
        self._memoization[key].dirty = True

    def set_profile(self, profile_id=None):
        self._selected_profile = profile_id


class Config(QtCore.QSettings):

    """Configuration.
    QSettings is not thread safe, each thread must use its own instance of this class.
    Use `get_config()` to obtain a Config instance for the current thread.
    Changes to one Config instances are automatically available to all other instances.

    Use `Config.from_app` or `Config.from_file` to obtain a new `Config` instance.

    See: https://doc.qt.io/qt-5/qsettings.html#accessing-settings-from-multiple-threads-or-processes-simultaneously
    """

    def __init__(self):
        # Do not call `QSettings.__init__` here. The proper overloaded `QSettings.__init__`
        # gets called in `from_app` or `from_config`. Only those class methods must be used
        # to create a new instance of `Config`.
        pass

    def __initialize(self):
        """Common initializer method for :meth:`from_app` and
        :meth:`from_file`."""

        self.setAtomicSyncRequired(False)  # See comment in event()
        self.application = ConfigSection(self, "application")
        self.profiles = ConfigSection(self, "profiles")
        self.setting = SettingConfigSection(self, "setting")
        self.persist = ConfigSection(self, "persist")

        TextOption("application", "version", '0.0.0dev0')
        self._version = Version.from_string(self.application["version"])
        self._upgrade_hooks = dict()

    def event(self, event):
        if event.type() == QtCore.QEvent.UpdateRequest:
            # Syncing the config file can trigger a deadlock between QSettings internal mutex and
            # the Python GIL in PyQt up to 5.15.2. Workaround this by handling this ourselves
            # with custom file locking.
            # See also https: // tickets.metabrainz.org/browse/PICARD-2088
            log.debug('Config file update requested on thread %r', threading.get_ident())
            self.sync()
            return True
        else:
            return super().event(event)

    def sync(self):
        # Custom file locking for save multi process syncing of the config file. This is needed
        # as we have atomicSyncRequired disabled.
        with fasteners.InterProcessLock(self.get_lockfile_name()):
            super().sync()

    def get_lockfile_name(self):
        filename = self.fileName()
        directory = os.path.dirname(filename)
        filename = '.' + os.path.basename(filename) + '.synclock'
        return os.path.join(directory, filename)

    @classmethod
    def from_app(cls, parent):
        """Build a Config object using the default configuration file
        location."""
        this = cls()
        QtCore.QSettings.__init__(this, QtCore.QSettings.IniFormat,
                                  QtCore.QSettings.UserScope, PICARD_ORG_NAME,
                                  PICARD_APP_NAME, parent)

        # Check if there is a config file specifically for this version
        versioned_config_file = this._versioned_config_filename(PICARD_VERSION)
        if os.path.isfile(versioned_config_file):
            return cls.from_file(parent, versioned_config_file)

        # If there are no settings, copy existing settings from old format
        # (registry on windows systems)
        if not this.allKeys():
            oldFormat = QtCore.QSettings(PICARD_ORG_NAME, PICARD_APP_NAME)
            for k in oldFormat.allKeys():
                this.setValue(k, oldFormat.value(k))
            this.sync()

        this.__initialize()
        this._backup_settings()
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

    def register_upgrade_hook(self, func, *args):
        """Register a function to upgrade from one config version to another"""
        to_version = Version.from_string(func.__name__)
        assert to_version <= PICARD_VERSION, "%r > %r !!!" % (to_version, PICARD_VERSION)
        self._upgrade_hooks[to_version] = {
            'func': func,
            'args': args,
            'done': False
        }

    def run_upgrade_hooks(self, outputfunc=None):
        """Executes registered functions to upgrade config version to the latest"""
        if self._version == Version(0, 0, 0, 'dev', 0):
            # This is a freshly created config
            self._version = PICARD_VERSION
            self._write_version()
            return
        if not self._upgrade_hooks:
            return
        if self._version >= PICARD_VERSION:
            if self._version > PICARD_VERSION:
                print("Warning: config file %s was created by a more recent "
                      "version of Picard (current is %s)" % (
                          self._version.to_string(),
                          PICARD_VERSION.to_string()
                      ))
            return
        for version in sorted(self._upgrade_hooks):
            hook = self._upgrade_hooks[version]
            if self._version < version:
                try:
                    if outputfunc and hook['func'].__doc__:
                        outputfunc("Config upgrade %s -> %s: %s" % (
                                   self._version.to_string(),
                                   version.to_string(),
                                   hook['func'].__doc__.strip()))
                    hook['func'](self, *hook['args'])
                except BaseException:
                    import traceback
                    raise ConfigUpgradeError(
                        "Error during config upgrade from version %s to %s "
                        "using %s():\n%s" % (
                            self._version.to_string(),
                            version.to_string(),
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

    def _backup_settings(self):
        if Version(0, 0, 0) < self._version < PICARD_VERSION:
            backup_path = self._versioned_config_filename()
            log.info('Backing up config file to %s', backup_path)
            try:
                shutil.copyfile(self.fileName(), backup_path)
            except OSError:
                log.error('Failed backing up config file to %s', backup_path)

    def _write_version(self):
        self.application["version"] = self._version.to_string()
        self.sync()

    def _versioned_config_filename(self, version=None):
        if not version:
            version = self._version
        return os.path.join(os.path.dirname(self.fileName()), '%s-%s.ini' % (
            self.applicationName(), version.to_string(short=True)))


class Option(QtCore.QObject):

    """Generic option."""

    registry = {}
    qtype = None

    def __init__(self, section, name, default):
        key = (section, name)
        if key in self.registry:
            stack = inspect.stack()
            fmt = "Option %s/%s already declared"
            args = [section, name]
            if len(stack) > 1:
                f = stack[1]
                fmt += "\nat %s:%d: in %s"
                args.extend((f.filename, f.lineno, f.function))
                if f.code_context:
                    fmt += "\n%s"
                    args.append("\n".join(f.code_context).rstrip())
            log.error(fmt, *args)
        super().__init__()
        self.section = section
        self.name = name
        self.default = default
        if not hasattr(self, "convert"):
            self.convert = type(default)
        self.registry[key] = self

    @classmethod
    def get(cls, section, name):
        return cls.registry.get((section, name))

    @classmethod
    def add_if_missing(cls, section, name, default):
        if not cls.exists(section, name):
            cls(section, name, default)

    @classmethod
    def exists(cls, section, name):
        return (section, name) in cls.registry


class TextOption(Option):

    convert = str
    qtype = 'QString'


class BoolOption(Option):

    convert = bool
    qtype = bool


class IntOption(Option):

    convert = int


class FloatOption(Option):

    convert = float


class ListOption(Option):

    convert = list
    qtype = 'QVariantList'


config = None
setting = None
persist = None
profiles = None


def setup_config(app, filename=None):
    global config, setting, persist, profiles
    if filename is None:
        config = Config.from_app(app)
    else:
        config = Config.from_file(app, filename)
    setting = config.setting
    persist = config.persist
    profiles = config.profiles


def get_config():
    """Returns a config object for the current thread.

    Config objects for threads are created on demand and cached for later use.
    """
    return config
