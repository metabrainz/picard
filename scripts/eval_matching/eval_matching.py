#!/usr/bin/env python3
"""
Synthetic corpus generator and evaluation harness for release matching.

Generates file metadata from known releases with various degradation patterns,
then measures how often the matcher correctly identifies the source release
among a set of candidates (correct + distractors).
"""

import json
from pathlib import Path
import random
import sys


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from picard.cluster import CLUSTER_COMPARISON_WEIGHTS
from picard.mbjson import release_to_metadata
from picard.metadata import Metadata


CORPUS_DIR = Path(__file__).parent / 'corpus'

# Real MB releases grouped by confusability scenario
# Each group: (target_file, [distractor_files], scenario_description)
EVAL_SCENARIOS = [
    # Same title, same artist, different albums (Weezer Blue vs Green)
    {
        'target': 'eval_release_3a8a6113.json',  # Weezer Blue 1994 US
        'distractors': [
            'eval_release_a9897d0b.json',  # Weezer Green 2001
            'eval_release_b072b162.json',  # Weezer Blue 1994 DE (same RG, different edition)
        ],
        'scenario': 'same_title_different_albums',
    },
    {
        'target': 'eval_release_a9897d0b.json',  # Weezer Green 2001
        'distractors': [
            'eval_release_3a8a6113.json',  # Weezer Blue 1994 US
            'eval_release_b072b162.json',  # Weezer Blue 1994 DE
        ],
        'scenario': 'same_title_different_albums',
    },
    # Same album, different editions (title spelling varies, artist name varies)
    {
        'target': 'eval_release_6a76904c.json',  # GY!BE kranky US "Lift Yr."
        'distractors': [
            'eval_release_e3334c4e.json',  # GY!BE Constellation AU "Lift Your...!"
            'eval_release_f77eeaef.json',  # GY!BE 2017 reissue "Lift Your..." (no !)
            'eval_release_748e3e26.json',  # GY!BE 2018 vinyl "Lift Your...To Heaven"
        ],
        'scenario': 'same_album_variant_titles',
    },
    {
        'target': 'eval_release_e3334c4e.json',  # GY!BE Constellation AU
        'distractors': [
            'eval_release_6a76904c.json',  # GY!BE kranky US
            'eval_release_f77eeaef.json',  # GY!BE 2017 reissue
            'eval_release_748e3e26.json',  # GY!BE 2018 vinyl
        ],
        'scenario': 'same_album_variant_titles',
    },
    # Multi-artist, different editions with different track counts
    {
        'target': 'eval_release_2810aeef.json',  # Collision Course 23 tracks
        'distractors': [
            'eval_release_a72497d5.json',  # Collision Course 13 tracks
            'eval_release_2c5e4198.json',  # Jay-Z solo album (wrong artist combo)
        ],
        'scenario': 'multi_artist_editions',
    },
    {
        'target': 'eval_release_a72497d5.json',  # Collision Course 13 tracks
        'distractors': [
            'eval_release_2810aeef.json',  # Collision Course 23 tracks
            'eval_release_2c5e4198.json',  # Jay-Z solo album
        ],
        'scenario': 'multi_artist_editions',
    },
    # EP vs other releases by same artist
    {
        'target': 'eval_release_20b2dd9a.json',  # Radiohead My Iron Lung EP
        'distractors': [
            'eval_release_2810aeef.json',  # Different artist entirely
            'eval_release_3a8a6113.json',  # Different artist entirely
        ],
        'scenario': 'ep_identification',
    },
    # Greatest Hits compilations - same artist, same title, different compilations
    {
        'target': 'eval_release_bab57bb1.json',  # Queen Greatest Hits 1981 US (14 tracks, no barcode)
        'distractors': [
            'eval_release_ee99a91b.json',  # Queen Greatest Hits 2008 (39 tracks)
            'eval_release_fcb78d0d.json',  # Queen Greatest Hits 1981 DE (18 tracks, no barcode)
        ],
        'scenario': 'greatest_hits_compilations',
    },
    {
        'target': 'eval_release_ee99a91b.json',  # Queen Greatest Hits 2008 (39 tracks)
        'distractors': [
            'eval_release_bab57bb1.json',  # Queen Greatest Hits 1981 US (14 tracks)
            'eval_release_fcb78d0d.json',  # Queen Greatest Hits 1981 DE (18 tracks)
        ],
        'scenario': 'greatest_hits_compilations',
    },
    # Classical - same composition, different performers
    {
        'target': 'eval_release_f390ab14.json',  # Beethoven 5 - Karajan/BPO 1978
        'distractors': [
            'eval_release_f394e886.json',  # Beethoven 5 - Szell/Cleveland 1977
        ],
        'scenario': 'classical_same_composition',
    },
    {
        'target': 'eval_release_f394e886.json',  # Beethoven 5 - Szell/Cleveland 1977
        'distractors': [
            'eval_release_f390ab14.json',  # Beethoven 5 - Karajan/BPO 1978
        ],
        'scenario': 'classical_same_composition',
    },
    # Non-Latin scripts - same album, different editions
    {
        'target': 'eval_release_3ac4a81e.json',  # 椎名林檎 三毒史 digital
        'distractors': [
            'eval_release_4fdf1514.json',  # 椎名林檎 三毒史 CD edition
        ],
        'scenario': 'non_latin_editions',
    },
    {
        'target': 'eval_release_4fdf1514.json',  # 椎名林檎 三毒史 CD edition
        'distractors': [
            'eval_release_3ac4a81e.json',  # 椎名林檎 三毒史 digital
        ],
        'scenario': 'non_latin_editions',
    },
    # Live vs studio - same artist, different albums
    {
        'target': 'eval_release_eccae410.json',  # Nirvana Nevermind (studio)
        'distractors': [
            'eval_release_f4469159.json',  # Nirvana MTV Unplugged (live)
            'eval_release_8e061dc4.json',  # Nevermind US alt edition (barcode with leading 0)
        ],
        'scenario': 'live_vs_studio',
    },
    {
        'target': 'eval_release_f4469159.json',  # Nirvana MTV Unplugged (live)
        'distractors': [
            'eval_release_eccae410.json',  # Nirvana Nevermind (studio)
            'eval_release_8e061dc4.json',  # Nevermind US alt edition
        ],
        'scenario': 'live_vs_studio',
    },
]


def load_release(filename):
    with open(CORPUS_DIR / filename, encoding='utf-8') as f:
        return json.load(f)


# --- Degradation patterns ---


def perfect(metadata, release):
    """No degradation — metadata exactly matches release."""
    pass


def missing_barcode(metadata, release):
    """File has no barcode tag (very common)."""
    metadata.pop('barcode', None)


def missing_date(metadata, release):
    """File has no date tag."""
    metadata.pop('date', None)


def year_only(metadata, release):
    """File has only the year, not full date."""
    if 'date' in metadata:
        date = metadata['date']
        if len(date) > 4:
            metadata['date'] = date[:4]


def typo_album(metadata, release):
    """Album name has a typo."""
    album = metadata.get('album', '')
    if len(album) > 3:
        i = random.randint(1, len(album) - 2)
        metadata['album'] = album[:i] + 'x' + album[i + 1 :]


def wrong_case_album(metadata, release):
    """Album name in wrong case."""
    if 'album' in metadata:
        metadata['album'] = metadata['album'].lower()


def missing_artist(metadata, release):
    """No albumartist tag."""
    metadata.pop('albumartist', None)


def extra_artist_suffix(metadata, release):
    """Artist has extra text (e.g., 'feat.' suffix)."""
    if 'albumartist' in metadata:
        metadata['albumartist'] = metadata['albumartist'] + ' feat. Someone'


def wrong_track_count(metadata, release):
    """Track count is off by one (bonus track edition)."""
    if '~totalalbumtracks' in metadata:
        try:
            n = int(metadata['~totalalbumtracks'])
            metadata['~totalalbumtracks'] = str(n + 1)
        except ValueError:
            pass
    if 'totaltracks' in metadata:
        try:
            n = int(metadata['totaltracks'])
            metadata['totaltracks'] = str(n + 1)
        except ValueError:
            pass


def wrong_barcode(metadata, release):
    """File has a barcode but it's wrong."""
    metadata['barcode'] = '9999999999999'


def missing_most(metadata, release):
    """Only album name and artist remain."""
    keep = {'album', 'albumartist'}
    for key in list(metadata.keys()):
        if key not in keep and not key.startswith('~'):
            metadata.pop(key, None)


def swapped_artist_album(metadata, release):
    """Artist and album are swapped (common ripping error)."""
    album = metadata.get('album', '')
    artist = metadata.get('albumartist', '')
    if album and artist:
        metadata['album'] = artist
        metadata['albumartist'] = album


DEGRADATIONS = [
    ('perfect', perfect),
    ('missing_barcode', missing_barcode),
    ('missing_date', missing_date),
    ('year_only', year_only),
    ('typo_album', typo_album),
    ('wrong_case_album', wrong_case_album),
    ('missing_artist', missing_artist),
    ('extra_artist_suffix', extra_artist_suffix),
    ('wrong_track_count', wrong_track_count),
    ('wrong_barcode', wrong_barcode),
    ('missing_most', missing_most),
    ('swapped_artist_album', swapped_artist_album),
]


# --- Corpus generation ---


def metadata_from_release(release):
    """Convert a release dict to Metadata as if it were file tags."""
    m = Metadata()
    release_to_metadata(release, m)
    # Also set totaltracks from media
    total = 0
    for media in release.get('media', []):
        total += media.get('track-count', 0)
    if total:
        m['totaltracks'] = str(release.get('media', [{}])[0].get('track-count', total))
        m['~totalalbumtracks'] = str(total)
    return m


def generate_corpus():
    """Generate test cases using real MB releases as targets and distractors."""
    corpus = []

    for scenario in EVAL_SCENARIOS:
        target = load_release(scenario['target'])
        distractors = [load_release(f) for f in scenario['distractors']]
        candidates = [target] + distractors

        for deg_name, deg_fn in DEGRADATIONS:
            m = metadata_from_release(target)
            deg_fn(m, target)

            corpus.append(
                {
                    'degradation': deg_name,
                    'release_title': target['title'],
                    'scenario': scenario['scenario'],
                    'metadata': m,
                    'correct_id': target['id'],
                    'candidates': candidates,
                }
            )

    return corpus


# --- Evaluation ---


def evaluate(corpus, weights):
    """Run the matcher on each corpus entry and report accuracy."""
    results = {'correct': 0, 'wrong': 0, 'ambiguous': 0, 'details': []}

    for entry in corpus:
        metadata = entry['metadata']
        scores = []

        for candidate in entry['candidates']:
            match = metadata.compare_to_release(candidate, weights)
            scores.append((match.similarity, candidate['id']))

        scores.sort(key=lambda x: x[0], reverse=True)
        best_sim = scores[0][0]
        best_id = scores[0][1]

        # Check for ties at the top
        tied_ids = [cid for sim, cid in scores if sim == best_sim]
        if len(tied_ids) > 1 and entry['correct_id'] in tied_ids:
            status = 'ambiguous'
            results['ambiguous'] += 1
        elif best_id == entry['correct_id']:
            status = 'correct'
            results['correct'] += 1
        else:
            status = 'wrong'
            results['wrong'] += 1

        results['details'].append(
            {
                'release': entry['release_title'],
                'degradation': entry['degradation'],
                'scenario': entry.get('scenario', '?'),
                'status': status,
                'best_sim': best_sim,
                'picked_id': best_id,
                'expected_id': entry['correct_id'],
                'margin': best_sim - scores[1][0] if len(scores) > 1 else 0,
            }
        )

    return results


def print_report(results, weights_name):
    total = results['correct'] + results['wrong'] + results['ambiguous']
    results['correct'] / total if total else 0
    print(f"\n{'=' * 70}")
    print(f"Matching evaluation: {weights_name}")
    print(f"{'=' * 70}")
    print(f"Correct:   {results['correct']}/{total} ({results['correct'] / total:.1%})")
    print(f"Ambiguous: {results['ambiguous']}/{total} ({results['ambiguous'] / total:.1%}) [tied with distractor]")
    print(f"Wrong:     {results['wrong']}/{total} ({results['wrong'] / total:.1%})")
    print()

    # Show problems
    problems = [d for d in results['details'] if d['status'] != 'correct']
    if problems:
        print("PROBLEMS:")
        print(f"{'Release':<25} {'Degradation':<22} {'Status':<10} {'Sim':<8} {'Margin':<8}")
        print(f"{'-' * 25} {'-' * 22} {'-' * 10} {'-' * 8} {'-' * 8}")
        for p in problems:
            print(
                f"{p['release']:<25} {p['degradation']:<22} {p['status']:<10} {p['best_sim']:<8.4f} {p['margin']:<8.4f}"
            )
    else:
        print("All cases matched correctly with clear margins!")

    # Per-degradation summary
    print("\nPer-degradation breakdown:")
    print(f"{'Degradation':<25} {'OK':<5} {'Amb':<5} {'Fail':<5} {'Total':<5} {'Rate':<8} {'Avg Margin':<10}")
    print(f"{'-' * 25} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 8} {'-' * 10}")
    from collections import Counter

    deg_ok = Counter()
    deg_amb = Counter()
    deg_fail = Counter()
    deg_total = Counter()
    deg_margins = {}
    for d in results['details']:
        deg = d['degradation']
        deg_total[deg] += 1
        deg_margins.setdefault(deg, []).append(d['margin'])
        if d['status'] == 'correct':
            deg_ok[deg] += 1
        elif d['status'] == 'ambiguous':
            deg_amb[deg] += 1
        else:
            deg_fail[deg] += 1
    for deg in [name for name, _ in DEGRADATIONS]:
        ok = deg_ok[deg]
        amb = deg_amb[deg]
        fail = deg_fail[deg]
        t = deg_total[deg]
        rate = ok / t if t else 0
        avg_margin = sum(deg_margins.get(deg, [0])) / len(deg_margins.get(deg, [1]))
        marker = ' ✗' if rate < 1.0 else ''
        print(f"{deg:<25} {ok:<5} {amb:<5} {fail:<5} {t:<5} {rate:<8.1%} {avg_margin:<10.4f}{marker}")

    # Per-scenario summary
    from collections import Counter as Counter2

    scen_ok = Counter2()
    scen_amb = Counter2()
    scen_fail = Counter2()
    scen_total = Counter2()
    for d in results['details']:
        scen = d.get('scenario', '?')
        scen_total[scen] += 1
        if d['status'] == 'correct':
            scen_ok[scen] += 1
        elif d['status'] == 'ambiguous':
            scen_amb[scen] += 1
        else:
            scen_fail[scen] += 1
    print("\nPer-scenario breakdown:")
    print(f"{'Scenario':<30} {'OK':<5} {'Amb':<5} {'Fail':<5} {'Total':<5} {'Rate':<8}")
    print(f"{'-' * 30} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 8}")
    for scen in sorted(scen_total.keys()):
        ok = scen_ok[scen]
        amb = scen_amb[scen]
        fail = scen_fail[scen]
        t = scen_total[scen]
        rate = ok / t if t else 0
        marker = ' ✗' if rate < 1.0 else ''
        print(f"{scen:<30} {ok:<5} {amb:<5} {fail:<5} {t:<5} {rate:<8.1%}{marker}")


def main():
    random.seed(42)  # Reproducible

    from collections import defaultdict
    from unittest.mock import MagicMock, patch

    defaults = defaultdict(
        lambda: False,
        {
            'preferred_release_countries': [],
            'preferred_release_formats': [],
            'release_type_scores': [('Album', 1.0), ('Single', 0.5), ('EP', 0.7), ('Other', 0.3)],
        },
    )
    mock_config = MagicMock()
    mock_config.setting = defaults
    with (
        patch('picard.config.get_config', return_value=mock_config),
        patch('picard.mbjson.get_config', return_value=mock_config),
        patch('picard.metadata.get_config', return_value=mock_config),
    ):
        corpus = generate_corpus()
        results = evaluate(corpus, CLUSTER_COMPARISON_WEIGHTS)
        print_report(results, 'CLUSTER_COMPARISON_WEIGHTS')


if __name__ == '__main__':
    main()
