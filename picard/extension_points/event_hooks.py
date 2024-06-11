# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2013, 2017 Lukáš Lalinský
# Copyright (C) 2007-2011, 2014-2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008 ojnkpjg
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2014, 2019 Michael Wiencek
# Copyright (C) 2012 Erik Wasser
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012 noobie
# Copyright (C) 2012-2014, 2016-2017 Wieland Hoffmann
# Copyright (C) 2013, 2018 Calvin Walton
# Copyright (C) 2013-2014 Ionuț Ciocîrlan
# Copyright (C) 2013-2015, 2017, 2021 Sophist-UK
# Copyright (C) 2013-2015, 2017-2024 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Suhas
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2021, 2023 Bob Swift
# Copyright (C) 2022 skelly37
# Copyright (C) 2024 Suryansh Shakya
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


from picard.album import album_post_removal_processors
from picard.file import (
    file_post_addition_to_track_processors,
    file_post_load_processors,
    file_post_removal_to_track_processors,
    file_post_save_processors,
)


def register_album_post_removal_processor(function, priority=0):
    """Registers an album-removed processor.
    Args:
        function: function to call after album removal, it will be passed the album object
        priority: optional, 0 by default
    Returns:
        None
    """
    album_post_removal_processors.register(function.__module__, function, priority)


def register_file_post_load_processor(function, priority=0):
    """Registers a file-loaded processor.

    Args:
        function: function to call after file has been loaded, it will be passed the file object
        priority: optional, 0 by default
    Returns:
        None
    """
    file_post_load_processors.register(function.__module__, function, priority)


def register_file_post_addition_to_track_processor(function, priority=0):
    """Registers a file-added-to-track processor.

    Args:
        function: function to call after file addition, it will be passed the track and file objects
        priority: optional, 0 by default
    Returns:
        None
    """
    file_post_addition_to_track_processors.register(function.__module__, function, priority)


def register_file_post_removal_from_track_processor(function, priority=0):
    """Registers a file-removed-from-track processor.

    Args:
        function: function to call after file removal, it will be passed the track and file objects
        priority: optional, 0 by default
    Returns:
        None
    """
    file_post_removal_to_track_processors.register(function.__module__, function, priority)


def register_file_post_save_processor(function, priority=0):
    """Registers file saved processor.

    Args:
        function: function to call after save, it will be passed the file object
        priority: optional, 0 by default
    Returns:
        None
    """
    file_post_save_processors.register(function.__module__, function, priority)
