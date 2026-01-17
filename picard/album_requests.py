# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
# Copyright (C) 2024 Laurent Monin
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

from dataclasses import dataclass
from enum import IntEnum
import time

from picard.webservice import PendingRequest


class TaskType(IntEnum):
    """Type of album request, determines if it blocks album loading."""

    CRITICAL = 0  # Must complete before album.loaded = True
    OPTIONAL = 1  # Can complete after album is loaded
    PLUGIN = 2  # Plugin-initiated, doesn't block loading


@dataclass
class TaskInfo:
    """Information about a pending album request."""

    task_id: str
    type: TaskType
    description: str
    started_at: float
    timeout: float | None = None
    plugin_id: str | None = None
    request: PendingRequest | None = None  # PendingRequest object if available

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = time.time()

    def is_timed_out(self) -> bool:
        """Check if request has exceeded its timeout."""
        if self.timeout is None:
            return False
        return (time.time() - self.started_at) > self.timeout

    def elapsed_time(self) -> float:
        """Get elapsed time since request started."""
        return time.time() - self.started_at
