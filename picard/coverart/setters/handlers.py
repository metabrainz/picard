# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections.abc import Iterator
from contextlib import ExitStack
from functools import singledispatch

from picard import log
from picard.album import Album
from picard.cluster import (
    Cluster,
    TempItemList,
)
from picard.file import File
from picard.item import (
    FileListItem,
    Item,
    MetadataItem,
)
from picard.track import Track


# Single dispatch function - this is the heart of the pattern
@singledispatch
def _set_coverart_dispatch(source_obj: MetadataItem, setter) -> bool:
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
def _handle_album(album: Album, setter) -> bool:
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

    with album.suspend_metadata_images_update:
        setter._set_image(album)

        # If the album is still loading, tracks are in `_new_tracks`
        tracks = getattr(album, '_new_tracks', None) or album.tracks
        for track in tracks:
            setter._set_image(track)

        for file in album.iterfiles():
            if setter._set_image(file):
                file.update(signal=False)

    album.update(update_tracks=True)
    return True


@_set_coverart_dispatch.register
def _handle_filelist(filelist: FileListItem, setter) -> bool:
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
            for parent in _iter_item_parents(file):
                stack.enter_context(parent.suspend_metadata_images_update)
                parents.add(parent)

            if setter._set_image(file):
                file.update(signal=False)

        for parent in parents:
            if isinstance(parent, Album):
                parent.update(update_tracks=False)
            else:
                parent.update()

    filelist.update()
    return True


@_set_coverart_dispatch.register
def _handle_tempitemlist(itemlist: TempItemList, setter) -> bool:
    """
    Handle TempItemList (multi-object selection aggregate) objects in the single dispatch pattern.

    Set cover art on all items in the temporary item list.

    Parameters
    ----------
    itemlist : TempItemList
        The file list item to set cover art on
    setter
        The CoverArtSetter instance

    Returns
    -------
    bool
        True if cover art was set successfully
    """
    log.debug("set_coverart_tempitemlist %r", itemlist)

    items = set(itemlist.items)
    parents = set()
    with ExitStack() as stack:
        stack.enter_context(itemlist.suspend_metadata_images_update)
        setter._set_image(itemlist)

        for item in items:
            for parent in _iter_item_parents(item):
                if parent not in items:
                    stack.enter_context(parent.suspend_metadata_images_update)
                    parents.add(parent)

            if setter._set_image(item):
                item.update()

        for parent in parents:
            if isinstance(parent, Album):
                parent.update(update_tracks=False)
            else:
                parent.update()

    return True


@_set_coverart_dispatch.register
def _handle_file(file: File, setter) -> bool:
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

    if setter._set_image(file):
        file.update()
    return True


def _iter_item_parents(item: Item) -> Iterator[MetadataItem]:
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
    parent = None
    if isinstance(item, File):
        parent = item.parent_item
    if isinstance(item, (Track, Cluster)) or isinstance(item, Cluster):
        parent = item.album
    if parent:
        if parent.can_show_coverart:
            yield parent
        yield from _iter_item_parents(parent)
