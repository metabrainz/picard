# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2025-2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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


from functools import partial
from queue import (
    Empty,
    Queue,
)
import time
from unittest.mock import (
    Mock,
    patch,
)

from PyQt6.QtCore import (
    QCoreApplication,
    QObject,
    QThreadPool,
)
from PyQt6.QtTest import QTest

from test.picardtestcase import PicardTestCase

from picard.util import thread


def mock_function():
    return 1


def mock_exception():
    raise Exception


class MainEventInterceptor(QObject):
    def eventFilter(self, obj, event):
        if isinstance(event, thread.ProxyToMainEvent):
            event.run()
            event.accept()
            return True
        return super().eventFilter(obj, event)


class ThreadTest(PicardTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = QCoreApplication.instance()
        if cls.app is None:
            cls.app = QCoreApplication([])
        cls.threadpool = QThreadPool()
        cls.event_interceptor = MainEventInterceptor()

    def setUp(self):
        super().setUp()
        self.tagger = self.app
        self.tagger.installEventFilter(self.event_interceptor)
        self.result_queue = Queue()

    def tearDown(self):
        super().tearDown()
        self.tagger.removeEventFilter(self.event_interceptor)

    def _send_task_result(self, result=None, error=None):
        if not result and not error:
            return
        self.result_queue.put((result, error))

    def _get_task_result(self):
        while True:
            try:
                return self.result_queue.get_nowait()
            except Empty:
                # necessary to process Qt events sent by other threads
                QTest.qWait(100)  # type: ignore[call-arg]

    def test_run_task(self):
        thread.run_task(mock_function, self._send_task_result, thread_pool=self.threadpool)
        result, error = self._get_task_result()
        self.assertEqual(result, 1)
        self.assertIsNone(error)
        thread.run_task(mock_exception, self._send_task_result, thread_pool=self.threadpool)
        result, error = self._get_task_result()
        self.assertIsNone(result)
        self.assertIsInstance(error, Exception)

    def test_to_main(self):
        thread.to_main(self._send_task_result, result="test", error=None)
        result, error = self._get_task_result()
        self.assertEqual(result, "test")
        self.assertIsNone(error)
        thread.to_main(self._send_task_result, result=None, error=Exception())
        result, error = self._get_task_result()
        self.assertIsNone(result)
        self.assertIsInstance(error, Exception)

    def test_to_main_with_blocking(self):
        func = partial(thread.to_main_with_blocking, self._send_task_result, result="test", error=None)
        thread.run_task(func, thread_pool=self.threadpool)
        result, error = self._get_task_result()
        self.assertEqual(result, "test")
        self.assertIsNone(error)
        func = partial(thread.to_main_with_blocking, self._send_task_result, result=None, error=Exception())
        thread.run_task(func, thread_pool=self.threadpool)
        result, error = self._get_task_result()
        self.assertIsNone(result)
        self.assertIsInstance(error, Exception)

    def test_task_counter(self):
        task_counter = thread.TaskCounter()
        self.assertEqual(task_counter.count, 0)
        for i in range(3):
            thread.run_task(self._get_task_result, thread_pool=self.threadpool, task_counter=task_counter)
            self.assertEqual(task_counter.count, i + 1)
        for i in range(3):
            self.result_queue.put(i)
        task_counter.wait_for_tasks()
        self.assertEqual(task_counter.count, 0)

    def test_process_in_batches_rejects_non_positive_time_budget(self):
        for bad_budget in (0, -1, -0.5):
            with self.subTest(bad_budget=bad_budget):
                with self.assertRaises(ValueError):
                    thread.process_in_batches([1, 2, 3], mock_function, "test", time_budget=bad_budget)

    def test_pending_batches_counts_the_chains_waiting_for_the_event_loop(self):
        processed = []

        def slow(item):
            time.sleep(0.01)
            processed.append(item)

        on_complete = Mock()
        self.assertEqual(0, thread.pending_batches())
        # Two items do not fit in a 5 ms batch: the rest waits for the event loop.
        thread.process_in_batches([1, 2, 3, 4], slow, "test", time_budget=0.005, on_complete=on_complete)
        self.assertEqual(1, thread.pending_batches())
        self.assertLess(len(processed), 4)
        on_complete.assert_not_called()
        while thread.pending_batches():
            QTest.qWait(5)
        self.assertEqual([1, 2, 3, 4], processed)
        on_complete.assert_called_once_with()

    def test_pending_batches_is_zero_when_the_first_batch_does_it_all(self):
        thread.process_in_batches([1, 2, 3], Mock(), "test")
        self.assertEqual(0, thread.pending_batches())

    def test_pending_batches_does_not_stay_above_zero_when_a_batch_fails(self):
        def fail(item):
            raise RuntimeError("boom")

        with patch.object(thread, '_pending_batches', 1):
            with self.assertRaises(RuntimeError):
                thread._next_batch([1, 2], fail, "test", 0.05, None)
            self.assertEqual(0, thread.pending_batches())

    def test_process_in_batches_processes_all_items(self):
        processed = []
        on_complete = Mock()
        thread.process_in_batches([1, 2, 3], processed.append, "test", on_complete=on_complete)
        QTest.qWait(50)
        self.assertEqual(processed, [1, 2, 3])
        on_complete.assert_called_once_with()
