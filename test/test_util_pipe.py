# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
# Copyright (C) 2022-2023 Philipp Wolfer
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


import concurrent.futures
from platform import python_version
import time
import uuid

from test.picardtestcase import PicardTestCase

from picard.util import pipe


def pipe_listener(pipe_handler):
    while True:
        for message in pipe_handler.read_from_pipe():
            if message and message != pipe.Pipe.NO_RESPONSE_MESSAGE:
                return message


class TestPipe(PicardTestCase):
    # some random name that is different on each run
    NAME = str(uuid.uuid4())
    VERSION = python_version()

    def test_invalid_args(self):
        # Pipe should be able to make args iterable (last argument)
        self.assertRaises(pipe.PipeErrorInvalidArgs, pipe.Pipe, self.NAME, self.VERSION, 1)
        self.assertRaises(pipe.PipeErrorInvalidAppData, pipe.Pipe, 21, self.VERSION, None)
        self.assertRaises(pipe.PipeErrorInvalidAppData, pipe.Pipe, self.NAME, 21, None)

    def test_pipe_protocol(self):
        message = "foo"

        __pool = concurrent.futures.ThreadPoolExecutor()
        pipe_handler = pipe.Pipe(self.NAME, self.VERSION)
        try:
            plistener = __pool.submit(pipe_listener, pipe_handler)
            time.sleep(.2)
            res = ""

            # handle the write/read processes
            try:
                pipe_handler.send_to_pipe(message)
                res = plistener.result(timeout=6)
            except concurrent.futures._base.TimeoutError:
                pass

            self.assertEqual(res, message,
                            "Data is sent and read correctly")
        finally:
            time.sleep(.2)
            pipe_handler.stop()
            __pool.shutdown()
