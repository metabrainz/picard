# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Philipp Wolfer
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

from test.picardtestcase import PicardTestCase

from picard.ui.options.plugins import PluginsOptionsPage


class PluginsOptionsPageTest(PicardTestCase):

    def test_link_authors(self):
        self.assertEqual(
            '<a href="mailto:coyote@acme.com">Wile E. Coyote</a>, Road &lt;Runner&gt;',
            PluginsOptionsPage.link_authors('Wile E. Coyote <coyote@acme.com>, Road <Runner>'),
        )
