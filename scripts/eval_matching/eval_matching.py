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

from collections import (
    Counter,
    defaultdict,
)
import json
from pathlib import Path
import random
import re
import sys
from unittest.mock import (
    MagicMock,
    patch,
)

from picard.matching import (
    compare_to_release,
    compare_to_track,
)


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from picard.cluster import CLUSTER_COMPARISON_WEIGHTS
from picard.file import FILE_COMPARISON_WEIGHTS
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
            "eval_release_748e3e26.json",  # 2018 vinyl (same barcode as AU)
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
        "expectations": {
            "*": "correct",  # different barcodes make these distinguishable
            "missing_barcode": "ambiguous",
        },
    },
    {
        "target": "eval_release_4fdf1514.json",  # 椎名林檎 三毒史 CD
        "distractors": [
            "eval_release_3ac4a81e.json",  # 椎名林檎 三毒史 digital
        ],
        "scenario": "non_latin_editions",
        "expectations": {
            "*": "correct",  # different barcodes make these distinguishable
            "missing_barcode": "ambiguous",
        },
    },
    # --- Live vs studio: same artist, different albums ---
    {
        "target": "eval_release_eccae410.json",  # Nirvana Nevermind AU (DGC)
        "distractors": [
            "eval_release_f4469159.json",  # Nirvana MTV Unplugged
            "eval_release_8e061dc4.json",  # Nevermind US (Geffen, different catno)
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
    # --- Remaster vs original: same album, different editions ---
    {
        "target": "eval_release_1a8c4ac3.json",  # Rumours 1984 GB CD (11 tracks)
        "distractors": [
            "eval_release_3c297f7a.json",  # Rumours 2013 XE remaster (11 tracks)
            "eval_release_5c976ee2.json",  # Rumours 2013 US deluxe (40 tracks)
        ],
        "scenario": "remaster_vs_original",
    },
    {
        "target": "eval_release_3c297f7a.json",  # Rumours 2013 XE remaster (11 tracks)
        "distractors": [
            "eval_release_1a8c4ac3.json",  # Rumours 1984 GB CD (11 tracks)
            "eval_release_5c976ee2.json",  # Rumours 2013 US deluxe (40 tracks)
        ],
        "scenario": "remaster_vs_original",
    },
    {
        "target": "eval_release_5c976ee2.json",  # Rumours 2013 US deluxe (40 tracks)
        "distractors": [
            "eval_release_1a8c4ac3.json",  # Rumours 1984 GB CD (11 tracks)
            "eval_release_3c297f7a.json",  # Rumours 2013 XE remaster (11 tracks)
        ],
        "scenario": "remaster_vs_original",
    },
    # --- Same title, different artists (Greatest Hits by various bands) ---
    {
        "target": "eval_release_a9d4cf0c.json",  # Elton John - Greatest Hits 1984
        "distractors": [
            "eval_release_5c62d977.json",  # ABBA - Greatest Hits
            "eval_release_bab57bb1.json",  # Queen - Greatest Hits 1981
        ],
        "scenario": "same_title_different_artist",
    },
    {
        "target": "eval_release_5c62d977.json",  # ABBA - Greatest Hits
        "distractors": [
            "eval_release_a9d4cf0c.json",  # Elton John - Greatest Hits 1984
            "eval_release_bab57bb1.json",  # Queen - Greatest Hits 1981
        ],
        "scenario": "same_title_different_artist",
    },
    {
        "target": "eval_release_bab57bb1.json",  # Queen - Greatest Hits 1981
        "distractors": [
            "eval_release_a9d4cf0c.json",  # Elton John - Greatest Hits 1984
            "eval_release_5c62d977.json",  # ABBA - Greatest Hits
        ],
        "scenario": "same_title_different_artist",
    },
    # --- Multi-disc vs single-disc: same album, different editions ---
    {
        "target": "eval_release_e9b0f69e.json",  # In Rainbows XE CD (10 tracks, 1 disc)
        "distractors": [
            "eval_release_ea92a194.json",  # In Rainbows discbox (28 tracks, 4 media)
            "eval_release_cba282c5.json",  # In Rainbows US CD (10 tracks, 1 disc)
        ],
        "scenario": "multi_disc_vs_single",
    },
    {
        "target": "eval_release_ea92a194.json",  # In Rainbows discbox (28 tracks, 4 media)
        "distractors": [
            "eval_release_e9b0f69e.json",  # In Rainbows XE CD (10 tracks)
            "eval_release_cba282c5.json",  # In Rainbows US CD (10 tracks)
        ],
        "scenario": "multi_disc_vs_single",
    },
    {
        "target": "eval_release_cba282c5.json",  # In Rainbows US CD (10 tracks, 1 disc)
        "distractors": [
            "eval_release_e9b0f69e.json",  # In Rainbows XE CD (10 tracks)
            "eval_release_ea92a194.json",  # In Rainbows discbox (28 tracks)
        ],
        "scenario": "multi_disc_vs_single",
    },
    # --- Self-titled albums: artist name = album name, different artists ---
    {
        "target": "eval_release_2529f558.json",  # Metallica - Metallica (Black Album)
        "distractors": [
            "eval_release_7c07f9a1.json",  # Beyoncé - BEYONCÉ
            "eval_release_3a8a6113.json",  # Weezer - Weezer (Blue Album)
        ],
        "scenario": "self_titled_albums",
    },
    {
        "target": "eval_release_7c07f9a1.json",  # Beyoncé - BEYONCÉ
        "distractors": [
            "eval_release_2529f558.json",  # Metallica - Metallica
            "eval_release_3a8a6113.json",  # Weezer - Weezer (Blue Album)
        ],
        "scenario": "self_titled_albums",
    },
    {
        "target": "eval_release_3a8a6113.json",  # Weezer - Weezer (Blue Album)
        "distractors": [
            "eval_release_2529f558.json",  # Metallica - Metallica
            "eval_release_7c07f9a1.json",  # Beyoncé - BEYONCÉ
        ],
        "scenario": "self_titled_albums",
    },
    # --- Same compilation, different country: identical tracks/recordings, only barcode differs ---
    {
        "target": "eval_release_9764a202.json",  # Black Sabbath - The Dio Years DE (barcode 081227999247)
        "distractors": [
            "eval_release_c5192d47.json",  # Black Sabbath - The Dio Years AU (barcode 9325583042089)
        ],
        "scenario": "same_compilation_different_country",
    },
    {
        "target": "eval_release_c5192d47.json",  # Black Sabbath - The Dio Years AU (barcode 9325583042089)
        "distractors": [
            "eval_release_9764a202.json",  # Black Sabbath - The Dio Years DE (barcode 081227999247)
        ],
        "scenario": "same_compilation_different_country",
    },
    {
        "target": "eval_release_97c0a036.json",  # Explosive Drum & Bass
        "distractors": [],
        "scenario": "similar_track_titles_on_medium",
    },
    # Magazine samplers from different months with same track count
    {
        "target": "eval_release_90b66a30.json",  # Paste Magazine Sampler #48: November 2008
        "distractors": [
            "eval_release_30979257.json",  # Paste Magazine Sampler #41: April 2008
        ],
        "scenario": "similar_samplers",
    },
    {
        "target": "eval_release_30979257.json",  # Paste Magazine Sampler #41: April 2008
        "distractors": [
            "eval_release_90b66a30.json",  # Paste Magazine Sampler #48: November 2008
        ],
        "scenario": "similar_samplers",
    },
    # Re-recording, different track artists (see PICARD-1538)
    {
        "target": "eval_release_3f48d22d.json",  # Vinicius de Moraes - A arca de Noé (1980)
        "distractors": [
            "eval_release_58651b56.json",  # Vinicius de Moraes - A arca de Noé (2013 re-recording)
        ],
        "scenario": "rerecording_different_artists",
    },
    {
        "target": "eval_release_58651b56.json",  # Vinicius de Moraes - A arca de Noé (2013 re-recording)
        "distractors": [
            "eval_release_3f48d22d.json",  # Vinicius de Moraes - A arca de Noé (1980)
        ],
        "scenario": "rerecording_different_artists",
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


def wrong_isrc(metadata, release):
    """Replace ISRC with one from an adjacent track on the same release.

    Simulates a common ripping error where ISRCs shift by one track.
    Falls back to a completely wrong ISRC if no adjacent track has one.
    """
    if "isrc" not in metadata:
        return
    # Find an ISRC from a different track on the same release
    for media in release.get("media", []):
        for track in media.get("tracks", []):
            recording = track.get("recording", {})
            for isrc in recording.get("isrcs", []):
                if isrc != metadata["isrc"]:
                    metadata["isrc"] = isrc
                    return
    # Fallback: completely wrong ISRC
    metadata["isrc"] = "XXYYY0000001"


def less_isrcs(metadata, release):
    isrcs = metadata.getall('isrc')
    if len(isrcs) > 1:
        metadata['isrc'] = isrcs[0:-1]


def missing_most(metadata, release):
    """Strip everything except album and artist (minimal metadata)."""
    keep = {"album", "albumartist"}
    for key in list(metadata.keys()):
        if key not in keep and not key.startswith("~"):
            metadata.pop(key, None)


def length_small_diff(metadata, release):
    """Track duration off by 3 seconds (encoding/padding variance)."""
    if metadata.length > 0:
        metadata.length = metadata.length + 3000


def length_large_diff(metadata, release):
    """Track duration off by 15 seconds (different edit/version)."""
    if metadata.length > 0:
        metadata.length = metadata.length + 15000


def title_remaster_suffix(metadata, release):
    """Track title has '(Remastered)' appended (common in streaming/reissues)."""
    if "title" in metadata:
        metadata["title"] = metadata["title"] + " (Remastered)"


def missing_tracknumber(metadata, release):
    """No track number tag (common in poorly ripped files)."""
    metadata.pop("tracknumber", None)


def wrong_date_year(metadata, release):
    """Date is a reissue year instead of original (off by ~10 years)."""
    if "date" in metadata:
        metadata["date"] = "2003"


def swapped_artist_album(metadata, release):
    """Swap artist and album fields (common ripping/tagging error)."""
    album = metadata.get("album", "")
    artist = metadata.get("albumartist", "")
    if album and artist:
        metadata["album"] = artist
        metadata["albumartist"] = album


def missing_eti(metadata, release):
    """Remove extra title information from album / track titles."""
    re_eti = re.compile(r"\s+\(.*?\)$")
    if "title" in release:
        release["title"] = re_eti.sub("", release["title"])
    for media in release.get("media", []):
        for track in media.get("tracks", []):
            if "title" in track:
                track["title"] = re_eti.sub("", track["title"])
            recording = track.get("recording", {})
            if "title" in recording:
                recording["title"] = re_eti.sub("", recording["title"])


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
    ("wrong_isrc", wrong_isrc),
    ("less_isrcs", less_isrcs),
    ("length_small_diff", length_small_diff),
    ("length_large_diff", length_large_diff),
    ("title_remaster_suffix", title_remaster_suffix),
    ("missing_tracknumber", missing_tracknumber),
    ("wrong_date_year", wrong_date_year),
    ("missing_most", missing_most),
    ("swapped_artist_album", swapped_artist_album),
    ("missing_eti", missing_eti),
    # Combined degradations (realistic multi-issue files)
    ("combo_no_barcode_year_only", lambda m, r: (missing_barcode(m, r), year_only(m, r))),
    ("combo_no_barcode_typo", lambda m, r: (missing_barcode(m, r), typo_album(m, r))),
    ("combo_no_barcode_no_date", lambda m, r: (missing_barcode(m, r), missing_date(m, r))),
    ("combo_remaster_length", lambda m, r: (title_remaster_suffix(m, r), length_small_diff(m, r))),
    ("combo_wrong_date_no_barcode", lambda m, r: (wrong_date_year(m, r), missing_barcode(m, r))),
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
                    "expectations": scenario.get("expectations"),
                }
            )
    return corpus


def _aggregate_file_metadata(file_metadata_list):
    """Simulate Cluster._compute_aggregate_tags on a list of Metadata objects.

    Replicates the cluster aggregation logic: majority threshold,
    single-value consensus, multi-valued intersection.
    """
    from picard.cluster import Cluster

    # Create a minimal cluster with mock files
    cluster = Cluster.__new__(Cluster)
    cluster.files = []
    for m in file_metadata_list:
        mock_file = MagicMock()
        mock_file.metadata = m
        cluster.files.append(mock_file)
    return cluster._compute_aggregate_tags()


def generate_cluster_corpus():
    """Build cluster-level corpus that exercises the aggregation path.

    Simulates the real Picard flow:
      1. Each file in the cluster has per-file metadata (with barcode, etc.)
      2. Degradation is applied to each file's metadata
      3. _compute_aggregate_tags() aggregates across files → cluster metadata
      4. compare_to_release scores against the aggregated metadata

    This tests whether the aggregation + scoring pipeline correctly
    identifies the target release when file metadata is degraded.
    """
    corpus = []
    for scenario in SCENARIOS:
        target = load_release(scenario["target"])
        distractors = [load_release(f) for f in scenario["distractors"]]
        candidates = [target] + distractors

        # Get track count to simulate N files in the cluster
        all_tracks = []
        for media in target.get("media", []):
            all_tracks.extend(media.get("tracks", []))
        if not all_tracks:
            continue

        for deg_name, deg_fn in DEGRADATIONS:
            # Create per-file metadata for each track, then degrade each
            file_metadata_list = []
            for track in all_tracks:
                m = metadata_from_track(track, target)
                deg_fn(m, target)
                file_metadata_list.append(m)

            # Aggregate across files (like Cluster._compute_aggregate_tags)
            aggregated = _aggregate_file_metadata(file_metadata_list)

            # Build cluster-level metadata from first file as base,
            # then override with aggregated values
            cluster_meta = metadata_from_release(target)
            deg_fn(cluster_meta, target)
            for tag, value in aggregated.items():
                cluster_meta[tag] = value
            # Clear tags that didn't survive aggregation
            for tag in ('barcode', 'catalognumber', 'date', 'label'):
                if tag not in aggregated and tag in cluster_meta:
                    del cluster_meta[tag]

            corpus.append(
                {
                    "degradation": deg_name,
                    "scenario": scenario["scenario"],
                    "release_title": target["title"],
                    "metadata": cluster_meta,
                    "correct_id": target["id"],
                    "candidates": candidates,
                    "expectations": scenario.get("expectations"),
                }
            )
    return corpus


def metadata_from_track(track, release):
    """Convert a track + its release to Metadata, simulating a tagged file.

    Populates title, artist, length, plus release-level fields (album, date, etc.).
    """
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


def _build_track_candidates(track, release, distractors):
    """Build track dicts with attached releases for compare_to_track.

    Returns a list of (track_dict, release_id) tuples. Each track_dict
    has a 'releases' key containing the parent release, as expected by
    compare_to_track.
    """
    candidates = []

    # Correct track from target release
    correct_track = dict(track)
    correct_track["releases"] = [release]
    candidates.append((correct_track, release["id"]))

    # Find a matching-position track from each distractor, or use first track
    pos = track.get("position", 1)
    for dist in distractors:
        dist_track = None
        for media in dist.get("media", []):
            for t in media.get("tracks", []):
                if t.get("position") == pos:
                    dist_track = t
                    break
            if dist_track:
                break
        if not dist_track:
            # Fall back to first track
            for media in dist.get("media", []):
                if media.get("tracks"):
                    dist_track = media["tracks"][0]
                    break
        if dist_track:
            dt = dict(dist_track)
            dt["releases"] = [dist]
            candidates.append((dt, dist["id"]))

    return candidates


def generate_file_corpus():
    """Build file-level evaluation corpus.

    For each scenario, picks a track from the target release and tests
    whether compare_to_track correctly identifies it among tracks from
    distractor releases. Tests first and middle tracks.
    """
    corpus = []
    for scenario in SCENARIOS:
        target = load_release(scenario["target"])
        distractors = [load_release(f) for f in scenario["distractors"]]

        # Pick tracks to test: first track and a middle track
        all_tracks = []
        for media in target.get("media", []):
            all_tracks.extend(media.get("tracks", []))
        if not all_tracks:
            continue

        test_tracks = [all_tracks[0]]
        if len(all_tracks) > 2:
            test_tracks.append(all_tracks[len(all_tracks) // 2])

        for track in test_tracks:
            candidates = _build_track_candidates(track, target, distractors)

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
                        "correct_id": target["id"],
                        "candidates": candidates,
                        "expectations": scenario.get("expectations"),
                    }
                )
    return corpus


# =============================================================================
# Evaluation
# =============================================================================


def _get_expected_status(entry, config_profile):
    """Get the expected status for a corpus entry given the config profile.

    Looks up expectations dict on the entry: specific profile key first,
    then "*" wildcard, then defaults to "correct".
    """
    expectations = entry.get("expectations")
    if not expectations:
        return "correct"
    if config_profile in expectations:
        return expectations[config_profile]
    return expectations.get("*", "correct")


def evaluate(corpus, weights, config_profile="neutral"):
    """Score each corpus entry and classify as correct/ambiguous/wrong.

    Returns a dict with counts and per-entry details including all candidate
    scores for diagnostic purposes. When a test case has expectations defined,
    the result is scored against the expected outcome for the given config_profile.
    """
    results = {"correct": 0, "wrong": 0, "ambiguous": 0, "has_scores": True, "details": []}

    for entry in corpus:
        scores = [(compare_to_release(entry["metadata"], c, weights).similarity, c["id"]) for c in entry["candidates"]]
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

        # Check against expected outcome for this config profile
        expected = _get_expected_status(entry, config_profile)
        met_expectation = status == expected
        results[status] += 1

        results["details"].append(
            {
                "release": entry["release_title"],
                "degradation": entry["degradation"],
                "scenario": entry["scenario"],
                "status": status,
                "expected_status": expected,
                "met_expectation": met_expectation,
                "best_sim": best_sim,
                "margin": margin,
                "scores": scores,
                "correct_id": entry["correct_id"],
                "candidates": {c["id"]: c for c in entry["candidates"]},
            }
        )

    return results


def evaluate_file_corpus(corpus, weights, config_profile="neutral"):
    """Score file-level corpus using compare_to_track.

    Each entry has candidates as (track_dict, release_id) tuples.
    compare_to_track returns SimMatchTrack with the best release match.
    """
    results = {"correct": 0, "wrong": 0, "ambiguous": 0, "has_scores": True, "details": []}

    for entry in corpus:
        scores = []
        for track_dict, release_id in entry["candidates"]:
            match = compare_to_track(entry["metadata"], track_dict, weights)
            scores.append((match.similarity, release_id))

        scores.sort(key=lambda x: x[0], reverse=True)
        best_sim, best_id = scores[0]
        margin = best_sim - scores[1][0] if len(scores) > 1 else 0

        tied_ids = {cid for sim, cid in scores if sim == best_sim}
        if len(tied_ids) > 1 and entry["correct_id"] in tied_ids:
            status = "ambiguous"
        elif best_id == entry["correct_id"]:
            status = "correct"
        else:
            status = "wrong"

        expected = _get_expected_status(entry, config_profile)
        met_expectation = status == expected
        results[status] += 1

        results["details"].append(
            {
                "release": entry["release_title"],
                "degradation": entry["degradation"],
                "scenario": entry["scenario"],
                "status": status,
                "expected_status": expected,
                "met_expectation": met_expectation,
                "best_sim": best_sim,
                "margin": margin,
                "scores": scores,
                "correct_id": entry["correct_id"],
            }
        )

    return results


# =============================================================================
# Reporting
# =============================================================================


def _grouped_breakdown(details, group_key, group_names=None):
    """Compute per-group pass/fail counts from detail entries."""
    ok = Counter()
    fail = Counter()
    total = Counter()
    margins = defaultdict(list)

    for d in details:
        g = d[group_key]
        total[g] += 1
        margins[g].append(d["margin"])
        if d.get("met_expectation", d["status"] == "correct"):
            ok[g] += 1
        else:
            fail[g] += 1

    names = group_names or sorted(total.keys())
    return [(n, ok[n], fail[n], total[n], margins[n]) for n in names]


_DIFF_FIELDS = ["barcode", "date", "country", "title", "track-count"]


def _print_field_diff(problem):
    """Print fields that differ between tied candidates."""
    scores = problem["scores"]
    best_sim = scores[0][0]
    tied_ids = [cid for sim, cid in scores if sim == best_sim]
    if len(tied_ids) < 2:
        return
    candidates = problem.get("candidates", {})
    releases = [candidates[cid] for cid in tied_ids if cid in candidates]
    if len(releases) < 2:
        return

    diffs = []
    for field in _DIFF_FIELDS:
        values = set()
        for r in releases:
            if field == "track-count":
                val = sum(m.get("track-count", 0) for m in r.get("media", []))
            else:
                val = r.get(field, "")
            values.add(str(val))
        if len(values) > 1:
            diffs.append(field)

    if diffs:
        print(f"  differs on: {', '.join(diffs)}")
        for cid in tied_ids:
            r = candidates.get(cid, {})
            vals = []
            for f in diffs:
                if f == "track-count":
                    v = sum(m.get("track-count", 0) for m in r.get("media", []))
                else:
                    v = r.get(f, "")
                vals.append(f"{f}={v}")
            print(f"    {cid[:8]}: {', '.join(vals)}")
    else:
        print("  differs on: nothing visible (identical release-level metadata)")


def print_report(results, weights_name, verbose=False):
    """Print a formatted evaluation report to stdout.

    With verbose=True, shows per-candidate scores for failed cases
    so the operator can see exactly why the matcher got confused.
    """
    total = results["correct"] + results["wrong"] + results["ambiguous"]
    met = sum(1 for d in results["details"] if d.get("met_expectation", d["status"] == "correct"))
    unmet = total - met
    print(f"\n{'=' * 70}")
    print(f"  {weights_name}")
    print(f"{'=' * 70}")
    print(f"  Pass:      {met:>3}/{total} ({met / total:.1%})")
    print(f"  Fail:      {unmet:>3}/{total} ({unmet / total:.1%})")
    print(
        f"  (actual breakdown: correct={results['correct']}, ambiguous={results['ambiguous']}, wrong={results['wrong']})"
    )

    # Score distribution (file-level)
    if results.get("has_scores"):
        sims = sorted(d["best_sim"] for d in results["details"])
        n = len(sims)
        mean = sum(sims) / n
        p5 = sims[int(n * 0.05)]
        p25 = sims[int(n * 0.25)]
        p50 = sims[n // 2]
        print(
            f"  Scores: min={sims[0]:.4f}  p5={p5:.4f}  p25={p25:.4f}"
            f"  median={p50:.4f}  mean={mean:.4f}  max={sims[-1]:.4f}"
        )

    # Problems summary (always shown)
    problems = [d for d in results["details"] if not d.get("met_expectation", d["status"] == "correct")]
    if not verbose and problems:
        print(f"\n  {'Release':<25} {'Degradation':<22} {'Status':<9} {'Sim':>6} {'Margin':>6}")
        print(f"  {'-' * 25} {'-' * 22} {'-' * 9} {'-' * 6} {'-' * 6}")
        for p in problems:
            print(
                f"  {p['release'][:25]:<25} {p['degradation']:<22} "
                f"{p['status']:<9} {p['best_sim']:6.4f} {p['margin']:6.4f}"
            )

    # Verbose: show candidate scores for each failure
    if verbose and problems:
        print(f"\n  DETAILED DIAGNOSTICS ({len(problems)} problems)")
        print(f"  {'─' * 66}")
        for p in problems:
            correct_id = p["correct_id"]
            expected = p.get("expected_status", "correct")
            print(f"\n  [{p['status'].upper()}] {p['release']} | {p['scenario']}")
            print(f"  degradation: {p['degradation']}")
            if expected != "correct":
                print(f"  expected: {expected}")
            print("  candidates (▶ = correct, ✗ = picked wrong):")
            for sim, cid in p["scores"]:
                marker = "  "
                if cid == correct_id:
                    marker = "▶ "
                elif cid == p["scores"][0][1] and p["status"] == "wrong":
                    marker = "✗ "
                print(f"    {marker}{sim:.4f}  {cid[:8]}")
            # Show fields that differ between tied candidates
            if p["status"] == "ambiguous" and "candidates" in p:
                _print_field_diff(p)

    # Per-degradation
    deg_names = [name for name, _ in DEGRADATIONS]
    rows = _grouped_breakdown(results["details"], "degradation", deg_names)
    has_scores = results.get("has_scores")
    if has_scores:
        print(f"\n  {'Degradation':<25} {'Pass':>4} {'Fail':>4} {'N':>3} {'Rate':>6} {'AvgMargin':>9} {'AvgSim':>7}")
        print(f"  {'-' * 25} {'-' * 4} {'-' * 4} {'-' * 3} {'-' * 6} {'-' * 9} {'-' * 7}")
    else:
        print(f"\n  {'Degradation':<25} {'Pass':>4} {'Fail':>4} {'N':>3} {'Rate':>6} {'AvgMargin':>9}")
        print(f"  {'-' * 25} {'-' * 4} {'-' * 4} {'-' * 3} {'-' * 6} {'-' * 9}")
    for name, ok, fail, n, margins in rows:
        rate = ok / n if n else 0
        avg_m = sum(margins) / len(margins) if margins else 0
        flag = " ✗" if rate < 1.0 else ""
        if has_scores:
            deg_sims = [d["best_sim"] for d in results["details"] if d["degradation"] == name]
            avg_sim = sum(deg_sims) / len(deg_sims) if deg_sims else 0
            print(f"  {name:<25} {ok:>4} {fail:>4} {n:>3} {rate:>5.0%} {avg_m:>9.4f} {avg_sim:>7.4f}{flag}")
        else:
            print(f"  {name:<25} {ok:>4} {fail:>4} {n:>3} {rate:>5.0%} {avg_m:>9.4f}{flag}")

    # Per-scenario
    rows = _grouped_breakdown(results["details"], "scenario")
    print(f"\n  {'Scenario':<30} {'Pass':>4} {'Fail':>4} {'N':>3} {'Rate':>6}")
    print(f"  {'-' * 30} {'-' * 4} {'-' * 4} {'-' * 3} {'-' * 6}")
    for name, ok, fail, n, _ in rows:
        rate = ok / n if n else 0
        flag = " ✗" if rate < 1.0 else ""
        print(f"  {name:<30} {ok:>4} {fail:>4} {n:>3} {rate:>5.0%}{flag}")


# =============================================================================
# Configuration profiles
# =============================================================================
# Each profile represents a different user configuration.
# To add a new profile: append to CONFIG_PROFILES.

CONFIG_PROFILES = {
    "neutral": {
        "preferred_release_countries": [],
        "preferred_release_formats": [],
        "preferred_release_types": ["Album", "EP"],
        "discouraged_release_types": [],
    },
    "prefer_us_cd": {
        "preferred_release_countries": ["US"],
        "preferred_release_formats": ["CD"],
        "preferred_release_types": ["Album", "EP"],
        "discouraged_release_types": [],
    },
    "prefer_eu_vinyl": {
        "preferred_release_countries": ["XE", "DE", "GB"],
        "preferred_release_formats": ["12\" Vinyl", "Vinyl"],
        "preferred_release_types": ["Album", "EP"],
        "discouraged_release_types": [],
    },
    "prefer_jp_digital": {
        "preferred_release_countries": ["JP"],
        "preferred_release_formats": ["Digital Media"],
        "preferred_release_types": ["Album", "EP"],
        "discouraged_release_types": [],
    },
    "compilations_low": {
        "preferred_release_countries": [],
        "preferred_release_formats": [],
        "preferred_release_types": ["Album", "EP"],
        "discouraged_release_types": ["Compilation"],
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
        patch("picard.matching.get_config", return_value=mock_config),
    ):
        corpus = generate_corpus()
        return evaluate(corpus, weights, config_profile=profile_name)


def _run_cluster_aggregated_with_config(profile_name, weights):
    """Generate cluster-aggregated corpus and evaluate.

    Unlike _run_with_config which feeds metadata directly to scoring,
    this simulates the real flow: per-file metadata → aggregation → scoring.
    """
    mock_config = _make_config(profile_name)
    with (
        patch("picard.config.get_config", return_value=mock_config),
        patch("picard.mbjson.get_config", return_value=mock_config),
        patch("picard.matching.get_config", return_value=mock_config),
    ):
        corpus = generate_cluster_corpus()
        return evaluate(corpus, weights, config_profile=profile_name)


def print_comparison(all_results):
    """Print a side-by-side comparison of all config profiles."""
    print(f"\n{'=' * 70}")
    print("  CONFIG COMPARISON")
    print(f"{'=' * 70}")
    print(f"\n  {'Profile':<20} {'Pass':>8} {'Fail':>8} {'Rate':>6}")
    print(f"  {'-' * 20} {'-' * 8} {'-' * 8} {'-' * 6}")
    for name, results in all_results.items():
        total = results["correct"] + results["wrong"] + results["ambiguous"]
        met = sum(1 for d in results["details"] if d.get("met_expectation", d["status"] == "correct"))
        rate = met / total if total else 0
        print(f"  {name:<20} {met:>3}/{total:<3}  {total - met:>3}/{total:<3} {rate:>5.1%}")

    # Per-scenario comparison across configs
    scenarios = sorted({d["scenario"] for d in next(iter(all_results.values()))["details"]})
    print("\n  Per-scenario pass rate by config:")
    header = f"  {'Scenario':<30}" + "".join(f" {n[:12]:>12}" for n in all_results)
    print(header)
    print(f"  {'-' * 30}" + "".join(f" {'-' * 12}" for _ in all_results))
    for scen in scenarios:
        row = f"  {scen:<30}"
        for results in all_results.values():
            scen_details = [d for d in results["details"] if d["scenario"] == scen]
            n = len(scen_details)
            ok = sum(1 for d in scen_details if d.get("met_expectation", d["status"] == "correct"))
            row += f" {ok:>3}/{n:<3} {ok / n:>4.0%}" if n else f" {'N/A':>12}"
        print(row)


def _filter_results(results, scenario=None, degradation=None):
    """Filter result details by scenario and/or degradation substring."""
    details = results["details"]
    if scenario:
        details = [d for d in details if scenario in d["scenario"]]
    if degradation:
        details = [d for d in details if degradation in d["degradation"]]
    filtered = {
        "correct": sum(1 for d in details if d["status"] == "correct"),
        "ambiguous": sum(1 for d in details if d["status"] == "ambiguous"),
        "wrong": sum(1 for d in details if d["status"] == "wrong"),
        "details": details,
    }
    if results.get("has_scores"):
        filtered["has_scores"] = True
    return filtered


def _snapshot_key(detail):
    """Create a unique key for a result entry."""
    return (detail["scenario"], detail["release"], detail["degradation"], detail.get("correct_id", ""))


def _save_snapshot(results, path):
    """Save a results snapshot for later comparison."""
    snapshot = []
    for d in results["details"]:
        snapshot.append(
            {
                "scenario": d["scenario"],
                "release": d["release"],
                "degradation": d["degradation"],
                "correct_id": d.get("correct_id", ""),
                "status": d["status"],
                "best_sim": round(d["best_sim"], 6),
            }
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"\n  Snapshot saved to {path} ({len(snapshot)} entries)")


def _compare_snapshot(current_results, snapshot_path):
    """Compare current results against a saved snapshot and show changes."""
    with open(snapshot_path, encoding="utf-8") as f:
        data = json.load(f)

    # Support both old (dict with meta) and plain list snapshot formats
    if isinstance(data, dict) and "entries" in data:
        previous = data["entries"]
    else:
        previous = data

    prev_by_key = {(e["scenario"], e["release"], e["degradation"], e.get("correct_id", "")): e for e in previous}
    curr_by_key = {_snapshot_key(d): d for d in current_results["details"]}

    improved = []
    regressed = []
    STATUS_RANK = {"wrong": 0, "ambiguous": 1, "correct": 2}

    for key, curr in curr_by_key.items():
        prev = prev_by_key.get(key)
        if not prev:
            continue
        prev_rank = STATUS_RANK[prev["status"]]
        curr_rank = STATUS_RANK[curr["status"]]
        if curr_rank > prev_rank:
            improved.append((key, prev["status"], curr["status"], prev["best_sim"], curr["best_sim"]))
        elif curr_rank < prev_rank:
            regressed.append((key, prev["status"], curr["status"], prev["best_sim"], curr["best_sim"]))

    prev_correct = sum(1 for e in previous if e["status"] == "correct")
    curr_correct = current_results["correct"]

    # Score distribution comparison
    prev_sims = sorted(e["best_sim"] for e in previous)
    curr_sims = sorted(d["best_sim"] for d in current_results["details"])
    prev_mean = sum(prev_sims) / len(prev_sims) if prev_sims else 0
    curr_mean = sum(curr_sims) / len(curr_sims) if curr_sims else 0

    print(f"\n{'=' * 70}")
    print("  SCORE DELTA")
    print(f"{'=' * 70}")
    print(f"  Previous: {prev_correct}/{len(previous)} correct")
    print(f"  Current:  {curr_correct}/{len(curr_by_key)} correct")
    print(f"  Improved: {len(improved)}  Regressed: {len(regressed)}")
    delta = curr_mean - prev_mean
    sign = "+" if delta >= 0 else ""
    print(f"  Mean score: {prev_mean:.4f} → {curr_mean:.4f} ({sign}{delta:.4f})")

    if improved:
        print(f"\n  IMPROVED ({len(improved)}):")
        for key, prev_s, curr_s, prev_sim, curr_sim in improved:
            _, release, deg, _ = key
            print(f"    {release[:20]:<20} {deg:<22} {prev_s:>9} → {curr_s:<9} ({prev_sim:.4f} → {curr_sim:.4f})")

    if regressed:
        print(f"\n  REGRESSED ({len(regressed)}):")
        for key, prev_s, curr_s, prev_sim, curr_sim in regressed:
            _, release, deg, _ = key
            print(f"    {release[:20]:<20} {deg:<22} {prev_s:>9} → {curr_s:<9} ({prev_sim:.4f} → {curr_sim:.4f})")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate release matching accuracy")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show per-candidate scores for failures")
    parser.add_argument(
        "-l", "--list", action="store_true", help="List available scenarios, degradations, and profiles"
    )
    parser.add_argument(
        "-s",
        "--scenario",
        help="Run only scenarios matching this substring",
    )
    parser.add_argument(
        "-d",
        "--degradation",
        help="Run only degradations matching this substring",
    )
    parser.add_argument(
        "-p",
        "--profile",
        choices=list(CONFIG_PROFILES),
        help="Run only this config profile (default: all)",
    )
    parser.add_argument(
        "--file-only",
        action="store_true",
        help="Run only file-level evaluation",
    )
    parser.add_argument(
        "--cluster-only",
        action="store_true",
        help="Run only cluster-level evaluation",
    )
    parser.add_argument(
        "--cluster-aggregated",
        action="store_true",
        help="Include cluster-aggregated evaluation (tests aggregation + scoring pipeline)",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        help="Save results snapshot to FILE for later comparison",
    )
    parser.add_argument(
        "--compare",
        metavar="FILE",
        help="Compare current results against a previous snapshot",
    )
    args = parser.parse_args()

    if args.list:
        print("Scenarios:")
        for s in sorted({sc["scenario"] for sc in SCENARIOS}):
            print(f"  {s}")
        print("\nDegradations:")
        for name, _ in DEGRADATIONS:
            print(f"  {name}")
        print("\nProfiles:")
        for name in CONFIG_PROFILES:
            print(f"  {name}")
        return

    profiles = [args.profile] if args.profile else list(CONFIG_PROFILES)

    if not args.file_only:
        all_results = {}
        for profile_name in profiles:
            random.seed(42)
            results = _run_with_config(profile_name, CLUSTER_COMPARISON_WEIGHTS)
            results = _filter_results(results, args.scenario, args.degradation)
            all_results[profile_name] = results
            print_report(results, f"CLUSTER_COMPARISON_WEIGHTS [{profile_name}]", verbose=args.verbose)

        if len(profiles) > 1:
            print_comparison(all_results)

        if args.cluster_aggregated:
            for profile_name in profiles:
                random.seed(42)
                agg_results = _run_cluster_aggregated_with_config(profile_name, CLUSTER_COMPARISON_WEIGHTS)
                agg_results = _filter_results(agg_results, args.scenario, args.degradation)
                print_report(agg_results, f"CLUSTER_AGGREGATED [{profile_name}]", verbose=args.verbose)

    if not args.cluster_only:
        random.seed(42)
        file_profile = profiles[0] if args.profile else "neutral"
        mock_config = _make_config(file_profile)
        with (
            patch("picard.config.get_config", return_value=mock_config),
            patch("picard.mbjson.get_config", return_value=mock_config),
            patch("picard.matching.get_config", return_value=mock_config),
        ):
            file_corpus = generate_file_corpus()
            file_results = evaluate_file_corpus(file_corpus, FILE_COMPARISON_WEIGHTS, config_profile=file_profile)
            file_results = _filter_results(file_results, args.scenario, args.degradation)
            print_report(file_results, f"FILE_COMPARISON_WEIGHTS [{file_profile}]", verbose=args.verbose)

    # Save/compare snapshots (uses neutral cluster results)
    if not args.file_only:
        current = all_results.get("neutral", all_results.get(profiles[0]))
    else:
        current = file_results

    if args.save:
        _save_snapshot(current, args.save)

    if args.compare:
        _compare_snapshot(current, args.compare)


if __name__ == "__main__":
    main()
