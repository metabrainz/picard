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

"""Tagger._file_loaded: what happens when a file finishes loading."""

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.file import File
from picard.tagger import Tagger


class TaggerFileLoadedTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({'cluster_new_files': False})
        self.tagger = MagicMock(spec=Tagger)
        self.tagger.window = MagicMock()
        self.tagger.unclustered_files = MagicMock()
        self.tagger._pending_files_count = 1
        self.tagger._restoring_session = False

    @staticmethod
    def _file(state=File.State.NORMAL, error=False):
        file = MagicMock(state=state)
        file.has_error.return_value = error
        return file

    def _loaded(self, file, **kwargs):
        Tagger._file_loaded(self.tagger, file, **kwargs)

    def test_a_removed_file_settles_the_pending_count_and_is_not_placed(self):
        removed = self._file(state=File.State.REMOVED)
        self._loaded(removed)
        self.assertEqual(0, self.tagger._pending_files_count)
        self.tagger.window.suspend_while_loading_exit.assert_called_once_with()
        self.tagger.move_file.assert_not_called()
        self.tagger.unclustered_files.add_file.assert_not_called()
        removed.remove.assert_not_called()
