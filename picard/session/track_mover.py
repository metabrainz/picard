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

"""Track movement functionality for session management.

This module handles moving files to their designated tracks when loading sessions,
separating the complex file-to-track movement logic from other concerns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from picard.album import Album
from picard.file import File
from picard.session.constants import SessionConstants
from picard.session.retry_helper import RetryHelper


class TrackMover:
    """Handles moving files to their target tracks."""

    def __init__(self, tagger: Any) -> None:
        """Initialize the track mover.

        Parameters
        ----------
        tagger : Any
            The Picard tagger instance.
        """
        self.tagger = tagger

    def move_files_to_tracks(self, album: Album, track_specs: list[tuple[Path, str]]) -> None:
        """Move files to their designated tracks when ready.

        Parameters
        ----------
        album : Album
            The album containing the tracks.
        track_specs : list[tuple[Path, str]]
            List of (file_path, recording_id) tuples to move.

        Notes
        -----
        This method schedules file moves when both the file and track are ready.
        It uses the retry helper to wait for proper conditions.
        """

        def run_when_album_ready() -> None:
            for fpath, rid in track_specs:
                self._schedule_move(fpath, rid, album)

        album.run_when_loaded(run_when_album_ready)

    def _schedule_move(self, fpath: Path, recording_id: str, album: Album) -> None:
        """Schedule a file move when both file and track are ready.

        Parameters
        ----------
        fpath : Path
            The file path to move.
        recording_id : str
            The recording ID of the target track.
        album : Album
            The album containing the track.
        """

        def attempt_move() -> None:
            file = self.tagger.files.get(str(fpath))
            if not file or file.state == File.PENDING:
                return

            rec_to_track = {t.id: t for t in album.tracks}
            track = rec_to_track.get(recording_id)
            if track is None:
                return

            file.move(track)

        def is_ready() -> bool:
            file = self.tagger.files.get(str(fpath))
            if not file or file.state == File.PENDING:
                return False

            rec_to_track = {t.id: t for t in album.tracks}
            track = rec_to_track.get(recording_id)
            return track is not None

        RetryHelper.retry_until(
            condition_fn=is_ready, action_fn=attempt_move, delay_ms=SessionConstants.FAST_RETRY_DELAY_MS
        )

    def move_file_to_nat(self, fpath: Path, recording_id: str) -> None:
        """Move a file to NAT (Non-Album Track) when ready.

        Parameters
        ----------
        fpath : Path
            The file path to move.
        recording_id : str
            The recording ID for the NAT.
        """

        def attempt_nat_move() -> None:
            file = self.tagger.files.get(str(fpath))
            if not file or file.state == File.PENDING:
                return
            self.tagger.move_file_to_nat(file, recording_id)

        def is_file_ready() -> bool:
            file = self.tagger.files.get(str(fpath))
            return file is not None and file.state != File.PENDING

        RetryHelper.retry_until(
            condition_fn=is_file_ready, action_fn=attempt_nat_move, delay_ms=SessionConstants.DEFAULT_RETRY_DELAY_MS
        )
