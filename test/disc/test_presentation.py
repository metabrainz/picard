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


from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.disc.presentation import (
    DiscPresentation,
    disc_presentation,
    set_disc_presentation_sink,
)


class DiscPresentationTest(PicardTestCase):
    def test_accessor_is_stable(self):
        self.assertIs(disc_presentation(), disc_presentation())
        self.assertIsInstance(disc_presentation(), DiscPresentation)

    def test_lookup_finished_noop_without_sink(self):
        facade = DiscPresentation()
        self.assertFalse(facade.has_sink)
        facade.lookup_finished()  # must not raise

    def test_lookup_finished_forwards_to_sink(self):
        facade = DiscPresentation()
        sink = MagicMock()
        facade.set_sink(sink)
        facade.lookup_finished()
        sink.disc_lookup_finished.assert_called_once_with()

    def test_present_releases_forwards_to_sink(self):
        facade = DiscPresentation()
        sink = MagicMock()
        facade.set_sink(sink)
        disc = MagicMock()
        releases = [{'id': 'r1'}, {'id': 'r2'}]
        files = [MagicMock()]
        facade.present_releases(disc, releases, files_to_match=files)
        sink.present_disc_releases.assert_called_once_with(disc, releases, files_to_match=files)

    def test_present_releases_multiple_matches_shows_picker_even_with_skip_dialog(self):
        facade = DiscPresentation()
        sink = MagicMock()
        facade.set_sink(sink)
        disc = MagicMock()
        releases = [{'id': 'r1'}, {'id': 'r2'}]
        facade.present_releases(disc, releases, skip_dialog=True)
        # skip_dialog only skips the picker for a single match; ambiguous still prompts.
        sink.present_disc_releases.assert_called_once_with(disc, releases, files_to_match=None)

    def test_present_releases_skip_dialog_single_match_autoloads_with_disc_metadata(self):
        # The key fix: even with a GUI sink, a skip_dialog single match is
        # auto-loaded (no picker) AND carries the disc id + ISRCs.
        facade = DiscPresentation()
        sink = MagicMock()
        facade.set_sink(sink)
        disc = MagicMock()
        disc.id = 'disc-1'
        disc.isrcs = {1: 'USRC17607839'}
        files = [MagicMock()]
        with patch('picard.workspace.workspace') as mock_ws:
            album = mock_ws.return_value.load_album.return_value
            facade.present_releases(disc, [{'id': 'rel-1'}], files_to_match=files, skip_dialog=True)
            sink.present_disc_releases.assert_not_called()
            mock_ws.return_value.load_album.assert_called_once_with(
                'rel-1', discid='disc-1', disc_isrcs={1: 'USRC17607839'}
            )
            mock_ws.return_value.move_files_to_album.assert_called_once_with(files, album=album)

    def test_set_sink_none_reverts(self):
        self.addCleanup(set_disc_presentation_sink, None)
        set_disc_presentation_sink(MagicMock())
        self.assertTrue(disc_presentation().has_sink)
        set_disc_presentation_sink(None)
        self.assertFalse(disc_presentation().has_sink)


class DiscPresentationHeadlessAutoLoadTest(PicardTestCase):
    """Without a sink, present_releases auto-loads a single unambiguous match."""

    def _disc(self):
        disc = MagicMock()
        disc.id = 'disc-1'
        disc.isrcs = {}
        return disc

    def test_single_match_loads_and_matches_files(self):
        facade = DiscPresentation()
        disc = self._disc()
        files = [MagicMock()]
        with patch('picard.workspace.workspace') as mock_ws:
            album = mock_ws.return_value.load_album.return_value
            facade.present_releases(disc, [{'id': 'rel-1'}], files_to_match=files)
            mock_ws.return_value.load_album.assert_called_once_with('rel-1', discid='disc-1', disc_isrcs={})
            mock_ws.return_value.move_files_to_album.assert_called_once_with(files, album=album)

    def test_present_releases_records_last_loaded_album(self):
        facade = DiscPresentation()
        disc = self._disc()
        with patch('picard.workspace.workspace') as mock_ws:
            album = mock_ws.return_value.load_album.return_value
            self.assertIsNone(facade.last_loaded_album)
            returned = facade.present_releases(disc, [{'id': 'rel-1'}])
            self.assertIs(album, returned)
            self.assertIs(album, facade.last_loaded_album)

    def test_reset_last_loaded_clears_it(self):
        facade = DiscPresentation()
        disc = self._disc()
        with patch('picard.workspace.workspace'):
            facade.present_releases(disc, [{'id': 'rel-1'}])
            self.assertIsNotNone(facade.last_loaded_album)
        facade.reset_last_loaded()
        self.assertIsNone(facade.last_loaded_album)

    def test_no_match_records_none(self):
        facade = DiscPresentation()
        disc = self._disc()
        facade.last_loaded_album = object()  # stale value from a prior lookup
        with patch('picard.workspace.workspace') as mock_ws:
            returned = facade.present_releases(disc, [])
            self.assertIsNone(returned)
            self.assertIsNone(facade.last_loaded_album)
            mock_ws.return_value.load_album.assert_not_called()

    def test_single_match_without_files_loads_only(self):
        facade = DiscPresentation()
        disc = self._disc()
        with patch('picard.workspace.workspace') as mock_ws:
            facade.present_releases(disc, [{'id': 'rel-1'}])
            mock_ws.return_value.load_album.assert_called_once_with('rel-1', discid='disc-1', disc_isrcs={})
            mock_ws.return_value.move_files_to_album.assert_not_called()

    def test_no_match_loads_nothing(self):
        facade = DiscPresentation()
        with patch('picard.workspace.workspace') as mock_ws:
            facade.present_releases(self._disc(), [])
            mock_ws.return_value.load_album.assert_not_called()

    def test_ambiguous_match_loads_nothing(self):
        facade = DiscPresentation()
        with patch('picard.workspace.workspace') as mock_ws:
            facade.present_releases(self._disc(), [{'id': 'r1'}, {'id': 'r2'}])
            mock_ws.return_value.load_album.assert_not_called()

    def test_match_without_id_loads_nothing(self):
        facade = DiscPresentation()
        with patch('picard.workspace.workspace') as mock_ws:
            facade.present_releases(self._disc(), [{'title': 'no id'}])
            mock_ws.return_value.load_album.assert_not_called()
