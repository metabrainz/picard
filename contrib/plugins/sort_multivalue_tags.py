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
PLUGIN_DESCRIPTION = u'Sort Multi-Value Tags e.g. Performers alphabetically.'
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.15.0", "0.15.1", "0.16.0", "1.0.0", "1.1.0", "1.2.0", "1.3.0"]

from picard.metadata import register_track_metadata_processor

class SortMultiValueTags:

    # Exclude the following tags because the sort order is related to other tags or has a meaning like primary artist
    exclude_tags = [
        'artist', 'artistsort', 'musicbrainz_artistid',
        'albumartist', 'albumartistsort', 'musicbrainz_albumartistid',
        'releasetype',
        ]

    # Define and register the Track Metadata function
    def sort_multivalue_tags(self, tagger, metadata, track, release):

        for tag in metadata.keys():
            if tag in SortMultiValueTags.exclude_tags:
                continue
            data = dict.get(metadata, tag)
            if len(data) > 1:
                sorted_data = sorted(data)
                if data != sorted_data:
                    metadata.set(tag,sorted_data)

register_track_metadata_processor(SortMultiValueTags().sort_multivalue_tags)
