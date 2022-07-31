# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
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
from random import randint

from test.picardtestcase import PicardTestCase

from picard.util import pipe


def pipe_listener(pipe_handler):
    while True:
        for message in pipe_handler.read_from_pipe():
            if message != pipe.Pipe.NO_RESPONSE_MESSAGE:
                return message


def pipe_writer(pipe_handler, to_send):
    if not to_send:
        return False

    while not pipe_handler.send_to_pipe(to_send):
        pass

    return True


class TestPipe(PicardTestCase):
    # we don't need any strong and secure random numbers, just anything that is different on each run
    NAME = str(randint(0, 99999999))  # nosec
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

        pipe_listener_handler = pipe.Pipe(self.NAME, self.VERSION)
        if pipe_listener_handler.path_was_forced:
            pipe_writer_handler = pipe.Pipe(self.NAME, self.VERSION, args=None, forced_path=pipe_listener_handler.path)
        else:
            pipe_writer_handler = pipe.Pipe(self.NAME, self.VERSION)

        __pool = concurrent.futures.ThreadPoolExecutor()
        for message in to_send:
            plistener = __pool.submit(pipe_listener, pipe_listener_handler)
            pwriter = __pool.submit(pipe_writer, pipe_writer_handler, message)
            res = ""

            # handle the write/read processes
            try:
                res = plistener.result(timeout=6)
            except concurrent.futures._base.TimeoutError:
                pipe_writer_handler.send_to_pipe(pipe_writer_handler.MESSAGE_TO_IGNORE)
            try:
                pwriter.result(timeout=0.01)
            except concurrent.futures._base.TimeoutError:
                pipe_listener_handler.read_from_pipe()

            self.assertEqual(res, message,
                             "Data is sent and read correctly")
