# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from functools import partial
from queue import (
    Empty,
    Queue,
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
        cls.app = QCoreApplication([])
        cls.threadpool = QThreadPool()
        cls.event_interceptor = MainEventInterceptor()

    def setUp(self):
        super().setUp()
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
                QTest.qWait(100)

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
