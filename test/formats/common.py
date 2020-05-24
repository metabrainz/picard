# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Zenara Daley
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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


import os.path
import unittest

import mutagen

from test.picardtestcase import PicardTestCase

from picard import config
import picard.formats
from picard.formats import ext_to_format
from picard.formats.mutagenext.aac import AACAPEv2
from picard.formats.mutagenext.ac3 import AC3APEv2
from picard.formats.mutagenext.tak import TAK
from picard.formats.util import guess_format
from picard.metadata import Metadata


settings = {
    'clear_existing_tags': False,
    'embed_only_one_front_image': False,
    'enabled_plugins': '',
    'id3v23_join_with': '/',
    'id3v2_encoding': 'utf-8',
    'rating_steps': 6,
    'rating_user_email': 'users@musicbrainz.org',
    'remove_ape_from_mp3': False,
    'remove_id3_from_flac': False,
    'remove_images_from_tags': False,
    'save_images_to_tags': True,
    'write_id3v1': True,
    'write_id3v23': False,
    'itunes_compatible_grouping': False,
    'aac_save_ape': True,
    'ac3_save_ape': True,
    'write_wave_riff_info': True,
    'remove_wave_riff_info': False,
    'wave_riff_info_encoding': 'iso-8859-1',
}


def save_metadata(filename, metadata):
    f = picard.formats.open_(filename)
    loaded_metadata = f._load(filename)
    f._copy_loaded_metadata(loaded_metadata)
    f._save(filename, metadata)


def load_metadata(filename):
    f = picard.formats.open_(filename)
    return f._load(filename)


def save_and_load_metadata(filename, metadata):
    """Save new metadata to a file and load it again."""
    save_metadata(filename, metadata)
    return load_metadata(filename)


def load_raw(filename):
    # First try special implementations in Picard
    f = mutagen.File(filename, [AACAPEv2, AC3APEv2, TAK])
    if f is None:
        f = mutagen.File(filename)
    return f


def save_raw(filename, tags):
    f = load_raw(filename)
    for k, v in tags.items():
        f[k] = v
    f.save()


TAGS = {
    'albumartist': 'Foo',
    'albumartistsort': 'Foo',
    'album': 'Foo Bar',
    'albumsort': 'Foo',
    'arranger': 'Foo',
    'artist': 'Foo',
    'artistsort': 'Foo',
    'asin': 'Foo',
    'barcode': 'Foo',
    'bpm': '80',
    'catalognumber': 'Foo',
    'comment': 'Foo',
    'comment:foo': 'Foo',
    'comment:deu:foo': 'Foo',
    'compilation': '1',
    'composer': 'Foo',
    'composersort': 'Foo',
    'conductor': 'Foo',
    'copyright': 'Foo',
    'date': '2004',
    'discnumber': '1',
    'discsubtitle': 'Foo',
    'djmixer': 'Foo',
    'encodedby': 'Foo',
    'encodersettings': 'Foo',
    'engineer': 'Foo',
    'gapless': '1',
    'genre': 'Foo',
    'grouping': 'Foo',
    'isrc': 'Foo',
    'key': 'E#m',
    'label': 'Foo',
    'lyricist': 'Foo',
    'lyrics': 'Foo',
    'media': 'Foo',
    'mixer': 'Foo',
    'mood': 'Foo',
    'movement': 'Foo',
    'movementnumber': '2',
    'movementtotal': '8',
    'musicbrainz_albumartistid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_albumid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_artistid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_discid': 'HJRFvVfxx0MU_6v8v9swQUxDmZQ-',
    'musicbrainz_originalalbumid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_originalartistid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_releasegroupid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_trackid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_trmid': 'Foo',
    'musicbrainz_workid': '00000000-0000-0000-0000-000000000000',
    'musicip_fingerprint': 'Foo',
    'musicip_puid': '00000000-0000-0000-0000-000000000000',
    'originaldate': '1980-01-20',
    'originalyear': '1980',
    'originalfilename': 'Foo',
    'performer': 'Foo',
    'performer:guest vocal': 'Foo',
    'podcast': '1',
    'podcasturl': 'Foo',
    'producer': 'Foo',
    'releasecountry': 'XW',
    'releasestatus': 'Foo',
    'releasetype': 'Foo',
    'remixer': 'Foo',
    'show': 'Foo',
    'showmovement': '1',
    'showsort': 'Foo',
    'subtitle': 'Foo',
    'title': 'Foo',
    'titlesort': 'Foo',
    'totaldiscs': '2',
    'totaltracks': '10',
    'tracknumber': '2',
    'website': 'http://example.com',
    'work': 'Foo'
}

REPLAYGAIN_TAGS = {
    'replaygain_album_gain': '-6.48 dB',
    'replaygain_album_peak': '0.978475',
    'replaygain_album_range': '7.84 dB',
    'replaygain_track_gain': '-6.16 dB',
    'replaygain_track_peak': '0.976991',
    'replaygain_track_range': '8.22 dB',
    'replaygain_reference_loudness': '-18.00 LUFS',
}


def skipUnlessTestfile(func):
    def _decorator(self, *args, **kwargs):
        if not self.testfile:
            raise unittest.SkipTest("No test file set")
        func(self, *args, **kwargs)
    return _decorator


# prevent unittest to run tests in those classes
class CommonTests:

    class BaseFileTestCase(PicardTestCase):
        testfile = None
        testfile_ext = None
        testfile_path = None

        def setUp(self):
            super().setUp()
            config.setting = settings.copy()
            if self.testfile:
                _name, self.testfile_ext = os.path.splitext(self.testfile)
                self.testfile_path = os.path.join('test', 'data', self.testfile)
                self.testfile_ext = os.path.splitext(self.testfile)[1]
                self.filename = self.copy_of_original_testfile()
                self.format = ext_to_format(self.testfile_ext[1:])

        def copy_of_original_testfile(self):
            return self.copy_file_tmp(self.testfile_path, self.testfile_ext)

    class SimpleFormatsTestCase(BaseFileTestCase):

        expected_info = {}
        unexpected_info = []

        @skipUnlessTestfile
        def test_can_open_and_save(self):
            metadata = save_and_load_metadata(self.filename, Metadata())
            self.assertTrue(metadata['~format'])

        @skipUnlessTestfile
        def test_info(self):
            if not self.expected_info:
                raise unittest.SkipTest("Ratings not supported for %s" % self.format.NAME)
            metadata = save_and_load_metadata(self.filename, Metadata())
            for key, expected_value in self.expected_info.items():
                value = metadata.length if key == 'length' else metadata[key]
                self.assertEqual(expected_value, value, '%s: %r != %r' % (key, expected_value, value))
            for key in self.unexpected_info:
                self.assertNotIn(key, metadata)

        def _test_supported_tags(self, tags):
            metadata = Metadata(tags)
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            for (key, value) in tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        def _test_unsupported_tags(self, tags):
            metadata = Metadata(tags)
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            for tag in tags:
                self.assertFalse(self.format.supports_tag(tag))
                self.assertNotIn(tag, loaded_metadata, '%s: %r != None' % (tag, loaded_metadata[tag]))

    class TagFormatsTestCase(SimpleFormatsTestCase):

        def setUp(self):
            super().setUp()
            self.tags = TAGS.copy()
            self.replaygain_tags = REPLAYGAIN_TAGS.copy()
            self.unsupported_tags = {}
            self.setup_tags()

        def setup_tags(self):
            if self.testfile:
                supports_tag = self.format.supports_tag
                self.unsupported_tags = {tag: val for tag, val in self.tags.items() if not supports_tag(tag)}
                self.remove_tags(self.unsupported_tags.keys())

        def set_tags(self, dict_tag_value=None):
            if dict_tag_value:
                self.tags.update(dict_tag_value)

        def remove_tags(self, tag_list=None):
            for tag in tag_list:
                del self.tags[tag]

        @skipUnlessTestfile
        def test_simple_tags(self):
            self._test_supported_tags(self.tags)

        @skipUnlessTestfile
        def test_replaygain_tags(self):
            self._test_supported_tags(self.replaygain_tags)

        @skipUnlessTestfile
        def test_replaygain_tags_case_insensitive(self):
            tags = {
                'replaygain_album_gain': '-6.48 dB',
                'Replaygain_Album_Peak': '0.978475',
                'replaygain_album_range': '7.84 dB',
                'replaygain_track_gain': '-6.16 dB',
                'replaygain_track_peak': '0.976991',
                'replaygain_track_range': '8.22 dB',
                'replaygain_reference_loudness': '-18.00 LUFS',
            }
            save_raw(self.filename, tags)
            loaded_metadata = load_metadata(self.filename)
            for (key, value) in self.replaygain_tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        @skipUnlessTestfile
        def test_save_does_not_modify_metadata(self):
            tags = dict(self.tags)
            if self.supports_ratings:
                tags['~rating'] = '3'
            metadata = Metadata(tags)
            save_metadata(self.filename, metadata)
            for (key, value) in tags.items():
                self.assertEqual(metadata[key], value, '%s: %r != %r' % (key, metadata[key], value))

        @skipUnlessTestfile
        def test_unsupported_tags(self):
            self._test_unsupported_tags(self.unsupported_tags)

        @skipUnlessTestfile
        def test_preserve_unchanged_tags(self):
            metadata = Metadata(self.tags)
            save_metadata(self.filename, metadata)
            loaded_metadata = save_and_load_metadata(self.filename, Metadata())
            for (key, value) in self.tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        @skipUnlessTestfile
        def test_delete_simple_tags(self):
            metadata = Metadata(self.tags)
            if self.supports_ratings:
                metadata['~rating'] = 1
            original_metadata = save_and_load_metadata(self.filename, metadata)
            del metadata['albumartist']
            del metadata['musicbrainz_artistid']
            if self.supports_ratings:
                del metadata['~rating']
            new_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertIn('albumartist', original_metadata)
            self.assertNotIn('albumartist', new_metadata)
            self.assertIn('musicbrainz_artistid', original_metadata)
            self.assertNotIn('musicbrainz_artistid', new_metadata)
            if self.supports_ratings:
                self.assertIn('~rating', original_metadata)
                self.assertNotIn('~rating', new_metadata)

        @skipUnlessTestfile
        def test_delete_tags_with_empty_description(self):
            for key in ('lyrics', 'lyrics:', 'comment', 'comment:', 'performer', 'performer:'):
                name = key.rstrip(':')
                name_with_description = name + ':foo'
                if not self.format.supports_tag(name):
                    continue
                metadata = Metadata()
                metadata[name] = 'bar'
                metadata[name_with_description] = 'other'
                original_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertIn(name, original_metadata)
                del metadata[key]
                new_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertNotIn(name, new_metadata)
                # Ensure the names with description did not get deleted
                if name_with_description in original_metadata:
                    self.assertIn(name_with_description, new_metadata)

        @skipUnlessTestfile
        def test_delete_tags_with_description(self):
            for key in (
                'comment:foo', 'comment:de:foo', 'performer:foo', 'lyrics:foo',
                'comment:a*', 'comment:a[', 'performer:(x)', 'performer: Ä é '
            ):
                if not self.format.supports_tag(key):
                    continue
                prefix = key.split(':')[0]
                metadata = Metadata()
                metadata[key] = 'bar'
                original_metadata = save_and_load_metadata(self.filename, metadata)
                if key not in original_metadata and prefix in original_metadata:
                    continue  # Skip if the type did not support saving this kind of tag
                self.assertEqual('bar', original_metadata[key], original_metadata)
                metadata[prefix] = '(foo) bar'
                del metadata[key]
                new_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertNotIn(key, new_metadata)
                self.assertEqual('(foo) bar', new_metadata[prefix])

        @skipUnlessTestfile
        def test_delete_nonexistant_tags(self):
            for key in ('title', 'foo', 'comment:foo', 'comment:de:foo',
                        'performer:foo', 'lyrics:foo', 'totaltracks'):
                if not self.format.supports_tag(key):
                    continue
                metadata = Metadata()
                save_metadata(self.filename, metadata)
                del metadata[key]
                new_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertNotIn(key, new_metadata)

        @skipUnlessTestfile
        def test_delete_complex_tags(self):
            metadata = Metadata(self.tags)
            original_metadata = save_and_load_metadata(self.filename, metadata)
            del metadata['totaldiscs']
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('totaldiscs', original_metadata)
            if self.testfile_ext in ('.m4a', '.m4v'):
                self.assertEqual('0', new_metadata['totaldiscs'])
            else:
                self.assertNotIn('totaldiscs', new_metadata)

        @skipUnlessTestfile
        def test_delete_performer(self):
            if not self.format.supports_tag('performer:'):
                raise unittest.SkipTest('Tag "performer:" not supported for %s' % self.format.NAME)
            metadata = Metadata({
                'performer:piano': ['Piano1', 'Piano2'],
                'performer:guitar': ['Guitar1'],
            })
            original_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertIn('Piano1', original_metadata.getall('performer:piano'))
            self.assertIn('Piano2', original_metadata.getall('performer:piano'))
            self.assertEqual(2, len(original_metadata.getall('performer:piano')))
            self.assertEqual('Guitar1', original_metadata['performer:guitar'])

            del metadata['performer:piano']
            new_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertNotIn('performer:piano', new_metadata)
            self.assertEqual('Guitar1', metadata['performer:guitar'])

        @skipUnlessTestfile
        def test_save_performer(self):
            if not self.format.supports_tag('performer:'):
                raise unittest.SkipTest('Tag "performer:" not supported for %s' % self.format.NAME)
            instrument = "accordéon clavier « boutons »"
            artist = "桑山哲也"
            tag = "performer:" + instrument
            metadata = Metadata({tag: artist})
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertIn(tag, loaded_metadata)
            self.assertEqual(artist, loaded_metadata[tag])

        @skipUnlessTestfile
        def test_ratings(self):
            if not self.supports_ratings:
                raise unittest.SkipTest("Ratings not supported")
            for rating in range(6):
                rating = 1
                metadata = Metadata()
                metadata['~rating'] = rating
                loaded_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertEqual(int(loaded_metadata['~rating']), rating, '~rating: %r != %r' % (loaded_metadata['~rating'], rating))

        @skipUnlessTestfile
        def test_invalid_rating_email(self):
            if not self.supports_ratings:
                raise unittest.SkipTest("Ratings not supported")
            metadata = Metadata()
            metadata['~rating'] = 3
            config.setting['rating_user_email'] = '{in\tvälid}'
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(loaded_metadata['~rating'], metadata['~rating'])

        @skipUnlessTestfile
        def test_guess_format(self):
            temp_file = self.copy_of_original_testfile()
            audio = guess_format(temp_file)
            audio_original = picard.formats.open_(self.filename)
            self.assertEqual(type(audio), type(audio_original))

        @skipUnlessTestfile
        def test_split_ext(self):
            f = picard.formats.open_(self.filename)
            self.assertEqual(f._fixed_splitext(f.filename), os.path.splitext(f.filename))
            self.assertEqual(f._fixed_splitext('.test'), os.path.splitext('.test'))
            if f.EXTENSIONS:
                self.assertEqual(f._fixed_splitext(f.EXTENSIONS[0]), ('', f.EXTENSIONS[0]))
                self.assertNotEqual(f._fixed_splitext(f.EXTENSIONS[0]), os.path.splitext(f.EXTENSIONS[0]))

        @skipUnlessTestfile
        def test_clear_existing_tags_off(self):
            config.setting['clear_existing_tags'] = False
            existing_metadata = Metadata({'artist': 'The Artist'})
            save_metadata(self.filename, existing_metadata)
            new_metadata = Metadata({'title': 'The Title'})
            loaded_metadata = save_and_load_metadata(self.filename, new_metadata)
            self.assertEqual(existing_metadata['artist'], loaded_metadata['artist'])
            self.assertEqual(new_metadata['title'], loaded_metadata['title'])

        @skipUnlessTestfile
        def test_clear_existing_tags_on(self):
            config.setting['clear_existing_tags'] = True
            existing_metadata = Metadata({'artist': 'The Artist'})
            save_metadata(self.filename, existing_metadata)
            new_metadata = Metadata({'title': 'The Title'})
            loaded_metadata = save_and_load_metadata(self.filename, new_metadata)
            self.assertNotIn('artist', loaded_metadata)
            self.assertEqual(new_metadata['title'], loaded_metadata['title'])

        @skipUnlessTestfile
        def test_lyrics_with_description(self):
            metadata = Metadata({'lyrics:foó': 'bar'})
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(metadata['lyrics:foó'], loaded_metadata['lyrics'])

        @skipUnlessTestfile
        def test_comments_with_description(self):
            if not self.format.supports_tag('comment:foó'):
                return
            metadata = Metadata({'comment:foó': 'bar'})
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(metadata['comment:foó'], loaded_metadata['comment:foó'])

        @skipUnlessTestfile
        def test_invalid_track_and_discnumber(self):
            # This test assumes a non-numeric test number can be written. For
            # formats not supporting this it needs to be overridden.
            metadata = Metadata({
                'discnumber': 'notanumber',
                'tracknumber': 'notanumber',
            })
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(loaded_metadata['discnumber'], metadata['discnumber'])
            self.assertEqual(loaded_metadata['totaldiscs'], metadata['totaldiscs'])
            self.assertEqual(loaded_metadata['tracknumber'], metadata['tracknumber'])
            self.assertEqual(loaded_metadata['totaltracks'], metadata['totaltracks'])

        @skipUnlessTestfile
        def test_save_movementnumber_without_movementtotal(self):
            if not self.format.supports_tag('movementnumber'):
                raise unittest.SkipTest('Tag "movementnumber" not supported for %s' % self.format.NAME)
            metadata = Metadata({'movementnumber': 7})
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(loaded_metadata['movementnumber'], metadata['movementnumber'])
            self.assertNotIn('movementtotal', loaded_metadata)
