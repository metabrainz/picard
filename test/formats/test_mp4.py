import mutagen

from picard.formats import ext_to_format

from .common import (
    CommonTests,
    load_metadata,
    load_raw,
    save_metadata,
    save_raw,
    skipUnlessTestfile,
)
from .coverart import CommonCoverArtTests


class MP4Test(CommonTests.TagFormatsTestCase):
    testfile = 'test.m4a'
    supports_ratings = False
    expected_info = {
        'length': 106,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '14.376',
        '~bits_per_sample': '16',
    }

    def test_supports_tag(self):
        fmt = ext_to_format(self.testfile_ext[1:])
        self.assertTrue(fmt.supports_tag('copyright'))
        self.assertTrue(fmt.supports_tag('compilation'))
        self.assertTrue(fmt.supports_tag('bpm'))
        self.assertTrue(fmt.supports_tag('djmixer'))
        self.assertTrue(fmt.supports_tag('discnumber'))
        self.assertTrue(fmt.supports_tag('lyrics:lead'))
        self.assertTrue(fmt.supports_tag('~length'))
        for tag in self.replaygain_tags.keys():
            self.assertTrue(fmt.supports_tag(tag))

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertIn('AAC LC', metadata['~format'])

    @skipUnlessTestfile
    def test_replaygain_tags_case_insensitive(self):
        tags = mutagen.mp4.MP4Tags()
        tags['----:com.apple.iTunes:replaygain_album_gain'] = [b'-6.48 dB']
        tags['----:com.apple.iTunes:Replaygain_Album_Peak'] = [b'0.978475']
        tags['----:com.apple.iTunes:replaygain_album_range'] = [b'7.84 dB']
        tags['----:com.apple.iTunes:replaygain_track_gain'] = [b'-6.16 dB']
        tags['----:com.apple.iTunes:REPLAYGAIN_track_peak'] = [b'0.976991']
        tags['----:com.apple.iTunes:REPLAYGAIN_TRACK_RANGE'] = [b'8.22 dB']
        tags['----:com.apple.iTunes:replaygain_reference_loudness'] = [b'-18.00 LUFS']
        save_raw(self.filename, tags)
        loaded_metadata = load_metadata(self.filename)
        for (key, value) in self.replaygain_tags.items():
            self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

    @skipUnlessTestfile
    def test_replaygain_tags_not_duplicated(self):
        # Ensure values are not duplicated on repeated save
        tags = mutagen.mp4.MP4Tags()
        tags['----:com.apple.iTunes:Replaygain_Album_Peak'] = [b'-6.48 dB']
        save_raw(self.filename, tags)
        loaded_metadata = load_metadata(self.filename)
        save_metadata(self.filename, loaded_metadata)
        raw_metadata = load_raw(self.filename)
        self.assertFalse('----:com.apple.iTunes:Replaygain_Album_Peak' in raw_metadata)
        self.assertTrue('----:com.apple.iTunes:REPLAYGAIN_ALBUM_PEAK' in raw_metadata)


class Mp4CoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.m4a'
