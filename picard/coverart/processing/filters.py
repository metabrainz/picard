# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
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

from picard import log
from picard.config import get_config
from picard.extension_points.cover_art_filters import (
    register_cover_art_filter,
    register_cover_art_metadata_filter,
)


def _check_threshold_size(width, height):
    config = get_config()
    if not config.setting['filter_cover_by_size']:
        return True
    # If the given width or height is -1, that dimension is not considered
    min_width = config.setting['cover_minimum_width'] if width != -1 else -1
    min_height = config.setting['cover_minimum_height'] if height != -1 else -1
    if width < min_width or height < min_height:
        log.debug(
            "Discarding cover art due to size. Image size: %d x %d. Minimum: %d x %d",
            width,
            height,
            min_width,
            min_height
        )
        return False
    return True


def size_filter(data, info):
    return _check_threshold_size(info.width, info.height)


def size_metadata_filter(metadata):
    if 'width' not in metadata or 'height' not in metadata:
        return True
    return _check_threshold_size(metadata['width'], metadata['height'])


register_cover_art_filter(size_filter)
register_cover_art_metadata_filter(size_metadata_filter)
