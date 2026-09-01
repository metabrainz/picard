# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


import gzip
import json
from unittest.mock import (
    Mock,
)

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard.album import (
    Album,
    AlbumStatus,
)
from picard.file import File
from picard.track import Track


class TrackTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.album = Album('123')

    def test_column(self):
        self.album.metadata['test'] = 'foo'
        self.assertEqual(self.album.column('test'), 'foo')
        self.assertEqual(self.album.column('unknown'), '')

    def test_column_title(self):
        self.assertEqual(self.album.column('title'), '')
        self.album.metadata['album'] = 'Foo'
        self.assertEqual(self.album.column('title'), 'Foo')
        self.album.status = AlbumStatus.LOADING
        self.assertEqual(self.album.column('title'), "[loading album information]")
        self.album.status = AlbumStatus.ERROR
        self.assertEqual(self.album.column('title'), f"[could not load album {self.album.id}]")

    def test_column_title_with_tracks(self):
        self.album.metadata['album'] = 'Foo'
        self.assertEqual(self.album.column('title'), 'Foo')
        track1 = Track('t1')
        self.album.tracks.append(track1)
        self.assertEqual(self.album.column('title'), 'Foo‎ (0/1; 0 images)')
        track2 = Track('t2')
        self.album.tracks.append(track2)
        self.assertEqual(self.album.column('title'), 'Foo‎ (0/2; 0 images)')
        track2.metadata.images.append(Mock())
        self.album.update_metadata_images_from_children()
        self.assertEqual(self.album.column('title'), 'Foo‎ (0/2; 1 image)')
        file1 = File('somefile.opus')
        track2.files.append(file1)
        self.assertEqual(self.album.column('title'), 'Foo‎ (1/2; 1*; 1 image)')
        file1.state = File.State.NORMAL
        self.assertEqual(self.album.column('title'), 'Foo‎ (1/2; 1 image)')

    def test_column_length(self):
        self.assertEqual(self.album.column('~length'), '')
        self.album.metadata.length = 6000
        self.assertEqual(self.album.column('~length'), '0:06')

    def test_column_artist(self):
        self.album.metadata['artist'] = 'The Artist'
        self.album.metadata['albumartist'] = 'The Album Artist'
        self.assertEqual(self.album.column('artist'), 'The Album Artist')
        self.assertEqual(self.album.column('artist'), self.album.column('albumartist'))

    def test_column_tracknumber(self):
        self.album.metadata['tracknumber'] = '3'
        self.album.metadata['~totalalbumtracks'] = '42'
        self.assertEqual(self.album.column('tracknumber'), '42')
        self.assertEqual(self.album.column('tracknumber'), self.album.column('~totalalbumtracks'))

    def test_column_discnumber(self):
        self.album.metadata['discnumber'] = '3'
        self.album.metadata['totaldiscs'] = '42'
        self.assertEqual(self.album.column('discnumber'), '42')
        self.assertEqual(self.album.column('discnumber'), self.album.column('totaldiscs'))

    def test_column_coverart(self):
        image = Mock()
        image.dimensions_as_string.return_value = '100x100'
        self.album.metadata.images.append(image)
        self.assertEqual(self.album.column('covercount'), '1')
        self.assertEqual(self.album.column('coverdimensions'), '100x100')

    def test_release_node_cache_roundtrip(self):
        # The property stores the node compressed but returns an equal dict.
        node = {
            'id': 'abc',
            'media': [{'tracks': [{'title': f'T{i}'} for i in range(12)]}],
            'artist-credit': [{'name': 'X', 'joinphrase': ''}],
        }
        self.album._release_node_cache = node
        self.assertEqual(self.album._release_node_cache, node)

    def test_release_node_cache_none(self):
        self.album._release_node_cache = None
        self.assertIsNone(self.album._release_node_cache)
        self.assertIsNone(self.album._release_node_cache_blob)

    def test_release_node_cache_is_compressed(self):
        # Stored blob must be smaller than the raw JSON for repetitive data.
        node = {'media': [{'tracks': [{'title': 'Song', 'length': 210000} for _ in range(30)]}]}
        self.album._release_node_cache = node
        blob = self.album._release_node_cache_blob
        self.assertIsInstance(blob, bytes)
        raw = json.dumps(node).encode('utf-8')
        self.assertLess(len(blob), len(raw))
        # And it round-trips.
        self.assertEqual(json.loads(gzip.decompress(blob).decode('utf-8')), node)

    def test_release_node_cache_roundtrip_real_release(self):
        # Round-trip must be exact for a real MB release node (nested
        # structure, Unicode, artist-credits, relations, etc.) and the stored
        # blob must be much smaller than the live JSON.
        node = load_test_json('release.json')
        self.album._release_node_cache = node
        self.assertEqual(self.album._release_node_cache, node)
        raw = json.dumps(node).encode('utf-8')
        self.assertLess(len(self.album._release_node_cache_blob), len(raw))
