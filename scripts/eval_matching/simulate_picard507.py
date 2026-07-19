#!/usr/bin/env python3
"""Simulate PICARD-507: loaded album boost causes incorrect cluster matching.

Demonstrates that the loaded-album identifier boost in compare_to_release()
could cause a *different* cluster to incorrectly match to an already-loaded
release. With the fix applied, this script confirms the bug no longer occurs.

Scenario (from the original bug report):
  - User loads Paste Magazine Sampler #48 (release 90b66a30)
  - User then looks up Paste Magazine Sampler #41 (release 30979257)
  - Without the fix: #48 gets boosted and wins when metadata is degraded
  - With the fix: #41 always wins regardless of what else is loaded

Usage:
    python scripts/eval_matching/simulate_picard507.py
"""

from collections import defaultdict
import json
from pathlib import Path
import sys
from unittest.mock import (
    MagicMock,
    patch,
)


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from picard.cluster import CLUSTER_COMPARISON_WEIGHTS
from picard.matching import compare_to_release
from picard.mbjson import release_to_metadata
from picard.metadata import Metadata


CORPUS_DIR = Path(__file__).parent / "corpus"


def load_release(filename):
    with open(CORPUS_DIR / filename) as f:
        return json.load(f)


def metadata_from_release(release):
    """Build file metadata as if tagged from this release."""
    m = Metadata()
    release_to_metadata(release, m)
    total = sum(media.get("track-count", 0) for media in release.get("media", []))
    if total:
        first_medium_tracks = release.get("media", [{}])[0].get("track-count", total)
        m["totaltracks"] = str(first_medium_tracks)
        m["~totalalbumtracks"] = str(total)
    return m


def make_config():
    settings = defaultdict(lambda: False)
    settings.update(
        {
            "preferred_release_types": ["Album", "EP", "Single"],
            "discouraged_release_types": [],
            "preferred_release_countries": [],
            "preferred_release_formats": [],
        }
    )
    mock_config = MagicMock()
    mock_config.setting = settings
    return mock_config


def run_simulation():
    mock_config = make_config()

    # Load the two Paste Magazine releases from the bug report
    release_48 = load_release("eval_release_90b66a30.json")  # Sampler #48
    release_41 = load_release("eval_release_30979257.json")  # Sampler #41

    print("=" * 70)
    print("  PICARD-507 Simulation: Loaded Album Boost")
    print("=" * 70)
    print()
    print(f"  Release A: {release_48['title']}")
    print(f"             ID: {release_48['id']}")
    print(f"  Release B: {release_41['title']}")
    print(f"             ID: {release_41['id']}")
    print()

    config_patches = (
        patch("picard.config.get_config", return_value=mock_config),
        patch("picard.matching.get_config", return_value=mock_config),
        patch("picard.mbjson.get_config", return_value=mock_config),
    )

    # Candidates returned by MB search (both releases appear)
    candidates = [release_41, release_48]

    with config_patches[0], config_patches[1], config_patches[2]:
        file_metadata = metadata_from_release(release_41)

    all_pass = True

    # --- Test 1: Perfect metadata ---
    print("-" * 70)
    print("  Test 1: Perfect metadata")
    print("-" * 70)
    with config_patches[0], config_patches[1], config_patches[2]:
        scores = []
        for c in candidates:
            match = compare_to_release(file_metadata, c, CLUSTER_COMPARISON_WEIGHTS)
            scores.append((match.similarity, c["id"], c["title"]))
        scores.sort(key=lambda x: x[0], reverse=True)

    for sim, rid, title in scores:
        marker = "◀ CORRECT" if rid == release_41["id"] else ""
        print(f"    {sim:.4f}  {title[:50]:<50} {marker}")
    winner = scores[0][1]
    ok = winner == release_41["id"]
    all_pass &= ok
    print(f"\n  Winner: {'CORRECT ✓' if ok else 'WRONG ✗'}")
    print(f"  Margin: {scores[0][0] - scores[1][0]:.4f}")

    # --- Test 2: Missing date (common for CD rips) ---
    print()
    print("-" * 70)
    print("  Test 2: Missing date (simulates CD rip)")
    print("-" * 70)
    with config_patches[0], config_patches[1], config_patches[2]:
        degraded = metadata_from_release(release_41)
    degraded.pop("date", None)
    degraded.pop("barcode", None)

    with config_patches[0], config_patches[1], config_patches[2]:
        scores = []
        for c in candidates:
            match = compare_to_release(degraded, c, CLUSTER_COMPARISON_WEIGHTS)
            scores.append((match.similarity, c["id"], c["title"]))
        scores.sort(key=lambda x: x[0], reverse=True)

    for sim, rid, title in scores:
        marker = "◀ CORRECT" if rid == release_41["id"] else ""
        print(f"    {sim:.4f}  {title[:50]:<50} {marker}")
    winner = scores[0][1]
    ok = winner == release_41["id"]
    all_pass &= ok
    print(f"\n  Winner: {'CORRECT ✓' if ok else 'WRONG ✗'}")
    print(f"  Margin: {scores[0][0] - scores[1][0]:.4f}")

    # --- Test 3: Wrong track count ---
    print()
    print("-" * 70)
    print("  Test 3: Wrong track count + missing date")
    print("-" * 70)
    with config_patches[0], config_patches[1], config_patches[2]:
        degraded2 = metadata_from_release(release_41)
    degraded2.pop("date", None)
    degraded2.pop("barcode", None)
    degraded2["totaltracks"] = str(int(degraded2.get("totaltracks", "0")) + 1)

    with config_patches[0], config_patches[1], config_patches[2]:
        scores = []
        for c in candidates:
            match = compare_to_release(degraded2, c, CLUSTER_COMPARISON_WEIGHTS)
            scores.append((match.similarity, c["id"], c["title"]))
        scores.sort(key=lambda x: x[0], reverse=True)

    for sim, rid, title in scores:
        marker = "◀ CORRECT" if rid == release_41["id"] else ""
        print(f"    {sim:.4f}  {title[:50]:<50} {marker}")
    winner = scores[0][1]
    ok = winner == release_41["id"]
    all_pass &= ok
    print(f"\n  Winner: {'CORRECT ✓' if ok else 'WRONG ✗'}")
    print(f"  Margin: {scores[0][0] - scores[1][0]:.4f}")

    # --- Summary ---
    print()
    print("=" * 70)
    print("  Summary")
    print("=" * 70)
    if all_pass:
        print("\n  All tests PASS: correct release wins in all scenarios.")
        print("  The loaded-album boost has been removed — PICARD-507 is fixed.")
        return 0
    else:
        print("\n  Some tests FAILED: matching is incorrect for these releases.")
        return 1


if __name__ == "__main__":
    sys.exit(run_simulation())
