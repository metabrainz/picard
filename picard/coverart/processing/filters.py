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

from PyQt6.QtGui import QImage

from picard import log
from picard.config import get_config
from picard.extension_points.cover_art_filters import register_cover_art_filter


def size_filter(data):
    config = get_config()
    if not config.setting['filter_cover_by_size']:
        return True
    image = QImage.fromData(data)
    width = config.setting['cover_width_threshold']
    height = config.setting['cover_height_threshold']
    if not (image.width() >= width and image.height() >= height):
        log.debug(
            "Discarding cover art due to size. Image size: %d x %d. Minimum: %d x %d",
            image.width(),
            image.height(),
            width,
            height
        )
        return False
    return True


register_cover_art_filter(size_filter)
