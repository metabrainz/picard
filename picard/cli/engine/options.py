#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Control Picard's options from a session, without touching the configuration.

An option set in a session lives only for that session: the configuration file
is not written, so a mistake in a test run cannot change the settings the GUI
uses. It is done with what the core already has for the options dialog, an
in-memory profile: :class:`SessionOptions` puts a "session" profile with the top
priority in front of the user's profiles, and ``config.setting[...]`` then
returns its values like any profile's. Nothing else needs to know.

That only works for options that take part in profiles (180 of the 192), which
excludes internal and interface state (theme, plugin state, scripts); those
cannot be changed for a session. :meth:`SessionOptions.save` writes options to the
configuration, the one deliberate way to make them last.

Values are described and checked with the option's own type: ``Option.convert``
and the numeric bounds of ``checked_convert``.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
import difflib
import fnmatch
import json
from typing import Any

from picard.config import (
    BoolOption,
    BoundedNumberOption,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    OutOfBoundsError,
    SettingConfigSection,
    TextOption,
    get_config,
)
from picard.i18n import gettext as _


SECTION = 'setting'

# Id of the in-memory profile holding the session's values.
SESSION_PROFILE_ID = 'picard-cli-session'

_TRUE = frozenset({'1', 'true', 'yes', 'on'})
_FALSE = frozenset({'0', 'false', 'no', 'off'})

# Option kinds that can be set from text; anything else (scripts, colours, ...)
# is shown but not changed.
_SETTABLE_KINDS = frozenset({'bool', 'int', 'float', 'text', 'list'})


class OptionCommandError(ValueError):
    """The option name or value given by the user is not usable."""


def option_kind(option: Option) -> str:
    """A short name for the type of ``option``: bool, int, float, list, text or other."""
    for kind, option_type in (
        ('bool', BoolOption),
        ('int', IntOption),
        ('float', FloatOption),
        ('list', ListOption),
        ('text', TextOption),
    ):
        if isinstance(option, option_type):
            return kind
    return 'other'


def _plain(value: Any) -> Any:
    """``value`` as plain, serializable data."""
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def _parse_list(text: str) -> list[str]:
    """A list from a JSON array, or from comma-separated items."""
    text = text.strip()
    if text.startswith('['):
        try:
            return [str(item) for item in json.loads(text)]
        except ValueError as e:
            raise OptionCommandError(f"not a valid list: {e}") from None
    return [item.strip() for item in text.split(',') if item.strip()]


def parse_value(option: Option, text: str) -> Any:
    """The value of ``option`` written as ``text``, checked with the option's own rules."""
    if isinstance(option, BoolOption):
        word = text.strip().lower()
        if word in _TRUE:
            return True
        if word in _FALSE:
            return False
        raise OptionCommandError(f"expected true or false, not {text!r}")
    if isinstance(option, BoundedNumberOption):
        try:
            return option.checked_convert(text.strip())
        except OutOfBoundsError as e:
            raise OptionCommandError(f"{text.strip()} is out of range (nearest allowed: {e.corrected})") from None
        except ValueError:
            number = 'a whole number' if isinstance(option, IntOption) else 'a number'
            raise OptionCommandError(f"expected {number}, not {text!r}") from None
    if isinstance(option, ListOption):
        return _parse_list(text)
    return text


class SessionOptions:
    """The options of a session: values set for it, over the user's configuration.

    Nothing touches the configuration until :meth:`set` is first used, so a
    session that never sets an option behaves exactly as without this class.
    """

    def __init__(self):
        self._values: dict[str, Any] = {}
        self._installed = False

    # --- lookups ---------------------------------------------------------------

    @staticmethod
    def names() -> list[str]:
        """The names of all the options, sorted."""
        return sorted(name for section, name in Option.registry if section == SECTION)

    @staticmethod
    def _option(name: str) -> Option:
        option = Option.get(SECTION, name)
        if option is None:
            close = difflib.get_close_matches(name, SessionOptions.names(), n=3)
            hint = f" (did you mean {', '.join(close)}?)" if close else ""
            raise OptionCommandError(f"unknown option {name!r}{hint}")
        return option

    def _profile_titled(self, name: str) -> 'str | None':
        """The title of the first enabled profile of the user that sets ``name``."""
        config = get_config()
        profiles = config.profiles[SettingConfigSection.PROFILES_KEY] or []
        all_settings = config.profiles[SettingConfigSection.SETTINGS_KEY] or {}
        for profile in profiles:
            if profile['enabled'] and (all_settings.get(profile['id']) or {}).get(name) is not None:
                return profile['title']
        return None

    def source_of(self, name: str) -> str:
        """Where the value of ``name`` comes from: session, a profile, the config or the default."""
        if name in self._values:
            return 'session'
        title = self._profile_titled(name)
        if title is not None:
            return f"profile {title}"
        return 'config' if name in get_config().setting else 'default'

    def describe(self, name: str) -> dict[str, Any]:
        """The current value of ``name`` with its default, type, title and source."""
        option = self._option(name)
        kind = option_kind(option)
        return {
            'name': name,
            'value': _plain(get_config().setting[name]),
            'default': _plain(option.default),
            'type': kind,
            'title': _(option.title) if option.title else '',
            'source': self.source_of(name),
            'settable': option.in_profile and kind in _SETTABLE_KINDS,
        }

    def matching(self, pattern: 'str | None' = None) -> list[dict[str, Any]]:
        """The options matching ``pattern`` (a substring of the name or title, or a glob).

        Without a pattern, only those not at their default: set in the
        configuration, by a profile or by the session.
        """
        infos = []
        for name in self.names():
            info = self.describe(name)
            if pattern is None:
                if info['source'] == 'default':
                    continue
            elif not self._matches(pattern, name, info['title']):
                continue
            infos.append(info)
        return infos

    @staticmethod
    def _matches(pattern: str, name: str, title: str) -> bool:
        if not any(char in pattern for char in '*?['):
            pattern = f"*{pattern}*"
        return fnmatch.fnmatchcase(name, pattern) or fnmatch.fnmatchcase(title.lower(), pattern.lower())

    # --- the session's own values ----------------------------------------------

    def _install(self) -> None:
        """Put the session profile, with the top priority, in front of the user's profiles."""
        if self._installed:
            return
        config = get_config()
        section = config.setting
        profiles = list(config.profiles[SettingConfigSection.PROFILES_KEY] or [])
        saved = deepcopy(config.profiles[SettingConfigSection.SETTINGS_KEY] or {})
        session_profile = {'id': SESSION_PROFILE_ID, 'title': 'Session', 'enabled': True}
        # The settings dict of the session profile IS self._values: setting a
        # value is then enough for the configuration to return it.
        section.set_profiles_override([session_profile, *profiles])
        section.set_settings_override({**saved, SESSION_PROFILE_ID: self._values})
        self._installed = True

    @contextmanager
    def _without_session(self) -> Iterator[None]:
        """Write to the configuration as if the session did not exist."""
        section = get_config().setting
        profiles, settings = section.profiles_override, section.settings_override
        section.set_profiles_override(None)
        section.set_settings_override(None)
        try:
            yield
        finally:
            section.set_profiles_override(profiles)
            section.set_settings_override(settings)

    def set(self, name: str, text: str) -> dict[str, Any]:
        """Set ``name`` for the session, from its text form."""
        option = self._option(name)
        if not option.in_profile or option_kind(option) not in _SETTABLE_KINDS:
            raise OptionCommandError(f"{name} cannot be changed for a session")
        try:
            value = parse_value(option, text)
        except OptionCommandError as e:
            raise OptionCommandError(f"{name}: {e}") from None
        self._install()
        self._values[name] = value
        return self.describe(name)

    def unset(self, name: str) -> dict[str, Any]:
        """Forget the session's value of ``name``."""
        self._option(name)
        self._values.pop(name, None)
        return self.describe(name)

    def save(self, names: 'list[str] | None' = None) -> list[dict[str, Any]]:
        """Write the session's values (or just those of ``names``) to the configuration.

        Written as the GUI would: into the user profile that sets an option if
        there is one, else into the configuration itself. The value then no
        longer differs from the session's, so it stops being a session value.
        """
        chosen = list(self._values) if names is None else names
        for name in chosen:
            self._option(name)
            if name not in self._values:
                raise OptionCommandError(f"{name} has not been set in this session")
        config = get_config()
        with self._without_session():
            for name in chosen:
                config.setting[name] = self._values[name]
        for name in chosen:
            del self._values[name]
        if chosen:
            # A profile of the user may just have been written to: start again from
            # the saved state rather than from the copy taken when the session began.
            self._installed = False
            self._install()
        return [self.describe(name) for name in chosen]
