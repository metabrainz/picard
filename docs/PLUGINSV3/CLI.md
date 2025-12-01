# Plugin v3 CLI Commands Reference

This document provides a complete reference for the `picard plugins` command-line interface.

---

## Plugin Identification

Plugins can be identified in multiple ways. Understanding these identifiers is important for using the CLI effectively.

### Identifier Types

**Registry ID** (recommended for registry plugins)
- Short, human-readable identifier from the official registry
- Example: `view-script-variables`, `listenbrainz`
- Only available for plugins installed from the registry
- Easiest to remember and type
- Stored when you install from registry

**Plugin ID** (internal identifier)
- Directory name where plugin is installed
- Format: `<sanitized-name>_<uuid>`
- Example: `listenbrainz_891a96e7-0e29-41d4-a716-446655440000`
- Always unique, used internally by Picard
- Automatically generated during installation

**UUID** (universal identifier)
- Unique identifier from MANIFEST.toml
- Example: `a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d`
- Never changes, even if plugin moves repositories
- Used for blacklisting and tracking

**Display Name** (human-readable name)
- Plugin's display name from MANIFEST.toml
- Example: `ListenBrainz Submitter`
- May not be unique (though rare)
- Case-insensitive matching

### How Commands Accept Identifiers

Most commands accept a plugin identifier, which can be:

### How Commands Accept Identifiers

Most commands accept a plugin identifier, which can be:

- **Registry ID**: `view-script-variables` (only for plugins installed from registry, always unique)
- **Plugin ID**: `listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d` (always unique, used internally)
- **Display name**: `ListenBrainz Submitter` (case-insensitive, may not be unique)
- **UUID**: `a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d` (always unique)
- **Prefix**: Any prefix of any identifier type (unique if no collisions)

**Note:** The Plugin ID is the directory name where the plugin is installed. It consists of a sanitized version of the display name plus the UUID (e.g., `listenbrainz_891a96e7-...`).

**Registry ID (recommended):** If you installed a plugin from the registry (e.g., `picard plugins --install view-script-variables`), you can use the short registry ID for all operations. This is stored when you install from the registry and is much easier to remember than the full Plugin ID.

**Prefix matching:** You can use any prefix of **any identifier type** (Registry ID, Plugin ID, UUID, or Display name). All matching is **case-insensitive**. The command will match if the prefix uniquely identifies a single plugin. Exact matches are prioritized over prefix matches.

**Examples:**
```bash
# Registry ID (exact or prefix)
picard plugins --info view-script-variables            # Exact registry ID
picard plugins --info view-script                      # Registry ID prefix
picard plugins --info VIEW-SCRIPT                      # Case-insensitive

# Display name (exact or prefix)
picard plugins --info "ListenBrainz Submitter"         # Exact display name
picard plugins --info "ListenBrainz"                   # Display name prefix
picard plugins --info listenbrainz                     # Case-insensitive

# Plugin ID (exact or prefix)
picard plugins --info listenbrainz_a1b2c3d4-e5f6-...   # Full Plugin ID
picard plugins --info listenbrainz_a1b2                # Plugin ID prefix

# UUID (exact or prefix)
picard plugins --info a1b2c3d4-e5f6-4a5b-8c9d-...      # Full UUID
picard plugins --info a1b2c3d4                         # UUID prefix
```

**Note:** If multiple plugins match (e.g., ambiguous prefix like `view` matching both `view-script-variables` and `view-history`), you'll get an error listing the matches. Use a more specific identifier (longer prefix, full identifier, or UUID).

---

## Quick Reference

```bash
# List installed plugins
picard plugins --list

# Install plugin
picard plugins --install https://github.com/user/plugin
picard plugins --install listenbrainz  # By name (Phase 3)

# Update plugins
picard plugins --update listenbrainz
picard plugins --update-all

# Enable/disable
picard plugins --enable listenbrainz
picard plugins --disable listenbrainz

# Uninstall
picard plugins --uninstall listenbrainz
picard plugins --uninstall listenbrainz --purge  # Delete config too

# Get info
picard plugins --info listenbrainz

# Show MANIFEST
picard plugins --manifest                    # Template
picard plugins --manifest listenbrainz       # From installed plugin
picard plugins --manifest ~/dev/my-plugin    # From local directory

# Browse/search (Phase 3)
picard plugins --browse
picard plugins --search "cover art"

# Disable colored output
picard plugins --list --no-color
picard plugins --validate ~/dev/my-plugin --no-color
```

---

## CLI Modes

Plugin commands work in two modes:

**Standalone (Picard not running):**
- Commands modify config files and plugin directories
- Changes take effect when Picard starts
- Phase 1 implementation

```bash
picard plugins --enable listenbrainz
# Output: Plugin enabled. Restart Picard to load it.
```

**Remote (Picard running):**
- Commands sent to running Picard via `-e` option
- Changes take effect immediately (hot reload)
- Phase 2 implementation

```bash
picard -e "PLUGIN_ENABLE listenbrainz"
# Output: Plugin enabled and loaded.
```

---

## Complete Command Line Interface

**Base command:** `picard plugins [OPTIONS]`

### Help Output

```
usage: picard plugins [-h] [-l] [-i URL [URL ...]] [-u PLUGIN [PLUGIN ...]]
                      [-e PLUGIN [PLUGIN ...]] [-d PLUGIN [PLUGIN ...]]
                      [--update PLUGIN [PLUGIN ...]] [--update-all]
                      [--info NAME|URL] [--ref REF] [--switch-ref PLUGIN REF]
                      [--browse] [--search TERM] [--check-blacklist URL]
                      [--refresh-registry] [--check-updates] [--reinstall]
                      [--status] [-y] [--force-blacklisted] [--trust-community]
                      [--trust LEVEL] [--category CATEGORY] [--purge] [--no-color]

Manage Picard plugins (install, update, enable, disable)

options:
  -h, --help            show this help message and exit

Plugin Management:
  -l, --list            list all installed plugins with details
  -i URL [URL ...], --install URL [URL ...]
                        install plugin(s) from git URL(s) or by name
  -u PLUGIN [PLUGIN ...], --uninstall PLUGIN [PLUGIN ...]
                        uninstall plugin(s)
  -e PLUGIN [PLUGIN ...], --enable PLUGIN [PLUGIN ...]
                        enable plugin(s)
  -d PLUGIN [PLUGIN ...], --disable PLUGIN [PLUGIN ...]
                        disable plugin(s)
  --update PLUGIN [PLUGIN ...]
                        update specific plugin(s) to latest version
  --update-all          update all installed plugins
  --info NAME|URL       show detailed information about a plugin
  --status              show detailed status of all plugins (for debugging)
  --validate URL        validate plugin MANIFEST from git URL

Git Version Control:
  --ref REF             git ref (branch, tag, or commit) to use with --install, --validate
  --switch-ref PLUGIN REF
                        switch plugin to different git ref without reinstalling

Plugin Discovery:
  --browse              browse official plugin registry
  --search TERM         search official plugins by name or description
  --check-blacklist URL
                        check if a plugin URL is blacklisted

Registry:
  --refresh-registry    force refresh of plugin registry cache (can be combined with other commands)
  --check-updates       check for available plugin updates

Advanced Options:
  --reinstall           force reinstall when used with --install
  -y, --yes             skip all confirmation prompts (for automation)
  --force-blacklisted   install plugin even if blacklisted (DANGEROUS!)
  --trust-community     skip warnings for community plugins
  --trust LEVEL         filter plugins by trust level (official, trusted, community)
  --category CATEGORY   filter plugins by category (metadata, coverart, ui, scripting, formats, other)
  --purge               delete plugin configuration when uninstalling
  --no-color            disable colored output

Trust Levels:
  🛡️  official      - Reviewed by Picard team (highest trust)
  ✓  trusted   - Known authors, not reviewed (high trust)
  ⚠️  community        - Other authors, not reviewed (use caution)
  🔓 unregistered     - Not in registry (local/unknown source - lowest trust)

For more information, visit: https://picard.musicbrainz.org/docs/plugins/
```

---

## Commands Summary

| Command | Status | Phase | Description |
|---------|--------|-------|-------------|
| `--list` / `-l` | ✅ Done | 1.3 | List all installed plugins |
| `--install <url>` / `-i` | ✅ Done | 1.1 | Install plugin from git URL |
| `--install <name>` | ✅ Done | 3.3 | Install official plugin by name |
| `--uninstall <name>` / `-u` | ✅ Done | 1.1 | Uninstall plugin |
| `--enable <name>` / `-e` | ✅ Done | 1.1 | Enable plugin |
| `--disable <name>` / `-d` | ✅ Done | 1.1 | Disable plugin |
| `--update <name>` | ✅ Done | 1.4 | Update specific plugin |
| `--update-all` | ✅ Done | 1.4 | Update all plugins |
| `--info <name\|url>` | ✅ Done | 1.3 | Show plugin details |
| `--status <name>` | ✅ Done | 1.5 | Show detailed plugin status |
| `--ref <ref>` | ✅ Done | 1.6 | Specify git ref (branch/tag/commit) |
| `--switch-ref <name> <ref>` | ✅ Done | 1.6 | Switch plugin to different ref |
| `--check-updates` | ✅ Done | 1.4 | Check for updates within installed ref |
| `--reinstall` | ✅ Done | 1.7 | Force reinstall (use with --install) |
| `--purge` | ✅ Done | 1.7 | Delete plugin config on uninstall |
| `--clean-config <name>` | ✅ Done | 1.7 | Delete plugin configuration |
| `--yes` / `-y` | ✅ Done | 1.3 | Skip confirmation prompts |
| `--force-blacklisted` | ✅ Done | 1.8 | Override blacklist warning |
| `--validate <url>` | ✅ Done | 2.1 | Validate plugin MANIFEST |
| `--manifest [target]` | ✅ Done | 2.1 | Show MANIFEST.toml (template or from plugin) |
| `--browse` | ✅ Done | 3.3 | Browse official plugins |
| `--search <term>` | ✅ Done | 3.3 | Search official plugins |
| `--check-blacklist <url>` | ✅ Done | 1.8 | Check if URL is blacklisted |
| `--refresh-registry` | ✅ Done | 3.2 | Force refresh plugin registry cache |
| `--trust-community` | ✅ Done | 3.2 | Skip community plugin warnings |
| `--trust <level>` | ✅ Done | 3.3 | Filter by trust level (with --browse/--search) |
| `--category <cat>` | ✅ Done | 3.3 | Filter by category (with --browse/--search) |

---

## Detailed Command Specifications

### List Plugins

**Command:** `picard plugins --list` or `picard plugins -l`

**Description:** List all installed plugins with status and details

**Example output:**
```
Installed plugins:

  listenbrainz (enabled) 🛡️
    Version: 2.1.0
    Git ref: main @ a1b2c3d
    API: 3.0
    Trust: official
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/listenbrainz
    Description: Submit your music to ListenBrainz

  discogs (disabled) ✓
    Version: 1.5.0
    Git ref: dev @ f4e5d6c
    API: 3.0, 3.1
    Trust: trusted
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/discogs
    Description: Discogs metadata provider

Total: 2 plugins (1 enabled, 1 disabled)
```

---

### Install Plugin

**Command:** `picard plugins --install <url|path|id>` or `picard plugins -i <url|path|id>`

**Description:** Install plugin from git repository URL, local path, or registry ID

**Examples:**
```bash
# Install from GitHub
picard plugins --install https://github.com/metabrainz/picard-plugin-listenbrainz

# Install from specific ref
picard plugins --install https://github.com/user/plugin --ref v1.0.0

# Install from local repository (absolute path)
picard plugins --install ~/dev/my-plugin

# Install from local repository (relative path - note the ./)
picard plugins --install ./my-plugin

# Install from registry by ID
picard plugins --install view-script-variables

# Install multiple
picard plugins --install url1 url2 url3
```

**How the argument is interpreted:**
- **Contains `/` or `://`** → Treated as URL or file path
- **No `/` or `://`** → Treated as registry ID (looks up in plugin registry)

**Important:** If you have a local directory without a path separator, you must prefix it with `./` to avoid registry lookup:
```bash
# Wrong - will look in registry:
picard plugins --install my-plugin

# Correct - will use local directory:
picard plugins --install ./my-plugin
```

**Behavior:**
1. Check if URL is blacklisted
2. Clone git repository
3. Read and validate MANIFEST.toml
4. Check API version compatibility
5. Show trust level warning if needed
6. Install to plugins3 directory
7. Enable plugin (if user confirms)

---

### Install from Registry

**Command:** `picard plugins --install <registry-id>`

**Description:** Install plugin by registry ID (no slashes or protocol)

**Examples:**
```bash
# Install by registry ID
picard plugins --install view-script-variables

# Install multiple from registry
picard plugins --install listenbrainz discogs acoustid
```

**Note:** The registry ID is shown in `--browse` and `--search` output. It's different from the internal plugin_id that gets created after installation.

**Versioning behavior:**
- If plugin has `versioning_scheme` in registry and no `--ref` specified:
  - Fetches all tags from repository
  - Filters by versioning pattern (e.g., semver: v1.0.0, v2.1.3)
  - Installs latest matching tag
- Otherwise: installs first ref (usually `main` branch)

**Examples with versioning:**
```bash
# Plugin with versioning_scheme: semver
picard plugins --install my-plugin
# Installs latest tag (e.g., v2.1.4)

# Override to install specific version
picard plugins --install my-plugin --ref v1.0.0

# Override to install branch instead
picard plugins --install my-plugin --ref main
```

---

### Uninstall Plugin

**Command:** `picard plugins --uninstall <name>` or `picard plugins -u <name>`

**Description:** Uninstall plugin and optionally remove config

**Examples:**
```bash
# Uninstall plugin (keep config)
picard plugins --uninstall listenbrainz

# Uninstall and delete config
picard plugins --uninstall listenbrainz --purge

# Uninstall multiple
picard plugins --uninstall listenbrainz discogs
```

---

### Enable/Disable Plugin

**Commands:**
- `picard plugins --enable <name>` or `picard plugins -e <name>`
- `picard plugins --disable <name>` or `picard plugins -d <name>`

**Description:** Enable or disable installed plugin

**Examples:**
```bash
# Enable plugin (using registry ID if installed from registry)
picard plugins --enable view-script-variables

# Enable plugin (using plugin ID)
picard plugins --enable listenbrainz_a1b2c3d4-e5f6-...

# Disable plugin
picard plugins --disable view-script-variables

# Enable multiple
picard plugins --enable listenbrainz discogs acoustid
```

**Note:** If you installed a plugin from the registry, you can use the short registry ID (e.g., `view-script-variables`) instead of the long plugin_id with UUID suffix.

---

### Update Plugin

**Commands:**
- `picard plugins --update <name>` - Update specific plugin
- `picard plugins --update-all` - Update all plugins
- `picard plugins --check-updates` - Check for available updates

**Description:** Update plugin to latest version from git

**Examples:**
```bash
# Update one plugin (using registry ID if installed from registry)
picard plugins --update view-script-variables

# Update one plugin (using plugin ID)
picard plugins --update listenbrainz_a1b2c3d4-e5f6-...

# Update to specific ref
picard plugins --update view-script-variables --ref v2.0.0

# Update all plugins
picard plugins --update-all

# Check for updates without installing
picard plugins --check-updates
```

**Note on registry ID:** If you installed a plugin from the registry (e.g., `picard plugins --install view-script-variables`), you can use the short registry ID for updates instead of the long plugin_id with UUID suffix.

**Note on `--check-updates`:** This command checks for updates within the currently installed git ref (branch/tag). If a plugin is installed from a specific branch (e.g., `dev`), it will only check for updates on that branch, not on other branches like `main`. To switch to a different branch, use `--switch-ref` instead.

**Versioning behavior:**
- If plugin has `versioning_scheme` in registry:
  - Fetches all tags from repository
  - Filters by versioning pattern
  - Finds tags newer than currently installed version
  - Updates to latest matching tag
- Otherwise: updates to latest commit on installed branch

**Examples with versioning:**
```bash
# Plugin with versioning_scheme: semver, currently on v2.1.4
picard plugins --update my-plugin
# Discovers and updates to v3.0.0

# Plugin on branch (no versioning_scheme)
picard plugins --update my-plugin
# Updates to latest commit on current branch
```

**Note on tags:** If a plugin is installed with a version tag (e.g., `v1.0.0`, `1.2.3`), `--update` will automatically find and switch to the latest version tag. Non-version tags (e.g., `stable`, `latest`) are treated as immutable.

```bash
# Plugin installed with version tag v1.0.0
picard plugins --update myplugin
# Output: Updated from v1.0.0 to v1.2.0

# Plugin installed with non-version tag "stable"
picard plugins --update myplugin
# Output: Already up to date

# To switch to a specific tag manually
picard plugins --switch-ref myplugin v2.0.0

# Or switch to a branch for continuous updates
picard plugins --switch-ref myplugin main
```

**Note on commits:** If a plugin was installed with a specific commit hash, `--update` will report "Already up to date" because commit hashes are immutable. Use `--switch-ref` to change to a different commit, tag, or branch.

**Example:**
```bash
# Plugin installed from 'dev' branch at v0.7.3
picard plugins --check-updates
# Output: All plugins are up to date (checks 'dev' branch only)

# To switch to 'main' branch (which might have v1.0.0)
picard plugins --switch-ref myplugin main
```

---

### Plugin Info

**Command:** `picard plugins --info <identifier>`

**Description:** Show detailed information about plugin

**Plugin Lookup:** Plugins can be identified by:
- **Registry ID**: `view-script-variables` (only for plugins installed from registry)
- **Plugin ID**: `listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d`
- **Display name**: `ListenBrainz Submitter` (case-insensitive)
- **UUID**: `a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d`
- **Prefix**: Any prefix of Plugin ID or UUID (must be unique)
- **Git URL**: `https://github.com/user/plugin` (for registry lookup)

**Examples:**
```bash
# By registry ID (if installed from registry)
picard plugins --info view-script-variables

# By display name
picard plugins --info listenbrainz

# By UUID
picard plugins --info a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# By UUID prefix
picard plugins --info a1b2c3d4

# By Plugin ID
picard plugins --info listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# By Plugin ID prefix
picard plugins --info listenbrainz_a1b2

# By URL (not installed)
picard plugins --info https://github.com/user/plugin
```

**Example output:**
```
Plugin: ListenBrainz Submitter
UUID: a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d
Status: enabled
Version: 2.1.0
Author: MusicBrainz Picard Team
Trust Level: official 🛡️

Git Information:
  URL: https://github.com/metabrainz/picard-plugin-listenbrainz
  Ref: main
  Commit: a1b2c3d4e5f6 (2025-11-20)
  Message: Fix authentication bug

API Versions: 3.0
Category: metadata
License: GPL-2.0

Path: ~/.local/share/MusicBrainz/Picard/plugins3/listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

Description:
  Submit your music to ListenBrainz and update your listening history.

Installed: 2025-11-15 10:30:00
Last Updated: 2025-11-20 14:15:00
```

---

### Git Ref Management

**Commands:**
- `picard plugins --install <url> --ref <ref>` - Install specific ref
- `picard plugins --switch-ref <name> <ref>` - Switch to different ref
- `picard plugins --update <name> --ref <ref>` - Update to specific ref
- `picard plugins --info <name>` - Show available refs for registered plugins

**Description:** Manage git branches, tags, and commits

**Understanding refs:**
- **Branches** (e.g., `main`, `dev`): Mutable - `--update` pulls latest commits
- **Version tags** (e.g., `v1.0.0`, `2.1.3`): `--update` automatically finds and switches to latest version tag
- **Non-version tags** (e.g., `stable`, `latest`): Immutable - use `--switch-ref` to change
- **Commits** (e.g., `abc1234`): Immutable - cannot be updated, use `--switch-ref` to change

**Registry refs:**
Plugins in the official registry can specify multiple refs (branches/tags) that are available for installation:
- **Default ref**: First ref in the list, automatically selected based on your Picard version
- **Beta/testing refs**: Optional refs for testing new features
- **Version-specific refs**: Separate branches for different Picard major versions

**Auto-selection:**
When installing a registered plugin without specifying `--ref`, Picard automatically selects the most appropriate ref based on your Picard API version. For example:
- Picard 3.x users get the `picard-v3` branch
- Picard 4.x users get the `main` branch

**When to use `--update` vs `--switch-ref`:**
- Use `--update` to get the latest version (works for both branches and tags)
- Use `--switch-ref` to change to a different branch/tag, or to switch from commit to branch/tag

**Examples:**
```bash
# Install from registry (auto-selects appropriate ref)
picard plugins --install my-plugin

# Install specific ref from registry
picard plugins --install my-plugin --ref beta

# Show available refs for registered plugin
picard plugins --info my-plugin
# Output:
#   Available refs:
#     - main (default) - Stable release for Picard 4.x
#     - beta - Testing new features
#     - picard-v3 - Maintenance branch for Picard 3.x

# Install from tag
picard plugins --install https://github.com/user/plugin --ref v1.0.0

# Install from branch
picard plugins --install https://github.com/user/plugin --ref dev

# Switch to different branch
picard plugins --switch-ref myplugin dev

# Switch to beta ref (for registered plugin)
picard plugins --switch-ref myplugin beta

# Switch to tag
picard plugins --switch-ref myplugin v1.1.0
```

**Ref validation:**

When using `--switch-ref`, Picard validates the ref exists:

- **With `versioning_scheme`**: Validates tag matches pattern and exists
  ```bash
  picard plugins --switch-ref my-plugin v1.0.0
  # If invalid:
  # ✗ Error: Tag 'v1.0.0' not found
  #
  # Available versions:
  #   v2.1.4 (latest)
  #   v2.1.3
  #   v2.0.0
  ```

- **With explicit `refs`**: Validates ref is in registry list
  ```bash
  picard plugins --switch-ref my-plugin beta
  # If invalid:
  # ✗ Error: Ref 'beta' not available for this plugin
  #
  # Available refs:
  #   main (default) - Stable release for Picard 4.x
  #   picard-v3 - Maintenance branch for Picard 3.x
  ```

**Use cases:**

1. **Testing beta features:**
   ```bash
   # Switch to beta channel
   picard plugins --switch-ref my-plugin beta

   # Switch back to stable
   picard plugins --switch-ref my-plugin main
   ```

2. **Staying on older Picard version:**
   ```bash
   # If you're on Picard 3.x and plugin moved to 4.x API
   picard plugins --switch-ref my-plugin picard-v3
   ```

3. **Pinning to specific version:**
   ```bash
   # Pin to specific tag
   picard plugins --switch-ref my-plugin v2.1.0
   ```

---

### Reinstall Plugin

**Command:** `picard plugins --install <url> --reinstall`

**Description:** Force reinstall of an already installed plugin. Useful for:
- Recovering from corrupted plugin files
- Resetting plugin to clean state
- Testing plugin installation process

**Examples:**
```bash
# Reinstall plugin from same URL
picard plugins --install https://github.com/user/plugin --reinstall

# Reinstall with different ref
picard plugins --install https://github.com/user/plugin --ref v2.0.0 --reinstall

# Reinstall without prompts (automation)
picard plugins --install https://github.com/user/plugin --reinstall --yes
```

**Behavior:**
1. Checks if plugin is already installed from the same URL
2. If plugin has uncommitted changes, prompts to discard them (or errors with `--yes`)
3. Uninstalls existing plugin
4. Installs fresh copy from git repository
5. Preserves plugin configuration (unless `--purge` is used)

**Note:** If the plugin has uncommitted local changes, you'll be prompted to discard them. In non-interactive mode (`--yes`), the operation will fail to prevent data loss.

---

### Trust Community Plugins

**Command:** `picard plugins --install <url> --trust-community`

**Description:** Skip warnings when installing community plugins. This flag only affects **community** trust level plugins - unregistered plugins will still show warnings.

**Trust Levels:**
- **Official** (🛡️) - No warnings (Picard team maintained)
- **Trusted** (✓) - No warnings (Known authors)
- **Community** (⚠️) - Warnings shown (unless `--trust-community` used)
- **Unregistered** (🔓) - Warnings always shown (not in registry)

**Examples:**
```bash
# Install community plugin with warnings (default)
picard plugins --install https://github.com/user/community-plugin
# Output: WARNING: This is a community plugin
#         Community plugins are not reviewed by the Picard team
#         Only install plugins from sources you trust
#         Do you want to continue? [y/N]

# Install community plugin without warnings
picard plugins --install https://github.com/user/community-plugin --trust-community

# Unregistered plugins still show warnings
picard plugins --install https://github.com/unknown/plugin --trust-community
# Output: WARNING: This plugin is not in the official registry
#         Installing unregistered plugins may pose security risks
#         ...
```

**Use case:** Useful for automation or when you've already reviewed the plugin and trust the author.

**Security note:** Only use this flag if you understand the risks. Community plugins are not reviewed by the Picard team. See [SECURITY.md](SECURITY.md) for details on the trust model.

---

### Browse Official Plugins

**Command:** `picard plugins --browse`

**Description:** Browse official plugin registry

**Examples:**
```bash
# Browse all plugins
picard plugins --browse

# Browse by category
picard plugins --browse --category metadata

# Browse by trust level
picard plugins --browse --trust official

# Browse official + trusted
picard plugins --browse --trust official,trusted
```

---

### Search Plugins

**Command:** `picard plugins --search <term>`

**Description:** Search official plugin registry

**Examples:**
```bash
# Search by name
picard plugins --search listenbrainz

# Search by keyword
picard plugins --search "cover art"

# Search with filters
picard plugins --search metadata --category metadata
picard plugins --search script --trust official
```

---

### Check Blacklist

**Command:** `picard plugins --check-blacklist <url>`

**Description:** Check if a plugin URL is blacklisted before installing

**Examples:**
```bash
# Check if URL is blacklisted
picard plugins --check-blacklist https://github.com/user/plugin

# Example output (not blacklisted):
# ✓ URL is not blacklisted

# Example output (blacklisted):
# ✗ URL is blacklisted: Security vulnerability CVE-2024-1234
```

**Exit codes:**
- `0` - URL is not blacklisted (safe to install)
- `1` - URL is blacklisted (do not install)

**Note:** Blacklisted plugins are blocked during installation unless `--force-blacklisted` is used (not recommended).

---

### Refresh Registry

**Command:** `picard plugins --refresh-registry`

**Description:** Force refresh of plugin registry cache

**Examples:**
```bash
# Refresh registry cache
picard plugins --refresh-registry

# Combine with other commands (recommended when switching registries)
picard plugins --refresh-registry --browse
picard plugins --refresh-registry --install view-script-variables

# After changing PICARD_PLUGIN_REGISTRY_URL
export PICARD_PLUGIN_REGISTRY_URL="https://example.com/custom-registry.json"
picard plugins --refresh-registry --browse
```

**Use cases:**
- Switching to a different registry URL
- Testing with custom registries
- Forcing immediate update of registry data
- Clearing stale cache

**Note:** The registry is cached for 24 hours by default. Use `--refresh-registry` to bypass the cache and fetch the latest version immediately. It can be combined with any other command that uses the registry (--browse, --search, --install, etc.).

---

### Status and Debug

**Command:** `picard plugins --status`

**Description:** Show detailed plugin state for debugging

**Example output:**
```
Plugin Status Report:

listenbrainz:
  State: ENABLED
  Module: Loaded
  Hooks: 5 registered
  Config: 3 settings
  Last enabled: 2025-11-20 10:30:00

discogs:
  State: DISABLED
  Module: Loaded (not active)
  Hooks: 0 registered
  Last disabled: 2025-11-18 15:45:00
```

---

## Common Workflows

### Discover and Install
```bash
picard plugins --search "listenbrainz.org"
picard plugins --info listenbrainz
picard plugins --install listenbrainz
```

### Validate Plugin

**Command:** `picard plugins --validate <url> [--ref <ref>]`

**Description:** Validate a plugin's MANIFEST.toml without installing it

**Use cases:**
- Plugin developers testing their MANIFEST
- Registry maintainers validating submissions
- Users checking plugin before installation

**Example:**
```bash
# Validate main branch
picard plugins --validate https://github.com/user/my-plugin

# Validate specific branch
picard plugins --validate https://github.com/user/my-plugin --ref dev

# Validate specific tag
picard plugins --validate https://github.com/user/my-plugin --ref v1.0.0
```

**Success output:**
```
Validating plugin from: https://github.com/user/my-plugin
Cloning repository...
✓ MANIFEST.toml found

✓ Validation passed

Plugin Information:
  Name: My Plugin
  Version: 1.0.0
  Authors: John Doe
  Description: A great plugin for Picard
  API versions: 3.0
  License: GPL-2.0-or-later
```

**Error output:**
```
Validating plugin from: https://github.com/user/bad-plugin
Cloning repository...
✓ MANIFEST.toml found

✗ Validation failed with 3 error(s):

  • Missing required field: version
  • Field 'description' must be 1-200 characters (got 250)
  • Section 'name_i18n' is present but empty
```

### Show MANIFEST

**Command:** `picard plugins --manifest [plugin|path|url]`

**Description:** Display MANIFEST.toml template or from a plugin

**Use cases:**
- Get a template for creating new plugins (no argument)
- View MANIFEST from installed plugin
- View MANIFEST from local plugin directory
- View MANIFEST from remote git repository

**Examples:**
```bash
# Show template (for creating new plugins)
picard plugins --manifest

# Show MANIFEST from installed plugin
picard plugins --manifest listenbrainz

# Show MANIFEST from local directory
picard plugins --manifest ~/dev/my-plugin

# Show MANIFEST from git repository
picard plugins --manifest https://github.com/user/plugin
```

**Template output (no argument):**
```toml
# MANIFEST.toml Template
# See https://picard-docs.musicbrainz.org/en/extending/plugins.html

# Required fields
uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"  # Generate with `uuidgen` or online tool
name = "My Plugin Name"
version = "1.0.0"
description = "Short one-line description (1-200 characters)"
api = ["3.0"]

# Optional fields (recommended)
# authors = ["Your Name"]
# maintainers = ["Your Name"]
# license = "GPL-2.0-or-later"
# license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
# long_description = """
# Detailed multi-line description (1-2000 characters).
# Explain features, requirements, usage notes, etc.
# """
# categories = ["metadata", "coverart", "ui", "scripting", "formats", "other"]
# homepage = "https://github.com/username/plugin-name"
# min_python_version = "3.9"

# Translation tables (optional)
# [name_i18n]
# de = "Mein Plugin Name"
# fr = "Mon nom de plugin"
```

**Plugin output (with argument):**
```toml
uuid = "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"
name = "ListenBrainz Submitter"
version = "2.1.0"
description = "Submit your music to ListenBrainz"
long_description = """
This plugin integrates with ListenBrainz...
"""
api = ["3.0", "3.1"]
authors = ["MusicBrainz Picard Team"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
homepage = "https://github.com/metabrainz/picard-plugin-listenbrainz"
categories = ["metadata"]
```


### Update Workflow
```bash
picard plugins --check-updates
picard plugins --update-all
```

### Testing Workflow
```bash
picard plugins --install <url> --ref dev
picard plugins --disable plugin
picard plugins --enable plugin
picard plugins --switch-ref plugin main
```

### Cleanup Workflow
```bash
picard plugins --list
picard plugins --disable old-plugin
picard plugins --uninstall old-plugin --purge
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Plugin not found |
| 3 | Network error |
| 4 | Git error |
| 5 | Blacklisted plugin |
| 6 | Incompatible API version |
| 7 | Invalid manifest |
| 8 | User cancelled |

---

## See Also

- **[ROADMAP.md](ROADMAP.md)** - Development phases and tasks
- **[MANIFEST.md](MANIFEST.md)** - Plugin development guide
- **[REGISTRY.md](REGISTRY.md)** - Registry system details
