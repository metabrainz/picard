# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009, 2019-2022 Philipp Wolfer
# Copyright (C) 2013, 2015, 2018-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
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


ext_point_options_pages = ExtensionPoint(label='options_pages')


def register_options_page(page_class):
    ext_point_options_pages.register(page_class.__module__, page_class)
