# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Antonio Larrosa <alarrosa@suse.com>
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


def get_image_type(image):
    return image.types_as_string()


class ImageList(list):

    def __init__(self):
        super(ImageList, self).__init__()

    def __eq__(self, other):
        return sorted(self, key=get_image_type) == sorted(other, key=get_image_type)

    def __getslice__(self, i, j):
        i = max(0, min(i, len(self)))
        j = max(0, min(j, len(self)))
        r = ImageList()
        r[:] = [self[it] for it in range(i, j)]
        return r


def _process_images(state, src_obj):
    from picard.track import Track

    # Check new images
    if state.update_new_metadata:
        if state.first_new_obj:
            state.new_images = src_obj.metadata.images[:]
            state.first_new_obj = False
        else:
            if state.new_images != src_obj.metadata.images:
                state.has_common_new_images = False
                state.new_images.extend([image for image in src_obj.metadata.images if image not in state.new_images])

    if state.update_orig_metadata and not isinstance(src_obj, Track):
        # Check orig images, but not for Tracks (which don't have a useful orig_metadata)
        if state.first_orig_obj:
            state.orig_images = src_obj.orig_metadata.images[:]
            state.first_orig_obj = False
        else:
            if state.orig_images != src_obj.orig_metadata.images:
                state.has_common_orig_images = False
                state.orig_images.extend([image for image in src_obj.orig_metadata.images if image not in state.orig_images])


def update_metadata_images(obj):
    from picard.track import Track
    from picard.cluster import Cluster
    from picard.album import Album

    class State:
        new_images = ImageList()
        orig_images = ImageList()
        has_common_new_images = True
        has_common_orig_images = True
        first_new_obj = True
        first_orig_obj = True
        # The next variables specify what will be updated
        update_new_metadata = False
        update_orig_metadata = False

    state = State()

    if isinstance(obj, Album):
        sources = []
        for track in obj.tracks:
            sources.append(track)
            sources += track.linked_files
        sources += obj.unmatched_files.files
        state.update_new_metadata = True
        state.update_orig_metadata = True
    elif isinstance(obj, Track):
        sources = obj.linked_files
        state.update_orig_metadata = True
    elif isinstance(obj, Cluster):
        sources = obj.files
        state.update_new_metadata = True

    for src_obj in sources:
        _process_images(state, src_obj)

    if state.update_new_metadata:
        obj.metadata.images = state.new_images
        obj.metadata.has_common_images = state.has_common_new_images

    if state.update_orig_metadata:
        obj.orig_metadata.images = state.orig_images
        obj.orig_metadata.has_common_images = state.has_common_orig_images
