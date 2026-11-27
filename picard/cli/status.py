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

"""The status messages of the core, received by an interactive console.

The core reports what it is doing ("Loading album … …") through
:func:`picard.notification.notifier`; the GUI shows these messages in its status
bar. Without a sink they are only logged. :class:`ShellStatus` is the sink of
the console: it keeps the latest message, for the busy indicator to show.
"""

from typing import Any

from picard import log
from picard.i18n import gettext as _


def _format(message: str, params: Any) -> str:
    """``message`` with its placeholders filled in; as it is if they do not fit (a status must not raise)."""
    try:
        return message % params
    except (TypeError, ValueError, KeyError):
        return message


class ShellStatus:
    """A :class:`~picard.notification.NotifierSink` that keeps the latest status message."""

    def __init__(self):
        # Set from whichever thread reports, read by the busy indicator; a single
        # assignment is atomic, so there is no lock.
        self.latest: str | None = None

    def reset(self) -> None:
        """Forget the message, when a new command starts."""
        self.latest = None

    def set_statusbar_message(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Receive a status message, with the arguments of ``MainWindow.set_statusbar_message``.

        ``*args`` are the values of the placeholders (a mapping for named ones),
        ``echo`` is the function the untranslated message is passed to (default
        ``log.debug``), and ``translate`` the function that translates it (default
        ``_``); ``None`` disables either. An empty message clears the status.
        """
        echo = kwargs.get('echo', log.debug)
        translate = kwargs.get('translate', _)
        if len(args) == 1 and hasattr(args[0], 'keys') and hasattr(args[0], '__getitem__'):
            params = args[0]
        else:
            params = args
        if not message:
            self.latest = None
            return
        if echo:
            echo(_format(message, params))
        if translate:
            message = translate(message)
        self.latest = _format(message, params)

    # The rest of the sink is about a graphical interface.

    def enable_action(self, action_id: Any, enabled: Any) -> None:
        pass

    def set_processing(self, processing: bool = True) -> None:
        pass

    def flash_busy_cursor(self) -> None:
        pass
