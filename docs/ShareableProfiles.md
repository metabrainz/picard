# Shareable Profiles: TOML-Based Profile Exchange Format

## Summary

A human-readable TOML format for exporting and importing Picard option profiles,
enabling users to easily share configurations on forums and community spaces.
Profiles bundle settings overrides together with their associated scripts
(file naming and tagger scripts), forming self-contained configuration packages
for specific use cases (e.g., optimizing for Navidrome, Plex, Jellyfin, etc.).

---

## Goals

1. **Easy community exchange** — Users can share profiles as text on forums, paste
   them in GitHub issues, or attach them as files. No centralized registry required.
2. **Self-contained** — A profile file includes everything needed: settings, file
   naming script, and tagger scripts. No external dependencies.
3. **Human-readable and editable** — TOML with comments lets users understand *what*
   a profile does and *why* before importing it.
4. **Safe by default** — Security-sensitive options (credentials, tokens) and
   user-specific options (filesystem paths) are excluded from export.
5. **Forward/backward compatible** — Unknown settings are ignored on import.
   A `picard_version_min` field signals compatibility requirements.

---

## Motivation

### The Problem

Users of media servers like Navidrome, Plex, or Jellyfin need specific Picard
configurations to get the best results. This typically involves:

- A file naming script (folder/file structure)
- Tagger scripts (writing extra tags like `ALBUMARTISTS`, `RELEASEDATE`, etc.)
- Specific settings (use ID3v2.4, standardize artist names, embed cover art)

Today, this knowledge lives scattered across documentation pages, forum threads,
and GitHub gists. Users must manually piece together scripts and settings, which
is error-prone and discouraging for newcomers.

### Real-World Example: Navidrome

Navidrome's [tagging documentation](https://www.navidrome.org/docs/usage/library/tagging/#picard-specific-tips)
recommends specific Picard scripts for multi-valued artist tags, date handling,
and album version metadata. Their docs also recommend:

- Using standardized artist names (to prevent duplicate entries)
- Writing ID3v2.4 (for multi-valued tag support)
- Embedding cover art + saving as files

A single importable profile could set all of this up in one click.

> **Note:** Some of these recommendations (e.g., standardized artist names) could
> become Picard defaults in the future. However, this does not eliminate the need
> for shareable profiles: a profile for a specific media server would still need to
> override this setting in case the user has disabled it, and the bundled scripts
> remain the primary value of a shared profile.

---

## Design Decisions

### Why TOML?

**Decision:** Use TOML as the profile format.

**Rationale:**
- Already used in the project (plugin `MANIFEST.toml`, `pyproject.toml`)
- `tomllib` (stdlib Python 3.11+) / `tomli` for reading — already a runtime dependency
- `tomlkit` (comment-preserving read/write) — currently a dev-only dependency,
  would need to be promoted to a runtime dependency (see below)
- Supports multiline strings — scripts are readable inline without escaping
- Supports comments — profiles are self-documenting
- More human-friendly than JSON; less complex than YAML
- Familiar to Python developers

#### TOML dependencies status

| Package | Current status | Purpose |
|---------|---------------|---------|
| `tomli` | Runtime dep (Python < 3.11 fallback) | Read-only TOML parsing |
| `tomllib` | Stdlib (Python 3.11+) | Read-only TOML parsing |
| `tomlkit` | Dev-only dep (`[dependency-groups] dev`) | Comment-preserving TOML read/write |

To implement profile export, `tomlkit` must be promoted to a runtime dependency.
This is acceptable — it is already vetted in the project and `phw` has expressed
openness to including it if write support is needed.

#### Current YAML usage in the codebase

`PyYAML` is currently a runtime dependency. Here is where it is used:

| Location | Purpose | Can migrate to TOML? |
|----------|---------|---------------------|
| `picard/script/serializer.py` | Script package export/import (`.ptsp`/`.yaml`) | **Yes** — primary migration target |
| `picard/session/session_manager.py` | Session save (gzip-compressed YAML) | **Yes** — internal format |
| `picard/session/session_loader.py` | Session load | **Yes** — with fallback for existing files |
| `picard/disc/whipperlog.py` | Parse Whipper CD rip logs (external YAML format) | **No** — external tool output |
| `picard/config_upgrade_hooks.py` | Migrate legacy config data (`create_from_yaml`) | **No** — must read existing user data |

#### Where TOML is already used

| Location | Purpose |
|----------|---------|
| `picard/plugin3/manifest.py` | Read plugin `MANIFEST.toml` (via `tomllib`/`tomli`) |
| `picard/plugin3/registry.py` | Read plugin registry TOML data |
| `picard/plugin3/api_impl.py` | Plugin configuration |
| `pyproject.toml` | Project metadata and build config |

#### Can PyYAML be removed entirely?

**No.** Two use cases require YAML reading indefinitely:

1. **Whipper log parsing** (`picard/disc/whipperlog.py`) — Whipper is an external
   CD ripping tool that outputs YAML logs. This format is not under our control.
2. **Config upgrade hooks** — Existing users may have YAML-encoded script data in
   their configuration that must be readable during upgrades.

However, new features (shareable profiles, and potentially script export and
sessions) should default to TOML. The script serializer could be updated to
export TOML by default while still accepting YAML imports for backward
compatibility.

**Alternatives considered:**
- JSON: No comments, multiline strings require escaping, not forum-friendly
- YAML: Security concerns, complexity, indentation sensitivity
- Custom format: Unnecessary when TOML fits perfectly

---

### Why Not a Centralized Registry?

**Decision:** No registry. Profiles are exchanged as files or text.

**Rationale:**
- Lowest barrier to sharing (paste on a forum, attach to an issue)
- No infrastructure to maintain
- No moderation/approval bottleneck
- Community can curate collections organically (GitHub repos, wiki pages)
- Does not preclude adding an optional registry later if demand arises

---

### The `shareable` Flag on Options

**Decision:** Add a `shareable` boolean to the `Option` class. Options with
`shareable=False` are excluded from profile export in **share mode** (the default),
but included in **backup mode**.

**Rationale:**

There are two distinct export use cases:

- **Share** (posting on a forum, helping another user): sensitive or personal
  options must be excluded to prevent accidental credential leaks or useless
  paths that only make sense on the exporter's machine.
- **Backup** (migrating to a new machine, restoring config): everything should
  be included because the importer is the same person.

Rather than a single "exportable" gate, export has a **mode** selector:

| Mode | Behavior |
|------|----------|
| Share (default) | Excludes options with `shareable=False` |
| Backup | Includes all profile options regardless of `shareable` |

Backup mode is scoped to individual profiles (not the entire Picard config).
A user migrating to a new machine can export each of their profiles separately.
Full application backup (all profiles, base settings, window state) is a
different concern and out of scope for this feature.

The flag name `shareable` communicates intent clearly: "is this safe/meaningful
to share with another person?"

**Options that should be `shareable=False`:**

| Option | Reason |
|--------|--------|
| `proxy_password` | Credential |
| `proxy_username` | Credential |
| `listenbrainz_token` | Credential |
| `proxy_server_host` | Environment-specific |
| `proxy_server_port` | Environment-specific |
| `move_files_to` | User-specific path |
| `starting_directory_path` | User-specific path |
| `autobackup_directory` | User-specific path |
| `windows_long_paths` | Platform-specific |

Note: `shareable` only applies to options that already have `in_profile=True`.
Options with `in_profile=False` (window geometry, persist state, etc.) are never
in profiles and thus never exported in either mode.

On import, the `shareable` flag is not checked — any valid `in_profile=True`
option found in the file is accepted. The flag only protects the *exporter*
from accidentally including sensitive data when sharing.

---

### Human-Readable Values

**Decision:** All option values in the exported TOML must be clear, human-readable
text. Internal representations (opaque IDs, encoded tuples, index numbers) are
converted to meaningful equivalents on export, and converted back on import.

**Rationale:**
- Users must be able to read, understand, and hand-edit a profile
- Forum readers must be able to evaluate a profile before importing it
- Internal storage formats are an implementation detail that should not leak

**Examples:**

| Option | Internal format | Exported as |
|--------|----------------|-------------|
| `caa_image_types` | `('front',)` | `["front"]` |
| `ca_providers` | `[('Cover Art Archive', True), ...]` | (handled via `[settings]` as a TOML array of tables if needed, or simplified) |

Complex options that cannot be cleanly represented in TOML should be documented
case by case. If an option's internal format is already human-readable (strings,
booleans, simple lists), it maps directly to TOML types with no conversion.

---

### Script Ordering

**Decision:** Tagger scripts are ordered. The `[[scripts.tagging]]` array in TOML
preserves insertion order, and import must maintain that order.

**Rationale:**
- Tagger scripts execute sequentially; order can affect results
  (e.g., a script that sets `%date%` must run before one that reads it)
- TOML arrays of tables are ordered by specification
- The import appends scripts in the same order they appear in the file

---

**Decision:** When a profile overrides `active_file_naming_script_id` or
`list_of_scripts`, the actual script content is embedded in the exported file
under a `[scripts]` section.

**Rationale:**
- Makes the profile self-contained (no dangling references)
- Scripts are the most valuable part of a shared profile
- TOML multiline strings make scripts perfectly readable inline
- On import, scripts are registered/merged into the user's script collections

---

## File Format Specification

### Extension

`.toml` — Standard, universally recognized, syntax-highlighted by editors.
Picard identifies profile files by the presence of `[profile]` header, not by
extension.

### Structure

```toml
# Picard Exportable Profile
# https://picard.musicbrainz.org/

[profile]
title = "Navidrome optimized"
description = """
Optimized tagging and file naming for Navidrome media server.
Sets up multi-valued artist tags, proper date handling, and a clean
folder structure. Based on Navidrome's official tagging guidelines.
"""
author = "MusicBrainz Community"
version = "1.0"
created = "2026-06-21"
picard_version = "3.0.0"
picard_version_min = "3.0"

[settings]
# Use standardized artist names — Navidrome matches artists by name,
# so consistent naming prevents duplicate entries.
standardize_artists = true

# Write ID3v2.4 — required for proper multi-valued tag support.
# Navidrome docs: "Avoid [ID3v2.3] if possible and prefer the newer ID3v2.4"
write_id3v23 = false

# Embed cover art in files AND save as separate file.
# Navidrome reads both; doing both maximizes compatibility.
save_images_to_tags = true
save_images_to_files = true
embed_only_one_front_image = true

[scripts.naming]
id = "_profile_naming"
title = "Navidrome / media server friendly"
script = """
$if2(%albumartist%,%artist%)/
%album%$if(%_releasecomment%, \\(%_releasecomment%\\))\
$if(%date%, [$left(%date%,4)])/
$if($gt(%totaldiscs%,1),$num(%discnumber%,1)-,)\
$num(%tracknumber%,2) %title%
"""

[[scripts.tagging]]
title = "Navidrome: Multi-valued artist tags"
script = """
$setmulti(albumartists,%_albumartists%)
$setmulti(albumartistssort,%_albumartists_sort%)
$setmulti(artistssort,%_artists_sort%)
"""

[[scripts.tagging]]
title = "Navidrome: Album version & subtitle"
script = """
$set(musicbrainz_albumcomment,%_releasecomment%)
$if(%_recordingcomment%,$set(subtitle,%_recordingcomment%))
"""

[[scripts.tagging]]
title = "Navidrome: Date handling"
script = """
$set(releasedate,%date%)
$set(date,%_recording_firstreleasedate%)
$set(originaldate,%originaldate%)
$delete(originalyear)
"""
```

### Section Details

#### `[profile]` — Metadata (required)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Display name for the profile |
| `description` | string | no | What this profile does and why |
| `author` | string | no | Who created/maintains it |
| `version` | string | no | Profile version (for user reference) |
| `created` | string | no | ISO date of creation |
| `picard_version` | string | yes | Picard version that generated this file (serves as format identifier) |
| `picard_version_min` | string | no | Minimum Picard version required to use this profile |

#### `[settings]` — Option Overrides (optional)

Key-value pairs where keys are Picard option names and values are their
overridden values. Only options with `in_profile=True` are accepted on import.
In share mode, options with `shareable=False` are excluded from export.
In backup mode, all profile options are included.
Unknown keys are silently ignored on import.

#### `[scripts.naming]` — File Naming Script (optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | no | Script ID (generated if missing) |
| `title` | string | yes | Display name |
| `script` | string | yes | The naming script content |

#### `[[scripts.tagging]]` — Tagger Scripts (optional, array)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Display name |
| `script` | string | yes | The tagger script content |

Only enabled scripts are exported. Imported scripts are always enabled.

---

## Import Behavior

1. Parse TOML, validate `[profile]` section exists
2. Check `picard_version_min` — warn if current Picard is older
3. Create a new profile with `title` from `[profile]`
4. If `[scripts.naming]` exists:
   - Register the script in `file_renaming_scripts` (generate ID if not provided)
   - Set the profile's `active_file_naming_script_id` override to that ID
5. If `[[scripts.tagging]]` entries exist:
   - Append to the profile's `list_of_scripts` override
   - Set `enable_tagger_scripts = true` in the profile
6. Apply `[settings]` as profile overrides:
   - Skip unknown option names (forward compatibility)
   - Skip options where `in_profile=False` (cannot be overridden by a profile)
   - `active_file_naming_script_id`, `enable_tagger_scripts`, and `list_of_scripts`
     are handled implicitly by steps 4-5 when scripts are present
7. Profile is created in disabled state — user can review and enable it

### Conflict Handling

- If a naming script with the same `id` already exists, the user is asked
  whether to update the existing script or create a new one
- Re-importing a profile with the same title creates a new profile (with
  "(copy)" suffix) — profiles are never silently overwritten
- Tagger scripts are always appended (no deduplication by name)
- Settings simply override — the profile system handles precedence

### Removed or Renamed Options

Profiles may reference options that no longer exist in the current Picard version
(removed, renamed, or not yet introduced). Handling:

1. **Unknown options are skipped** — import does not fail
2. **Warnings are collected and shown to the user** after import:
   *"2 settings were not recognized and were skipped: `old_name`, `other_name`"*
3. **The profile is still created** with whatever settings *could* be applied.
   Scripts always import successfully since they are plain text.
4. **`picard_version_min`** provides an early signal — if the importing Picard
   version is older than what the profile expects, a warning is shown *before*
   import: *"This profile was created for Picard 3.2+. Some settings may not
   apply to your version (3.0)."*

This mirrors Picard's existing config upgrade strategy: unrecognized keys are
silently dropped. Profiles degrade gracefully rather than failing entirely.

---

## Export Behavior

1. User selects a profile and clicks "Export"
2. User chooses export mode:
   - **Share** (default): for posting on forums / sending to other users
   - **Backup**: for personal migration / restore
3. Collect all overridden settings for that profile
4. In share mode, filter out options where `shareable=False`
5. If `active_file_naming_script_id` is overridden, resolve and embed the
   referenced script into `[scripts.naming]`
6. If `list_of_scripts` is overridden, embed only **enabled** scripts
   into `[[scripts.tagging]]` (disabled scripts are not exported)
7. Remove `active_file_naming_script_id` and `list_of_scripts` from `[settings]`
   (they're represented in `[scripts]` instead)
8. Write TOML using `tomlkit` (preserves multiline strings, allows adding comments)
9. Save as file or copy to clipboard

---

## UI Integration

### Options → Profiles page

Add two buttons to the profile list button bar:

- **Export** — Exports the selected profile to a `.toml` file (save dialog)
- **Import** — Imports a profile from a `.toml` file (open dialog)

### Optional: Clipboard support

- "Copy profile to clipboard" — for quick forum posting
- "Import from clipboard" — for quick pasting

### Optional: Bundled example profiles

Ship a few `.toml` files in `resources/profiles/` and show them in a
"Community Profiles" section with an "Import" button. These serve as starting
points and documentation-by-example.

---

## CLI Integration

```bash
# Export
picard profile export "Navidrome optimized" -o navidrome.toml

# Import from file
picard profile import navidrome.toml

# Import from URL
picard profile import https://example.com/navidrome.toml

# List profiles
picard profile list
```

---

## Implementation Plan

### Phase 1: Core (minimal viable)

1. Add `shareable` flag to `Option.__init__` (default `True`)
2. Mark security/path options as `shareable=False`
3. Implement `profile_export.py`:
   - `export_profile(profile_id, mode='share') -> str` (returns TOML string)
   - `import_profile(toml_string) -> profile_id` (creates profile, returns ID)
4. Add Export/Import buttons to profiles UI

### Phase 2: Polish

1. Clipboard copy/paste support
2. CLI `picard profile export/import` commands
3. Version compatibility warning on import
4. Ship example profiles (Navidrome, Plex/Jellyfin, etc.)

### Phase 3: Community (future, optional)

1. First-run "What's your media server?" wizard
2. Curated profile collection (community GitHub repo or wiki)

---

## Open Questions

1. **Should import create a disabled profile?** Suggestion: yes, so users can
   review before activating. Alternative: prompt the user on import.

2. **Should tagger scripts be merged or replaced?** Suggestion: append to
   existing scripts (least surprising, non-destructive). Users can manually
   remove duplicates afterward.

3. **Should we support partial profiles?** (e.g., only scripts, no settings)
   Suggestion: yes, all sections besides `[profile]` are optional. A file with
   only `[[scripts.tagging]]` and no `[settings]` would be valid.

4. **Should the naming script ID be stable or regenerated?** Suggestion: use
   the ID from the file when present, with collision handling (ask user).
   This would allow re-importing an updated profile to refresh the script
   rather than duplicating it.

5. **Plugin options** — Profiles can override plugin options (via
   `plugin.<uuid>/option_name`). Suggestion: include them in export if the
   plugin is installed. On import, skip silently if the plugin isn't present.
   Consider noting required plugins in `[profile]` metadata.

---

## References

- [Navidrome Tagging Guidelines](https://www.navidrome.org/docs/usage/library/tagging/)
- [Navidrome tag mappings](https://github.com/navidrome/navidrome/blob/master/resources/mappings.yaml)
- [Picard scripting docs](https://picard-docs.musicbrainz.org/)
- [Community naming scripts](https://community.metabrainz.org/t/repository-for-neat-file-name-string-patterns-and-tagger-script-snippets/2786)
- [TOML specification](https://toml.io/)
