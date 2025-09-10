# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Session loading functionality.

This module handles loading and restoring Picard sessions from files,
breaking down the complex loading logic into focused, manageable components.
"""

from __future__ import annotations

from contextlib import suppress
import gzip
from pathlib import Path
from typing import Any, Protocol

import yaml

from PyQt6 import QtCore

from picard.album import Album
from picard.config import get_config
from picard.const.defaults import EXCLUDED_OVERRIDE_TAGS
from picard.i18n import gettext as _
from picard.metadata import Metadata
from picard.session.constants import SessionConstants
from picard.session.metadata_handler import MetadataHandler
from picard.session.session_data import AlbumItems, GroupedItems
from picard.session.track_mover import TrackMover


class ProgressReporter(Protocol):
    """Protocol for emitting session loading progress updates."""

    def emit(self, stage: str, details: dict[str, Any] | None = None) -> None:  # pragma: no cover - interface
        """Emit a progress update for a given stage.

        Parameters
        ----------
        stage : str
            Identifier of the current stage.
        details : dict[str, Any] | None, optional
            Additional details for the stage, by default None.
        """
        ...


class TaggerProgressReporter:
    """Progress reporter that routes updates to the Picard UI when available."""

    def __init__(self, tagger: Any) -> None:
        self._tagger = tagger

    def emit(self, stage: str, details: dict[str, Any] | None = None) -> None:
        # Avoid letting UI progress errors break loading flow
        with suppress(AttributeError, RuntimeError, TypeError):
            # Forward to status indicators if present
            if hasattr(self._tagger, 'window') and hasattr(self._tagger.window, 'status_indicators'):
                for indicator in self._tagger.window.status_indicators:
                    if hasattr(indicator, 'session_progress'):
                        indicator.session_progress(stage, details or {})

            # Additionally update statusbar text
            if hasattr(self._tagger, 'window') and hasattr(self._tagger.window, 'set_statusbar_message'):
                msg = self._format_stage_message(stage, details)
                if msg:
                    self._tagger.window.set_statusbar_message(msg)

    def _format_stage_message(self, stage: str, details: dict[str, Any] | None) -> str | None:
        def msg_preload(d: dict[str, Any] | None) -> str:
            return _("Preloading albums from cache ({albums})…").format(albums=(d or {}).get('albums', 0))

        def msg_load_items(d: dict[str, Any] | None) -> str:
            return _("Loading files and albums ({files} files)…").format(files=(d or {}).get('files', 0))

        def msg_finalize(details_unused: dict[str, Any] | None) -> str:
            pending = getattr(self._tagger.webservice, 'num_pending_web_requests', 0)
            if pending:
                return _("Waiting on network ({requests} requests)…").format(requests=pending)
            return _("Finalizing…")

        dispatch: dict[str, Any] = {
            'read': _("Reading session…"),
            'apply_overrides': _("Applying overrides…"),
            'preload_cache': msg_preload,
            'load_items': msg_load_items,
            'finalize': msg_finalize,
        }

        entry = dispatch.get(stage)
        if entry is None:
            return None
        return entry(details) if callable(entry) else entry


class SessionFileReader:
    """Read and parse session files (YAML or gzipped YAML)."""

    def read(self, path: str | Path) -> dict[str, Any]:
        """Read and parse a session file.

        Parameters
        ----------
        path : str | Path
            Path to the session file.

        Returns
        -------
        dict[str, Any]
            Parsed session data.

        Raises
        ------
        FileNotFoundError
            If the path does not exist.
        yaml.YAMLError
            If the file cannot be parsed as YAML.
        """
        p = Path(path)
        raw = p.read_bytes()
        if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
            text = gzip.decompress(raw).decode("utf-8")
            return yaml.safe_load(text)
        return yaml.safe_load(raw.decode("utf-8"))


class ConfigurationManager:
    """Restore configuration and manage safe-restore lifecycle flags."""

    def prepare_session(self, tagger: Any) -> None:
        """Clear current session and set restoring flag when configured.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.
        """
        tagger.clear_session()
        if get_config().setting['session_safe_restore']:
            tagger._restoring_session = True

    def restore_options(self, options: dict[str, Any]) -> None:
        """Restore core configuration options from the session payload.

        Parameters
        ----------
        options : dict[str, Any]
            Options mapping from the session file.
        """
        config = get_config()
        config.setting['rename_files'] = bool(options.get('rename_files', config.setting['rename_files']))
        config.setting['move_files'] = bool(options.get('move_files', config.setting['move_files']))
        config.setting['dont_write_tags'] = bool(options.get('dont_write_tags', config.setting['dont_write_tags']))


class ItemGrouper:
    """Group raw session items and extract metadata deltas."""

    def group(self, items: list[dict[str, Any]]) -> GroupedItems:
        """Group items by their destination (unclustered, clusters, albums, NAT).

        Parameters
        ----------
        items : list[dict[str, Any]]
            Raw item entries from the session payload.

        Returns
        -------
        GroupedItems
            Items grouped by location type.
        """
        by_unclustered: list[Path] = []
        by_cluster: dict[tuple[str, str], list[Path]] = {}
        by_album: dict[str, AlbumItems] = {}
        nat_items: list[tuple[Path, str]] = []

        for it in items:
            fpath = Path(it['file_path']).expanduser()
            loc = it.get('location', {})
            ltype = str(loc.get('type', SessionConstants.LOCATION_UNCLUSTERED))

            if ltype == SessionConstants.LOCATION_UNCLUSTERED:
                by_unclustered.append(fpath)
            elif ltype == SessionConstants.LOCATION_CLUSTER:
                key = (str(loc.get('cluster_title', "")), str(loc.get('cluster_artist', "")))
                by_cluster.setdefault(key, []).append(fpath)
            elif ltype in {SessionConstants.LOCATION_ALBUM_UNMATCHED, SessionConstants.LOCATION_TRACK}:
                album_id = str(loc.get('album_id'))
                entry = by_album.setdefault(album_id, AlbumItems(unmatched=[], tracks=[]))
                if ltype == SessionConstants.LOCATION_ALBUM_UNMATCHED:
                    entry.unmatched.append(fpath)
                else:
                    entry.tracks.append((fpath, str(loc.get('recording_id'))))
            elif ltype == SessionConstants.LOCATION_NAT:
                nat_items.append((fpath, str(loc.get('recording_id'))))
            else:
                by_unclustered.append(fpath)

        return GroupedItems(unclustered=by_unclustered, by_cluster=by_cluster, by_album=by_album, nat_items=nat_items)

    def extract_metadata(self, items: list[dict[str, Any]]) -> dict[Path, dict[str, list[Any]]]:
        """Extract per-path metadata deltas from item entries.

        Parameters
        ----------
        items : list[dict[str, Any]]
            Raw item entries from the session payload.

        Returns
        -------
        dict[Path, dict[str, list[Any]]]
            Mapping of file path to tag delta list.
        """
        metadata_by_path: dict[Path, dict[str, list[Any]]] = {}
        for it in items:
            fpath = Path(it['file_path']).expanduser()
            md = it.get('metadata', {})
            if 'tags' in md:
                tags = {k: MetadataHandler.as_list(v) for k, v in md['tags'].items()}
                metadata_by_path[fpath] = tags
        return metadata_by_path


class UIStateManager:
    """Manage UI-related state such as album expansion and delayed updates."""

    def __init__(self, tagger: Any, default_delay_ms: int) -> None:
        self._tagger = tagger
        self._delay_ms = default_delay_ms

    def ensure_album_visible(self, album: Album, saved_expanded: set[str] | None) -> None:
        """Ensure an album node is visible and expanded according to saved state.

        Parameters
        ----------
        album : Album
            Album whose UI node should be expanded/updated.
        saved_expanded : set[str] | None
            Saved expanded album IDs; if None, expand by default.
        """

        def run() -> None:
            album.update(update_tracks=True)
            if album.ui_item:
                if saved_expanded is not None:
                    album.ui_item.setExpanded(album.id in saved_expanded)
                else:
                    album.ui_item.setExpanded(True)

        album.run_when_loaded(run)

    def apply_expansions_later(self, expanded_albums: set[str]) -> None:
        """Apply album expansion states after a short delay to avoid flicker.

        Parameters
        ----------
        expanded_albums : set[str]
            Album IDs that should be expanded.
        """

        def set_expansions() -> None:
            for album_id, album in self._tagger.albums.items():
                ui_item = getattr(album, 'ui_item', None)
                if ui_item is None:
                    continue
                ui_item.setExpanded(album_id in expanded_albums)

        QtCore.QTimer.singleShot(self._delay_ms, set_expansions)


class AlbumManager:
    """Manage album loading and caching strategies."""

    def __init__(self, tagger: Any, ui_state: UIStateManager) -> None:
        self._tagger = tagger
        self._ui_state = ui_state
        self.loaded_albums: dict[str, Album] = {}
        self._suppress_network: bool = False
        self._saved_expanded_albums: set[str] | None = None

    def configure(self, suppress_network: bool, saved_expanded_albums: set[str] | None) -> None:
        """Set runtime behavior flags for album loading.

        Parameters
        ----------
        suppress_network : bool
            Whether to suppress MB web requests.
        saved_expanded_albums : set[str] | None
            Saved UI expansion state from session.
        """
        self._suppress_network = suppress_network
        self._saved_expanded_albums = saved_expanded_albums

    def preload_from_cache(self, mb_cache: dict[str, Any], grouped_items: GroupedItems) -> None:
        """Preload albums using embedded MB cache data if available."""
        needed_album_ids = set(grouped_items.by_album.keys()) | set(mb_cache.keys())
        for album_id in needed_album_ids:
            node = mb_cache.get(album_id)
            if not node:
                continue
            album = self._tagger.albums.get(album_id)
            if not album:
                album = self._build_from_cache(album_id, node)
            self.loaded_albums[album_id] = album
            self._ui_state.ensure_album_visible(album, self._saved_expanded_albums)
            if not self._suppress_network:
                album.load()

    def load_needed_albums(self, grouped_items: GroupedItems, mb_cache: dict[str, Any]) -> None:
        """Ensure albums referenced by grouped items are available."""
        for album_id in set(grouped_items.by_album.keys()):
            if album_id in self.loaded_albums:
                continue
            node = mb_cache.get(album_id)
            album = self.load_album_with_strategy(album_id, node)
            if album:
                self.loaded_albums[album_id] = album

    def load_unmatched_albums(self, album_ids: list[str], mb_cache: dict[str, Any]) -> None:
        """Load albums that have no files matched to them."""
        for album_id in album_ids:
            if album_id in self.loaded_albums:
                continue
            node = mb_cache.get(album_id)
            album = self.load_album_with_strategy(album_id, node)
            if album:
                self.loaded_albums[album_id] = album

    def load_album_files(self, by_album: dict[str, AlbumItems], track_mover: TrackMover) -> None:
        """Add files to albums and move them to specific tracks as needed."""
        for album_id, groups in by_album.items():
            album = self.loaded_albums[album_id]
            all_paths = list(groups.unmatched) + [fp for (fp, _rid) in groups.tracks]
            if all_paths:
                self._tagger.add_files([str(p) for p in all_paths], target=album.unmatched_files)

            self._ui_state.ensure_album_visible(album, self._saved_expanded_albums)

            if groups.tracks:
                track_mover.move_files_to_tracks(album, groups.tracks)

    def ensure_loaded_for_overrides(self, album_ids: set[str], mb_cache: dict[str, Any]) -> None:
        """Ensure albums referenced by overrides are available and visible."""
        for album_id in album_ids:
            if album_id in self.loaded_albums:
                continue
            node = mb_cache.get(album_id)
            album = self.load_album_with_strategy(album_id, node)
            if album:
                self.loaded_albums[album_id] = album

    def load_album_with_strategy(self, album_id: str, cached_node: dict[str, Any] | None) -> Album | None:
        """Load an album using cache if available and optionally the network.

        Parameters
        ----------
        album_id : str
            The MusicBrainz release ID.
        cached_node : dict[str, Any] | None
            Cached release tree if available.

        Returns
        -------
        Album | None
            The loaded album, or None if suppressed and no cache exists.
        """
        if cached_node is not None:
            album = self._build_from_cache(album_id, cached_node)
            self._ui_state.ensure_album_visible(album, self._saved_expanded_albums)
            if not self._suppress_network:
                album.load()
            return album

        if self._suppress_network:
            return None

        album = self._tagger.load_album(album_id)
        self._ui_state.ensure_album_visible(album, self._saved_expanded_albums)
        return album

    def _build_from_cache(self, album_id: str, node: dict[str, Any]) -> Album:
        """Construct and finalize an album from cached MB data without network."""
        album = self._tagger.albums.get(album_id)
        if not album:
            album = Album(album_id)
            self._tagger.albums[album_id] = album
            if hasattr(self._tagger, 'album_added'):
                self._tagger.album_added.emit(album)

        album.loaded = False
        album.metadata.clear()
        album.genres.clear()
        album._new_metadata = Metadata()
        album._new_tracks = []
        album._requests = max(1, getattr(album, '_requests', 0))

        with suppress(KeyError, TypeError, ValueError):
            album._parse_release(node)
            album._run_album_metadata_processors()
            album._requests -= 1
            album._finalize_loading(error=False)

        return album


class OverrideApplicator:
    """Apply album and track metadata overrides from the session payload."""

    def __init__(self, album_manager: AlbumManager) -> None:
        self._albums = album_manager

    def apply(self, data: dict[str, Any], mb_cache: dict[str, Any]) -> None:
        """Apply overrides, ensuring referenced albums are loaded.

        Parameters
        ----------
        data : dict[str, Any]
            Session data containing overrides.
        mb_cache : dict[str, Any]
            Cached MB data to avoid network when possible.
        """
        track_overrides_by_album = data.get('album_track_overrides', {})
        album_meta_overrides = data.get('album_overrides', {})

        referenced_album_ids = set(track_overrides_by_album.keys()) | set(album_meta_overrides.keys())
        self._albums.ensure_loaded_for_overrides(referenced_album_ids, mb_cache)

        for album_id, track_overrides in track_overrides_by_album.items():
            album = self._albums.loaded_albums.get(album_id)
            if album:
                self._apply_track_overrides(album, track_overrides)

        for album_id, overrides in album_meta_overrides.items():
            album = self._albums.loaded_albums.get(album_id)
            if album:
                self._apply_album_overrides(album, overrides)

    def _apply_track_overrides(self, album: Album, overrides: dict[str, dict[str, list[Any]]]) -> None:
        def run() -> None:
            track_by_id = {t.id: t for t in album.tracks}
            for track_id, tags in overrides.items():
                tr = track_by_id.get(track_id)
                if not tr:
                    continue
                for tag, values in tags.items():
                    if tag in EXCLUDED_OVERRIDE_TAGS:
                        continue
                    tr.metadata[tag] = MetadataHandler.as_list(values)
                tr.update()

        album.run_when_loaded(run)

    def _apply_album_overrides(self, album: Album, overrides: dict[str, list[Any]]) -> None:
        def run() -> None:
            for tag, values in overrides.items():
                album.metadata[tag] = MetadataHandler.as_list(values)
            album.update(update_tracks=False)

        album.run_when_loaded(run)


class SessionLoader:
    """Orchestrate loading and restoring Picard sessions."""

    def __init__(self, tagger: Any) -> None:
        """Initialize the session loader.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.
        """
        self.tagger = tagger
        self._progress: ProgressReporter = TaggerProgressReporter(tagger)
        self._file_reader = SessionFileReader()
        self._config_mgr = ConfigurationManager()
        self._grouper = ItemGrouper()
        self._ui_state = UIStateManager(tagger, SessionConstants.DEFAULT_RETRY_DELAY_MS)
        self._albums = AlbumManager(tagger, self._ui_state)
        self._overrides = OverrideApplicator(self._albums)
        self.track_mover = TrackMover(tagger)
        # Module-level state bound to a single session load
        self._saved_expanded_albums: set[str] | None = None
        self._mb_cache: dict[str, Any] = {}
        self._suppress_mb_requests: bool = False

    @property
    def loaded_albums(self) -> dict[str, Album]:
        """Expose albums loaded during the session.

        Returns
        -------
        dict[str, Album]
            Mapping of MusicBrainz release ID to `Album`.
        """
        return self._albums.loaded_albums

    @loaded_albums.setter
    def loaded_albums(self, value: dict[str, Album]) -> None:
        self._albums.loaded_albums = value

    # Note: Previously exposed internal methods are now encapsulated in
    # dedicated components (SessionFileReader, ConfigurationManager,
    # ItemGrouper, UIStateManager, AlbumManager, OverrideApplicator).

    def load_from_path(self, path: str | Path) -> None:
        """Load and restore a Picard session from file.

        Parameters
        ----------
        path : str | Path
            The file path to load the session from.

        Notes
        -----
        Orchestrates reading the session, restoring configuration, loading
        items and albums, applying overrides, and restoring UI state.
        """
        self._progress.emit("read", details={'path': str(path)})
        data = self._file_reader.read(path)

        self._config_mgr.prepare_session(self.tagger)
        self._config_mgr.restore_options(data.get('options', {}))

        self._suppress_mb_requests = get_config().setting['session_no_mb_requests_on_load']
        self._saved_expanded_albums = set(data.get('expanded_albums', [])) if 'expanded_albums' in data else None
        self._albums.configure(self._suppress_mb_requests, self._saved_expanded_albums)

        items = data.get('items', [])
        grouped_items = self._grouper.group(items)
        metadata_map = self._grouper.extract_metadata(items)

        self._mb_cache = data.get('mb_cache', {})
        if self._mb_cache:
            self._progress.emit("preload_cache", details={'albums': len(self._mb_cache)})
            self._albums.preload_from_cache(self._mb_cache, grouped_items)

        total_files = (
            len(grouped_items.unclustered)
            + sum(len(v) for v in grouped_items.by_cluster.values())
            + sum(len(g.unmatched) + len(g.tracks) for g in grouped_items.by_album.values())
        )
        self._progress.emit("load_items", details={'files': total_files})

        # Load albums for items and place files accordingly
        self._albums.load_needed_albums(grouped_items, self._mb_cache)

        if grouped_items.unclustered:
            self.tagger.add_files([str(p) for p in grouped_items.unclustered], target=self.tagger.unclustered_files)
        for (title, artist), paths in grouped_items.by_cluster.items():
            cluster = self.tagger.load_cluster(title, artist)
            self.tagger.add_files([str(p) for p in paths], target=cluster)
        self._albums.load_album_files(grouped_items.by_album, self.track_mover)

        # NAT items
        for fpath, rid in grouped_items.nat_items:
            self.track_mover.move_file_to_nat(fpath, rid)

        # Unmatched albums
        self._albums.load_unmatched_albums(data.get('unmatched_albums', []), self._mb_cache)

        # Apply overrides
        self._progress.emit("apply_overrides")
        self._overrides.apply(data, self._mb_cache)

        if metadata_map:
            self._schedule_metadata_application(metadata_map)

        # Restore UI state
        self._progress.emit("finalize")
        expanded = set(data.get('expanded_albums', []))
        self._ui_state.apply_expansions_later(expanded)

    # The following block of methods are retained for scheduling and lifecycle.

    def _schedule_metadata_application(self, metadata_map: dict[Path, dict[str, list[Any]]]) -> None:
        """Schedule metadata application after files are loaded.

        Parameters
        ----------
        metadata_map : dict[Path, dict[str, list[Any]]]
            Mapping of file paths to their metadata tag deltas.
        """
        QtCore.QTimer.singleShot(
            SessionConstants.DEFAULT_RETRY_DELAY_MS,
            lambda: MetadataHandler.apply_tag_deltas_if_any(self.tagger, metadata_map),
        )

    def _unset_restoring_flag_when_idle(self) -> None:
        """Unset the restoring flag when all operations are complete.

        Notes
        -----
        This method checks if all file loads and web requests are finished
        before unsetting the session restoring flag.
        """
        if not get_config().setting['session_safe_restore']:
            return

        if self.tagger._pending_files_count == 0 and not self.tagger.webservice.num_pending_web_requests:
            self.tagger._restoring_session = False
        else:
            QtCore.QTimer.singleShot(SessionConstants.DEFAULT_RETRY_DELAY_MS, self._unset_restoring_flag_when_idle)

    def finalize_loading(self) -> None:
        """Finalize the loading process.

        Notes
        -----
        This method should be called after the main loading is complete
        to handle cleanup tasks like unsetting the restoring flag.
        """
        QtCore.QTimer.singleShot(SessionConstants.DEFAULT_RETRY_DELAY_MS, self._unset_restoring_flag_when_idle)
