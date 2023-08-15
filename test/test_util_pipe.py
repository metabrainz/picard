# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
# Copyright (C) 2023 Philipp Wolfer
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
import uuid

from test.picardtestcase import PicardTestCase

from picard.util import pipe


def pipe_listener(pipe_handler):
    while True:
        for message in pipe_handler.read_from_pipe():
            if message != pipe.Pipe.NO_RESPONSE_MESSAGE:
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
        to_send = (
            "it", "tests", "picard", "pipe",
            "my_music_file.mp3",
            TestPipe.NAME, TestPipe.VERSION,
            "last-case",
            "https://test-ca.se/index.html",
            "file:///data/test.py",
            "www.wikipedia.mp3",
            "mbid://recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
            "https://musicbrainz.org/recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
        )

        for message in to_send:
            __pool = concurrent.futures.ThreadPoolExecutor()
            pipe_handler = pipe.Pipe(self.NAME, self.VERSION)
            try:
                plistener = __pool.submit(pipe_listener, pipe_handler)
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
                pipe_handler.stop()
                __pool.shutdown()
