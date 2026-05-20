# Matching Evaluation Tools

Two evaluation harnesses for Picard's matching algorithms:

- **`eval_matching.py`** — Release matching (cluster → release, file → track within a release)
- **`eval_recording_lookup.py`** — Recording lookup (file → best recording from search results)

---

## Release Matching Evaluation

Measures how accurately Picard's release matcher identifies the correct release
from a set of confusable candidates when file metadata is degraded.

## Quick Start

```bash
# Run full evaluation (all configs, cluster + file level)
python scripts/eval_matching/eval_matching.py

# Focus on a specific problem with diagnostics
python scripts/eval_matching/eval_matching.py -v -s non_latin --cluster-only -p neutral

# Filter by degradation pattern
python scripts/eval_matching/eval_matching.py -d combo --cluster-only -p neutral

# Save baseline, make changes, compare
python scripts/eval_matching/eval_matching.py --cluster-only -p neutral --save baseline.json
# ... edit matching code ...
python scripts/eval_matching/eval_matching.py --cluster-only -p neutral --compare baseline.json

# Refresh corpus from MusicBrainz (after API changes)
python scripts/eval_matching/refresh_corpus.py

# Add a new release to the corpus
python scripts/eval_matching/refresh_corpus.py --add <RELEASE_MBID>
```

## How It Works

1. Each **scenario** defines a target release and plausible distractors (wrong
   candidates the matcher might confuse it with).
2. File metadata is generated from the target, then **degraded** (typos, missing
   fields, wrong values) to simulate real-world imperfect tags.
3. The matcher scores all candidates; we check if the target wins, ties, or loses.

Two matching levels are tested:

- **Cluster-level** (`compare_to_release`): uses album, artist, date, barcode,
  track count — what Picard uses when matching a cluster of files to a release.
- **File-level** (`compare_to_track`): adds track title, artist, and duration —
  what Picard uses when matching individual files to tracks.

## CLI Options

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Show per-candidate scores and field diffs for failures |
| `-s`, `--scenario` | Filter to scenarios matching a substring |
| `-d`, `--degradation` | Filter to degradations matching a substring |
| `-p`, `--profile` | Run only one config profile (neutral, prefer_us_cd, etc.) |
| `--cluster-only` | Skip file-level evaluation |
| `--file-only` | Skip cluster-level evaluation |
| `--save FILE` | Save results snapshot for later comparison |
| `--compare FILE` | Compare current results against a previous snapshot |

## Score Delta Workflow

When iterating on the matching algorithm:

```bash
# 1. Save baseline before changes
python scripts/eval_matching/eval_matching.py --cluster-only -p neutral --save baseline.json

# 2. Make changes to picard/metadata.py, picard/cluster.py, etc.

# 3. Compare against baseline
python scripts/eval_matching/eval_matching.py --cluster-only -p neutral --compare baseline.json
```

The delta report shows exactly which cases improved or regressed:

```text
  SCORE DELTA
======================================================================
  Previous: 150/255 correct
  Current:  158/255 correct
  Improved: 10  Regressed: 2

  IMPROVED (10):
    三毒史                 perfect                ambiguous → correct  (1.0000 → 1.0000)
    ...

  REGRESSED (2):
    Weezer               wrong_date_year          correct → wrong    (0.9838 → 0.9200)
```

## Verbose Diagnostics

With `-v`, failures show per-candidate scores and which fields differ between
tied candidates:

```text
  [AMBIGUOUS] MTV Ultimate Mash‐Ups Presents: Collision Course | multi_artist_editions
  degradation: perfect
  candidates (▶ = correct, ✗ = picked wrong):
    ▶ 0.9189  2810aeef
      0.9189  a72497d5
      0.5947  2c5e4198
  differs on: barcode, track-count
    2810aeef: barcode=093624896227, track-count=23
    a72497d5: barcode=093624896326, track-count=13
```

## Scenarios

| Scenario | Challenge |
|----------|-----------|
| `same_title_different_albums` | Weezer Blue vs Green — same title, same artist |
| `same_album_variant_titles` | GY!BE editions with different title spellings |
| `multi_artist_editions` | Collision Course 23-track vs 13-track editions |
| `ep_identification` | Radiohead EP vs unrelated releases |
| `greatest_hits_compilations` | Queen GH 1981 vs 2008 — same title, different content |
| `classical_same_composition` | Beethoven 5th — Karajan vs Szell |
| `non_latin_editions` | 椎名林檎 三毒史 — digital vs CD, identical metadata |
| `live_vs_studio` | Nirvana Nevermind vs MTV Unplugged |

## Degradation Patterns

Each scenario is tested with all degradations applied to the file metadata:

| Degradation | Simulates |
|-------------|-----------|
| `perfect` | No degradation (baseline) |
| `missing_barcode` | File has no barcode tag |
| `missing_date` | File has no date tag |
| `year_only` | Date truncated to year |
| `typo_album` | Single-character typo in album name |
| `wrong_case_album` | Album name lowercased |
| `missing_artist` | No albumartist tag |
| `extra_artist_suffix` | Artist has "feat. Someone" appended |
| `wrong_track_count` | Track count off by one |
| `wrong_barcode` | Barcode present but incorrect |
| `length_small_diff` | Track duration off by 3 seconds |
| `length_large_diff` | Track duration off by 15 seconds |
| `title_remaster_suffix` | Track title has "(Remastered)" appended |
| `missing_tracknumber` | No track number tag |
| `wrong_date_year` | Date is a reissue year (2003) |
| `missing_most` | Only album + artist remain |
| `swapped_artist_album` | Artist and album fields swapped |

### Combined Degradations

Realistic multi-issue patterns (filter with `-d combo`):

| Degradation | Simulates |
|-------------|-----------|
| `combo_no_barcode_year_only` | Missing barcode + year-only date |
| `combo_no_barcode_typo` | Missing barcode + album typo |
| `combo_no_barcode_no_date` | Missing barcode + missing date |
| `combo_remaster_length` | Remaster title suffix + small length diff |
| `combo_wrong_date_no_barcode` | Wrong date year + missing barcode |

## Config Profiles

Matching is evaluated across different user preference configurations:

| Profile | Preferences |
|---------|-------------|
| `neutral` | No country/format preferences |
| `prefer_us_cd` | US + CD |
| `prefer_eu_vinyl` | EU/DE/GB + Vinyl |
| `prefer_jp_digital` | JP + Digital Media |
| `compilations_low` | Low scores for compilations |

## Corpus

### Structure

```text
corpus/
├── releases.tsv            # Registry: MBID<tab>description (source of truth)
└── eval_release_*.json     # Cached MB API responses
```

### Managing the Corpus

The `releases.tsv` file is the single source of truth. JSON fixtures are cached
copies of MB API responses, committed for reproducibility and offline use.

```bash
# Add a new release
python scripts/eval_matching/refresh_corpus.py --add <MBID>
# → fetches from MB, saves JSON, appends to releases.tsv

# Refresh all fixtures (e.g., after API format change)
python scripts/eval_matching/refresh_corpus.py
```

After adding a release, add a scenario entry in `eval_matching.py` → `SCENARIOS`
to include it in the evaluation.

## Extending

- **New scenario**: add release JSONs to corpus (via `refresh_corpus.py --add`),
  then append to `SCENARIOS` in `eval_matching.py`.
- **New degradation**: define a `fn(metadata, release)` function, append to
  `DEGRADATIONS`.
- **New combined degradation**: add a lambda composing existing functions to
  `DEGRADATIONS`.
- **New config profile**: append to `CONFIG_PROFILES` dict.

## Per-Config Expectations

By default, a test case passes when the matcher picks the target release
("correct"). Some scenarios are inherently ambiguous or config-dependent — for
example, two releases identical except for media format. For these, you can
define the expected outcome per config profile:

```python
{
    "target": "eval_release_3ac4a81e.json",  # digital edition
    "distractors": [
        "eval_release_4fdf1514.json",  # CD edition
    ],
    "scenario": "non_latin_editions",
    "expectations": {
        "*": "ambiguous",              # wildcard default
        "prefer_jp_digital": "correct",
        "prefer_us_cd": "wrong",
    },
}
```

Rules:
- If `expectations` is not set, the expected outcome is `"correct"` for all profiles.
- A specific profile key takes priority over the `"*"` wildcard.
- Valid expected values: `"correct"`, `"ambiguous"`, `"wrong"`.
- A test **passes** when the actual outcome matches the expected outcome.

---

## Recording Lookup Evaluation

Measures how accurately Picard's recording matcher identifies the correct
recording from a set of candidates, simulating the file lookup flow
(`compare_to_track` + `find_best_match_with_margin`).

### Quick Start

```bash
# Run full evaluation
python scripts/eval_matching/eval_recording_lookup.py

# Synthetic scenarios only (edge cases)
python scripts/eval_matching/eval_recording_lookup.py -d synthetic

# Verbose output with failure details
python scripts/eval_matching/eval_recording_lookup.py -v

# Filter by scenario name
python scripts/eval_matching/eval_recording_lookup.py -s multi_isrc

# Test with similarity threshold and margin (like real Picard settings)
python scripts/eval_matching/eval_recording_lookup.py --min-similarity 0.5 --min-margin 0.05

# Save baseline, make changes, compare
python scripts/eval_matching/eval_recording_lookup.py --save baseline.json
# ... edit matching code ...
python scripts/eval_matching/eval_recording_lookup.py --compare baseline.json
```

### How It Works

Two types of test cases are combined:

1. **Release-derived cases**: Tracks from the existing release corpus are used as
   candidates (same as `eval_matching.py` file-level tests). All degradation
   patterns are applied.

2. **Synthetic cases**: Hand-crafted JSON fixtures in `corpus/eval_recording_*.json`
   that test specific edge cases not covered by the release corpus.

For each test case:
1. File metadata is built (from a target track or synthetic definition)
2. `compare_to_track()` scores all candidates
3. `find_best_match_with_margin()` picks the winner (or rejects)
4. Result is classified as correct/wrong/ambiguous/below_floor

### CLI Options

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Show per-candidate scores for failures |
| `-s`, `--scenario` | Filter to scenarios matching a substring |
| `-d`, `--degradation` | Filter to degradations matching a substring |
| `--min-similarity` | Minimum similarity threshold (default: 0.0) |
| `--min-margin` | Minimum margin between best and second (default: 0.0) |
| `--save FILE` | Save results snapshot for later comparison |
| `--compare FILE` | Compare current results against a previous snapshot |

### Synthetic Scenario Fixtures

Synthetic scenarios live in `corpus/eval_recording_*.json`. Each file has this
structure:

```json
{
  "description": "Human-readable description of what this fixture tests",
  "releases": {
    "release_key": {
      "id": "release-mbid",
      "title": "Album Title",
      "artist-credit": [{"name": "Artist", "artist": {"id": "...", "name": "Artist", "sort-name": "Artist"}}],
      "date": "2020",
      "country": "US",
      "release-group": {"id": "rg-...", "primary-type": "Album"},
      "media": [{"format": "CD", "track-count": 10}]
    }
  },
  "recordings": [
    {
      "id": "recording-mbid",
      "title": "Track Title",
      "length": 240000,
      "artist-credit": [{"name": "Artist", "artist": {"id": "...", "name": "Artist", "sort-name": "Artist"}}],
      "isrcs": ["ISRC00000001"],
      "release": "release_key",
      "score": 100
    }
  ],
  "scenarios": [
    {
      "name": "scenario_identifier",
      "description": "What this scenario tests",
      "correct_id": "recording-mbid",
      "file": {
        "title": "Track Title",
        "artist": "Artist",
        "length": 240000,
        "album": "Optional album",
        "date": "Optional date",
        "isrcs": ["Optional", "ISRCs"]
      }
    }
  ]
}
```

### Key rules

- `releases` is a dict of release objects keyed by a local reference name.
- Each recording's `"release"` field references a key in `releases`.
- `artist-credit` must include the nested `artist` object with `id`, `name`, and `sort-name`.
- `file.length` is in milliseconds (0 means no duration info).
- `file.isrcs` is optional; omit or use `[]` for no ISRCs.

### Current Fixtures

| Fixture | Scenarios | Tests |
|---------|-----------|-------|
| `eval_recording_multi_isrc.json` | 4 | Multiple ISRCs: full subset, partial overlap, unique, all wrong |
| `eval_recording_same_song.json` | 6 | Studio/live/remaster/cover of same song |
| `eval_recording_zero_length.json` | 2 | Missing duration on file or candidate |
| `eval_recording_unicode.json` | 2 | Non-ASCII titles (kanji), variant album characters |
| `eval_recording_short_tracks.json` | 2 | Very short tracks (15-22s), proportional length diffs |
| `eval_recording_feat_artists.json` | 3 | Featuring/joint artist credits |
| `eval_recording_same_recording.json` | 3 | Same recording on album/compilation/single |
| `eval_recording_extreme_similarity.json` | 1 | Same ISRC/length/title, only release country differs |
| `eval_recording_parenthetical.json` | 4 | Title variants: Radio Edit, Acoustic, Live, missing suffix |

### Adding New Scenarios

1. Create a new `corpus/eval_recording_<name>.json` file following the structure above.
2. Run the eval to verify: `python scripts/eval_matching/eval_recording_lookup.py -d synthetic -v`
3. No Python code changes needed — fixtures are auto-discovered by glob.

### Score Delta Workflow

```bash
# 1. Save baseline
python scripts/eval_matching/eval_recording_lookup.py --save baseline.json

# 2. Edit picard/metadata.py (e.g., fix ISRC scoring)

# 3. Compare
python scripts/eval_matching/eval_recording_lookup.py --compare baseline.json
```

Output shows improved/regressed cases:

```text
  SCORE DELTA
======================================================================
  Previous: 1266/1269 correct
  Current:  1268/1269 correct
  Improved: 2  Regressed: 0

  IMPROVED (2):
    File has 2 ISRCs...          synthetic    wrong → correct
    File ISRCs dont match...     synthetic    wrong → correct
```

### Known Issues Found

The eval has identified a scoring gap in `compare_to_track`:

**When a file has ISRCs but a candidate recording has none**, the ISRC comparison
is skipped entirely for that candidate. This means the no-ISRC candidate gets
scored purely on similarity without any ISRC penalty, while candidates with
partially matching ISRCs get a lower score (0.8) that can drag them below the
no-ISRC candidate.

This affects the `multi_isrc_partial_overlap` and `multi_isrc_all_wrong` scenarios.
