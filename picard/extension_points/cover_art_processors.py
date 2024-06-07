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

from enum import IntEnum

from picard.plugin import ExtensionPoint


ext_point_cover_art_processors = ExtensionPoint(label='cover_art_processors')


class ProcessingTarget(IntEnum):
    TAGS = 0
    FILE = 1
    BOTH = 2


class ImageProcessor:

    def save_to_tags(self):
        return False

    def save_to_file(self):
        return False

    def same_processing(self):
        return False

    def run(self, data, info, target):
        pass


def get_cover_art_processors():
    queue_both, queue_tags, queue_file = [], [], []
    for processor in ext_point_cover_art_processors:
        if processor.same_processing():
            queue_both.append(processor)
        else:
            if processor.save_to_tags():
                queue_tags.append(processor)
            if processor.save_to_file():
                queue_file.append(processor)
    return queue_both, queue_tags, queue_file


def register_cover_art_processor(cover_art_processor):
    instance = cover_art_processor()
    ext_point_cover_art_processors.register(cover_art_processor.__module__, instance)
