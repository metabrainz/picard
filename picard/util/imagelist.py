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

    def __eq__(self, other):
        return sorted(self, key=get_image_type) == sorted(other, key=get_image_type)

    def __getitem__(self, k):
        result = super().__getitem__(k)
        try:
            return ImageList(result)
        except TypeError:
            return result


class ImageListState:
    def __init__(self):
        self.new_images = set()
        self.orig_images = set()
        self.has_common_new_images = True
        self.has_common_orig_images = True
        # The next variables specify what will be updated
        self.update_new_metadata = False
        self.update_orig_metadata = False


def _process_images(state, src_obj):
    from picard.track import Track

    # Check new images
    if state.update_new_metadata:
        if state.new_images != set(src_obj.metadata.images):
            state.has_common_new_images = False
            state.new_images = state.new_images.union(src_obj.metadata.images)

    if state.update_orig_metadata and not isinstance(src_obj, Track):
        # Check orig images, but not for Tracks (which don't have a useful orig_metadata)
        if state.orig_images != set(src_obj.orig_metadata.images):
            state.has_common_orig_images = False
            state.orig_images = state.orig_images.union(src_obj.orig_metadata.images)


def _update_state(obj, state, sources):
    for src_obj in sources:
        _process_images(state, src_obj)

    if state.update_new_metadata:
        obj.metadata.images = ImageList(state.new_images)
        obj.metadata.has_common_images = state.has_common_new_images

    if state.update_orig_metadata:
        obj.orig_metadata.images = ImageList(state.orig_images)
        obj.orig_metadata.has_common_images = state.has_common_orig_images


# TODO: use functools.singledispatch when py3 is supported
def update_metadata_images(obj):
    from picard.album import Album
    from picard.cluster import Cluster
    from picard.track import Track

    state = ImageListState()

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

    _update_state(obj, state, sources)
