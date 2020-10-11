# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2018 Wieland Hoffmann
# Copyright (C) 2018 Laurent Monin
# Copyright (C) 2019-2020 Philipp Wolfer
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


from unittest.mock import (
    MagicMock,
    patch,
)

from PyQt5.QtNetwork import QNetworkProxy

from test.picardtestcase import PicardTestCase

from picard import config
from picard.webservice import (
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


class WebServiceTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        config.setting = {
            'use_proxy': False,
            'server_host': '',
            'network_transfer_timeout_seconds': 30,
        }
        self.ws = WebService()

    def tearDown(self):
        del self.ws
        config.setting = {}

    @patch.object(WebService, 'add_task')
    def test_webservice_method_calls(self, mock_add_task):
        host = "abc.xyz"
        port = 80
        path = ""
        handler = None
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
        config.setting = {
            'use_proxy': False,
            'network_transfer_timeout_seconds': 30,
        }
        self.ws = WebService()

        # Patching the QTimers since they can only be started in a QThread
        self.ws._timer_run_next_task = MagicMock()
        self.ws._timer_count_pending_requests = MagicMock()

    def tearDown(self):
        del self.ws
        config.setting = {}

    def test_add_task(self):

        mock_timer1 = self.ws._timer_run_next_task
        mock_timer2 = self.ws._timer_count_pending_requests

        host = "abc.xyz"
        port = 80
        request = WSRequest("", host, port, "", None)
        key = request.get_host_key()

        self.ws.add_task(0, request)
        request.priority = True
        self.ws.add_task(0, request)
        request.important = True
        self.ws.add_task(1, request)

        # Test if timer start was called in case it was inactive
        mock_timer1.isActive.return_value = False
        mock_timer2.isActive.return_value = False
        request.priority = False
        self.ws.add_task(1, request)
        self.assertIn('start', repr(mock_timer1.method_calls))

        # Test if key was added to prio queue
        self.assertEqual(len(self.ws._queues[1]), 1)
        self.assertIn(key, self.ws._queues[1])

        # Test if 2 requests were added in prio queue
        self.assertEqual(len(self.ws._queues[1][key]), 2)

        # Test if important request was added ahead in the queue
        self.assertEqual(self.ws._queues[0][key][0], 1)

    def test_remove_task(self):
        host = "abc.xyz"
        port = 80
        request = WSRequest("", host, port, "", None)
        key = request.get_host_key()

        # Add a task and check for its existance
        task = self.ws.add_task(0, request)
        self.assertIn(key, self.ws._queues[0])
        self.assertEqual(len(self.ws._queues[0][key]), 1)

        # Remove the task and check
        self.ws.remove_task(task)
        self.assertIn(key, self.ws._queues[0])
        self.assertEqual(len(self.ws._queues[0][key]), 0)

        # Try to remove a non existing task and check for errors
        non_existing_task = (1, "a", "b")
        self.ws.remove_task(non_existing_task)

    def test_run_task(self):
        host = "abc.xyz"
        port = 80
        request = WSRequest("", host, port, "", None)
        key = request.get_host_key()

        mock_task = MagicMock()
        mock_task2 = MagicMock()
        delay_func = ratecontrol.get_delay_to_next_request = MagicMock()

        # Patching the get delay function to delay the 2nd task on queue to the next call
        delay_func.side_effect = [(False, 0), (True, 0), (False, 0), (False, 0), (False, 0), (False, 0)]
        self.ws.add_task(mock_task, request)
        request.priority = True
        self.ws.add_task(mock_task2, request)
        request.priority = False
        self.ws.add_task(mock_task, request)
        self.ws.add_task(mock_task, request)

        # Ensure no tasks are run before run_next_task is called
        self.assertEqual(mock_task.call_count, 0)
        self.ws._run_next_task()

        # Ensure priority task is run first
        self.assertEqual(mock_task2.call_count, 1)
        self.assertEqual(mock_task.call_count, 0)
        self.assertIn(key, self.ws._queues[1])

        # Ensure that the calls are run as expected
        self.ws._run_next_task()
        self.assertEqual(mock_task.call_count, 1)

        # Checking if the cleanup occurred on the prio queue
        self.assertNotIn(key, self.ws._queues[1])

        # Check the call counts on proper execution of tasks
        self.ws._run_next_task()
        self.assertEqual(mock_task.call_count, 2)
        self.ws._run_next_task()
        self.assertEqual(mock_task.call_count, 3)

        # Ensure that the clean up happened on the normal queue
        self.ws._run_next_task()
        self.assertEqual(mock_task.call_count, 3)
        self.assertNotIn(key, self.ws._queues[0])


class WebServiceProxyTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        config.setting = PROXY_SETTINGS.copy()

    def tearDown(self):
        config.setting = {}

    def test_proxy_setup(self):
        proxy_types = [
            ('http', QNetworkProxy.HttpProxy),
            ('socks', QNetworkProxy.Socks5Proxy),
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
