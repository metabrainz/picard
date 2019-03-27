import os.path
import shutil
from tempfile import mkstemp
from test.picardtestcase import PicardTestCase

from PyQt5 import QtCore

from picard import (
    config,
    # log,
)
from picard.coverart.image import (
    CoverArtImage,
    TagCoverArtImage,
)
import picard.formats
from picard.metadata import Metadata
from .common import (
    load_raw,
    settings,
)


class TestCoverArt(PicardTestCase):

    def setUp(self):
        super().setUp()
        with open(os.path.join('test', 'data', 'mb.jpg'), 'rb') as f:
            self.jpegdata = f.read()
        with open(os.path.join('test', 'data', 'mb.png'), 'rb') as f:
            self.pngdata = f.read()

    def _common_set_up(self, extra=None):
        config.setting = settings.copy()
        if extra is not None:
            config.setting.update(extra)

    def _set_up(self, original, extra=None):
        fd, self.filename = mkstemp(suffix=os.path.splitext(original)[1])
        os.close(fd)
        shutil.copy(original, self.filename)
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
            imgdata2 = imgdata + b'xxx'
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

    def test_asf(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wma'))

    def test_ape(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wv'))

    def test_mp3(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp3'))

    def test_mp4(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.m4a'))

    def test_ogg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ogg'))

    def test_flac(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.flac'))

    # test for multiple images added to files, some types don't accept more than
    # one, and there is no guarantee that order is preserved
    def test_asf_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.wma'),
                                   set('abcdefg'[:]))

    def test_ape_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.wv'),
                                   set('a'))

    def test_mp3_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.mp3'),
                                   set('abcdefg'[:]))

    def test_mp4_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.m4a'),
                                   set('abcdefg'[:]))

    def test_ogg_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.ogg'),
                                   set('abcdefg'[:]))

    def test_flac_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.flac'),
                                   set('abcdefg'[:]))

    def test_asf_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.wma'),
            set('a'))

    def test_ape_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.wv'),
            set('a'))

    def test_mp3_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.mp3'),
            set('a'))

    def test_mp4_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.m4a'),
            set('a'))

    def test_ogg_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.ogg'),
            set('a'))

    def test_flac_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.flac'),
            set('a'))

    def test_flac_set_picture_dimensions(self):
        self._set_up(os.path.join('test', 'data', 'test.flac'))
        try:
            tests = [
                CoverArtImage(data=self.jpegdata),
                CoverArtImage(data=self.pngdata),
            ]
            for test in tests:
                self._file_save_image(self.filename, test)
                raw_metadata = load_raw(self.filename)
                pic = raw_metadata.pictures[0]
                self.assertNotEqual(pic.width, 0)
                self.assertEqual(pic.width, test.width)
                self.assertNotEqual(pic.height, 0)
                self.assertEqual(pic.height, test.height)
        finally:
            self._tear_down()

    def _test_cover_art(self, filename):
        self._set_up(filename)
        try:
            source_types = ["front", "booklet"]
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            tests = [
                CoverArtImage(data=self.jpegdata + b"a" * 1024 * 128, types=source_types),
                CoverArtImage(data=self.pngdata + b"a" * 1024 * 128, types=source_types),
            ]
            for test in tests:
                self._file_save_image(self.filename, test)
                f = picard.formats.open_(self.filename)
                loaded_metadata = f._load(self.filename)
                image = loaded_metadata.images[0]
                self.assertEqual(test.mimetype, image.mimetype)
                self.assertEqual(test, image)
        finally:
            self._tear_down()

    @staticmethod
    def _file_save_image(filename, image):
        f = picard.formats.open_(filename)
        metadata = Metadata()
        metadata.images.append(image)
        f._save(filename, metadata)

    def _cover_metadata(self):
        imgdata = self.jpegdata
        metadata = Metadata()
        metadata.images.append(
            TagCoverArtImage(
                file='a',
                tag='a',
                data=imgdata + b'a',
                support_types=True,
                types=[u'booklet', u'front'],
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='b',
                tag='b',
                data=imgdata + b'b',
                support_types=True,
                types=[u'back'],
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='c',
                tag='c',
                data=imgdata + b'c',
                support_types=True,
                types=[u'front'],
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='d',
                tag='d',
                data=imgdata + b'd',
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='e',
                tag='e',
                data=imgdata + b'e',
                is_front=False
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='f',
                tag='f',
                data=imgdata + b'f',
                types=[u'front']
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='g',
                tag='g',
                data=imgdata + b'g',
                types=[u'back'],
                is_front=True
            )
        )
        return metadata

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

    def _test_cover_art_types(self, filename, expect):
        self._set_up(filename)
        expect = {ord(char) for char in expect}
        try:
            f = picard.formats.open_(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open_(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set()
            for n, image in enumerate(loaded_metadata.images):
                found.add(image.data[-1])
            self.assertEqual(expect, found)
        finally:
            self._tear_down()

    def _test_cover_art_types_only_front(self, filename, expect):
        self._set_up(filename, {'embed_only_one_front_image': True})
        expect = {ord(char) for char in expect}
        try:
            f = picard.formats.open_(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open_(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set()
            for n, image in enumerate(loaded_metadata.images):
                found.add(image.data[-1])
            self.assertEqual(expect, found)
        finally:
            self._tear_down()
