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

from picard.ui.util import (
    busy_cursor_start,
    busy_cursor_stop,
    flash_busy_cursor,
)


class BusyCursorPrimitivesTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.ui.util')

    def test_start_pushes_wait_cursor(self):
        busy_cursor_start()
        self.tagger.setOverrideCursor.assert_called_once()

    def test_stop_restores_cursor(self):
        busy_cursor_stop()
        self.tagger.restoreOverrideCursor.assert_called_once_with()


class FlashBusyCursorTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.ui.util')

    def test_shows_cursor_and_schedules_stop_with_default_delay(self):
        with patch('picard.ui.util.QtCore.QTimer.singleShot') as mock_single_shot:
            flash_busy_cursor()
        # The busy cursor is shown immediately (start), and stop is scheduled.
        self.tagger.setOverrideCursor.assert_called_once()
        self.tagger.restoreOverrideCursor.assert_not_called()
        mock_single_shot.assert_called_once_with(BUSY_CURSOR_FLASH_DELAY_MS, busy_cursor_stop)

    def test_custom_delay_is_used(self):
        with patch('picard.ui.util.QtCore.QTimer.singleShot') as mock_single_shot:
            flash_busy_cursor(123)
        mock_single_shot.assert_called_once_with(123, busy_cursor_stop)

    def test_scheduled_callback_restores_cursor(self):
        # Verify the callback handed to the timer actually restores the cursor.
        captured = {}

        def fake_single_shot(msecs, callback):
            captured['callback'] = callback

        with patch('picard.ui.util.QtCore.QTimer.singleShot', side_effect=fake_single_shot):
            flash_busy_cursor()

        self.tagger.restoreOverrideCursor.assert_not_called()
        captured['callback']()
        self.tagger.restoreOverrideCursor.assert_called_once_with()


class TaggerSearchFlashTest(PicardTestCase):
    """Tagger.search should flash only when it dispatches async work, not when
    it falls back to opening a modal search dialog (which is its own feedback).
    """

    def setUp(self):
        super().setUp()
        patcher = patch('picard.tagger.notifier')
        self.mock_flash = patcher.start().return_value.flash_busy
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
