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

**Decision:** Option values in the exported TOML should be as human-readable as
practical. Simple types (strings, booleans, integers, flat lists) map directly
to TOML. Complex internal representations are converted to clearer equivalents
where the cost is reasonable.

**Rationale:**
- Users should be able to read and understand most of a profile
- Forum readers should be able to evaluate a profile before importing it
- Internal storage formats are an implementation detail that should not leak

**Pragmatic approach:** Full human-readability for every option is not always
worth the implementation and maintenance cost. Where a structured-but-opaque
representation (e.g., list of lists) is the natural TOML mapping and the option
is rarely hand-edited, that's acceptable. The priority is: scripts and common
settings are readable; niche complex options are at least valid TOML.

**Examples:**

| Option | Internal format | Exported as | Notes |
|--------|----------------|-------------|-------|
| `caa_image_types` | `['front']` | `["front"]` | Direct mapping |
| `ca_providers` | `[('Cover Art Archive', True), ...]` | `[["Cover Art Archive", true], ...]` | List of lists — already readable since names are strings |
| `release_type_scores` | `[('album', 0.75), ...]` | `[["album", 0.75], ...]` | List of lists — clear enough |
| `standardize_artists` | `True` | `true` | Direct mapping |

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
# Picard Profile
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

# Optional: plugins required by this profile
required_plugins = [
    {uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890", name = "My Cool Plugin"},
]

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
| `required_plugins` | array of tables | no | Plugins needed for this profile's settings (informational; `uuid` is the key, `name` is for display) |

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
| `enabled` | boolean | no | Whether the script is enabled (default: `true`; only present in backup mode) |

In share mode: only enabled scripts are exported (no `enabled` field written).
In backup mode: all scripts are exported with an explicit `enabled` field.
Imported scripts default to enabled if the field is absent.

#### `[plugins.<uuid>]` — Plugin Option Overrides (optional)

Each plugin with overridden options gets its own sub-table keyed by UUID:

```toml
[plugins."a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
# Plugin: "My Cool Plugin"
my_option = "value"
another_option = 42
```

| Field | Type | Description |
|-------|------|-------------|
| (any key) | any | Plugin option key-value pairs |

The UUID is the canonical plugin identifier (names can clash between plugins).
Plugin name is included as a comment for human readability. On import, plugin
sections for uninstalled plugins are skipped with a warning.

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
   - Respect the `enabled` field if present (default: `true`)
   - Set `enable_tagger_scripts = true` in the profile
6. If `[plugins.*]` sections exist:
   - For each plugin UUID, check if the plugin is installed
   - If installed: apply settings as profile overrides (keyed as
     `plugin.<uuid>/option_name`)
   - If not installed: collect for warning message, skip settings
7. Apply `[settings]` as profile overrides:
   - Skip unknown option names (forward compatibility)
   - Skip options where `in_profile=False` (cannot be overridden by a profile)
   - `active_file_naming_script_id`, `enable_tagger_scripts`, and `list_of_scripts`
     are handled implicitly by steps 4-5 when scripts are present
8. Show warnings (if any): unrecognized options, missing plugins, version mismatch
9. Profile is created in disabled state — user can review and enable it

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
   referenced script into `[scripts.naming]` (unless it's a built-in preset,
   in which case keep the ID in `[settings]` and omit `[scripts.naming]`)
6. If `list_of_scripts` is overridden:
   - **Share mode:** embed only **enabled** scripts into `[[scripts.tagging]]`
   - **Backup mode:** embed **all** scripts with an explicit `enabled` field
7. Remove `active_file_naming_script_id` and `list_of_scripts` from `[settings]`
   (they're represented in `[scripts]` instead)
8. If plugin options are present, resolve plugin names from installed plugins
   and populate `required_plugins` in `[profile]` metadata
9. Write TOML using `tomlkit` (preserves multiline strings, allows adding comments)
10. Save as file or copy to clipboard

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

The `picard-cli profiles` command provides profile management from the terminal:

```bash
# List all profiles
picard-cli profiles list

# Export by title (outputs to stdout)
picard-cli profiles export "Navidrome optimized"

# Export by partial title or UUID prefix, to a file
picard-cli profiles export Navidrome -o navidrome.toml

# Export in backup mode (includes sensitive data and profile UUID)
picard-cli profiles export Navidrome -o navidrome.toml --mode backup

# Import from file (created disabled by default)
picard-cli profiles import navidrome.toml

# Import and enable immediately
picard-cli profiles import navidrome.toml --enable

# Import and replace an existing profile (by title or UUID)
picard-cli profiles import navidrome.toml --replace "Navidrome optimized"
picard-cli profiles import navidrome.toml --replace 6d70
```

Profile resolution (for `--export` and `--replace`) supports exact match,
partial title (case-insensitive), and UUID prefix matching. Errors on
ambiguous matches.

---

## Known Issues & Edge Cases

This section documents potential pitfalls discovered during design review,
along with proposed mitigations.

### Tuple-to-List Conversion

**Problem:** TOML has no tuple type. Several `in_profile=True` options store
lists of tuples internally:

| Option | Internal structure | After TOML round-trip |
|--------|-------------------|----------------------|
| `list_of_scripts` | `[(pos, name, enabled, script), ...]` | `[[pos, name, enabled, script], ...]` |
| `release_type_scores` | `[("album", 0.75), ...]` | `[["album", 0.75], ...]` |
| `ca_providers` | `[("Cover Art Archive", True), ...]` | `[["Cover Art Archive", true], ...]` |
| `script_exceptions` | `[(script_id, threshold), ...]` | `[[script_id, threshold], ...]` |

Python's tuple-unpacking (`for a, b in items:`) works with both tuples and
lists, so existing code tolerates this. However, the type identity is lost.

**Mitigation:**
- `list_of_scripts` is already handled: export extracts it into
  `[[scripts.tagging]]` sections, import reconstructs the tuple list.
- For other options: export as TOML list-of-lists. On import, the
  `ListOption.convert()` method already calls `list(value)` on the outer
  container; inner elements survive as lists. This is acceptable since all
  consuming code uses iteration/unpacking, not `isinstance(x, tuple)` checks.
- If a future code change introduces tuple-identity checks, the import
  deserializer can add explicit tuple conversion keyed by option name.

### Semantic Dependencies Between Options

**Problem:** Some options reference or depend on others. Importing one without
its companion can leave configuration in an inconsistent state.

| Dependency | Risk |
|-----------|------|
| `active_file_naming_script_id` → `file_renaming_scripts` | ID points to a script that doesn't exist |
| `enable_tagger_scripts` + `list_of_scripts` | Master toggle vs per-script enabled flags |
| `caa_restrict_image_types` → `caa_image_types` | Type list only meaningful when restriction is on |
| `ca_providers` ordering → cover art behavior | Provider order determines which source is tried first |

**Mitigation:**
- The design already handles the most critical case: scripts are embedded in
  the export file, and import registers them before setting the reference ID.
- For the other dependencies: no special handling needed. Profiles override
  individual settings; the profile system already allows partial overrides.
  A profile that sets `caa_image_types` without `caa_restrict_image_types` is
  valid — it just means the restriction setting comes from a lower-priority
  profile or the base config. This is existing profile behavior, not new.
- Documentation/comments in exported profiles can hint at related settings.

### Side Effects Outside the Profile (Naming Scripts)

**Problem:** `file_renaming_scripts` (the dict of all naming scripts) is NOT a
per-profile setting — it's a global dict. But `active_file_naming_script_id`
(which profile to select) IS per-profile. This means:

- Importing a profile with a naming script injects the script into the **global**
  `file_renaming_scripts` dict, not into the profile itself.
- If the user later deletes the imported profile, the naming script remains
  as an orphan in the global dict.
- Multiple profiles can reference the same naming script. Deleting one profile
  should not remove a script that another profile uses.

**Mitigation:**
- This is acceptable behavior. Naming scripts are a global resource (like fonts
  or color schemes) — profiles merely *select* one. Users can manage scripts
  independently via the Script Editor.
- On profile deletion, optionally offer to delete the associated naming script
  if no other profile references it. This is a UX enhancement for Phase 2.
- Document this behavior clearly in user-facing import UI ("This will add a
  file naming script to your collection").

### Preset Script References

**Problem:** A profile may override `active_file_naming_script_id` to a preset
ID (`"Preset 1"`, `"Preset 2"`, `"Preset 3"`). Presets are hardcoded in Picard,
not stored in `file_renaming_scripts`.

**Questions:**
- Should export embed the preset's script content? This creates a redundant
  copy on import (the preset already exists).
- Should export just reference the preset by ID? This assumes the preset
  content is identical across versions (it may not be).

**Recommendation:** If the active script is a preset, export it by reference
only (include the ID in settings, do NOT embed in `[scripts.naming]`). Presets
are guaranteed to exist on any Picard installation. If preset content changes
between versions, that's intentional — the user should get the updated version.
Add a `preset = true` flag or omit `[scripts.naming]` entirely when the active
script is a preset.

### Disabled Tagger Scripts in Backup Mode

**Problem:** The design says "Only enabled scripts are exported." This is
correct for share mode (recipients want working scripts, not disabled cruft).
But in backup mode, disabled scripts carry user intent ("I have this script
but chose to turn it off") and should be preserved.

**Mitigation:** In backup mode, export ALL tagger scripts with an explicit
`enabled` field:

```toml
[[scripts.tagging]]
title = "My experimental script"
enabled = false
script = """..."""
```

On import: if `enabled` field is present, respect it. If absent (share mode
format), default to `true` (current behavior).

### Config Version Skew and Renamed Options

**Problem:** Picard has renamed many options over its history (e.g.,
`dont_write_tags` → `enable_tag_saving` with inverted semantics,
`selected_file_naming_script_id` → `active_file_naming_script_id`). The config
upgrade hooks that handle these renames only run on the main config file at
startup — they do NOT run on imported profile data.

A TOML file exported from an older Picard version may contain option names that
the importing version doesn't recognize. These are silently skipped, leading to
silent data loss.

**Severity:** Low in practice. Profiles are most likely shared between users
running similar versions. The `picard_version` field in exports identifies the
source version. Cross-version sharing of very old profiles is an edge case.

**Possible mitigations (from simplest to most complex):**

1. **Accept silent loss** (current design) — unknown options are skipped with
   a warning. The `picard_version_min` field gives an early signal. This is
   the same strategy as Picard's existing config handling.

2. **Maintain a rename mapping** — a small dict of `{old_name: new_name}` (and
   `{old_name: (new_name, transform_fn)}` for inverted booleans) that the
   importer consults before skipping unknown options. This covers the common
   cases without the full upgrade hook machinery.

3. **Run upgrade hooks on import** — most complex, highest fidelity, but the
   upgrade hooks assume they're operating on a full config, not a partial
   settings dict. Would need refactoring.

**Recommendation:** Option 2 for Phase 2. A lightweight rename map covers 90%
of cases with minimal complexity. Phase 1 can ship with option 1 (silent skip +
warning).

### Profile `None` Values (Tracked-but-Not-Overridden)

**Problem:** In the profile system, a setting can be in three states:
1. Not tracked by the profile (key absent)
2. Tracked but no override value (`None`)
3. Overridden with a specific value (non-`None`)

State 2 means "this profile manages this setting, but currently uses the base
config value." It carries intent but no portable value.

**Mitigation:**
- **Share mode:** Skip `None`-valued settings entirely. They carry no useful
  information for another user (whose base config will be different anyway).
- **Backup mode:** Also skip them. The tracked-but-no-value state is a UI
  artifact (checkboxes in the profiles settings tree). On import, the profile
  is recreated with only the concrete overrides; the user can re-check
  additional settings in the profiles UI if they want to track them.
- This means round-tripping a profile through export/import may lose the
  "tracked" state for settings that have no override. This is acceptable —
  the tracked-but-no-value state has no effect on runtime behavior.

### Plugin Options in TOML

**Problem:** Plugin profile keys use the format `plugin.<uuid>/option_name`.
These keys contain dots and slashes which need careful TOML handling (dots in
bare TOML keys are table path separators).

Additionally:
- Plugin UUIDs are opaque to humans reading the export — but they are the
  **only** unique identifier for plugins (names can clash between plugins)
- If the plugin isn't installed on the importing system, settings are dead weight
- Plugin UUIDs are installation-independent (defined in MANIFEST.toml), so they
  ARE portable across systems that have the same plugin installed

**Mitigation for TOML format:** Use a dedicated `[plugins]` section keyed by
UUID (the canonical identifier), with plugin name as a human-readable comment:

```toml
[plugins."a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
# Plugin: "My Cool Plugin"
my_option = "value"
another_option = 42
```

The UUID is the key because:
- Names are not unique (two plugins could have the same name)
- The profile system already keys plugin settings by UUID internally
- Import matching must use UUID, not name

The plugin name is included only as a comment for human readers and in the
`[profile]` metadata (see below) to enable useful warning messages.

**Mitigation for portability:** On import, if a plugin UUID is not recognized
(plugin not installed), show a warning with the plugin name (extracted from
the export's metadata):
*"This profile requires plugins that are not installed: My Cool Plugin
(a1b2c3d4-...). Some settings were skipped."*

To enable this, the `[profile]` section includes a `required_plugins` field:

```toml
[profile]
# ...
required_plugins = [
    {uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890", name = "My Cool Plugin"},
]
```

The `name` field here is informational only (for display in warnings). The
`uuid` is what matters for matching. See open question 5.

### Multiline Scripts with Triple Quotes

**Problem:** TOML multiline literal strings use `'''` delimiters. If a Picard
script contains the sequence `'''`, it would terminate the string early.

**Severity:** Extremely unlikely in practice — Picard's scripting language uses
`$function()`, `%variable%`, and standard text. Triple single-quotes are not
part of the language and would be unusual in file/folder names.

**Mitigation:** `tomlkit` handles this automatically by choosing the appropriate
string representation. If using multiline literal strings (`'''`) and the content
contains `'''`, fall back to multiline basic strings (`"""`) with proper escaping.
No special handling needed in our code if we rely on `tomlkit` for serialization.

### Enum Value Stability

**Problem:** Options backed by Enums (`ImageFormat`, `ResizeModes`) store the
enum's `.value` (a string or int). If enum values are reordered or renamed
between versions, imported values become invalid.

**Severity:** Low. Enum values in Picard are stable (they represent user-facing
choices like `"jpeg"` or resize mode integers). Adding new values is fine;
renaming existing ones would be a breaking change that config upgrade hooks
would handle for the main config but not for imported profiles.

**Mitigation:** Same as renamed options — accept silent fallback to default if
the value doesn't match a known enum member. The `Option.convert()` method
already handles conversion failures by returning the default and logging an
error.

---

## Implementation Plan

### Phase 1: Core (implemented)

1. Add `shareable` flag to `Option.__init__` (default `True`)
2. Mark security/path options as `shareable=False`
3. Promote `tomlkit` to runtime dependency
4. Implement `picard/profiles/exporter.py` (`export_profile()`)
5. Implement `picard/profiles/importer.py` (`import_profile()`)
6. Implement `picard/profiles/settings_upgrades.py` (version-keyed transforms)
7. Implement `picard/profiles/cli.py` (`picard-cli profiles` subcommand)
8. Add Export/Import buttons to profiles UI (with replace support)

### Phase 2: Polish

1. Clipboard copy/paste support
2. Ship example profiles (Navidrome, Plex/Jellyfin, etc.)
3. Import from URL support in CLI

### Phase 3: Community (future, optional)

1. First-run "What's your media server?" wizard
2. Curated profile collection (community GitHub repo or wiki)

---

## Open Questions

### 1. Should import create a disabled profile?

**Possible answers:**
- a) Always create disabled — user must manually enable
- b) Always create enabled — immediate effect
- c) Prompt the user on import ("Enable this profile now?")

**Answer:** (c) Prompt the user. This follows the general Picard pattern of
asking the user when needed. For CLI import, default to disabled with a
`--enable` flag.

---

### 2. Should tagger scripts be merged or replaced?

**Possible answers:**
- a) Append imported scripts after existing ones
- b) Replace the profile's entire `list_of_scripts` with the imported set
- c) Deduplicate by title (update existing, append new)
- d) Append, but warn/skip if a script with identical title AND content exists

**Answer:** (d) Append, with deduplication on exact match (same title + same
content). This avoids accumulating identical copies on repeated imports while
still allowing scripts with the same title but different content to coexist.
If only the title matches but content differs, append as a new script (user
may have customized it). Show a summary after import: "2 scripts added,
1 duplicate skipped."

---

### 3. Should we support partial profiles? (only scripts, no settings)

**Possible answers:**
- a) Yes — all sections besides `[profile]` are optional
- b) No — require at least one of `[settings]` or `[scripts]`

**Answer:** (a) Yes. Partial profiles are fine. A file with only
`[[scripts.tagging]]` and no `[settings]` is valid and useful (sharing scripts
without imposing settings). Validation is simpler: just check `[profile]`
exists.

---

### 4. Should the naming script ID be stable or regenerated on import?

**Possible answers:**
- a) Always regenerate a new UUID — avoids collisions, always creates a new script
- b) Use the ID from the file, with collision handling (ask user on conflict)
- c) Use the ID from the file, silently overwrite on collision

**Answer:** (b) Use the file's ID with collision prompt. This allows
re-importing an updated profile to refresh the script rather than duplicating
it. Silent overwrite (c) is dangerous; always-regenerate (a) leads to script
accumulation on repeated imports.

---

### 5. How should plugin options be handled in export/import?

**Possible answers:**
- a) Always include plugin settings in export; skip on import if plugin absent
- b) Only export plugin settings if explicitly requested by user
- c) Exclude plugin settings entirely (plugins manage their own config)

**Answer:** (b) Only export plugin settings if explicitly requested by user.
Plugin settings may contain sensitive data (API keys, tokens, credentials)
that the `shareable` flag on core options wouldn't catch — plugins define their
own options and may not mark them as non-shareable. Requiring explicit opt-in
prevents accidental leaks. On import, skip with a warning if the plugin isn't
present. Store `required_plugins` in `[profile]` metadata (with UUID +
informational name) so the warning can name the missing plugins.

---

### 6. Should export embed preset naming scripts?

**Possible answers:**
- a) Embed the preset script content (makes file self-contained)
- b) Reference by preset ID only (no `[scripts.naming]` section)
- c) Embed content but mark it as a preset (import recognizes and uses the
   existing preset instead of creating a duplicate)

**Answer:** (c) Embed the content but mark it as a preset. This anticipates
possible changes to presets (renamed or content updated between versions).
By embedding the content, the profile is self-contained and works even if the
preset evolves. On import, if a preset with the same ID exists, the importer
can compare content and use the local preset if it matches, or ask the user
if it differs. Add a `preset = true` field in `[scripts.naming]` to signal
this.

---

### 7. Should backup mode export disabled tagger scripts?

**Possible answers:**
- a) Yes — export all scripts with an `enabled` field
- b) No — export only enabled scripts in both modes

**Answer:** (a) Yes. Backup mode must include everything to allow full profile
restoration. Disabled scripts are exported with `enabled = false`. Share mode
continues to export only enabled scripts (without the field).

---

### 8. Should import apply a rename mapping for old option names?

**Possible answers:**
- a) No — accept silent loss, rely on `picard_version_min` warning
- b) Yes — maintain a lightweight rename map (old_name → new_name + optional
   transform function)
- c) Yes — run full config upgrade hooks on imported settings

**Answer:** Yes — the infrastructure now exists (PICARD-3330). The merged
`_rename_option_in_settings()` and `_upgrade_option_value_in_settings()` helpers
operate on plain dicts, so they can be applied to imported profile settings
directly. The import flow:

1. Read `picard_version` from the TOML file
2. Identify which upgrade transforms apply between that version and current
3. Apply the relevant renames/transforms to the imported settings dict

This can be implemented in Phase 1 by maintaining a registry of version-keyed
setting transforms (parallel to the hooks but operating on dicts only). This
avoids silent data loss without the complexity of running full upgrade hooks.

---

### 9. Should profile deletion offer to clean up orphaned naming scripts?

**Possible answers:**
- a) Yes — prompt to delete the script if unreferenced
- b) No — naming scripts are independent resources, never auto-delete
- c) Yes — silently delete unreferenced scripts

**Answer:** (a) Prompt. Naming scripts are a side effect of import (injected
into the global dict). Prompting on profile deletion avoids silent accumulation
while respecting that the user might want to keep the script for other purposes.

---

### 10. What is the canonical file extension and default filename?

**Possible answers:**
- a) `.toml` only — standard, syntax-highlighted everywhere
- b) `.picard-profile.toml` — allows OS-level file association while keeping
   TOML highlighting
- c) Custom extension like `.pcp` (Picard Configuration Profile)

**Answer:** (a) Use `.toml` extension. The default filename when saving uses
the prefix `picard-profile-` followed by a slugified profile title, e.g.,
`picard-profile-navidrome-optimized.toml`. This makes exported files
immediately recognizable in a directory while keeping standard TOML extension
for editor support and syntax highlighting. Picard identifies profile files
by content (`[profile]` header), not extension.

---

### 11. How should `enable_tagger_scripts` interact with imported scripts?

**Possible answers:**
- a) Always set `enable_tagger_scripts = true` when scripts are present
   (current design) — scripts wouldn't be shared if the author didn't intend
   them to run
- b) Respect the exported value of `enable_tagger_scripts` — preserve the
   author's exact configuration
- c) In share mode: always enable (a). In backup mode: preserve exact value (b)

**Answer:** (c) Mode-dependent, with user prompt if needed. In share mode,
scripts are always enabled (the author shared them to be used). In backup mode,
the exact value of `enable_tagger_scripts` is preserved for faithful
restoration. If the situation is ambiguous, prompt the user.

---

### 12. Should complex list-of-tuple options have bespoke TOML representations?

**Possible answers:**
- a) Export as plain list-of-lists — simple, minimal code, positional meaning
   is documented
- b) Use TOML arrays of inline tables with named fields:
   `[{type = "album", score = 0.75}, ...]` — more readable but requires
   per-option serialization/deserialization logic
- c) Hybrid — use named fields only for options where readability matters most
   (e.g., `ca_providers` where users might hand-edit), plain lists for the rest

**Answer:** (a) Start with plain list-of-lists. This is simplest to implement
and can be upgraded to (b) or (c) later without breaking compatibility — the
importer can detect the format by checking whether elements are lists or dicts,
accepting both. Old exports remain valid when the export format evolves.

---

## References

- [Navidrome Tagging Guidelines](https://www.navidrome.org/docs/usage/library/tagging/)
- [Navidrome tag mappings](https://github.com/navidrome/navidrome/blob/master/resources/mappings.yaml)
- [Picard scripting docs](https://picard-docs.musicbrainz.org/)
- [Community naming scripts](https://community.metabrainz.org/t/repository-for-neat-file-name-string-patterns-and-tagger-script-snippets/2786)
- [TOML specification](https://toml.io/)
