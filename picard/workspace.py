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

"""The workspace: the working set of a tagging run.

Beyond the long-lived *services* (see :mod:`picard.services`), the tagging
core keeps a *workspace*: the mutable working set of the current run — the
file, album, cluster and release-group registries, plus the small amount of
batch-save/restore bookkeeping that spans those entities. Historically this
state lives as attributes on the GUI ``Tagger`` object and core code reaches it
via ``self.tagger.<field>`` (i.e. ``tagger_instance()``), which couples the
tagging core to the GUI application object.

This module introduces :class:`Workspace`, a plain holder for that state, and a
process-wide accessor :func:`workspace` with :func:`set_workspace_provider`,
mirroring the injected-provider pattern already used by :mod:`picard.services`,
:mod:`picard.notification` and :mod:`picard.view_updates`.

The GUI ``Tagger`` owns a single :class:`Workspace` and exposes each field as a
property delegating to it, so existing ``self.tagger.albums`` (etc.) keep
working as a backwards-compatible surface for GUI code and plugins. Core code
reaches the working set and its orchestration methods through ``workspace()``
instead of the ``Tagger``, and the headless application builds and installs its
own workspace — so the same core code runs under the GUI, ``picard-cli`` or a
future web frontend.

Naming note: the *workspace* is the live, in-memory working set. It is distinct
from the :mod:`picard.session` package, which saves and restores that working
set to/from disk — the latter serializes the former.

The *services* vs *workspace* split is deliberate: services are long-lived
infrastructure shared across runs; the workspace is the per-run working set
that ``clear_session`` resets. ``stopping`` is application lifecycle (not
workspace) and stays on the application object.
"""


class Workspace:
    """The mutable working set of a tagging run.

    Holds the entity registries (``files``, ``albums``, ``clusters``,
    ``release_groups``, ``mbid_redirects``, ``unclustered_files``, ``nats``)
    and the batch-save / session-restore bookkeeping that spans them, together
    with the orchestration over that working set (loading and removing albums,
    clusters and files, NAT handling, autotagging, trashing). It is UI-agnostic:
    user feedback goes through the notification/view facades, not the GUI.
    """

    def __init__(self):
        # ClusterList/UnclusteredFiles are imported here, not at module level,
        # to break a circular import: picard.cluster imports picard.file, and
        # picard.file imports this module (workspace). A module-level import of
        # picard.cluster here would close that cycle.
        from picard.cluster import (
            ClusterList,
            UnclusteredFiles,
        )

        # Entity registries ---------------------------------------------------
        # filename -> File
        self.files = {}
        # left-pane clusters
        self.clusters = ClusterList()
        # release_id -> Album
        self.albums = {}
        # release_group_id -> ReleaseGroup
        self.release_groups = {}
        # old release_id -> new release_id (release redirects)
        self.mbid_redirects = {}
        # the "unclustered files" bucket
        self.unclustered_files = UnclusteredFiles()
        # the non-album-tracks container, created on first use
        self.nats = None

        # Bookkeeping ---------------------------------------------------------
        # Number of files currently queued/loading. Drives post-load actions
        # (e.g. auto-clustering of newly added files).
        self._pending_files_count = 0
        # Number of file save tasks currently queued or running. Used to
        # coalesce the (expensive) selection/metadata-box refresh so it runs
        # once when a batch save finishes rather than once per saved file.
        self._saving_files_count = 0
        # Parent containers (clusters/tracks/albums) whose cover-art image
        # aggregation was deferred during a batch save; each is refreshed once
        # when the batch completes (see File._saving_finished).
        self._saving_dirty_image_parents = set()
        # When True, we are restoring a session; skip auto-matching by MBIDs.
        self._restoring_session = False


_workspace: Workspace | None = None


def workspace() -> Workspace:
    """Return the process-wide :class:`Workspace`.

    The instance is created lazily on first access. This keeps importing this
    module free of any dependency on :mod:`picard.cluster` (which indirectly
    imports :mod:`picard.file`, which imports this module), avoiding an
    import-time cycle.
    """
    global _workspace
    if _workspace is None:
        _workspace = Workspace()
    return _workspace


def set_workspace_provider(provider: Workspace | None) -> None:
    """Install the :class:`Workspace` the accessor returns.

    Passing ``None`` resets the accessor; a fresh, empty workspace is created
    on the next :func:`workspace` call. Intended for the GUI / headless
    application objects, which each own the workspace for their run, and for
    tests that need an isolated workspace.
    """
    global _workspace
    _workspace = provider
