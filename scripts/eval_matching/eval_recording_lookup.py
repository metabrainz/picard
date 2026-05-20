#!/usr/bin/env python3
"""Recording lookup evaluation harness.

Measures how accurately Picard's recording matcher identifies the correct
recording from a set of candidates when file metadata is degraded.

This simulates the recording lookup flow (file → MB search → pick best match)
using the same corpus as the release evaluation. Candidates are built from
tracks across target + distractor releases.

Usage:
    python scripts/eval_matching/eval_recording_lookup.py
    python scripts/eval_matching/eval_recording_lookup.py -v -s same_title
    python scripts/eval_matching/eval_recording_lookup.py -d typo_album
    python scripts/eval_matching/eval_recording_lookup.py --save baseline.json
    python scripts/eval_matching/eval_recording_lookup.py --compare baseline.json
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from unittest.mock import (
    MagicMock,
    patch,
)


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from picard.file import FILE_COMPARISON_WEIGHTS
from picard.metadata import (
    Metadata,
    SimMatchTrack,
)
from picard.util import find_best_match_with_margin

# Reuse corpus and degradations from the release eval
from eval_matching import (
    DEGRADATIONS,
    SCENARIOS,
    load_release,
    metadata_from_release,
)


# =============================================================================
# Corpus generation
# =============================================================================


def _track_to_search_result(track, release):
    """Format a track as a MB recording search result entry.

    Mimics the structure returned by /ws/2/recording?query=...
    """
    recording = track.get("recording", {})
    result = {
        "id": recording.get("id", track.get("id", "")),
        "title": track.get("title", ""),
        "length": track.get("length", 0),
        "artist-credit": track.get("artist-credit", recording.get("artist-credit", [])),
        "releases": [release],
        "isrcs": recording.get("isrcs", []),
        "score": 100,
    }
    if "video" in track:
        result["video"] = track["video"]
    return result


def metadata_from_track(track, release):
    """Build file metadata from a track + release, simulating a tagged file."""
    m = metadata_from_release(release)
    m["title"] = track["title"]
    if "artist-credit" in track:
        ac = track["artist-credit"]
        m["artist"] = "".join(c.get("name", "") + c.get("joinphrase", "") for c in ac)
    m.length = track.get("length", 0) or 0
    m["tracknumber"] = track.get("number", "1")
    recording = track.get("recording", {})
    isrcs = recording.get("isrcs", [])
    if isrcs:
        for isrc in isrcs:
            m.add("isrc", isrc)
    return m


def generate_corpus():
    """Build recording lookup evaluation corpus.

    For each scenario, picks tracks from the target release and builds
    candidate lists from matching-position tracks across all releases.
    Tests whether compare_to_track + find_best_match_with_margin picks
    the correct recording.
    """
    corpus = []
    for scenario in SCENARIOS:
        target = load_release(scenario["target"])
        distractors = [load_release(f) for f in scenario["distractors"]]

        # Collect tracks to test: first and middle
        all_tracks = []
        for media in target.get("media", []):
            all_tracks.extend(media.get("tracks", []))
        if not all_tracks:
            continue

        test_tracks = [all_tracks[0]]
        if len(all_tracks) > 2:
            test_tracks.append(all_tracks[len(all_tracks) // 2])

        for track in test_tracks:
            # Build candidate list (simulating MB search results)
            candidates = [_track_to_search_result(track, target)]
            pos = track.get("position", 1)

            for dist in distractors:
                for media in dist.get("media", []):
                    for t in media.get("tracks", []):
                        if t.get("position") == pos:
                            candidates.append(_track_to_search_result(t, dist))
                            break
                    else:
                        continue
                    break
                else:
                    # Fall back to first track
                    for media in dist.get("media", []):
                        if media.get("tracks"):
                            candidates.append(_track_to_search_result(media["tracks"][0], dist))
                            break

            correct_recording_id = candidates[0]["id"]

            for deg_name, deg_fn in DEGRADATIONS:
                m = metadata_from_track(track, target)
                deg_fn(m, target)
                corpus.append(
                    {
                        "degradation": deg_name,
                        "scenario": scenario["scenario"],
                        "release_title": target["title"],
                        "track_title": track["title"],
                        "metadata": m,
                        "correct_id": correct_recording_id,
                        "candidates": candidates,
                        "expectations": scenario.get("expectations"),
                    }
                )
    return corpus


# =============================================================================
# Synthetic scenarios — edge cases not covered by the release corpus
# =============================================================================

# Helpers to build synthetic candidates


def _make_candidate(recording_id, title, artist, length, isrcs=None, release=None):
    """Build a synthetic recording search result."""
    candidate = {
        "id": recording_id,
        "title": title,
        "length": length,
        "artist-credit": [
            {"name": artist, "artist": {"id": "artist-" + recording_id, "name": artist, "sort-name": artist}}
        ],
        "isrcs": isrcs or [],
        "score": 100,
    }
    if release:
        candidate["releases"] = [release]
    return candidate


def _make_release(release_id, title, artist, date="2020", country="US"):
    """Build a minimal synthetic release."""
    return {
        "id": release_id,
        "title": title,
        "artist-credit": [
            {"name": artist, "artist": {"id": "artist-" + release_id, "name": artist, "sort-name": artist}}
        ],
        "date": date,
        "country": country,
        "release-group": {"id": "rg-" + release_id, "primary-type": "Album"},
        "media": [{"format": "CD", "track-count": 10}],
    }


def _make_file_metadata(title, artist, length, isrcs=None, album="", date=""):
    """Build synthetic file metadata."""
    m = Metadata()
    m["title"] = title
    m["artist"] = artist
    m.length = length
    if album:
        m["album"] = album
    if date:
        m["date"] = date
    if isrcs:
        for isrc in isrcs:
            m.add("isrc", isrc)
    return m


SYNTHETIC_SCENARIOS = []


def _build_multi_isrc_scenarios():
    """Test cases for files with multiple ISRCs."""
    release_a = _make_release("aaaa-1111", "Album A", "Artist X", "2020")
    release_b = _make_release("bbbb-2222", "Album B", "Artist X", "2021")

    # Correct recording has ISRC1 + ISRC2
    correct = _make_candidate(
        "rec-correct-1",
        "My Song",
        "Artist X",
        240000,
        isrcs=["ISRC00000001", "ISRC00000002"],
        release=release_a,
    )
    # Distractor shares ISRC1 only (different recording of same song)
    partial_match = _make_candidate(
        "rec-partial-1",
        "My Song",
        "Artist X",
        242000,
        isrcs=["ISRC00000001", "ISRC00000099"],
        release=release_b,
    )
    # Distractor has no matching ISRCs
    no_match = _make_candidate(
        "rec-nomatch-1",
        "My Song",
        "Artist X",
        238000,
        isrcs=["ISRC00000088"],
        release=release_b,
    )
    # Distractor has no ISRCs at all
    no_isrc = _make_candidate(
        "rec-noisrc-1",
        "My Song",
        "Artist X",
        241000,
        isrcs=[],
        release=release_b,
    )

    candidates = [correct, partial_match, no_match, no_isrc]

    # File has both ISRCs → should pick correct (subset match = 1.0)
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "multi_isrc_full_subset",
            "description": "File has 2 ISRCs, both match correct recording",
            "metadata": _make_file_metadata(
                "My Song",
                "Artist X",
                240000,
                isrcs=["ISRC00000001", "ISRC00000002"],
            ),
            "correct_id": "rec-correct-1",
            "candidates": candidates,
        }
    )

    # File has 1 matching + 1 non-matching ISRC → partial (0.8)
    # Should still beat the no-match candidates
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "multi_isrc_partial_overlap",
            "description": "File has 2 ISRCs, only 1 matches correct recording",
            "metadata": _make_file_metadata(
                "My Song",
                "Artist X",
                240000,
                isrcs=["ISRC00000001", "ISRC00000777"],
            ),
            "correct_id": "rec-correct-1",
            "candidates": candidates,
        }
    )

    # File has only ISRC2 (not shared with partial_match) → subset of correct
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "multi_isrc_unique_isrc",
            "description": "File has 1 ISRC that only the correct recording has",
            "metadata": _make_file_metadata(
                "My Song",
                "Artist X",
                240000,
                isrcs=["ISRC00000002"],
            ),
            "correct_id": "rec-correct-1",
            "candidates": candidates,
        }
    )

    # File has wrong ISRC entirely but good metadata → should still match on similarity
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "multi_isrc_all_wrong",
            "description": "File ISRCs don't match any candidate, rely on similarity",
            "metadata": _make_file_metadata(
                "My Song",
                "Artist X",
                240000,
                isrcs=["ISRC00000999"],
            ),
            "correct_id": "rec-correct-1",
            "candidates": candidates,
        }
    )


def _build_same_song_different_recording_scenarios():
    """Test cases where candidates are different recordings of the same song."""
    release_studio = _make_release("rel-studio", "Greatest Hits", "The Band", "2005")
    release_live = _make_release("rel-live", "Live at Wembley", "The Band", "2008")
    release_remaster = _make_release("rel-remaster", "Greatest Hits (Remastered)", "The Band", "2015")
    release_cover = _make_release("rel-cover", "Tribute Album", "Cover Band", "2019")

    # Studio version (original)
    studio = _make_candidate(
        "rec-studio",
        "Bohemian Rhapsody",
        "The Band",
        354000,
        isrcs=["GBISRC0000001"],
        release=release_studio,
    )
    # Live version (longer, same artist)
    live = _make_candidate(
        "rec-live",
        "Bohemian Rhapsody",
        "The Band",
        412000,
        isrcs=["GBISRC0000002"],
        release=release_live,
    )
    # Remaster (same length, different ISRC)
    remaster = _make_candidate(
        "rec-remaster",
        "Bohemian Rhapsody",
        "The Band",
        355000,
        isrcs=["GBISRC0000003"],
        release=release_remaster,
    )
    # Cover by different artist
    cover = _make_candidate(
        "rec-cover",
        "Bohemian Rhapsody",
        "Cover Band",
        348000,
        isrcs=["GBISRC0000004"],
        release=release_cover,
    )

    candidates = [studio, live, remaster, cover]

    # File tagged from studio version with correct ISRC
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "same_song_studio_with_isrc",
            "description": "Studio recording, correct ISRC, multiple similar candidates",
            "metadata": _make_file_metadata(
                "Bohemian Rhapsody",
                "The Band",
                354000,
                isrcs=["GBISRC0000001"],
            ),
            "correct_id": "rec-studio",
            "candidates": candidates,
        }
    )

    # File tagged from studio but no ISRC — must rely on length + release info
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "same_song_studio_no_isrc",
            "description": "Studio recording, no ISRC, similar lengths among candidates",
            "metadata": _make_file_metadata(
                "Bohemian Rhapsody",
                "The Band",
                354000,
                album="Greatest Hits",
                date="2005",
            ),
            "correct_id": "rec-studio",
            "candidates": candidates,
        }
    )

    # File from live version — longer duration should distinguish
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "same_song_live_by_length",
            "description": "Live recording, no ISRC, distinguished by longer duration",
            "metadata": _make_file_metadata(
                "Bohemian Rhapsody",
                "The Band",
                412000,
                album="Live at Wembley",
                date="2008",
            ),
            "correct_id": "rec-live",
            "candidates": candidates,
        }
    )

    # File from remaster — nearly same length as studio, different ISRC
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "same_song_remaster_with_isrc",
            "description": "Remaster, correct ISRC distinguishes from studio",
            "metadata": _make_file_metadata(
                "Bohemian Rhapsody",
                "The Band",
                355000,
                isrcs=["GBISRC0000003"],
            ),
            "correct_id": "rec-remaster",
            "candidates": candidates,
        }
    )

    # File from remaster — no ISRC, nearly same length as studio
    # This is inherently ambiguous without release info
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "same_song_remaster_no_isrc",
            "description": "Remaster, no ISRC, nearly same length as studio — needs release info",
            "metadata": _make_file_metadata(
                "Bohemian Rhapsody",
                "The Band",
                355000,
                album="Greatest Hits (Remastered)",
                date="2015",
            ),
            "correct_id": "rec-remaster",
            "candidates": candidates,
        }
    )

    # Cover version — different artist should make it easy
    SYNTHETIC_SCENARIOS.append(
        {
            "name": "same_song_cover_different_artist",
            "description": "Cover by different artist, easy to distinguish",
            "metadata": _make_file_metadata(
                "Bohemian Rhapsody",
                "Cover Band",
                348000,
                album="Tribute Album",
            ),
            "correct_id": "rec-cover",
            "candidates": candidates,
        }
    )


# Build all synthetic scenarios
_build_multi_isrc_scenarios()
_build_same_song_different_recording_scenarios()


def generate_synthetic_corpus():
    """Build corpus from synthetic scenarios (no degradations applied)."""
    corpus = []
    for scenario in SYNTHETIC_SCENARIOS:
        corpus.append(
            {
                "degradation": "synthetic",
                "scenario": scenario["name"],
                "release_title": scenario.get("description", ""),
                "track_title": scenario["metadata"].get("title", ""),
                "metadata": scenario["metadata"],
                "correct_id": scenario["correct_id"],
                "candidates": scenario["candidates"],
                "expectations": None,
            }
        )
    return corpus


# =============================================================================
# Evaluation
# =============================================================================


def evaluate(corpus, weights, min_similarity=0.0, min_margin=0.0, config_profile="neutral"):
    """Score each corpus entry using compare_to_track + find_best_match_with_margin.

    Mirrors the _match_to_track logic in picard/file.py.
    """
    results = {"correct": 0, "wrong": 0, "ambiguous": 0, "below_floor": 0, "details": []}

    for entry in corpus:
        all_matches = [entry["metadata"].compare_to_track(candidate, weights) for candidate in entry["candidates"]]
        all_matches.sort(key=lambda m: m.similarity, reverse=True)

        no_match = SimMatchTrack(similarity=-1, releasegroup=None, release=None, track=None)
        best_match = find_best_match_with_margin(
            iter(all_matches),
            no_match,
            min_similarity=min_similarity,
            min_margin=min_margin,
        )

        if best_match.result is no_match:
            status = "below_floor"
        else:
            matched_id = best_match.result.track.get("id", "")
            # The track id in search results is the recording id
            if matched_id == entry["correct_id"]:
                if best_match.reason == "ambiguous":
                    status = "ambiguous"
                else:
                    status = "correct"
            else:
                status = "wrong"

        results[status] += 1
        scores = [(m.similarity, m.track.get("id", "")) for m in all_matches]

        results["details"].append(
            {
                "release": entry["release_title"],
                "track": entry.get("track_title", ""),
                "degradation": entry["degradation"],
                "scenario": entry["scenario"],
                "status": status,
                "best_sim": best_match.similarity,
                "margin": scores[0][0] - scores[1][0] if len(scores) > 1 else 0,
                "scores": scores,
                "correct_id": entry["correct_id"],
            }
        )

    return results


# =============================================================================
# Reporting
# =============================================================================


def print_summary(results, label=""):
    total = sum(results[k] for k in ("correct", "wrong", "ambiguous", "below_floor"))
    correct = results["correct"]
    print(f"\n{'=' * 70}")
    if label:
        print(f"  {label}")
        print(f"{'=' * 70}")
    print(
        f"  Total: {total}  Correct: {correct}  Wrong: {results['wrong']}  "
        f"Ambiguous: {results['ambiguous']}  Below floor: {results['below_floor']}"
    )
    if total:
        print(f"  Accuracy: {correct / total:.1%}")
    print(f"{'=' * 70}")


def print_failures(results, verbose=False):
    failures = [d for d in results["details"] if d["status"] != "correct"]
    if not failures:
        return
    print(f"\n  FAILURES ({len(failures)}):")
    for f in failures:
        print(f"    [{f['status'].upper():11}] {f['release']:<40} | {f['track']}")
        print(f"               degradation: {f['degradation']}")
        if verbose:
            print(f"               scores: {f['scores'][:5]}")
            print(f"               correct_id: {f['correct_id']}")
        print()


def save_results(results, path):
    snapshot = []
    for d in results["details"]:
        snapshot.append(
            {
                "release": d["release"],
                "track": d["track"],
                "degradation": d["degradation"],
                "scenario": d["scenario"],
                "status": d["status"],
                "best_sim": d["best_sim"],
            }
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Saved {len(snapshot)} results to {path}")


def compare_results(results, compare_path):
    with open(compare_path, encoding="utf-8") as f:
        previous = json.load(f)

    prev_map = {}
    for entry in previous:
        key = (entry["release"], entry["track"], entry["degradation"])
        prev_map[key] = entry

    improved = []
    regressed = []
    for d in results["details"]:
        key = (d["release"], d["track"], d["degradation"])
        prev = prev_map.get(key)
        if not prev:
            continue
        if prev["status"] != "correct" and d["status"] == "correct":
            improved.append((d, prev))
        elif prev["status"] == "correct" and d["status"] != "correct":
            regressed.append((d, prev))

    prev_correct = sum(1 for e in previous if e["status"] == "correct")
    curr_correct = results["correct"]

    print("\n  SCORE DELTA")
    print(f"{'=' * 70}")
    print(f"  Previous: {prev_correct}/{len(previous)} correct")
    print(f"  Current:  {curr_correct}/{len(results['details'])} correct")
    print(f"  Improved: {len(improved)}  Regressed: {len(regressed)}")

    if improved:
        print(f"\n  IMPROVED ({len(improved)}):")
        for curr, prev in improved[:20]:
            print(f"    {curr['release']:<30} {curr['degradation']:<25} {prev['status']} → {curr['status']}")

    if regressed:
        print(f"\n  REGRESSED ({len(regressed)}):")
        for curr, prev in regressed[:20]:
            print(f"    {curr['release']:<30} {curr['degradation']:<25} {prev['status']} → {curr['status']}")


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show failure details")
    parser.add_argument("-s", "--scenario", help="Filter scenarios by substring")
    parser.add_argument("-d", "--degradation", help="Filter degradations by substring")
    parser.add_argument("--min-similarity", type=float, default=0.0, help="Minimum similarity threshold (default: 0.0)")
    parser.add_argument(
        "--min-margin", type=float, default=0.0, help="Minimum margin between best and second (default: 0.0)"
    )
    parser.add_argument("--save", metavar="FILE", help="Save results snapshot")
    parser.add_argument("--compare", metavar="FILE", help="Compare against previous snapshot")
    args = parser.parse_args()

    # Mock config — defaultdict(False) handles any missing key
    mock_config = MagicMock()
    mock_config.setting = defaultdict(lambda: False)
    mock_config.setting.update(
        {
            "release_type_scores": [],
            "preferred_release_countries": [],
            "preferred_release_formats": [],
        }
    )

    with (
        patch("picard.config.get_config", return_value=mock_config),
        patch("picard.mbjson.get_config", return_value=mock_config),
        patch("picard.metadata.get_config", return_value=mock_config),
    ):
        corpus = generate_corpus() + generate_synthetic_corpus()

        # Apply filters
        if args.scenario:
            corpus = [e for e in corpus if args.scenario in e["scenario"]]
        if args.degradation:
            corpus = [e for e in corpus if args.degradation in e["degradation"]]

        if not corpus:
            print("No test cases match the filters.", file=sys.stderr)
            sys.exit(1)

        results = evaluate(
            corpus,
            FILE_COMPARISON_WEIGHTS,
            min_similarity=args.min_similarity,
            min_margin=args.min_margin,
        )

    print_summary(results, label="Recording Lookup Evaluation")
    print_failures(results, verbose=args.verbose)

    if args.save:
        save_results(results, args.save)
    if args.compare:
        compare_results(results, args.compare)


if __name__ == "__main__":
    main()
