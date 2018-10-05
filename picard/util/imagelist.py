# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Antonio Larrosa <alarrosa@suse.com>
# Copyright (C) 2018 Philipp Wolfer <ph.wolfer@gmail.com>
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
        self.sources = []
        self.has_common_new_images = True
        self.has_common_orig_images = True
        self.first_new_obj = True
        self.first_orig_obj = True
        # The next variables specify what will be updated
        self.update_new_metadata = False
        self.update_orig_metadata = False


def _process_images(state, src_obj):
    from picard.track import Track

    # Check new images
    if state.update_new_metadata:
        if state.new_images != set(src_obj.metadata.images):
            if not state.first_new_obj:
                state.has_common_new_images = False
            state.new_images = state.new_images.union(src_obj.metadata.images)
        if state.first_new_obj:
            state.first_new_obj = False

    if state.update_orig_metadata and not isinstance(src_obj, Track):
        # Check orig images, but not for Tracks (which don't have a useful orig_metadata)
        if state.orig_images != set(src_obj.orig_metadata.images):
            if not state.first_orig_obj:
                state.has_common_orig_images = False
            state.orig_images = state.orig_images.union(src_obj.orig_metadata.images)
        if state.first_orig_obj:
            state.first_orig_obj = False


def _update_state(obj, state):
    is_first = True
    for src_obj in state.sources:
        _process_images(state, src_obj)

    if state.update_new_metadata:
        obj.metadata.images = ImageList(state.new_images)
        obj.metadata.has_common_images = state.has_common_new_images

    if state.update_orig_metadata:
        obj.orig_metadata.images = ImageList(state.orig_images)
        obj.orig_metadata.has_common_images = state.has_common_orig_images


# TODO: use functools.singledispatch when py3 is supported
def _get_state(obj):
    from picard.album import Album
    from picard.cluster import Cluster
    from picard.track import Track

    state = ImageListState()

    if isinstance(obj, Album):
        for track in obj.tracks:
            state.sources.append(track)
            state.sources += track.linked_files
        state.sources += obj.unmatched_files.files
        state.update_new_metadata = True
        state.update_orig_metadata = True
    elif isinstance(obj, Track):
        state.sources = obj.linked_files
        state.update_orig_metadata = True
    elif isinstance(obj, Cluster):
        state.sources = obj.files
        state.update_new_metadata = True

    return state


def update_metadata_images(obj):
    state = _get_state(obj)

    _update_state(obj, state)


def _remove_images(metadata, sources, removed_images):
    if not metadata.images or not removed_images:
        return

    if not sources:
        metadata.images = ImageList()
        metadata.has_common_images = True
        return

    current_images = set(metadata.images)

    if metadata.has_common_images and current_images == removed_images:
        return

    common_images = True
    previous_images = None
    for source in sources:
        source_images = set(source.metadata.images)
        if previous_images and common_images and previous_images != source_images:
            common_images = False
        previous_images = set(source.metadata.images)
        removed_images = removed_images.difference(source_images)
        if not removed_images and not common_images:
            return

    metadata.images = ImageList(current_images.difference(removed_images))
    metadata.has_common_images = common_images


def remove_metadata_images(obj, removed_sources):
    state = _get_state(obj)

    if state.update_new_metadata:
        removed_images = set()
        for s in removed_sources:
            removed_images = removed_images.union(s.metadata.images)
        _remove_images(obj.metadata, state.sources, removed_images)
