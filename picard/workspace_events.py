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

"""Frontend-agnostic "working set changed" signals for the tagging core.

The working-set orchestration (adding/removing albums, clusters and files)
needs to announce changes so a frontend can react — the GUI tree views add and
remove tree items, the status bar updates its counts, the metadata filter
tracks loaded files. Historically these announcements are Qt signals declared
on the GUI ``Tagger`` object (``album_added``/``album_removed``,
``cluster_added``/``cluster_removed``, ``file_loaded``,
``tagger_stats_changed``), and core code emits them via ``self.tagger.<sig>``.

This module provides a single, UI-independent emitter, :class:`WorkspaceEvents`
— a ``QObject`` carrying those same signals — plus a process-wide accessor
:func:`workspace_events`. Unlike the injected-sink facades
(:mod:`picard.notification`, :mod:`picard.view_sync`), it carries no sink: it
is a stateless signal hub, so a single eager instance is shared by every
frontend. The GUI connects its views to it; headless connects nothing.

The :class:`~picard.workspace.Workspace` orchestration methods emit through
``workspace_events()`` rather than reaching into the application object. A GUI
frontend connects its views to the same emitter; headless code simply never
connects a listener, so emission is a cheap no-op.

``QtCore`` signals work without a GUI (the headless application already relies
on this), so the emitter is a plain ``QObject`` used identically in both modes
— no separate no-op implementation is needed. Signal payloads are typed as
``object`` to keep this module free of core-entity imports (and the import
cycles they would create); the carried values are the usual Album / Cluster /
File instances.
"""

from PyQt6 import QtCore


class WorkspaceEvents(QtCore.QObject):
    """Qt signals announcing working-set (registry) changes.

    One instance is shared process-wide (see :func:`workspace_events`). The GUI
    connects its views to these signals; the working-set orchestration emits on
    them. In headless mode nothing connects, so emitting is a no-op.
    """

    #: An album (including a NAT album) was added to the working set.
    album_added = QtCore.pyqtSignal(object)
    #: An album was removed from the working set.
    album_removed = QtCore.pyqtSignal(object)
    #: A cluster was added to the working set.
    cluster_added = QtCore.pyqtSignal(object)
    #: A cluster was removed from the working set.
    cluster_removed = QtCore.pyqtSignal(object)
    #: A file finished loading.
    file_loaded = QtCore.pyqtSignal(object)
    #: Aggregate counts changed (file/album/pending totals) — refresh stats.
    tagger_stats_changed = QtCore.pyqtSignal()


# The process-wide emitter. A QObject with signals can be constructed (and
# connected/emitted) without a QApplication, and this module imports only
# PyQt6, so the instance is created eagerly at import — no lazy-init or
# installable provider is needed. It is a stateless signal hub shared by every
# frontend: the GUI connects its views to it, headless connects nothing. This
# matches the eager-singleton facades picard.notification / picard.view_sync.
_workspace_events = WorkspaceEvents()


def workspace_events() -> WorkspaceEvents:
    """Return the process-wide :class:`WorkspaceEvents` emitter."""
    return _workspace_events


def _reset_workspace_events_for_tests() -> None:
    """Replace the shared emitter with a fresh one (test isolation only).

    Tests connect listeners to the emitter; a fresh instance drops any
    connections left by a previous test. Not for production use — the emitter
    is a process-wide singleton that application code never replaces.
    """
    global _workspace_events
    _workspace_events = WorkspaceEvents()
