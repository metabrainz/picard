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
from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import (
    MagicMock,
    patch,
)


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from picard.file import FILE_COMPARISON_WEIGHTS
from picard.matching import (
    SimMatchTrack,
    compare_to_track,
    find_best_match_with_margin,
)
from picard.metadata import Metadata

# Reuse corpus and degradations from the release eval
from eval_matching import (
    CORPUS_DIR,
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
    recording_id = recording.get("id", "")
    result = {
        "id": recording_id,
        "title": track.get("title", ""),
        "length": track.get("length", 0),
        "artist-credit": track.get("artist-credit", recording.get("artist-credit", [])),
        "isrcs": recording.get("isrcs", []),
        "score": 100,
    }

    # On recording search results media has only the track for this recording
    # with track-offset indicating the skipped tracks.
    recording_release = deepcopy(release)
    for medium in recording_release.get("media", []):
        for pos, track in enumerate(medium.get("tracks", [])):
            if track.get("recording", {}).get("id", "") == recording_id:
                medium["track-offset"] = pos
                del track["recording"]
                medium["track"] = [track]
                break
        del medium["tracks"]

    result["releases"] = [recording_release]

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
        m["isrc"] = isrcs
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

        # Build candidate list (simulating MB search results)
        # Use all tracks from the release to test for mismatches with similar tracks
        # on the same release.
        candidates = [_track_to_search_result(track, target) for track in all_tracks]

        for track in test_tracks:
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

            correct_recording_id = track["recording"]["id"]

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
# Synthetic scenarios — loaded from JSON fixtures
# =============================================================================


def _load_synthetic_fixture(filename):
    """Load a synthetic recording scenario fixture from the corpus directory."""
    with open(CORPUS_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _resolve_candidates(fixture):
    """Resolve recording entries into candidate dicts with embedded releases."""
    releases = fixture["releases"]
    candidates = []
    for rec in fixture["recordings"]:
        candidate = dict(rec)
        release_key = candidate.pop("release", None)
        if release_key and release_key in releases:
            candidate["releases"] = [releases[release_key]]
        candidates.append(candidate)
    return candidates


def generate_synthetic_corpus():
    """Build corpus from synthetic JSON fixtures in corpus/eval_recording_*.json."""
    corpus = []
    for path in sorted(CORPUS_DIR.glob("eval_recording_*.json")):
        fixture = _load_synthetic_fixture(path.name)
        candidates = _resolve_candidates(fixture)

        for scenario in fixture["scenarios"]:
            file_data = scenario["file"]
            m = Metadata()
            m["title"] = file_data["title"]
            m["artist"] = file_data["artist"]
            m.length = file_data["length"]
            if "album" in file_data:
                m["album"] = file_data["album"]
            if "date" in file_data:
                m["date"] = file_data["date"]
            for isrc in file_data.get("isrcs", []):
                m.add("isrc", isrc)

            corpus.append(
                {
                    "degradation": "synthetic",
                    "scenario": scenario["name"],
                    "release_title": scenario.get("description", ""),
                    "track_title": file_data["title"],
                    "metadata": m,
                    "correct_id": scenario["correct_id"],
                    "candidates": candidates,
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
        all_matches = [compare_to_track(entry["metadata"], candidate, weights) for candidate in entry["candidates"]]
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
        json.dump(snapshot, f, indent=2, sort_keys=True)
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
    parser.add_argument("-v", "--verbose", action="store_true", help="Show per-candidate scores for failures")
    parser.add_argument("-l", "--list", action="store_true", help="List available scenarios and degradations")
    parser.add_argument("-s", "--scenario", help="Run only scenarios matching this substring")
    parser.add_argument("-d", "--degradation", help="Run only degradations matching this substring")
    parser.add_argument("--min-similarity", type=float, default=0.0, help="Minimum similarity threshold (default: 0.0)")
    parser.add_argument(
        "--min-margin", type=float, default=0.0, help="Minimum margin between best and second (default: 0.0)"
    )
    parser.add_argument("--save", metavar="FILE", help="Save results snapshot to FILE for later comparison")
    parser.add_argument("--compare", metavar="FILE", help="Compare current results against a previous snapshot")
    args = parser.parse_args()

    # Mock config — defaultdict(False) handles any missing key
    mock_config = MagicMock()
    mock_config.setting = defaultdict(lambda: False)
    mock_config.setting.update(
        {
            "preferred_release_types": [],
            "discouraged_release_types": [],
            "preferred_release_countries": [],
            "preferred_release_formats": [],
        }
    )

    with (
        patch("picard.config.get_config", return_value=mock_config),
        patch("picard.mbjson.get_config", return_value=mock_config),
        patch("picard.matching.get_config", return_value=mock_config),
    ):
        corpus = generate_corpus() + generate_synthetic_corpus()

        if args.list:
            scenarios = sorted(set(e["scenario"] for e in corpus))
            degradations = sorted(set(e["degradation"] for e in corpus))
            print("Scenarios:")
            for s in scenarios:
                print(f"  {s}")
            print("\nDegradations:")
            for d in degradations:
                print(f"  {d}")
            sys.exit(0)

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
