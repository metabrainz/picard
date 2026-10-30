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

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

from picard import log
from picard.services import services
from picard.workspace_events import workspace_events


if TYPE_CHECKING:
    from picard.album import (
        Album,
        NatAlbum,
    )
    from picard.cluster import (
        ClusterList,
        UnclusteredFiles,
    )
    from picard.file import File
    from picard.releasegroup import ReleaseGroup


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
        self.files: dict[str, File] = {}
        # left-pane clusters
        self.clusters: ClusterList = ClusterList()
        # release_id -> Album
        self.albums: dict[str, Album] = {}
        # release_group_id -> ReleaseGroup
        self.release_groups: dict[str, ReleaseGroup] = {}
        # old release_id -> new release_id (release redirects)
        self.mbid_redirects: dict[str, str] = {}
        # the "unclustered files" bucket
        self.unclustered_files: UnclusteredFiles = UnclusteredFiles()
        # the non-album-tracks container, created on first use
        self.nats: NatAlbum | None = None

        # Bookkeeping ---------------------------------------------------------
        # Number of files currently queued/loading. Drives post-load actions
        # (e.g. auto-clustering of newly added files).
        self._pending_files_count: int = 0
        # Number of file save tasks currently queued or running. Used to
        # coalesce the (expensive) selection/metadata-box refresh so it runs
        # once when a batch save finishes rather than once per saved file.
        self._saving_files_count: int = 0
        # Parent containers (clusters/tracks/albums) whose cover-art image
        # aggregation was deferred during a batch save; each is refreshed once
        # when the batch completes (see File._saving_finished).
        self._saving_dirty_image_parents: set[Any] = set()
        # When True, we are restoring a session; skip auto-matching by MBIDs.
        self._restoring_session: bool = False

    # --- registry orchestration ---------------------------------------------

    def get_release_group_by_id(self, rg_id: str) -> ReleaseGroup:
        """Return the ReleaseGroup for ``rg_id``, creating it if unknown.

        The release-group registry is keyed by MBID; a new ReleaseGroup is
        created and cached on first request for an id.
        """
        # Imported here, not at module level, to avoid an import cycle
        # (picard.releasegroup -> picard.item -> ... -> picard.workspace).
        from picard.releasegroup import ReleaseGroup

        return self.release_groups.setdefault(rg_id, ReleaseGroup(rg_id))

    def remove_files(self, files, from_parent: bool = True) -> None:
        """Remove ``files`` from the working set.

        Cancels any pending lookup/fingerprint work, drops each file from the
        registry and detaches it from its parent, then announces the change.
        """
        acoustid_client = services().acoustid_client
        for file in files:
            if file.filename in self.files:
                file.clear_lookup_task()
                acoustid_client.stop_analyze(file)
                del self.files[file.filename]
                file.remove(from_parent)
        workspace_events().tagger_stats_changed.emit()

    def remove_album(self, album) -> None:
        """Remove ``album`` from the working set.

        Stops any in-flight loading, removes the album's files, clears the
        album from the registry and its release group, drops the NAT reference
        if applicable, announces the removal and runs post-removal processors.
        """
        # Local imports break cycles: picard.album imports this module, and
        # the ISRC manager is reached as a service.
        from picard.album import run_album_post_removal_processors

        log.debug("Removing %r", album)
        if album.id not in self.albums:
            return
        album.stop_loading()
        album.cancel_tasks()
        self.remove_files(list(album.iterfiles()))
        services().isrc_submit_manager.remove_album(album)
        del self.albums[album.id]
        if album.release_group:
            album.release_group.remove_album(album.id)
        if album == self.nats:
            self.nats = None
        workspace_events().album_removed.emit(album)
        run_album_post_removal_processors(album)
        workspace_events().tagger_stats_changed.emit()

    def remove_cluster(self, cluster) -> None:
        """Remove ``cluster`` from the working set.

        Special clusters (the unclustered bucket) are never removed. Clears the
        cluster's files, removes them from the working set, drops the cluster
        from the registry and announces the change.
        """
        if cluster.special:
            return
        log.debug("Removing %r", cluster)
        files = list(cluster.files)
        cluster.files = []
        cluster.clear()
        self.remove_files(files, from_parent=False)
        self.clusters.remove(cluster)
        workspace_events().cluster_removed.emit(cluster)

    def load_album(self, album_id: str, discid=None, disc_isrcs=None):
        """Load the release ``album_id`` into the working set.

        Resolves release redirects, returns the already-loaded album if present
        (attaching ``discid``), otherwise creates it, registers it, announces
        the addition and starts loading.
        """
        # Imported here to avoid the album <-> workspace import cycle.
        from picard.album import Album

        album_id = self.mbid_redirects.get(album_id, album_id)
        album = self.albums.get(album_id)
        if album:
            log.debug("Album %s already loaded.", album_id)
            album.add_discid(discid)
            return album
        album = Album(album_id, discid=discid, disc_isrcs=disc_isrcs)
        self.albums[album_id] = album
        workspace_events().album_added.emit(album)
        album.load()
        return album

    def move_files_to_album(self, files, albumid: str | None = None, album=None):
        """Move ``files`` to tracks on album ``albumid`` (or a given album).

        Exactly one of ``albumid`` / ``album`` is expected; when no album is
        given, ``albumid`` must be a release MBID.
        """
        if album is None:
            assert albumid is not None, "move_files_to_album requires albumid or album"
            album = self.load_album(albumid)
        album.match_files(files)

    def move_file_to_track(self, file, albumid, recordingid):
        """Move ``file`` to recording ``recordingid`` on album ``albumid``."""
        album = self.load_album(albumid)
        file.match_recordingid = recordingid
        album.match_files([file])


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
