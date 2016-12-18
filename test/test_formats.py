# -*- coding: utf-8 -*-
import os.path
import picard.formats
import unittest
import shutil


from PyQt4 import QtCore
from picard import config, log
from picard.coverart.image import CoverArtImage, TagCoverArtImage
from picard.metadata import Metadata
from tempfile import mkstemp
from contextlib import contextmanager
from ctypes.wintypes import MSG


settings = {
    'enabled_plugins': '',
    'clear_existing_tags': False,
    'remove_extra_padding': False,
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
        self.exit_cleanup = []

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

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
        config.setting = settings.copy()
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
        'key': 'E#m',
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
        'originaldate': '1980-08-30',
        'originalyear': '1980',
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
        #'totaltracks': '10',
        'discnumber': '1',
        'totaldiscs': '2',
        'compilation': '1',
        'comment:': 'Foo',
        # FIXME: comment:foo is unsupported in our WMA implementation
        #'comment:foo': 'Foo',
        'genre': 'Foo',
        'bpm': '80',
        'key': 'E#m',
        'mood': 'Foo',
        'isrc': 'Foo',
        'copyright': 'Foo',
        'lyrics': 'Foo',
        'media': 'Foo',
        'label': 'Foo',
        'catalognumber': 'Foo',
        'barcode': 'Foo',
        'encodedby': 'Foo',
        'encodersettings': 'Foo',
        'albumsort': 'Foo',
        'albumartistsort': 'Foo',
        'artistsort': 'Foo',
        'titlesort': 'Foo',
        'composersort': 'Foo',
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
        'website': 'http://example.com',
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
        'key': 'E#m',
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


class TTATest(FormatsTest):
    original = os.path.join('test', 'data', 'test.tta')
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
        'key': 'E#m',
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


if picard.formats.AiffFile:
    class AIFFTest(FormatsTest):
        original = os.path.join('test', 'data', 'test.aiff')
        supports_ratings = False
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
            'key': 'E#m',
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
        'key': 'E#m',
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
        'key': 'E#m',
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
        'key': 'E#m',
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


class MusepackSV7Test(FormatsTest):
    original = os.path.join('test', 'data', 'test-sv7.mpc')
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
        'key': 'E#m',
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


class MusepackSV8Test(FormatsTest):
    original = os.path.join('test', 'data', 'test-sv8.mpc')
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
        'key': 'E#m',
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

    def _test_cover_art(self, filename):
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
            for t in tests:
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
                image = loaded_metadata.images[0]
                self.assertEqual(image.mimetype, tests[t]['mime'])
                self.assertEqual(image.data, imgdata)
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

    def _test_cover_art_types_only_front(self, filename, expect):
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

class PaddingTester(unittest.TestCase):

    @contextmanager
    def tempcopy(self, filename):
        fdesc, fname = mkstemp(suffix=os.path.splitext(filename)[1])
        os.close(fdesc)
        shutil.copy2(filename, fname)
        self.tmps.append(fname)
        (yield fname)

    @contextmanager
    def tagcoverartimage(self, src, tag='a', types=[u'front'], is_front=True, support_types=True, comment='No comment'):
        with self.tempcopy(src) as fpic:
            with open(fpic, 'rb') as f:
                (yield TagCoverArtImage(fpic, tag, types, is_front, support_types, comment, f.read()))

    def assertIsFile(self, path, msg=None):
        if msg is None:
            msg = "{0} is not a file.".format(path)
        self.assertTrue(os.path.isfile(path), msg)

    def assertFilteredTagDictEqual(self, first, second, msg=None):
        filter_m = lambda m: {k: v for k, v in m.iteritems() if not k.startswith("~")}
        self.assertEqual(filter_m(first), filter_m(second), msg)

    def _assertPicNumber(self, comparator, comparator_word, metadata, expected, msg=None):
        found = len(metadata.images)
        if msg is None:
            msg = "Number of picture should be {0} {1} but is {2}.".format(comparator_word, expected, found)
        comparator(found, expected, msg)

    def assertPicNumberEqual(self, metadata, expected, msg=None):
        self._assertPicNumber(lambda x, y, z: self.assertEqual(x, y, z), "equal to", metadata, expected, msg)
    
    def assertPicNumberGreater(self, metadata, expected, msg=None):
        self._assertPicNumber(lambda x, y, z: self.assertGreater(x, y, z), "greater than", metadata, expected, msg)

    def assertPicNumberGreaterEqual(self, metadata, expected, msg=None):
        self._assertPicNumber(lambda x, y, z: self.assertGreaterEqual(x, y, z), "greater than or equal to", metadata, expected, msg)

    def assertPicNumberLess(self, metadata, expected, msg=None):
        self._assertPicNumber(lambda x, y, z: self.assertLess(x, y, z), "less than", metadata, expected, msg)

    def assertPicNumberLessEqual(self, metadata, expected, msg=None):
        self._assertPicNumber(lambda x, y, z: self.assertLessEqual(x, y, z), "less than or equal to", metadata, expected, msg)

    def _assertFileSize(self, comparator, comparator_word, fname, expected, msg=None):
        self.assertIsFile(fname, msg)
        size = os.path.getsize(fname)
        if msg is None:
            msg = "File size should be {0} {1} but is {2}.".format(comparator_word, expected, size)
        comparator(size, expected, msg)

    def assertFileSizeEqual(self, fname, expected, msg=None):
        self._assertFileSize(lambda x, y, z : self.assertEqual(x, y, z), "equal to", fname, expected, msg)

    def assertFileSizeGreater(self, fname, expected, msg=None):
        self._assertFileSize(lambda x, y, z : self.assertGreater(x, y, z), "greater than", fname, expected, msg)

    def assertFileSizeGreaterEqual(self, fname, expected, msg=None):
        self._assertFileSize(lambda x, y, z : self.assertGreaterEqual(x, y, z), "greater than or equal to", fname, expected, msg)

    def assertFileSizeLess(self, fname, expected, msg=None):
        self._assertFileSize(lambda x, y, z : self.assertLess(x, y, z), "less than", fname, expected, msg)

    def assertFileSizeLessEqual(self, fname, expected, msg=None):
        self._assertFileSize(lambda x, y, z : self.assertLessEqual(x, y, z), "less than or equal to", fname, expected, msg)

    def decomposeFile(self, fname):
        size = os.path.getsize(fname)
        pf = picard.formats.open(fname)
        metadata = pf._load(fname)
        nb_pics = len(metadata.images)
        return (pf, size, metadata, nb_pics)

    def assertEmbedPicture(self, faudio, fpicture):
        with self.tempcopy(faudio) as aud:
            with self.tagcoverartimage(src=fpicture) as pic:
                (paud_0, size_0, metadata_0, nb_pics_0) = self.decomposeFile(aud)
                metadata_1 = Metadata()
                metadata_1.copy(metadata_0)
                metadata_1.append_image(pic)
                paud_0._save(aud, metadata_1)
                (_, _, metadata_2, _) = self.decomposeFile(aud)
                self.assertFilteredTagDictEqual(metadata_1, metadata_2)
                self.assertPicNumberEqual(metadata_2, nb_pics_0 + 1)
                self.assertFileSizeGreater(aud, size_0)

    def assertCreatePaddingFromRemovingPicture(self, faudio, fpicture):
        with self.tempcopy(faudio) as aud:
            with self.tagcoverartimage(src=fpicture) as pic:
                (paud_0, size_0, metadata_0, nb_pics_0) = self.decomposeFile(aud)
                metadata_1 = Metadata()
                metadata_1.copy(metadata_0)
                metadata_1.append_image(pic)
                paud_0._save(aud, metadata_1)
                (paud_2, size_2, metadata_2, nb_pics_2) = self.decomposeFile(aud)
                self.assertFilteredTagDictEqual(metadata_1, metadata_2)
                self.assertPicNumberEqual(metadata_2, nb_pics_0 + 1)
                self.assertFileSizeGreater(aud, size_0)
                config.setting.update({'clear_existing_tags': True})
                paud_2._save(aud, metadata_0)
                (_, _, metadata_3, _) = self.decomposeFile(aud)
                self.assertFilteredTagDictEqual(metadata_3, metadata_0)
                self.assertPicNumberEqual(metadata_3, nb_pics_0)
                self.assertPicNumberEqual(metadata_3, nb_pics_2 - 1)
                self.assertFileSizeEqual(aud, size_2)

    def assertCreateThenRemovePaddingFromRemovingPicture(self, faudio, fpicture):
        with self.tempcopy(faudio) as aud:
            with self.tagcoverartimage(src=fpicture) as pic:
                (paud_0, size_0, metadata_0, nb_pics_0) = self.decomposeFile(aud)
                metadata_1 = Metadata()
                metadata_1.copy(metadata_0)
                metadata_1.append_image(pic)
                paud_0._save(aud, metadata_1)
                (paud_2, size_2, metadata_2, nb_pics_2) = self.decomposeFile(aud)
                self.assertFilteredTagDictEqual(metadata_1, metadata_2)
                self.assertPicNumberEqual(metadata_2, nb_pics_0 + 1)
                self.assertFileSizeGreater(aud, size_0)
                config.setting.update({'clear_existing_tags': True})
                paud_2._save(aud, metadata_0)
                (paud_3, size_3, metadata_3, nb_pics_3) = self.decomposeFile(aud)
                self.assertFilteredTagDictEqual(metadata_3, metadata_0)
                self.assertPicNumberEqual(metadata_3, nb_pics_0)
                self.assertPicNumberEqual(metadata_3, nb_pics_2 - 1)
                self.assertFileSizeEqual(aud, size_2)
                config.setting.update({'remove_extra_padding': True})
                paud_3._save(aud, metadata_0)
                (_, _, metadata_4, _) = self.decomposeFile(aud)
                self.assertFilteredTagDictEqual(metadata_4, metadata_0)
                self.assertFilteredTagDictEqual(metadata_4, metadata_3)
                self.assertPicNumberEqual(metadata_4, nb_pics_0)
                self.assertPicNumberEqual(metadata_4, nb_pics_3)
                self.assertPicNumberEqual(metadata_4, nb_pics_2 - 1)
                self.assertFileSizeLess(aud, size_3)

    def assertRemoveExtraPaddingDoesNotThrowException(self, f):
        with self.tempcopy(f) as ff:
            config.setting.update({'clear_existing_tags': True})
            config.setting.update({'remove_extra_padding': True})
            pff = picard.formats.open(ff)
            metadata = pff._load(ff)
            pff._save(ff, metadata)

    DATA_FILE = os.path.join('test', 'data', 'b2h_test_C.dat')
    IMG_FILE_GIF = os.path.join('test', 'data', 'mb.gif')
    IMG_FILE_JPG = os.path.join('test', 'data', 'mb.jpg')
    IMG_FILE_PNG = os.path.join('test', 'data', 'mb.png')
    AUDIO_FILE_AIFF = os.path.join('test', 'data', 'test.aiff')
    AUDIO_FILE_FLAC = os.path.join('test', 'data', 'test.flac')
    AUDIO_FILE_M4A = os.path.join('test', 'data', 'test.m4a')
    AUDIO_FILE_MP3 = os.path.join('test', 'data', 'test.mp3')
    AUDIO_FILE_OGG = os.path.join('test', 'data', 'test.ogg')
    AUDIO_FILE_TTA = os.path.join('test', 'data', 'test.tta')
    AUDIO_FILE_WMA = os.path.join('test', 'data', 'test.wma')
    AUDIO_FILE_WV = os.path.join('test', 'data', 'test.wv')
    AUDIO_FILE_SV7MPC = os.path.join('test', 'data', 'test-sv7.mpc')
    AUDIO_FILE_SV8MPC = os.path.join('test', 'data', 'test-sv8.mpc')

    def setUp(self):
        self.assertIsFile(self.DATA_FILE)
        self.assertIsFile(self.IMG_FILE_GIF)
        self.assertIsFile(self.IMG_FILE_JPG)
        self.assertIsFile(self.IMG_FILE_PNG)
        self.assertIsFile(self.AUDIO_FILE_AIFF)
        self.assertIsFile(self.AUDIO_FILE_FLAC)
        self.assertIsFile(self.AUDIO_FILE_M4A)
        self.assertIsFile(self.AUDIO_FILE_MP3)
        self.assertIsFile(self.AUDIO_FILE_OGG)
        self.assertIsFile(self.AUDIO_FILE_TTA)
        self.assertIsFile(self.AUDIO_FILE_WMA)
        self.assertIsFile(self.AUDIO_FILE_WV)
        self.assertIsFile(self.AUDIO_FILE_SV7MPC)
        self.assertIsFile(self.AUDIO_FILE_SV8MPC)
        config.setting = settings.copy()
        QtCore.QObject.tagger = FakeTagger()
        self.tmps = list()

    def tearDown(self):
        QtCore.QObject.tagger.run_cleanup()
        for f in self.tmps:
            os.unlink(f)

    # AIFF
    def test_assertRemoveExtraPadding_AIFF(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_AIFF)
    def test_assertEmbedPicture_gif_into_AIFF(self):
        self.assertEmbedPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_AIFF(self):
        self.assertEmbedPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_AIFF(self):
        self.assertEmbedPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_PNG)
    def test_assertCreatePaddingFromRemovingPicture_gif_into_AIFF(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_GIF)
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_AIFF(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_JPG)
    def test_assertCreatePaddingFromRemovingPicture_png_into_AIFF(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_PNG)
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_AIFF(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_GIF)
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_AIFF(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_JPG)
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_AIFF(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_AIFF, self.IMG_FILE_PNG)

    # FLAC
    def test_assertRemoveExtraPadding_FLAC(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_FLAC)
    def test_assertEmbedPicture_gif_into_FLAC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_FLAC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_FLAC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_PNG)
    def test_assertCreatePaddingFromRemovingPicture_gif_into_FLAC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_GIF)
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_FLAC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_JPG)
    def test_assertCreatePaddingFromRemovingPicture_png_into_FLAC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_PNG)
    # Unexpected failure : Padding is not removed!!
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_FLAC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_GIF)
    # Unexpected failure : Padding is not removed!!
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_FLAC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_JPG)
    # Unexpected failure : Padding is not removed!!
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_FLAC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_FLAC, self.IMG_FILE_PNG)

    # M4A
    def test_assertRemoveExtraPadding_M4A(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_M4A)
    @unittest.expectedFailure
    def test_assertEmbedPicture_gif_into_M4A(self):
        self.assertEmbedPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_M4A(self):
        self.assertEmbedPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_M4A(self):
        self.assertEmbedPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_M4A(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_GIF)
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_M4A(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_JPG)
    def test_assertCreatePaddingFromRemovingPicture_png_into_M4A(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_M4A(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_GIF)
    # Unexpected failure : Padding is not removed!!
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_M4A(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_JPG)
    # Unexpected failure : Padding is not removed!!
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_M4A(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_M4A, self.IMG_FILE_PNG)

    # MP3
    def test_assertRemoveExtraPadding_MP3(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_MP3)
    def test_assertEmbedPicture_gif_into_MP3(self):
        self.assertEmbedPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_MP3(self):
        self.assertEmbedPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_MP3(self):
        self.assertEmbedPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_PNG)
    def test_assertCreatePaddingFromRemovingPicture_gif_into_MP3(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_GIF)
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_MP3(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_JPG)
    def test_assertCreatePaddingFromRemovingPicture_png_into_MP3(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_PNG)
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_MP3(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_GIF)
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_MP3(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_JPG)
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_MP3(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_MP3, self.IMG_FILE_PNG)

    # OGG
    def test_assertRemoveExtraPadding_OGG(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_OGG)
    def test_assertEmbedPicture_gif_into_OGG(self):
        self.assertEmbedPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_OGG(self):
        self.assertEmbedPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_OGG(self):
        self.assertEmbedPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_OGG(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_OGG(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_png_into_OGG(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_OGG(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_OGG(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_OGG(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_OGG, self.IMG_FILE_PNG)

    # TTA
    def test_assertRemoveExtraPadding_TTA(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_TTA)
    def test_assertEmbedPicture_gif_into_TTA(self):
        self.assertEmbedPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_TTA(self):
        self.assertEmbedPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_TTA(self):
        self.assertEmbedPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_TTA(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_TTA(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_png_into_TTA(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_TTA(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_TTA(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_TTA(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_TTA, self.IMG_FILE_PNG)

    # WMA
    def test_assertRemoveExtraPadding_WMA(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_WMA)
    def test_assertEmbedPicture_gif_into_WMA(self):
        self.assertEmbedPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_WMA(self):
        self.assertEmbedPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_WMA(self):
        self.assertEmbedPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_WMA(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_WMA(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_png_into_WMA(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_WMA(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_WMA(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_WMA(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_WMA, self.IMG_FILE_PNG)

    # WV
    def test_assertRemoveExtraPadding_WV(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_WV)
    def test_assertEmbedPicture_gif_into_WV(self):
        self.assertEmbedPicture(self.AUDIO_FILE_WV, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_WV(self):
        self.assertEmbedPicture(self.AUDIO_FILE_WV, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_WV(self):
        self.assertEmbedPicture(self.AUDIO_FILE_WV, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_WV(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_WV, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_WV(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_WV, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_png_into_WV(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_WV, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_WV(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_WV, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_WV(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_WV, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_WV(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_WV, self.IMG_FILE_PNG)

    # SV7MPC
    def test_assertRemoveExtraPadding_SV7MPC(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_SV7MPC)
    def test_assertEmbedPicture_gif_into_SV7MPC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_SV7MPC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_SV7MPC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_SV7MPC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_SV7MPC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_png_into_SV7MPC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_SV7MPC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_SV7MPC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_SV7MPC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_SV7MPC, self.IMG_FILE_PNG)

    # SV8MPC
    def test_assertRemoveExtraPadding_SV8MPC(self):
        self.assertRemoveExtraPaddingDoesNotThrowException(self.AUDIO_FILE_SV8MPC)
    def test_assertEmbedPicture_gif_into_SV8MPC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_GIF)
    def test_assertEmbedPicture_jpg_into_SV8MPC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_JPG)
    def test_assertEmbedPicture_png_into_SV8MPC(self):
        self.assertEmbedPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_gif_into_SV8MPC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_jpg_into_SV8MPC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreatePaddingFromRemovingPicture_png_into_SV8MPC(self):
        self.assertCreatePaddingFromRemovingPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_PNG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_gif_into_SV8MPC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_GIF)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_jpg_into_SV8MPC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_JPG)
    @unittest.expectedFailure
    def test_assertCreateThenRemovePaddingFromRemovingPicture_png_into_SV8MPC(self):
        self.assertCreateThenRemovePaddingFromRemovingPicture(self.AUDIO_FILE_SV8MPC, self.IMG_FILE_PNG)
