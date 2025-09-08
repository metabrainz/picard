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
import json
from pathlib import Path
from typing import Any

from PyQt6 import QtCore

from picard.album import Album
from picard.config import get_config
from picard.i18n import gettext as _
from picard.session.constants import SessionConstants
from picard.session.metadata_handler import MetadataHandler
from picard.session.session_data import AlbumItems, GroupedItems
from picard.session.track_mover import TrackMover


class SessionLoader:
    """Handles loading and restoring Picard sessions."""

    def __init__(self, tagger: Any) -> None:
        """Initialize the session loader.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.
        """
        self.tagger = tagger
        self.track_mover = TrackMover(tagger)
        self.loaded_albums: dict[str, Album] = {}
        # Saved UI expansion state from session (None = not provided)
        self._saved_expanded_albums: set[str] | None = None

    def load_from_path(self, path: str | Path) -> None:
        """Main entry point for loading a session.

        Parameters
        ----------
        path : str | Path
            The file path to load the session from.

        Notes
        -----
        This method orchestrates the entire session loading process:
        1. Read and parse the session file
        2. Prepare the session (clear current, set flags)
        3. Restore configuration options
        4. Group items by location type
        5. Load items to their proper locations
        6. Apply metadata overrides
        7. Schedule metadata application
        """
        self._emit_progress("read", details={'path': str(path)})
        data = self._read_session_file(path)
        self._prepare_session(data)
        self._restore_options(data.get('options', {}))
        # Cache saved UI expansion state for later album updates
        self._saved_expanded_albums = set(data.get('expanded_albums', [])) if "expanded_albums" in data else None

        items = data.get('items', [])
        grouped_items = self._group_items_by_location(items)
        metadata_map = self._extract_metadata(items)

        # If mb_cache is provided, try to pre-load albums from cached JSON
        mb_cache = data.get('mb_cache', {})
        if mb_cache:
            self._emit_progress("preload_cache", details={'albums': len(mb_cache)})
            self._preload_albums_from_cache(mb_cache, grouped_items)

        self._emit_progress(
            "load_items",
            details={
                'files': len(grouped_items.unclustered)
                + sum(len(v) for v in grouped_items.by_cluster.values())
                + sum(len(g.unmatched) + len(g.tracks) for g in grouped_items.by_album.values())
            },
        )
        self._load_items(grouped_items)
        self._load_unmatched_albums(data.get('unmatched_albums', []))
        self._emit_progress("apply_overrides")
        self._apply_overrides(data)

        if metadata_map:
            self._schedule_metadata_application(metadata_map)

        # Restore UI state (expanded albums and file view roots)
        self._emit_progress("finalize")
        self._restore_ui_state(data)

    # ----------------------
    # Progress reporting API
    # ----------------------
    def _emit_progress(self, stage: str, details: dict[str, Any] | None = None) -> None:
        # Do not let progress reporting break loading
        with suppress(AttributeError, RuntimeError, TypeError):
            # Forward to main window / status indicator if available
            if hasattr(self.tagger, 'window') and hasattr(self.tagger.window, 'status_indicators'):
                for indicator in self.tagger.window.status_indicators:
                    if hasattr(indicator, 'session_progress'):
                        indicator.session_progress(stage, details or {})
            # Additionally, update status bar text when possible
            if hasattr(self.tagger, 'window') and hasattr(self.tagger.window, 'set_statusbar_message'):
                msg = self._format_stage_message(stage, details)
                if msg:
                    self.tagger.window.set_statusbar_message(msg)

    def _format_stage_message(self, stage: str, details: dict[str, Any] | None) -> str | None:
        def msg_preload(d: dict[str, Any] | None) -> str:
            return _("Preloading albums from cache ({albums})…").format(albums=(d or {}).get('albums', 0))

        def msg_load_items(d: dict[str, Any] | None) -> str:
            return _("Loading files and albums ({files} files)…").format(files=(d or {}).get('files', 0))

        def msg_finalize(_d: dict[str, Any] | None) -> str:
            pending = getattr(self.tagger.webservice, 'num_pending_web_requests', 0)
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

    def _preload_albums_from_cache(self, mb_cache: dict[str, Any], grouped_items: GroupedItems) -> None:
        """Preload albums from embedded MB JSON cache when available.

        Parameters
        ----------
        mb_cache : dict[str, Any]
            Mapping of album IDs to MB release JSON nodes.
        grouped_items : GroupedItems
            Items grouped by location type (used to know which albums are needed).
        """
        needed_album_ids = set(grouped_items.by_album.keys()) | set(mb_cache.keys())
        for album_id in needed_album_ids:
            node = mb_cache.get(album_id)
            if not node:
                continue
            album = self.tagger.albums.get(album_id)
            if not album:
                # Create album instance via normal path but intercept to parse from JSON node
                album = self.tagger.load_album(album_id)
            # If album supports parsing from cached release node, do so
            parse_from_json = getattr(album, '_parse_release', None)
            if callable(parse_from_json):
                # Fall back to normal loading path if parsing fails
                with suppress(KeyError, TypeError, ValueError):
                    parse_from_json(node)
                    album._run_album_metadata_processors()
                    album.update(update_tracks=True)
                    self.loaded_albums[album_id] = album
                    self._ensure_album_visible(album)

    def _read_session_file(self, path: Path) -> dict[str, Any]:
        """Read and parse session file.

        Parameters
        ----------
        path : Path
            The file path to read.

        Returns
        -------
        dict[str, Any]
            The parsed session data.

        Raises
        ------
        json.JSONDecodeError
            If the file contains invalid JSON.
        FileNotFoundError
            If the file does not exist.
        """
        p = Path(path)
        # Detect gzip by magic bytes and decode accordingly
        raw = p.read_bytes()
        if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
            text = gzip.decompress(raw).decode("utf-8")
            return json.loads(text)
        else:
            return json.loads(raw.decode("utf-8"))

    def _prepare_session(self, data: dict[str, Any]) -> None:
        """Prepare the session for loading.

        Parameters
        ----------
        data : dict[str, Any]
            The session data.
        """
        # Close current session
        self.tagger.clear_session()
        # Respect user setting for safe restore (defaults enabled)
        if get_config().setting['session_safe_restore']:
            self.tagger._restoring_session = True

    def _restore_options(self, options: dict[str, Any]) -> None:
        """Restore configuration options.

        Parameters
        ----------
        options : dict[str, Any]
            The options to restore.
        """
        config = get_config()
        config.setting['rename_files'] = bool(options.get('rename_files', config.setting['rename_files']))
        config.setting['move_files'] = bool(options.get('move_files', config.setting['move_files']))
        config.setting['dont_write_tags'] = bool(options.get('dont_write_tags', config.setting['dont_write_tags']))

    def _group_items_by_location(self, items: list[dict[str, Any]]) -> GroupedItems:
        """Group items by their target location.

        Parameters
        ----------
        items : list[dict[str, Any]]
            List of session items.

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

    def _extract_metadata(self, items: list[dict[str, Any]]) -> dict[Path, dict[str, list[Any]]]:
        """Extract metadata from session items.

        Parameters
        ----------
        items : list[dict[str, Any]]
            List of session items.

        Returns
        -------
        dict[Path, dict[str, list[Any]]]
            Mapping of file paths to their metadata tag deltas.
        """
        metadata_by_path: dict[Path, dict[str, list[Any]]] = {}
        for it in items:
            fpath = Path(it['file_path']).expanduser()
            md = it.get('metadata', {})
            if "tags" in md:
                tags = {k: MetadataHandler.as_list(v) for k, v in md['tags'].items()}
                metadata_by_path[fpath] = tags
        return metadata_by_path

    def _load_items(self, grouped_items: GroupedItems) -> None:
        """Load items to their proper locations.

        Parameters
        ----------
        grouped_items : GroupedItems
            Items grouped by location type.
        """
        # Load albums upfront
        self._load_albums(grouped_items)

        # Add unclustered files
        if grouped_items.unclustered:
            self.tagger.add_files([str(p) for p in grouped_items.unclustered], target=self.tagger.unclustered_files)

        # Add cluster files
        for (title, artist), paths in grouped_items.by_cluster.items():
            cluster = self.tagger.load_cluster(title, artist)
            self.tagger.add_files([str(p) for p in paths], target=cluster)

        # Add album files
        self._load_album_files(grouped_items.by_album)

        # Handle NAT items
        for fpath, rid in grouped_items.nat_items:
            self.track_mover.move_file_to_nat(fpath, rid)

    def _load_unmatched_albums(self, unmatched_album_ids: list[str]) -> None:
        """Load albums that have no files matched to them.

        Parameters
        ----------
        unmatched_album_ids : list[str]
            List of album IDs to load.
        """
        for album_id in unmatched_album_ids:
            if album_id not in self.loaded_albums:
                album = self.tagger.load_album(album_id)
                self.loaded_albums[album_id] = album
                # Ensure album becomes visible and expanded once loaded
                self._ensure_album_visible(album)

    def _load_albums(self, grouped_items: GroupedItems) -> None:
        """Load albums that will be needed.

        Parameters
        ----------
        grouped_items : GroupedItems
            Items grouped by location type.
        """
        album_ids = set(grouped_items.by_album.keys())
        for album_id in album_ids:
            self.loaded_albums[album_id] = self.tagger.load_album(album_id)

    def _load_album_files(self, by_album: dict[str, AlbumItems]) -> None:
        """Load files into albums and move them to tracks.

        Parameters
        ----------
        by_album : dict[str, AlbumItems]
            Files grouped by album ID.
        """
        for album_id, groups in by_album.items():
            album = self.loaded_albums[album_id]
            all_paths = list(groups.unmatched) + [fp for (fp, _rid) in groups.tracks]
            if all_paths:
                self.tagger.add_files([str(p) for p in all_paths], target=album.unmatched_files)

            # Ensure album node is expanded/visible early
            self._ensure_album_visible(album)

            # Move files to their tracks
            if groups.tracks:
                self.track_mover.move_files_to_tracks(album, groups.tracks)

    def _ensure_album_visible(self, album: Album) -> None:
        """Ensure album node is expanded and visible.

        Parameters
        ----------
        album : Album
            The album to make visible.
        """

        def run() -> None:
            album.update(update_tracks=True)
            if album.ui_item:
                if self._saved_expanded_albums is not None:
                    album.ui_item.setExpanded(album.id in self._saved_expanded_albums)
                else:
                    album.ui_item.setExpanded(True)

        album.run_when_loaded(run)

    def _restore_ui_state(self, data: dict[str, Any]) -> None:
        """Restore saved UI expansion state.

        Parameters
        ----------
        data : dict[str, Any]
            The session data.
        """
        expanded_albums = set(data.get('expanded_albums', []))

        def set_expansions() -> None:
            # Album view: set expansion for albums we have
            for album_id, album in self.tagger.albums.items():
                ui_item = getattr(album, 'ui_item', None)
                if ui_item is None:
                    continue
                ui_item.setExpanded(album_id in expanded_albums)

            # File view roots: keep default expansion for unmatched / clusters
            # (Optional future: persist these as well.)

        # Delay until after albums finished initial load to avoid toggling too early
        QtCore.QTimer.singleShot(SessionConstants.DEFAULT_RETRY_DELAY_MS, set_expansions)

    def _apply_overrides(self, data: dict[str, Any]) -> None:
        """Apply metadata overrides to albums and tracks.

        Parameters
        ----------
        data : dict[str, Any]
            The session data containing overrides.
        """
        track_overrides_by_album = data.get('album_track_overrides', {})
        album_meta_overrides = data.get('album_overrides', {})

        # Ensure albums referenced by overrides are loaded and visible
        referenced_album_ids = set(track_overrides_by_album.keys()) | set(album_meta_overrides.keys())
        for album_id in referenced_album_ids:
            if album_id not in self.loaded_albums:
                album = self.tagger.load_album(album_id)
                self.loaded_albums[album_id] = album
                self._ensure_album_visible(album)

        # Apply track-level overrides
        for album_id, track_overrides in track_overrides_by_album.items():
            album = self.loaded_albums.get(album_id)
            if album:
                self._apply_track_overrides(album, track_overrides)

        # Apply album-level overrides
        for album_id, overrides in album_meta_overrides.items():
            album = self.loaded_albums.get(album_id)
            if album:
                self._apply_album_overrides(album, overrides)

    def _apply_track_overrides(self, album: Album, overrides: dict[str, dict[str, list[Any]]]) -> None:
        """Apply track-level metadata overrides.

        Parameters
        ----------
        album : Album
            The album containing the tracks.
        overrides : dict[str, dict[str, list[Any]]]
            Track overrides by track ID.
        """

        def run() -> None:
            track_by_id = {t.id: t for t in album.tracks}
            for track_id, tags in overrides.items():
                tr = track_by_id.get(track_id)
                if not tr:
                    continue
                # Apply overrides to track metadata so columns reflect user edits
                for tag, values in tags.items():
                    # Never override computed lengths
                    if tag in SessionConstants.EXCLUDED_OVERRIDE_TAGS:
                        continue
                    tr.metadata[tag] = MetadataHandler.as_list(values)
                tr.update()

        album.run_when_loaded(run)

    def _apply_album_overrides(self, album: Album, overrides: dict[str, list[Any]]) -> None:
        """Apply album-level metadata overrides.

        Parameters
        ----------
        album : Album
            The album to apply overrides to.
        overrides : dict[str, list[Any]]
            Album-level overrides.
        """

        def run() -> None:
            for tag, values in overrides.items():
                album.metadata[tag] = MetadataHandler.as_list(values)
            album.update(update_tracks=False)

        album.run_when_loaded(run)

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
