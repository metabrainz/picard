# -*- coding: utf-8 -*-
from contextlib import suppress
import os.path
import shutil
from tempfile import mkdtemp
from test.picardtestcase import PicardTestCase

from picard import config
import picard.formats


settings = {
    'enabled_plugins': '',
    'move_files': True,
    'move_additional_files': True,
    'move_additional_files_pattern': 'cover.jpg',
}


class TestFileSystem(PicardTestCase):

    def setUp(self):
        super().setUp()
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

        files = dict()
        files['old_mp3'] = self._set_up_src_file(os.path.join('test', 'data', 'test.mp3'),
                                                 os.path.join(src_rel_path, 'test.mp3'))
        files['old_img'] = self._set_up_src_file(os.path.join('test', 'data', 'mb.jpg'),
                                                 os.path.join(src_rel_path, 'cover.jpg'))
        files['old_hidden_img'] = self._set_up_src_file(os.path.join('test', 'data', 'mb.jpg'),
                                                        os.path.join(src_rel_path,
                                                                     '.hidden.jpg'))

        with suppress(FileExistsError):
            os.mkdir(os.path.join(self.tgt_directory, tgt_rel_path))

        # Prepare the target filenames under self.tgt_directory
        # .../<tgt_rel_path>/test.mp3
        # .../<tgt_rel_path>/cover.jpg

        files['new_mp3'] = self._set_up_tgt_filename(
            os.path.join(tgt_rel_path, 'test.mp3'))

        files['new_img'] = self._set_up_tgt_filename(
            os.path.join(tgt_rel_path, 'cover.jpg'))

        files['new_hidden_img'] = self._set_up_tgt_filename(
            os.path.join(tgt_rel_path, '.hidden.jpg'))

        return files

    def test_move_additional_files_source_unicode(self):
        files = self._prepare_files(src_rel_path='música')

        f = picard.formats.open_(files['old_mp3'])
        f._move_additional_files(files['old_mp3'], files['new_mp3'])

        self.assertTrue(os.path.isfile(files['new_img']))
        self.assertFalse(os.path.isfile(files['old_img']))

    def test_move_additional_files_target_unicode(self):
        files = self._prepare_files(tgt_rel_path='música')

        f = picard.formats.open_(files['old_mp3'])
        f._move_additional_files(files['old_mp3'], files['new_mp3'])

        self.assertTrue(os.path.isfile(files['new_img']))
        self.assertFalse(os.path.isfile(files['old_img']))

    def test_move_additional_files_duplicate_patterns(self):
        files = self._prepare_files()

        config.setting['move_additional_files_pattern'] = 'cover.jpg *.jpg'

        f = picard.formats.open_(files['old_mp3'])
        f._move_additional_files(files['old_mp3'], files['new_mp3'])

        self.assertTrue(os.path.isfile(files['new_img']))
        self.assertFalse(os.path.isfile(files['old_img']))

    def test_move_additional_files_hidden_nopattern(self):
        files = self._prepare_files()

        config.setting['move_additional_files_pattern'] = '*.jpg'

        f = picard.formats.open_(files['old_mp3'])
        f._move_additional_files(files['old_mp3'], files['new_mp3'])

        self.assertFalse(os.path.isfile(files['new_hidden_img']))
        self.assertTrue(os.path.isfile(files['old_hidden_img']))

    def test_move_additional_files_hidden_pattern(self):
        files = self._prepare_files()

        config.setting['move_additional_files_pattern'] = '*.jpg .*.jpg'

        f = picard.formats.open_(files['old_mp3'])
        f._move_additional_files(files['old_mp3'], files['new_mp3'])

        self.assertTrue(os.path.isfile(files['new_hidden_img']))
        self.assertFalse(os.path.isfile(files['old_hidden_img']))
