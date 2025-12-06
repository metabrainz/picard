# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025 Laurent Monin
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

"""Utilities for async operations."""

from picard.plugin3.asyncops.callbacks import OperationResult
from picard.util.thread import run_task


class OperationCancelled(Exception):
    """Raised when operation is cancelled."""

    pass


class CancellationToken:
    """Token to signal operation cancellation."""

    def __init__(self):
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def is_cancelled(self):
        return self._cancelled


def run_async(func, callback, progress_callback=None, cancellation_token=None):
    """Run function asynchronously with optional progress reporting.

    Args:
        func: Function to run in worker thread
        callback: Callback(OperationResult) on completion
        progress_callback: Optional callback for progress updates
        cancellation_token: Optional token to check for cancellation
    """

    def _wrapper():
        # Check cancellation before starting
        if cancellation_token and cancellation_token.is_cancelled():
            raise OperationCancelled()
        return func()

    def _on_complete(result=None, error=None):
        callback(
            OperationResult(
                success=error is None, result=result, error=error, error_message=str(error) if error else ''
            )
        )

    run_task(_wrapper, _on_complete)
