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

from collections.abc import (
    Callable,
    Iterable,
    Iterator,
)
from functools import partial
import os
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from PyQt6 import QtCore

from picard import log
from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.item import ListOfMetadataItems
from picard.notification import notifier
from picard.services import services
from picard.util import (
    IterableFiles,
    iter_files_from_objects,
    mbid_validate,
    thread,
)
from picard.view_updates import view_updates
from picard.workspace_events import workspace_events


if TYPE_CHECKING:
    from picard.album import (
        Album,
        NatAlbum,
    )
    from picard.cluster import (
        Cluster,
        ClusterList,
        UnclusteredFiles,
    )
    from picard.file import File
    from picard.item import Item
    from picard.releasegroup import ReleaseGroup
    from picard.track import NonAlbumTrack


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

    # --- save-batch coordination --------------------------------------------
    #
    # File saves run on a thread pool. The selection/metadata-box refresh and
    # the per-parent cover-art image rebuild are expensive, so instead of doing
    # them once per saved file they are coalesced to run once when the whole
    # batch finishes. Files call begin_save()/end_save() around each save and
    # defer_image_parent() for the parents to refresh; end_save() reports when
    # the batch is complete.

    def begin_save(self) -> None:
        """Record that a file save task has been queued."""
        self._saving_files_count += 1

    def end_save(self) -> bool:
        """Record that a file save task finished; return True if the batch is done.

        "Done" means no save tasks remain in flight, so the caller can run the
        coalesced end-of-batch refresh (see :meth:`flush_saving_image_parents`).
        """
        if self._saving_files_count > 0:
            self._saving_files_count -= 1
        return self._saving_files_count == 0

    def defer_image_parent(self, parent) -> None:
        """Register ``parent`` for a single cover-art rebuild at batch end.

        During a batch save, a file registers its parent containers here
        instead of emitting ``metadata_images_changed`` per file; they are
        rebuilt once by :meth:`flush_saving_image_parents`.
        """
        self._saving_dirty_image_parents.add(parent)

    def flush_saving_image_parents(self):
        """Rebuild cover-art image aggregation once for each container whose
        update was deferred during a batch save, then clear the set.

        During a batch save, files register their parent containers (clusters,
        tracks, albums) via :meth:`defer_image_parent` instead of emitting
        ``metadata_images_changed`` per file (which would rebuild each parent's
        image list over all children once per saved file). This performs that
        rebuild a single time when the batch completes. For standalone files
        (no parent) the set stays empty and this is a no-op.
        """
        parents = self._saving_dirty_image_parents
        if not parents:
            return
        # Copy and clear first: update_metadata_images() may emit signals that
        # trigger further updates; we don't want to iterate a mutating set.
        self._saving_dirty_image_parents = set()
        for parent in parents:
            update = getattr(parent, 'update_metadata_images', None)
            if update is not None:
                update()

    # --- session-restore bookkeeping ----------------------------------------
    #
    # While a saved session is being restored, auto-matching by MBID is
    # suppressed until all file loads and web requests settle. The session
    # loader sets ``restoring_session`` and later clears it once
    # ``pending_files_count`` reaches zero.

    @property
    def pending_files_count(self) -> int:
        """Number of files currently queued/loading."""
        return self._pending_files_count

    def add_pending_files(self, count: int) -> None:
        """Increase the pending-files counter by ``count``."""
        self._pending_files_count += count

    def file_pending_done(self) -> int:
        """Record one pending file as settled; return the remaining count."""
        self._pending_files_count -= 1
        return self._pending_files_count

    @property
    def restoring_session(self) -> bool:
        """True while a saved session is being restored."""
        return self._restoring_session

    @restoring_session.setter
    def restoring_session(self, value: bool) -> None:
        self._restoring_session = value

    def iter_album_files(self) -> Iterator[File]:
        """Yield every file matched to a loaded album."""
        for album in self.albums.values():
            yield from album.iterfiles()

    def iter_all_files(self) -> Iterator[File]:
        """Yield every file in the working set (unclustered, album, cluster)."""
        # unclustered_files.files is a ListOfMetadataItems (typed MetadataItem)
        # but only ever holds File at runtime; narrow to File.
        yield from cast("Iterator[File]", self.unclustered_files.files)
        yield from self.iter_album_files()
        yield from self.clusters.iterfiles()

    def clear_session(self) -> None:
        """Remove all files, clusters and albums from the working set."""
        with view_updates().suspend_selection():
            # Remove all albums (includes NAT)
            for album in list(self.albums.values()):
                self.remove_album(album)
            # Remove all left-pane clusters
            for cluster in list(self.clusters):
                self.remove_cluster(cluster)
            # Remove all unclustered files
            if self.unclustered_files.files:
                # ListOfMetadataItems holds MetadataItem; the unclustered bucket
                # only ever contains File at runtime.
                self.remove_files(cast("list[File]", list(self.unclustered_files.files)))

    def get_release_group_by_id(self, rg_id: str) -> ReleaseGroup:
        """Return the ReleaseGroup for ``rg_id``, creating it if unknown.

        The release-group registry is keyed by MBID; a new ReleaseGroup is
        created and cached on first request for an id.
        """
        # Imported here, not at module level, to avoid an import cycle
        # (picard.releasegroup -> picard.item -> ... -> picard.workspace).
        from picard.releasegroup import ReleaseGroup

        return self.release_groups.setdefault(rg_id, ReleaseGroup(rg_id))

    def remove_files(self, files: Iterable[File], from_parent: bool = True) -> None:
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

    def remove_album(self, album: Album) -> None:
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

    def remove_cluster(self, cluster: Cluster) -> None:
        """Remove ``cluster`` from the working set.

        Special clusters (the unclustered bucket) are never removed. Clears the
        cluster's files, removes them from the working set, drops the cluster
        from the registry and announces the change.
        """
        if cluster.special:
            return
        log.debug("Removing %r", cluster)
        # cluster.files is a ListOfMetadataItems (MetadataItem) but holds File.
        files = cast("list[File]", list(cluster.files))
        cluster.files = ListOfMetadataItems()
        cluster.clear()
        self.remove_files(files, from_parent=False)
        self.clusters.remove(cluster)
        workspace_events().cluster_removed.emit(cluster)

    def load_album(self, album_id: str, discid=None, disc_isrcs: dict[int, str] | None = None) -> Album:
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

    def move_files_to_album(
        self, files: Iterable[File], albumid: str | None = None, album: Album | None = None
    ) -> None:
        """Move ``files`` to tracks on album ``albumid`` (or a given album).

        Exactly one of ``albumid`` / ``album`` is expected; when no album is
        given, ``albumid`` must be a release MBID.
        """
        if album is None:
            assert albumid is not None, "move_files_to_album requires albumid or album"
            album = self.load_album(albumid)
        album.match_files(files)

    def move_file_to_track(self, file: File, albumid: str, recordingid: str) -> None:
        """Move ``file`` to recording ``recordingid`` on album ``albumid``."""
        album = self.load_album(albumid)
        file.match_recordingid = recordingid
        album.match_files([file])

    def move_file_to_album(self, file: File, albumid: str) -> None:
        """Move ``file`` to a track on album ``albumid``."""
        self.move_files_to_album([file], albumid)

    def move_file(self, file: File, target: Item | None) -> Item | None:
        """Move ``file`` to ``target``, if possible.

        ``target`` may be an album (the file goes to a matching track, or to the
        album's unmatched bucket while a session is being restored) or any other
        container the file can be moved into. If the move is rejected and the
        file would be left without a parent, it falls back to the unclustered
        bucket so it still appears in the working set.

        Returns the container the file actually ended up in, or ``None`` if the
        target was unsupported and no move happened.
        """
        # Imported here to avoid the album/file <-> workspace import cycle.
        from picard.album import Album
        from picard.file import File

        if isinstance(target, Album):
            # During restore place into album's unmatched bucket without matching
            if self.restoring_session:
                file.move(target.unmatched_files)
            else:
                self.move_files_to_album([file], album=target)
        else:
            if isinstance(target, File) and target.parent_item:
                target = target.parent_item
            if not file.move(target):
                # Ensure a file always has a parent so it shows up in UI
                if not file.parent_item:
                    target = self.unclustered_files
                    file.move(target)
                # Unsupported target, do not move the file
                else:
                    target = None
        return target

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

    def get_nat_by_id(self, nat_id: str) -> NonAlbumTrack | None:
        """Return the already-loaded NAT with ``nat_id``, or None."""
        if self.nats is not None:
            for nat in self.nats.tracks:
                if nat.id == nat_id:
                    # NatAlbum.tracks is typed list[Track] (shared base), but by
                    # construction a NATs container only ever holds
                    # NonAlbumTrack (see load_nat); narrow to the real type.
                    return cast("NonAlbumTrack", nat)
        return None

    def load_nat(self, nat_id: str, node=None) -> NonAlbumTrack:
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

    def move_file_to_nat(self, file: File, recordingid: str, node=None) -> None:
        """Move ``file`` to the non-album track ``recordingid``."""
        nats = self.create_nats()
        file.move(nats.unmatched_files)
        nat = self.load_nat(recordingid, node=node)
        nat.run_when_loaded(partial(file.move, nat))
        if nat.loaded:
            nats.update()

    def autotag(self, objects: Iterable[Item]) -> None:
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

    def remove_nat(self, track: NonAlbumTrack) -> None:
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

    def remove(self, objects: Iterable[Item]) -> None:
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
                # files accumulated above are all File at runtime, but the
                # Track/UnclusteredFiles .files sources are typed MetadataItem.
                self.remove_files(cast("list[File]", files))

    def trash_files(self, files: Iterable[File]) -> None:
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

    def load_cluster(self, name: str, artist: str) -> Cluster:
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

    def apply_file_cluster(self, file_cluster) -> Cluster | UnclusteredFiles:
        """Place one computed ``file_cluster`` group into the working set.

        A group of more than one file becomes a cluster (created or reused via
        :meth:`load_cluster`); a single-file group stays in the unclustered
        bucket. Returns the container the files were added to. This is the
        per-group application step shared by the synchronous
        :meth:`cluster_files` and the asynchronous :meth:`cluster`.
        """
        files = set(file_cluster.files)
        if len(files) > 1:
            container: Cluster | UnclusteredFiles = self.load_cluster(file_cluster.title, file_cluster.artist)
        else:
            container = self.unclustered_files
        container.add_files(files)
        return container

    def cluster_files(self, files) -> list:
        """Group ``files`` into clusters by metadata and apply the result synchronously.

        Runs the clustering algorithm inline (it is CPU-bound metadata grouping,
        not I/O — no event loop needed) and applies each resulting group via
        :meth:`apply_file_cluster`. Returns the list of clusters that received
        files (new or existing), in creation order; single-file groups stay in
        the unclustered bucket and are not included.

        This is the blocking variant, for callers that want the result
        immediately (e.g. a headless command). The GUI and other event-loop
        frontends use the asynchronous :meth:`cluster` instead.
        """
        # Imported here to avoid the cluster <-> workspace import cycle.
        from picard.cluster import (
            Cluster,
            UnclusteredFiles,
        )

        touched: list = []
        for file_cluster in Cluster.cluster(files):
            container = self.apply_file_cluster(file_cluster)
            if not isinstance(container, UnclusteredFiles) and container not in touched:
                touched.append(container)
        return touched

    def cluster(self, objs: Iterable[IterableFiles], on_complete: Callable[[], Any] | None = None) -> None:
        """Group the files reachable from ``objs`` into clusters asynchronously.

        The clustering algorithm is CPU-bound, so it runs on a worker thread
        (via :func:`picard.util.thread.run_task`); the resulting groups are then
        applied on the main thread in time-budgeted batches (via
        :func:`picard.util.thread.process_in_batches`) so a frontend stays
        responsive while many clusters are created. ``on_complete`` (if given)
        is called once all groups have been applied.

        This is frontend-agnostic: the threading and batching rely only on the
        application's thread pool and Qt event loop (present in the GUI and the
        headless application alike), and user feedback goes through the
        notification/view facades. The synchronous :meth:`cluster_files` is the
        blocking alternative for callers that want the result immediately.
        """
        # Imported here to avoid the cluster <-> workspace import cycle.
        from picard.cluster import Cluster

        files = tuple(iter_files_from_objects(objs))
        if files:
            # Clustering runs on a background thread; acknowledge the action.
            notifier().flash_busy()
        if log.is_debug():
            limit = 5
            count = len(files)
            remain = max(0, count - limit)
            log.debug(
                "Clustering %d files: %r%s", count, files[:limit], f" and {remain} more files..." if remain else ""
            )

        def compute():
            # Run fully in the worker thread; do not return the iterator.
            return tuple(Cluster.cluster(files))

        thread.run_task(compute, partial(self._clustering_finished, on_complete))

    def _clustering_finished(self, on_complete, result=None, error=None) -> None:
        """Apply computed clusters on the main thread, in batches."""
        if error:
            log.error("Error while clustering: %r", error)
            return
        clusters = list(result or ())
        view_updates().suspend_while_loading_enter()

        def finished():
            view_updates().suspend_while_loading_exit()
            if on_complete:
                on_complete()

        thread.process_in_batches(clusters, self.apply_file_cluster, "Clustering", on_complete=finished)

    def save(self, objects: Iterable[IterableFiles]) -> None:
        """Save every file reachable from ``objects`` to disk.

        ``objects`` may be any mix of files, tracks, albums and clusters (any
        object exposing ``iterfiles``); each contained file is saved. The
        per-file threading (the save thread pool) and the batch coalescing of
        shared cover-art parents live in :class:`~picard.file.File` and the
        begin_save/end_save bookkeeping, so this is a thin, UI-agnostic driver
        usable from the GUI and headless.
        """
        for file in iter_files_from_objects(objects, save=True):
            file.save()

    @property
    def use_acoustid(self) -> bool:
        """True when AcoustID is the configured fingerprinting system."""
        return get_config().setting['fingerprinting_system'] == 'acoustid'

    def analyze(self, objs: Iterable[IterableFiles]) -> None:
        """Identify files by AcoustID fingerprint (the GUI "Scan" action).

        For each analyzable file reachable from ``objs``, compute its AcoustID
        fingerprint and look up matching recordings, applying the result via
        the file's usual ACOUSTID lookup handler. No-op unless AcoustID is the
        configured fingerprinting system. UI-agnostic: the fingerprint work
        runs on the AcoustID client (a service) and results arrive
        asynchronously.
        """
        if not self.use_acoustid:
            return
        # Imported here to avoid the file <-> workspace import cycle.
        from picard.file import File

        flashed = False
        for file in iter_files_from_objects(objs):
            if file.can_analyze:
                if not flashed:
                    # Result appears asynchronously; acknowledge the action once.
                    notifier().flash_busy()
                    flashed = True
                file.set_pending()
                services().acoustid_client.analyze(file, partial(file._lookup_finished, File.LookupType.ACOUSTID))

    def generate_fingerprints(self, objs: Iterable[IterableFiles]) -> None:
        """Compute AcoustID fingerprints for files without matching them.

        No-op unless AcoustID is the configured fingerprinting system.
        """
        if not self.use_acoustid:
            return

        def finished(file, result):
            file.clear_pending()

        for file in iter_files_from_objects(objs):
            file.set_pending()
            services().acoustid_client.fingerprint(file, partial(finished, file))

    def place_loaded_file(self, file: File, target: Item | None = None, unmatched_files: list | None = None) -> bool:
        """Place a freshly loaded ``file`` into the working set.

        Implements the per-file placement policy applied right after a file
        loads: honour embedded MusicBrainz IDs (move to the matching track,
        album or non-album track), otherwise move it to ``target`` (falling
        back to the unclustered bucket), and — when nothing matched — optionally
        queue an AcoustID analyze. Files that errored go to the unclustered
        bucket. ``file`` must be a successfully loaded, error-free file.

        When ``unmatched_files`` is given, a file that could not be placed
        anywhere meaningful is appended to it (the caller uses this to decide
        whether to auto-cluster the leftovers).

        Returns True if the file was moved somewhere other than the unclustered
        bucket. This is the UI-agnostic core of the GUI ``Tagger._file_loaded``
        callback; the GUI keeps the view-suspend bookkeeping and the auto-cluster
        of the leftovers around this call.
        """
        config = get_config()
        file_moved = False
        if not config.setting['ignore_file_mbids'] and not self.restoring_session:
            recordingid = file.metadata.getall('musicbrainz_recordingid')
            recordingid = recordingid[0] if recordingid else ''
            is_valid_recordingid = mbid_validate(recordingid)

            albumid = file.metadata.getall('musicbrainz_albumid')
            albumid = albumid[0] if albumid else ''
            is_valid_albumid = mbid_validate(albumid)

            if is_valid_albumid and is_valid_recordingid:
                log.debug("%r has release (%s) and recording (%s) MBIDs, moving to track…", file, albumid, recordingid)
                self.move_file_to_track(file, albumid, recordingid)
                file_moved = True
            elif is_valid_albumid:
                log.debug("%r has only release MBID (%s), moving to album…", file, albumid)
                self.move_file_to_album(file, albumid)
                file_moved = True
            elif is_valid_recordingid:
                log.debug("%r has only recording MBID (%s), moving to non-album track…", file, recordingid)
                self.move_file_to_nat(file, recordingid)
                file_moved = True

        if not file_moved:
            target = self.move_file(file, target)
            if target and target != self.unclustered_files:
                file_moved = True

        if not file_moved and unmatched_files is not None:
            unmatched_files.append(file)

        # fallback on analyze if nothing else worked
        if not file_moved and not self.restoring_session and config.setting['analyze_new_files'] and file.can_analyze:
            log.debug("Trying to analyze %r …", file)
            self.analyze([file])

        return file_moved


_workspace: Workspace | None = None


class WorkspaceHost:
    """Delegating access to the working set for an application object.

    Both the GUI ``Tagger`` and the headless ``HeadlessTagger`` own a
    :class:`Workspace` as ``self._workspace`` and historically exposed each of
    its entity registries as ``self.<field>`` (so core code and plugins reaching
    the running app via ``tagger_instance()`` — e.g. ``self.tagger.albums`` —
    keep working). This mixin provides those delegating properties once, shared
    by both app objects, instead of duplicating the boilerplate in each. The
    save-batch / session-restore bookkeeping is not delegated; it is reached
    through the :class:`Workspace` public methods (``begin_save`` etc.).

    Requires the host to set ``self._workspace`` (a :class:`Workspace`) before
    these are used.
    """

    _workspace: Workspace

    @property
    def files(self) -> dict[str, File]:
        return self._workspace.files

    @files.setter
    def files(self, value: dict[str, File]) -> None:
        self._workspace.files = value

    @property
    def clusters(self) -> ClusterList:
        return self._workspace.clusters

    @clusters.setter
    def clusters(self, value: ClusterList) -> None:
        self._workspace.clusters = value

    @property
    def albums(self) -> dict[str, Album]:
        return self._workspace.albums

    @albums.setter
    def albums(self, value: dict[str, Album]) -> None:
        self._workspace.albums = value

    @property
    def release_groups(self) -> dict[str, ReleaseGroup]:
        return self._workspace.release_groups

    @release_groups.setter
    def release_groups(self, value: dict[str, ReleaseGroup]) -> None:
        self._workspace.release_groups = value

    @property
    def mbid_redirects(self) -> dict[str, str]:
        return self._workspace.mbid_redirects

    @mbid_redirects.setter
    def mbid_redirects(self, value: dict[str, str]) -> None:
        self._workspace.mbid_redirects = value

    @property
    def unclustered_files(self) -> UnclusteredFiles:
        return self._workspace.unclustered_files

    @unclustered_files.setter
    def unclustered_files(self, value: UnclusteredFiles) -> None:
        self._workspace.unclustered_files = value

    @property
    def nats(self) -> NatAlbum | None:
        return self._workspace.nats

    @nats.setter
    def nats(self, value: NatAlbum | None) -> None:
        self._workspace.nats = value

    # --- working-set operations (shared plugin/GUI compatibility surface) ----
    #
    # Thin delegates so both the GUI Tagger and the headless HeadlessTagger
    # expose the same working-set operations on the app object. Core code calls
    # workspace().<op> directly; these keep tagger.<op> working for plugins and
    # existing GUI callers.

    def iter_album_files(self) -> Iterator[File]:
        """Yield every file matched to a loaded album.

        Delegates to :meth:`Workspace.iter_album_files`.
        """
        return self._workspace.iter_album_files()

    def iter_all_files(self) -> Iterator[File]:
        """Yield every file in the working set.

        Delegates to :meth:`Workspace.iter_all_files`.
        """
        return self._workspace.iter_all_files()

    def clear_session(self) -> None:
        """Remove all files, clusters and albums from the working set.

        Delegates to :meth:`Workspace.clear_session`.
        """
        self._workspace.clear_session()

    def get_release_group_by_id(self, rg_id: str) -> ReleaseGroup:
        """Return the ReleaseGroup for ``rg_id``, creating it if unknown.

        Delegates to :meth:`Workspace.get_release_group_by_id`.
        """
        return self._workspace.get_release_group_by_id(rg_id)

    def load_album(self, album_id: str, discid=None, disc_isrcs: dict[int, str] | None = None) -> Album:
        """Load the release ``album_id`` into the working set.

        Delegates to :meth:`Workspace.load_album`.
        """
        return self._workspace.load_album(album_id, discid=discid, disc_isrcs=disc_isrcs)

    def load_nat(self, nat_id: str, node=None) -> NonAlbumTrack:
        """Load the non-album track ``nat_id`` into the NATs container.

        Delegates to :meth:`Workspace.load_nat`.
        """
        return self._workspace.load_nat(nat_id, node=node)

    def get_nat_by_id(self, nat_id: str) -> NonAlbumTrack | None:
        """Return the already-loaded NAT with ``nat_id``, or None.

        Delegates to :meth:`Workspace.get_nat_by_id`.
        """
        return self._workspace.get_nat_by_id(nat_id)

    def create_nats(self) -> NatAlbum:
        """Return the Non-Album-Tracks container, creating it on first use.

        Delegates to :meth:`Workspace.create_nats`.
        """
        return self._workspace.create_nats()

    def load_cluster(self, name: str, artist: str) -> Cluster:
        """Return the cluster matching ``name``/``artist``, creating it if new.

        Delegates to :meth:`Workspace.load_cluster`.
        """
        return self._workspace.load_cluster(name, artist)

    def move_files_to_album(
        self, files: Iterable[File], albumid: str | None = None, album: Album | None = None
    ) -> None:
        """Move ``files`` to tracks on album ``albumid`` (or a given album).

        Delegates to :meth:`Workspace.move_files_to_album`.
        """
        self._workspace.move_files_to_album(files, albumid=albumid, album=album)

    def move_file_to_album(self, file: File, albumid: str) -> None:
        """Move ``file`` to a track on album ``albumid``.

        Delegates to :meth:`Workspace.move_file_to_album`.
        """
        self._workspace.move_file_to_album(file, albumid)

    def move_file_to_track(self, file: File, albumid: str, recordingid: str) -> None:
        """Move ``file`` to recording ``recordingid`` on album ``albumid``.

        Delegates to :meth:`Workspace.move_file_to_track`.
        """
        self._workspace.move_file_to_track(file, albumid, recordingid)

    def move_file_to_nat(self, file: File, recordingid: str, node=None) -> None:
        """Move ``file`` to the non-album track ``recordingid``.

        Delegates to :meth:`Workspace.move_file_to_nat`.
        """
        self._workspace.move_file_to_nat(file, recordingid, node=node)

    def move_file(self, file: File, target: Item | None) -> Item | None:
        """Move ``file`` to ``target``, if possible.

        Delegates to :meth:`Workspace.move_file`.
        """
        return self._workspace.move_file(file, target)

    def autotag(self, objects: Iterable[Item]) -> None:
        """Look up metadata for each taggable object in ``objects``.

        Delegates to :meth:`Workspace.autotag`.
        """
        self._workspace.autotag(objects)

    def remove_files(self, files: Iterable[File], from_parent: bool = True) -> None:
        """Remove ``files`` from the working set.

        Delegates to :meth:`Workspace.remove_files`.
        """
        self._workspace.remove_files(files, from_parent=from_parent)

    def remove_album(self, album: Album) -> None:
        """Remove ``album`` from the working set.

        Delegates to :meth:`Workspace.remove_album`.
        """
        self._workspace.remove_album(album)

    def remove_nat(self, track: NonAlbumTrack) -> None:
        """Remove the non-album track ``track`` from the working set.

        Delegates to :meth:`Workspace.remove_nat`.
        """
        self._workspace.remove_nat(track)

    def remove_cluster(self, cluster: Cluster) -> None:
        """Remove ``cluster`` from the working set.

        Delegates to :meth:`Workspace.remove_cluster`.
        """
        self._workspace.remove_cluster(cluster)

    def remove(self, objects: Iterable[Item]) -> None:
        """Remove ``objects`` (files, tracks, albums, clusters) from the set.

        Delegates to :meth:`Workspace.remove`.
        """
        self._workspace.remove(objects)

    def trash_files(self, files: Iterable[File]) -> None:
        """Move ``files`` to the system trash and remove them from the set.

        Delegates to :meth:`Workspace.trash_files`.
        """
        self._workspace.trash_files(files)

    def save(self, objects: Iterable[IterableFiles]) -> None:
        """Save every file reachable from ``objects`` to disk.

        Delegates to :meth:`Workspace.save`.
        """
        self._workspace.save(objects)

    @property
    def use_acoustid(self) -> bool:
        """True when AcoustID is the configured fingerprinting system.

        Delegates to :attr:`Workspace.use_acoustid`.
        """
        return self._workspace.use_acoustid

    def analyze(self, objs: Iterable[IterableFiles]) -> None:
        """Identify files by AcoustID fingerprint (the "Scan" action).

        Delegates to :meth:`Workspace.analyze`.
        """
        self._workspace.analyze(objs)

    def generate_fingerprints(self, objs: Iterable[IterableFiles]) -> None:
        """Compute AcoustID fingerprints for files without matching them.

        Delegates to :meth:`Workspace.generate_fingerprints`.
        """
        self._workspace.generate_fingerprints(objs)


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
