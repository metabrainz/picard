# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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

from picard.browser.filelookup import FileLookup

from picard.ui.metadatabox import MetadataBox


class MetadataBoxFileLookupTest(PicardTestCase):
    def test_filelook_methods(self):
        """Test if methods listed in MetadataBox.LOOKUP_TAGS are valid FileLookup methods"""
        for method_as_string in MetadataBox.LOOKUP_TAGS.values():
            method = getattr(FileLookup, method_as_string, None)
            self.assertIsNotNone(method, f"No such FileLookup.{method_as_string}")
            self.assertTrue(callable(method), f"FileLookup.{method_as_string} is not callable")
