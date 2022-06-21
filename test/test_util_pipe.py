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

from test.picardtestcase import PicardTestCase

from picard import (
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
)
from picard.util import pipe


def pipe_listener(pipe_handler, end_of_sequence):
    IGNORED_OUTPUT = {pipe.Pipe.MESSAGE_TO_IGNORE, pipe.Pipe.NO_RESPONSE_MESSAGE, "", end_of_sequence}
    received = []
    messages = []

    while end_of_sequence not in messages:
        messages = pipe_handler.read_from_pipe()
        for message in messages:
            if message not in IGNORED_OUTPUT:
                received.append(message)

    return tuple(received)


def pipe_writer(pipe_handler, to_send, end_of_sequence):
    for message in to_send:
        while not pipe_handler.send_to_pipe(message):
            pass
    while not pipe_handler.send_to_pipe(end_of_sequence):
        pass


class TestPipe(PicardTestCase):
    SUFFIX = f"{PICARD_APP_NAME}_v{PICARD_FANCY_VERSION_STR}_pipe_file"

    def test_invalid_args(self):
        # Pipe should be able to make args iterable (last argument)
        self.assertRaises(pipe.PipeErrorInvalidArgs, pipe.Pipe, PICARD_APP_NAME, PICARD_FANCY_VERSION_STR, 1)
        self.assertRaises(pipe.PipeErrorInvalidAppData, pipe.Pipe, 21, PICARD_FANCY_VERSION_STR, None)
        self.assertRaises(pipe.PipeErrorInvalidAppData, pipe.Pipe, PICARD_APP_NAME, 21, None)

    def test_pipe_protocol(self):
        END_OF_SEQUENCE = "stop"
        to_send = (
            ("it", "tests", "picard", "pipe"),
            ("test", "number", "two"),
            ("my_music_file.mp3",),
        )

        pipe_listener_handler = pipe.Pipe(PICARD_APP_NAME, PICARD_FANCY_VERSION_STR)
        if pipe_listener_handler.path_was_forced:
            pipe_writer_handler = pipe.Pipe(PICARD_APP_NAME, PICARD_FANCY_VERSION_STR, forced_path=pipe_listener_handler.path)
        else:
            pipe_writer_handler = pipe.Pipe(PICARD_APP_NAME, PICARD_FANCY_VERSION_STR)

        for messages in to_send:
            __pool = concurrent.futures.ThreadPoolExecutor()
            plistener = __pool.submit(pipe_listener, pipe_listener_handler, END_OF_SEQUENCE)
            __pool.submit(pipe_writer, pipe_writer_handler, messages, END_OF_SEQUENCE)
            self.assertEqual(plistener.result(), messages,
                             "Data is sent and read correctly")
