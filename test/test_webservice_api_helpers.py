# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2023 Laurent Monin
# Copyright (C) 2019-2023 Philipp Wolfer
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

from PyQt6.QtCore import QUrl

from test.picardtestcase import PicardTestCase

from picard.webservice import WebService
from picard.webservice.api_helpers import APIHelper


class APITest(PicardTestCase):
    def setUp(self):
        super().setUp()
        base_url = "http://abc.com/v1"
        self.path = "/test/more/test"
        self.complete_url = QUrl(base_url + self.path)
        self.ws = MagicMock(auto_spec=WebService)
        self.api = APIHelper(self.ws, base_url=base_url)

    def _test_ws_function_args(self, ws_function):
        self.assertGreater(ws_function.call_count, 0)
        self.assertEqual(ws_function.call_args[1]['url'], self.complete_url)

    def test_get(self):
        self.api.get(self.path, None)
        self._test_ws_function_args(self.ws.get_url)

    def test_post(self):
        self.api.post(self.path, None, None)
        self._test_ws_function_args(self.ws.post_url)

    def test_put(self):
        self.api.put(self.path, None, None)
        self._test_ws_function_args(self.ws.put_url)

    def test_delete(self):
        self.api.delete(self.path, None)
        self._test_ws_function_args(self.ws.delete_url)
