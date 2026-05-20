# Writing Synthetic Recording Scenarios

This guide walks through creating a synthetic scenario fixture from scratch
for `eval_recording_lookup.py`.

## When to Write a Synthetic Scenario

Write one when you want to test a specific matching edge case that isn't
covered by the real release corpus — for example:

- A bug report where Picard picks the wrong recording
- A new feature (like multi-ISRC support) that needs targeted validation
- An ambiguous situation you want to document and track

## Thinking About the Scenario

Before writing JSON, answer these questions:

1. **What is the correct recording?** (the one the file was ripped from)
2. **What makes it hard?** (similar candidates that could confuse the matcher)
3. **What signal should distinguish it?** (ISRC, length, title, artist, release info)

### Example: "Radio Edit vs Album Version"

A common real-world problem: a file tagged as "Love Song" could match either
the 4-minute album version or the 3.5-minute radio edit. The length difference
should be the distinguishing signal.

## File Structure

Each fixture is a JSON file in `scripts/eval_matching/corpus/` named
`eval_recording_<descriptive_name>.json`.

```text
scripts/eval_matching/corpus/eval_recording_radio_edit.json
```

The file has three sections:

```json
{
  "description": "...",
  "releases": { ... },
  "recordings": [ ... ],
  "scenarios": [ ... ]
}
```

## Step-by-Step Example

### Step 1: Define the releases

Releases provide context for the matcher (album title, date, country, format).
Give each a short key name for reference.

```json
"releases": {
  "album": {
    "id": "rel-album-001",
    "title": "First Album",
    "artist-credit": [
      {
        "name": "The Artist",
        "artist": {
          "id": "artist-001",
          "name": "The Artist",
          "sort-name": "Artist, The"
        }
      }
    ],
    "date": "2020-03-15",
    "country": "US",
    "release-group": {"id": "rg-album-001", "primary-type": "Album"},
    "media": [{"format": "CD", "track-count": 12}]
  },
  "single": {
    "id": "rel-single-001",
    "title": "Love Song",
    "artist-credit": [
      {
        "name": "The Artist",
        "artist": {
          "id": "artist-001",
          "name": "The Artist",
          "sort-name": "Artist, The"
        }
      }
    ],
    "date": "2020-01-10",
    "country": "US",
    "release-group": {"id": "rg-single-001", "primary-type": "Single"},
    "media": [{"format": "CD", "track-count": 3}]
  }
}
```

### Step 2: Define the recordings (candidates)

These are the recordings the matcher will choose between. Each references
a release by its key name.

```json
"recordings": [
  {
    "id": "rec-album-version",
    "title": "Love Song",
    "length": 243000,
    "artist-credit": [
      {
        "name": "The Artist",
        "artist": {
          "id": "artist-001",
          "name": "The Artist",
          "sort-name": "Artist, The"
        }
      }
    ],
    "isrcs": ["USRC10000001"],
    "release": "album",
    "score": 100
  },
  {
    "id": "rec-radio-edit",
    "title": "Love Song (Radio Edit)",
    "length": 211000,
    "artist-credit": [
      {
        "name": "The Artist",
        "artist": {
          "id": "artist-001",
          "name": "The Artist",
          "sort-name": "Artist, The"
        }
      }
    ],
    "isrcs": ["USRC10000002"],
    "release": "single",
    "score": 100
  }
]
```

### Step 3: Define the scenarios (test cases)

Each scenario describes a file's metadata and which recording it should match.

```json
"scenarios": [
  {
    "name": "radio_edit_by_title_and_length",
    "description": "File tagged as Radio Edit with matching short length",
    "correct_id": "rec-radio-edit",
    "file": {
      "title": "Love Song (Radio Edit)",
      "artist": "The Artist",
      "length": 211000
    }
  },
  {
    "name": "album_version_by_length",
    "description": "File title is plain 'Love Song', length matches album version",
    "correct_id": "rec-album-version",
    "file": {
      "title": "Love Song",
      "artist": "The Artist",
      "length": 243000,
      "album": "First Album"
    }
  }
]
```

### Step 4: Run and verify

```bash
# Run only your new scenarios
python scripts/eval_matching/eval_recording_lookup.py -s radio_edit -v

# Run all synthetic scenarios
python scripts/eval_matching/eval_recording_lookup.py -d synthetic -v
```

If a scenario fails, the verbose output shows all candidate scores:

```text
  FAILURES (1):
    [WRONG      ] File title is plain 'Love Song'... | Love Song
               degradation: synthetic
               scores: [(0.9182, 'rec-radio-edit'), (0.8834, 'rec-album-version')]
               correct_id: rec-album-version
```

## Field Reference

### Release fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Release MBID (use real or fake) |
| `title` | string | yes | Release title |
| `artist-credit` | array | yes | See artist-credit format below |
| `date` | string | no | Release date (`YYYY`, `YYYY-MM`, or `YYYY-MM-DD`) |
| `country` | string | no | ISO 3166-1 alpha-2 country code |
| `release-group` | object | no | `{"id": "...", "primary-type": "Album"}` |
| `media` | array | no | `[{"format": "CD", "track-count": 12}]` |
| `barcode` | string | no | UPC/EAN barcode |

`primary-type` values: `Album`, `Single`, `EP`, `Broadcast`, `Other`

`format` values: `CD`, `Digital Media`, `Vinyl`, `Cassette`, etc.

### Recording fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Recording MBID |
| `title` | string | yes | Recording title |
| `length` | int | yes | Duration in milliseconds |
| `artist-credit` | array | yes | See artist-credit format below |
| `isrcs` | array | no | List of ISRC strings (default: `[]`) |
| `release` | string | yes | Key name referencing a release in `releases` |
| `score` | int | no | MB search relevance 0-100 (default: 100) |
| `video` | bool | no | Whether this is a video recording |

### File (metadata) fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Track title as tagged in the file |
| `artist` | string | yes | Track artist as tagged in the file |
| `length` | int | yes | Duration in milliseconds (0 = unknown/missing) |
| `album` | string | no | Album name tag |
| `date` | string | no | Date tag |
| `isrcs` | array | no | List of ISRC strings |

### Artist-credit format

Every `artist-credit` array must use this structure:

```json
[
  {
    "name": "Display Name",
    "artist": {
      "id": "artist-mbid",
      "name": "Artist Name",
      "sort-name": "Name, Artist"
    }
  }
]
```

For multiple artists (featuring, collaboration):

```json
[
  {
    "name": "Main Artist",
    "joinphrase": " feat. ",
    "artist": {"id": "a-1", "name": "Main Artist", "sort-name": "Main Artist"}
  },
  {
    "name": "Guest Artist",
    "artist": {"id": "a-2", "name": "Guest Artist", "sort-name": "Guest Artist"}
  }
]
```

## Using Real MusicBrainz Data

You can base synthetic fixtures on real MB data. Here's how to look up
the information you need.

### From the MB website

1. Find the recording: `https://musicbrainz.org/recording/<MBID>`
2. Note the title, length, artist credit, and ISRCs (under "External links")
3. Click through to the release for release-level details

### From the MB API

Fetch a recording with its releases and ISRCs:

```bash
curl -s "https://musicbrainz.org/ws/2/recording/<RECORDING_MBID>?inc=releases+isrcs+artist-credits&fmt=json" | python -m json.tool
```

Fetch a release with full details:

```bash
curl -s "https://musicbrainz.org/ws/2/release/<RELEASE_MBID>?inc=artist-credits+media+release-groups&fmt=json" | python -m json.tool
```

### Mapping API response to fixture format

**Recording** (API → fixture):

```text
API field                    → Fixture field
─────────────────────────────────────────────
id                           → id
title                        → title
length                       → length
artist-credit                → artist-credit (copy as-is)
isrcs                        → isrcs
(pick a release from list)   → release (use your key name)
score (from search results)  → score
```

**Release** (API → fixture):

```text
API field                    → Fixture field
─────────────────────────────────────────────
id                           → id
title                        → title
artist-credit                → artist-credit (copy as-is)
date                         → date
country                      → country
release-group.id             → release-group.id
release-group.primary-type   → release-group.primary-type
media[].format               → media[].format
media[].track-count          → media[].track-count
barcode                      → barcode (optional)
```

You can strip fields you don't need — the matcher only uses what's listed
in the field reference above. Extra fields are ignored.

### Example: converting a real recording

Say you want to test with "Bohemian Rhapsody" by Queen (recording
`2eaab267-aaa0-4485-a498-4be18e498857`):

```bash
curl -s "https://musicbrainz.org/ws/2/recording/2eaab267-aaa0-4485-a498-4be18e498857?inc=releases+isrcs+artist-credits&fmt=json" | python -m json.tool > /tmp/rec.json
```

Then extract what you need into the fixture format, keeping only the
fields listed above.

## Design Tips

- **One fixture per problem domain** — group related scenarios together
  (e.g., all "featuring artist" cases in one file)
- **Start with the simplest failing case** — don't add 10 candidates if 2
  reproduce the issue
- **Make candidates confusable** — if they're too different, the test is
  trivial and doesn't catch regressions
- **Vary one signal at a time** — have one scenario where ISRC distinguishes,
  another where length does, another where only album title helps
- **Include a "should be easy" scenario** — confirms the basic case works
  before testing edge cases
- **Use realistic durations** — copy actual lengths from MB rather than
  inventing round numbers; real duration differences between versions are
  often just 1-3 seconds

## Common Patterns

### Testing ISRC matching

Give one candidate matching ISRCs, another with different ISRCs, and one with
no ISRCs to test all branches:

```json
"file": {"title": "Song", "artist": "Artist", "length": 240000, "isrcs": ["ISRC1", "ISRC2"]}
```

### Testing without any strong signal

No ISRCs, no album — forces the matcher to rely on title + artist + length
similarity only:

```json
"file": {"title": "Song", "artist": "Artist", "length": 240000}
```

### Testing release preference

When recordings are identical, album/date info should break the tie:

```json
"file": {"title": "Song", "artist": "Artist", "length": 240000, "album": "Specific Album", "date": "2020"}
```
