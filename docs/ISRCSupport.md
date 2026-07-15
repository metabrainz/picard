# ISRC Support in Picard

## Overview

This document describes the design for improved ISRC (International Standard
Recording Code) support in Picard. The goal is to make better use of ISRCs —
from existing file tags or from CD reads — for looking up recordings, and
optionally submitting them to MusicBrainz after tagging.

## Related Tickets

| Ticket | Title | Status | Relevance |
|--------|-------|--------|-----------|
| [PICARD-163](https://tickets.metabrainz.org/browse/PICARD-163) | ISRC support in Picard | Open | Primary ticket — use ISRCs for lookup and submission |
| [PICARD-2961](https://tickets.metabrainz.org/browse/PICARD-2961) | Add a "Lookup by..." menu for files and clusters | Open | UI for ISRC-based lookup |
| [PICARD-604](https://tickets.metabrainz.org/browse/PICARD-604) | Ripping support (extra mode/tab) | Open | CD ISRC extraction context |
| [MBS-9367](https://tickets.metabrainz.org/browse/MBS-9367) | Allow submitting ISRCs when adding a release | Open | Server-side submission UX |
| [MBS-10053](https://tickets.metabrainz.org/browse/MBS-10053) | Add a release-level ISRC editor/submission tool with seeding support | Open | Server-side batch submission |
| [PICARD-506](https://tickets.metabrainz.org/browse/PICARD-506) | Allow Picard to submit/lookup to services other than AcoustID | Closed | Historical context |

## Current State

### What Picard already does with ISRCs

1. **Reads ISRCs from all major file formats** — via tag mappings in the
   format handlers (`picard/formats/id3.py`, `mp4.py`, `asf.py`, `apev2.py`,
   and pass-through for Vorbis/FLAC).

2. **Includes ISRC in metadata search** — `File.lookup_metadata()` passes
   the ISRC to `find_tracks()`, which includes it in the Lucene search query
   via `build_lucene_query()`.

3. **Uses ISRC for track matching** — `_isrcs_score()` in `picard/matching.py`
   scores ISRC overlap between file metadata and candidate tracks. The ISRC
   identifier weight is defined in `FILE_COMPARISON_WEIGHTS` in
   `picard/file.py`.

4. **Fetches ISRCs from MusicBrainz** — When loading a release, `inc=isrcs`
   is included in the API request (see `picard/album.py`), and ISRCs are stored
   in track metadata via `add_isrcs_to_metadata()` in `picard/mbjson.py`.

5. **Requests OAuth `submit_isrc` scope** — The authentication flow in
   `picard/tagger.py` already requests this scope, but no submission code
   exists.

### What Picard does NOT do

- **Direct ISRC lookup** via the `/ws/2/isrc/<isrc>` API endpoint
- **ISRC extraction from CD** — `Disc.read()` in `picard/disc/__init__.py`
  only requests `features=['mcn']`, not `'isrc'`
- **ISRC submission** to MusicBrainz — no POST logic implemented despite the
  OAuth scope being available
- **Dedicated "Lookup by ISRC" UI action** — no way to explicitly look up
  by ISRC from the UI

## Design

### Feature 1: ISRC Extraction from CD

#### Background

`Disc.read()` uses `discid.read(device, features=['mcn'])` to calculate disc
IDs. The `python-discid` library also supports an `'isrc'` feature that
extracts the ISRC from each track on the disc (accessible via `track.isrc`).

The external tool [musicbrainz-isrcsubmit](https://github.com/JonnyJD/musicbrainz-isrcsubmit)
uses the same library for this purpose, plus fallback backends (cdrdao,
mediatools) for drives where libdiscid's ISRC reading is unreliable.

#### Approach

- Add `'isrc'` to the features list in `Disc.read()`, conditional on
  `'isrc' in discid.FEATURES` (not all builds of libdiscid support it).
- Store extracted per-track ISRCs in the `Disc` object (keyed by track number).
- After the disc is matched to a release, associate ISRCs with recording IDs
  for potential submission.

#### Considerations

- **Platform/drive reliability:** Some CD drives report incorrect ISRCs (e.g.,
  duplicating an adjacent track's ISRC). Validate against the standard format
  and detect obvious duplicate patterns.
- **Performance:** Reading ISRCs may add time to the disc read. If significant,
  make it opt-in via an option.
- **Integration:** Display extracted ISRCs in the CD lookup dialog. After
  matching, use them for submission (Feature 3).

### Feature 2: ISRC Lookup

#### Background

The MusicBrainz API provides a direct ISRC lookup:

    GET /ws/2/isrc/<isrc>?inc=<INC>

This returns a list of recordings associated with the ISRC. It is more precise
than including the ISRC as a field in a Lucene search query, which is what
Picard currently does.

See: [MusicBrainz API — Non-MBID Lookups — isrc](https://musicbrainz.org/doc/MusicBrainz_API#isrc)

#### Rate Limiting Constraint

The MB API is rate-limited to 1 request/second. A naive per-file ISRC lookup
for an album of 15 tracks would take 15 seconds minimum — unacceptable as a
default behavior. The design must keep the number of extra API calls minimal.

#### Approach

The automatic file lookup (`lookup_metadata()`) already includes the ISRC in
the Lucene search query at no extra API cost. This remains unchanged.

Direct ISRC lookup is exposed only as an **explicit user action** ("Lookup by
ISRC"), not part of the automatic flow:

- Add a `lookup_isrc()` method to `MBAPIHelper` in
  `picard/webservice/api_helpers/musicbrainz.py`. It performs a GET to
  `/isrc/<isrc>` with optional `inc` parameters (same as recording lookups).
- Add a "Lookup by ISRC" context menu action for files and clusters (relates
  to PICARD-2961).
- For a **single file**: one API call to look up its ISRC.
- For a **cluster**: look up one ISRC to identify the release from the
  recording's release list, then load that release normally (2 calls total,
  regardless of album size).

Optionally, a future setting could allow preferring direct ISRC lookup over
search in the automatic flow — as a replacement for the search call (not an
addition), keeping the total call count the same.

#### Considerations

- **Multiple results:** One ISRC can map to multiple recordings. Results must
  still go through matching/scoring.
- **Cluster strategy:** Pick one ISRC from the cluster, look it up, use the
  returned recording's releases to find the best release candidate, then load
  that release. This avoids per-file lookups.

### Feature 3: ISRC Submission

#### Background

The MusicBrainz API supports ISRC submission via an XML POST to
`/ws/2/recording/?client=<client-id>`. The request body contains a
`<recording-list>` with recordings and their associated ISRCs. Authentication
is required (Picard already requests the `submit_isrc` OAuth scope).

See: [MusicBrainz API — ISRC submission](https://musicbrainz.org/doc/MusicBrainz_API#ISRC_submission)

The existing `wrap_xml_metadata()` helper and the pattern used in
`submit_ratings()` (both in `picard/webservice/api_helpers/musicbrainz.py`)
serve as a reference for building the submission request.

#### ISRC Sources

1. **From file tags:** After a file is matched to a track, compare the file's
   ISRCs with the recording's ISRCs (already fetched via `inc=isrcs`). ISRCs
   present in the file but absent from MB are candidates for submission.

2. **From CD:** After a CD lookup matches tracks to recordings, the extracted
   ISRCs can be compared with what's already in MB.

#### Submission Flow

1. **Collect pending ISRCs:** As files are matched, accumulate
   `{recording_id: [isrc, ...]}` pairs for ISRCs not yet in MB.

2. **User review:** Display pending ISRC count (similar to AcoustID fingerprint
   submission). The user triggers submission explicitly.

3. **Batch submit:** Send all pending ISRCs in a single POST request (the API
   supports multiple recordings per request).

4. **Feedback:** Report success/failure to the user.

#### Considerations

- **Validation:** ISRCs must match the standard format before submission.
  Invalid ISRCs should be silently skipped.

- **Duplicate detection:** If the same ISRC appears on multiple files matched
  to different recordings, flag it as suspicious. Don't submit without user
  review.

- **Confidence threshold:** Only submit ISRCs when the file-to-recording match
  is confident. Low-confidence matches should not trigger submission.

- **User control:** Submission must be opt-in and reviewable, never automatic.
  Provide an option to enable/disable ISRC submission entirely.

- **Trust levels:** CD-sourced ISRCs are higher trust (the disc ID gives
  unambiguous recording associations). File-sourced ISRCs may come from
  incorrect tags and warrant more scrutiny.

## Implementation Plan

Each step below is a self-contained commit with its own unit tests where
applicable. Non-UI work comes first; UI integration last. The ISRC lookup
and submission paths are independent and don't block each other.

Commit title conventions:

- English title describing what the commit does
- If a commit resolves a ticket, prefix with `PICARD-XXXX:`
- If multiple tickets, comma-separated: `PICARD-163, PICARD-2961:`

### Step 1: Add ISRC validation and normalization utilities

Add a module (e.g. `picard/util/isrc.py`) with:

- `normalize_isrc(value: str) -> str` — strip hyphens/spaces, uppercase
- `is_valid_isrc(value: str) -> bool` — check normalized value against the
  format `[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}` (12 characters)

Unit tests: valid ISRCs, with/without hyphens, lowercase input, too
short/long, invalid characters, empty string.

Commit: `Add ISRC validation and normalization utilities`

### Step 2: Extract ISRCs from CD during disc read

In `picard/disc/__init__.py`:

- In `Disc.read()`, add `'isrc'` to the `features` list, conditional on
  `'isrc' in discid.FEATURES`.
- In `_set_disc_details()`, iterate `disc.tracks` and store validated ISRCs
  in a `self.isrcs` dict keyed by track number.

Unit tests: mock `discid.read()` returning tracks with/without ISRCs,
verify storage, verify invalid ISRCs are skipped, verify behavior when
`'isrc'` not in `discid.FEATURES`.

Commit: `Extract ISRCs from CD during disc read`

### Step 3: Add ISRC lookup method to MBAPIHelper

In `picard/webservice/api_helpers/musicbrainz.py`:

- Add `lookup_isrc(self, isrc, handler, inc=None)` — performs GET to
  `/isrc/<isrc>` with optional `inc` query args. Follow the pattern of
  existing `_get_by_id()` calls.

Unit tests: verify the constructed URL and query parameters.

Commit: `Add ISRC lookup method to MBAPIHelper`

### Step 4: Add ISRC submission method to MBAPIHelper

In `picard/webservice/api_helpers/musicbrainz.py`:

- Add `submit_isrcs(self, recordings_isrcs, handler)` — POST to
  `/recording/` with XML body containing `<recording-list>` with ISRCs.
  Follow the `submit_ratings()` pattern (uses `wrap_xml_metadata()`,
  `CLIENT_STRING`, `request_mimetype='application/xml; charset=utf-8'`).

Unit tests: verify generated XML structure for various inputs (single
recording/single ISRC, multiple recordings, multiple ISRCs per recording).

Commit: `Add ISRC submission method to MBAPIHelper`

### Step 5: Add ISRC submission manager

Add `picard/isrcsubmit.py` (or similar), following the `AcoustIDManager`
pattern in `picard/acoustid/manager.py`:

- Tracks pending ISRCs: `{recording_id: set(isrcs)}` for ISRCs found in
  files but not yet in MB.
- Methods: `add(file, recording_id, file_isrcs, mb_isrcs)`,
  `update(file, recording_id)`, `remove(file)`, `is_submitted(file)`,
  `submit()`.
- `add()` compares file ISRCs against MB ISRCs for the recording; stores
  only the difference.
- `submit()` calls `MBAPIHelper.submit_isrcs()` with accumulated pending
  ISRCs, handles response.
- After state changes, calls `_check_unsubmitted()` to signal UI.

Unit tests: add/remove/update lifecycle, duplicate detection (same ISRC for
different recordings), empty cases, submission payload construction.

Commit: `Add ISRC submission manager`

### Step 6: Detect submittable ISRCs on file-to-track match

In the file matching / track assignment flow:

- After a file is matched to a track, compare `file.metadata.getall('isrc')`
  with the recording's ISRCs (available from the release data fetched with
  `inc=isrcs`).
- Feed new ISRCs into the submission manager via `add()`.
- When a file is unmatched/removed, call `remove()`.

Unit tests: verify detection logic — file has ISRC that MB doesn't, file has
ISRC that MB already has, file has no ISRC.

Commit: `Detect submittable ISRCs on file-to-track match`

### Step 7: Add submit ISRC toolbar/menu action

Wire up the submission manager to the UI:

- Add a `MainAction.SUBMIT_ISRC` enum value.
- Create the action (similar to `_create_submit_acoustid_action()`).
- Enable/disable it based on `_check_unsubmitted()` from the submission
  manager.
- Trigger `submit()` on the manager when activated.
- Show statusbar feedback on success/failure.

Commit: `PICARD-163: Add submit ISRC toolbar/menu action`

### Step 8: Add "Lookup by ISRC" context menu action

Add a context menu action for files and clusters:

- For a **single file**: call `lookup_isrc()` with the file's ISRC, handle
  the response (list of recordings), load the best matching release.
- For a **cluster**: pick one file with a valid ISRC, look it up, use the
  recording's release list to identify the release, load it.
- If no ISRC is available or lookup returns nothing, show a message or fall
  back to metadata search.

Commit: `PICARD-163, PICARD-2961: Add "Lookup by ISRC" context menu action`

### Step 9: Display extracted ISRCs in CD lookup dialog

In the CD lookup dialog (`picard/ui/cdlookup.py`):

- Show per-track ISRCs extracted from the disc (informational, read-only).
- If ISRCs were not extracted (feature unavailable or no ISRCs on disc),
  don't show the column/field.

Commit: `Display extracted ISRCs in CD lookup dialog`

### Step 10: Add option to enable/disable ISRC submission

In the options UI:

- Add a checkbox to enable/disable ISRC submission (under the existing
  fingerprint/submission settings section).
- When disabled, the submission manager still detects pending ISRCs but
  `submit()` is a no-op and the toolbar action stays hidden/disabled.
- Default: enabled (since submission is already user-triggered, not
  automatic).

Commit: `Add option to enable/disable ISRC submission`

## ISRC Format Reference

An ISRC consists of 12 alphanumeric characters: `CC-XXX-YY-NNNNN`

- `CC` — Country code (2 uppercase letters, ISO 3166-1 alpha-2)
- `XXX` — Registrant code (3 alphanumeric characters)
- `YY` — Year of reference (2 digits)
- `NNNNN` — Designation code (5 digits)

Stored without hyphens: `CCXXXYYNNNNN`

Validation regex: `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$`

## References

- [MusicBrainz API — ISRC lookup](https://musicbrainz.org/doc/MusicBrainz_API#isrc)
- [MusicBrainz API — ISRC submission](https://musicbrainz.org/doc/MusicBrainz_API#ISRC_submission)
- [musicbrainz-isrcsubmit](https://github.com/JonnyJD/musicbrainz-isrcsubmit) — External ISRC submission tool using the same library
- [python-discid documentation](https://python-discid.readthedocs.io/)
- [ISRC on Wikipedia](https://en.wikipedia.org/wiki/International_Standard_Recording_Code)
