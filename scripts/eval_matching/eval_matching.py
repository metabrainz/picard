#!/usr/bin/env python3
"""Release matching evaluation harness.

Measures how accurately Picard's release matcher identifies the correct release
from a set of candidates when file metadata is degraded in various ways.

Usage:
    python scripts/eval_matching/eval_matching.py

How it works:
    1. For each scenario, a "target" release is the correct answer and
       "distractors" are plausible wrong candidates.
    2. File metadata is generated from the target, then degraded (typos,
       missing fields, wrong values) to simulate real-world imperfect tags.
    3. The matcher scores all candidates; we check if the target wins.

Extending:
    - Add releases: drop JSON files in corpus/ (fetched from MB API with
      inc=artist-credits+media+release-groups&fmt=json)
    - Add scenarios: append to SCENARIOS list
    - Add degradations: define a function(metadata, release) and add to DEGRADATIONS
"""

from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import sys
from unittest.mock import (
    MagicMock,
    patch,
)


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from picard.cluster import CLUSTER_COMPARISON_WEIGHTS
from picard.mbjson import release_to_metadata
from picard.metadata import Metadata


CORPUS_DIR = Path(__file__).parent / "corpus"


# =============================================================================
# Scenarios
# =============================================================================
# Each scenario defines a target release and distractors (plausible wrong matches).
# To add a new scenario: add a release JSON to corpus/, then append here.

SCENARIOS = [
    # --- Same title, same artist, different albums ---
    {
        "target": "eval_release_3a8a6113.json",  # Weezer Blue 1994 US
        "distractors": [
            "eval_release_a9897d0b.json",  # Weezer Green 2001
            "eval_release_b072b162.json",  # Weezer Blue 1994 DE edition
        ],
        "scenario": "same_title_different_albums",
    },
    {
        "target": "eval_release_a9897d0b.json",  # Weezer Green 2001
        "distractors": [
            "eval_release_3a8a6113.json",  # Weezer Blue 1994 US
            "eval_release_b072b162.json",  # Weezer Blue 1994 DE
        ],
        "scenario": "same_title_different_albums",
    },
    # --- Same album, variant title spellings / artist name changes ---
    {
        "target": "eval_release_6a76904c.json",  # GY!BE kranky US "Lift Yr."
        "distractors": [
            "eval_release_e3334c4e.json",  # Constellation AU "Lift Your...!"
            "eval_release_f77eeaef.json",  # 2017 reissue "Lift Your..."
            "eval_release_748e3e26.json",  # 2018 vinyl "...To Heaven"
        ],
        "scenario": "same_album_variant_titles",
    },
    {
        "target": "eval_release_e3334c4e.json",  # GY!BE Constellation AU
        "distractors": [
            "eval_release_6a76904c.json",  # kranky US
            "eval_release_f77eeaef.json",  # 2017 reissue
            "eval_release_748e3e26.json",  # 2018 vinyl
        ],
        "scenario": "same_album_variant_titles",
    },
    # --- Multi-artist, different editions with different track counts ---
    {
        "target": "eval_release_2810aeef.json",  # Collision Course 23 tracks
        "distractors": [
            "eval_release_a72497d5.json",  # Collision Course 13 tracks
            "eval_release_2c5e4198.json",  # Jay-Z solo album
        ],
        "scenario": "multi_artist_editions",
    },
    {
        "target": "eval_release_a72497d5.json",  # Collision Course 13 tracks
        "distractors": [
            "eval_release_2810aeef.json",  # Collision Course 23 tracks
            "eval_release_2c5e4198.json",  # Jay-Z solo album
        ],
        "scenario": "multi_artist_editions",
    },
    # --- EP identification ---
    {
        "target": "eval_release_20b2dd9a.json",  # Radiohead My Iron Lung EP
        "distractors": [
            "eval_release_2810aeef.json",  # Different artist
            "eval_release_3a8a6113.json",  # Different artist
        ],
        "scenario": "ep_identification",
    },
    # --- Greatest Hits: same artist, same title, different compilations ---
    {
        "target": "eval_release_bab57bb1.json",  # Queen GH 1981 US (14t, no barcode)
        "distractors": [
            "eval_release_ee99a91b.json",  # Queen GH 2008 (39t)
            "eval_release_fcb78d0d.json",  # Queen GH 1981 DE (18t, no barcode)
        ],
        "scenario": "greatest_hits_compilations",
    },
    {
        "target": "eval_release_ee99a91b.json",  # Queen GH 2008 (39t)
        "distractors": [
            "eval_release_bab57bb1.json",  # Queen GH 1981 US (14t)
            "eval_release_fcb78d0d.json",  # Queen GH 1981 DE (18t)
        ],
        "scenario": "greatest_hits_compilations",
    },
    # --- Classical: same composition, different performers ---
    {
        "target": "eval_release_f390ab14.json",  # Beethoven 5 - Karajan 1978
        "distractors": [
            "eval_release_f394e886.json",  # Beethoven 5 - Szell 1977
        ],
        "scenario": "classical_same_composition",
    },
    {
        "target": "eval_release_f394e886.json",  # Beethoven 5 - Szell 1977
        "distractors": [
            "eval_release_f390ab14.json",  # Beethoven 5 - Karajan 1978
        ],
        "scenario": "classical_same_composition",
    },
    # --- Non-Latin scripts: same album, different editions ---
    {
        "target": "eval_release_3ac4a81e.json",  # 椎名林檎 三毒史 digital
        "distractors": [
            "eval_release_4fdf1514.json",  # 椎名林檎 三毒史 CD
        ],
        "scenario": "non_latin_editions",
    },
    {
        "target": "eval_release_4fdf1514.json",  # 椎名林檎 三毒史 CD
        "distractors": [
            "eval_release_3ac4a81e.json",  # 椎名林檎 三毒史 digital
        ],
        "scenario": "non_latin_editions",
    },
    # --- Live vs studio: same artist, different albums ---
    {
        "target": "eval_release_eccae410.json",  # Nirvana Nevermind
        "distractors": [
            "eval_release_f4469159.json",  # Nirvana MTV Unplugged
            "eval_release_8e061dc4.json",  # Nevermind alt edition (leading-0 barcode)
        ],
        "scenario": "live_vs_studio",
    },
    {
        "target": "eval_release_f4469159.json",  # Nirvana MTV Unplugged
        "distractors": [
            "eval_release_eccae410.json",  # Nirvana Nevermind
            "eval_release_8e061dc4.json",  # Nevermind alt edition
        ],
        "scenario": "live_vs_studio",
    },
]


# =============================================================================
# Degradation patterns
# =============================================================================
# Each function mutates a Metadata object to simulate imperfect file tags.
# Signature: fn(metadata: Metadata, release: dict) -> None
# To add a new degradation: define the function and append to DEGRADATIONS.


def perfect(metadata, release):
    """No degradation — metadata exactly matches release."""


def missing_barcode(metadata, release):
    """Remove barcode tag (very common in real files)."""
    metadata.pop("barcode", None)


def missing_date(metadata, release):
    """Remove date tag entirely."""
    metadata.pop("date", None)


def year_only(metadata, release):
    """Truncate date to year only (e.g., '1994-05-10' → '1994')."""
    if "date" in metadata and len(metadata["date"]) > 4:
        metadata["date"] = metadata["date"][:4]


def typo_album(metadata, release):
    """Introduce a single-character typo in album name."""
    album = metadata.get("album", "")
    if len(album) > 3:
        i = random.randint(1, len(album) - 2)
        metadata["album"] = album[:i] + "x" + album[i + 1 :]


def wrong_case_album(metadata, release):
    """Lowercase the album name."""
    if "album" in metadata:
        metadata["album"] = metadata["album"].lower()


def missing_artist(metadata, release):
    """Remove albumartist tag."""
    metadata.pop("albumartist", None)


def extra_artist_suffix(metadata, release):
    """Append 'feat. Someone' to artist (common in poorly tagged files)."""
    if "albumartist" in metadata:
        metadata["albumartist"] = metadata["albumartist"] + " feat. Someone"


def wrong_track_count(metadata, release):
    """Increment track count by 1 (simulates bonus track edition)."""
    for key in ("~totalalbumtracks", "totaltracks"):
        if key in metadata:
            try:
                metadata[key] = str(int(metadata[key]) + 1)
            except ValueError:
                pass


def wrong_barcode(metadata, release):
    """Replace barcode with an incorrect value."""
    metadata["barcode"] = "9999999999999"


def missing_most(metadata, release):
    """Strip everything except album and artist (minimal metadata)."""
    keep = {"album", "albumartist"}
    for key in list(metadata.keys()):
        if key not in keep and not key.startswith("~"):
            metadata.pop(key, None)


def swapped_artist_album(metadata, release):
    """Swap artist and album fields (common ripping/tagging error)."""
    album = metadata.get("album", "")
    artist = metadata.get("albumartist", "")
    if album and artist:
        metadata["album"] = artist
        metadata["albumartist"] = album


DEGRADATIONS = [
    ("perfect", perfect),
    ("missing_barcode", missing_barcode),
    ("missing_date", missing_date),
    ("year_only", year_only),
    ("typo_album", typo_album),
    ("wrong_case_album", wrong_case_album),
    ("missing_artist", missing_artist),
    ("extra_artist_suffix", extra_artist_suffix),
    ("wrong_track_count", wrong_track_count),
    ("wrong_barcode", wrong_barcode),
    ("missing_most", missing_most),
    ("swapped_artist_album", swapped_artist_album),
]


# =============================================================================
# Corpus generation
# =============================================================================


def load_release(filename):
    """Load a release JSON fixture from the corpus directory."""
    with open(CORPUS_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def metadata_from_release(release):
    """Convert a MB release dict to Metadata, simulating file tags.

    Populates album, artist, date, barcode, totaltracks, etc. from the
    release data as if a file had been tagged from this release.
    """
    m = Metadata()
    release_to_metadata(release, m)
    total = sum(media.get("track-count", 0) for media in release.get("media", []))
    if total:
        first_medium_tracks = release.get("media", [{}])[0].get("track-count", total)
        m["totaltracks"] = str(first_medium_tracks)
        m["~totalalbumtracks"] = str(total)
    return m


def generate_corpus():
    """Build the evaluation corpus from scenarios and degradations.

    For each scenario × degradation combination, generates one test case
    consisting of degraded file metadata and a candidate set (target + distractors).
    """
    corpus = []
    for scenario in SCENARIOS:
        target = load_release(scenario["target"])
        distractors = [load_release(f) for f in scenario["distractors"]]
        candidates = [target] + distractors

        for deg_name, deg_fn in DEGRADATIONS:
            m = metadata_from_release(target)
            deg_fn(m, target)
            corpus.append(
                {
                    "degradation": deg_name,
                    "scenario": scenario["scenario"],
                    "release_title": target["title"],
                    "metadata": m,
                    "correct_id": target["id"],
                    "candidates": candidates,
                }
            )
    return corpus


# =============================================================================
# Evaluation
# =============================================================================


def evaluate(corpus, weights):
    """Score each corpus entry and classify as correct/ambiguous/wrong.

    Returns a dict with counts and per-entry details including margin
    (score difference between best and second-best candidate).
    """
    results = {"correct": 0, "wrong": 0, "ambiguous": 0, "details": []}

    for entry in corpus:
        scores = [(entry["metadata"].compare_to_release(c, weights).similarity, c["id"]) for c in entry["candidates"]]
        scores.sort(key=lambda x: x[0], reverse=True)
        best_sim, best_id = scores[0]
        margin = best_sim - scores[1][0] if len(scores) > 1 else 0

        # Classify result
        tied_ids = {cid for sim, cid in scores if sim == best_sim}
        if len(tied_ids) > 1 and entry["correct_id"] in tied_ids:
            status = "ambiguous"
        elif best_id == entry["correct_id"]:
            status = "correct"
        else:
            status = "wrong"
        results[status] += 1

        results["details"].append(
            {
                "release": entry["release_title"],
                "degradation": entry["degradation"],
                "scenario": entry["scenario"],
                "status": status,
                "best_sim": best_sim,
                "margin": margin,
            }
        )

    return results


# =============================================================================
# Reporting
# =============================================================================


def _grouped_breakdown(details, group_key, group_names=None):
    """Compute per-group OK/ambiguous/fail counts from detail entries."""
    ok = Counter()
    amb = Counter()
    fail = Counter()
    total = Counter()
    margins = defaultdict(list)

    for d in details:
        g = d[group_key]
        total[g] += 1
        margins[g].append(d["margin"])
        if d["status"] == "correct":
            ok[g] += 1
        elif d["status"] == "ambiguous":
            amb[g] += 1
        else:
            fail[g] += 1

    names = group_names or sorted(total.keys())
    return [(n, ok[n], amb[n], fail[n], total[n], margins[n]) for n in names]


def print_report(results, weights_name):
    """Print a formatted evaluation report to stdout."""
    total = results["correct"] + results["wrong"] + results["ambiguous"]
    print(f"\n{'=' * 70}")
    print(f"  {weights_name}")
    print(f"{'=' * 70}")
    print(f"  Correct:   {results['correct']:>3}/{total} ({results['correct'] / total:.1%})")
    print(f"  Ambiguous: {results['ambiguous']:>3}/{total} ({results['ambiguous'] / total:.1%})")
    print(f"  Wrong:     {results['wrong']:>3}/{total} ({results['wrong'] / total:.1%})")

    # Problems
    problems = [d for d in results["details"] if d["status"] != "correct"]
    if problems:
        print(f"\n  {'Release':<25} {'Degradation':<22} {'Status':<9} {'Sim':>6} {'Margin':>6}")
        print(f"  {'-' * 25} {'-' * 22} {'-' * 9} {'-' * 6} {'-' * 6}")
        for p in problems:
            print(
                f"  {p['release'][:25]:<25} {p['degradation']:<22} "
                f"{p['status']:<9} {p['best_sim']:6.4f} {p['margin']:6.4f}"
            )

    # Per-degradation
    deg_names = [name for name, _ in DEGRADATIONS]
    rows = _grouped_breakdown(results["details"], "degradation", deg_names)
    print(f"\n  {'Degradation':<25} {'OK':>3} {'Amb':>3} {'Fail':>4} {'N':>3} {'Rate':>6} {'AvgMargin':>9}")
    print(f"  {'-' * 25} {'-' * 3} {'-' * 3} {'-' * 4} {'-' * 3} {'-' * 6} {'-' * 9}")
    for name, ok, amb, fail, n, margins in rows:
        rate = ok / n if n else 0
        avg_m = sum(margins) / len(margins) if margins else 0
        flag = " ✗" if rate < 1.0 else ""
        print(f"  {name:<25} {ok:>3} {amb:>3} {fail:>4} {n:>3} {rate:>5.0%} {avg_m:>9.4f}{flag}")

    # Per-scenario
    rows = _grouped_breakdown(results["details"], "scenario")
    print(f"\n  {'Scenario':<30} {'OK':>3} {'Amb':>3} {'Fail':>4} {'N':>3} {'Rate':>6}")
    print(f"  {'-' * 30} {'-' * 3} {'-' * 3} {'-' * 4} {'-' * 3} {'-' * 6}")
    for name, ok, amb, fail, n, _ in rows:
        rate = ok / n if n else 0
        flag = " ✗" if rate < 1.0 else ""
        print(f"  {name:<30} {ok:>3} {amb:>3} {fail:>4} {n:>3} {rate:>5.0%}{flag}")


# =============================================================================
# Configuration profiles
# =============================================================================
# Each profile represents a different user configuration.
# To add a new profile: append to CONFIG_PROFILES.

CONFIG_PROFILES = {
    "neutral": {
        "preferred_release_countries": [],
        "preferred_release_formats": [],
        "release_type_scores": [
            ("Album", 1.0),
            ("Single", 0.5),
            ("EP", 0.7),
            ("Other", 0.3),
        ],
    },
    "prefer_us_cd": {
        "preferred_release_countries": ["US"],
        "preferred_release_formats": ["CD"],
        "release_type_scores": [
            ("Album", 1.0),
            ("Single", 0.5),
            ("EP", 0.7),
            ("Other", 0.3),
        ],
    },
    "prefer_eu_vinyl": {
        "preferred_release_countries": ["XE", "DE", "GB"],
        "preferred_release_formats": ["12\" Vinyl", "Vinyl"],
        "release_type_scores": [
            ("Album", 1.0),
            ("Single", 0.5),
            ("EP", 0.7),
            ("Other", 0.3),
        ],
    },
    "prefer_jp_digital": {
        "preferred_release_countries": ["JP"],
        "preferred_release_formats": ["Digital Media"],
        "release_type_scores": [
            ("Album", 1.0),
            ("Single", 0.5),
            ("EP", 0.7),
            ("Other", 0.3),
        ],
    },
    "compilations_low": {
        "preferred_release_countries": [],
        "preferred_release_formats": [],
        "release_type_scores": [
            ("Album", 1.0),
            ("Single", 0.3),
            ("EP", 0.5),
            ("Compilation", 0.2),
            ("Other", 0.1),
        ],
    },
}


# =============================================================================
# Main
# =============================================================================


def _make_config(profile_name):
    """Create a mock config from a named profile."""
    profile = CONFIG_PROFILES[profile_name]
    settings = defaultdict(lambda: False)
    settings.update(profile)
    mock = MagicMock()
    mock.setting = settings
    return mock


def _run_with_config(profile_name, weights):
    """Generate corpus and evaluate with a specific config profile."""
    mock_config = _make_config(profile_name)
    with (
        patch("picard.config.get_config", return_value=mock_config),
        patch("picard.mbjson.get_config", return_value=mock_config),
        patch("picard.metadata.get_config", return_value=mock_config),
    ):
        corpus = generate_corpus()
        return evaluate(corpus, weights)


def print_comparison(all_results):
    """Print a side-by-side comparison of all config profiles."""
    print(f"\n{'=' * 70}")
    print("  CONFIG COMPARISON")
    print(f"{'=' * 70}")
    print(f"\n  {'Profile':<20} {'Correct':>8} {'Ambiguous':>10} {'Wrong':>8} {'Score':>6}")
    print(f"  {'-' * 20} {'-' * 8} {'-' * 10} {'-' * 8} {'-' * 6}")
    for name, results in all_results.items():
        total = results["correct"] + results["wrong"] + results["ambiguous"]
        # Score: correct=1, ambiguous=0.5, wrong=0
        score = (results["correct"] + 0.5 * results["ambiguous"]) / total
        print(
            f"  {name:<20} {results['correct']:>3}/{total:<3} "
            f"{results['ambiguous']:>4}/{total:<3}  "
            f"{results['wrong']:>3}/{total:<3} "
            f"{score:>5.1%}"
        )

    # Per-scenario comparison across configs
    scenarios = sorted({d["scenario"] for d in next(iter(all_results.values()))["details"]})
    print("\n  Per-scenario correct rate by config:")
    header = f"  {'Scenario':<30}" + "".join(f" {n[:12]:>12}" for n in all_results)
    print(header)
    print(f"  {'-' * 30}" + "".join(f" {'-' * 12}" for _ in all_results))
    for scen in scenarios:
        row = f"  {scen:<30}"
        for results in all_results.values():
            scen_details = [d for d in results["details"] if d["scenario"] == scen]
            n = len(scen_details)
            ok = sum(1 for d in scen_details if d["status"] == "correct")
            row += f" {ok:>3}/{n:<3} {ok / n:>4.0%}" if n else f" {'N/A':>12}"
        print(row)


def main():
    random.seed(42)

    all_results = {}
    for profile_name in CONFIG_PROFILES:
        random.seed(42)  # Reset seed for each profile (consistent degradations)
        results = _run_with_config(profile_name, CLUSTER_COMPARISON_WEIGHTS)
        all_results[profile_name] = results
        print_report(results, f"CLUSTER_COMPARISON_WEIGHTS [{profile_name}]")

    print_comparison(all_results)


if __name__ == "__main__":
    main()
