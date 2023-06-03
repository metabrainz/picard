# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2021 Laurent Monin
# Copyright (C) 2019-2022 Philipp Wolfer
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


import sys
from unittest.mock import (
    MagicMock,
    patch,
)

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkProxy

from test.picardtestcase import PicardTestCase

from picard import config
from picard.webservice import (
    RequestPriorityQueue,
    RequestTask,
    UnknownResponseParserError,
    WebService,
    WSRequest,
    ratecontrol,
)


PROXY_SETTINGS = {
    "use_proxy": True,
    "proxy_type": 'http',
    "proxy_server_host": '127.0.0.1',
    "proxy_server_port": 3128,
    "proxy_username": 'user',
    "proxy_password": 'password',
    "network_transfer_timeout_seconds": 30,
}


def dummy_handler(*args, **kwargs):
    """Dummy handler method for tests"""


class WebServiceTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values({
            'use_proxy': False,
            'server_host': '',
            'network_transfer_timeout_seconds': 30,
        })
        self.ws = WebService()

    @patch.object(WebService, 'add_task')
    def test_webservice_method_calls(self, mock_add_task):
        host = "abc.xyz"
        port = 80
        path = ""
        handler = dummy_handler
        data = None

        def get_wsreq(mock_add_task):
            return mock_add_task.call_args[0][1]

        self.ws.get(host, port, path, handler)
        self.assertEqual(1, mock_add_task.call_count)
        self.assertEqual(host, get_wsreq(mock_add_task).host)
        self.assertEqual(port, get_wsreq(mock_add_task).port)
        self.assertIn("GET", get_wsreq(mock_add_task).method)
        self.ws.post(host, port, path, data, handler)
        self.assertIn("POST", get_wsreq(mock_add_task).method)
        self.ws.put(host, port, path, data, handler)
        self.assertIn("PUT", get_wsreq(mock_add_task).method)
        self.ws.delete(host, port, path, handler)
        self.assertIn("DELETE", get_wsreq(mock_add_task).method)
        self.ws.download(host, port, path, handler)
        self.assertIn("GET", get_wsreq(mock_add_task).method)
        self.assertEqual(5, mock_add_task.call_count)


class WebServiceTaskTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values({
            'use_proxy': False,
            'network_transfer_timeout_seconds': 30,
        })
        self.ws = WebService()
        self.queue = self.ws._queue = MagicMock()

        # Patching the QTimers since they can only be started in a QThread
        self.ws._timer_run_next_task = MagicMock()
        self.ws._timer_count_pending_requests = MagicMock()

    def test_add_task(self):
        request = WSRequest(
            method='GET',
            qurl=QUrl('http://abc.xyz'),
            handler=dummy_handler,
        )
        func = 1
        task = self.ws.add_task(func, request)
        self.assertEqual((request.get_host_key(), func, 0), task)
        self.ws._queue.add_task.assert_called_with(task, False)
        request.important = True
        task = self.ws.add_task(func, request)
        self.ws._queue.add_task.assert_called_with(task, True)

    def test_add_task_calls_timers(self):
        mock_timer1 = self.ws._timer_run_next_task
        mock_timer2 = self.ws._timer_count_pending_requests
        request = WSRequest(
            method='GET',
            qurl=QUrl('http://abc.xyz'),
            handler=dummy_handler,
        )
        self.ws.add_task(0, request)
        mock_timer1.start.assert_not_called()
        mock_timer2.start.assert_not_called()

        # Test if timer start was called in case it was inactive
        mock_timer1.isActive.return_value = False
        mock_timer2.isActive.return_value = False
        self.ws.add_task(0, request)
        mock_timer1.start.assert_called_with(0)
        mock_timer2.start.assert_called_with(0)

    def test_remove_task(self):
        task = RequestTask(('example.com', 80), dummy_handler, priority=0)
        self.ws.remove_task(task)
        self.ws._queue.remove_task.assert_called_with(task)

    def test_remove_task_calls_timers(self):
        mock_timer = self.ws._timer_count_pending_requests
        task = RequestTask(('example.com', 80), dummy_handler, priority=0)
        self.ws.remove_task(task)
        mock_timer.start.assert_not_called()
        mock_timer.isActive.return_value = False
        self.ws.remove_task(task)
        mock_timer.start.assert_called_with(0)

    def test_run_next_task(self):
        mock_timer = self.ws._timer_run_next_task
        self.ws._queue.run_ready_tasks.return_value = sys.maxsize
        self.ws._run_next_task()
        self.ws._queue.run_ready_tasks.assert_called()
        mock_timer.start.assert_not_called()

    def test_run_next_task_starts_next(self):
        mock_timer = self.ws._timer_run_next_task
        delay = 42
        self.ws._queue.run_ready_tasks.return_value = delay
        self.ws._run_next_task()
        self.ws._queue.run_ready_tasks.assert_called()
        mock_timer.start.assert_called_with(42)


class RequestTaskTest(PicardTestCase):

    def test_from_request(self):
        request = WSRequest(
            method='GET',
            qurl=QUrl('https://example.com'),
            handler=dummy_handler,
            priority=True,
        )
        func = 1
        task = RequestTask.from_request(request, func)
        self.assertEqual(request.get_host_key(), task.hostkey)
        self.assertEqual(func, task.func)
        self.assertEqual(1, task.priority)
        self.assertEqual((request.get_host_key(), func, 1), task)


class RequestPriorityQueueTest(PicardTestCase):

    def test_add_task(self):
        queue = RequestPriorityQueue(ratecontrol)
        key = ("abc.xyz", 80)

        task1 = RequestTask(key, dummy_handler, priority=0)
        queue.add_task(task1)
        task2 = RequestTask(key, dummy_handler, priority=1)
        queue.add_task(task2)
        task3 = RequestTask(key, dummy_handler, priority=0)
        queue.add_task(task3, important=True)
        task4 = RequestTask(key, dummy_handler, priority=1)
        queue.add_task(task4, important=True)

        # Test if 2 requests were added in each queue
        self.assertEqual(len(queue._queues[0][key]), 2)
        self.assertEqual(len(queue._queues[1][key]), 2)

        # Test if important request was added ahead in the queue
        self.assertEqual(queue._queues[0][key][0], task3.func)
        self.assertEqual(queue._queues[0][key][1], task1.func)
        self.assertEqual(queue._queues[1][key][0], task4.func)
        self.assertEqual(queue._queues[1][key][1], task2.func)

    def test_remove_task(self):
        queue = RequestPriorityQueue(ratecontrol)
        key = ("abc.xyz", 80)

        # Add a task and check for its existence
        task = RequestTask(key, dummy_handler, priority=0)
        task = queue.add_task(task)
        self.assertIn(key, queue._queues[0])
        self.assertEqual(len(queue._queues[0][key]), 1)

        # Remove the task and check
        queue.remove_task(task)
        self.assertIn(key, queue._queues[0])
        self.assertEqual(len(queue._queues[0][key]), 0)

        # Try to remove a non existing task and check for errors
        non_existing_task = (1, "a", "b")
        queue.remove_task(non_existing_task)

    def test_run_task(self):
        mock_ratecontrol = MagicMock()
        delay_func = mock_ratecontrol.get_delay_to_next_request = MagicMock()

        queue = RequestPriorityQueue(mock_ratecontrol)
        key = ("abc.xyz", 80)

        # Patching the get delay function to delay the 2nd task on queue to the next call
        delay_func.side_effect = [(False, 0), (True, 0), (False, 0), (False, 0), (False, 0), (False, 0)]
        func1 = MagicMock()
        task1 = RequestTask(key, func1, priority=0)
        queue.add_task(task1)
        func2 = MagicMock()
        task2 = RequestTask(key, func2, priority=1)
        queue.add_task(task2)
        task3 = RequestTask(key, func1, priority=0)
        queue.add_task(task3)
        task4 = RequestTask(key, func1, priority=0)
        queue.add_task(task4)

        # Ensure no tasks are run before run_next_task is called
        self.assertEqual(func1.call_count, 0)
        queue.run_ready_tasks()

        # Ensure priority task is run first
        self.assertEqual(func2.call_count, 1)
        self.assertEqual(func1.call_count, 0)
        self.assertIn(key, queue._queues[1])

        # Ensure that the calls are run as expected
        queue.run_ready_tasks()
        self.assertEqual(func1.call_count, 1)

        # Checking if the cleanup occurred on the prio queue
        self.assertNotIn(key, queue._queues[1])

        # Check the call counts on proper execution of tasks
        queue.run_ready_tasks()
        self.assertEqual(func1.call_count, 2)
        queue.run_ready_tasks()
        self.assertEqual(func1.call_count, 3)

        # Ensure that the clean up happened on the normal queue
        queue.run_ready_tasks()
        self.assertEqual(func1.call_count, 3)
        self.assertNotIn(key, queue._queues[0])

    def test_count(self):
        queue = RequestPriorityQueue(ratecontrol)
        key = ("abc.xyz", 80)

        self.assertEqual(0, queue.count())
        task1 = RequestTask(key, dummy_handler, priority=0)
        queue.add_task(task1)
        self.assertEqual(1, queue.count())
        task2 = RequestTask(key, dummy_handler, priority=1)
        queue.add_task(task2)
        self.assertEqual(2, queue.count())
        task3 = RequestTask(key, dummy_handler, priority=0)
        queue.add_task(task3, important=True)
        self.assertEqual(3, queue.count())
        task4 = RequestTask(key, dummy_handler, priority=1)
        queue.add_task(task4, important=True)
        self.assertEqual(4, queue.count())
        queue.remove_task(task1)
        self.assertEqual(3, queue.count())
        queue.remove_task(task2)
        self.assertEqual(2, queue.count())
        queue.remove_task(task3)
        self.assertEqual(1, queue.count())
        queue.remove_task(task4)
        self.assertEqual(0, queue.count())


class WebServiceProxyTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values(PROXY_SETTINGS)

    def test_proxy_setup(self):
        proxy_types = [
            ('http', QNetworkProxy.ProxyType.HttpProxy),
            ('socks', QNetworkProxy.ProxyType.Socks5Proxy),
        ]
        for proxy_type, expected_qt_type in proxy_types:
            config.setting['proxy_type'] = proxy_type
            ws = WebService()
            proxy = ws.manager.proxy()
            self.assertEqual(proxy.type(), expected_qt_type)
            self.assertEqual(proxy.user(), PROXY_SETTINGS['proxy_username'])
            self.assertEqual(proxy.password(), PROXY_SETTINGS['proxy_password'])
            self.assertEqual(proxy.hostName(), PROXY_SETTINGS['proxy_server_host'])
            self.assertEqual(proxy.port(), PROXY_SETTINGS['proxy_server_port'])


class ParserHookTest(PicardTestCase):

    def test_parser_hook(self):
        WebService.add_parser('A', 'mime', 'parser')

        self.assertIn('A', WebService.PARSERS)
        self.assertEqual(WebService.PARSERS['A'].mimetype, 'mime')
        self.assertEqual(WebService.PARSERS['A'].mimetype, WebService.get_response_mimetype('A'))
        self.assertEqual(WebService.PARSERS['A'].parser, 'parser')
        self.assertEqual(WebService.PARSERS['A'].parser, WebService.get_response_parser('A'))

        with self.assertRaises(UnknownResponseParserError):
            WebService.get_response_parser('B')
        with self.assertRaises(UnknownResponseParserError):
            WebService.get_response_mimetype('B')
