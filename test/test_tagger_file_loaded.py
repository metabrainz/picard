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


class TaggerAutoClusterAfterLastFileTest(PicardTestCase):
    """cluster_new_files clusters the unmatched files once the last load is done.

    The loads finish in any order, so it must not matter what kind of file is
    the last one: a file that failed to load, one that turned out unsupported
    or one removed meanwhile must not stop the others from being clustered
    (PICARD-3542).
    """

    def setUp(self):
        super().setUp()
        self.set_config_values({'cluster_new_files': True, 'ignore_file_mbids': True, 'analyze_new_files': False})
        self._reset()

    def _reset(self):
        self.tagger = MagicMock(spec=Tagger)
        self.tagger.window = MagicMock()
        self.tagger.unclustered_files = MagicMock()
        # Nothing to place the files on: they are left over, as without MBIDs.
        self.tagger.move_file.return_value = self.tagger.unclustered_files
        self.tagger._pending_files_count = 3
        self.tagger._restoring_session = False
        self.unmatched = []
        self.good = [self._file(), self._file()]

    @staticmethod
    def _file(state=File.State.NORMAL, error=False):
        file = MagicMock(state=state)
        file.has_error.return_value = error
        return file

    def _finish(self, *finished, **kwargs):
        for file in finished:
            Tagger._file_loaded(self.tagger, file, unmatched_files=self.unmatched, **kwargs)

    def test_clusters_when_the_last_file_failed_to_load(self):
        self._finish(*self.good, self._file(state=File.State.ERROR, error=True))
        self.tagger.cluster.assert_called_once_with(self.good)

    def test_clusters_when_the_last_file_was_removed_while_loading(self):
        self._finish(*self.good, self._file(state=File.State.REMOVED))
        self.tagger.cluster.assert_called_once_with(self.good)

    def test_clusters_when_the_last_file_was_found_unsupported(self):
        self._finish(*self.good)
        self._finish(self._file(), remove_file=True)
        self.tagger.cluster.assert_called_once_with(self.good)

    def test_clusters_once_whatever_the_order(self):
        for position in range(3):
            with self.subTest(failed_at=position):
                self._reset()
                failed = self._file(state=File.State.ERROR, error=True)
                order = list(self.good)
                order.insert(position, failed)
                self._finish(*order)
                self.tagger.cluster.assert_called_once_with(self.good)

    def test_a_file_removed_after_it_was_placed_is_not_clustered(self):
        gone = self._file()
        self._finish(gone)
        gone.state = File.State.REMOVED  # removed by the user while the others load
        self._finish(*self.good)
        self.tagger.cluster.assert_called_once_with(self.good)

    def test_nothing_to_cluster_when_every_unmatched_file_was_removed(self):
        gone = self._file()
        self._finish(gone)
        gone.state = File.State.REMOVED
        self._finish(self._file(error=True), self._file(error=True))
        self.tagger.cluster.assert_not_called()

    def test_does_not_cluster_while_files_are_still_pending(self):
        self._finish(*self.good)
        self.tagger.cluster.assert_not_called()

    def test_does_not_cluster_when_the_setting_is_off(self):
        self.set_config_values({'cluster_new_files': False})
        self._finish(*self.good, self._file(state=File.State.ERROR, error=True))
        self.tagger.cluster.assert_not_called()
