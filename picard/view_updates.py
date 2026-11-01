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

"""Frontend-agnostic view-update suspension for the tagging core.

Some core operations move many files between containers in a tight loop (e.g.
`Album.match_files`). In the GUI this is wrapped in a context manager that
suspends the metadata box from re-rendering on every individual change and
refreshes once at the end — a pure UI performance optimization. Core code must
not reach into the GUI (`self.tagger.window.metadata_box.ignore_updates`) for
this, because that window does not exist in headless/CLI mode.

This module provides a small process-wide facade whose context managers core
code can use unconditionally:

    from picard.view_updates import view_updates

    with view_updates().suspend_metadata_box():
        for file, target in moves:
            file.move(target)

When a GUI frontend installs a sink, the context delegates to it (suspending
and then refreshing the view). With no sink (headless), the context is a no-op.
Mirrors the injected-provider pattern of `picard.notification` /
`picard.services`.
"""

from contextlib import (
    AbstractContextManager,
    nullcontext,
)
from typing import (
    Any,
    Protocol,
    runtime_checkable,
)


@runtime_checkable
class ViewUpdatesSink(Protocol):
    """Interface a frontend provides to receive view-update suspensions.

    The GUI main window satisfies this structurally: it exposes a metadata box
    with an ``ignore_updates`` context, an ``ignore_selection_changes`` context,
    a ``suspend_while_loading`` context, and the matching
    ``suspend_while_loading_enter`` / ``suspend_while_loading_exit`` methods.
    """

    @property
    def metadata_box(self) -> Any: ...

    @property
    def ignore_selection_changes(self) -> AbstractContextManager: ...

    @property
    def suspend_while_loading(self) -> AbstractContextManager: ...

    def suspend_while_loading_enter(self) -> None: ...

    def suspend_while_loading_exit(self) -> None: ...


class ViewUpdates:
    """Provides view-update suspension contexts, or no-ops when headless.

    A single instance is shared process-wide (see :func:`view_updates`). A GUI
    frontend installs its main window as the sink; in headless mode the sink
    stays ``None`` and the contexts/methods are no-ops.

    Several core operations touch a lot of items in a loop (file moves,
    clustering, bulk removal). In the GUI these are wrapped to suspend the
    selection/metadata-box/tree refresh and do it once at the end — purely a UI
    optimization. Core code uses the contexts here so the same code path works
    with or without a GUI.
    """

    def __init__(self):
        self._sink = None

    def set_sink(self, sink):
        """Install (or clear, with ``None``) the sink to delegate to."""
        self._sink = sink

    @property
    def has_sink(self) -> bool:
        return self._sink is not None

    def suspend_metadata_box(self) -> AbstractContextManager:
        """Suspend metadata-box refresh for a batch of changes.

        Delegates to the GUI's ``metadata_box.ignore_updates`` context when a
        sink is installed; a no-op context otherwise.
        """
        sink = self._sink
        if sink is None:
            return nullcontext()
        return sink.metadata_box.ignore_updates

    def suspend_selection(self) -> AbstractContextManager:
        """Suspend selection-change handling for a batch of changes.

        Delegates to the GUI's ``ignore_selection_changes`` context when a sink
        is installed; a no-op context otherwise.
        """
        sink = self._sink
        if sink is None:
            return nullcontext()
        return sink.ignore_selection_changes

    def suspend_while_loading(self) -> AbstractContextManager:
        """Suspend expensive view work (sorting, filtering) during a load.

        Delegates to the GUI's ``suspend_while_loading`` context when a sink is
        installed; a no-op context otherwise.
        """
        sink = self._sink
        if sink is None:
            return nullcontext()
        return sink.suspend_while_loading

    def suspend_while_loading_enter(self) -> None:
        """Imperatively begin a "while loading" suspension.

        For callers that enter and exit across asynchronous boundaries (where a
        ``with`` block cannot span the two). Paired with
        :meth:`suspend_while_loading_exit`. A no-op when headless.
        """
        if self._sink is not None:
            self._sink.suspend_while_loading_enter()

    def suspend_while_loading_exit(self) -> None:
        """Imperatively end a "while loading" suspension.

        Paired with :meth:`suspend_while_loading_enter`. A no-op when headless.
        """
        if self._sink is not None:
            self._sink.suspend_while_loading_exit()


_view_updates = ViewUpdates()


def view_updates() -> ViewUpdates:
    """Return the process-wide :class:`ViewUpdates` facade."""
    return _view_updates


def set_view_updates_sink(sink) -> None:
    """Install the sink (e.g. the main window) view suspensions delegate to.

    Passing ``None`` clears the sink and reverts to headless (no-op) behaviour.
    """
    _view_updates.set_sink(sink)
