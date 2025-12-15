# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014-2015, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2015 Rahul Raturi
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016 Wieland Hoffmann
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2019-2021 Philipp Wolfer
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


from picard.extension_points.options_pages import register_options_page
from picard.plugin import ExtensionPoint


ext_point_cover_art_providers = ExtensionPoint(label='cover_art_providers')


def register_cover_art_provider(provider):
    ext_point_cover_art_providers.register(provider.__module__, provider)
    if hasattr(provider, 'OPTIONS') and provider.OPTIONS:
        if not hasattr(provider.OPTIONS, 'NAME'):
            provider.OPTIONS.NAME = provider.name.lower().replace(' ', '_')
        if not hasattr(provider.OPTIONS, 'TITLE'):
            provider.OPTIONS.TITLE = provider.display_title()
        register_options_page(provider.OPTIONS)
