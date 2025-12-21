# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014, 2017 Lukáš Lalinský
# Copyright (C) 2008, 2014, 2019-2024 Philipp Wolfer
# Copyright (C) 2012, 2017 Wieland Hoffmann
# Copyright (C) 2012-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2024 Laurent Monin
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021-2025 Bob Swift
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


from collections import (
    defaultdict,
    namedtuple,
)
from enum import Enum
import os
import shutil
from typing import Any

from PyQt6 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION,
    log,
)
from picard.profile import profile_groups_all_settings
from picard.version import Version


class Option(QtCore.QObject):
    """Generic option."""

    registry = {}
    qtype = None

    def __init__(self, section, name, default, title=None):
        super().__init__()
        self.section = section
        self.name = name
        self.default = default
        self.title = title
        self.registry[(section, name)] = self

    @classmethod
    def get(cls, section, name):
        return cls.registry.get((section, name))

    @classmethod
    def get_default(cls, section, name):
        opt = cls.get(section, name)
        if opt is None:
            raise OptionError("No such option", section, name)
        return opt.default

    @classmethod
    def get_title(cls, section, name):
        opt = cls.get(section, name)
        if opt is None:
            raise OptionError("No such option", section, name)
        return opt.title

    @classmethod
    def add_if_missing(cls, section, name, default, *args, **kwargs):
        if not cls.exists(section, name):
            cls(section, name, default, *args, **kwargs)

    @classmethod
    def exists(cls, section, name):
        return (section, name) in cls.registry

    def convert(self, value):
        if isinstance(self.default, Enum):
            # Convert underlying value type first
            value = type(self.default.value)(value)
        return type(self.default)(value)


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
    def convert(self, value):
        if value is None:
            return []
        elif isinstance(value, str):
            raise ValueError('Expected list or list like object, got "%r"' % value)
        return list(value)


class Memovar:
    def __init__(self):
        self.dirty = True
        self.value = None


class ConfigUpgradeError(Exception):
    pass


class ConfigSection(QtCore.QObject):
    """Configuration section."""

    # Signal emitted when the value of a setting has changed.
    setting_changed = QtCore.pyqtSignal(str, object, object)

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
        old_value = self.__getitem__(name)
        key = self.key(name)
        if isinstance(value, Enum):
            value = value.value
        self.__qt_config.setValue(key, value)
        self._memoization[key].dirty = True
        if value != old_value:
            self.setting_changed.emit(name, old_value, value)

    def __contains__(self, name):
        return self.__qt_config.contains(self.key(name))

    def as_dict(self):
        return {key: self[key] for section, key in list(Option.registry) if section == self.__name}

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

    def register_option(self, name: str, default: Any) -> Option:
        """Register an option.

        The option type is determined by the type of the default value.
        The default must not be None.

        Raises:
            TypeError: If default is None.
        """
        if default is None:
            raise TypeError('Option default value must not be None')

        if isinstance(default, Enum):
            option_type = Option
        elif isinstance(default, str):
            option_type = TextOption
        elif isinstance(default, bool):
            option_type = BoolOption
        elif isinstance(default, int):
            option_type = IntOption
        elif isinstance(default, float):
            option_type = FloatOption
        elif isinstance(default, list) or isinstance(default, tuple):
            option_type = ListOption
        else:
            option_type = Option

        return option_type(self.__name, name, default)


class SettingConfigSection(ConfigSection):
    """Custom subclass to automatically accommodate saving and retrieving values based on user profile settings."""

    PROFILES_KEY = 'user_profiles'
    SETTINGS_KEY = 'user_profile_settings'

    @classmethod
    def init_profile_options(cls):
        ListOption.add_if_missing('profiles', cls.PROFILES_KEY, [])
        Option.add_if_missing('profiles', cls.SETTINGS_KEY, {})

    def __init__(self, config, name):
        super().__init__(config, name)
        self.__qt_config = config
        self.__name = name
        self.__prefix = self.__name + '/'
        self._memoization = defaultdict(Memovar)
        self.init_profile_options()
        self.profiles_override = None
        self.settings_override = None

    def _get_active_profile_ids(self):
        if self.profiles_override is None:
            profiles = self.__qt_config.profiles[self.PROFILES_KEY]
        else:
            profiles = self.profiles_override
        if profiles is None:
            return
        for profile in profiles:
            if profile['enabled']:
                yield profile['id']

    def _get_active_profile_settings(self):
        for profile_id in self._get_active_profile_ids():
            yield profile_id, self._get_profile_settings(profile_id)

    def _get_profile_settings(self, profile_id):
        if self.settings_override is None:
            # Set to None if profile_id not in profile settings
            profile_settings = (
                self.__qt_config.profiles[self.SETTINGS_KEY][profile_id]
                if profile_id in self.__qt_config.profiles[self.SETTINGS_KEY]
                else None
            )
        else:
            # Set to None if profile_id not in settings_override
            profile_settings = self.settings_override[profile_id] if profile_id in self.settings_override else None
        if profile_settings is None:
            log.error("Unable to find settings for user profile '%s'", profile_id)
            return {}
        return profile_settings

    def __getitem__(self, name):
        # Don't process settings that are not profile-specific
        if name in profile_groups_all_settings():
            for _profile_id, settings in self._get_active_profile_settings():
                if name in settings and settings[name] is not None:
                    return settings[name]
        return super().__getitem__(name)

    def __setitem__(self, name, value):
        # Don't process settings that are not profile-specific
        if name in profile_groups_all_settings():
            for profile_id, settings in self._get_active_profile_settings():
                if name in settings:
                    old_value = settings[name]
                    self._save_profile_setting(profile_id, name, value)
                    if value != old_value:
                        self.setting_changed.emit(name, old_value, value)
                    return
        super().__setitem__(name, value)

    def _save_profile_setting(self, profile_id, name, value):
        profile_settings = self.__qt_config.profiles[self.SETTINGS_KEY]
        profile_settings[profile_id][name] = value
        key = self.__qt_config.profiles.key(self.SETTINGS_KEY)
        self.__qt_config.setValue(key, profile_settings)
        self._memoization[key].dirty = True

    def set_profiles_override(self, new_profiles=None):
        self.profiles_override = new_profiles

    def set_settings_override(self, new_settings=None):
        self.settings_override = new_settings


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
        self.application = ConfigSection(self, 'application')
        self.profiles = ConfigSection(self, 'profiles')
        self.setting = SettingConfigSection(self, 'setting')
        self.persist = ConfigSection(self, 'persist')

        if 'version' not in self.application or not self.application['version']:
            TextOption('application', 'version', '0.0.0dev0')
        self._version = Version.from_string(self.application['version'])

    @classmethod
    def from_app(cls, parent):
        """Build a Config object using the default configuration file
        location."""
        this = cls()
        QtCore.QSettings.__init__(
            this,
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.UserScope,
            PICARD_ORG_NAME,
            PICARD_APP_NAME,
            parent,
        )

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
        QtCore.QSettings.__init__(this, filename, QtCore.QSettings.Format.IniFormat, parent)
        this.__initialize()
        return this

    def run_upgrade_hooks(self, hooks):
        """Executes passed hooks to upgrade config version to the latest"""
        if self._version == Version(0, 0, 0, 'dev', 0):
            # This is a freshly created config
            self._write_version(PICARD_VERSION)
            return
        if not hooks:
            return
        if self._version >= PICARD_VERSION:
            if self._version > PICARD_VERSION:
                print(
                    "Warning: config file %s was created by a more recent "
                    "version of Picard (current is %s)" % (self._version, PICARD_VERSION)
                )
            return
        for version in list(hooks):
            hook = hooks[version]
            if self._version < version:
                try:
                    if hook.__doc__:
                        log.debug(
                            "Config upgrade %s -> %s: %s"
                            % (
                                self._version,
                                version,
                                hook.__doc__.strip(),
                            )
                        )
                    hook(self)
                except BaseException as e:
                    raise ConfigUpgradeError(
                        "Error during config upgrade from version %s to %s "
                        "using %s()"
                        % (
                            self._version,
                            version,
                            hook.__name__,
                        )
                    ) from e
                else:
                    del hooks[version]
                    self._write_version(version)
            else:
                # hook is not applicable, mark as done
                del hooks[version]

        if not hooks:
            # all hooks were executed, ensure config is marked with latest version
            self._write_version(PICARD_VERSION)

    def _backup_settings(self):
        if Version(0, 0, 0) < self._version < PICARD_VERSION:
            backup_path = self._versioned_config_filename()
            self._save_backup(backup_path)

    def _save_backup(self, backup_path):
        log.info("Backing up config file to %s", backup_path)
        try:
            shutil.copyfile(self.fileName(), backup_path)
        except OSError:
            log.error("Failed backing up config file to %s", backup_path)
            return False
        return True

    def _write_version(self, new_version):
        self._version = new_version
        self.application['version'] = str(self._version)
        self.sync()

    def _versioned_config_filename(self, version=None):
        if not version:
            version = self._version
        return os.path.join(
            os.path.dirname(self.fileName()), '%s-%s.ini' % (self.applicationName(), version.short_str())
        )

    def save_user_backup(self, backup_path):
        if backup_path == self.fileName():
            log.warning("Attempt to backup configuration file to the same path.")
            return False
        return self._save_backup(backup_path)


class OptionError(Exception):
    def __init__(self, message, section, name):
        super().__init__("Option %s/%s: %s" % (section, name, message))


config = None
setting = None
persist = None
profiles = None


def setup_config(app=None, filename=None):
    if app is None:
        app = QtCore.QCoreApplication.instance()
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


def load_new_config(filename=None):
    config_file = get_config().fileName()
    try:
        shutil.copy(filename, config_file)
    except OSError:
        log.error("Failed restoring config file from %s", filename)
        return False
    setup_config(filename=config_file)
    return True


QuickMenuItem = namedtuple('QuickMenuItem', ['name', 'title'])
_quick_menu_items = {}


def register_quick_menu_item(group_order: int, group_name: str, option: Option):
    if option.qtype is not bool or not option.title:
        return
    if group_name not in _quick_menu_items:
        _quick_menu_items[group_name] = {'order': group_order, 'options': []}
    _quick_menu_items[group_name]['options'].append(QuickMenuItem(option.name, option.title))


def get_quick_menu_items():
    for group, value in sorted(_quick_menu_items.items(), key=lambda x: (x[1]['order'], x[0])):
        yield {'group_title': group, 'options': value['options']}
