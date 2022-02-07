# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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
