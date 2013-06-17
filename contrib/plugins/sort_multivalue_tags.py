# -*- coding: utf-8 -*-

# This is the Sort Multivalue Tags plugin for MusicBrainz Picard.
# Copyright (C) 2013 Sophist
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

PLUGIN_NAME = u"Sort Multi-Value Tags"
PLUGIN_AUTHOR = u"Sophist"
PLUGIN_DESCRIPTION = u'Sort Multi-Value Tags e.g. Release Type, Lyrics alphabetically.'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.15"]

from picard.metadata import register_track_metadata_processor

# Define and register the Track Metadata function
def sort_multivalue_tags(tagger, metadata, track, release):

    for tag in metadata.keys():
        data = metadata.getall(tag)
        if len(data) > 1:
            sorted_data = sorted(data)
            if data != sorted_data:
                metadata.set(tag, sorted_data)

register_track_metadata_processor(sort_multivalue_tags)
