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

"""Frontend-agnostic presentation actions for the tagging core.

A few core operations ask the frontend to perform a user-visible *presentation*
action that only makes sense when there is a window / tree view, such as raising
the application window to the front when a load is triggered from outside, or
removing items from the working set while keeping the tree view's selection
sane. Historically core did this by reaching into ``self.tagger.window`` /
``self.tagger.window.panel``, which does not exist in headless/CLI mode.

This module provides a small process-wide facade whose methods core code calls
unconditionally:

    from picard.view_presentation import view_presentation

    view_presentation().bring_to_front()
    view_presentation().remove([album])

A GUI frontend installs a sink (the application object); the facade forwards to
it. With no sink (headless), ``bring_to_front`` is a no-op and ``remove`` falls
back to removing straight from the workspace. Mirrors the injected-sink pattern
of :mod:`picard.notification`, :mod:`picard.view_updates` and
:mod:`picard.view_sync`.

This is distinct from :mod:`picard.view_updates` (which SUSPENDS view updates
around bulk operations) and :mod:`picard.view_sync` (which REQUESTS a one-off
refresh of the current selection): this facade performs a discrete presentation
ACTION on behalf of core.
"""

from collections.abc import Iterable
from typing import (
    Protocol,
    runtime_checkable,
)


@runtime_checkable
class ViewPresentationSink(Protocol):
    """Interface a frontend provides to perform presentation actions.

    The GUI application satisfies this structurally: ``bring_tagger_front``
    raises and activates the main window, and ``panel`` exposes a ``remove``
    that removes objects while suspending the tree's own selection-change
    handling and then fixing up the current selection.
    """

    def bring_tagger_front(self) -> None: ...

    @property
    def panel(self): ...


class ViewPresentation:
    """Performs presentation actions via an installed sink, or no-ops.

    A single instance is shared process-wide (see :func:`view_presentation`). A
    GUI frontend installs a sink; in headless mode the sink stays ``None`` and
    the actions are no-ops.
    """

    def __init__(self):
        self._sink: ViewPresentationSink | None = None

    def set_sink(self, sink: ViewPresentationSink | None):
        """Install (or clear, with ``None``) the sink to forward to."""
        self._sink = sink

    @property
    def has_sink(self) -> bool:
        return self._sink is not None

    def bring_to_front(self) -> None:
        """Raise and activate the application window.

        Forwards to the sink when installed; a no-op in headless mode (there is
        no window to raise).
        """
        if self._sink is not None:
            self._sink.bring_tagger_front()

    def remove(self, objects: Iterable) -> None:
        """Remove ``objects`` from the working set, keeping the view consistent.

        With a GUI sink, delegates to the panel's ``remove`` (which suspends the
        tree's own selection-change handling and then fixes up the current
        selection). In headless mode there is no tree, so it removes straight
        from the workspace.
        """
        if self._sink is not None:
            self._sink.panel.remove(objects)
        else:
            # Imported here to avoid an import cycle: picard.workspace reaches
            # this facade, so it must not be imported at module load time.
            from picard.workspace import workspace

            workspace().remove(objects)


_view_presentation = ViewPresentation()


def view_presentation() -> ViewPresentation:
    """Return the process-wide :class:`ViewPresentation` facade."""
    return _view_presentation


def set_view_presentation_sink(sink: ViewPresentationSink | None) -> None:
    """Install the sink (e.g. the application) presentation actions forward to.

    Passing ``None`` clears the sink and reverts to headless (no-op) behaviour.
    """
    _view_presentation.set_sink(sink)
