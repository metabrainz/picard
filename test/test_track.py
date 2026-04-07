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

from test.picardtestcase import PicardTestCase

from picard.track import Track


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
