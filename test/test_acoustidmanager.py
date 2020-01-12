from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.acoustid.manager import AcoustIDManager
from picard.file import File


class AcoustIDManagerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.acoustidmanager = AcoustIDManager()
        self.tagger.window = MagicMock()
        self.tagger.window.enable_submit = MagicMock()

    def test_add_invalid(self):
        file = File('foo.flac')
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_not_called()

    def test_add_and_update(self):
        file = File('foo.flac')
        file.acoustid_fingerprint = 'foo'
        file.acoustid_length = 120
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_called_with(False)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.tagger.window.enable_submit.assert_called_with(True)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_called_with(False)

    def test_add_and_remove(self):
        file = File('foo.flac')
        file.acoustid_fingerprint = 'foo'
        file.acoustid_length = 120
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_called_with(False)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.tagger.window.enable_submit.assert_called_with(True)
        self.acoustidmanager.remove(file)
        self.tagger.window.enable_submit.assert_called_with(False)

    def test_is_submitted(self):
        file = File('foo.flac')
        file.acoustid_fingerprint = 'foo'
        file.acoustid_length = 120
        self.assertTrue(self.acoustidmanager.is_submitted(file))
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.assertTrue(self.acoustidmanager.is_submitted(file))
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.assertFalse(self.acoustidmanager.is_submitted(file))
        self.acoustidmanager.update(file, '')
        self.assertTrue(self.acoustidmanager.is_submitted(file))
