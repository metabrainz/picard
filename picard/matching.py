# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2009, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012-2014, 2018, 2020 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2024 Laurent Monin
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018 Xincognito10
# Copyright (C) 2020 Gabriel Ferreira
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2022 Bob Swift
# Copyright (C) 2022 skelly37
# Copyright (C) 2024 x11x
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

from collections.abc import Iterable
from dataclasses import (
    dataclass,
    field,
)
from operator import attrgetter
from typing import (
    TYPE_CHECKING,
    Generic,
    Protocol,
    TypeAlias,
    TypeVar,
)

from picard.config import Config, get_config
from picard.mbjson import artist_credit_from_node, get_score
from picard.similarity import similarity2
from picard.util import (
    compare_barcodes,
    extract_year_from_date,
    linear_combination_of_weights,
)


if TYPE_CHECKING:
    from picard.metadata import Metadata

# lengths difference over this number of milliseconds will give a score of 0.0
# equal lengths will give a score of 1.0
# example
# a     b     score
# 20000 0     0.333333333333
# 20000 10000 0.666666666667
# 20000 20000 1.0
# 20000 30000 0.666666666667
# 20000 40000 0.333333333333
# 20000 50000 0.0
LENGTH_SCORE_THRESHOLD_MS = 30000

_DATE_MATCH_FACTORS = {
    'exact': 1.00,
    'year': 0.95,
    'close_year': 0.85,
    'exists_vs_null': 0.65,
    'no_release_date': 0.25,
    'differed': 0.0,
}

# Similarity keys that are on release-level. Keep in sync with compare_to_release_parts.
_RELEASE_WEIGHT_KEYS = {
    'similarity': frozenset({'album', 'albumartist', 'date', 'totaltracks', 'totalalbumtracks'}),
    'preferences': frozenset({'format', 'releasecountry', 'releasetype'}),
}


class Similar(Protocol):
    """Any type that provides a "similarity" attribute."""

    similarity: float


@dataclass
class SimMatchTrack:
    """Holds the similarity score and release/track data for a matched track."""

    similarity: float
    releasegroup: dict | None
    release: dict | None
    track: dict | None


@dataclass
class SimMatchRelease:
    """Holds the similarity score and release data for a matched release."""

    similarity: float
    release: dict | None


# Generic type variable that implements the Similar protocol.
S = TypeVar('S', bound=Similar)


@dataclass
class MatchResult(Generic[S]):
    similarity: float
    result: S
    reason: str | None = None


# Type for a pair of score and weight (e.g. (0.8, 12))
ScoreWeightPair: TypeAlias = tuple[float, int]

# Weight tuple used to effectively skip a release during matching.
# A large weight with score 0 means it only gets picked if there are no other options.
_SKIP_RELEASE_WEIGHT: ScoreWeightPair = (0, 999)

# Type for the tiered weights dict structure
TieredWeights: TypeAlias = dict[str, dict[str, int]]


@dataclass
class ReleaseMatchParts:
    """Structured matching result organized by tier.

    Tier 1 (identifiers): Exact matches like barcode, catalog number.
        High weight — decisive when present.
    Tier 2 (similarity): Fuzzy signals like album title, artist, track count, date.
        Moderate weight — core matching when identifiers are absent.
    Tier 3 (preferences): User preferences like country, format, release type.
        Low weight — tie-breaking discriminators.
    """

    identifiers: list[ScoreWeightPair] = field(default_factory=list)
    similarity: list[ScoreWeightPair] = field(default_factory=list)
    preferences: list[ScoreWeightPair] = field(default_factory=list)

    def merged_with(self, other: 'ReleaseMatchParts') -> 'ReleaseMatchParts':
        """Return a new ReleaseMatchParts combining self and other."""
        return ReleaseMatchParts(
            identifiers=self.identifiers + other.identifiers,
            similarity=self.similarity + other.similarity,
            preferences=self.preferences + other.preferences,
        )

    def combine_tiers(self) -> float:
        """Combine tiers with tier-aware logic instead of a flat average.

        - If identifiers strongly match (≥0.9): score is high, preferences
          only fine-tune (identifiers confirm this IS the release).
        - If identifiers strongly mismatch (≤0.1): score is capped low
          (identifiers say this is NOT the release, regardless of similarity).
        - Otherwise: similarity drives the score, preferences act as tiebreaker.
        """
        sim_score = linear_combination_of_weights(self.similarity) if self.similarity else None
        pref_score = linear_combination_of_weights(self.preferences) if self.preferences else 0.5

        if not self.identifiers:
            if sim_score is None:
                # Only preferences available (e.g., isvideo-only comparison)
                return pref_score
            # No identifiers — similarity drives, preferences tiebreak
            return sim_score * 0.9 + pref_score * 0.1

        id_score = linear_combination_of_weights(self.identifiers)

        if id_score >= 0.9:
            # Strong identifier match — this IS the release.
            # Include small similarity component to break ties between
            # candidates that both have matching identifiers.
            base = sim_score if sim_score is not None else 1.0
            return 0.85 + base * 0.1 + pref_score * 0.05
        if id_score <= 0.1:
            # Strong identifier mismatch — cap the score
            base = sim_score if sim_score is not None else 0.0
            return min(0.3, base * 0.3)

        # Partial identifier signal — blend all tiers
        base = sim_score if sim_score is not None else 0.5
        return id_score * 0.4 + base * 0.5 + pref_score * 0.1


def compare_to_release(metadata: 'Metadata', release: dict, weights: TieredWeights) -> SimMatchRelease:
    """
    Compare metadata to a MusicBrainz release. Produces a probability as a
    linear combination of weights that the metadata matches a certain album.
    """
    config = get_config()
    parts = _compare_to_release_parts(metadata, release, weights, config)
    sim = parts.combine_tiers() * get_score(release)
    return SimMatchRelease(similarity=sim, release=release)


def _compare_to_release_parts(
    metadata: 'Metadata', release: dict, weights: TieredWeights, config: Config | None = None
) -> ReleaseMatchParts:
    result = ReleaseMatchParts()
    id_w = weights.get('identifiers', {})
    sim_w = weights.get('similarity', {})
    pref_w = weights.get('preferences', {})

    # Tier 1: Identifiers — exact matches, cheap to compute
    if 'barcode' in id_w:
        file_barcode = metadata.get('barcode', '')
        if file_barcode and 'barcode' in release:
            release_barcode = release['barcode']
            if compare_barcodes(file_barcode, release_barcode):
                result.identifiers.append((1.0, id_w['barcode']))
            else:
                result.identifiers.append((0.0, id_w['barcode']))

    if 'catno' in id_w:
        file_catno = metadata.get('catalognumber', '')
        if file_catno and 'label-info' in release:
            release_label_info = release['label-info']
            if release_label_info:
                file_label = metadata.get('label', '') or ''
                score = _catno_label_score(file_catno, file_label, release_label_info)
                result.identifiers.append((score, id_w['catno']))

    # Tier 2: Similarity — fuzzy matching core
    with metadata._lock.lock_for_read():
        if 'album' in metadata and 'album' in sim_w:
            b = release['title']
            result.similarity.append((similarity2(metadata['album'], b), sim_w['album']))

        if 'albumartist' in metadata and 'albumartist' in sim_w:
            a = metadata['albumartist']
            b = artist_credit_from_node(release['artist-credit']).name
            result.similarity.append((similarity2(a, b), sim_w['albumartist']))

        if 'totaltracks' in sim_w:
            try:
                a = int(metadata['totaltracks'])
                if 'media' in release:
                    score = 0.0
                    for media in release['media']:
                        b = media.get('track-count', 0)
                        score = max(score, _trackcount_score(a, b))
                        if score == 1.0:
                            break
                else:
                    b = release['track-count']
                    score = _trackcount_score(a, b)
                result.similarity.append((score, sim_w['totaltracks']))
            except (ValueError, KeyError):
                pass

        if 'totalalbumtracks' in sim_w:
            try:
                a = int(metadata['~totalalbumtracks'] or metadata['totaltracks'])
                if 'track-count' in release:
                    b = release['track-count']
                else:
                    b = sum(m.get('track-count', 0) for m in release.get('media', []))
                score = _trackcount_score(a, b)
                result.similarity.append((score, sim_w['totalalbumtracks']))
            except (ValueError, KeyError):
                pass

        # Date matching
        if 'date' in sim_w:
            result.similarity.append((_date_score(release, metadata), sim_w['date']))

    # Tier 3: Preferences — tie-breaking discriminators
    if config is None:
        config = get_config()
    if 'releasecountry' in pref_w:
        _weights_from_preferred_countries(
            result.preferences,
            release,
            config.setting['preferred_release_countries'],
            pref_w['releasecountry'],
        )

    if 'format' in pref_w:
        _weights_from_preferred_formats(
            result.preferences,
            release,
            config.setting['preferred_release_formats'],
            pref_w['format'],
        )

    if 'releasetype' in pref_w:
        _weights_from_preferred_release_types(
            result.preferences,
            release,
            config.setting['preferred_release_types'],
            config.setting['discouraged_release_types'],
            pref_w['releasetype'],
        )

    return result


def compare_to_track(metadata: 'Metadata', track: dict, weights: TieredWeights) -> SimMatchTrack:
    track_parts = ReleaseMatchParts()
    releases = []
    id_w = weights.get('identifiers', {})
    sim_w = weights.get('similarity', {})
    pref_w = weights.get('preferences', {})

    with metadata._lock.lock_for_read():
        # Tier 1: ISRC — recording-level identifier
        if 'isrc' in id_w:
            file_isrcs = metadata.getall('isrc')
            if file_isrcs:
                recording = track.get('recording', track)
                track_isrcs = recording.get('isrcs', [])
                score = _isrcs_score(file_isrcs, track_isrcs)
                track_parts.identifiers.append((score, id_w['isrc']))

        # Track-level similarity signals
        if 'title' in metadata and 'title' in sim_w:
            a = metadata['title']
            b = track.get('title', '')
            track_parts.similarity.append((similarity2(a, b), sim_w["title"]))

        if 'artist' in metadata and 'artist' in sim_w:
            a = metadata['artist']
            artist_credits = track.get('artist-credit', [])
            b = artist_credit_from_node(artist_credits).name
            track_parts.similarity.append((similarity2(a, b), sim_w["artist"]))

        a = metadata.length
        if a > 0 and 'length' in track and 'length' in sim_w:
            b = track['length']
            score = length_score(a, b)
            track_parts.similarity.append((score, sim_w["length"]))

        if 'isvideo' in pref_w:
            metadata_is_video = metadata['~video'] == '1'
            track_is_video = bool(track.get('video'))
            score = 1 if metadata_is_video == track_is_video else 0
            track_parts.preferences.append((score, pref_w['isvideo']))

        if "releases" in track:
            releases = track['releases']

            if 'tracknumber' in metadata and 'tracknumber' in sim_w:
                sim = _compare_tracknumber(track.get('recording', {}).get('id'), metadata, releases)
                track_parts.similarity.append((sim, sim_w["tracknumber"]))

        search_score = get_score(track)
        if not releases:
            # No releases available — use neutral score (0.5) for all
            # release-level weights, ensuring tracks with releases are preferred.
            release_parts = _get_weighted_release_parts(weights, 0.5)
            track_parts = track_parts.merged_with(release_parts)
            sim = track_parts.combine_tiers() * search_score
            return SimMatchTrack(similarity=sim, releasegroup=None, release=None, track=track)

    result = SimMatchTrack(similarity=-1, releasegroup=None, release=None, track=None)
    config = get_config()
    for release in releases:
        release_parts = _compare_to_release_parts(metadata, release, weights, config)
        combined = track_parts.merged_with(release_parts)
        sim = combined.combine_tiers() * search_score
        if sim > result.similarity:
            rg = release['release-group'] if "release-group" in release else None
            result = SimMatchTrack(similarity=sim, releasegroup=rg, release=release, track=track)
    return result


def sort_by_similarity(candidates: Iterable[S]) -> list[S]:
    """Sorts the objects in candidates by similarity.

    Args:
        candidates: Iterable with objects having a `similarity` attribute
    Returns: List of candidates sorted by similarity (highest similarity first)
    """
    return sorted(candidates, reverse=True, key=attrgetter('similarity'))


def find_best_match(candidates: Iterable[S], no_match: S) -> MatchResult[S]:
    """Returns a MatchResult based on the similarity of candidates.

    Args:
        candidates: Iterable with objects having a `similarity` attribute
        no_match: Match to return if there was no candidate

    Returns: `MatchResult` with the similarity and the matched object as result.
    """
    best_match = max(candidates, key=attrgetter('similarity'), default=no_match)
    return MatchResult(similarity=getattr(best_match, 'similarity', 0.0), result=best_match)


def find_best_match_with_margin(
    candidates: Iterable[S], no_match: S, min_similarity: float = 0.0, min_margin: float = 0.0
) -> MatchResult[S]:
    """Find best match, flagging if below floor or margin is too small.

    Args:
        candidates: Iterable with objects having a `similarity` attribute
        no_match: Match to return if no candidate passes the floor
        min_similarity: Reject if best score is below this floor
        min_margin: Flag as ambiguous if best - second_best < this value
            (skipped when there's only one candidate)

    Returns: `MatchResult` with similarity, result, and reason.
        reason is None (confident), 'ambiguous' (margin too small,
        best match still returned), or 'below_floor' (no_match returned).
    """
    best = no_match
    second_best_sim = -1.0
    for candidate in candidates:
        sim = candidate.similarity
        if sim > best.similarity:
            second_best_sim = best.similarity
            best = candidate
        elif sim > second_best_sim:
            second_best_sim = sim

    if best.similarity < min_similarity:
        return MatchResult(similarity=no_match.similarity, result=no_match, reason='below_floor')

    if second_best_sim >= 0 and (best.similarity - second_best_sim) < min_margin:
        return MatchResult(similarity=best.similarity, result=best, reason='ambiguous')

    return MatchResult(similarity=best.similarity, result=best, reason=None)


def length_score(a: int | None, b: int | None) -> float:
    """Compare two track lengths and calculate a similarity score.
    The similarity is based on the absolute difference between the lengths,
    with a threshold of LENGTH_SCORE_THRESHOLD_MS. The score will degrade linearly
    up to a difference of LENGTH_SCORE_THRESHOLD_MS.
    """
    if a is None or b is None:
        return 0.0
    return 1.0 - min(abs(a - b), LENGTH_SCORE_THRESHOLD_MS) / float(LENGTH_SCORE_THRESHOLD_MS)


def _date_score(release: dict, metadata: 'Metadata') -> float:
    """Score how well the file's date matches the release date."""
    if not release.get('date'):
        return _DATE_MATCH_FACTORS['no_release_date']
    release_date = release['date']
    if 'date' not in metadata:
        return _DATE_MATCH_FACTORS['exists_vs_null']
    metadata_date = metadata['date']
    if release_date == metadata_date:
        return _DATE_MATCH_FACTORS['exact']
    release_year = extract_year_from_date(release_date)
    if release_year is None:
        return 0.0
    metadata_year = extract_year_from_date(metadata_date)
    if metadata_year is None:
        return 0.0
    if release_year == metadata_year:
        return _DATE_MATCH_FACTORS['year']
    if abs(release_year - metadata_year) <= 2:
        return _DATE_MATCH_FACTORS['close_year']
    return _DATE_MATCH_FACTORS['differed']


def _catno_label_score(file_catno: str, file_label: str, release_label_info: list[dict]) -> float:
    """Score catalog number + label match against release label-info.

    Returns 1.0 for exact catno match (with matching or absent label),
    0.0 for catno mismatch when release has catalog numbers.
    """
    release_catnos = []
    for li in release_label_info:
        cat = li.get('catalog-number', '')
        if cat:
            label_name = ''
            if label := li.get('label', None):
                label_name = label.get('name', '')
            release_catnos.append((cat, label_name))

    if not release_catnos:
        return 0.5  # release has no catalog numbers, neutral

    file_catno = file_catno.strip().lower()
    file_label = file_label.strip().lower()
    for release_catno, release_label in release_catnos:
        if file_catno == release_catno.strip().lower():
            # Catno matches; if file also has label, check it too
            if not file_label or not release_label:
                return 1.0
            if file_label == release_label.strip().lower():
                return 1.0
            # Catno matches but label differs — still a good signal
            return 0.8
    # File has a catno but it doesn't match any on this release
    return 0.0


def _trackcount_score(actual: int, expected: int) -> float:
    """Score how well a file's track count matches a release's track count.

    Returns 1.0 for exact match, degrades based on the ratio of difference
    to expected count. Files with more tracks than the release are penalized
    more heavily (impossible without bonus tracks), but not zeroed out.
    """
    if actual == expected:
        return 1.0
    if expected == 0:
        return 0.0
    diff = abs(actual - expected)
    ratio = diff / expected
    if actual > expected:
        # File claims more tracks than release has — unlikely but possible
        # (bonus track edition, tagging error)
        return max(0.0, 1.0 - ratio * 3)
    else:
        # File has fewer tracks — could be single disc of multi-disc release
        return max(0.0, 1.0 - ratio * 2)


def _compare_tracknumber(recording_id: str, metadata: 'Metadata', releases: list[dict]) -> float:
    """Compares the track number from metadata to the track number in the release."""
    try:
        tracknumber = int(metadata['tracknumber'])
    except ValueError:
        tracknumber = None

    # Find the track in the media and compare track numbers
    if tracknumber:
        for release in releases:
            for medium in release.get('media', []):
                track_offset = medium.get('track-offset', None)

                # For recording lookups the web service returns only a "track" field
                # containing the the track corresponding to the recording and sets
                # the track-offset to indicate the number of skipped tracks before it.
                # The track has no position field, so we use the track-offset to compare.
                if track_offset is not None and 'track' in medium:
                    if medium['track'] and tracknumber == track_offset + 1:
                        return 1.0
                    continue
                # Else if the data contains a "tracks" field with full track listing
                # search for the track with matching recording and compare its position.
                else:
                    tracks = medium.get('tracks', [])
                    matching_tracks = filter(
                        lambda t: t.get('recording', {}).get('id') == recording_id,
                        tracks,
                    )
                    for matching_track in matching_tracks:
                        if matching_track.get('position') == tracknumber:
                            return 1.0
        # Track number did not match on any medium across all releases
        return 0.0

    # No valid track number in metadata — neutral (neither confirms nor denies)
    return 0.5


def _isrcs_score(file_isrcs: Iterable[str], track_isrcs: Iterable[str]) -> float:
    file_isrcs = set(isrc.upper() for isrc in file_isrcs)
    track_isrcs = set(isrc.upper() for isrc in track_isrcs)
    # Candidate has no ISRCs — neutral (neither confirms nor denies)
    if not file_isrcs or not track_isrcs:
        return 0.5
    # All file ISRCs are present in the track ISRCs — perfect match
    elif file_isrcs.issubset(track_isrcs):
        return 1.0
    # Some file ISRCs are present in the track ISRCs — partial match
    elif file_isrcs.intersection(track_isrcs):
        return 0.8
    return 0.0


def _get_weighted_release_parts(weights: dict[str, dict[str, int]], score: float) -> ReleaseMatchParts:
    """Sum of all release-level weights (used as fallback when no releases are available).

    Consider only release-level similarity keys (see _RELEASE_WEIGHT_KEYS).
    """
    result = ReleaseMatchParts()
    for tier in {'similarity', 'preferences'}:
        if tier in weights:
            keys = _RELEASE_WEIGHT_KEYS.get(tier, [])
            total_weight = sum(value for key, value in weights[tier].items() if key in keys)
            getattr(result, tier).append((score, total_weight))
    return result


def _weights_from_preferred_release_types(
    parts: list[ScoreWeightPair],
    release: dict,
    preferred_types: list[str],
    discouraged_types: list[str],
    weight_release_type: int = 1,
) -> None:
    """Score a release based on preferred/discouraged release type lists.

    Scoring:
    - Preferred types: position-based score (first = highest), range (0.5, 1.0]
    - Discouraged types: score 0, triggers skip (large zero weight)
    - Unlisted types: neutral score 0.5

    If a release has multiple types (primary + secondary), the scores are averaged.
    If any type is discouraged, the release is skipped entirely.
    """
    skip_release = False
    score = 0.0
    total_preferred = len(preferred_types)

    if 'release-group' in release and 'primary-type' in release['release-group']:
        types_found = [release['release-group']['primary-type']]
        if 'secondary-types' in release['release-group']:
            types_found += release['release-group']['secondary-types']
        for release_type in types_found:
            if release_type in discouraged_types:
                skip_release = True
            elif total_preferred and release_type in preferred_types:
                i = preferred_types.index(release_type)
                score += 0.5 + 0.5 * (total_preferred - i) / total_preferred
            else:
                score += 0.5
        score /= len(types_found)
    else:
        score = 0.5

    if skip_release:
        parts.append(_SKIP_RELEASE_WEIGHT)
    else:
        parts.append((score, weight_release_type))


def _weights_from_preferred_countries(parts, release, preferred_countries, weight):
    total_countries = len(preferred_countries)
    if total_countries:
        score = 0.0
        if "country" in release:
            try:
                i = preferred_countries.index(release['country'])
                score = float(total_countries - i) / float(total_countries)
            except ValueError:
                pass
        parts.append((score, weight))


def _weights_from_preferred_formats(parts, release, preferred_formats, weight):
    total_formats = len(preferred_formats)
    if total_formats and 'media' in release:
        score = 0.0
        subtotal = 0
        for medium in release['media']:
            if "format" in medium:
                try:
                    i = preferred_formats.index(medium['format'])
                    score += float(total_formats - i) / float(total_formats)
                except ValueError:
                    pass
                subtotal += 1
        if subtotal > 0:
            score /= subtotal
        parts.append((score, weight))
