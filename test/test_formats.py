import os.path
import picard.formats
import unittest
import shutil


from PyQt4 import QtCore
from collections import defaultdict
from picard import config, log
from picard.metadata import Metadata
from tempfile import mkstemp


settings = {
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


class FakeTagger(QtCore.QObject):

    tagger_stats_changed = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)
        QtCore.QObject.config = config
        QtCore.QObject.log = log
        self.tagger_stats_changed.connect(self.emit)
        self.images = defaultdict(lambda: None)

    def emit(self, *args):
        pass


def save_and_load_metadata(filename, metadata):
    """Save new metadata to a file and load it again."""
    f = picard.formats.open(filename)
    loaded_metadata = f._load(filename)
    f._copy_loaded_metadata(loaded_metadata)
    f._save(filename, metadata)
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
        config.setting = settings
        QtCore.QObject.tagger = FakeTagger()

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
        'album': 'Foo Bar',
        'album': '1',
        'title': 'Foo',
        'artist': 'Foo',
        'albumartist': 'Foo',
        'date': '2004',
        'originaldate': '1980',
        'artist': 'Foo',
        'composer': 'Foo',
        'lyricist': 'Foo',
        'conductor': 'Foo',
        'performer:guest vocal': 'Foo',
        'remixer': 'Foo',
        'arranger': 'Foo',
        'engineer': 'Foo',
        'producer': 'Foo',
        'djmixer': 'Foo',
        'mixer': 'Foo',
        'grouping': 'Foo',
        'subtitle': 'Foo',
        'discsubtitle': 'Foo',
        'tracknumber': '2',
        'totaltracks': '10',
        'discnumber': '1',
        'totaldiscs': '2',
        'compilation': '1',
        'comment:': 'Foo',
        'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        'media': 'Foo',
        'label': 'Foo',
        'catalognumber': 'Foo',
        'barcode': 'Foo',
        'encodedby': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        #'composersort': 'Foo',
        #'showsort': 'Foo',
        'musicbrainz_trackid': 'Foo',
        'musicbrainz_albumid': 'Foo',
        'musicbrainz_artistid': 'Foo',
        'musicbrainz_albumartistid': 'Foo',
        'musicbrainz_trmid': 'Foo',
        'musicbrainz_discid': 'Foo',
        'musicip_puid': 'Foo',
        'musicip_fingerprint': 'Foo',
        'releasestatus': 'Foo',
        'releasetype': 'Foo',
        'asin': 'Foo',
        #'gapless': '1',
        #'podcast': '1',
        #'podcasturl': 'Foo',
        #'show': 'Foo',
    }


class WMATest(FormatsTest):
    original = os.path.join('test', 'data', 'test.wma')
    supports_ratings = True
    tags = {
        'album': 'Foo Bar',
        'album': '1',
        'title': 'Foo',
        'artist': 'Foo',
        'albumartist': 'Foo',
        'date': '2004',
        'originaldate': '1980',
        'artist': 'Foo',
        'composer': 'Foo',
        'lyricist': 'Foo',
        'conductor': 'Foo',
        #'performer:guest vocal': 'Foo',
        'remixer': 'Foo',
        #'arranger': 'Foo',
        #'engineer': 'Foo',
        'producer': 'Foo',
        #'djmixer': 'Foo',
        #'mixer': 'Foo',
        'grouping': 'Foo',
        'subtitle': 'Foo',
        'discsubtitle': 'Foo',
        'tracknumber': '2',
        #'totaltracks': '10',
        'discnumber': '1',
        #'totaldiscs': '2',
        #'compilation': '1',
        'comment:': 'Foo',
        # FIXME: comment:foo is unsupported in our WMA implementation
        #'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        #'media': 'Foo',
        'label': 'Foo',
        #'catalognumber': 'Foo',
        #'barcode': 'Foo',
        'encodedby': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        #'composersort': 'Foo',
        #'showsort': 'Foo',
        'musicbrainz_trackid': 'Foo',
        'musicbrainz_albumid': 'Foo',
        'musicbrainz_artistid': 'Foo',
        'musicbrainz_albumartistid': 'Foo',
        'musicbrainz_trmid': 'Foo',
        'musicbrainz_discid': 'Foo',
        'musicip_puid': 'Foo',
        #'musicip_fingerprint': 'Foo',
        'releasestatus': 'Foo',
        'releasetype': 'Foo',
        #'asin': 'Foo',
        #'gapless': '1',
        #'podcast': '1',
        #'podcasturl': 'Foo',
        #'show': 'Foo',
    }


class MP3Test(FormatsTest):
    original = os.path.join('test', 'data', 'test.mp3')
    supports_ratings = True
    tags = {
        'album': 'Foo Bar',
        'album': '1',
        'title': 'Foo',
        'artist': 'Foo',
        'albumartist': 'Foo',
        'date': '2004',
        'originaldate': '1980',
        'artist': 'Foo',
        'composer': 'Foo',
        'lyricist': 'Foo',
        'conductor': 'Foo',
        'performer:guest vocal': 'Foo',
        'remixer': 'Foo',
        'arranger': 'Foo',
        'engineer': 'Foo',
        'producer': 'Foo',
        'djmixer': 'Foo',
        'mixer': 'Foo',
        'grouping': 'Foo',
        'subtitle': 'Foo',
        'discsubtitle': 'Foo',
        'tracknumber': '2',
        'totaltracks': '10',
        'discnumber': '1',
        'totaldiscs': '2',
        'compilation': '1',
        'comment:': 'Foo',
        'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        'media': 'Foo',
        'label': 'Foo',
        'catalognumber': 'Foo',
        'barcode': 'Foo',
        'encodedby': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        #'composersort': 'Foo',
        #'showsort': 'Foo',
        'musicbrainz_trackid': 'Foo',
        'musicbrainz_albumid': 'Foo',
        'musicbrainz_artistid': 'Foo',
        'musicbrainz_albumartistid': 'Foo',
        'musicbrainz_trmid': 'Foo',
        'musicbrainz_discid': 'Foo',
        'musicip_puid': 'Foo',
        'musicip_fingerprint': 'Foo',
        'releasestatus': 'Foo',
        'releasetype': 'Foo',
        'asin': 'Foo',
        #'gapless': '1',
        #'podcast': '1',
        #'podcasturl': 'Foo',
        #'show': 'Foo',
    }


class OggVorbisTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.ogg')
    supports_ratings = True
    tags = {
        'album': 'Foo Bar',
        'album': '1',
        'title': 'Foo',
        'artist': 'Foo',
        'albumartist': 'Foo',
        'date': '2004',
        'originaldate': '1980',
        'artist': 'Foo',
        'composer': 'Foo',
        'lyricist': 'Foo',
        'conductor': 'Foo',
        'performer:guest vocal': 'Foo',
        'remixer': 'Foo',
        'arranger': 'Foo',
        'engineer': 'Foo',
        'producer': 'Foo',
        'djmixer': 'Foo',
        'mixer': 'Foo',
        'grouping': 'Foo',
        'subtitle': 'Foo',
        'discsubtitle': 'Foo',
        'tracknumber': '2',
        'totaltracks': '10',
        'discnumber': '1',
        'totaldiscs': '2',
        'compilation': '1',
        'comment:': 'Foo',
        'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        'media': 'Foo',
        'label': 'Foo',
        'catalognumber': 'Foo',
        'barcode': 'Foo',
        'encodedby': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        #'composersort': 'Foo',
        #'showsort': 'Foo',
        'musicbrainz_trackid': 'Foo',
        'musicbrainz_albumid': 'Foo',
        'musicbrainz_artistid': 'Foo',
        'musicbrainz_albumartistid': 'Foo',
        'musicbrainz_trmid': 'Foo',
        'musicbrainz_discid': 'Foo',
        'musicip_puid': 'Foo',
        'musicip_fingerprint': 'Foo',
        'releasestatus': 'Foo',
        'releasetype': 'Foo',
        'asin': 'Foo',
        #'gapless': '1',
        #'podcast': '1',
        #'podcasturl': 'Foo',
        #'show': 'Foo',
    }


class MP4Test(FormatsTest):
    original = os.path.join('test', 'data', 'test.m4a')
    supports_ratings = False
    tags = {
        'album': 'Foo Bar',
        'album': '1',
        'title': 'Foo',
        'artist': 'Foo',
        'albumartist': 'Foo',
        'date': '2004',
        #'originaldate': '1980',
        'artist': 'Foo',
        'composer': 'Foo',
        'lyricist': 'Foo',
        'conductor': 'Foo',
        #'performer:guest vocal': 'Foo',
        'remixer': 'Foo',
        #'arranger': 'Foo',
        'engineer': 'Foo',
        'producer': 'Foo',
        'djmixer': 'Foo',
        'mixer': 'Foo',
        'grouping': 'Foo',
        'subtitle': 'Foo',
        'discsubtitle': 'Foo',
        'tracknumber': '2',
        'totaltracks': '10',
        'discnumber': '1',
        'totaldiscs': '2',
        'compilation': '1',
        'comment:': 'Foo',
        # FIXME: comment:foo is unsupported in our MP4 implementation
        #'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        'media': 'Foo',
        'label': 'Foo',
        'catalognumber': 'Foo',
        'barcode': 'Foo',
        'encodedby': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        'composersort': 'Foo',
        'showsort': 'Foo',
        'musicbrainz_trackid': 'Foo',
        'musicbrainz_albumid': 'Foo',
        'musicbrainz_artistid': 'Foo',
        'musicbrainz_albumartistid': 'Foo',
        'musicbrainz_trmid': 'Foo',
        'musicbrainz_discid': 'Foo',
        'musicip_puid': 'Foo',
        'musicip_fingerprint': 'Foo',
        'releasestatus': 'Foo',
        'releasetype': 'Foo',
        'asin': 'Foo',
        'gapless': '1',
        'podcast': '1',
        'podcasturl': 'Foo',
        'show': 'Foo',
    }


class WavPackTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.wv')
    supports_ratings = False
    tags = {
        'album': 'Foo Bar',
        'album': '1',
        'title': 'Foo',
        'artist': 'Foo',
        'albumartist': 'Foo',
        'date': '2004',
        #'originaldate': '1980',
        'artist': 'Foo',
        'composer': 'Foo',
        'lyricist': 'Foo',
        'conductor': 'Foo',
        'performer:guest vocal': 'Foo',
        'remixer': 'Foo',
        'arranger': 'Foo',
        'engineer': 'Foo',
        'producer': 'Foo',
        'djmixer': 'Foo',
        'mixer': 'Foo',
        'grouping': 'Foo',
        'subtitle': 'Foo',
        'discsubtitle': 'Foo',
        'tracknumber': '2',
        'totaltracks': '10',
        'discnumber': '1',
        'totaldiscs': '2',
        'compilation': '1',
        'comment:': 'Foo',
        'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        'media': 'Foo',
        'label': 'Foo',
        'catalognumber': 'Foo',
        'barcode': 'Foo',
        'encodedby': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        #'composersort': 'Foo',
        #'showsort': 'Foo',
        'musicbrainz_trackid': 'Foo',
        'musicbrainz_albumid': 'Foo',
        'musicbrainz_artistid': 'Foo',
        'musicbrainz_albumartistid': 'Foo',
        'musicbrainz_trmid': 'Foo',
        'musicbrainz_discid': 'Foo',
        'musicip_puid': 'Foo',
        #'musicip_fingerprint': 'Foo',
        'releasestatus': 'Foo',
        'releasetype': 'Foo',
        'asin': 'Foo',
        #'gapless': '1',
        #'podcast': '1',
        #'podcasturl': 'Foo',
        #'show': 'Foo',
    }


class TestCoverArt(unittest.TestCase):

    def _set_up(self, original):
        fd, self.filename = mkstemp(suffix=os.path.splitext(original)[1])
        os.close(fd)
        shutil.copy(original, self.filename)
        QtCore.QObject.tagger = FakeTagger()

    def _tear_down(self):
        map(lambda i: i._delete(), QtCore.QObject.tagger.images.itervalues())
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
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            dummyload = "a" * 1024 * 128
            tests = {
                'jpg': {
                    'mime': 'image/jpeg',
                    'head': 'JFIF'
                },
                'png': {
                    'mime': 'image/png',
                    'head': 'PNG'
                },
            }
            for t in tests:
                f = picard.formats.open(self.filename)
                metadata = Metadata()
                imgdata = tests[t]['head'] + dummyload
                metadata.make_and_add_image(tests[t]['mime'], imgdata)
                f._save(self.filename, metadata)

                f = picard.formats.open(self.filename)
                loaded_metadata = f._load(self.filename)
                image = loaded_metadata.images[0]
                self.assertEqual(image.mimetype, tests[t]['mime'])
                self.assertEqual(image.data, imgdata)
        finally:
            self._tear_down()
