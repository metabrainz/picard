# -*- coding: utf-8 -*-
import os.path
import picard.formats
import unittest
import shutil

from PyQt5 import QtCore
from picard import config, log
from picard.coverart.image import CoverArtImage, TagCoverArtImage
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
    'id3v23_join_with': '/',
    'remove_ape_from_mp3': False,
    'remove_id3_from_flac': False,
    'rating_steps': 6,
    'rating_user_email': 'users@musicbrainz.org',
    'embed_only_one_front_image': False,
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
    f = picard.formats.open_(filename)
    loaded_metadata = f._load(filename)
    f._copy_loaded_metadata(loaded_metadata)
    f._save(filename, metadata)
    f = picard.formats.open_(filename)
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
        for (key, value) in self.tags.items():
            metadata[key] = value
        loaded_metadata = save_and_load_metadata(self.filename, metadata)
        for (key, value) in self.tags.items():
            # if key == 'comment:foo':
            #    print "%r" % loaded_metadata
            self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

    def test_delete_simple_tags(self):
        if not self.original:
            return
        metadata = Metadata()
        for (key, value) in self.tags.items():
            metadata[key] = value
        if self.supports_ratings:
            metadata['~rating'] = 1
        original_metadata = save_and_load_metadata(self.filename, metadata)
        metadata.delete('albumartist')
        if self.supports_ratings:
            metadata.delete('~rating')
        new_metadata = save_and_load_metadata(self.filename, metadata)
        self.assertIn('albumartist', original_metadata.keys())
        self.assertNotIn('albumartist', new_metadata.keys())
        if self.supports_ratings:
            self.assertIn('~rating', original_metadata.keys())
            self.assertNotIn('~rating', new_metadata.keys())

    def test_delete_complex_tags(self):
        if not self.original:
            return
        metadata = Metadata()

        for (key, value) in self.tags.items():
            metadata[key] = value

        original_metadata = save_and_load_metadata(self.filename, metadata)
        metadata.delete('totaldiscs')
        new_metadata = save_and_load_metadata(self.filename, metadata)

        self.assertIn('totaldiscs', original_metadata)
        if self.original.split(".")[1] == 'm4a':
            self.assertEqual(u'0', new_metadata['totaldiscs'])
        else:
            self.assertNotIn('totaldiscs', new_metadata)

    def test_delete_performer(self):
        if not self.original:
            return
        if 'performer:guest vocal' in self.tags:
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value

            metadata['performer:piano'] = 'Foo'

            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('performer:piano')
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('performer:guest vocal', original_metadata)
            self.assertIn('performer:guest vocal', new_metadata)
            self.assertIn('performer:piano', original_metadata)
            self.assertNotIn('performer:piano', new_metadata)

    def test_ratings(self):
        if not self.original or not self.supports_ratings:
            return
        for rating in range(6):
            rating = 1
            metadata = Metadata()
            metadata['~rating'] = rating
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(int(loaded_metadata['~rating']), rating, '~rating: %r != %r' % (loaded_metadata['~rating'], rating))

    def test_guess_format(self):
        if self.original:
            fd, temp_file = mkstemp()
            os.close(fd)
            self.addCleanup(os.unlink, temp_file)
            shutil.copy(self.original, temp_file)
            audio = picard.formats.guess_format(temp_file)
            audio_original = picard.formats.open_(self.filename)
            self.assertEqual(type(audio), type(audio_original))

    def test_split_ext(self):
        if self.original:
            f = picard.formats.open_(self.filename)
            self.assertEqual(f._fixed_splitext(f.filename), os.path.splitext(f.filename))
            self.assertEqual(f._fixed_splitext(f.EXTENSIONS[0]), ('', f.EXTENSIONS[0]))
            self.assertEqual(f._fixed_splitext('.test'), os.path.splitext('.test'))
            self.assertNotEqual(f._fixed_splitext(f.EXTENSIONS[0]), os.path.splitext(f.EXTENSIONS[0]))


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


class ID3Test(FormatsTest):

    def test_id3_freeform_delete(self):
        if not self.original:
            return
        metadata = Metadata()
        for (key, value) in self.tags.items():
            metadata[key] = value

        metadata['Foo'] = 'Foo'
        original_metadata = save_and_load_metadata(self.filename, metadata)
        metadata.delete('Foo')
        new_metadata = save_and_load_metadata(self.filename, metadata)

        self.assertIn('Foo', original_metadata)
        self.assertNotIn('Foo', new_metadata)

    def test_id3_ufid_delete(self):
        if not self.original:
            return
        metadata = Metadata()
        for (key, value) in self.tags.items():
            metadata[key] = value
        metadata['musicbrainz_recordingid'] = "Foo"
        original_metadata = save_and_load_metadata(self.filename, metadata)
        metadata.delete('musicbrainz_recordingid')
        new_metadata = save_and_load_metadata(self.filename, metadata)

        self.assertIn('musicbrainz_recordingid', original_metadata)
        self.assertNotIn('musicbrainz_recordingid', new_metadata)

    def test_id3_multiple_freeform_delete(self):
        if not self.original:
            return
        metadata = Metadata()
        for (key, value) in self.tags.items():
            metadata[key] = value

        metadata['Foo'] = 'Foo'
        metadata['Bar'] = 'Foo'
        metadata['FooBar'] = 'Foo'
        original_metadata = save_and_load_metadata(self.filename, metadata)
        metadata.delete('Foo')
        metadata.delete('Bar')
        new_metadata = save_and_load_metadata(self.filename, metadata)

        self.assertIn('Foo', original_metadata)
        self.assertIn('Bar', original_metadata)
        self.assertIn('FooBar', original_metadata)
        self.assertNotIn('Foo', new_metadata)
        self.assertNotIn('Bar', new_metadata)
        self.assertIn('FooBar', new_metadata)

    def test_performer_duplication(self):
        if not self.original:
            return

        def reset_id3_ver(): config.setting['write_id3v23'] = False

        self.addCleanup(reset_id3_ver)
        config.setting['write_id3v23'] = True
        metadata = Metadata()
        tags = {
            'album': 'Foo',
            'title': 'Foo',
            'artist': 'Foo',
            'performer:piano': 'Foo'
        }

        for (key, value) in tags.items():
            metadata[key] = value

        original_metadata = save_and_load_metadata(self.filename, metadata)
        new_metadata = save_and_load_metadata(self.filename, original_metadata)

        self.assertEqual(len(new_metadata['performer:piano']), len(original_metadata['performer:piano']))

    def test_comment_delete(self):
        if not self.original:
            return
        metadata = Metadata()
        for (key, value) in self.tags.items():
            metadata[key] = value
        metadata['comment:bar'] = 'Foo'
        original_metadata = save_and_load_metadata(self.filename, metadata)
        metadata.delete('comment:bar')
        new_metadata = save_and_load_metadata(self.filename, metadata)

        self.assertIn('comment:foo', original_metadata)
        self.assertIn('comment:bar', original_metadata)
        self.assertIn('comment:foo', new_metadata)
        self.assertNotIn('comment:bar', new_metadata)

    def test_id3v23_simple_tags(self):
        if not self.original:
            return
        def reset_to_id3v24(): config.setting['write_id3v23'] = False
        config.setting['write_id3v23'] = True
        self.addCleanup(reset_to_id3v24)
        metadata = Metadata()
        for (key, value) in self.tags.items():
            metadata[key] = value
        loaded_metadata = save_and_load_metadata(self.filename, metadata)
        for (key, value) in self.tags.items():
            # if key == 'comment:foo':
            #    print "%r" % loaded_metadata
            self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))


class MP3Test(ID3Test):
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


class TTATest(ID3Test):
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
    class AIFFTest(ID3Test):
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
            # 'discsubtitle': 'Foo',
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
            # 'albumsort': 'Foo',
            'albumartistsort': 'Foo',
            # 'artistsort': 'Foo',
            # 'titlesort': 'Foo',
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
    'embed_only_one_front_image': True,
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

    def _test_cover_art(self, filename):
        self._set_up(filename)
        try:
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            tests = {
                'jpg': {
                    'mime': 'image/jpeg',
                    'data': self.jpegdata + b"a" * 1024 * 128
                },
                'png': {
                    'mime': 'image/png',
                    'data': self.pngdata + b"a" * 1024 * 128
                },
            }
            for t in tests:
                f = picard.formats.open_(self.filename)
                metadata = Metadata()
                imgdata = tests[t]['data']
                metadata.append_image(
                    CoverArtImage(
                        data=imgdata
                    )
                )
                f._save(self.filename, metadata)

                f = picard.formats.open_(self.filename)
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
                data=imgdata + b'a',
                support_types=True,
                types=[u'booklet', u'front'],
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='b',
                tag='b',
                data=imgdata + b'b',
                support_types=True,
                types=[u'back'],
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='c',
                tag='c',
                data=imgdata + b'c',
                support_types=True,
                types=[u'front'],
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='d',
                tag='d',
                data=imgdata + b'd',
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='e',
                tag='e',
                data=imgdata + b'e',
                is_front=False
            )
        )
        metadata.append_image(
            TagCoverArtImage(
                file='f',
                tag='f',
                data=imgdata + b'f',
                types=[u'front']
            )
        )
        metadata.append_image(
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
