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

"""User-facing notification facade usable in both GUI and headless (CLI) modes.

Core/tagging code needs to report progress, status messages and action
availability to *a* user interface, but must not depend on a GUI being
present: the ``picard-cli`` headless mode runs on a bare ``QCoreApplication``
with no ``Tagger`` and no ``MainWindow`` (``tagger_instance()`` even raises
there).

This module provides a small process-wide facade that core code can call
unconditionally:

    from picard.notification import notifier

    notifier().status_message(N_("Loading %(id)s …"), {'id': album_id})

The method names describe *intent* (report a status message, mark the app as
processing, toggle a named action), not a particular rendering. A GUI sink
renders a status message in its status bar, a CLI sink might print it, a web
sink might push it over a socket.

By default the facade only logs (headless behaviour). A frontend installs a
sink at startup via :func:`set_notifier_sink`, after which notifications are
forwarded to it. Because the facade is independent of ``Tagger``, the same
core call sites work unchanged whether a GUI is running or not.

A sink is any object implementing :class:`NotifierSink` (the GUI main window
does so structurally). Keep this facade narrow: other "core needs the active
frontend" concerns (e.g. interactive confirmation prompts) should get their
own dedicated facade rather than being bolted on here.
"""

from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

from picard import log


@runtime_checkable
class NotifierSink(Protocol):
    """Structural interface a frontend provides to receive notifications.

    The GUI ``MainWindow`` satisfies this structurally; a CLI or web frontend
    can implement the same methods to receive the identical notifications.
    """

    def set_statusbar_message(self, message: str, *args: Any, **kwargs: Any) -> None: ...

    def enable_action(self, action_id: Any, enabled: Any) -> None: ...

    def set_processing(self, processing: bool = True) -> None: ...


class Notifier:
    """Forwards notifications to an installed sink, or logs if none.

    A single instance is shared process-wide (see :func:`notifier`). A
    frontend installs its sink (the GUI installs its main window); in headless
    mode the sink stays ``None`` and calls degrade to logging / no-ops.
    """

    def __init__(self):
        self._sink: NotifierSink | None = None

    def set_sink(self, sink: NotifierSink | None):
        """Install (or clear, with ``None``) the sink to forward to."""
        self._sink = sink

    @property
    def has_sink(self) -> bool:
        return self._sink is not None

    def status_message(self, message, *args, **kwargs):
        """Report a user-facing status/progress message.

        Forwards to the sink when one is installed. Otherwise the message is
        only logged, mirroring the sink's ``echo`` semantics (``echo``
        defaults to ``log.debug``; ``echo=None`` disables logging). See
        :meth:`picard.ui.mainwindow.MainWindow.set_statusbar_message` for the
        accepted arguments.
        """
        if self._sink is not None:
            self._sink.set_statusbar_message(message, *args, **kwargs)
            return
        echo = kwargs.get('echo', log.debug)
        if message and echo:
            params = args[0] if args else ()
            try:
                echo(message % params)
            except (TypeError, ValueError, KeyError):
                echo(message)

    def enable_action(self, action_id, enabled):
        """Enable/disable a named action.

        Forwards to the sink when installed; a no-op in headless mode.
        """
        if self._sink is not None:
            self._sink.enable_action(action_id, enabled)

    def set_processing(self, processing=True):
        """Signal that a (potentially long) processing operation is active.

        Forwards to the sink when installed; a no-op in headless mode.
        """
        if self._sink is not None:
            self._sink.set_processing(processing)


_notifier = Notifier()


def notifier():
    """Return the process-wide :class:`Notifier` facade."""
    return _notifier


def set_notifier_sink(sink):
    """Install the sink (e.g. the main window) that notifications forward to.

    Passing ``None`` clears the sink and reverts to headless (log-only)
    behaviour.
    """
    _notifier.set_sink(sink)
