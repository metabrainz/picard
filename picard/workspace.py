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

from functools import partial
import os
from typing import (
    TYPE_CHECKING,
    Any,
)

from PyQt6 import QtCore

from picard import log
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.notification import notifier
from picard.services import services
from picard.view_updates import view_updates
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

    def create_nats(self) -> NatAlbum:
        """Return the Non-Album-Tracks container, creating it on first use."""
        # Imported here to avoid the album <-> workspace import cycle.
        from picard.album import NatAlbum

        if self.nats is None:
            self.nats = NatAlbum()
            self.albums['NATS'] = self.nats
            workspace_events().album_added.emit(self.nats)
            # ui_item is None in headless mode (no tree view); guard the GUI
            # expand. The GUI sets ui_item when it adds the album to the tree.
            if self.nats.ui_item is not None:
                self.nats.ui_item.setExpanded(True)
        return self.nats

    def get_nat_by_id(self, nat_id):
        """Return the already-loaded NAT with ``nat_id``, or None."""
        if self.nats is not None:
            for nat in self.nats.tracks:
                if nat.id == nat_id:
                    return nat
        return None

    def load_nat(self, nat_id, node=None):
        """Load the non-album track ``nat_id`` into the NATs container."""
        # Imported here to avoid the track <-> workspace import cycle.
        from picard.track import NonAlbumTrack

        nats = self.create_nats()
        nat = self.get_nat_by_id(nat_id)
        if nat:
            log.debug("NAT %s already loaded.", nat_id)
            return nat
        nat = NonAlbumTrack(nat_id)
        nats.tracks.append(nat)
        nats.update(True)
        if node:
            nat._parse_recording(node)
        else:
            nat.load()
        return nat

    def move_file_to_nat(self, file, recordingid, node=None):
        """Move ``file`` to the non-album track ``recordingid``."""
        nats = self.create_nats()
        file.move(nats.unmatched_files)
        nat = self.load_nat(recordingid, node=node)
        nat.run_when_loaded(partial(file.move, nat))
        if nat.loaded:
            nats.update()

    def autotag(self, objects):
        """Look up metadata for each taggable object in ``objects``.

        Flashes the busy cursor once per batch (fire-and-forget feedback) and
        delegates the actual lookup to each object.
        """
        flashed = False
        for obj in objects:
            if obj.can_autotag:
                if not flashed:
                    # Result appears asynchronously; acknowledge the action once.
                    notifier().flash_busy()
                    flashed = True
                obj.lookup_metadata()

    def remove_nat(self, track) -> None:
        """Remove the non-album track ``track`` from the working set."""
        log.debug("Removing %r", track)
        self.remove_files(list(track.iterfiles()))
        if not self.nats:
            return
        try:
            self.nats.tracks.remove(track)
        except ValueError:
            return
        if not self.nats.tracks:
            self.remove_album(self.nats)
        else:
            self.nats.update(True)

    def remove(self, objects) -> None:
        """Remove ``objects`` (files, tracks, albums, clusters) from the set."""
        # Imported here to avoid cycles with the entity modules.
        from picard.album import Album
        from picard.cluster import (
            Cluster,
            UnclusteredFiles,
        )
        from picard.file import File
        from picard.track import (
            NonAlbumTrack,
            Track,
        )

        files = []
        with view_updates().suspend_selection():
            for obj in objects:
                if isinstance(obj, File):
                    files.append(obj)
                elif isinstance(obj, NonAlbumTrack):
                    self.remove_nat(obj)
                elif isinstance(obj, Track):
                    files.extend(obj.files)
                elif isinstance(obj, Album):
                    notifier().status_message(
                        N_("Removing album %(id)s: %(artist)s - %(album)s"),
                        {'id': obj.id, 'artist': obj.metadata['albumartist'], 'album': obj.metadata['album']},
                    )
                    self.remove_album(obj)
                elif isinstance(obj, UnclusteredFiles):
                    files.extend(list(obj.files))
                elif isinstance(obj, Cluster):
                    self.remove_cluster(obj)
            if files:
                self.remove_files(files)

    def trash_files(self, files) -> None:
        """Move ``files`` to the system trash and remove them from the set."""
        with view_updates().suspend_selection():
            files_removed = []
            for file in files:
                success, new_location = QtCore.QFile.moveToTrash(file.filename)
                # If the old file still exists, consider this an error. Moving to
                # trash without write permission on the file can fail on Linux with
                # success still being set to True.
                if success and not os.path.exists(file.filename):
                    # While the file has not been fully removed, update the location
                    # to the trash location. Removing the files completely will be done
                    # afterwards.
                    del self.files[file.filename]
                    file.filename = new_location
                    self.files[new_location] = file
                    files_removed.append(file)
                else:
                    notifier().status_message(_('Failed moving "%(filename)s" to trash'), {'filename': file.filename})

            if files_removed:
                self.remove_files(files)
            notifier().status_message(_('Moved %(count)i files to trash'), {'count': len(files_removed)})

    def load_cluster(self, name, artist):
        """Return the cluster matching ``name``/``artist``, creating it if new."""
        # Imported here to avoid the cluster <-> workspace import cycle.
        from picard.cluster import Cluster

        for cluster in self.clusters:
            cm = cluster.metadata
            if name == cm['album'] and artist == cm['albumartist']:
                return cluster
        cluster = Cluster(name, artist)
        self.clusters.append(cluster)
        workspace_events().cluster_added.emit(cluster)
        return cluster


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
