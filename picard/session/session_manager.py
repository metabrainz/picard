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

This module serves as the main entry point for session operations, delegating
to specialized modules for specific functionality.

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
Session files use the .mbps.gz extension and contain gzip-compressed YAML data
with version information, options, file locations, and metadata overrides.
"""

from __future__ import annotations

import gzip
from pathlib import Path
import tempfile
from typing import Any

import yaml

from picard.session.constants import SessionConstants
from picard.session.session_exporter import SessionExporter
from picard.session.session_loader import SessionLoader


def export_session(tagger: Any) -> dict[str, Any]:
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
    exporter = SessionExporter()
    return exporter.export_session(tagger)


def save_session_to_path(tagger: Any, path: str | Path) -> None:
    """Save session data to a file.

    Parameters
    ----------
    tagger : Any
        The Picard tagger instance to save session data from.
    path : str | Path
        The file path to save the session to. If the extension does not end with
        .mbps.gz, it will be automatically added.

    Notes
    -----
    The session is saved as YAML (UTF-8) and gzip-compressed. If the
    file already exists, it will be overwritten. The write operation is atomic
    to prevent file corruption in case of crashes.
    """
    p = Path(path)
    # Ensure multi-part extension .mbps.gz
    if not str(p).lower().endswith(SessionConstants.SESSION_FILE_EXTENSION):
        p = Path(str(p) + SessionConstants.SESSION_FILE_EXTENSION)

    data = export_session(tagger)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Convert to YAML and gzip-compress to reduce file size
    yaml_text = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    compressed = gzip.compress(yaml_text.encode("utf-8"))

    # Atomic write: write to temporary file first, then rename
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=p.parent, prefix=p.stem + "_", suffix=p.suffix, delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_bytes(compressed)

        # Atomic rename to final destination
        temp_path.replace(p)
    except (OSError, IOError, PermissionError):
        # Clean up temporary file if it exists and rename failed
        if temp_path and temp_path.exists():
            temp_path.unlink()
        raise  # Caller will handle the exception


def load_session_from_path(tagger: Any, path: str | Path) -> None:
    """Load session data from a file.

    Parameters
    ----------
    tagger : Any
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
    loader = SessionLoader(tagger)
    loader.load_from_path(path)
    loader.finalize_loading()
