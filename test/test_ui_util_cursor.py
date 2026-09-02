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

from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.const import BUSY_CURSOR_FLASH_DELAY_MS
from picard.tagger import Tagger

from picard.ui.util import flash_busy_cursor


class FlashBusyCursorTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.ui.util')

    def test_shows_cursor_and_schedules_restore_with_default_delay(self):
        with patch('picard.ui.util.QtCore.QTimer.singleShot') as mock_single_shot:
            flash_busy_cursor()
        self.tagger.set_wait_cursor.assert_called_once_with()
        # Restore is scheduled, not called synchronously.
        self.tagger.restore_cursor.assert_not_called()
        mock_single_shot.assert_called_once_with(BUSY_CURSOR_FLASH_DELAY_MS, self.tagger.restore_cursor)

    def test_custom_delay_is_used(self):
        with patch('picard.ui.util.QtCore.QTimer.singleShot') as mock_single_shot:
            flash_busy_cursor(123)
        mock_single_shot.assert_called_once_with(123, self.tagger.restore_cursor)

    def test_scheduled_callback_restores_cursor(self):
        # Verify the callback handed to the timer actually restores the cursor.
        captured = {}

        def fake_single_shot(msecs, callback):
            captured['callback'] = callback

        with patch('picard.ui.util.QtCore.QTimer.singleShot', side_effect=fake_single_shot):
            flash_busy_cursor()

        self.tagger.restore_cursor.assert_not_called()
        captured['callback']()
        self.tagger.restore_cursor.assert_called_once_with()


class TaggerClusterActionsFlashTest(PicardTestCase):
    """Cluster-panel actions (cluster, lookup/autotag, analyze) should flash the
    busy cursor once per user action to acknowledge the async work.
    """

    def setUp(self):
        super().setUp()
        # The Tagger methods call the module-level flash_busy_cursor() imported
        # into picard.tagger; patch it there and assert on the mock.
        patcher = patch('picard.tagger.flash_busy_cursor')
        self.mock_flash = patcher.start()
        self.addCleanup(patcher.stop)

    def _mock_self(self):
        # Use a mock in place of a real Tagger so we can call the unbound
        # methods without constructing the whole application.
        return MagicMock(spec=Tagger)

    def test_cluster_flashes_when_files_present(self):
        tagger = self._mock_self()
        files = (MagicMock(), MagicMock())
        with (
            patch('picard.tagger.iter_files_from_objects', return_value=iter(files)),
            patch('picard.tagger.thread'),
        ):
            Tagger.cluster(tagger, object())
        self.mock_flash.assert_called_once_with()

    def test_cluster_does_not_flash_when_no_files(self):
        tagger = self._mock_self()
        with (
            patch('picard.tagger.iter_files_from_objects', return_value=iter(())),
            patch('picard.tagger.thread'),
        ):
            Tagger.cluster(tagger, object())
        self.mock_flash.assert_not_called()

    def test_autotag_flashes_once_for_batch(self):
        tagger = self._mock_self()
        obj1 = MagicMock(can_autotag=True)
        obj2 = MagicMock(can_autotag=True)
        Tagger.autotag(tagger, [obj1, obj2])
        self.mock_flash.assert_called_once_with()
        obj1.lookup_metadata.assert_called_once_with()
        obj2.lookup_metadata.assert_called_once_with()

    def test_autotag_does_not_flash_when_nothing_taggable(self):
        tagger = self._mock_self()
        obj = MagicMock(can_autotag=False)
        Tagger.autotag(tagger, [obj])
        self.mock_flash.assert_not_called()
        obj.lookup_metadata.assert_not_called()

    def test_analyze_flashes_once_for_batch(self):
        tagger = self._mock_self()
        tagger.use_acoustid = True
        tagger._acoustid = MagicMock()
        file1 = MagicMock(can_analyze=True)
        file2 = MagicMock(can_analyze=True)
        with patch('picard.tagger.iter_files_from_objects', return_value=iter((file1, file2))):
            Tagger.analyze(tagger, object())
        self.mock_flash.assert_called_once_with()

    def test_analyze_does_not_flash_when_acoustid_disabled(self):
        tagger = self._mock_self()
        tagger.use_acoustid = False
        with patch('picard.tagger.iter_files_from_objects', return_value=iter((MagicMock(),))):
            Tagger.analyze(tagger, object())
        self.mock_flash.assert_not_called()

    def test_analyze_does_not_flash_when_nothing_analyzable(self):
        tagger = self._mock_self()
        tagger.use_acoustid = True
        file = MagicMock(can_analyze=False)
        with patch('picard.tagger.iter_files_from_objects', return_value=iter((file,))):
            Tagger.analyze(tagger, object())
        self.mock_flash.assert_not_called()


class TaggerSearchFlashTest(PicardTestCase):
    """Tagger.search should flash only when it dispatches async work, not when
    it falls back to opening a modal search dialog (which is its own feedback).
    """

    def setUp(self):
        super().setUp()
        patcher = patch('picard.tagger.flash_busy_cursor')
        self.mock_flash = patcher.start()
        self.addCleanup(patcher.stop)

    def _mock_self(self, lookup):
        tagger = MagicMock(spec=Tagger)
        tagger.get_file_lookup.return_value = lookup
        tagger.window = MagicMock()
        return tagger

    def test_builtin_search_flashes_on_mbid_match(self):
        self.set_config_values({'builtin_search': True})
        lookup = MagicMock()
        lookup.mbid_lookup.return_value = True  # dispatched an async load
        tagger = self._mock_self(lookup)
        Tagger.search(tagger, 'some-mbid', 'album')
        self.mock_flash.assert_called_once_with()

    def test_builtin_search_does_not_flash_on_dialog_fallback(self):
        self.set_config_values({'builtin_search': True})
        lookup = MagicMock()
        lookup.mbid_lookup.return_value = False  # falls back to modal dialog
        tagger = self._mock_self(lookup)
        with patch('picard.tagger.AlbumSearchDialog') as mock_dialog:
            Tagger.search(tagger, 'Radiohead', 'album')
            mock_dialog.assert_called_once_with(tagger.window)
        self.mock_flash.assert_not_called()

    def test_browser_search_flashes(self):
        self.set_config_values({'builtin_search': False})
        lookup = MagicMock()
        tagger = self._mock_self(lookup)
        Tagger.search(tagger, 'Radiohead', 'album')
        self.mock_flash.assert_called_once_with()
        lookup.search_entity.assert_called_once()

    def test_force_browser_flashes_even_with_builtin_search(self):
        self.set_config_values({'builtin_search': True})
        lookup = MagicMock()
        tagger = self._mock_self(lookup)
        Tagger.search(tagger, 'Radiohead', 'album', force_browser=True)
        self.mock_flash.assert_called_once_with()
        lookup.search_entity.assert_called_once()

    def test_unknown_search_type_does_nothing(self):
        lookup = MagicMock()
        tagger = self._mock_self(lookup)
        Tagger.search(tagger, 'x', 'not-a-type')
        self.mock_flash.assert_not_called()
        lookup.mbid_lookup.assert_not_called()
