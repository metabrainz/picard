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

"""Session management for Picard.

This module provides functionality to save and restore Picard sessions,
including file locations, metadata overrides, and configuration options.
Sessions allow users to preserve their work state across application restarts.

Classes
-------
SessionItemLocation
    Dataclass representing the location of a file within a session.

Functions
---------
export_session
    Export current session data to a dictionary.
save_session_to_path
    Save session data to a file.
load_session_from_path
    Load session data from a file.

Notes
-----
Session files use the .mbps extension and contain JSON data with version
information, options, file locations, and metadata overrides.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from PyQt6 import QtCore

from picard.album import Album, NatAlbum
from picard.cluster import Cluster, UnclusteredFiles
from picard.config import get_config
from picard.file import File
from picard.metadata import Metadata


SESSION_FILE_EXTENSION = ".mbps"


@dataclass(frozen=True)
class SessionItemLocation:
    """Location information for a file within a session.

    Parameters
    ----------
    type : str
        The type of location (e.g., "unclustered", "track", "album_unmatched", "cluster", "nat").
    album_id : str | None, optional
        The MusicBrainz album ID if the file is associated with an album.
    recording_id : str | None, optional
        The MusicBrainz recording ID if the file is associated with a specific track.
    cluster_title : str | None, optional
        The cluster title for files in a cluster.
    cluster_artist : str | None, optional
        The cluster artist for files in a cluster.
    """

    type: str
    album_id: str | None = None
    recording_id: str | None = None
    cluster_title: str | None = None
    cluster_artist: str | None = None


def _serialize_metadata_for_file(file: File) -> dict[str, list[Any]]:
    # Store only user-visible tags, skip internal (~) ones
    tags: dict[str, list[Any]] = {}
    for key, values in file.metadata.rawitems():
        if key.startswith("~") or key == "length":
            continue
        # Copy as list to be JSON serializable
        tags[key] = list(values)
    return tags


def _deserialize_metadata(tags: dict[str, list[Any]]) -> Metadata:
    md = Metadata()
    for key, values in tags.items():
        md[key] = values
    return md


def _as_list(values: Any) -> list[Any]:
    if isinstance(values, (list, tuple)):
        return list(values)
    # Treat scalars / strings as single-value list
    return [values]


def _detect_location(file: File) -> SessionItemLocation:
    parent = file.parent_item
    if parent is None:
        return SessionItemLocation(type="unclustered")

    # File under a track (right pane)
    if hasattr(parent, "album") and isinstance(parent.album, Album):
        if isinstance(parent.album, NatAlbum):
            # NAT special handling
            return SessionItemLocation(type="nat", recording_id=parent.id)
        # Track placement
        if hasattr(parent, "id"):
            return SessionItemLocation(type="track", album_id=parent.album.id, recording_id=parent.id)
        # Fallback to album unmatched
        return SessionItemLocation(type="album_unmatched", album_id=parent.album.id)

    # Unmatched files inside an album
    if isinstance(parent, Cluster) and parent.related_album:
        return SessionItemLocation(type="album_unmatched", album_id=parent.related_album.id)

    # Left pane cluster
    if isinstance(parent, Cluster):
        if isinstance(parent, UnclusteredFiles):
            return SessionItemLocation(type="unclustered")
        return SessionItemLocation(
            type="cluster",
            cluster_title=str(parent.metadata["album"]),
            cluster_artist=str(parent.metadata["albumartist"]),
        )

    # Default
    return SessionItemLocation(type="unclustered")


def export_session(tagger) -> dict[str, Any]:
    """Export current session data to a dictionary.

    Parameters
    ----------
    tagger
        The Picard tagger instance to export session data from.

    Returns
    -------
    dict[str, Any]
        Dictionary containing session data with the following keys:
        - version: Session format version (currently 1)
        - options: Configuration options (rename_files, move_files, dont_write_tags)
        - items: List of file items with paths and locations
        - album_track_overrides: Track-level metadata overrides per album
        - album_overrides: Album-level metadata overrides

    Notes
    -----
    Only user-visible tags are exported, internal tags (starting with ~) are excluded.
    The function captures manual metadata overrides made in the UI.
    """
    config = get_config()
    session: dict[str, Any] = {
        "version": 1,
        "options": {
            "rename_files": bool(config.setting["rename_files"]),
            "move_files": bool(config.setting["move_files"]),
            "dont_write_tags": bool(config.setting["dont_write_tags"]),
        },
        "items": [],
        "album_track_overrides": {},  # album_id -> recording_id -> {tag: [values]}
        "album_overrides": {},  # album_id -> {tag: [values]}
    }

    for file in tagger.iter_all_files():
        loc = _detect_location(file)
        entry: dict[str, Any] = {
            "file_path": str(Path(file.filename)),
            "location": {
                k: v
                for k, v in {
                    "type": loc.type,
                    "album_id": loc.album_id,
                    "recording_id": loc.recording_id,
                    "cluster_title": loc.cluster_title,
                    "cluster_artist": loc.cluster_artist,
                }.items()
                if v is not None
            },
        }
        # Persist unsaved tag changes
        if not file.is_saved():
            entry["metadata"] = {"tags": _serialize_metadata_for_file(file)}
        session["items"].append(entry)

    # Capture manual track-level overrides per album/track
    album_overrides: dict[str, dict[str, dict[str, list[Any]]]] = {}
    # Capture album-level overrides (e.g. albumartist)
    album_meta_overrides: dict[str, dict[str, list[Any]]] = {}
    EXCLUDED_OVERRIDE_TAGS = {"length", "~length"}
    for album in tagger.albums.values():
        if isinstance(album, NatAlbum):
            continue
        overrides_for_album: dict[str, dict[str, list[Any]]] = {}
        # Album-level diffs vs orig_metadata
        album_diff = album.metadata.diff(album.orig_metadata)
        if album_diff:
            album_meta_overrides[album.id] = {
                k: _as_list(v) for k, v in album_diff.rawitems() if k not in EXCLUDED_OVERRIDE_TAGS
            }
        for track in album.tracks:
            # The difference to scripted_metadata are user edits made in UI
            diff = track.metadata.diff(track.scripted_metadata)
            if diff:
                # Convert to JSON-friendly dict; ensure values are lists of strings
                overrides_for_album[track.id] = {
                    k: _as_list(v) for k, v in diff.rawitems() if k not in EXCLUDED_OVERRIDE_TAGS
                }
        if overrides_for_album:
            album_overrides[album.id] = overrides_for_album
    if album_overrides:
        session["album_track_overrides"] = album_overrides
    if album_meta_overrides:
        session["album_overrides"] = album_meta_overrides
    return session


def save_session_to_path(tagger, path: str | Path) -> None:
    """Save session data to a file.

    Parameters
    ----------
    tagger
        The Picard tagger instance to save session data from.
    path : str | Path
        The file path to save the session to. If the extension is not .mbps,
        it will be automatically added.

    Notes
    -----
    The session is saved as JSON with UTF-8 encoding and 2-space indentation.
    If the file already exists, it will be overwritten.
    """
    p = Path(path)
    if p.suffix.lower() != SESSION_FILE_EXTENSION:
        p = p.with_suffix(SESSION_FILE_EXTENSION)
    data = export_session(tagger)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _apply_saved_metadata_if_any(tagger, file_path_to_md: dict[Path, Metadata]) -> None:
    # Try applying metadata after files have loaded
    pending: list[Path] = []
    for fpath, md in file_path_to_md.items():
        file = tagger.files.get(str(fpath))
        if not file or file.state == File.PENDING:
            pending.append(fpath)
            continue
        with suppress(OSError, ValueError, AttributeError, KeyError):
            # Preserve computed length from current metadata
            md.length = file.metadata.length or file.orig_metadata.length
            file.copy_metadata(md)
            file.update()

    if pending:
        QtCore.QTimer.singleShot(
            200, lambda: _apply_saved_metadata_if_any(tagger, {p: file_path_to_md[p] for p in pending})
        )


def load_session_from_path(tagger, path: str | Path) -> None:
    """Load session data from a file.

    Parameters
    ----------
    tagger
        The Picard tagger instance to load session data into.
    path : str | Path
        The file path to load the session from.

    Notes
    -----
    This function will:
    - Clear the current session
    - Restore configuration options
    - Load files to their original locations (unclustered, clusters, albums, tracks)
    - Apply saved metadata overrides
    - Handle NAT (Non-Album Track) items

    The function respects the session_safe_restore configuration setting
    to prevent overwriting unsaved changes.
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    # Close current session
    tagger.clear_session()
    # Respect user setting for safe restore (defaults enabled)
    if get_config().setting['session_safe_restore']:
        tagger._restoring_session = True

    # Restore quick option states (affect menu toggles)
    opts = data.get("options", {})
    config = get_config()
    config.setting["rename_files"] = bool(opts.get("rename_files", config.setting["rename_files"]))
    config.setting["move_files"] = bool(opts.get("move_files", config.setting["move_files"]))
    config.setting["dont_write_tags"] = bool(opts.get("dont_write_tags", config.setting["dont_write_tags"]))

    items = data.get("items", [])
    track_overrides_by_album: dict[str, dict[str, dict[str, list[Any]]]] = data.get("album_track_overrides", {})
    album_meta_overrides: dict[str, dict[str, list[Any]]] = data.get("album_overrides", {})

    # Group by placement target to leverage Tagger.add_files batching
    by_unclustered: list[Path] = []
    by_cluster: dict[tuple[str, str], list[Path]] = {}
    by_album: dict[str, dict[str, list[Path]]] = {}
    nat_items: list[tuple[Path, str]] = []  # (path, recording_id)

    # Collect metadata to apply after loading
    metadata_by_path: dict[Path, Metadata] = {}

    for it in items:
        fpath = Path(it["file_path"]).expanduser()
        loc = it.get("location", {})
        ltype = str(loc.get("type", "unclustered"))
        md = it.get("metadata", {})
        if "tags" in md:
            tags = {k: _as_list(v) for k, v in md["tags"].items()}
            metadata_by_path[fpath] = _deserialize_metadata(tags)  # type: ignore[arg-type]

        if ltype == "unclustered":
            by_unclustered.append(fpath)
        elif ltype == "cluster":
            key = (str(loc.get("cluster_title", "")), str(loc.get("cluster_artist", "")))
            by_cluster.setdefault(key, []).append(fpath)
        elif ltype in {"album_unmatched", "track"}:
            album_id = str(loc.get("album_id"))
            entry = by_album.setdefault(album_id, {"unmatched": [], "tracks": []})
            if ltype == "album_unmatched":
                entry["unmatched"].append(fpath)
            else:
                entry["tracks"].append((fpath, str(loc.get("recording_id"))))
        elif ltype == "nat":
            nat_items.append((fpath, str(loc.get("recording_id"))))
        else:
            by_unclustered.append(fpath)

    # Helper to convert Paths to strings for Tagger.add_files
    def _to_strs(paths: list[Path]) -> list[str]:
        return [str(p) for p in paths]

    # Load albums upfront
    loaded_albums: dict[str, Album] = {}
    for album_id in by_album.keys() | set(track_overrides_by_album.keys()) | set(album_meta_overrides.keys()):
        loaded_albums[album_id] = tagger.load_album(album_id)

    # Add unclustered files
    if by_unclustered:
        tagger.add_files(_to_strs(by_unclustered), target=tagger.unclustered_files)

    # Add cluster files
    for (title, artist), paths in by_cluster.items():
        cluster = tagger.load_cluster(title, artist)
        tagger.add_files(_to_strs(paths), target=cluster)

    # Add album files (both unmatched and those destined for tracks)
    for album_id, groups in by_album.items():
        album = loaded_albums[album_id]
        all_paths: list[Path] = list(groups["unmatched"]) + [fp for (fp, _rid) in groups["tracks"]]
        if all_paths:
            tagger.add_files(_to_strs(all_paths), target=album.unmatched_files)

        # Ensure album node is expanded/visible early
        def _ensure_album_visible(a: Album):
            def _run():
                a.update(update_tracks=True)
                if a.ui_item:
                    a.ui_item.setExpanded(True)

            a.run_when_loaded(_run)

        _ensure_album_visible(album)

        # After album is loaded move files to their tracks, waiting for files to be ready
        def _move_when_loaded(album: Album, track_specs: list[tuple[Path, str]]):
            def _attempt_move(fpath: Path, rid: str):
                file = tagger.files.get(str(fpath))
                if not file or file.state == File.PENDING:
                    QtCore.QTimer.singleShot(150, lambda: _attempt_move(fpath, rid))
                    return
                rec_to_track = {t.id: t for t in album.tracks}
                track = rec_to_track.get(rid)
                if track is None:
                    # Album not ready yet, retry
                    QtCore.QTimer.singleShot(150, lambda: _attempt_move(fpath, rid))
                    return
                file.move(track)

            def _run():
                for fpath, rid in track_specs:
                    _attempt_move(fpath, rid)

            album.run_when_loaded(_run)

        if groups["tracks"]:
            _move_when_loaded(album, groups["tracks"])  # type: ignore[arg-type]

    # Apply manual track-level overrides after album data has loaded
    for album_id, track_overrides in track_overrides_by_album.items():
        album = loaded_albums.get(album_id)
        if not album:
            continue

        def _apply_overrides(a: Album, overrides: dict[str, dict[str, list[Any]]]):
            def _run():
                track_by_id = {t.id: t for t in a.tracks}
                for track_id, tags in overrides.items():
                    tr = track_by_id.get(track_id)
                    if not tr:
                        continue
                    # Apply overrides to track metadata so columns reflect user edits
                    for tag, values in tags.items():
                        # Never override computed lengths
                        if tag in {"length", "~length"}:
                            continue
                        tr.metadata[tag] = _as_list(values)
                    tr.update()

            a.run_when_loaded(_run)

        _apply_overrides(album, track_overrides)

    # Apply album-level overrides after album data has loaded
    for album_id, overrides in album_meta_overrides.items():
        album = loaded_albums.get(album_id)
        if not album:
            continue

        def _apply_album_overrides(a: Album, tags: dict[str, list[Any]]):
            def _run():
                for tag, values in tags.items():
                    a.metadata[tag] = _as_list(values)
                a.update(update_tracks=False)

            a.run_when_loaded(_run)

        _apply_album_overrides(album, overrides)

    # Handle NAT items
    for fpath, rid in nat_items:

        def _move_nat(path: Path = fpath, recording_id: str = rid):
            file = tagger.files.get(str(path))
            if not file or file.state == File.PENDING:
                QtCore.QTimer.singleShot(200, lambda: _move_nat(path, recording_id))
                return
            tagger.move_file_to_nat(file, recording_id)

        _move_nat()

    # Apply metadata edits after load completes (retry until loaded)
    if metadata_by_path:
        QtCore.QTimer.singleShot(200, lambda: _apply_saved_metadata_if_any(tagger, metadata_by_path))

    # Unset restoring flag when all file loads and web requests finish
    def _unset_when_idle():
        if not get_config().setting['session_safe_restore']:
            return
        if tagger._pending_files_count == 0 and not tagger.webservice.num_pending_web_requests:
            tagger._restoring_session = False
        else:
            QtCore.QTimer.singleShot(200, _unset_when_idle)

    QtCore.QTimer.singleShot(200, _unset_when_idle)
