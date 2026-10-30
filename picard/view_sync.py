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

"""Frontend-agnostic view-refresh requests for the tagging core.

A few core operations finish by asking the GUI to re-render the currently
selected item — the metadata box and the cover-art box — so a just-loaded
album or an edited track shows up. Historically core did this by reaching into
``self.tagger.window.refresh_metadatabox()`` /
``self.tagger.window.cover_art_box.update_metadata()``, which does not exist in
headless/CLI mode.

This module provides a small process-wide facade whose methods core code calls
unconditionally:

    from picard.view_sync import view_sync

    view_sync().refresh_metadata_box()
    view_sync().update_cover_art()

A GUI frontend installs its main window as the sink; the facade forwards to it.
With no sink (headless), the calls are no-ops. Mirrors the injected-sink
pattern of :mod:`picard.notification` and :mod:`picard.view_updates`.

This is distinct from :mod:`picard.view_updates`, which SUSPENDS view updates
around bulk operations; this facade REQUESTS a one-off refresh of the current
selection after an operation completes.
"""

from typing import (
    Protocol,
    runtime_checkable,
)


@runtime_checkable
class ViewSyncSink(Protocol):
    """Interface a frontend provides to receive view-refresh requests.

    The GUI main window satisfies this structurally: ``refresh_metadatabox``
    re-renders the metadata box for the current selection, and the cover-art
    box (``cover_art_box``) exposes ``update_metadata``.
    """

    def refresh_metadatabox(self) -> None: ...

    @property
    def cover_art_box(self): ...


class ViewSync:
    """Forwards view-refresh requests to an installed sink, or no-ops.

    A single instance is shared process-wide (see :func:`view_sync`). A GUI
    frontend installs its main window as the sink; in headless mode the sink
    stays ``None`` and the requests are no-ops.
    """

    def __init__(self):
        self._sink: ViewSyncSink | None = None

    def set_sink(self, sink: ViewSyncSink | None):
        """Install (or clear, with ``None``) the sink to forward to."""
        self._sink = sink

    @property
    def has_sink(self) -> bool:
        return self._sink is not None

    def refresh_metadata_box(self) -> None:
        """Request a refresh of the metadata box for the current selection.

        Forwards to the sink when installed; a no-op in headless mode.
        """
        if self._sink is not None:
            self._sink.refresh_metadatabox()

    def update_cover_art(self) -> None:
        """Request a refresh of the cover-art box for the current selection.

        Forwards to the sink when installed; a no-op in headless mode.
        """
        if self._sink is not None:
            self._sink.cover_art_box.update_metadata()


_view_sync = ViewSync()


def view_sync() -> ViewSync:
    """Return the process-wide :class:`ViewSync` facade."""
    return _view_sync


def set_view_sync_sink(sink: ViewSyncSink | None) -> None:
    """Install the sink (e.g. the main window) view-refresh requests forward to.

    Passing ``None`` clears the sink and reverts to headless (no-op) behaviour.
    """
    _view_sync.set_sink(sink)
