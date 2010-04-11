import os.path
import unittest
import shutil
from tempfile import mkstemp
from picard import log
from picard.metadata import Metadata
import picard.formats
from PyQt4 import QtCore


class FakeTagger():
    def __init__(self):
        if "PICARD_DEBUG" in os.environ:
            self.log = log.DebugLog()
        else:
            self.log = log.Log()
        QtCore.QObject.log = self.log

    def emit(self, *args):
        pass


class FakeConfig():
    def __init__(self):
        self.setting = {
            'enabled_plugins': '',
            'clear_existing_tags': False,
            'remove_images_from_tags': False,
            'write_id3v1': True,
            'id3v2_encoding': 'utf-8',
            'save_images_to_tags': True,
            'write_id3v23': False,
            'remove_ape_from_mp3': False,
            'remove_id3_from_flac': False
        }


class FormatsTest(unittest.TestCase):

    original = None
    tags = []

    def setUp(self):
        if not self.original:
            return
        fd, self.filename = mkstemp(suffix=os.path.splitext(self.original)[1])
        os.close(fd)
        shutil.copy(self.original, self.filename)
        QtCore.QObject.tagger = FakeTagger()
        QtCore.QObject.config = FakeConfig()

    def tearDown(self):
        if not self.original:
            return
        os.unlink(self.filename)

    def test_simple_tags(self):
        if not self.original:
            return
        f = picard.formats.open(self.filename)
        # The loading process is very tightly coupled to the threading
        # library and loading without instantiating a thread pool
        # unless internal functions are used
        loaded_metadata = f._load(self.filename)
        f._copy_metadata(loaded_metadata)
        metadata = Metadata()
        for (key, value) in self.tags.iteritems():
            metadata[key] = value
        f._save(self.filename, metadata, f.config.setting)
        f = picard.formats.open(self.filename)
        loaded_metadata = f._load(self.filename)
        f._copy_metadata(loaded_metadata)
        for (key, value) in self.tags.iteritems():
            self.assertEqual(f.metadata[key], value, '%s: %r != %r' % (key, f.metadata[key], value))

class FLACTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.flac')
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'compilation' : '1',
        'comment' : 'Foo',
        'genre' : 'Foo',
        'bpm' : 'Foo',
        'mood' : 'Foo',
        'isrc' : 'Foo',
        'copyright' : 'Foo',
        'lyrics' : 'Foo',
        'media' : 'Foo',
        'label' : 'Foo',
        'catalognumber' : 'Foo',
        'barcode' : 'Foo',
        'encodedby' : 'Foo',
        'albumsort' : 'Foo',
        'albumartistsort' : 'Foo',
        'artistsort' : 'Foo',
        'titlesort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        }


class ASFTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.wma')
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        #'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'engineer' : 'Foo',
        #'producer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        #'discsubtitle' : 'Foo',
        #'compilation' : '1',
        #'comment' : 'Foo',
        'genre' : 'Foo',
        'bpm' : 'Foo',
        'mood' : 'Foo',
        'isrc' : 'Foo',
        'copyright' : 'Foo',
        'lyrics' : 'Foo',
        #'media' : 'Foo',
        'label' : 'Foo',
        #'catalognumber' : 'Foo',
        #'barcode' : 'Foo',
        'encodedby' : 'Foo',
        'albumsort' : 'Foo',
        'albumartistsort' : 'Foo',
        'artistsort' : 'Foo',
        'titlesort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        }


class MP3Test(FormatsTest):
    original = os.path.join('test', 'data', 'test.mp3')
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'compilation' : '1',
        #'comment' : 'Foo',
         'genre' : 'Foo',
         'bpm' : 'Foo',
         'mood' : 'Foo',
        'isrc' : 'Foo',
        'copyright' : 'Foo',
        # TODO
        # 'lyrics' : 'Foo',
        'media' : 'Foo',
        'label' : 'Foo',
        'catalognumber' : 'Foo',
        'barcode' : 'Foo',
        'encodedby' : 'Foo',
        'albumsort' : 'Foo',
        'albumartistsort' : 'Foo',
        'artistsort' : 'Foo',
        'titlesort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        }


class OggVorbisTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.ogg')
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'compilation' : '1',
        'comment' : 'Foo',
        'genre' : 'Foo',
        'bpm' : 'Foo',
        'mood' : 'Foo',
        'isrc' : 'Foo',
        'copyright' : 'Foo',
        'lyrics' : 'Foo',
        'media' : 'Foo',
        'label' : 'Foo',
        'catalognumber' : 'Foo',
        'barcode' : 'Foo',
        'encodedby' : 'Foo',
        'albumsort' : 'Foo',
        'albumartistsort' : 'Foo',
        'artistsort' : 'Foo',
        'titlesort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        }


class MP4VorbisTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.m4a')
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004-00-00',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'grouping' : 'Foo',
        'compilation' : '1',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        'encodedby' : 'Foo',
        'lyrics' : 'Foo',
        'copyright' : 'Foo',
        }


class WavPackTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.wv')
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'compilation' : '1',
        'comment' : 'Foo',
        'genre' : 'Foo',
        'bpm' : 'Foo',
        'mood' : 'Foo',
        'isrc' : 'Foo',
        'copyright' : 'Foo',
        'lyrics' : 'Foo',
        'media' : 'Foo',
        'label' : 'Foo',
        'catalognumber' : 'Foo',
        'barcode' : 'Foo',
        'encodedby' : 'Foo',
        'albumsort' : 'Foo',
        'albumartistsort' : 'Foo',
        'artistsort' : 'Foo',
        'titlesort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        }


class TestCoverArt(unittest.TestCase):

    def _set_up(self, original):
        fd, self.filename = mkstemp(suffix=os.path.splitext(original)[1])
        os.close(fd)
        shutil.copy(original, self.filename)
        QtCore.QObject.tagger = FakeTagger()
        QtCore.QObject.config = FakeConfig()

    def _tear_down(self):
        os.unlink(self.filename)

    def test_asf(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wma'))

    def test_ape(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wv'))

    def test_mp3(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp3'))

    def test_mp4(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.m4a'))

    def test_vorbis(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ogg'))

    def _test_cover_art(self, filename):
        self._set_up(filename)
        try:
            f = picard.formats.open(self.filename)
            # f.metadata.clear()
            # f.metadata.add_image("image/jpeg", "JFIFfoobar")
            metadata = Metadata()
            metadata.add_image("image/jpeg", "JFIFfoobar")
            f._save(self.filename, metadata, f.config.setting)

            f = picard.formats.open(self.filename)
            f._load(self.filename)
            self.assertEqual(metadata.images[0][0], "image/jpeg")
            self.assertEqual(metadata.images[0][1], "JFIFfoobar")

            f = picard.formats.open(self.filename)
            metadata = Metadata()
            metadata.add_image("image/png", "PNGfoobar")
            f._save(self.filename, metadata, f.config.setting)

            f = picard.formats.open(self.filename)
            f._load(self.filename)
            self.assertEqual(metadata.images[0][0], "image/png")
            self.assertEqual(metadata.images[0][1], "PNGfoobar")
        finally:
            self._tear_down()
