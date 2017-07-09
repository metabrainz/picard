# -*- coding: utf-8 -*-

import unittest
from picard import config
from picard.webservice import WebService
from mock import patch

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
        mock_add_task.assert_called()
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
