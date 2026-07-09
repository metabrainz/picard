# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021-2022 Philipp Wolfer
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


from collections import Counter
from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.album import NatAlbum
from picard.tagger import Tagger
from picard.track import (
    NonAlbumTrack,
    Track,
)


class TrackTest(PicardTestCase):
    def test_can_link_fingerprint(self):
        track = Track('123')
        self.assertTrue(track.can_link_fingerprint)


class TrackGenres2MetadataTest(PicardTestCase):
    def test_empty(self):
        genres = Counter()
        ret = Track._genres_to_metadata(genres)
        self.assertEqual(ret, [])

    def test_basic(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres)
        self.assertEqual(ret, ['Blues', 'Pop', 'Rock'])

    def test_negative_zero(self):
        genres = Counter(pop=-6, rock=0, blues=-2)
        ret = Track._genres_to_metadata(genres)
        self.assertEqual(ret, [])
        genres = Counter(pop=-6, rock=1, blues=-2)
        ret = Track._genres_to_metadata(genres)
        self.assertEqual(ret, ['Rock'])

    def test_limit(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres, limit=2)
        self.assertEqual(ret, ['Pop', 'Rock'])

    def test_limit_0(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres, limit=0)
        self.assertEqual(ret, [])

    def test_limit_after_filter(self):
        genres = Counter(rock=5, blues=7, pop=1, psychedelic=3)
        filters = '-rock'
        ret = Track._genres_to_metadata(genres, limit=3, filters=filters)
        self.assertEqual(ret, ['Blues', 'Pop', 'Psychedelic'])

    def test_minusage(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres, minusage=10)
        self.assertEqual(ret, ['Blues', 'Pop', 'Rock'])
        ret = Track._genres_to_metadata(genres, minusage=50)
        self.assertEqual(ret, ['Pop', 'Rock'])
        ret = Track._genres_to_metadata(genres, minusage=90)
        self.assertEqual(ret, ['Rock'])

    def test_filters(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres, filters="-blues")
        self.assertEqual(ret, ['Pop', 'Rock'])

    def test_join_with(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres, join_with=",")
        self.assertEqual(ret, ['Blues,Pop,Rock'])

    def test_limit_with_tied_counts(self):
        """Genres with equal counts must be selected deterministically.

        Counter.most_common() returns tied items in insertion order, which
        can vary depending on the order the API response is parsed.  The
        result must be the same regardless of insertion order.
        See https://community.metabrainz.org/t/genre-keeps-changing/814606
        """
        # Simulate two different insertion orders from the API
        genres_order1 = Counter()
        genres_order1['modern classical'] = 1
        genres_order1['electronic'] = 1
        genres_order1['pop'] = 1

        genres_order2 = Counter()
        genres_order2['electronic'] = 1
        genres_order2['pop'] = 1
        genres_order2['modern classical'] = 1

        ret1 = Track._genres_to_metadata(genres_order1, limit=1)
        ret2 = Track._genres_to_metadata(genres_order2, limit=1)
        self.assertEqual(ret1, ret2)


class TestRemoveNat(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'nat_name': 'Standalone Recordings'})
        self.nats = NatAlbum()
        self.tagger.nats = self.nats
        self.tagger.albums = {'NATS': self.nats}
        self.tagger.album_removed = MagicMock()
        self.tagger.remove_files = MagicMock()
        self.tagger.remove_album = MagicMock()

    def _make_nat(self, nat_id):
        nat = NonAlbumTrack(nat_id)
        self.nats.tracks.append(nat)
        return nat

    def test_remove_nat_track_not_in_list(self):
        """Removing a NAT track not in self.nats.tracks should not raise ValueError."""
        nat = NonAlbumTrack('fake-recording-id')
        # Track is NOT in self.nats.tracks — this must not crash
        Tagger.remove_nat(self.tagger, nat)

    def test_remove_nat_last_track_removes_album(self):
        """Removing the last NAT track should remove the NAT album."""
        nat = self._make_nat('recording-1')
        Tagger.remove_nat(self.tagger, nat)
        self.tagger.remove_album.assert_called_once_with(self.nats)

    def test_remove_nat_not_last_track_updates(self):
        """Removing a NAT track when others remain should update the album."""
        nat1 = self._make_nat('recording-1')
        self._make_nat('recording-2')
        Tagger.remove_nat(self.tagger, nat1)
        self.assertNotIn(nat1, self.nats.tracks)
