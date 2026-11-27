# Picard, the next-generation MusicBrainz tagger
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

"""The confirmations the console asks for, which a session can turn on or off.

A destructive command has a confirmation key (``confirm_key``): the name of the
command, with underscores (``save``, ``option_save``). Every confirmation is on
unless its key is in the ``shell_confirmations_off`` persisted option, which is
the console's own: the GUI has its own choices ("do not show again") and the two
do not affect each other. ``confirm on`` and ``confirm off`` override a key for
this session only; ``confirm save`` writes the overrides to the configuration.
"""

from collections.abc import Iterable

from picard.config import get_config


_OPTION = 'shell_confirmations_off'


class SessionConfirmations:
    """Whether each confirmation is asked for in a session: its own value, else the saved one."""

    def __init__(self) -> None:
        self._values: dict[str, bool] = {}

    @staticmethod
    def _saved_off() -> set[str]:
        """The keys of the confirmations turned off in the configuration."""
        return set(get_config().persist[_OPTION])

    def is_enabled(self, key: str) -> bool:
        """Whether the console asks for the confirmation ``key``."""
        if key in self._values:
            return self._values[key]
        return key not in self._saved_off()

    def source_of(self, key: str) -> str:
        """Where the state of ``key`` comes from: ``session``, ``config`` (saved off) or ``default``."""
        if key in self._values:
            return 'session'
        return 'config' if key in self._saved_off() else 'default'

    def set(self, key: str, enabled: bool) -> None:
        """Ask (or not) for the confirmation ``key`` in this session."""
        self._values[key] = enabled

    def overridden(self) -> list[str]:
        """The keys set in this session, sorted."""
        return sorted(self._values)

    def save(self, keys: Iterable[str]) -> None:
        """Write the values set in this session for ``keys`` to the configuration, and forget them there."""
        off = self._saved_off()
        saved = [key for key in keys if key in self._values]
        if not saved:
            return
        for key in saved:
            if self._values.pop(key):
                off.discard(key)
            else:
                off.add(key)
        get_config().persist[_OPTION] = sorted(off)


def confirmation_keys(commands: Iterable) -> dict[str, list[str]]:
    """The confirmations of ``commands``, as ``{key: names of the commands that ask for it}``, by key."""
    keys: dict[str, list[str]] = {}
    for command in commands:
        if command.destructive:
            keys.setdefault(command.confirm_key, []).append(command.name)
    return dict(sorted(keys.items()))
