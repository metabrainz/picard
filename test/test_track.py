# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2022 Laurent Monin
# Copyright (C) 2021-2022, 2024-2025 Philipp Wolfer
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

from picard.album import (
    Album,
    AlbumArtist,
)
from picard.const import VARIOUS_ARTISTS_ID
from picard.releasegroup import ReleaseGroup
from picard.track import (
    Track,
    TrackArtist,
)


class TrackTest(PicardTestCase):
    def test_can_link_fingerprint(self):
        track = Track('123')
        self.assertTrue(track.can_link_fingerprint)

    def test_merge_folksonomy_tags_no_album(self):
        track = Track('123')
        track._genres = Counter(pop=6, rock=7, blues=2)
        self.assertEqual(track._merge_folksonomy_tags('genres'), track._genres)

    def test_merge_folksonomy_tags_with_album(self):
        track = Track('123')
        track._genres = Counter(pop=6, rock=7)
        album = Album('456')
        album._genres = Counter(rock=3, blues=2)
        release_group = ReleaseGroup('789')
        release_group._genres = Counter(blues=1)
        album.release_group = release_group
        track.album = album
        expected = Counter(pop=6, rock=10, blues=3)
        self.assertEqual(track._merge_folksonomy_tags('genres'), expected)

    def test_merge_folksonomy_tags_artist_genre_fallback(self):
        self.set_config_values({'artists_genres': True})
        track = Track('123')
        album = Album('456')
        artist1 = AlbumArtist('1')
        artist1._genres = Counter(rock=1, blues=2)
        album._album_artists.append(artist1)
        artist2 = AlbumArtist('2')
        artist2._genres = Counter(pop=2, rock=1)
        album._album_artists.append(artist2)
        track.album = album
        expected = artist1._genres + artist2._genres
        self.assertEqual(track._merge_folksonomy_tags('genres'), expected)

    def test_merge_folksonomy_tags_various_artist_genre_fallback(self):
        self.set_config_values({'artists_genres': True})
        track = Track('123')
        track.metadata['musicbrainz_albumartistid'] = VARIOUS_ARTISTS_ID
        album = Album('456')
        album_artist = AlbumArtist('1')
        album_artist._genres = Counter(country=1)
        album._album_artists.append(album_artist)
        track.album = album
        track_artist1 = TrackArtist('2')
        track_artist1._genres = Counter(rock=1, blues=2)
        track._track_artists.append(track_artist1)
        track_artist2 = TrackArtist('3')
        track_artist2._genres = Counter(pop=2, rock=1)
        track._track_artists.append(track_artist2)
        expected = track_artist1._genres + track_artist2._genres
        self.assertEqual(track._merge_folksonomy_tags('genres'), expected)

    def test_add_genres_variable(self):
        track = Track('123')
        track._genres = Counter(pop=6, rock=7, blues=2)
        track._add_genres_variable()
        self.assertEqual(track.metadata.getall('~genres'), ['blues', 'pop', 'rock'])

    def test_add_folksonomy_tags_variable(self):
        track = Track('123')
        track._genres = Counter(pop=6, rock=7, blues=2)
        track._folksonomy_tags = Counter(live=2, pop=6, rock=7, blues=2, favorite=1)
        track._add_folksonomy_tags_variable()
        self.assertEqual(track.metadata.getall('~folksonomy_tags'), ['favorite', 'live'])


class TrackGenresToMetadataTest(PicardTestCase):
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
        ret = Track._genres_to_metadata(genres, filters='-blues')
        self.assertEqual(ret, ['Pop', 'Rock'])

    def test_join_with(self):
        genres = Counter(pop=6, rock=7, blues=2)
        ret = Track._genres_to_metadata(genres, join_with=',')
        self.assertEqual(ret, ['Blues,Pop,Rock'])
