# -*- coding: utf-8 -*-

import os.path
import picard.formats
import unittest
import shutil

from PyQt4 import QtCore
from picard import config, log
from picard.coverart.image import CoverArtImage, TagCoverArtImage
from picard.metadata import Metadata
from picard.util.tags import TAG_NAMES, PRESERVED_TAGS
from tempfile import mkstemp
from functools import partial


class FakeTagger(QtCore.QObject):

    tagger_stats_changed = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)
        QtCore.QObject.config = config
        QtCore.QObject.log = log
        self.tagger_stats_changed.connect(self.emit)
        self.exit_cleanup = []
        #log.log_levels = 0


    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def emit(self, *args):
        pass


settings = {
    'enabled_plugins': '',
    'clear_existing_tags': False,
    'remove_images_from_tags': False,
    'write_id3v1': True,
    'write_id3v23': False,
    'id3v2_encoding': 'utf-16',
    'id3v23_join_with': '; ',
    'save_images_to_tags': True,
    'remove_ape_from_mp3': False,
    'remove_id3_from_flac': False,
    'rating_steps': 6,
    'rating_user_email': 'users@musicbrainz.org',
    'save_only_front_images_to_tags': False,
}

cover_settings = {
    'save_only_front_images_to_tags': True,
}

class TestCoverArt(unittest.TestCase):

    def setUp(self):
        with open(os.path.join('test', 'data', 'mb.jpg'), 'rb') as f:
            self.jpegdata = f.read()
        with open(os.path.join('test', 'data', 'mb.png'), 'rb') as f:
            self.pngdata = f.read()

    def _common_set_up(self, extra=None):
        config.setting = settings.copy()
        if extra is not None:
            config.setting.update(extra)
        QtCore.QObject.tagger = FakeTagger()

    def _set_up(self, test_file, extra=None):
        fd, self.filename = mkstemp(suffix=os.path.splitext(test_file)[1])
        os.close(fd)
        shutil.copy(test_file, self.filename)
        self._common_set_up(extra)

    def _common_tear_down(self):
        QtCore.QObject.tagger.run_cleanup()

    def _tear_down(self):
        os.unlink(self.filename)
        self._common_tear_down()

    def test_coverartimage(self):
        tests = {
            'jpg': {
                'mime': 'image/jpeg',
                'data': self.jpegdata
            },
            'png': {
                'mime': 'image/png',
                'data': self.pngdata
            },
        }
        tmp_files = []
        for t in tests:
            imgdata = tests[t]['data']
            imgdata2 = imgdata + 'xxx'
            # set data once
            coverartimage = CoverArtImage(
                data=imgdata2
            )
            tmp_file = coverartimage.tempfile_filename
            tmp_files.append(tmp_file)
            l = os.path.getsize(tmp_file)
            # ensure file was written, and check its length
            self.assertEqual(l, len(imgdata2))
            self.assertEqual(coverartimage.data, imgdata2)

            # set data again, with another payload
            coverartimage.set_data(imgdata)

            tmp_file = coverartimage.tempfile_filename
            tmp_files.append(tmp_file)
            l = os.path.getsize(tmp_file)
            # check file length again
            self.assertEqual(l, len(imgdata))
            self.assertEqual(coverartimage.data, imgdata)

        QtCore.QObject.tagger.run_cleanup()

    def _test_cover_art(self, filename, t):
        self._set_up(filename)
        try:
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            tests = {
                'jpg': {
                    'mime': 'image/jpeg',
                    'data': self.jpegdata + "a" * 1024 * 128
                },
                'png': {
                    'mime': 'image/png',
                    'data': self.pngdata + "a" * 1024 * 128
                },
            }
            f = picard.formats.open(self.filename)
            metadata = Metadata()
            imgdata = tests[t]['data']
            metadata.append_image(
                CoverArtImage(
                    data=imgdata
                )
            )
            f._save(self.filename, metadata)

            f = picard.formats.open(self.filename)
            loaded_metadata = f._load(self.filename)
            self.assertEqual(len(loaded_metadata.images),1, '\n\n%s image not loaded' % t)
            image = loaded_metadata.images[0]
            self.assertEqual(tests[t]['mime'], image.mimetype,
                '\n\n%s image mime type incorrect: %s->%s' % (t, tests[t]['mime'], image.mimetype))
            self.assertEqual(imgdata, image.data, '\n\n%s image data incorrect' % t)
        finally:
            self._tear_down()

    def _cover_metadata(self):
        imgdata = self.jpegdata
        metadata = Metadata()
        metadata.append_image(
            TagCoverArtImage(
                file='a',
                tag='a',
                data=imgdata + 'a',
                support_types=True,
                types=[u'booklet', u'front'],
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='b',
                tag='b',
                data=imgdata + 'b',
                support_types=True,
                types=[u'back'],
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='c',
                tag='c',
                data=imgdata + 'c',
                support_types=True,
                types=[u'front'],
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='d',
                tag='d',
                data=imgdata + 'd',
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='e',
                tag='e',
                data=imgdata + 'e',
                is_front=False
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='f',
                tag='f',
                data=imgdata + 'f',
                types=[u'front']
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='g',
                tag='g',
                data=imgdata + 'g',
                types=[u'back'],
                is_front=True
            )
        )
        return metadata

    def test_ape_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ape'), 'jpg')

    def test_ape_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ape'), 'png')

    def test_mpcv7_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test-sv7.mpc'), 'jpg')

    def test_mpcv7_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test-sv7.mpc'), 'png')

    def test_mpcv8_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test-sv8.mpc'), 'jpg')

    def test_mpcv8_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test-sv8.mpc'), 'png')

    def test_ofr_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ofr'), 'jpg')

    def test_ofr_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ofr'), 'png')

    def test_tak_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.tak'), 'jpg')

    def test_tak_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.tak'), 'png')

    def test_wv_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wv'), 'jpg')

    def test_wv_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wv'), 'png')

    def test_asf_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.asf'), 'jpg')

    def test_asf_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.asf'), 'png')

    def test_wma_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wma'), 'jpg')

    def test_wma_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wma'), 'png')

    def test_aiff_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.aiff'), 'jpg')

    def test_aiff_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.aiff'), 'png')

    def test_mp3_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp3'), 'jpg')

    def test_mp3_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp3'), 'png')

    def test_tta_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.tta'), 'jpg')

    def test_tta_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.tta'), 'png')

    def test_m4a_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.m4a'), 'jpg')

    def test_m4a_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.m4a'), 'png')

    def test_mp4_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp4'), 'jpg')

    def test_mp4_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp4'), 'png')

    def test_flac_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.flac'), 'jpg')

    def test_flac_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.flac'), 'png')

    def test_oggflac_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test-flac.oga'), 'jpg')

    def test_oggflac_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test-flac.oga'), 'png')

    def test_ogg_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ogg'), 'jpg')

    def test_ogg_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ogg'), 'png')

    def test_opus_jpg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.opus'), 'jpg')

    def test_opus_png(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.opus'), 'png')

    # test for multiple images added to files, some types don't accept more than
    # one, and there is no guarantee that order is preserved
    def test_ape_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.ape'),
            set('a'))

    def test_mpcv7_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test-sv7.mpc'),
            set('a'))

    def test_mpcv8_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test-sv8.mpc'),
            set('a'))

    def test_ofr_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.ofr'),
            set('a'))

    def test_tak_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.tak'),
            set('a'))

    def test_wv_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.wv'),
            set('a'))

    def test_asf_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.asf'),
            set('abcdefg'[:]))

    def test_wma_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.wma'),
            set('abcdefg'[:]))

    def test_aiff_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.aiff'),
            set('abcdefg'[:]))

    def test_mp3_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.mp3'),
            set('abcdefg'[:]))

    def test_tta_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.tta'),
            set('abcdefg'[:]))

    def test_m4a_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.m4a'),
            set('abcdefg'[:]))

    def test_mp4_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.mp4'),
            set('abcdefg'[:]))

    def test_flac_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.flac'),
            set('abcdefg'[:]))

    def test_oggflac_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test-flac.oga'),
            set('abcdefg'[:]))

    def test_ogg_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.ogg'),
            set('abcdefg'[:]))

    def test_opus_multiple_covers(self):
        self._test_cover_art_multiple(
            os.path.join('test', 'data', 'test.opus'),
            set('abcdefg'[:]))

    def test_ape_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.ape'),
            set('a'))

    def test_mpcv7_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test-sv7.mpc'),
            set('a'))

    def test_mpcv8_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test-sv8.mpc'),
            set('a'))

    def test_ofr_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.ofr'),
            set('a'))

    def test_tak_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.tak'),
            set('a'))

    def test_wv_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.wv'),
            set('a'))

    def test_asf_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.asf'),
            set('a'))

    def test_wma_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.wma'),
            set('a'))

    def test_aiff_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.aiff'),
            set('a'))

    def test_mp3_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.mp3'),
            set('a'))

    def test_tta_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.tta'),
            set('a'))

    def test_m4a_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.m4a'),
            set('a'))

    def test_mp4_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.mp4'),
            set('a'))

    def test_flac_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.flac'),
            set('a'))

    def test_oggflac_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test-flac.oga'),
            set('a'))

    def test_ogg_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.ogg'),
            set('a'))

    def test_opus_front_cover_only(self):
        self._test_cover_art_front_only(
            os.path.join('test', 'data', 'test.opus'),
            set('a'))

    def test_is_front_image(self):
        self._common_set_up()
        try:
            m = self._cover_metadata()
            front_images = set('acdfg'[:])
            found = set()
            for img in m.images:
                if img.is_front_image():
                    found.add(img.tag)
            self.assertEqual(front_images, found)
        finally:
            self._common_tear_down()

    def _test_cover_art_multiple(self, filename, expect):
        self._set_up(filename)
        try:
            f = picard.formats.open(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set()
            for n, image in enumerate(loaded_metadata.images):
                found.add(image.data[-1])
            self.assertEqual(expect, found)
        finally:
            self._tear_down()

    def _test_cover_art_front_only(self, filename, expect):
        self._set_up(filename, {'save_only_front_images_to_tags': True})
        try:
            f = picard.formats.open(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set()
            for n, image in enumerate(loaded_metadata.images):
                found.add(image.data[-1])
            self.assertEqual(expect, found)
        finally:
            self._tear_down()
