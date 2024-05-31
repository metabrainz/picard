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

from picard.coverart.processing import (  # noqa: F401 # pylint: disable=unused-import
    filters,
)
from picard.extension_points.cover_art_filters import (
    ext_point_cover_art_filters,
    ext_point_cover_art_metadata_filters,
)


def run_image_filters(data):
    for f in ext_point_cover_art_filters:
        if not f(data):
            return False
    return True


def run_image_metadata_filters(metadata):
    for f in ext_point_cover_art_metadata_filters:
        if not f(metadata):
            return False
    return True


# def run_image_processors(data):
#     pass
