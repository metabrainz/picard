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

from collections import namedtuple
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    TypeAlias,
)

from picard.util import (
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

DATE_MATCH_FACTORS = {
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


SimMatchTrack = namedtuple('SimMatchTrack', 'similarity releasegroup release track')
SimMatchRelease = namedtuple('SimMatchRelease', 'similarity release')


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

    identifiers: list[tuple[float, int]] = field(default_factory=list)
    similarity: list[tuple[float, int]] = field(default_factory=list)
    preferences: list[tuple[float, int]] = field(default_factory=list)

    @property
    def all_parts(self) -> list[tuple[float, int]]:
        """Flat list of all (score, weight) tuples for linear combination."""
        return self.identifiers + self.similarity + self.preferences

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


# Type for the tiered weights dict structure
TieredWeights: TypeAlias = dict[str, dict[str, int]]


def weights_from_release_type_scores(parts, release, release_type_scores, weight_release_type=1):
    # This function generates a score that determines how likely this release will be selected in a lookup.
    # The score goes from 0 to 1 with 1 being the most likely to be chosen and 0 the least likely
    # This score is based on the preferences of release-types found in this release
    # This algorithm works by taking the scores of the primary type (and secondary if found) and averages them
    # If no types are found, it is set to the score of the 'Other' type or 0.5 if 'Other' doesnt exist
    # It appends (score, weight_release_type) to passed parts list

    # if our preference is zero for the release_type, force to never return this recording
    # by using a large zero weight. This means it only gets picked if there are no others at all.
    skip_release = False

    type_scores = dict(release_type_scores)
    score = 0.0
    other_score = type_scores.get('Other', 0.5)
    if 'release-group' in release and 'primary-type' in release['release-group']:
        types_found = [release['release-group']['primary-type']]
        if 'secondary-types' in release['release-group']:
            types_found += release['release-group']['secondary-types']
        for release_type in types_found:
            type_score = type_scores.get(release_type, other_score)
            if type_score == 0:
                skip_release = True
            score += type_score
        score /= len(types_found)
    else:
        score = other_score

    if skip_release:
        parts.append((0, 9999))
    else:
        parts.append((score, weight_release_type))


def weights_from_preferred_countries(parts, release, preferred_countries, weight):
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


def weights_from_preferred_formats(parts, release, preferred_formats, weight):
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


def _date_score(release: dict, metadata: 'Metadata') -> float:
    """Score how well the file's date matches the release date."""
    if not release.get('date'):
        return DATE_MATCH_FACTORS['no_release_date']
    release_date = release['date']
    if 'date' not in metadata:
        return DATE_MATCH_FACTORS['exists_vs_null']
    metadata_date = metadata['date']
    if release_date == metadata_date:
        return DATE_MATCH_FACTORS['exact']
    release_year = extract_year_from_date(release_date)
    if release_year is None:
        return 0.0
    metadata_year = extract_year_from_date(metadata_date)
    if metadata_year is None:
        return 0.0
    if release_year == metadata_year:
        return DATE_MATCH_FACTORS['year']
    if abs(release_year - metadata_year) <= 2:
        return DATE_MATCH_FACTORS['close_year']
    return DATE_MATCH_FACTORS['differed']


def _catno_label_score(file_catno: str, file_label: str, release_label_info: list[dict]) -> float:
    """Score catalog number + label match against release label-info.

    file_catno and file_label should be pre-normalized (stripped, lowercased).
    Returns 1.0 for exact catno match (with matching or absent label),
    0.0 for catno mismatch when release has catalog numbers.
    """
    release_catnos = []
    for li in release_label_info:
        cat = li.get('catalog-number', '')
        if cat:
            label_name = ''
            if 'label' in li and li['label']:
                label_name = li['label'].get('name', '')
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
