# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
# Copyright (C) 2024 Suryansh Shakya
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import unittest

import mutagen

from picard.formats import ext_to_format
from picard.metadata import Metadata

from .common import (
    CommonTests,
    load_metadata,
    load_raw,
    save_and_load_metadata,
    save_metadata,
    save_raw,
    skipUnlessTestfile,
)
from .coverart import CommonCoverArtTests


# prevent unittest to run tests in those classes
class CommonMP4Tests:

    class MP4TestCase(CommonTests.TagFormatsTestCase):
        def test_supports_tag(self):
            fmt = ext_to_format(self.testfile_ext)
            self.assertTrue(fmt.supports_tag('copyright'))
            self.assertTrue(fmt.supports_tag('compilation'))
            self.assertTrue(fmt.supports_tag('bpm'))
            self.assertTrue(fmt.supports_tag('djmixer'))
            self.assertTrue(fmt.supports_tag('discnumber'))
            self.assertTrue(fmt.supports_tag('lyrics:lead'))
            self.assertTrue(fmt.supports_tag('Custom'))
            self.assertTrue(fmt.supports_tag('äöüéß\0'))  # Latin 1 is supported
            self.assertFalse(fmt.supports_tag('Б'))  # Unsupported custom tags
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
        def test_ci_tags_preserve_case(self):
            # Ensure values are not duplicated on repeated save and are saved
            # case preserving.
            for name in ('Replaygain_Album_Peak', 'Custom', 'äöüéß\0'):
                tags = mutagen.mp4.MP4Tags()
                tags['----:com.apple.iTunes:' + name] = [b'foo']
                save_raw(self.filename, tags)
                loaded_metadata = load_metadata(self.filename)
                loaded_metadata[name.lower()] = 'bar'
                save_metadata(self.filename, loaded_metadata)
                raw_metadata = load_raw(self.filename)
                self.assertIn('----:com.apple.iTunes:' + name, raw_metadata)
                self.assertEqual(
                    raw_metadata['----:com.apple.iTunes:' + name][0].decode('utf-8'),
                    loaded_metadata[name.lower()])
                self.assertEqual(1, len(raw_metadata['----:com.apple.iTunes:' + name]))
                self.assertNotIn('----:com.apple.iTunes:' + name.upper(), raw_metadata)

        @skipUnlessTestfile
        def test_delete_freeform_tags(self):
            metadata = Metadata()
            metadata['foo'] = 'bar'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual('bar', original_metadata['foo'])
            del metadata['foo']
            new_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertNotIn('foo', new_metadata)

        @skipUnlessTestfile
        def test_invalid_track_and_discnumber(self):
            metadata = Metadata({
                'discnumber': 'notanumber',
                'tracknumber': 'notanumber',
            })
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertNotIn('discnumber', loaded_metadata)
            self.assertNotIn('tracknumber', loaded_metadata)

        @skipUnlessTestfile
        def test_invalid_total_tracks_and_discs(self):
            metadata = Metadata({
                'discnumber': '1',
                'totaldiscs': 'notanumber',
                'tracknumber': '2',
                'totaltracks': 'notanumber',
            })
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(metadata['discnumber'], loaded_metadata['discnumber'])
            self.assertEqual('0', loaded_metadata['totaldiscs'])
            self.assertEqual(metadata['tracknumber'], loaded_metadata['tracknumber'])
            self.assertEqual('0', loaded_metadata['totaltracks'])

        @skipUnlessTestfile
        def test_invalid_int_tag(self):
            for tag in ('bpm', 'movementnumber', 'movementtotal', 'showmovement'):
                metadata = Metadata({tag: 'notanumber'})
                loaded_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertNotIn(tag, loaded_metadata)


class M4ATest(CommonMP4Tests.MP4TestCase):
    testfile = 'test.m4a'
    supports_ratings = False
    expected_info = {
        'length': 106,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '14.376',
        '~bits_per_sample': '16',
        '~filesize': '2559',
    }
    unexpected_info = ['~video']

    @unittest.skipUnless(mutagen.version >= (1, 43, 0), "mutagen >= 1.43.0 required")
    def test_hdvd_tag_considered_video(self):
        tags = mutagen.mp4.MP4Tags()
        tags['hdvd'] = [1]
        save_raw(self.filename, tags)
        metadata = load_metadata(self.filename)
        self.assertEqual('1', metadata["~video"])


class M4VTest(CommonMP4Tests.MP4TestCase):
    testfile = 'test.m4v'
    supports_ratings = False
    expected_info = {
        'length': 106,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '108.043',
        '~bits_per_sample': '16',
        '~video': '1',
        '~filesize': '4065',
    }


class Mp4CoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.m4a'
