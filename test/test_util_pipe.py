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


from test.picardtestcase import PicardTestCase

from picard import (
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
)
from picard.util import pipe


class TestPipe(PicardTestCase):

    def test_invalid_args(self):
        # Pipe should be able to make args iterable (last argument)
        self.assertRaises(pipe.PipeErrorInvalidArgs, pipe.Pipe, PICARD_APP_NAME, PICARD_FANCY_VERSION_STR, 1)
        self.assertRaises(pipe.PipeErrorInvalidAppData, pipe.Pipe, 21, PICARD_FANCY_VERSION_STR, None)
        self.assertRaises(pipe.PipeErrorInvalidAppData, pipe.Pipe, PICARD_APP_NAME, 21, None)

    def test_filename_generation(self):
        # TODO test pipe.__generate_filename for creating valid paths
        # also test fallback linux dir somehow
        # maybe some fake pipe instance that prevents itself from passing the args and creates the pipe just for tests
        # maybe some debug parameter to force use the fallback dir?
        pass

    def test_pipe_protocol(self):
        # TODO concurrent.futures like in util/pipe.py, one with listener, one with sender
        # test if the data is sent correctly
        pass
