# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2025-2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    TypeAlias,
)

from picard.album import Album
from picard.coverart.image import CoverArtImage
from picard.plugin import ExtensionPoint


if TYPE_CHECKING:
    from picard.plugin3.api import ImageInfo


CoverArtFilter: TypeAlias = Callable[[bytes, 'ImageInfo', Album, CoverArtImage], bool]
CoverArtMetadataFilter: TypeAlias = Callable[[dict[str, Any]], bool]

ext_point_cover_art_filters = ExtensionPoint[CoverArtFilter](label='cover_art_filters')
ext_point_cover_art_metadata_filters = ExtensionPoint[CoverArtMetadataFilter](label='cover_art_metadata_filters')


def register_cover_art_filter(cover_art_filter: CoverArtFilter) -> None:
    ext_point_cover_art_filters.register(cover_art_filter.__module__, cover_art_filter)


def register_cover_art_metadata_filter(cover_art_metadata_filter: CoverArtMetadataFilter) -> None:
    ext_point_cover_art_metadata_filters.register(cover_art_metadata_filter.__module__, cover_art_metadata_filter)
