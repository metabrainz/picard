import os.path
import unittest
import shutil
from tempfile import mkstemp
from picard import log
from picard.metadata import Metadata
import picard.formats
from PyQt4 import QtCore


class FakeTagger(QtCore.QObject):

    file_state_changed = QtCore.pyqtSignal(int)

    def __init__(self):
        QtCore.QObject.__init__(self)
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
            'remove_id3_from_flac': False,
            'rating_steps': 6,
            'rating_user_email': 'users@musicbrainz.org',
            'save_only_front_images_to_tags': False,
        }


def save_and_load_metadata(filename, metadata):
    """Save new metadata to a file and load it again."""
    f = picard.formats.open(filename)
    loaded_metadata = f._load(filename)
    f._copy_loaded_metadata(loaded_metadata)
    f._save(filename, metadata, f.config.setting)
    f = picard.formats.open(filename)
    loaded_metadata = f._load(filename)
    return loaded_metadata


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
        metadata = Metadata()
        for (key, value) in self.tags.iteritems():
            metadata[key] = value
        loaded_metadata = save_and_load_metadata(self.filename, metadata)
        for (key, value) in self.tags.iteritems():
            #if key == 'comment:foo':
            #    print "%r" % loaded_metadata
            self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

    def test_ratings(self):
        if not self.original or not self.supports_ratings:
            return
        for rating in range(6):
            rating = 1
            metadata = Metadata()
            metadata['~rating'] = rating
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(int(loaded_metadata['~rating']), rating, '~rating: %r != %r' % (loaded_metadata['~rating'], rating))


class FLACTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.flac')
    supports_ratings = True
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'originaldate' : '1980',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'arranger' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'djmixer' : 'Foo',
        'mixer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'tracknumber' : '2',
        'totaltracks' : '10',
        'discnumber' : '1',
        'totaldiscs' : '2',
        'compilation' : '1',
        'comment:' : 'Foo',
        'comment:foo' : 'Foo',
        'genre' : 'Foo',
        'bpm' : '80',
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
        #'composersort' : 'Foo',
        #'showsort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'musicip_fingerprint' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        'asin' : 'Foo',
        #'gapless' : '1',
        #'podcast' : '1',
        #'podcasturl' : 'Foo',
        #'show' : 'Foo',
        }


class WMATest(FormatsTest):
    original = os.path.join('test', 'data', 'test.wma')
    supports_ratings = True
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'originaldate' : '1980',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        #'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        #'arranger' : 'Foo',
        #'engineer' : 'Foo',
        'producer' : 'Foo',
        #'djmixer' : 'Foo',
        #'mixer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'tracknumber' : '2',
        #'totaltracks' : '10',
        'discnumber' : '1',
        #'totaldiscs' : '2',
        #'compilation' : '1',
        'comment:' : 'Foo',
        # FIXME: comment:foo is unsupported in our WMA implementation
        #'comment:foo' : 'Foo',
        'genre' : 'Foo',
        'bpm' : '80',
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
        #'composersort' : 'Foo',
        #'showsort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        #'musicip_fingerprint' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        #'asin' : 'Foo',
        #'gapless' : '1',
        #'podcast' : '1',
        #'podcasturl' : 'Foo',
        #'show' : 'Foo',
        }


class MP3Test(FormatsTest):
    original = os.path.join('test', 'data', 'test.mp3')
    supports_ratings = True
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'originaldate' : '1980',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'arranger' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'djmixer' : 'Foo',
        'mixer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'tracknumber' : '2',
        'totaltracks' : '10',
        'discnumber' : '1',
        'totaldiscs' : '2',
        'compilation' : '1',
        'comment:' : 'Foo',
        'comment:foo' : 'Foo',
        'genre' : 'Foo',
        'bpm' : '80',
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
        #'composersort' : 'Foo',
        #'showsort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'musicip_fingerprint' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        'asin' : 'Foo',
        #'gapless' : '1',
        #'podcast' : '1',
        #'podcasturl' : 'Foo',
        #'show' : 'Foo',
        }


class OggVorbisTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.ogg')
    supports_ratings = True
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        'originaldate' : '1980',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'arranger' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'djmixer' : 'Foo',
        'mixer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'tracknumber' : '2',
        'totaltracks' : '10',
        'discnumber' : '1',
        'totaldiscs' : '2',
        'compilation' : '1',
        'comment:' : 'Foo',
        'comment:foo' : 'Foo',
        'genre' : 'Foo',
        'bpm' : '80',
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
        #'composersort' : 'Foo',
        #'showsort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'musicip_fingerprint' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        'asin' : 'Foo',
        #'gapless' : '1',
        #'podcast' : '1',
        #'podcasturl' : 'Foo',
        #'show' : 'Foo',
        }


class MP4Test(FormatsTest):
    original = os.path.join('test', 'data', 'test.m4a')
    supports_ratings = False
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        #'originaldate' : '1980',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        #'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        #'arranger' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'djmixer' : 'Foo',
        'mixer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'tracknumber' : '2',
        'totaltracks' : '10',
        'discnumber' : '1',
        'totaldiscs' : '2',
        'compilation' : '1',
        'comment:' : 'Foo',
        # FIXME: comment:foo is unsupported in our MP4 implementation
        #'comment:foo' : 'Foo',
        'genre' : 'Foo',
        'bpm' : '80',
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
        'composersort' : 'Foo',
        'showsort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        'musicip_fingerprint' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        'asin' : 'Foo',
        'gapless' : '1',
        'podcast' : '1',
        'podcasturl' : 'Foo',
        'show' : 'Foo',
        }


class WavPackTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.wv')
    supports_ratings = False
    tags = {
        'album' : 'Foo Bar',
        'album' : '1',
        'title' : 'Foo',
        'artist' : 'Foo',
        'albumartist' : 'Foo',
        'date' : '2004',
        #'originaldate' : '1980',
        'artist' : 'Foo',
        'composer' : 'Foo',
        'lyricist' : 'Foo',
        'conductor' : 'Foo',
        'performer:guest vocal' : 'Foo',
        'remixer' : 'Foo',
        'arranger' : 'Foo',
        'engineer' : 'Foo',
        'producer' : 'Foo',
        'djmixer' : 'Foo',
        'mixer' : 'Foo',
        'grouping' : 'Foo',
        'subtitle' : 'Foo',
        'discsubtitle' : 'Foo',
        'tracknumber' : '2',
        'totaltracks' : '10',
        'discnumber' : '1',
        'totaldiscs' : '2',
        'compilation' : '1',
        'comment:' : 'Foo',
        'comment:foo' : 'Foo',
        'genre' : 'Foo',
        'bpm' : '80',
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
        #'composersort' : 'Foo',
        #'showsort' : 'Foo',
        'musicbrainz_trackid' : 'Foo',
        'musicbrainz_albumid' : 'Foo',
        'musicbrainz_artistid' : 'Foo',
        'musicbrainz_albumartistid' : 'Foo',
        'musicbrainz_trmid' : 'Foo',
        'musicbrainz_discid' : 'Foo',
        'musicip_puid' : 'Foo',
        #'musicip_fingerprint' : 'Foo',
        'releasestatus' : 'Foo',
        'releasetype' : 'Foo',
        'asin' : 'Foo',
        #'gapless' : '1',
        #'podcast' : '1',
        #'podcasturl' : 'Foo',
        #'show' : 'Foo',
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

    def test_ogg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ogg'))

    def test_flac(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.flac'))

    def _test_cover_art(self, filename):
        self._set_up(filename)
        try:
            f = picard.formats.open(self.filename)
            metadata = Metadata()
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            jpegFakeData = "JFIF" + ("a" * 1024 * 128)
            metadata.add_image("image/jpeg", jpegFakeData)
            f._save(self.filename, metadata, f.config.setting)

            f = picard.formats.open(self.filename)
            f._load(self.filename)
            self.assertEqual(metadata.images[0]["mime"], "image/jpeg")
            self.assertEqual(metadata.images[0]["data"], jpegFakeData)

            f = picard.formats.open(self.filename)
            metadata = Metadata()
            metadata.add_image("image/png", "PNGfoobar")
            f._save(self.filename, metadata, f.config.setting)

            f = picard.formats.open(self.filename)
            f._load(self.filename)
            self.assertEqual(metadata.images[0]["mime"], "image/png")
            self.assertEqual(metadata.images[0]["data"], "PNGfoobar")
        finally:
            self._tear_down()
