# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014, 2017 Lukáš Lalinský
# Copyright (C) 2008, 2014, 2019-2026 Philipp Wolfer
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
from contextlib import contextmanager
from enum import (
    Enum,
    IntEnum,
)
import os
import shutil
from typing import (
    Any,
    TypeAlias,
)

from PyQt6 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION,
    log,
    tagger_instance,
)
from picard.profile import (
    profile_groups_add_setting,
    setting_profile_key,
)
from picard.version import Version


ConfigValueType: TypeAlias = str | int | float | bool | list | tuple | dict | Enum | QtCore.QByteArray


class Option(QtCore.QObject):
    """Generic option."""

    registry: dict[tuple[str, str], 'Option'] = {}
    qtype: object = None

    def __init__(
        self,
        section: str,
        name: str,
        default: ConfigValueType,
        title: str | None = None,
        in_profile: bool = False,
        shareable: bool = True,
    ):
        super().__init__()
        self.section = section
        self.name = name
        self.default = default
        self.title = title
        self.in_profile = in_profile
        self.shareable = shareable
        if in_profile and not title:
            log.warning("Option '%s/%s' has in_profile=True but no title", section, name)
        self.registry[(section, name)] = self

        self._check_if_valid()

    def _do_logging(self, expected):
        log.warning("Invalid Option definition for %s/%s: should be %s", self.section, self.name, expected.__name__)

    def _check_if_valid(self):
        """Check if the option should be sub-classed, and log a warning."""
        tests: dict[type, type[Option]] = {
            str: TextOption,
            bool: BoolOption,
            int: IntOption,
            float: FloatOption,
            list: ListOption,
            tuple: ListOption,
            dict: Option,
        }

        subclass_tests = {
            IntEnum: IntOption,
            QtCore.QByteArray: Option,
        }

        t = type(self.default)
        if t in tests:
            if self.__class__ != tests[t]:
                self._do_logging(tests[t])
        else:
            for base, expected in subclass_tests.items():
                if issubclass(t, base) and self.__class__ != expected:
                    self._do_logging(expected)
                    break

    @classmethod
    def get(cls, section: str, name: str) -> 'Option | None':
        return cls.registry.get((section, name))

    @classmethod
    def get_default(cls, section: str, name: str) -> ConfigValueType:
        opt = cls.get(section, name)
        if opt is None:
            raise OptionError("No such option", section, name)
        return opt.default

    @classmethod
    def get_title(cls, section: str, name: str) -> str | None:
        opt = cls.get(section, name)
        if opt is None:
            raise OptionError("No such option", section, name)
        return opt.title

    @classmethod
    def add_if_missing(cls, section: str, name: str, default: ConfigValueType, *args, **kwargs):
        if not cls.exists(section, name):
            cls(section, name, default, *args, **kwargs)

    @classmethod
    def exists(cls, section: str, name: str) -> bool:
        return (section, name) in cls.registry

    def convert(self, value: Any):
        if isinstance(self.default, Enum):
            # Convert underlying value type first
            value = type(self.default.value)(value)
        return type(self.default)(value)

    def unregister(self):
        del self.registry[(self.section, self.name)]


class TextOption(Option):
    convert = str  # type: ignore[assignment]
    qtype = 'QString'


class BoolOption(Option):
    convert = bool  # type: ignore[assignment]
    qtype = bool


class IntOption(Option):
    def convert(self, value):
        value = int(value)
        # If the default is an IntEnum, return an IntEnum
        if isinstance(self.default, IntEnum):
            return type(self.default)(value)
        return value


class FloatOption(Option):
    convert = float  # type: ignore[assignment]


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
        self.value: ConfigValueType | None = None


class ConfigUpgradeError(Exception):
    pass


_SENTINEL = object()


class ConfigSection(QtCore.QObject):
    """Pure key-value configuration storage.

    Provides typed option access with memoization. No profile awareness —
    reads and writes go directly to/from the underlying QSettings store.
    Used for sections that don't participate in profiles (e.g. 'persist', 'profiles').
    """

    # Signal emitted when the value of a setting has changed.
    setting_changed = QtCore.pyqtSignal(str, object, object)

    def __init__(self, config: 'Config', name: str):
        super().__init__()
        self.__qt_config = config
        self.__name = name
        self.__prefix = self.__name + '/'
        self._memoization: dict[str, Memovar] = defaultdict(Memovar)
        self.display_name: str | None = None

    @property
    def section_name(self) -> str:
        """The name of this config section."""
        return self.__name

    def key(self, name):
        return self.__prefix + name

    def __getitem__(self, name: str) -> Any:
        opt = Option.get(self.__name, name)
        if opt is None:
            return None
        return self.value(opt, opt.default)

    def __setitem__(self, name: str, value: Any):
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

    def remove(self, name: str):
        key = self.key(name)
        config = self.__qt_config
        if config.contains(key):
            config.remove(key)
        try:
            del self._memoization[key]
        except KeyError:
            pass

    def raw_value(self, name: str, qtype: Any = None):
        """Return an option value without any type conversion."""
        key = self.key(name)
        if qtype is not None:
            value = self.__qt_config.value(key, type=qtype)
        else:
            value = self.__qt_config.value(key)
        return value

    def value(self, option: Option, default: ConfigValueType | None = None) -> Any:
        """Return an option value converted to the given Option type."""
        name = option.name
        if default is None:
            default = option.default
        if name in self:
            key = self.key(name)
            memovar = self._memoization[key]

            if memovar.dirty:
                try:
                    value = self.raw_value(name, qtype=option.qtype)
                    value = option.convert(value)
                    memovar.dirty = False
                    memovar.value = value
                except Exception as why:
                    log.error('Cannot read %s value: %s', self.key(name), why, exc_info=True)
                    value = default
                return value
            else:
                return memovar.value
        return default


class ProfileConfigSection(ConfigSection):
    """Configuration section with profile override support.

    Reads and writes for options marked with in_profile=True are intercepted:
    if an active profile overrides the option, the profile value is returned
    (or written) instead of the base config value.

    Used for plugin configuration sections that participate in profiles.
    """

    def __init__(self, config: 'Config', name: str):
        super().__init__(config, name)
        self.__qt_config = config

    def __getitem__(self, name: str) -> Any:
        opt = Option.get(self.section_name, name)
        if opt is None:
            return None
        if opt.in_profile:
            override = self._get_profile_override(name)
            if override is not _SENTINEL:
                return opt.convert(override)
        return self.value(opt, opt.default)

    def _profile_key(self, name: str) -> str:
        """Return the key for this option in the profile settings dict.

        Core options (section='setting') use bare name for backward compat.
        Plugin options use 'section/name' (e.g. 'plugin.<uuid>/greeting').
        """
        return setting_profile_key(name, self.section_name)

    def _get_all_profile_settings(self):
        """Return the active profile settings dict, or None if unavailable."""
        try:
            setting_section = self.__qt_config.setting
        except AttributeError:
            return None
        if setting_section.settings_override is not None:
            return setting_section.settings_override
        return self.__qt_config.profiles[SettingConfigSection.SETTINGS_KEY]

    def _is_settings_override_active(self) -> bool:
        """Return True if the dialog's settings override is active."""
        try:
            return self.__qt_config.setting.settings_override is not None
        except AttributeError:
            return False

    def _get_profile_override(self, name: str):
        """Check active profiles for an override of this option."""
        all_settings = self._get_all_profile_settings()
        if not all_settings:
            return _SENTINEL
        pkey = self._profile_key(name)
        for profile_id in self._get_active_profile_ids():
            settings = all_settings.get(profile_id)
            if settings and pkey in settings and settings[pkey] is not None:
                return settings[pkey]
        return _SENTINEL

    def _get_active_profile_ids(self):
        """Yield enabled profile IDs from the global profiles list."""
        try:
            setting_section = self.__qt_config.setting
        except AttributeError:
            return
        if setting_section.profiles_override is not None:
            profiles = setting_section.profiles_override
        else:
            profiles = self.__qt_config.profiles['user_profiles']
        if profiles:
            for profile in profiles:
                if profile['enabled']:
                    yield profile['id']

    def __setitem__(self, name: str, value: Any):
        opt = Option.get(self.section_name, name)
        if opt and opt.in_profile:
            if self._set_profile_override(name, value):
                return
        super().__setitem__(name, value)

    def _set_profile_override(self, name: str, value) -> bool:
        """Write value to active profile's settings if the option is overridden there.

        Returns True if the write was intercepted, False otherwise.
        """
        all_settings = self._get_all_profile_settings()
        if not all_settings:
            return False
        pkey = self._profile_key(name)
        is_override = self._is_settings_override_active()
        if isinstance(value, Enum):
            value = value.value
        for profile_id in self._get_active_profile_ids():
            settings = all_settings.get(profile_id)
            if settings and pkey in settings:
                old_value = settings[pkey]
                settings[pkey] = value
                if not is_override:
                    self._save_all_profile_settings(all_settings)
                if value != old_value:
                    self.setting_changed.emit(name, old_value, value)
                return True
        return False

    def _save_all_profile_settings(self, all_settings: dict):
        """Persist profile settings to the global profiles section."""
        key = self.__qt_config.profiles.key(SettingConfigSection.SETTINGS_KEY)
        self.__qt_config.setValue(key, all_settings)
        self.__qt_config.profiles._memoization[key].dirty = True

    def register_option(
        self, name: str, default: ConfigValueType, title: str | None = None, in_profile: bool = False
    ) -> Option:
        """Register an option in this config section.

        The option type is determined by the type of the default value.

        Args:
            name: Option name.
            default: Default value. Must not be None. Type determines the Option subclass.
            title: Human-readable title for display in profiles and quick menu.
                Falls back to name if not provided (with a warning for in_profile options).
            in_profile: If True, the option can be overridden by user profiles.

        Returns:
            The registered Option instance.

        Raises:
            TypeError: If default is None.
        """
        if default is None:
            raise TypeError('Option default value must not be None')

        if isinstance(default, str):
            option_type = TextOption
        elif isinstance(default, bool):
            option_type = BoolOption  # type: ignore[assignment]
        elif isinstance(default, int):
            option_type = IntOption  # type: ignore[assignment]
        elif isinstance(default, float):
            option_type = FloatOption  # type: ignore[assignment]
        elif isinstance(default, list) or isinstance(default, tuple):
            option_type = ListOption  # type: ignore[assignment]
        elif isinstance(default, Enum):
            option_type = Option  # type: ignore[assignment]
        else:
            option_type = Option  # type: ignore[assignment]

        opt = option_type(self.section_name, name, default, title=title, in_profile=in_profile)
        if in_profile:
            group_name = self.section_name
            group_title = self.display_name or self.section_name
            profile_groups_add_setting(
                group_name,
                name,
                (),
                title=group_title,
                parent='plugins',
                section=self.section_name,
            )
        return opt


class SettingConfigSection(ProfileConfigSection):
    """Profile-aware config section with dialog override support.

    Extends ProfileConfigSection with the ability to temporarily override
    profile data during options dialog editing (profiles_override,
    settings_override). This is the section used for Picard's global 'setting'.
    """

    PROFILES_KEY = 'user_profiles'
    SETTINGS_KEY = 'user_profile_settings'

    @classmethod
    def init_profile_options(cls):
        ListOption.add_if_missing('profiles', cls.PROFILES_KEY, [])
        Option.add_if_missing('profiles', cls.SETTINGS_KEY, {})

    def __init__(self, config: 'Config', name: str):
        super().__init__(config, name)
        self.__qt_config = config
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

    def set_profiles_override(self, new_profiles=None):
        self.profiles_override = new_profiles

    def set_settings_override(self, new_settings=None):
        self.settings_override = new_settings

    @contextmanager
    def no_profile(self):
        """Context manager that temporarily disables profile lookup."""
        saved_profiles = self.profiles_override
        saved_settings = self.settings_override
        self.profiles_override = []
        self.settings_override = None
        try:
            yield
        finally:
            self.profiles_override = saved_profiles
            self.settings_override = saved_settings


class Config(QtCore.QSettings):
    """Main configuration class based on QSettings.

    Use `Config.from_app` or `Config.from_file` to obtain a new `Config` instance.
    The class provides several `ConfigSection` instances that hold the actual settings.
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
        self.application: ConfigSection = ConfigSection(self, 'application')
        self.profiles: ConfigSection = ConfigSection(self, 'profiles')
        self.setting: SettingConfigSection = SettingConfigSection(self, 'setting')
        self.persist: ConfigSection = ConfigSection(self, 'persist')

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
        app = tagger_instance()
    global config, setting, persist, profiles
    if filename is None:
        config = Config.from_app(app)
    else:
        config = Config.from_file(app, filename)
    setting = config.setting
    persist = config.persist
    profiles = config.profiles


def get_config() -> Config:
    """Returns the global config object."""
    if not config:
        raise RuntimeError('config not yet set up')
    return config


def load_new_config(filename: str):
    config_file = get_config().fileName()
    try:
        shutil.copy(filename, config_file)
    except OSError:
        log.error("Failed restoring config file from %s", filename)
        return False
    setup_config(filename=config_file)
    return True


QuickMenuItem = namedtuple('QuickMenuItem', ['name', 'title'])
_quick_menu_items: dict[str, dict] = {}


def register_quick_menu_item(
    group_order: int, group_name: str, group_parent: str | None, group_title: str, option: Option
):
    """Register a BoolOption for the quick settings menu.

    Only BoolOptions are eligible. Non-bool options are silently skipped.
    If the option has no title, the option name is used with a warning.

    Args:
        group_order: Sort order for the group in the menu.
        group_name: Identifier for the options group (usually the page NAME).
        group_parent: Parent group name, or None/empty for top-level.
        group_title: Display title for the group.
        option: The Option to register. Must have qtype=bool.
    """
    if option.qtype is not bool:
        return
    # Plugin options are not supported in the quick settings menu yet
    if option.section != 'setting':
        return
    title = option.title
    if not title:
        log.warning("BoolOption '%s/%s' has no title, using option name for quick menu", option.section, option.name)
        title = option.name
    if group_name not in _quick_menu_items:
        group_parent = group_parent or ''
        _quick_menu_items[group_name] = {
            'order': group_order,
            'title': group_title,
            'parent': group_parent,
            'options': [],
        }
    _quick_menu_items[group_name]['options'].append(QuickMenuItem(option.name, title))


def get_quick_menu_items():
    for group, value in sorted(_quick_menu_items.items(), key=lambda x: (x[1]['parent'], x[1]['order'], x[0])):
        yield {'name': group, 'parent': value['parent'], 'title': value['title'], 'options': value['options']}
