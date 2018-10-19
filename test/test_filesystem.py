# -*- coding: utf-8 -*-
from contextlib import suppress
import os.path
import shutil
from tempfile import mkdtemp


from picard import config
import picard.formats
from test.picardtestcase import PicardTestCase

settings = {
    'enabled_plugins': '',
    'move_files': True,
    'move_additional_files': True,
    'move_additional_files_pattern': 'cover.jpg',
}


class TestFileSystem(PicardTestCase):

    def setUp(self):
        super(TestFileSystem, self).setUp()
        self.src_directory = mkdtemp()
        self.tgt_directory = mkdtemp()
        config.setting = settings.copy()

    def tearDown(self):
        shutil.rmtree(self.src_directory)
        shutil.rmtree(self.tgt_directory)

    def _set_up_src_file(self, filename, src_rel_path):
        """Copy filename to the src directory under src_rel_path."""
        path = os.path.join(self.src_directory, src_rel_path)
        shutil.copy(filename, path)
        return path

    def _set_up_tgt_filename(self, tgt_rel_path):
        """Return the absolute path to tgt_rel_path in the tgt directory."""
        return os.path.join(self.tgt_directory, tgt_rel_path)

    def _prepare_files(self, src_rel_path='', tgt_rel_path=''):
        """Prepare src files and tgt filenames for a test."""
        with suppress(FileExistsError):
            os.mkdir(os.path.join(self.src_directory, src_rel_path))

        # Prepare the source directory structure under self.src_directory
        # .../<src_rel_path>/test.mp3
        # .../<src_rel_path>/cover.jpg

        old_filename = self._set_up_src_file(os.path.join('test', 'data', 'test.mp3'),
                                             os.path.join(src_rel_path, 'test.mp3'))
        old_additional_filename = self._set_up_src_file(os.path.join('test', 'data', 'mb.jpg'),
                                                        os.path.join(src_rel_path, 'cover.jpg'))

        with suppress(FileExistsError):
            os.mkdir(os.path.join(self.tgt_directory, tgt_rel_path))

        # Prepare the target filenames under self.tgt_directory
        # .../<tgt_rel_path>/test.mp3
        # .../<tgt_rel_path>/cover.jpg

        new_filename = self._set_up_tgt_filename(os.path.join(tgt_rel_path, 'test.mp3'))

        new_additional_filename = self._set_up_tgt_filename(os.path.join(tgt_rel_path, 'cover.jpg'))

        return (old_filename, old_additional_filename, new_filename, new_additional_filename)

    def test_move_additional_files_source_unicode(self):
        files = self._prepare_files(src_rel_path='música')
        (old_filename, old_additional_filename, new_filename, new_additional_filename) = files

        f = picard.formats.open_(old_filename)
        f._move_additional_files(old_filename, new_filename)

        self.assertTrue(os.path.isfile(new_additional_filename))
        self.assertFalse(os.path.isfile(old_additional_filename))

    def test_move_additional_files_target_unicode(self):
        files = self._prepare_files(tgt_rel_path='música')
        (old_filename, old_additional_filename, new_filename, new_additional_filename) = files

        f = picard.formats.open_(old_filename)
        f._move_additional_files(old_filename, new_filename)

        self.assertTrue(os.path.isfile(new_additional_filename))
        self.assertFalse(os.path.isfile(old_additional_filename))

    def test_move_additional_files_duplicate_patterns(self):
        files = self._prepare_files()
        (old_filename, old_additional_filename, new_filename, new_additional_filename) = files

        config.setting['move_additional_files_pattern'] = 'cover.jpg *.jpg'

        f = picard.formats.open_(old_filename)
        f._move_additional_files(old_filename, new_filename)

        self.assertTrue(os.path.isfile(new_additional_filename))
        self.assertFalse(os.path.isfile(old_additional_filename))
