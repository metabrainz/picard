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

"""Metadata handling for session management.

This module provides utilities for serializing and deserializing metadata
for session files, with proper error handling and validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from picard.file import File
from picard.log import log
from picard.metadata import Metadata
from picard.session.constants import SessionConstants


class MetadataHandler:
    """Handles metadata serialization and deserialization for sessions."""

    @staticmethod
    def serialize_metadata_for_file(file: File) -> dict[str, list[Any]]:
        """Serialize metadata for a file, excluding internal tags.

        Parameters
        ----------
        file : File
            The file to serialize metadata for.

        Returns
        -------
        dict[str, list[Any]]
            Dictionary containing serialized metadata tags.

        Notes
        -----
        Only user-visible tags are serialized, internal tags (starting with ~)
        and length are excluded.
        """
        tags: dict[str, list[Any]] = {}
        for key, values in file.metadata.rawitems():
            if key.startswith(SessionConstants.INTERNAL_TAG_PREFIX) or key == "length":
                continue
            # Copy as list to be JSON serializable
            tags[key] = list(values)
        return tags

    @staticmethod
    def deserialize_metadata(tags: dict[str, list[Any]]) -> Metadata:
        """Deserialize metadata from a dictionary.

        Parameters
        ----------
        tags : dict[str, list[Any]]
            Dictionary containing serialized metadata tags.

        Returns
        -------
        Metadata
            The deserialized metadata object.
        """
        md = Metadata()
        for key, values in tags.items():
            md[key] = values
        return md

    @staticmethod
    def as_list(values: Any) -> list[Any]:
        """Convert values to a list format.

        Parameters
        ----------
        values : Any
            Values to convert to list format.

        Returns
        -------
        list[Any]
            List representation of the values.

        Notes
        -----
        Treats scalars/strings as single-value lists for consistency.
        """
        if isinstance(values, (list, tuple)):
            return list(values)
        # Treat scalars / strings as single-value list
        return [values]

    @staticmethod
    def safe_apply_metadata(file: File, metadata: Metadata) -> bool:
        """Safely apply metadata to a file with proper error handling.

        Parameters
        ----------
        file : File
            The file to apply metadata to.
        metadata : Metadata
            The metadata to apply.

        Returns
        -------
        bool
            True if metadata was applied successfully, False otherwise.

        Notes
        -----
        This method provides specific error handling instead of broad exception
        suppression, with proper logging for debugging.
        """
        try:
            # Preserve computed length from current metadata
            metadata.length = file.metadata.length or file.orig_metadata.length
            file.copy_metadata(metadata)
            file.update()
            return True
        except (AttributeError, KeyError) as e:
            log.warning(f"Failed to apply metadata to {file.filename}: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error applying metadata: {e}")
            return False

    @staticmethod
    def apply_saved_metadata_if_any(tagger: Any, file_path_to_md: dict[Path, Metadata]) -> None:
        """Apply saved metadata to files when they are ready.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.
        file_path_to_md : dict[Path, Metadata]
            Mapping of file paths to their metadata.

        Notes
        -----
        This method retries applying metadata until files are loaded and ready.
        Files that are still pending will be retried later.
        """
        from picard.session.retry_helper import RetryHelper

        pending: list[Path] = []
        for fpath, md in file_path_to_md.items():
            file = tagger.files.get(str(fpath))
            if not file or file.state == File.PENDING:
                pending.append(fpath)
                continue

            if not MetadataHandler.safe_apply_metadata(file, md):
                # If metadata application failed, we might want to retry
                pending.append(fpath)

        if pending:
            RetryHelper.retry_until(
                condition_fn=lambda: len(pending) == 0,
                action_fn=lambda: MetadataHandler.apply_saved_metadata_if_any(
                    tagger, {p: file_path_to_md[p] for p in pending}
                ),
                delay_ms=SessionConstants.DEFAULT_RETRY_DELAY_MS,
            )
