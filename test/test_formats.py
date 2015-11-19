# -*- coding: utf-8 -*-

# Set the following flag to fail tests which have warning or info log messages.
# This flag is available for identifying missing code in format processing:
# a. test metadata which is being saved and loaded as user tags rather than known tags;
# b. missing _supported_tags
DEBUG = False

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


TAG_DATA = {
    'acoustid_fingerprint': u'ACOUSTID Fingerprint',
    'acoustid_id': u'ACOUSTID ID',
    'album': u'ALBUM Foo Bar',
    'albumartist': u'ALBUMARTIST Bar Foo',
    'albumartists': [u'ALBUMARTISTS1 Foo Bar', u'ALBUMARTISTS2 Bar Foo'],
    'albumartistsort': u'ALBUMARTISTSORT Foo, Bar',
    'albumgenre': [u'ALBUMGENRE Foo', u'ALBUMGENRE Bar'],
    'albumrating': u'4.5',
    'albumsort': u'ALBUMSORT Bar, Foo',
    'arranger': [u'ARRANGER Foo', u'ARRANGER Bar'],
    'artist': u'ARTIST1 Foo Bar with ARTIST2 Bar Foo',
    'artists': [u'ARTISTS1 Foo Bar', u'ARTISTS2 Bar Foo'],
    'artistsort': u'ARTISTSORT Bar, Foo',
    'asin': u'ASIN Foo',
    'barcode': u'BARCODE Foo',
    'bpm': u'81.2345',
    'catalognumber': [u'CATALOG Foo', u'CATALOG Bar'],
    'category': u'CATEGORY Bar',
    'comment': u'COMMENT Line1\nLine2\nLine3',
    'comment:foo': u'COMMENT:Foo FooLine1\nFooLine2\nFooLine3',
    'comment:bar': [u'COMMENT:Bar Bar1', u'Bar2', u'Bar3'],
    'compilation': u'1',
    'composer': [u'COMPOSER Foo', u'COMPOSER Bar'],
    'composersort': [u'COMPOSERSORT ooF', u'COMPOSERSORT raB'],
    'conductor': [u'CONDUCTOR Foo', u'CONDUCTOR Bar'],
    'copyright': u'COPYRIGHT Bar',
    'country': u'COUNTRY Foo',
    'date': u'2004-12-31',
    'discnumber': u'3',
    'discsubtitle': u'DISCSUBTITLE Foo',
    'djmixer': [u'DJMIXER Foo', u'DJMIXER Bar'],
    'encodedby': u'ENCODEDBY Bar',
    'encodersettings': u'ENCODERSETTINGS Foo',
    'encodingtime': u'2015-11-05',
    'engineer': [u'ENGINEER Foo1', u'ENGINEER Foo2'],
    'genre': [u'GENRE Foo', u'GENRE Bar'],
    'grouping': [u'GROUPING Foo', u'GROUPING Bar'],
    'isrc': [u'ISRC Foo', u'ISRC Bar'],
    'key': u'E#m',
    'keywords': [u'KEYWORDS Foo', u'KEYWORDS Bar'],
    'label': [u'LABEL Foo', u'LABEL Bar'],
    'language': u'LANGUAGE Foo',
    'license': u'http://license.org',
    'lyricist': [u'LYRICIST Foo', u'LYRICIST Bar'],
    'lyrics': u'LYRICS Line1\nLine2\nLine3',
    'lyrics:foo': u'LYRICS:foo FooLine1\nFooLine2\nFooLine3',
    'lyrics:bar': [u'LYRICS:bar FooLine1', u'FooLine2', u'FooLine3'],
    'media': u'MEDIA Foo',
    'mixer': [u'MIXER Foo', u'MIXER Bar'],
    'mood': [u'MOOD Foo', u'MOOD Bar'],
    'musicbrainz_albumartistid': u'ALBUMARTIST-MBID',
    'musicbrainz_albumid': u'RELEASE-MBID',
    'musicbrainz_artistid': u'ARTIST-MBID',
    'musicbrainz_discid': u'DISCID',
    'musicbrainz_labelid': u'LABEL-MBID',
    'musicbrainz_original_albumid': u'ORIGRELEASE-MBID',
    'musicbrainz_original_artistid': u'ORIGARTIST-MBID',
    'musicbrainz_recordingid': u'RECORDING-MBID',
    'musicbrainz_releasegroupid': u'RELGRP-MBID',
    'musicbrainz_trackid': u'TRACK-MBID',
    'musicbrainz_workid': u'WORK-MBID',
    'musicip_fingerprint': u'MusicIP Fingerprint Foo',
    'musicip_puid': u'MusicIP PUID Bar',
    'occasion': [u'OCCASION Foo', u'OCCASION Bar'],
    'originalalbum': u'ORIGINALALBUM Foo',
    'originalartist': [u'ORIGINALARTIST Foo', u'ORIGINALARTIST Bar'],
    'originaldate': u'1980-08-30',
    'originalyear': u'1980',
    'originallyricist': [u'ORIGINALLYRICIST Foo', u'ORIGINALLYRICIST Bar'],
    'performer:': u'PERFORMER: Foo bar',
    'performer:foo': u'PERFORMER:foo Foo',
    'performer:bar': [u'PERFORMER:bar Bar1', u'PERFORMER:bar Bar2'],
    'performer:lead vocals': u'PERFORMER:lead_vocals Foo',
    'playdelay': u'1234',
    'producer': [u'PRODUCER Foo', u'PRODUCER Bar'],
    'quality': u'QUALITY Foo',
    'recordingcopyright': u'PHONORIGHT Bar',
    'recordingdate': u'1969-02-27',
    'recordinglocation': u'RECORDINGLOCATION Bar',
    'releasecountry': u'RELEASECOUNTRY Foo',
    'releasestatus': u'RELEASESTATUS Bar',
    'releasetype': [u'RELEASETYPE Foo', u'RELEASETYPE Bar'],
    'remixer': [u'REMIXER Foo', u'REMIXER Bar'],
    'script': u'SCRIPT Foo',
    'subtitle': u'SUBTITLE Foo Bar',
    'tempo': u'TEMPO Foo',
    'title': u'TITLE Bar Foo',
    'titlesort': u'TITLESORT Foo, Bar',
    'totaldiscs': u'4',
    'totaltracks': u'2',
    'tracknumber': u'1',
    'web_lyrics': u'http://lyrics.org/track',
    'web_discogs_artist': u'http://www.discogs.com/stuff/artist/stuff',
    'web_discogs_label': u'http://www.discogs.com/stuff/label/stuff',
    'web_discogs_release': u'http://www.discogs.com/stuff/release/stuff',
    'web_discogs_releasegroup': u'http://www.discogs.com/stuff/master/stuff',
    'web_official_artist': u'http://artist.org',
    'web_official_label': u'http://label.org/',
    'web_official_release': u'http://label.org/release',
    'web_wikipedia_artist': u'http://en.wikipedia.org/wiki/artistpage?query#hash',
    'web_wikipedia_label': u'http://en.wikipedia.org/wiki/labelpage?query#hash',
    'web_wikipedia_release': u'http://en.wikipedia.org/wiki/releasepage?query#hash',
    'web_wikipedia_work': u'http://en.wikipedia.org/wiki/workpage?query#hash',
    'work': u'WORK Foo',
    'writer': [u'WRITER Foo', u'WRITER Bar'],
    '~lyrics_sync': u'{"content_type": 1, "text": [["My", 1], ["Tune", 2]], "timestamp_format": 2}',
    '~lyrics_sync:bar(fra)': u'{"content_type": 1, "text": [["Foo", 1], ["Bar", 2]], "timestamp_format": 2}',
    '~lyrics_sync:foo(eng)': u'{"content_type": 1, "text": [["Bar", 1], ["Foo", 2]], "timestamp_format": 2}',
    '~rating': u'3',
    'web_coverart': u'http://coverartarchive.org',
    'web_musicbrainz_artist': u'http://musicbrainz.org/artist/ARTIST-MBID',
    'web_musicbrainz_label': u'http://musicbrainz.org/label/LABEL-MBID',
    'web_musicbrainz_recording': u'http://musicbrainz.org/recording/RECORDING-MBID',
    'web_musicbrainz_release': u'http://musicbrainz.org/release/RELEASE-MBID',
    'web_musicbrainz_releasegroup': u'http://musicbrainz.org/release-group/RELGRP-MBID',
    'web_musicbrainz_work': u'http://musicbrainz.org/work/WORK-MBID',
    'usertag': u'USERTAG Foo', # This undefined tag is deliberately included
}


class verify_tag_data(unittest.TestCase):
    # Check that:
    #   All test tags are valid
    #   All valid tags are in the test data

    def test_data_valid(self):
        failures = []
        for tag in TAG_DATA:
            if ':' in tag:
                tag = tag.split(':' ,1)[0]
                if not tag in TAG_NAMES \
                and not tag + ":" in TAG_NAMES:
                    failures.append(tag)
            elif not tag in TAG_NAMES and tag != 'usertag':
                failures.append(tag)
        if failures:
            self.fail('\n\nThe following test tags are not defined as Picard tags: ' + ', '.join(sorted(failures)))

    def test_data_comprehensive(self):
        failures = []
        for tag_name in TAG_NAMES:
            tag_colon = tag_name
            if not tag_name.startswith('~') and tag_name not in TAG_DATA:
                if not tag_name.endswith(':'):
                    tag_colon += ':'
                for tag in TAG_DATA:
                    if tag.startswith(tag_colon):
                        break
                else:
                    failures.append(tag_name)
        if failures:
            self.fail('\n\nThe following tags are not defined in test data: ' + ', '.join(sorted(failures)))


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

    def shortDescription(self):
        if self.test_format:
            return "FAILED IN: %s" % self.test_format.__class__.__module__

    test_format = None
    test_file = None
    test_tags = None

    def _log_receiver(self, level, time, msg):
        if level in log._log_prefixes:
            msg = "%s: %s" % (log._log_prefixes[level], msg.decode('ascii', 'replace'))
        self.log_messages.append((level, msg))

    write_id3v23 = False

    def setUp(self):
        if self.id().startswith('test.test_formats.FormatsTest.'):
            self.skipTest('Base test class')
        if not self.test_file:
            self.fail('\n\nTest filename not provided.')
        if not self.test_tags:
            self.fail('\n\nTest tags not provided.')
        fd, self.filename = mkstemp(suffix=os.path.splitext(self.test_file)[1])
        os.close(fd)
        shutil.copy(self.test_file, self.filename)
        config.setting = settings.copy()
        config.setting['write_id3v23'] = self.write_id3v23
        QtCore.QObject.tagger = FakeTagger()
        self.log_messages = []
        log.main_logger.unregister_receiver(log._stderr_receiver)
        log.main_logger.register_receiver(self._log_receiver)

    def tearDown(self):
        log.main_logger.unregister_receiver(self._log_receiver)
        if not self.test_file:
            return
        os.unlink(self.filename)

    def test_tags_valid(self):
        self.test_format = picard.formats.open(self.filename)
        if not hasattr(self.test_format, '_supported_tags'):
            if DEBUG:
                self.fail('\n\nFile format does not list supported tags.')
            else:
                self.skipTest('File format does not list supported tags.')

        failures = []
        format_specific = ''.join([
            '~',
            self.test_format.__class__.__module__.rsplit('.', 1)[1].lower(),
            ':',
        ])
        for tag in self.test_tags:
            if ':' in tag and not tag.startswith(format_specific):
                tag = tag.split(':' ,1)[0]
                if (not tag in self.test_format._supported_tags
                    and not '%s:' % tag in self.test_format._supported_tags
                    and tag not in failures):
                    failures.append(tag)
            elif (not tag in self.test_format._supported_tags
                    and not tag.startswith('user')
                    and not tag.startswith('~')
                    and tag not in failures):
                failures.append(tag)
        if failures:
            failure_desc = ('\n\nThe following test tags are not supported by %s: %s' %
                (self.test_format.__class__.__name__, ', '.join(sorted(failures))))
            self.fail(failure_desc)

    @unittest.skipIf(not DEBUG, "Only check test data covers all supported tags when DEBUG == True")
    def test_tags_comprehensive(self):
        self.test_format = picard.formats.open(self.filename)
        if not hasattr(self.test_format, '_supported_tags'):
            if DEBUG:
                self.fail('\n\nFile format does not list supported tags.')
            else:
                self.skipTest('File format does not list supported tags.')

        failures = []
        for tag_name in self.test_format._supported_tags:
            tag_colon = tag_name
            if (tag_name not in self.test_tags
                    and tag_name not in PRESERVED_TAGS):
                if not tag_name.endswith(':'):
                    tag_colon += ':'
                for tag in self.test_tags:
                    if tag.startswith(tag_colon):
                        break
                else:
                    failures.append(tag_name)
        if failures:
            failure_desc = '\n\nNOTE: THIS TEST IS FAILING DUE TO MISSING TEST DATA.'
            failure_desc += '\nSet DEBUG to False at the beginning of test_formats.py to stop this happening.'
            failure_desc += ('\n\nThe following tags supported by %s are not in the test data: %s' %
                (self.test_format.__class__.__name__, ', '.join(sorted(failures))))
            self.fail(failure_desc)

    def test_save_and_load_tags(self):
        metadata = Metadata()
        for (key, value) in self.test_tags.iteritems():
            metadata[key] = value
        loaded_metadata = save_and_load_metadata(self.filename, metadata)
        failure_desc = ""
        failures = []
        for (key, value) in self.test_tags.iteritems():
            result = loaded_metadata.getall(key)
            if (self.__class__.__name__.startswith('Format_ID3_')
                and len(result) == 1 and config.setting['write_id3v23']):
                result = result[0].split(config.setting['id3v23_join_with'])
            if len(result) == 1:
                result = result[0]
            elif not result:
                result = u''
            if value != result:
                failures.append('{!s:<35} {!r:<30} !=  {!r}'.format(key, value, result))
        if failures:
            failure_desc += '\n\nThe following metadata was not saved and re-loaded correctly:\n  ' + '\n  '.join(sorted(failures))
        failures = []
        for (key, value) in loaded_metadata.rawitems():
            if key not in self.test_tags and key not in PRESERVED_TAGS:
                failures.append('{!s:<35} {!r}'.format(key, value))
        if self.log_messages:
            error_types = log.LOG_ERROR | ((log.LOG_WARNING | log.LOG_INFO) if DEBUG else 0)
            messages = any(map(lambda x: x[0] & error_types, self.log_messages))
            errors = any(map(lambda x: x[0] & log.LOG_ERROR, self.log_messages))
        else:
            messages = errors = []
        if not DEBUG and not (errors or failure_desc):
            return
        if DEBUG and (messages or failures) and not (errors or failure_desc):
            failure_desc += '\n\nNOTE: THIS TEST IS ONLY FAILING DUE TO SHOWING LOG MESSAGES WHICH ARE NOT ERRORS.'
            failure_desc += '\nSet DEBUG to False at the beginning of test_formats.py to stop this happening.'
        if failures:
            failure_desc += '\n\nThe following additional metadata was loaded:\n  ' + '\n  '.join(sorted(failures))
        if messages:
            failure_desc += '\n\nThe following log messages were issued:\n  ' + '\n  '.join([m for (t, m) in self.log_messages])
        if failure_desc:
            self.test_format = picard.formats.open(self.filename)
            self.fail(failure_desc)

    def test_ratings(self):
        if not self.supports_ratings:
            self.skipTest('File type does not support ratings')
        for rating in range(6):
            rating = 1
            metadata = Metadata()
            metadata['~rating'] = rating
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(int(loaded_metadata['~rating']), rating, '~rating: %r != %r' % (loaded_metadata['~rating'], rating))


class Format_APEv2_MonkeysAudioTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.ape')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']


class Format_APEv2_MusepackSV7Test(FormatsTest):
    test_file = os.path.join('test', 'data', 'test-sv7.mpc')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']


class Format_APEv2_MusepackSV8Test(FormatsTest):
    test_file = os.path.join('test', 'data', 'test-sv8.mpc')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']


class Format_APEv2_WavPackTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.wv')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']


class Format_APEv2_OptimFROGTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.ofr')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']


class Format_APEv2_TomsAudioTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.tak')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']


class Format_ASF_ASFTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.asf')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    test_tags['~stereo'] = '0'
    test_tags['~video'] = '1'
    test_tags['~asf:FOO/Bar'] = 'Foo Bar'


class Format_ASF_WMATest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.wma')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    test_tags['~stereo'] = '0'
    test_tags['~video'] = '1'
    test_tags['~asf:FOO/Bar'] = 'Foo Bar'


if picard.formats.AiffFile:
    class Format_ID3_AIFFTest_id3v23(FormatsTest):
        write_id3v23 = True
        test_file = os.path.join('test', 'data', 'test.aiff')
        supports_ratings = False
        test_tags = TAG_DATA.copy()
        test_tags['userweb'] = 'http://foobar.com'


    class Format_ID3_AIFFTest_id3v24(FormatsTest):
        write_id3v23 = False
        test_file = os.path.join('test', 'data', 'test.aiff')
        supports_ratings = False
        test_tags = TAG_DATA.copy()
        test_tags['userweb'] = 'http://foobar.com'


class Format_ID3_MP3Test_id3v23(FormatsTest):
    write_id3v23 = True
    test_file = os.path.join('test', 'data', 'test.mp3')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    test_tags['userweb'] = 'http://foobar.com'


class Format_ID3_MP3Test_id3v24(FormatsTest):
    write_id3v23 = False
    test_file = os.path.join('test', 'data', 'test.mp3')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    test_tags['userweb'] = 'http://foobar.com'


class Format_ID3_TrueAudioTest_id3v23(FormatsTest):
    write_id3v23 = True
    test_file = os.path.join('test', 'data', 'test.tta')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    test_tags['userweb'] = 'http://foobar.com'


class Format_ID3_TrueAudioTest_id3v24(FormatsTest):
    write_id3v23 = False
    test_file = os.path.join('test', 'data', 'test.tta')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    test_tags['userweb'] = 'http://foobar.com'


class Format_MP4_MP4Test_m4a(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.m4a')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~mp4:XXXX'] = 'Foo Bar'


class Format_MP4_MP4Test_mp4(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.mp4')
    supports_ratings = False
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~mp4:XXXX'] = 'Foo Bar'


class Format_Vorbis_FLACTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.flac')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~vorbis:albumgenre'] = 'Foo Bar'
    test_tags['~vorbis:rating:someoneelse'] = 'Bar Foo'
    test_tags['~vorbis:fingerprint'] = 'Bar Foo'


class Format_Vorbis_OggFLACTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test-flac.oga')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~vorbis:albumgenre'] = 'Foo Bar'
    test_tags['~vorbis:rating:someoneelse'] = 'Bar Foo'
    test_tags['~vorbis:fingerprint'] = 'Bar Foo'


class Format_Vorbis_OggVorbisTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.ogg')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~vorbis:albumgenre'] = 'Foo Bar'
    test_tags['~vorbis:rating:someoneelse'] = 'Bar Foo'
    test_tags['~vorbis:fingerprint'] = 'Bar Foo'


class Format_Vorbis_OpusTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test.opus')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~vorbis:albumgenre'] = 'Foo Bar'
    test_tags['~vorbis:rating:someoneelse'] = 'Bar Foo'
    test_tags['~vorbis:fingerprint'] = 'Bar Foo'

@unittest.skip('Current synthetic test.oggtheora results in "OggTheoraHeaderError: no appropriate stream found"')
class Format_Vorbis_OggTheoraTest(FormatsTest):
    test_file = os.path.join('test', 'data', 'test-theora.ogv')
    supports_ratings = True
    test_tags = TAG_DATA.copy()
    del test_tags['~lyrics_sync']
    del test_tags['~lyrics_sync:foo(eng)']
    del test_tags['~lyrics_sync:bar(fra)']
    test_tags['~vorbis:albumgenre'] = 'Foo Bar'
    test_tags['~vorbis:rating:someoneelse'] = 'Bar Foo'
    test_tags['~vorbis:fingerprint'] = 'Bar Foo'


class BackwardsCompatibility(unittest.TestCase):

    def _log_receiver(self, level, time, msg):
        if level in log._log_prefixes:
            msg = "%s: %s" % (log._log_prefixes[level], msg.decode('ascii', 'replace'))
        self.log_messages.append((level, msg))

    def setUp(self):
        config.setting = settings.copy()
        QtCore.QObject.tagger = FakeTagger()
        log.main_logger.unregister_receiver(log._stderr_receiver)
        log.main_logger.register_receiver(self._log_receiver)

    def tearDown(self):
        log.main_logger.unregister_receiver(self._log_receiver)

    def test_backwards_compatibility(self):
        # Load each file in the versions directory and check that all tags are in TAG_NAMES
        failures = []
        error_types = log.LOG_ERROR | log.LOG_WARNING | log.LOG_INFO
        for path, dirs, names in os.walk(os.path.join('test', 'data', 'versions')):
                for name in names:
                    self.log_messages = []
                    extra_tags = []
                    filename = os.path.join(path, name)
                    f = picard.formats.open(filename)
                    metadata = f._load(filename)
                    for tag in metadata:
                        tag = tag.split(':', 1)[0] if ':' in tag else tag
                        if tag not in TAG_NAMES and tag + ':' not in TAG_NAMES:
                            extra_tags.append(tag)
                    messages = any(map(lambda x: x[0] & error_types, self.log_messages))
                    errors = any(map(lambda x: x[0] & log.LOG_ERROR, self.log_messages))
                    if extra_tags or errors:
                        failures.append('{!s:<30} {!s}'.format(name, ', '.join(extra_tags)))
                        if self.log_messages:
                            failures.append('  ' + '\n  '.join([m for (t, m) in self.log_messages]))

        if failures:
            self.fail('\n\nThe following non-standard tags are loaded:\n' + '\n'.join(failures))
