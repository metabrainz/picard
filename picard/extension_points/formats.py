# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2012 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2010, 2014, 2018-2020, 2023 Philipp Wolfer
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013, 2017-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2020 Gabriel Ferreira
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

from picard.plugin import ExtensionPoint


ext_point_formats = ExtensionPoint(label='formats')
formats_extensions = {}


def register_format(file_format):
    ext_point_formats.register(file_format.__module__, file_format)
    for ext in file_format.EXTENSIONS:
        formats_extensions[ext[1:]] = file_format
