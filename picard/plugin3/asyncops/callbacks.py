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

"""Callback and signal definitions for async operations."""

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Optional,
)


@dataclass
class OperationResult:
    """Result of an async operation."""

    success: bool
    result: Any = None
    error: Optional[Exception] = None
    error_message: str = ''


@dataclass
class ProgressUpdate:
    """Progress update for long-running operations."""

    operation: str  # 'install', 'update', 'fetch', etc.
    plugin_id: Optional[str] = None
    percent: int = 0  # 0-100
    message: str = ''
    current: int = 0
    total: int = 0


# Callback type definitions
OperationCallback = Callable[[OperationResult], None]
ProgressCallback = Callable[[ProgressUpdate], None]
