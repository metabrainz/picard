# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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


from contextlib import ExitStack
from functools import singledispatch

from picard import log
from picard.album import Album
from picard.cluster import Cluster
from picard.file import File
from picard.item import FileListItem
from picard.track import Track


# Single dispatch function - this is the heart of the pattern
@singledispatch
def _set_coverart_dispatch(source_obj, setter):
    """
    Handle unknown types in the single dispatch pattern.

    Parameters
    ----------
    source_obj
        The source object to set cover art on (unsupported type)
    setter
        The CoverArtSetter instance

    Returns
    -------
    bool
        False for unsupported object types
    """
    log.debug("No set_coverart handler for %r", source_obj)
    return False


@_set_coverart_dispatch.register
def _handle_album(album: Album, setter):
    """
    Handle Album objects in the single dispatch pattern.

    Set cover art on an album and all its associated tracks and files.

    Parameters
    ----------
    album : Album
        The album to set cover art on
    setter
        The CoverArtSetter instance

    Returns
    -------
    bool
        True if cover art was set successfully
    """
    log.debug("set_coverart_album %r", album)

    with ExitStack() as stack:
        stack.enter_context(album.suspend_metadata_images_update)
        setter._set_image(album)

        # If the album is still loading, tracks are in `_new_tracks`
        tracks = getattr(album, '_new_tracks', None) or album.tracks
        for track in tracks:
            stack.enter_context(track.suspend_metadata_images_update)
            setter._set_image(track)

        for file in album.iterfiles():
            setter._set_image(file)
            file.update(signal=False)

    album.update(update_tracks=False)
    return True


@_set_coverart_dispatch.register
def _handle_filelist(filelist: FileListItem, setter):
    """
    Handle FileListItem objects in the single dispatch pattern.

    Set cover art on a file list item and all its associated files and parent objects.

    Parameters
    ----------
    filelist : FileListItem
        The file list item to set cover art on
    setter
        The CoverArtSetter instance

    Returns
    -------
    bool
        True if cover art was set successfully
    """
    log.debug("set_coverart_filelist %r", filelist)

    parents = set()
    with ExitStack() as stack:
        stack.enter_context(filelist.suspend_metadata_images_update)
        setter._set_image(filelist)

        for file in filelist.iterfiles():
            for parent in _iter_file_parents(file):
                stack.enter_context(parent.suspend_metadata_images_update)
                parents.add(parent)

            setter._set_image(file)
            file.update(signal=False)

        for parent in parents:
            if isinstance(parent, Album):
                parent.update(update_tracks=False)
            else:
                parent.update()

    filelist.update()
    return True


@_set_coverart_dispatch.register
def _handle_file(file: File, setter):
    """
    Handle File objects in the single dispatch pattern.

    Set cover art on a single file.

    Parameters
    ----------
    file : File
        The file to set cover art on
    setter
        The CoverArtSetter instance

    Returns
    -------
    bool
        True if cover art was set successfully
    """
    log.debug("set_coverart_file %r", file)

    setter._set_image(file)
    file.update()
    return True


def _iter_file_parents(file: File):
    """
    Iterate over the parent objects of a file.

    Parameters
    ----------
    file : File
        The file to get parents for

    Yields
    ------
    object
        Parent objects of the file
    """
    parent = file.parent_item
    if parent:
        yield parent
        if (isinstance(parent, Track) or isinstance(parent, Cluster)) and parent.album:
            yield parent.album
