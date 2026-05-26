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

from collections.abc import Callable

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
        attempts = 0

        def attempt() -> None:
            nonlocal attempts
            attempts += 1
            if max_attempts and attempts > max_attempts:
                return

            if condition_fn():
                action_fn()
            else:
                QtCore.QTimer.singleShot(delay_ms, attempt)

        attempt()
