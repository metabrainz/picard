# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014, 2017 Lukáš Lalinský
# Copyright (C) 2008, 2014, 2019-2020 Philipp Wolfer
# Copyright (C) 2012, 2017 Wieland Hoffmann
# Copyright (C) 2012-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2019 Laurent Monin
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
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
import os
import shutil
import threading

from PyQt5 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION,
    log,
)
from picard.util import LockableObject
from picard.version import Version


class ConfigUpgradeError(Exception):
    pass


class ConfigSection(LockableObject):

    """Configuration section."""

    def __init__(self, config, name):
        super().__init__()
        self.__qt_config = config
        self.__name = name
        self.__prefix = self.__name + '/'
        self.__prefix_len = len(self.__prefix)

    def key(self, name):
        return self.__prefix + name

    def _subkeys(self):
        for key in self.__qt_config.allKeys():
            if key[:self.__prefix_len] == self.__prefix:
                yield key[self.__prefix_len:]

    def __getitem__(self, name):
        opt = Option.get(self.__name, name)
        if opt is None:
            return None
        return self.value(name, opt, opt.default)

    def __setitem__(self, name, value):
        self.lock_for_write()
        try:
            key = self.key(name)
            self.__qt_config.setValue(key, value)
        finally:
            self.unlock()

    def __contains__(self, name):
        return self.__qt_config.contains(self.key(name))

    def remove(self, name):
        self.lock_for_write()
        try:
            if name in self:
                key = self.key(name)
                self.__qt_config.remove(key)
        finally:
            self.unlock()

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
            self.lock_for_read()
            try:
                value = self.raw_value(name, qtype=option_type.qtype)
                value = option_type.convert(value)
            except Exception as why:
                log.error('Cannot read %s value: %s', self.key(name), why, exc_info=True)
                value = default
            finally:
                self.unlock()
            return value
        return default


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

        self.application = ConfigSection(self, "application")
        self.setting = ConfigSection(self, "setting")
        self.persist = ConfigSection(self, "persist")
        self.profile = ConfigSection(self, "profile/default")
        self.current_preset = "default"

        TextOption("application", "version", '0.0.0dev0')
        self._version = Version.from_string(self.application["version"])
        self._upgrade_hooks = dict()

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

    def switchProfile(self, profilename):
        """Sets the current profile."""
        key = "profile/%s" % (profilename,)
        if self.contains(key):
            self.profile.name = key
        else:
            raise KeyError("Unknown profile '%s'" % (profilename,))

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

_thread_configs = {}
_thread_config_lock = threading.RLock()


def setup_config(app, filename=None):
    global config, setting, persist
    if filename is None:
        config = Config.from_app(app)
    else:
        config = Config.from_file(app, filename)
    _thread_configs[threading.get_ident()] = config
    setting = config.setting
    persist = config.persist
    _init_purge_config_timer()


def get_config():
    """Returns a config object for the current thread.

    Config objects for threads are created on demand and cached for later use.
    """
    thread_id = threading.get_ident()
    thread_config = _thread_configs.get(thread_id)
    if not thread_config:
        _thread_config_lock.acquire()
        try:
            config_file = config.fileName()
            log.debug('Instantiating Config for thread %s using %s.', thread_id, config_file)
            thread_config = Config.from_file(None, config_file)
            _thread_configs[thread_id] = thread_config
        finally:
            _thread_config_lock.release()
    return thread_config


def _init_purge_config_timer(purge_interval_milliseconds=60000):
    def run_purge_config_timer():
        purge_config_instances()
        start_purge_config_timer()

    def start_purge_config_timer():
        QtCore.QTimer.singleShot(purge_interval_milliseconds, run_purge_config_timer)

    start_purge_config_timer()


def purge_config_instances():
    """Removes cached config instances for no longer active threads."""
    _thread_config_lock.acquire()
    try:
        all_threads = set([thread.ident for thread in threading.enumerate()])
        threads_config = set(_thread_configs)
        for thread_id in threads_config.difference(all_threads):
            log.debug('Purging config instance for thread %s.', thread_id)
            del _thread_configs[thread_id]
    finally:
        _thread_config_lock.release()
