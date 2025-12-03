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

"""Async operations for plugin3 GUI integration.

This module provides non-blocking versions of plugin3 operations
using Picard's existing thread pool and WebService infrastructure.
"""

from picard.plugin3.asyncops.callbacks import (
    OperationCallback,
    OperationResult,
    ProgressCallback,
    ProgressUpdate,
)
from picard.plugin3.asyncops.manager import AsyncPluginManager
from picard.plugin3.asyncops.registry import AsyncPluginRegistry
from picard.plugin3.asyncops.utils import (
    CancellationToken,
    OperationCancelled,
)


__all__ = [
    'AsyncPluginManager',
    'AsyncPluginRegistry',
    'CancellationToken',
    'OperationCallback',
    'OperationCancelled',
    'OperationResult',
    'ProgressCallback',
    'ProgressUpdate',
]
