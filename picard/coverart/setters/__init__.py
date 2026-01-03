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


from enum import IntEnum

from picard import log

from .handlers import _set_coverart_dispatch


class CoverArtSetterMode(IntEnum):
    """Enumeration for cover art setting modes."""

    APPEND = 0
    REPLACE = 1


class CoverArtSetter:
    """Handles setting cover art on different types of objects using single dispatch pattern."""

    def __init__(self, mode: CoverArtSetterMode, coverartimage, source_obj) -> None:
        """
        Initialize the CoverArtSetter.

        Parameters
        ----------
        mode : CoverArtSetterMode
            The mode to use when setting cover art (APPEND or REPLACE)
        coverartimage
            The cover art image to set
        source_obj
            The source object to set cover art on
        """
        self.mode = mode
        self.coverartimage = coverartimage
        self.source_obj = source_obj

    def set_coverart(self) -> bool:
        """
        Set cover art on the source object using single dispatch.

        Returns
        -------
        bool
            True if cover art was set successfully, False otherwise
        """
        return _set_coverart_dispatch(self.source_obj, self)

    def _set_image(self, obj) -> None:
        """
        Set the cover art image on an object based on the current mode.

        Parameters
        ----------
        obj
            The object to set the image on
        """
        if self.mode == CoverArtSetterMode.REPLACE:
            obj.metadata.images.strip_front_images()
            log.debug("Replacing images with %r in %r", self.coverartimage, obj)
        else:
            log.debug("Appending image %r to %r", self.coverartimage, obj)

        obj.metadata.images.append(self.coverartimage)
        obj.metadata_images_changed.emit()
