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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from unittest.mock import Mock

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


class MetadataBoxColorsChangedTest(PicardTestCase):
    def test_on_colors_changed_refreshes_without_dropping_caches(self):
        """Changing interface colors must refresh the box so tag highlights update.

        Regression test: the metadata box did not react to interface color
        changes, so after changing e.g. the "Tag added" color and applying, the
        box kept showing the old color until the next selection change rebuilt
        it. It now refreshes on theme.colors_changed.
        """
        box = MetadataBox.__new__(MetadataBox)
        box.update = Mock()

        box._on_colors_changed()

        box.update.assert_called_once_with(drop_album_caches=False)
