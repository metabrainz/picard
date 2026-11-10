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

"""`scan` command: identify files by AcoustID fingerprint.

Backed by Workspace.analyze plus the headless AcoustID idle-drain. The
fingerprint/lookup work itself is mocked here; the test exercises the command's
selector handling, the use_acoustid guard, and the identified / no_match
reporting.
"""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import Album
from picard.cli.engine.dispatch import dispatch
from picard.file import File


class ScanCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'fingerprinting_system': 'acoustid'})

    def _add_unclustered(self, name):
        f = File(name)
        self.wks.files[f.filename] = f
        self.wks.unclustered_files.add_file(f)
        return f

    def test_scan_disabled_acoustid_fails(self):
        self.set_config_values(setting={'fingerprinting_system': 'disabled'})
        self._add_unclustered('a.flac')
        result = dispatch(self.session, self.reg, 'scan')
        self.assertFalse(result.ok)

    def test_scan_no_analyzable_files_is_ok_empty(self):
        # A fresh File has no audio, so can_analyze is False.
        with patch.object(File, 'can_analyze', False):
            self._add_unclustered('a.flac')
            result = dispatch(self.session, self.reg, 'scan')
        self.assertTrue(result.ok)
        self.assertEqual([], result.items)

    def test_scan_reports_identified_and_no_match(self):
        identified = self._add_unclustered('hit.flac')
        missed = self._add_unclustered('miss.flac')

        # Simulate analyze(): the identified file gets moved onto an album track.
        album = Album('rel-1')
        track = MagicMock()
        track.album = album

        def fake_analyze(files):
            # identified file now has a Track parent (album reachable); missed
            # stays where it is (unclustered).
            identified.parent_item = track

        with (
            patch.object(File, 'can_analyze', True),
            patch.object(self.wks, 'analyze', side_effect=fake_analyze) as mock_analyze,
        ):
            result = dispatch(self.session, self.reg, 'scan')

        mock_analyze.assert_called_once()
        self.assertTrue(result.ok)
        by_status = {it.data['path']: it.status for it in result.items}
        self.assertEqual('identified', by_status[identified.filename])
        self.assertEqual('no_match', by_status[missed.filename])
        # The matched album is minted.
        album_handle = self.session.handle_for(album)
        self.assertIn(album_handle, result.mints)
