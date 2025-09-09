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

"""Constants for session management.

This module contains all constants used throughout the session management system,
including retry delays, file extensions, and excluded tags.
"""

from picard.i18n import N_


class SessionConstants:
    """Constants for session management operations.

    Retry delays
    ------------
    These delays govern how often we re-check readiness during session
    load/restore using Qt timers. They coordinate operations across
    asynchronous components (file scanning, network lookups, album/track
    population, UI creation) without requiring deep refactors.

    Attributes
    ----------
    DEFAULT_RETRY_DELAY_MS : int
        General-purpose delay (milliseconds) for deferred actions that need
        other subsystems to settle first. Used for:
        - Applying saved metadata / tag deltas once files are loaded
          (see `MetadataHandler.apply_saved_metadata_if_any`,
          `MetadataHandler.apply_tag_deltas_if_any`).
        - Restoring UI state (expanding albums) once UI items exist
          (see `SessionLoader._restore_ui_state`).
        - Finalizing the restoring flag when network/disk operations are idle
          (see `SessionLoader._unset_restoring_flag_when_idle`).

        Trade-offs
        ----------
        - Too short: Excess CPU wake-ups, risk of race-condition flapping,
          unnecessary network/UI churn.
        - Too long: Noticeable lag for metadata application and UI finalize.

        Tuning
        ------
        - Shorten for tests, small sessions, fast machines (snappier UI).
        - Lengthen for very large sessions, slow I/O/network (reduce churn).

    FAST_RETRY_DELAY_MS : int
        Lower-latency delay (milliseconds) for local readiness checks where
        objects stabilize quickly (e.g., file/album becomes ready) and we want
        prompt feedback. Used for:
        - Moving files to tracks once file/album are ready
          (see `TrackMover.move_files_to_tracks`).
        - Specialized helpers like `RetryHelper.retry_until_file_ready` and
          `RetryHelper.retry_until_album_ready`.

        Trade-offs
        ----------
        - Too short: High-frequency polling of local state, potential CPU
          spikes on large batches.
        - Too long: Sluggish track moves and perceived restore latency.

    Notes
    -----
    What is being retried
        Readiness checks and deferred execution (polling until conditions are
        true), not re-execution of failed logic.

    Why retries are needed
        In an event-driven Qt architecture not all components emit precise
        "ready" signals, and many operations require multiple conditions to be
        true simultaneously (e.g., file loaded AND album tracks available AND
        UI node created). Timed re-checks are a pragmatic coordination
        mechanism.

    Alternative (fully async/signals)
        We could replace polls with explicit signals/awaitables
        (e.g., file_ready, album_tracks_loaded, ui_item_created, webservice_idle),
        but this requires cross-cutting changes across `File`, `Album`, UI,
        WebService, and `Tagger`. Incremental migration is possible; until then
        these delays balance responsiveness and load.
    """

    # File handling
    SESSION_FILE_EXTENSION = ".mbps.gz"
    SESSION_FORMAT_VERSION = 1

    # Recent sessions
    # Number of recent session entries shown in the UI flyout menu.
    RECENT_SESSIONS_MAX = 5

    # Retry delays in milliseconds
    # Used by Qt timers for retry/poll loops during session load/restore.
    # Balance responsiveness with CPU/network load: shorter feels snappier
    # but risks busy-looping and churn; longer reduces load but adds visible lag.
    DEFAULT_RETRY_DELAY_MS = 200

    # General retries (e.g. metadata application, UI finalize).
    # Adjust up for huge sessions/slow I/O; down for tests/small sessions/fast
    # machines.
    FAST_RETRY_DELAY_MS = 150
    # Local readiness checks (files/albums becoming ready, track moves).
    # Too short ⇒ high CPU/race flapping; too long ⇒ sluggish moves/restore.

    # Location types
    LOCATION_UNCLUSTERED = "unclustered"
    LOCATION_TRACK = "track"
    LOCATION_ALBUM_UNMATCHED = "album_unmatched"
    LOCATION_CLUSTER = "cluster"
    LOCATION_NAT = "nat"


class SessionMessages:
    """Centralized session-related message strings.

    Define raw, untranslated strings. Call sites should mark for translation:
    - API/config titles: wrap with N_()
    - UI labels: wrap with _()
    """

    # Option titles (API/config)
    SESSION_SAFE_RESTORE_TITLE = N_("Honor local edits and placement on load (no auto-matching)")
    SESSION_LOAD_LAST_TITLE = N_("Load last saved session on startup")
    SESSION_AUTOSAVE_TITLE = N_("Auto-save session every N minutes (0 disables)")
    SESSION_BACKUP_TITLE = N_("Attempt to keep a session backup on unexpected shutdown")
    SESSION_INCLUDE_MB_DATA_TITLE = N_("Include MusicBrainz data in saved sessions (faster loads, risk of stale data)")
    SESSION_FOLDER_PATH_TITLE = N_("Sessions folder path (leave empty for default)")
