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

"""Session export functionality.

This module handles exporting current session data to a dictionary format,
separating the export logic from other session management concerns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from picard.album import NatAlbum
from picard.config import get_config
from picard.session.constants import SessionConstants
from picard.session.location_detector import LocationDetector
from picard.session.metadata_handler import MetadataHandler
from picard.session.session_data import SessionItemLocation


class SessionExporter:
    """Handles exporting session data from the current Picard state."""

    def __init__(self) -> None:
        """Initialize the session exporter."""
        self.location_detector = LocationDetector()

    def export_session(self, tagger: Any) -> dict[str, Any]:
        """Export current session data to a dictionary.

        Parameters
        ----------
        tagger : Any
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
            - unmatched_albums: List of album IDs that are loaded but have no files matched

        Notes
        -----
        Only user-visible tags are exported, internal tags (starting with ~) are excluded.
        The function captures manual metadata overrides made in the UI.
        Unmatched albums are preserved so they can be restored even when no files are matched to them.
        """
        config = get_config()
        session_data = {
            "version": SessionConstants.SESSION_FORMAT_VERSION,
            "options": self._export_options(config),
            "items": [],
            "album_track_overrides": {},
            "album_overrides": {},
            "unmatched_albums": [],
            "expanded_albums": [],
        }

        # Export file items
        for file in tagger.iter_all_files():
            item = self._export_file_item(file)
            session_data["items"].append(item)

        # Export metadata overrides and unmatched albums
        album_overrides, album_meta_overrides, unmatched_albums = self._export_metadata_overrides(tagger)
        if album_overrides:
            session_data["album_track_overrides"] = album_overrides
        if album_meta_overrides:
            session_data["album_overrides"] = album_meta_overrides
        if unmatched_albums:
            session_data["unmatched_albums"] = unmatched_albums

        # Export UI state (expanded albums)
        expanded_albums = self._export_ui_state(tagger)
        if expanded_albums:
            session_data["expanded_albums"] = expanded_albums

        return session_data

    def _export_ui_state(self, tagger: Any) -> list[str]:
        """Export UI expansion state for albums in album view.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.

        Returns
        -------
        list[str]
            List of album IDs whose items are expanded in the album view.
        """
        expanded: list[str] = []
        for album in tagger.albums.values():
            ui_item = getattr(album, "ui_item", None)
            if ui_item is not None and ui_item.isExpanded():
                expanded.append(album.id)
        return expanded

    def _export_options(self, config: Any) -> dict[str, bool]:
        """Export configuration options.

        Parameters
        ----------
        config : Any
            The Picard configuration object.

        Returns
        -------
        dict[str, bool]
            Dictionary containing the relevant configuration options.
        """
        return {
            "rename_files": bool(config.setting["rename_files"]),
            "move_files": bool(config.setting["move_files"]),
            "dont_write_tags": bool(config.setting["dont_write_tags"]),
        }

    def _export_file_item(self, file: Any) -> dict[str, Any]:
        """Export a single file item.

        Parameters
        ----------
        file : Any
            The file object to export.

        Returns
        -------
        dict[str, Any]
            Dictionary containing the file item data.
        """
        loc = self.location_detector.detect(file)
        entry = {
            "file_path": str(Path(file.filename)),
            "location": self._serialize_location(loc),
        }

        # Persist unsaved tag changes as deltas vs base metadata
        if not file.is_saved():
            parent = getattr(file, "parent_item", None)
            base_md = None
            # If the file is under a track, diff against the track's scripted metadata (user-visible basis)
            if parent is not None and hasattr(parent, "album"):
                base_md = getattr(parent, "scripted_metadata", getattr(parent, "metadata", None))
            # Otherwise, diff against the file's original on-disk metadata
            if base_md is None:
                base_md = getattr(file, "orig_metadata", None)

            if base_md is not None:
                diff = file.metadata.diff(base_md)
                delta_tags = {
                    k: MetadataHandler.as_list(v)
                    for k, v in diff.rawitems()
                    if k not in SessionConstants.EXCLUDED_OVERRIDE_TAGS
                    and not str(k).startswith(SessionConstants.INTERNAL_TAG_PREFIX)
                }
                if delta_tags:
                    entry["metadata"] = {"tags": delta_tags}

        return entry

    def _serialize_location(self, location: SessionItemLocation) -> dict[str, Any]:
        """Serialize a location object to a dictionary.

        Parameters
        ----------
        location : SessionItemLocation
            The location object to serialize.

        Returns
        -------
        dict[str, Any]
            Dictionary containing the location data.
        """
        return {
            k: v
            for k, v in {
                "type": location.type,
                "album_id": location.album_id,
                "recording_id": location.recording_id,
                "cluster_title": location.cluster_title,
                "cluster_artist": location.cluster_artist,
            }.items()
            if v is not None
        }

    def _export_metadata_overrides(
        self, tagger: Any
    ) -> tuple[dict[str, dict[str, dict[str, list[Any]]]], dict[str, dict[str, list[Any]]], list[str]]:
        """Export metadata overrides for albums and tracks.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.

        Returns
        -------
        tuple[dict, dict, list]
            Tuple containing (album_track_overrides, album_overrides, unmatched_albums).
        """
        album_overrides: dict[str, dict[str, dict[str, list[Any]]]] = {}
        album_meta_overrides: dict[str, dict[str, list[Any]]] = {}
        unmatched_albums: list[str] = []

        # Get all album IDs that have files matched to them
        albums_with_files = set()
        for file in tagger.iter_all_files():
            if hasattr(file, 'parent_item') and file.parent_item:
                if hasattr(file.parent_item, 'album') and file.parent_item.album:
                    albums_with_files.add(file.parent_item.album.id)

        for album in tagger.albums.values():
            if isinstance(album, NatAlbum):
                continue

            # Check if this album has any files matched to it
            has_files = album.id in albums_with_files

            # Album-level diffs vs orig_metadata
            album_diff = album.metadata.diff(album.orig_metadata)
            if album_diff:
                album_meta_overrides[album.id] = {
                    k: MetadataHandler.as_list(v)
                    for k, v in album_diff.rawitems()
                    if k not in SessionConstants.EXCLUDED_OVERRIDE_TAGS
                }

            # Track-level overrides
            overrides_for_album: dict[str, dict[str, list[Any]]] = {}
            for track in album.tracks:
                # The difference to scripted_metadata are user edits made in UI
                diff = track.metadata.diff(track.scripted_metadata)
                if diff:
                    overrides_for_album[track.id] = {
                        k: MetadataHandler.as_list(v)
                        for k, v in diff.rawitems()
                        if k not in SessionConstants.EXCLUDED_OVERRIDE_TAGS
                    }

            if overrides_for_album:
                album_overrides[album.id] = overrides_for_album

            # If album has no files matched and no overrides, it's an unmatched album
            if not has_files and not album_diff and not overrides_for_album:
                unmatched_albums.append(album.id)

        return album_overrides, album_meta_overrides, unmatched_albums
