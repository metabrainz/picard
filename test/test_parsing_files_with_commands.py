from test.picardtestcase import PicardTestCase

from picard.tagger import Tagger


class TestParsingFilesWithCommands(PicardTestCase):

    TEST_FILE = 'test/data/test-command-file-1.txt'

    def setUp(self):
        super().setUp()
        self.result = []
        for (cmd, cmdargs) in Tagger._read_commands_from_file(self.TEST_FILE):
            for cmd_arg in cmdargs or ['']:
                self.result.append(f"{cmd} {cmd_arg}")

    def test_no_argument_command(self):
        self.assertIn("CLUSTER unclustered", self.result)

    def test_no_argument_command_stripped_correctly(self):
        self.assertIn("FINGERPRINT ", self.result)

    def test_single_argument_command(self):
        self.assertIn("FROM_FILE command_file.txt", self.result)
        self.assertIn("LOAD file3.mp3", self.result)

    def test_multiple_arguments_command(self):
        self.assertIn("LOAD file1.mp3", self.result)
        self.assertIn("LOAD file2.mp3", self.result)

    def test_empty_lines(self):
        self.assertNotIn(" ", self.result)
        self.assertNotIn("", self.result)
        self.assertEqual(len(self.result), 6)

    def test_commented_lines(self):
        self.assertNotIn("#commented command", self.result)
