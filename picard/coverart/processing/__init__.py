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

from collections import namedtuple

from picard.coverart.processing import (  # noqa: F401 # pylint: disable=unused-import
    filters,
    processors,
)
from picard.extension_points.cover_art_filters import (
    ext_point_cover_art_filters,
    ext_point_cover_art_metadata_filters,
)
from picard.extension_points.cover_art_processors import (
    ProcessingTarget,
    get_cover_art_processors,
)
from picard.util import imageinfo


ImageInfo = namedtuple('ImageInfo', ['width', 'height', 'mime', 'extension', 'datalen'])


class CoverArtProcessingError(Exception):
    pass


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


def run_image_processors(data, coverartimage):
    try:
        info = ImageInfo(*imageinfo.identify(data))
        both, tags, file = get_cover_art_processors()
        for processor in both:
            data = processor.run(data, info, ProcessingTarget.BOTH)
        tags_data = data
        file_data = data
        for processor in tags:
            tags_data = processor.run(tags_data, info, ProcessingTarget.TAGS)
        for processor in file:
            file_data = processor.run(file_data, info, ProcessingTarget.FILE)
        coverartimage.set_data(tags_data)
        coverartimage.set_external_file_data(file_data)
    except imageinfo.IdentificationError as e:
        raise CoverArtProcessingError(e)
