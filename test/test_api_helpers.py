# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Laurent Monin
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019 Philipp Wolfer
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


from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.webservice import WebService
from picard.webservice.api_helpers import (
    APIHelper,
    MBAPIHelper,
)


class APITest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.host = "abc.com"
        self.port = 80
        self.api_path = "/v1/"
        self.path_list = ['test', 'more', 'test']
        self.complete_path = "/v1/test/more/test"
        self.ws = MagicMock(auto_spec=WebService)
        self.api = APIHelper(self.host, self.port, self.api_path, self.ws)

    def _test_ws_function_args(self, ws_function):
        self.assertGreater(ws_function.call_count, 0)
        self.assertEqual(ws_function.call_args[0][0], self.host)
        self.assertEqual(ws_function.call_args[0][1], self.port)
        self.assertEqual(ws_function.call_args[0][2], self.complete_path)

    def test_get(self):
        self.api.get(self.path_list, None)
        self._test_ws_function_args(self.ws.get)

    def test_post(self):
        self.api.post(self.path_list, None, None)
        self._test_ws_function_args(self.ws.post)

    def test_put(self):
        self.api.put(self.path_list, None, None)
        self._test_ws_function_args(self.ws.put)

    def test_delete(self):
        self.api.delete(self.path_list, None)
        self._test_ws_function_args(self.ws.delete)


class MBAPITest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.config = {'server_host': "mb.org", "server_port": 443}
        self.set_config_values(self.config)
        self.ws = MagicMock(auto_spec=WebService)
        self.api = MBAPIHelper(self.ws)

    def _test_ws_function_args(self, ws_function):
        self.assertGreater(ws_function.call_count, 0)
        self.assertEqual(ws_function.call_args[0][0], self.config['server_host'])
        self.assertEqual(ws_function.call_args[0][1], self.config['server_port'])
        self.assertIn("/ws/2/", ws_function.call_args[0][2])

    def assertInPath(self, ws_function, path):
        self.assertIn(path, ws_function.call_args[0][2])

    def assertNotInPath(self, ws_function, path):
        self.assertNotIn(path, ws_function.call_args[0][2])

    def assertInQuery(self, ws_function, argname, value=None):
        query_args = ws_function.call_args[1]['queryargs']
        self.assertIn(argname, query_args)
        self.assertEqual(value, query_args[argname])

    def _test_inc_args(self, ws_function, arg_list):
        self.assertInQuery(self.ws.get, 'inc', "+".join(arg_list))

    def test_get_release(self):
        inc_args_list = ['test']
        self.api.get_release_by_id("1", None, inc=inc_args_list)
        self._test_ws_function_args(self.ws.get)
        self.assertInPath(self.ws.get, "/release/1")
        self._test_inc_args(self.ws.get, inc_args_list)

    def test_get_track(self):
        inc_args_list = ['test']
        self.api.get_track_by_id("1", None, inc=inc_args_list)
        self._test_ws_function_args(self.ws.get)
        self.assertInPath(self.ws.get, "/recording/1")
        self._test_inc_args(self.ws.get, inc_args_list)

    def test_get_collection(self):
        inc_args_list = ["releases", "artist-credits", "media"]
        self.api.get_collection("1", None)
        self._test_ws_function_args(self.ws.get)
        self.assertInPath(self.ws.get, "collection")
        self.assertInPath(self.ws.get, "1/releases")
        self._test_inc_args(self.ws.get, inc_args_list)

    def test_get_collection_list(self):
        self.api.get_collection_list(None)
        self._test_ws_function_args(self.ws.get)
        self.assertInPath(self.ws.get, "collection")
        self.assertNotInPath(self.ws.get, "releases")

    def test_put_collection(self):
        self.api.put_to_collection("1", ["1", "2", "3"], None)
        self._test_ws_function_args(self.ws.put)
        self.assertInPath(self.ws.put, "collection/1/releases/1;2;3")

    def test_delete_collection(self):
        self.api.delete_from_collection("1", ["1", "2", "3", "4"] * 200, None)
        collection_string = ";".join(["1", "2", "3", "4"] * 100)
        self._test_ws_function_args(self.ws.delete)
        self.assertInPath(self.ws.delete, "collection/1/releases/" + collection_string)
        self.assertNotInPath(self.ws.delete, collection_string + ";" + collection_string)
        self.assertEqual(self.ws.delete.call_count, 2)
