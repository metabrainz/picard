# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2014 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2025 Laurent Monin
# Copyright (C) 2014 Francois Ferrand
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Paul Roub
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 ShubhamBhut
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
from enum import IntEnum

from picard import log
from picard.album import Album
from picard.cluster import Cluster
from picard.file import File
from picard.item import FileListItem
from picard.track import Track


class CoverArtSetterMode(IntEnum):
    APPEND = 0
    REPLACE = 1


class CoverArtSetter:

    def __init__(self, mode, coverartimage, source_obj):
        self.mode = mode
        self.coverartimage = coverartimage
        self.source_obj = source_obj

        if isinstance(self.source_obj, Album):
            self.set_coverart = self.set_coverart_album
        elif isinstance(self.source_obj, FileListItem):
            self.set_coverart = self.set_coverart_filelist
        elif isinstance(self.source_obj, File):
            self.set_coverart = self.set_coverart_file

    def set_coverart(self):
        log.debug("No set_coverart handler for %r", self.source_obj)
        return False

    def set_image(self, obj):
        if self.mode == CoverArtSetterMode.REPLACE:
            obj.metadata.images.strip_front_images()
            log.debug("Replacing images with %r in %r", self.coverartimage, obj)
        else:
            log.debug("Appending image %r to %r", self.coverartimage, obj)

        obj.metadata.images.append(self.coverartimage)
        obj.metadata_images_changed.emit()

    def set_coverart_album(self):
        album = self.source_obj
        log.debug("set_coverart_album %r", album)
        with ExitStack() as stack:
            stack.enter_context(album.suspend_metadata_images_update)
            self.set_image(album)
            for track in album.tracks:
                stack.enter_context(track.suspend_metadata_images_update)
                self.set_image(track)
            for file in album.iterfiles():
                self.set_image(file)
                file.update(signal=False)
        album.update(update_tracks=False)
        return True

    @staticmethod
    def iter_file_parents(file):
        parent = file.parent_item
        if parent:
            yield parent
            if isinstance(parent, Track) and parent.album:
                yield parent.album
            elif isinstance(parent, Cluster) and parent.related_album:
                yield parent.related_album

    def set_coverart_filelist(self):
        filelist = self.source_obj
        log.debug("set_coverart_filelist %r", filelist)
        parents = set()
        with ExitStack() as stack:
            stack.enter_context(filelist.suspend_metadata_images_update)
            self.set_image(filelist)
            for file in filelist.iterfiles():
                for parent in self.iter_file_parents(file):
                    stack.enter_context(parent.suspend_metadata_images_update)
                    parents.add(parent)
                self.set_image(file)
                file.update(signal=False)
            for parent in parents:
                if isinstance(parent, Album):
                    parent.update(update_tracks=False)
                else:
                    parent.update()
        filelist.update()
        return True

    def set_coverart_file(self):
        file = self.source_obj
        log.debug("set_coverart_file %r", file)
        self.set_image(file)
        file.update()
        return True
