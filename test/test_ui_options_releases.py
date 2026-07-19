# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from picard.ui.options.releases import ReleasesOptionsPage


class TestReleasesOptionsPageClass:
    def test_page_name(self):
        assert ReleasesOptionsPage.NAME == 'releases'

    def test_page_parent(self):
        assert ReleasesOptionsPage.PARENT == 'metadata'

    def test_options_keys(self):
        assert 'preferred_release_types' in ReleasesOptionsPage.OPTIONS
        assert 'discouraged_release_types' in ReleasesOptionsPage.OPTIONS
        assert 'preferred_release_countries' in ReleasesOptionsPage.OPTIONS
        assert 'preferred_release_formats' in ReleasesOptionsPage.OPTIONS
