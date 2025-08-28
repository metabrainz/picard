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

"""Context extraction strategies for different Picard item types."""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import Any

from picard.album import Album
from picard.cluster import Cluster
from picard.file import File
from picard.item import Item
from picard.track import Track


class ContextStrategy(ABC):
    """Abstract base class for context creation strategies."""

    @abstractmethod
    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        """Return (metadata, file_obj) tuple"""
        raise NotImplementedError

    @abstractmethod
    def can_handle(self, obj: Item) -> bool:
        """Check if this strategy can handle the given object type"""
        raise NotImplementedError


class FileContextStrategy(ContextStrategy):
    def can_handle(self, obj: Item) -> bool:
        return isinstance(obj, File)

    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        return (getattr(obj, 'metadata', None), obj if isinstance(obj, File) else None)


class TrackContextStrategy(ContextStrategy):
    def can_handle(self, obj: Item) -> bool:
        return isinstance(obj, Track)

    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        files = getattr(obj, 'files', None)
        num_linked = getattr(obj, 'num_linked_files', 0)
        file_obj = files[0] if isinstance(files, (list, tuple)) and num_linked == 1 else None
        return (getattr(obj, 'metadata', None), file_obj)


class AlbumContextStrategy(ContextStrategy):
    def can_handle(self, obj: Item) -> bool:
        return isinstance(obj, Album)

    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        return (getattr(obj, 'metadata', None), None)


class ClusterContextStrategy(ContextStrategy):
    def can_handle(self, obj: Item) -> bool:
        return isinstance(obj, Cluster)

    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        return (getattr(obj, 'metadata', None), None)


class DefaultContextStrategy(ContextStrategy):
    def can_handle(self, obj: Item) -> bool:
        return True

    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        return (getattr(obj, 'metadata', None), None)


class ContextStrategyManager:
    def __init__(self):
        self.strategies = [
            FileContextStrategy(),
            TrackContextStrategy(),
            AlbumContextStrategy(),
            ClusterContextStrategy(),
            DefaultContextStrategy(),
        ]

    def make_context(self, obj: Item) -> tuple[Any | None, Any | None]:
        for strategy in self.strategies:
            if strategy.can_handle(obj):
                return strategy.make_context(obj)
        return (None, None)
