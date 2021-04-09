# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020 Philipp Wolfer
# Copyright (C) 2019 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
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


from collections.abc import MutableSequence

from picard.config import get_config


class ImageList(MutableSequence):
    def __init__(self, iterable=()):
        self._images = list(iterable)
        self._hash_dict = {}
        self._changed = True

    def __len__(self):
        return len(self._images)

    def __getitem__(self, index):
        return self._images[index]

    def __setitem__(self, index, value):
        self._images[index] = value
        self._changed = True

    def __delitem__(self, index):
        del self._images[index]
        self._changed = True

    def insert(self, index, value):
        self._changed = True
        return self._images.insert(index, value)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._images)

    def _sorted(self):
        return sorted(self, key=lambda image: image.normalized_types())

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        return self._sorted() == other._sorted()

    def copy(self):
        return self.__class__(self._images)

    def get_front_image(self):
        for img in self:
            if img.is_front_image():
                return img
        return None

    def to_be_saved_to_tags(self, settings=None):
        """Generator returning images to be saved to tags according to
           passed settings or config.setting
        """
        if settings is None:
            config = get_config()
            settings = config.setting
        if settings['save_images_to_tags']:
            only_one_front = settings['embed_only_one_front_image']
            for image in self:
                if not image.can_be_saved_to_tags:
                    continue
                if only_one_front:
                    if not image.is_front_image():
                        continue
                    yield image
                    break
                else:
                    yield image

    def strip_front_images(self):
        self._images = [image for image in self._images if not image.is_front_image()]
        self._changed = True

    def hash_dict(self):
        if self._changed:
            self._hash_dict = {img.datahash.hash(): img for img in self._images}
            self._changed = False
        return self._hash_dict


class ImageListState:
    def __init__(self):
        self.new_images = {}
        self.orig_images = {}
        self.sources = []
        self.has_common_new_images = True
        self.has_common_orig_images = True
        self.first_new_obj = True
        self.first_orig_obj = True
        # The next variables specify what will be updated
        self.update_new_metadata = False
        self.update_orig_metadata = False


def _process_images(state, src_obj, Track):
    # Check new images
    if state.update_new_metadata:
        src_dict = src_obj.metadata.images.hash_dict()
        prev_len = len(state.new_images)
        state.new_images.update(src_dict)
        if len(state.new_images) != prev_len:
            if not state.first_new_obj:
                state.has_common_new_images = False
        if state.first_new_obj:
            state.first_new_obj = False

    if state.update_orig_metadata and not isinstance(src_obj, Track):
        # Check orig images, but not for Tracks (which don't have a useful orig_metadata)
        src_dict = src_obj.orig_metadata.images.hash_dict()
        prev_len = len(state.orig_images)
        state.orig_images.update(src_dict)
        if len(state.orig_images) != prev_len:
            if not state.first_orig_obj:
                state.has_common_orig_images = False
        if state.first_orig_obj:
            state.first_orig_obj = False


def _update_state(obj, state):
    from picard.track import Track

    changed = False
    for src_obj in state.sources:
        _process_images(state, src_obj, Track)

    if state.update_new_metadata:
        updated_images = ImageList(state.new_images.values())
        changed |= updated_images.hash_dict().keys() != obj.metadata.images.hash_dict().keys()
        obj.metadata.images = updated_images
        obj.metadata.has_common_images = state.has_common_new_images

    if state.update_orig_metadata:
        updated_images = ImageList(state.orig_images.values())
        changed |= updated_images.hash_dict().keys() != obj.orig_metadata.images.hash_dict().keys()
        obj.orig_metadata.images = updated_images
        obj.orig_metadata.has_common_images = state.has_common_orig_images

    return changed


# TODO: use functools.singledispatch when py3 is supported
def _get_state(obj):
    from picard.album import Album
    from picard.cluster import FileList
    from picard.track import Track

    state = ImageListState()

    if isinstance(obj, Album):
        for track in obj.tracks:
            state.sources.append(track)
            state.sources += track.files
        state.sources += obj.unmatched_files.files
        state.update_new_metadata = True
        state.update_orig_metadata = True
    elif isinstance(obj, Track):
        state.sources = obj.files
        state.update_orig_metadata = True
    elif isinstance(obj, FileList):
        state.sources = obj.files
        state.update_new_metadata = True
        state.update_orig_metadata = True

    return state


def _get_metadata_images(state, sources):
    new_images = set()
    orig_images = set()
    for s in sources:
        if state.update_new_metadata:
            new_images = new_images.union(s.metadata.images)
        if state.update_orig_metadata:
            orig_images = orig_images.union(s.orig_metadata.images)
    return (new_images, orig_images)


def update_metadata_images(obj):
    """Update the metadata images `obj` based on its children.

    Based on the type of `obj` this will update `obj.metadata.images` to
    represent the metadata images of all children (`Track` or `File` objects).

    This method will iterate over all children and completely rebuild
    `obj.metadata.images`. Whenever possible the more specific functions
    `add_metadata_images` or `remove_metadata_images` should be used.

    Args:
        obj: A `Cluster`, `Album` or `Track` object with `metadata` property
    Returns:
        bool: True, if images where changed, False otherwise
    """
    return _update_state(obj, _get_state(obj))


def _add_images(metadata, added_images):
    if not added_images:
        return

    current_images = set(metadata.images)
    if added_images != current_images:
        metadata.images = ImageList(current_images.union(added_images))
        metadata.has_common_images = False


def add_metadata_images(obj, added_sources):
    """Add the images in the metadata of `added_sources` to the metadata of `obj`.

    Args:
        obj: A `Cluster`, `Album` or `Track` object with `metadata` property
        added_sources: List of child objects (`Track` or `File`) which's metadata images should be added to `obj`
    """
    state = _get_state(obj)
    (added_new_images, added_orig_images) = _get_metadata_images(state, added_sources)

    if state.update_new_metadata:
        _add_images(obj.metadata, added_new_images)
    if state.update_orig_metadata:
        _add_images(obj.orig_metadata, added_orig_images)


def _remove_images(metadata, sources, removed_images):
    """Removes `removed_images` from metadata `images`, but only if they are not included in `sources`.

    Args:
        metadata: `Metadata` object from which images should be removed
        sources: List of source `Metadata` objects
        removed_images: Set of `CoverArt` proposed for removal from `metadata`
    """
    if not metadata.images or not removed_images:
        return

    if not sources:
        metadata.images = ImageList()
        metadata.has_common_images = True
        return

    current_images = set(metadata.images)

    if metadata.has_common_images and current_images == removed_images:
        return

    common_images = True  # True, if all children share the same images
    previous_images = None

    # Iterate over all sources and check whether the images proposed to be
    # removed are used in any sources. Images used in existing sources
    # must not be removed.
    for source_metadata in sources:
        source_images = set(source_metadata.images)
        if previous_images and common_images and previous_images != source_images:
            common_images = False
        previous_images = set(source_metadata.images)  # Remember for next iteration
        removed_images = removed_images.difference(source_images)
        if not removed_images and not common_images:
            return  # No images left to remove, abort immediatelly

    metadata.images = ImageList(current_images.difference(removed_images))
    metadata.has_common_images = common_images


def remove_metadata_images(obj, removed_sources):
    """Remove the images in the metadata of `removed_sources` from the metadata of `obj`.

    Args:
        obj: A `Cluster`, `Album` or `Track` object with `metadata` property
        removed_sources: List of child objects (`Track` or `File`) which's metadata images should be removed from `obj`
    """
    from picard.track import Track

    state = _get_state(obj)
    (removed_new_images, removed_orig_images) = _get_metadata_images(state, removed_sources)

    if state.update_new_metadata:
        sources = [s.metadata for s in state.sources]
        _remove_images(obj.metadata, sources, removed_new_images)
    if state.update_orig_metadata:
        sources = [s.orig_metadata for s in state.sources if not isinstance(s, Track)]
        _remove_images(obj.orig_metadata, sources, removed_orig_images)
