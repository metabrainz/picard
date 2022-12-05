# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
# Copyright (C) 2022 Bob Swift
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

from picard.util.remotecommands import RemoteCommands


class TestParsingFilesWithCommands(PicardTestCase):

    TEST_FILE = 'test/data/test-command-file-1.txt'

    def setUp(self):
        super().setUp()
        self.result = []
        RemoteCommands.set_quit(False)
        RemoteCommands.get_commands_from_file(self.TEST_FILE)
        while not RemoteCommands.command_queue.empty():
            (cmd, arg) = RemoteCommands.command_queue.get()
            self.result.append(f"{cmd} {arg}")
            RemoteCommands.command_queue.task_done()

    def test_no_argument_command(self):
        self.assertIn("CLUSTER ", self.result)

    def test_no_argument_command_stripped_correctly(self):
        self.assertIn("FINGERPRINT ", self.result)

    def test_single_argument_command(self):
        self.assertIn("LOAD file3.mp3", self.result)

    def test_multiple_arguments_command(self):
        self.assertIn("LOAD file1.mp3", self.result)
        self.assertIn("LOAD file2.mp3", self.result)

    def test_from_file_command_parsed(self):
        self.assertNotIn("FROM_FILE command_file.txt", self.result)
        self.assertNotIn("FROM_FILE test/data/test-command-file-1.txt", self.result)
        self.assertNotIn("FROM_FILE test/data/test-command-file-2.txt", self.result)

    def test_noting_added_after_quit(self):
        self.assertNotIn("LOOKUP clustered", self.result)

    def test_empty_lines(self):
        self.assertNotIn(" ", self.result)
        self.assertNotIn("", self.result)
        self.assertEqual(len(self.result), 7)

    def test_commented_lines(self):
        self.assertNotIn("#commented command", self.result)
