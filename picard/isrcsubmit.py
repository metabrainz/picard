# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from picard import (
    log,
    tagger_instance,
)
from picard.i18n import N_
from picard.util.isrc import valid_isrc

from picard.ui.enums import MainAction


class ISRCSubmitEntry:
    """Tracks ISRCs from a file that are not yet in MusicBrainz."""

    def __init__(self, recording_id: str, new_isrcs: set[str]):
        self.recording_id = recording_id
        self.new_isrcs = new_isrcs

    @property
    def is_submitted(self) -> bool:
        return not self.new_isrcs


class ISRCSubmitManager:
    """Manages pending ISRC submissions to MusicBrainz.

    Tracks ISRCs found in files that are not yet associated with their
    matched recordings in MusicBrainz.  Provides methods to add, update,
    and remove entries as files are matched/unmatched, and to submit all
    pending ISRCs in a single batch.
    """

    def __init__(self, mb_api):
        self.tagger = tagger_instance()
        self._mb_api = mb_api
        self._entries: dict[object, ISRCSubmitEntry] = {}
        self._last_submitted: dict[str, list[str]] = {}

    def add(self, file, recording_id: str, file_isrcs: list[str], mb_isrcs: list[str]) -> None:
        """Register ISRCs from a file that are not yet in MusicBrainz.

        Args:
            file: The matched file object (used as key).
            recording_id: The MBID of the matched recording.
            file_isrcs: ISRCs found in the file's metadata.
            mb_isrcs: ISRCs already associated with the recording in MB.
        """
        mb_isrcs_set = set(isrc.upper() for isrc in mb_isrcs)
        new_isrcs = set()
        for isrc in file_isrcs:
            normalized = valid_isrc(isrc)
            if normalized and normalized not in mb_isrcs_set:
                new_isrcs.add(normalized)
        if new_isrcs:
            self._entries[file] = ISRCSubmitEntry(recording_id, new_isrcs)
        elif file in self._entries:
            del self._entries[file]
        self._check_unsubmitted()

    def update(self, file, recording_id: str, mb_isrcs: list[str]) -> None:
        """Update recording association for a file.

        Called when a file is re-matched to a different recording.
        Re-evaluates which ISRCs are new for the updated recording.
        """
        entry = self._entries.get(file)
        if entry is None:
            return
        mb_isrcs_set = set(isrc.upper() for isrc in mb_isrcs)
        # Recalculate new ISRCs against the new recording
        new_isrcs = entry.new_isrcs - mb_isrcs_set
        if new_isrcs:
            self._entries[file] = ISRCSubmitEntry(recording_id, new_isrcs)
        else:
            del self._entries[file]
        self._check_unsubmitted()

    def remove(self, file) -> None:
        """Remove a file's pending ISRCs (e.g., when unmatched)."""
        if file in self._entries:
            del self._entries[file]
            self._check_unsubmitted()

    def is_submitted(self, file) -> bool:
        """Check whether a file has any pending (unsubmitted) ISRCs."""
        entry = self._entries.get(file)
        if entry:
            return entry.is_submitted
        return True

    @property
    def unsubmitted_count(self) -> int:
        """Number of files with pending ISRC submissions."""
        return sum(1 for entry in self._entries.values() if not entry.is_submitted)

    def pending_details(self) -> dict[tuple[str, str], list[tuple[str, str, list[str], list[str], bool]]]:
        """Return details for ISRC submissions, grouped by release.

        Returns a dict keyed by (album, albumartist) with values being lists
        of tuples: (track_number, title, existing_isrcs, new_isrcs, submittable),
        sorted by track number. Shows all tracks from affected albums;
        tracks with no pending ISRCs have submittable=False.
        """
        # Collect all albums that have pending entries
        albums = set()
        pending_map: dict[object, set[str]] = {}
        for obj, entry in self._entries.items():
            if not entry.is_submitted:
                pending_map[obj] = entry.new_isrcs
            album = getattr(obj, 'album', None)
            if album:
                albums.add(album)

        by_release: dict[tuple[str, str], list[tuple[str, str, list[str], list[str], bool]]] = {}
        for album in albums:
            album_name = album.metadata.get('album', '')
            albumartist = album.metadata.get('albumartist', '')
            release_key = (album_name, albumartist)
            if release_key not in by_release:
                by_release[release_key] = []
            for track in album.tracks:
                track_number = track.metadata.get('tracknumber', '?')
                title = track.metadata.get('title', '')
                existing_isrcs = track.metadata.getall('isrc')
                new_isrcs = pending_map.get(track, set())
                existing = [isrc for isrc in existing_isrcs if isrc.upper() not in new_isrcs]
                submittable = bool(new_isrcs)
                by_release[release_key].append((track_number, title, existing, sorted(new_isrcs), submittable))
            by_release[release_key].sort(key=lambda x: int(x[0]) if x[0].isdigit() else 999)
        return by_release

    def _pending_isrcs(self, isrcs_to_submit: set[str] | None = None) -> dict[str, list[str]]:
        """Build the submission payload: {recording_id: [isrcs]}.

        Args:
            isrcs_to_submit: If provided, only include these ISRCs.
        """
        result: dict[str, list[str]] = {}
        for entry in self._entries.values():
            if not entry.is_submitted:
                isrcs = entry.new_isrcs
                if isrcs_to_submit is not None:
                    isrcs = isrcs & isrcs_to_submit
                if isrcs:
                    existing = result.get(entry.recording_id, [])
                    existing.extend(sorted(isrcs))
                    result[entry.recording_id] = existing
        return result

    def submit(self, isrcs_to_submit: set[str] | None = None) -> None:
        """Submit pending ISRCs to MusicBrainz.

        Args:
            isrcs_to_submit: If provided, only submit these ISRCs.
        """
        pending = self._pending_isrcs(isrcs_to_submit)
        if not pending:
            self._check_unsubmitted()
            return
        total = sum(len(isrcs) for isrcs in pending.values())
        log.debug("ISRC submission: submitting %d ISRCs for %d recordings", total, len(pending))
        self.tagger.window.set_statusbar_message(
            N_("Submitting ISRCs …"),
            echo=None,
        )
        self._last_submitted = pending
        self._mb_api.submit_isrcs(pending, self._submission_finished)

    def _submission_finished(self, document, http, error) -> None:
        """Handle submission response."""
        if error:
            log.error("ISRC submission failed: %r", http.errorString() if http else error)
            self.tagger.window.set_statusbar_message(
                N_("ISRC submission failed"),
                echo=None,
                timeout=3000,
            )
        else:
            # Mark only the submitted ISRCs as done
            submitted = set()
            for isrcs in self._last_submitted.values():
                submitted.update(isrcs)
            for entry in self._entries.values():
                entry.new_isrcs -= submitted
            log.debug("ISRC submission finished successfully")
            self.tagger.window.set_statusbar_message(
                N_("ISRC submission finished successfully"),
                echo=None,
                timeout=3000,
            )
        self._last_submitted = {}
        self._check_unsubmitted()

    def _check_unsubmitted(self) -> None:
        """Update the UI action state based on pending submissions."""
        enabled = self.unsubmitted_count > 0
        self.tagger.window.enable_action(MainAction.SUBMIT_ISRC, enabled)
