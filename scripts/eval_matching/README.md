# Release Matching Evaluation

Measures how accurately Picard's release matcher identifies the correct release
from a set of confusable candidates when file metadata is degraded.

## Quick Start

```bash
# Run full evaluation (all configs, cluster + file level)
python scripts/eval_matching/eval_matching.py

# Focus on a specific problem
python scripts/eval_matching/eval_matching.py -v -s non_latin --cluster-only -p neutral

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
| `-v`, `--verbose` | Show per-candidate scores for each failure |
| `-s`, `--scenario` | Filter to scenarios matching a substring |
| `-p`, `--profile` | Run only one config profile (neutral, prefer_us_cd, etc.) |
| `--cluster-only` | Skip file-level evaluation |
| `--file-only` | Skip cluster-level evaluation |

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
| `missing_most` | Only album + artist remain |
| `swapped_artist_album` | Artist and album fields swapped |

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
- **New config profile**: append to `CONFIG_PROFILES` dict.
