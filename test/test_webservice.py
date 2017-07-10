# -*- coding: utf-8 -*-

import unittest
from picard import config
from picard.webservice import WebService
from unittest.mock import patch, MagicMock

PROXY_SETTINGS = {
    "use_proxy": True,
    "proxy_server_host": '127.0.0.1',
    "proxy_server_port": 3128,
    "proxy_username": 'user',
    "proxy_password": 'password'
}


class WebServiceTest(unittest.TestCase):

    def setUp(self):
        config.setting = {'use_proxy': False}
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
        self.ws.get(host, port, path, handler)
        self.assertEqual(1, mock_add_task.call_count)
        self.assertIn(host, mock_add_task.call_args[0])
        self.assertIn(port, mock_add_task.call_args[0])
        self.assertIn("'GET'", repr(mock_add_task.call_args))
        self.ws.post(host, port, path, data, handler)
        self.assertIn("'POST'", repr(mock_add_task.call_args))
        self.ws.put(host, port, path, data, handler)
        self.assertIn("'PUT'", repr(mock_add_task.call_args))
        self.ws.delete(host, port, path, handler)
        self.assertIn("'DELETE'", repr(mock_add_task.call_args))
        self.ws.download(host, port, path, handler)
        self.assertIn("'GET'", repr(mock_add_task.call_args))
        self.assertEqual(5, mock_add_task.call_count)


class WebServiceTaskTest(unittest.TestCase):

    def setUp(self):
        config.setting = {'use_proxy': False}
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
        key = (host, port)

        self.ws.add_task(0, host, port, priority=False)
        self.ws.add_task(0, host, port, priority=True)
        self.ws.add_task(1, host, port, priority=True, important=True)

        # Test if timer start was called in case it was inactive
        mock_timer1.isActive.return_value = False
        mock_timer2.isActive.return_value = False
        self.ws.add_task(1, host, port, priority=False, important=True)
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
        key = (host, port)

        # Add a task and check for its existance
        task = self.ws.add_task(0, host, port, priority=False)
        self.assertIn(key, self.ws._queues[0])
        self.assertEqual(len(self.ws._queues[0][key]), 1)

        # Remove the task and check
        self.ws.remove_task(task)
        self.assertIn(key, self.ws._queues[0])
        self.assertEqual(len(self.ws._queues[0][key]), 0)

        # Try to remove a non existing task and check for errors
        non_existing_task = (1, "a", "b")
        self.ws.remove_task(non_existing_task)


class WebServiceProxyTest(unittest.TestCase):

    def setUp(self):
        config.setting = PROXY_SETTINGS.copy()
        self.ws = WebService()
        self.proxy = self.ws.manager.proxy()

    def tearDown(self):
        del self.ws
        del self.proxy
        config.setting = {}

    def test_proxy_setup(self):
        self.assertEqual(self.proxy.user(), PROXY_SETTINGS['proxy_username'])
        self.assertEqual(self.proxy.password(), PROXY_SETTINGS['proxy_password'])
        self.assertEqual(self.proxy.hostName(), PROXY_SETTINGS['proxy_server_host'])
        self.assertEqual(self.proxy.port(), PROXY_SETTINGS['proxy_server_port'])
