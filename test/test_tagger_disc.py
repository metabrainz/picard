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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.tagger import Tagger


class TaggerLookupCdTest(PicardTestCase):
    """Tagger.lookup_cd: which drive is read."""

    def _lookup(self, setting, device=None):
        self.set_config_values({'cd_lookup_device': setting})
        tagger = MagicMock(spec=Tagger)
        Tagger.lookup_cd(tagger, device)
        tagger.run_lookup_cd.assert_called_once()
        return tagger.run_lookup_cd.call_args.args[0]

    def test_chosen_drive_is_used(self):
        self.assertEqual(self._lookup('/dev/sr0,/dev/sr1', device='/dev/sr1'), '/dev/sr1')

    def test_first_configured_drive_by_default(self):
        self.assertEqual(self._lookup('/dev/sr0,/dev/sr1'), '/dev/sr0')

    def test_spaces_around_the_configured_drive_are_dropped(self):
        self.assertEqual(self._lookup(' /dev/sr0 , /dev/sr1'), '/dev/sr0')

    def test_empty_items_are_skipped(self):
        self.assertEqual(self._lookup(', /dev/sr1'), '/dev/sr1')

    def test_no_configured_drive_lets_discid_detect_one(self):
        self.assertIsNone(self._lookup(''))
