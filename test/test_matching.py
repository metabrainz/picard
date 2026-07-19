# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018, 2020 Wieland Hoffmann
# Copyright (C) 2018-2021, 2023 Philipp Wolfer
# Copyright (C) 2018-2024 Laurent Monin
# Copyright (C) 2020 dukeyin
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


from collections import namedtuple

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard.acoustid.json_helpers import (
    parse_recording as acoustid_parse_recording,
)
from picard.cluster import CLUSTER_COMPARISON_WEIGHTS
from picard.file import FILE_COMPARISON_WEIGHTS
from picard.matching import (
    _SKIP_RELEASE_WEIGHT,
    ReleaseMatchParts,
    _catno_label_score,
    _compare_to_release_parts,
    _date_score,
    _get_weighted_release_parts,
    _isrcs_score,
    _trackcount_score,
    _weights_from_preferred_countries,
    _weights_from_preferred_formats,
    _weights_from_preferred_release_types,
    compare_to_release,
    compare_to_track,
    find_best_match,
    find_best_match_with_margin,
    length_score,
    sort_by_similarity,
)
from picard.mbjson import (
    release_to_metadata,
    track_to_metadata,
)
from picard.metadata import Metadata
from picard.options import StandardizeArtistNames
from picard.track import Track


settings = {
    'write_id3v23': False,
    'id3v23_join_with': '/',
    'preferred_release_countries': [],
    'preferred_release_formats': [],
    'preferred_release_types': ['Album', 'Other'],
    'discouraged_release_types': [],
    "standardize_artist_names": StandardizeArtistNames.NONE,
    'standardize_instruments': False,
    'standardize_vocals': False,
    'translate_artist_names': False,
    'release_ars': True,
}


class CompareToReleaseTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(settings)

    def test_compare_to_release(self):
        release = load_test_json('release.json')
        metadata = Metadata()
        release_to_metadata(release, metadata)
        match_ = compare_to_release(metadata, release, CLUSTER_COMPARISON_WEIGHTS)
        self.assertEqual(1.0, match_.similarity)
        self.assertEqual(release, match_.release)

    def test_compare_to_release_with_score(self):
        release = load_test_json('release.json')
        metadata = Metadata()
        release_to_metadata(release, metadata)
        for score, sim in ((42, 0.42), ('42', 0.42), ('foo', 1.0), (None, 1.0)):
            release['score'] = score
            match_ = compare_to_release(metadata, release, CLUSTER_COMPARISON_WEIGHTS)
            self.assertEqual(sim, match_.similarity)

    def test_compare_to_release_parts_totaltracks(self):
        release = load_test_json('release_multidisc.json')
        metadata = Metadata()
        weights = {"similarity": {"totaltracks": 30}}
        release_to_metadata(release, metadata)
        # Release has media with track counts [4, 3]
        for totaltracks, sim in ((4, 1.0), (3, 1.0), (2, 1 / 3), (5, 0.25)):
            metadata['totaltracks'] = totaltracks
            parts = _compare_to_release_parts(metadata, release, weights)
            self.assertAlmostEqual(parts.similarity[0][0], sim, places=5)
            self.assertEqual(parts.similarity[0][1], 30)

    def test_compare_to_release_parts_totalalbumtracks(self):
        release = load_test_json('release_multidisc.json')
        metadata = Metadata()
        weights = {"similarity": {"totalalbumtracks": 30}}
        release_to_metadata(release, metadata)
        for totaltracks, sim in ((7, 1.0), (6, 5 / 7), (8, 4 / 7)):
            metadata['~totalalbumtracks'] = totaltracks
            parts = _compare_to_release_parts(metadata, release, weights)
            self.assertAlmostEqual(parts.similarity[0][0], sim, places=5)
            self.assertEqual(parts.similarity[0][1], 30)

    def test_compare_to_release_parts_totalalbumtracks_totaltracks_fallback(self):
        release = load_test_json('release_multidisc.json')
        metadata = Metadata()
        weights = {"similarity": {"totalalbumtracks": 30}}
        release_to_metadata(release, metadata)
        for totaltracks, sim in ((7, 1.0), (6, 5 / 7), (8, 4 / 7)):
            metadata['totaltracks'] = totaltracks
            parts = _compare_to_release_parts(metadata, release, weights)
            self.assertAlmostEqual(parts.similarity[0][0], sim, places=5)
            self.assertEqual(parts.similarity[0][1], 30)

    def test_compare_to_release_parts_barcode_match(self):
        release = load_test_json('release.json')
        metadata = Metadata()
        weights = {"identifiers": {"barcode": 6}}
        metadata['barcode'] = '123'
        parts = _compare_to_release_parts(metadata, release, weights)
        self.assertIn((1.0, 6), parts.identifiers)

    def test_compare_to_release_parts_barcode_mismatch(self):
        release = load_test_json('release.json')
        metadata = Metadata()
        weights = {"identifiers": {"barcode": 6}}
        metadata['barcode'] = '999'
        parts = _compare_to_release_parts(metadata, release, weights)
        self.assertIn((0.0, 6), parts.identifiers)

    def test_compare_to_release_parts_barcode_no_release_barcode(self):
        release = load_test_json('release.json')
        release['barcode'] = ''
        metadata = Metadata()
        weights = {"identifiers": {"barcode": 6}}
        metadata['barcode'] = '123'
        parts = _compare_to_release_parts(metadata, release, weights)
        self.assertIn((0.0, 6), parts.identifiers)

    def test_compare_to_release_parts_barcode_no_file_barcode(self):
        release = load_test_json('release.json')
        metadata = Metadata()
        weights = {"identifiers": {"barcode": 6}}
        parts = _compare_to_release_parts(metadata, release, weights)
        self.assertFalse(parts.identifiers)

    def test_compare_to_release_parts_barcode_upc_ean_normalization(self):
        release = load_test_json('release.json')
        release['barcode'] = '0727361379704'
        metadata = Metadata()
        weights = {"identifiers": {"barcode": 6}}
        metadata['barcode'] = '727361379704'
        parts = _compare_to_release_parts(metadata, release, weights)
        self.assertIn((1.0, 6), parts.identifiers)

    def test_barcode_breaks_tie_between_identical_releases(self):
        release_with_barcode = load_test_json('release.json')
        release_without_barcode = load_test_json('release.json')
        release_without_barcode['barcode'] = ''
        release_without_barcode['id'] = 'different-id'
        metadata = Metadata()
        release_to_metadata(release_with_barcode, metadata)
        match_with = compare_to_release(metadata, release_with_barcode, CLUSTER_COMPARISON_WEIGHTS)
        match_without = compare_to_release(metadata, release_without_barcode, CLUSTER_COMPARISON_WEIGHTS)
        self.assertGreater(match_with.similarity, match_without.similarity)


class CompareToTrackTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(settings)

    def test_compare_to_track(self):
        track_json = load_test_json('track.json')
        track = Track(track_json['id'])
        track_to_metadata(track_json, track)
        match_ = compare_to_track(track.metadata, track_json, FILE_COMPARISON_WEIGHTS)
        self.assertGreaterEqual(match_.similarity, 0.7)
        self.assertEqual(track_json, match_.track)

    def test_compare_to_track_with_score(self):
        track_json = load_test_json('track.json')
        track = Track(track_json['id'])
        track_to_metadata(track_json, track)
        for score in (42, '42', 'foo', None):
            track_json['score'] = score
            match_ = compare_to_track(track.metadata, track_json, FILE_COMPARISON_WEIGHTS)
            # Score 42 → 0.42 multiplier; 'foo'/None → treated as 1.0
            if score in (42, '42'):
                self.assertLess(match_.similarity, 0.5)
            else:
                self.assertGreater(match_.similarity, 0.5)

    def test_compare_to_track_is_video(self):
        recording = load_test_json('recording_video_null.json')
        m = Metadata()
        match_ = compare_to_track(m, recording, {'preferences': {'isvideo': 1}})
        self.assertEqual(1.0, match_.similarity)
        m['~video'] = '1'
        match_ = compare_to_track(m, recording, {'preferences': {'isvideo': 1}})
        self.assertEqual(0.0, match_.similarity)
        recording['video'] = True
        match_ = compare_to_track(m, recording, {'preferences': {'isvideo': 1}})
        self.assertEqual(1.0, match_.similarity)

    def test_compare_to_track_full(self):
        recording = load_test_json('recording_video_null.json')
        m = Metadata(
            {
                'artist': 'Tim Green',
                'release': 'Eastbound Silhouette',
                'date': '2022',
                'title': 'Lune',
                'totaltracks': '6',
                'albumartist': 'Tim Green',
                'tracknumber': '4',
            }
        )
        match_ = compare_to_track(m, recording, FILE_COMPARISON_WEIGHTS)
        self.assertGreaterEqual(match_.similarity, 0.8)
        self.assertEqual(recording, match_.track)
        self.assertEqual(recording['releases'][0], match_.release)

    def test_compare_to_track_without_releases(self):
        self.set_config_values(
            {
                'preferred_release_types': ['Compilation', 'Other'],
                'discouraged_release_types': [],
            }
        )
        track_json = acoustid_parse_recording(load_test_json('acoustid.json'))
        track = Track(track_json['id'])
        track.metadata.update(
            {
                'album': 'x',
                'artist': 'Ed Sheeran',
                'title': 'Nina',
            }
        )
        track.metadata.length = 225000
        m1 = compare_to_track(track.metadata, track_json, FILE_COMPARISON_WEIGHTS)
        del track_json['releases']
        m2 = compare_to_track(track.metadata, track_json, FILE_COMPARISON_WEIGHTS)
        self.assertGreater(
            m1.similarity,
            m2.similarity,
            'Matching score for release with recordings must be higher then for release without',
        )


class ReleaseMatchPartsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    def test_combine_tiers_no_identifiers(self):
        """Without identifiers, similarity drives the score."""
        parts = ReleaseMatchParts(
            similarity=[(1.0, 10), (1.0, 5)],
            preferences=[(1.0, 2)],
        )
        # sim=1.0, pref=1.0 → 1.0*0.9 + 1.0*0.1 = 1.0
        self.assertAlmostEqual(1.0, parts.combine_tiers())

    def test_combine_tiers_strong_identifier_match(self):
        """Strong identifier match → high score, similarity still contributes."""
        parts = ReleaseMatchParts(
            identifiers=[(1.0, 28)],
            similarity=[(0.5, 10)],  # mediocre similarity
            preferences=[(0.0, 2)],  # worst preference
        )
        # id≥0.9 → 0.85 + 0.5*0.1 + 0.0*0.05 = 0.9
        self.assertAlmostEqual(0.9, parts.combine_tiers())

    def test_combine_tiers_strong_identifier_mismatch(self):
        """Strong identifier mismatch → score capped low."""
        parts = ReleaseMatchParts(
            identifiers=[(0.0, 28)],
            similarity=[(1.0, 10), (1.0, 5)],  # perfect similarity
            preferences=[(1.0, 2)],
        )
        # id≤0.1 → min(0.3, 1.0*0.3) = 0.3
        self.assertAlmostEqual(0.3, parts.combine_tiers())

    def test_combine_tiers_partial_identifier(self):
        """Partial identifier signal → blend all tiers."""
        parts = ReleaseMatchParts(
            identifiers=[(0.5, 28)],
            similarity=[(1.0, 10)],
            preferences=[(1.0, 2)],
        )
        # 0.5*0.4 + 1.0*0.5 + 1.0*0.1 = 0.8
        self.assertAlmostEqual(0.8, parts.combine_tiers())

    def test_combine_tiers_identifier_overrides_preference(self):
        """Barcode match wins over format preference mismatch."""
        # Release A: barcode matches, bad preference
        parts_a = ReleaseMatchParts(
            identifiers=[(1.0, 28)],
            similarity=[(0.8, 10)],
            preferences=[(0.0, 2)],
        )
        # Release B: no barcode, good preference
        parts_b = ReleaseMatchParts(
            similarity=[(0.8, 10)],
            preferences=[(1.0, 2)],
        )
        self.assertGreater(parts_a.combine_tiers(), parts_b.combine_tiers())


class ScoreHelpersTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    def test_length_score(self):
        results = (
            (20000, 0, 0.333333333333),
            (20000, 10000, 0.666666666667),
            (20000, 20000, 1.0),
            (20000, 30000, 0.666666666667),
            (20000, 40000, 0.333333333333),
            (20000, 50000, 0.0),
            (20000, None, 0.0),
            (None, 2000, 0.0),
            (None, None, 0.0),
        )
        for a, b, expected in results:
            actual = length_score(a, b)
            self.assertAlmostEqual(
                expected,
                actual,
                msg="a={a}, b={b}".format(a=a, b=b),
            )

    def test_date_score(self):
        self.assertEqual(0.25, _date_score({}, Metadata()))
        self.assertEqual(0.65, _date_score({'date': '2026'}, Metadata()))
        self.assertEqual(1.0, _date_score({'date': '2026-05-21'}, Metadata({'date': '2026-05-21'})))
        self.assertEqual(0.0, _date_score({'date': 'invalid'}, Metadata({'date': '2026-05-21'})))
        self.assertEqual(0.0, _date_score({'date': '2026-05-21'}, Metadata({'date': 'invalid'})))
        self.assertEqual(0.95, _date_score({'date': '2026-05-21'}, Metadata({'date': '2026-08-30'})))
        self.assertEqual(0.85, _date_score({'date': '2026-05-21'}, Metadata({'date': '2024-08-30'})))
        self.assertEqual(0.0, _date_score({'date': '2026-05-21'}, Metadata({'date': '2023-08-30'})))

    def test_catno_label_score(self):
        self.assertEqual(0.5, _catno_label_score('R-123', 'Foo', []))
        self.assertEqual(1.0, _catno_label_score('R-123', 'Foo', [{'catalog-number': 'R-123'}]))
        self.assertEqual(1.0, _catno_label_score('R-123', 'Foo', [{'catalog-number': 'r-123'}]))
        self.assertEqual(
            1.0, _catno_label_score('R-123', 'Foo', [{'catalog-number': '456'}, {'catalog-number': 'R-123'}])
        )
        self.assertEqual(
            1.0, _catno_label_score('R-123', 'Foo', [{'catalog-number': 'R-123', 'label': {'name': 'Foo'}}])
        )
        self.assertEqual(1.0, _catno_label_score('R-123', '', [{'catalog-number': 'R-123', 'label': {'name': 'Foo'}}]))
        self.assertEqual(
            0.8, _catno_label_score('R-123', 'Foo', [{'catalog-number': 'R-123', 'label': {'name': 'Bar'}}])
        )
        self.assertEqual(
            0.0, _catno_label_score('R-456', 'Foo', [{'catalog-number': 'R-123', 'label': {'name': 'Foo'}}])
        )

    def test_trackcount_score(self):
        self.assertEqual(1.0, _trackcount_score(5, 5))
        self.assertAlmostEqual(0.4, _trackcount_score(6, 5))  # 1 - (1/5)*3
        self.assertAlmostEqual(0.6, _trackcount_score(4, 5))  # 1 - (1/5)*2

    def test_isrcs_score(self):
        self.assertEqual(1.0, _isrcs_score(['ISRC1', 'ISRC2'], ['ISRC1', 'ISRC2']))
        self.assertEqual(1.0, _isrcs_score(['ISRC1'], ['ISRC1']))
        self.assertEqual(1.0, _isrcs_score(['ISRC1'], ['ISRC1', 'ISRC2']))
        self.assertEqual(0.8, _isrcs_score(['ISRC1', 'ISRC2'], ['ISRC2', 'ISRC3']))
        self.assertEqual(0.0, _isrcs_score(['ISRC1'], ['ISRC2', 'ISRC3']))
        self.assertEqual(0.5, _isrcs_score(['ISRC1'], []))
        self.assertEqual(0.5, _isrcs_score([], []))
        self.assertEqual(0.5, _isrcs_score([], ['ISRC1', 'ISRC2']))


class PreferredWeightsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    def test_preferred_release_types_preferred(self):
        release = load_test_json('release.json')  # primary-type = Album
        parts = []
        _weights_from_preferred_release_types(parts, release, ['Album'], [], 10)
        score, weight = parts[0]
        self.assertGreater(score, 0.5)
        self.assertEqual(weight, 10)

    def test_preferred_release_types_preferred_order(self):
        release = load_test_json('release.json')  # primary-type = Album
        parts1 = []
        _weights_from_preferred_release_types(parts1, release, ['Album', 'EP'], [], 10)
        parts2 = []
        _weights_from_preferred_release_types(parts2, release, ['EP', 'Album'], [], 10)
        # Album is first in parts1 → higher score
        self.assertGreater(parts1[0][0], parts2[0][0])

    def test_preferred_release_types_discouraged(self):
        release = load_test_json('release.json')  # primary-type = Album
        parts = []
        _weights_from_preferred_release_types(parts, release, [], ['Album'], 10)
        # Discouraged triggers skip
        self.assertEqual(parts[0], _SKIP_RELEASE_WEIGHT)

    def test_preferred_release_types_unlisted(self):
        release = load_test_json('release.json')  # primary-type = Album
        parts = []
        _weights_from_preferred_release_types(parts, release, ['EP'], [], 10)
        # Album is unlisted → neutral 0.5
        self.assertAlmostEqual(parts[0][0], 0.5)

    def test_preferred_release_types_no_type(self):
        release = load_test_json('release_no_type.json')
        parts = []
        _weights_from_preferred_release_types(parts, release, ['Album'], ['Compilation'], 10)
        # No type → neutral 0.5
        self.assertAlmostEqual(parts[0][0], 0.5)
        self.assertEqual(parts[0][1], 10)

    def test_get_weighted_release_parts(self):
        weights = {
            'similarity': {'album': 10, 'totaltracks': 5, 'title': 12},
            'preferences': {'releasecountry': 5, 'isvideo': 2},
        }
        parts = _get_weighted_release_parts(weights, 0.5)
        self.assertIsInstance(parts, ReleaseMatchParts)
        self.assertEqual(parts.identifiers, [])
        self.assertEqual(parts.similarity, [(0.5, 15)])
        self.assertEqual(parts.preferences, [(0.5, 5)])

    def test_preferred_countries(self):
        release = load_test_json('release.json')
        parts = []
        _weights_from_preferred_countries(parts, release, [], 666)
        self.assertFalse(parts)
        _weights_from_preferred_countries(parts, release, ['FR'], 666)
        self.assertEqual(parts[0], (0.0, 666))
        _weights_from_preferred_countries(parts, release, ['GB'], 666)
        self.assertEqual(parts[1], (1.0, 666))

    def test_preferred_formats(self):
        release = load_test_json('release.json')
        parts = []
        _weights_from_preferred_formats(parts, release, [], 777)
        self.assertFalse(parts)
        _weights_from_preferred_formats(parts, release, ['Digital Media'], 777)
        self.assertEqual(parts[0], (0.0, 777))
        _weights_from_preferred_formats(parts, release, ['12" Vinyl'], 777)
        self.assertEqual(parts[1], (1.0, 777))


SimMatchTest = namedtuple('SimMatchTest', 'similarity name')


class SortBySimilarity(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.test_values = [
            SimMatchTest(similarity=0.74, name='d'),
            SimMatchTest(similarity=0.61, name='a'),
            SimMatchTest(similarity=0.75, name='b'),
            SimMatchTest(similarity=0.75, name='c'),
        ]

    def test_sort_by_similarity(self):
        results = [result.name for result in sort_by_similarity(self.test_values)]
        self.assertEqual(results, ['b', 'c', 'd', 'a'])

    def test_findbestmatch(self):
        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match(self.test_values, no_match)

        self.assertEqual(best_match.result.name, 'b')
        self.assertEqual(best_match.similarity, 0.75)

    def test_findbestmatch_nomatch(self):
        self.test_values = []

        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match(self.test_values, no_match)

        self.assertEqual(best_match.result.name, 'no_match')
        self.assertEqual(best_match.similarity, -1)

    def test_find_best_match_with_margin(self):
        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match_with_margin(self.test_values, no_match)

        self.assertEqual(best_match.result.name, 'b')
        self.assertEqual(best_match.similarity, 0.75)
        self.assertIsNone(best_match.reason)

    def test_find_best_match_with_margin_min_similarity(self):
        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match_with_margin(self.test_values, no_match, min_similarity=0.75)

        self.assertEqual(best_match.result.name, 'b')
        self.assertEqual(best_match.similarity, 0.75)
        self.assertIsNone(best_match.reason)

    def test_find_best_match_with_margin_ambiguous(self):
        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match_with_margin(self.test_values, no_match, min_margin=0.01)

        self.assertEqual(best_match.result.name, 'b')
        self.assertEqual(best_match.similarity, 0.75)
        self.assertEqual(best_match.reason, 'ambiguous')

    def test_find_best_match_with_margin_below_floor(self):
        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match_with_margin(self.test_values, no_match, min_similarity=0.76)

        self.assertEqual(best_match.result, no_match)
        self.assertEqual(best_match.similarity, -1)
        self.assertEqual(best_match.reason, 'below_floor')
