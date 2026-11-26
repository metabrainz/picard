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

"""Integration tests of ``Workspace.save`` with the real batching.

Unlike the unit tests in ``test_workspace.py``, nothing is mocked between
``Workspace.save``, ``thread.process_in_batches`` and ``File.save`` /
``File._saving_finished``. Only the thread pool (writes are queued, then
finished by the test in a chosen order) and the clock (a fake one, so the
number of files per batch is deterministic) are replaced.
"""

from itertools import count
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from PyQt6.QtTest import QTest

from test.picardtestcase import PicardTestCase

from picard.file import File
from picard.util import thread
from picard.workspace import workspace


class SaveFile(File):
    EXTENSIONS = ('.mp3',)

    def __init__(self, filename):
        super().__init__(filename)
        # Observe refreshes without a real UI item.
        self.update_item = MagicMock()

    def selection_refreshes(self):
        return [c for c in self.update_item.call_args_list if c.kwargs.get('update_selection', True)]


class WorkspaceSaveDispatchTest(PicardTestCase):
    # The fake clock advances by 1 on every read, and a batch ends once it is
    # past the deadline: a budget of 3.5 lets 3 files start per batch.
    FILES_PER_BATCH = 3
    TIME_BUDGET = 3.5
    # Upper bound of event loop turns to wait for, so a bug cannot hang the suite.
    MAX_WAITS = 1000

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(
            {
                'clear_existing_tags': False,
                'preserve_images': False,
                'embed_only_one_front_image': False,
                'enabled_plugins': [],
                'enable_tag_saving': False,
                'rename_files': False,
                'move_files': False,
                'save_images_to_files': False,
                'delete_empty_dirs': False,
                'preserve_timestamps': False,
            }
        )
        self.tagger.save_thread_pool = MagicMock()
        self.wks = workspace()
        self.wks._saving_files_count = 0
        self.wks._saving_dirty_image_parents.clear()

        # Writes queued by File.save(), finished by the test: callbacks.
        self.queued = []
        patcher = patch('picard.file.thread.run_task', side_effect=self._queue_write)
        patcher.start()
        self.addCleanup(patcher.stop)

        clock = count()
        fake_time = Mock()
        fake_time.perf_counter.side_effect = lambda: float(next(clock))
        patcher = patch('picard.util.thread.time', fake_time)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(thread, '_BATCH_TIME_BUDGET', self.TIME_BUDGET)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch.object(self.wks, 'flush_saving_image_parents', wraps=self.wks.flush_saving_image_parents)
        self.mock_flush = patcher.start()
        self.addCleanup(patcher.stop)

    def _queue_write(self, func, callback, **kwargs):
        # callback is the bound File._saving_finished
        self.queued.append(callback)

    def _make_files(self, number):
        files = [SaveFile(f'/music/{i:02}.mp3') for i in range(number)]
        for file in files:
            self.wks.files[file.filename] = file
            self.addCleanup(self.wks.files.pop, file.filename, None)
        return files

    def _finish(self, callback):
        file = callback.__self__
        callback(result=file.filename)

    def _finish_all(self, order=None):
        callbacks, self.queued = self.queued, []
        for callback in order(callbacks) if order else callbacks:
            self._finish(callback)

    def _wait_for_dispatch(self):
        for _ in range(self.MAX_WAITS):
            if not thread.pending_batches():
                return
            QTest.qWait(1)
        self.fail('the dispatch did not finish')

    def _selection_refresh_count(self, files):
        return sum(len(file.selection_refreshes()) for file in files)

    def test_saves_are_started_in_several_batches(self):
        files = self._make_files(10)
        saved = self.wks.save(files)
        self.assertEqual(files, saved)
        # Only the first batch ran, the rest waits for the event loop.
        self.assertEqual(self.FILES_PER_BATCH, len(self.queued))
        self.assertEqual(1, thread.pending_batches())
        self._wait_for_dispatch()
        self.assertEqual(10, len(self.queued))
        self.assertEqual(
            [f.filename for f in files],
            [cb.__self__.filename for cb in self.queued],
        )

    def test_dispatch_hold_stays_until_the_last_batch(self):
        files = self._make_files(10)
        self.wks.save(files)
        # The write tasks queued so far, plus the dispatch hold.
        self.assertEqual(self.FILES_PER_BATCH + 1, self.wks._saving_files_count)
        self._wait_for_dispatch()
        self.assertEqual(10, len(self.queued))
        # Hold released once every save was started.
        self.assertEqual(10, self.wks._saving_files_count)

    def test_selection_refresh_runs_once_when_saves_finish_during_dispatch(self):
        files = self._make_files(10)
        self.wks.save(files)
        # The save thread is faster than the dispatch: everything queued so far
        # finishes before the next batch starts.
        for _ in range(self.MAX_WAITS):
            if not thread.pending_batches():
                break
            self._finish_all()
            self.assertEqual(0, self._selection_refresh_count(files), 'refresh ran before dispatch ended')
            QTest.qWait(1)
        else:
            self.fail('the dispatch did not finish')
        self._finish_all()
        self.assertEqual(0, self.wks._saving_files_count)
        self.assertEqual(1, self._selection_refresh_count(files))
        self.mock_flush.assert_called_once_with()

    def test_selection_refresh_runs_once_when_dispatch_ends_before_saves(self):
        files = self._make_files(10)
        self.wks.save(files)
        self._wait_for_dispatch()
        self.assertEqual(0, self._selection_refresh_count(files))
        self.mock_flush.assert_not_called()
        # Finish in reverse order: the refresh belongs to the last one to finish.
        self._finish_all(order=lambda callbacks: list(reversed(callbacks)))
        self.assertEqual(0, self.wks._saving_files_count)
        self.assertEqual(1, self._selection_refresh_count(files))
        self.assertEqual(1, len(files[0].selection_refreshes()))
        self.mock_flush.assert_called_once_with()

    def test_selection_refresh_runs_once_when_saves_end_mid_dispatch_then_after(self):
        files = self._make_files(10)
        self.wks.save(files)
        self._finish_all()
        self._wait_for_dispatch()
        self._finish_all()
        self.assertEqual(0, self.wks._saving_files_count)
        self.assertEqual(1, self._selection_refresh_count(files))
        self.mock_flush.assert_called_once_with()

    def test_file_removed_during_dispatch_is_not_saved(self):
        files = self._make_files(10)
        self.wks.save(files)
        # Removed while waiting for the event loop, as the user could do.
        removed = files[5]
        removed.state = File.State.REMOVED
        self._wait_for_dispatch()
        self.assertEqual(9, len(self.queued))
        self.assertNotIn(removed, [cb.__self__ for cb in self.queued])
        self._finish_all()
        self.assertEqual(0, self.wks._saving_files_count)
        self.assertEqual(1, self._selection_refresh_count(files))

    def test_last_file_removed_during_dispatch_does_not_break_the_batch_end(self):
        files = self._make_files(4)
        self.wks.save(files)
        files[-1].state = File.State.REMOVED
        self._wait_for_dispatch()
        self._finish_all()
        self.assertEqual(0, self.wks._saving_files_count)
        self.mock_flush.assert_called_once_with()
        self.assertEqual(0, len(files[-1].selection_refreshes()))

    def test_error_starting_one_save_does_not_block_the_batch_end(self):
        files = self._make_files(10)
        broken = files[4]
        broken.save = MagicMock(side_effect=RuntimeError('plugin error'))
        self.wks.save(files)
        self._wait_for_dispatch()
        self.assertEqual(9, len(self.queued))
        self._finish_all()
        # Not left open: a later save can still end its batch.
        self.assertEqual(0, self.wks._saving_files_count)
        self.assertEqual(1, self._selection_refresh_count(files))
        self.assertEqual(File.State.NORMAL, broken.state)

    def test_pending_batches_covers_the_whole_dispatch(self):
        # Headless run_until_idle relies on this to not stop half way.
        files = self._make_files(10)
        self.wks.save(files)
        seen = []
        for _ in range(self.MAX_WAITS):
            if not thread.pending_batches():
                break
            seen.append(len(self.queued))
            QTest.qWait(1)
        self.assertEqual(10, len(self.queued))
        self.assertEqual(sorted(seen), seen)
        self.assertLess(seen[0], 10)
