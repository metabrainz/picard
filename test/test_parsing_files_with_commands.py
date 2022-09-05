from test.picardtestcase import PicardTestCase

from picard.tagger import Tagger


class TestParsingFilesWithCommands(PicardTestCase):
    MOCK_FILE_CONTENTS = (
        "FROM_FILE file0.mp3",
        "",
        " ",
        "\n",
        "#commented command",
        "LOAD file1.mp3 file2.mp3",
    )

    def setUp(self):
        super().setUp()
        self.result = tuple(x for x in Tagger._parse_commands_from_lines(self.MOCK_FILE_CONTENTS))

    def test_single_argument_command(self):
        self.assertIn("command://FROM_FILE file0.mp3", self.result)

    def test_multiple_arguments_command(self):
        self.assertIn("command://LOAD file1.mp3", self.result)
        self.assertIn("command://LOAD file2.mp3", self.result)

    def test_empty_lines(self):
        self.assertNotIn("command:// ", self.result)
        self.assertNotIn("command://", self.result)
        # 1 FROM_FILE
        # 2 LOADs
        self.assertEqual(len(self.result), 3)

    def test_commented_lines(self):
        self.assertNotIn("command://#commented command", self.result)
