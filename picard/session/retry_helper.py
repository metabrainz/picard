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

"""Retry utility for session management operations.

This module provides utilities for retrying operations until conditions are met,
replacing the scattered timer patterns throughout the session management code.
"""

from __future__ import annotations

from typing import Callable

from PyQt6 import QtCore

from picard.session.constants import SessionConstants


class RetryHelper:
    """Utility for retrying operations until conditions are met."""

    @staticmethod
    def retry_until(
        condition_fn: Callable[[], bool],
        action_fn: Callable[[], None],
        delay_ms: int = SessionConstants.DEFAULT_RETRY_DELAY_MS,
        max_attempts: int | None = None,
    ) -> None:
        """Retry an action until a condition is met.

        Parameters
        ----------
        condition_fn : Callable[[], bool]
            Function that returns True when the condition is met.
        action_fn : Callable[[], None]
            Function to execute when the condition is met.
        delay_ms : int, optional
            Delay between retry attempts in milliseconds. Defaults to DEFAULT_RETRY_DELAY_MS.
        max_attempts : int | None, optional
            Maximum number of retry attempts. If None, retry indefinitely.

        Notes
        -----
        This replaces the scattered QtCore.QTimer.singleShot patterns throughout
        the session management code with a centralized retry mechanism.
        """
        attempts = [0]

        def attempt() -> None:
            attempts[0] += 1
            if max_attempts and attempts[0] > max_attempts:
                return

            if condition_fn():
                action_fn()
            else:
                QtCore.QTimer.singleShot(delay_ms, attempt)

        attempt()

    @staticmethod
    def retry_until_file_ready(
        file_getter: Callable[[], object | None],
        action_fn: Callable[[], None],
        delay_ms: int = SessionConstants.FAST_RETRY_DELAY_MS,
    ) -> None:
        """Retry an action until a file is ready (not PENDING state).

        Parameters
        ----------
        file_getter : Callable[[], object | None]
            Function that returns the file object or None.
        action_fn : Callable[[], None]
            Function to execute when the file is ready.
        delay_ms : int, optional
            Delay between retry attempts in milliseconds. Defaults to FAST_RETRY_DELAY_MS.

        Notes
        -----
        This is a specialized version of retry_until for the common pattern
        of waiting for files to be loaded and ready for operations.
        """

        def is_file_ready() -> bool:
            file_obj = file_getter()
            if not file_obj:
                return False
            # Check if file has a state attribute and it's not PENDING
            return hasattr(file_obj, 'state') and file_obj.state != getattr(file_obj, 'PENDING', 0)

        RetryHelper.retry_until(is_file_ready, action_fn, delay_ms)

    @staticmethod
    def retry_until_album_ready(
        album_getter: Callable[[], object | None],
        action_fn: Callable[[], None],
        delay_ms: int = SessionConstants.FAST_RETRY_DELAY_MS,
    ) -> None:
        """Retry an action until an album is ready (has tracks loaded).

        Parameters
        ----------
        album_getter : Callable[[], object | None]
            Function that returns the album object or None.
        action_fn : Callable[[], None]
            Function to execute when the album is ready.
        delay_ms : int, optional
            Delay between retry attempts in milliseconds. Defaults to FAST_RETRY_DELAY_MS.

        Notes
        -----
        This is a specialized version of retry_until for the common pattern
        of waiting for albums to be loaded with their tracks.
        """

        def is_album_ready() -> bool:
            album = album_getter()
            if not album:
                return False
            # Check if album has tracks loaded
            return hasattr(album, 'tracks') and hasattr(album.tracks, '__len__') and len(album.tracks) > 0

        RetryHelper.retry_until(is_album_ready, action_fn, delay_ms)
