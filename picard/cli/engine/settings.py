#
# Picard, the next-generation MusicBrainz tagger
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

"""The settings of the console itself, as opposed to the options of Picard.

They are for this session only and nothing is written to the configuration.
Each is a number, and -1 means no limit.
"""

from dataclasses import dataclass


# The value that stands for "no limit".
UNLIMITED = -1


@dataclass(frozen=True)
class Setting:
    default: int
    title: str


SETTINGS = {
    'open_max': Setting(5, "most pages that 'open' opens at once"),
    'minted_max': Setting(12, "most handles written after 'minted:' (0 for none)"),
}


class SettingError(ValueError):
    """A setting that does not exist, or a value it cannot have."""


class ConsoleSettings:
    """The values of the settings of a session; those not set have their default."""

    def __init__(self) -> None:
        self._values: dict[str, int] = {}

    @staticmethod
    def _check_name(name: str) -> Setting:
        try:
            return SETTINGS[name]
        except KeyError:
            raise SettingError(f"unknown setting {name!r} ({', '.join(SETTINGS)})") from None

    def get(self, name: str) -> int:
        """The value of a setting."""
        setting = self._check_name(name)
        return self._values.get(name, setting.default)

    def limit(self, name: str) -> 'int | None':
        """The value of a setting as a limit: None if it is unlimited."""
        value = self.get(name)
        return None if value == UNLIMITED else value

    def set(self, name: str, text: str) -> None:
        """Set a setting from text."""
        self._check_name(name)
        try:
            value = int(text)
        except ValueError:
            raise SettingError(f"{name} is a number, not {text!r} ({UNLIMITED} for no limit)") from None
        if value < UNLIMITED:
            raise SettingError(f"{name} cannot be less than {UNLIMITED} ({UNLIMITED} for no limit)")
        self._values[name] = value

    def describe(self, name: str) -> dict[str, object]:
        """A setting as data: its value, default and title, and whether the session changed it."""
        setting = self._check_name(name)
        return {
            'name': name,
            'value': self.get(name),
            'default': setting.default,
            'title': setting.title,
            'source': 'session' if name in self._values else 'default',
        }

    def names(self) -> list[str]:
        return list(SETTINGS)
