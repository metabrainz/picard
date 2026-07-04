# Plugin v3 CLI Commands Reference

This document provides a complete reference for the `picard-cli plugins` command-line interface.

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

- **Registry ID**: `view-script-variables` (only for plugins installed from registry, always unique)
- **Plugin ID**: `listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d` (always unique, used internally)
- **Display name**: `ListenBrainz Submitter` (case-insensitive, may not be unique)
- **UUID**: `a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d` (always unique)
- **Prefix**: Any prefix of any identifier type (unique if no collisions)

**Note:** The Plugin ID is the directory name where the plugin is installed. It consists of a sanitized version of the display name plus the UUID (e.g., `listenbrainz_891a96e7-...`).

**Registry ID (recommended):** If you installed a plugin from the registry (e.g., `picard-cli plugins install view-script-variables`), you can use the short registry ID for all operations. This is stored when you install from the registry and is much easier to remember than the full Plugin ID.

**Prefix matching:** You can use any prefix of **any identifier type** (Registry ID, Plugin ID, UUID, or Display name). All matching is **case-insensitive**. The command will match if the prefix uniquely identifies a single plugin. Exact matches are prioritized over prefix matches.

**Examples:**
```bash
# Registry ID (exact or prefix)
picard-cli plugins info view-script-variables            # Exact registry ID
picard-cli plugins info view-script                      # Registry ID prefix
picard-cli plugins info VIEW-SCRIPT                      # Case-insensitive

# Display name (exact or prefix)
picard-cli plugins info "ListenBrainz Submitter"         # Exact display name
picard-cli plugins info "ListenBrainz"                   # Display name prefix
picard-cli plugins info listenbrainz                     # Case-insensitive

# Plugin ID (exact or prefix)
picard-cli plugins info listenbrainz_a1b2c3d4-e5f6-...   # Full Plugin ID
picard-cli plugins info listenbrainz_a1b2                # Plugin ID prefix

# UUID (exact or prefix)
picard-cli plugins info a1b2c3d4-e5f6-4a5b-8c9d-...      # Full UUID
picard-cli plugins info a1b2c3d4                         # UUID prefix
```

**Note:** If multiple plugins match (e.g., ambiguous prefix like `view` matching both `view-script-variables` and `view-history`), you'll get an error listing the matches. Use a more specific identifier (longer prefix, full identifier, or UUID).

---

## Quick Reference

```bash
# List installed plugins
picard-cli plugins list

# Install plugin
picard-cli plugins install https://github.com/user/plugin
picard-cli plugins install listenbrainz  # By name (Phase 3)

# Update plugins
picard-cli plugins update listenbrainz
picard-cli plugins update --all

# Enable/disable
picard-cli plugins enable listenbrainz
picard-cli plugins disable listenbrainz

# Uninstall
picard-cli plugins remove listenbrainz
picard-cli plugins remove listenbrainz --purge  # Delete saved options too

# Get info
picard-cli plugins info listenbrainz

# Show MANIFEST
picard-cli plugins manifest                    # Template
picard-cli plugins manifest listenbrainz       # From installed plugin
picard-cli plugins manifest ~/dev/my-plugin    # From local directory

# Browse/search (Phase 3)
picard-cli plugins browse
picard-cli plugins search "cover art"

# Disable colored output
picard-cli plugins list --no-color
picard-cli plugins validate ~/dev/my-plugin --no-color
```

---

## CLI Modes

Plugin commands work in two modes:

**Standalone (Picard not running):**
- Commands modify config files and plugin directories
- Changes take effect when Picard starts
- Phase 1 implementation

```bash
picard-cli plugins enable listenbrainz
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

**Base command:** `picard-cli plugins <command> [OPTIONS]`

### Help Output

```text
usage: picard-cli plugins [-h] [--yes] [--locale LOCALE] <command> ...

Install, update, enable, and manage Picard plugins.

options:
  -h, --help        show this help message and exit
  --yes, -y         skip confirmation prompts
  --locale LOCALE   locale for displaying plugin info (e.g., 'fr', 'de', 'en')

plugin commands:
  <command>
    list            list all installed plugins
    install         install plugin(s) from git URL(s) or registry ID
    remove          uninstall plugin(s)
    enable          enable plugin(s)
    disable         disable plugin(s)
    update          update plugin(s) to latest version
    info            show detailed plugin information
    search          search plugins in registry
    browse          browse all plugins from registry
    init            create a new plugin project
    validate        validate a plugin MANIFEST
    refs            list available git refs for a plugin
    switch-ref      switch plugin to a different git ref
    manifest        show MANIFEST.toml (template if no argument)
    check-blacklist check if URL/UUID is blacklisted
    clean-config    delete saved options for a plugin
    refresh-registry
                    force refresh of plugin registry cache
    check-updates   check for available updates

Trust Levels:
  🛡️ official: Reviewed by Picard team (highest trust)
  ✓ trusted: Known authors, not reviewed (high trust)
  ⚠️ community: Other authors, not reviewed (use caution)
  🔓 unregistered: Not in registry (local/unknown source - lowest trust)

For more information, visit: https://picard.musicbrainz.org/docs/plugins/
```

---

## Commands Summary

| Command | Description |
|---------|-------------|
| `list` | List all installed plugins |
| `install <source>` | Install plugin from git URL, path, or registry ID |
| `remove <plugin>` | Uninstall plugin |
| `enable <plugin>` | Enable plugin |
| `disable <plugin>` | Disable plugin |
| `update <plugin>` | Update specific plugin |
| `update --all` | Update all plugins |
| `info <plugin>` | Show plugin details and status |
| `refs <plugin>` | List available git refs for plugin |
| `switch-ref <plugin> <ref>` | Switch plugin to different ref |
| `check-updates` | Check for updates within installed ref |
| `validate <path-or-url>` | Validate plugin MANIFEST |
| `manifest [target]` | Show MANIFEST.toml (template or from plugin) |
| `init [name]` | Create a new plugin project |
| `browse` | Browse official plugins |
| `search <term>` | Search official plugins |
| `check-blacklist [url]` | Check if URL and/or UUID is blacklisted |
| `clean-config [plugin]` | Delete plugin saved options or list orphaned configs |
| `refresh-registry` | Force refresh plugin registry cache |

---

## Detailed Command Specifications

### List Plugins

**Command:** `picard-cli plugins list`

**Description:** List all installed plugins with status and details

**Example output:**
```text
Installed plugins:

  listenbrainz (enabled) 🛡️
    Submit your music to ListenBrainz
    UUID: 891a96e7-0e29-41d4-a716-446655440000
    Registry ID: listenbrainz
    State: LOADED
    Version: 2.1.0 (main @a1b2c3d)
    Source: https://github.com/metabrainz/picard-plugins
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/listenbrainz

  discogs (disabled) ✓
    Retrieve metadata from Discogs
    UUID: f4e5d6c7-8a9b-4c5d-6e7f-8a9b0c1d2e3f
    Registry ID: discogs
    State: LOADED
    Version: 1.5.0 (dev @f4e5d6c)
    Source: https://github.com/metabrainz/picard-plugins
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/discogs
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/discogs
    Description: Discogs metadata provider

Total: 2 plugins (1 enabled, 1 disabled)
```

---

### Install Plugin

**Command:** `picard-cli plugins install <url|path|id>`

**Description:** Install plugin from git repository URL, local path, or registry ID

**Examples:**
```bash
# Install from GitHub
picard-cli plugins install https://github.com/metabrainz/picard-plugin-listenbrainz

# Install from specific ref
picard-cli plugins install https://github.com/user/plugin --ref v1.0.0

# Install from local repository (absolute path)
picard-cli plugins install ~/dev/my-plugin

# Install from local repository (relative path - note the ./)
picard-cli plugins install ./my-plugin

# Install from registry by ID
picard-cli plugins install view-script-variables

# Install multiple
picard-cli plugins install url1 url2 url3
```

**How the argument is interpreted:**
- **Contains `/` or `://`** → Treated as URL or file path
- **No `/` or `://`** → Treated as registry ID (looks up in plugin registry)

**Important:** If you have a local directory without a path separator, you must prefix it with `./` to avoid registry lookup:
```bash
# Wrong - will look in registry:
picard-cli plugins install my-plugin

# Correct - will use local directory:
picard-cli plugins install ./my-plugin
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

**Command:** `picard-cli plugins install <registry-id>`

**Description:** Install plugin by registry ID (no slashes or protocol)

**Examples:**
```bash
# Install by registry ID
picard-cli plugins install view-script-variables

# Install multiple from registry
picard-cli plugins install listenbrainz discogs acoustid
```

**Note:** The registry ID is shown in `browse` and `search` output. It's different from the internal plugin_id that gets created after installation.

**Versioning behavior:**
- If plugin has `versioning_scheme` in registry and no `--ref` specified:
  - Fetches all tags from repository
  - Filters by versioning pattern (e.g., semver: v1.0.0, v2.1.3)
  - Installs latest matching tag
- Otherwise: installs first ref (usually `main` branch)

**Examples with versioning:**
```bash
# Plugin with versioning_scheme: semver
picard-cli plugins install my-plugin
# Installs latest tag (e.g., v2.1.4)

# Override to install specific version
picard-cli plugins install my-plugin --ref v1.0.0

# Override to install branch instead
picard-cli plugins install my-plugin --ref main
```

---

### Uninstall Plugin

**Command:** `picard-cli plugins remove <name>`

**Description:** Uninstall plugin and optionally remove saved options

**Examples:**
```bash
# Uninstall plugin (keep saved options)
picard-cli plugins remove listenbrainz

# Uninstall and delete saved options
picard-cli plugins remove listenbrainz --purge

# Uninstall multiple
picard-cli plugins remove listenbrainz discogs
```

---

### Enable/Disable Plugin

**Commands:**
- `picard-cli plugins enable <name>`
- `picard-cli plugins disable <name>`

**Description:** Enable or disable installed plugin

**Examples:**
```bash
# Enable plugin (using registry ID if installed from registry)
picard-cli plugins enable view-script-variables

# Enable plugin (using plugin ID)
picard-cli plugins enable listenbrainz_a1b2c3d4-e5f6-...

# Disable plugin
picard-cli plugins disable view-script-variables

# Enable multiple
picard-cli plugins enable listenbrainz discogs acoustid
```

**Note:** If you installed a plugin from the registry, you can use the short registry ID (e.g., `view-script-variables`) instead of the long plugin_id with UUID suffix.

---

### Update Plugin

**Commands:**
- `picard-cli plugins update <name>` - Update specific plugin
- `picard-cli plugins update --all` - Update all plugins
- `picard-cli plugins check-updates` - Check for available updates

**Description:** Update plugin to latest version from git

**Examples:**
```bash
# Update one plugin (using registry ID if installed from registry)
picard-cli plugins update view-script-variables

# Update one plugin (using plugin ID)
picard-cli plugins update listenbrainz_a1b2c3d4-e5f6-...

# Update all plugins
picard-cli plugins update --all

# Check for updates without installing
picard-cli plugins check-updates

# To switch to a specific ref, use switch-ref
picard-cli plugins switch-ref view-script-variables v2.0.0
```

**Note on registry ID:** If you installed a plugin from the registry (e.g., `picard-cli plugins install view-script-variables`), you can use the short registry ID for updates instead of the long plugin_id with UUID suffix.

**Note on `check-updates`:** This command checks for updates within the currently installed git ref (branch/tag). If a plugin is installed from a specific branch (e.g., `dev`), it will only check for updates on that branch, not on other branches like `main`. To switch to a different branch, use `switch-ref` instead.

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
picard-cli plugins update my-plugin
# Discovers and updates to v3.0.0

# Plugin on branch (no versioning_scheme)
picard-cli plugins update my-plugin
# Updates to latest commit on current branch
```

**Note on tags:** If a plugin is installed with a version tag (e.g., `v1.0.0`, `1.2.3`), `update` will automatically find and switch to the latest version tag. Non-version tags (e.g., `stable`, `latest`) are treated as immutable.

```bash
# Plugin installed with version tag v1.0.0
picard-cli plugins update myplugin
# Output: Updated from v1.0.0 to v1.2.0

# Plugin installed with non-version tag "stable"
picard-cli plugins update myplugin
# Output: Already up to date

# To switch to a specific tag manually
picard-cli plugins switch-ref myplugin v2.0.0

# Or switch to a branch for continuous updates
picard-cli plugins switch-ref myplugin main
```

**Note on commits:** If a plugin was installed with a specific commit hash, `update` will report "Already up to date" because commit hashes are immutable. Use `switch-ref` to change to a different commit, tag, or branch.

**Example:**
```bash
# Plugin installed from 'dev' branch at v0.7.3
picard-cli plugins check-updates
# Output: All plugins are up to date (checks 'dev' branch only)

# To switch to 'main' branch (which might have v1.0.0)
picard-cli plugins switch-ref myplugin main
```

---

### Plugin Info

**Command:** `picard-cli plugins info <identifier>`

**Description:** Show detailed information and status about plugin

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
picard-cli plugins info view-script-variables

# By display name
picard-cli plugins info listenbrainz

# By UUID
picard-cli plugins info a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# By UUID prefix
picard-cli plugins info a1b2c3d4

# By Plugin ID
picard-cli plugins info listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# By Plugin ID prefix
picard-cli plugins info listenbrainz_a1b2

# By URL (not installed)
picard-cli plugins info https://github.com/user/plugin
```

**Example output:**
```text
Plugin: ListenBrainz Submitter
UUID: a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d
Status: enabled
State: LOADED
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
- `picard-cli plugins refs <name|url>` - List available refs for plugin
- `picard-cli plugins install <url> --ref <ref>` - Install specific ref
- `picard-cli plugins switch-ref <name> <ref>` - Switch to different ref
- `picard-cli plugins info <name>` - Show available refs for registered plugins

**Description:** Manage git branches, tags, and commits

**Understanding refs:**
- **Branches** (e.g., `main`, `dev`): Mutable - `update` pulls latest commits
- **Version tags** (e.g., `v1.0.0`, `2.1.3`): `update` automatically finds and switches to latest version tag
- **Non-version tags** (e.g., `stable`, `latest`): Immutable - use `switch-ref` to change
- **Commits** (e.g., `abc1234`): Immutable - cannot be updated, use `switch-ref` to change

**Registry refs:**
Plugins in the official registry can specify multiple refs (branches/tags) that are available for installation:
- **Default ref**: First ref in the list, automatically selected based on your Picard version
- **Beta/testing refs**: Optional refs for testing new features
- **Version-specific refs**: Separate branches for different Picard major versions

**Auto-selection:**
When installing a registered plugin without specifying `--ref`, Picard automatically selects the most appropriate ref based on your Picard API version. For example:
- Picard 3.x users get the `picard-v3` branch
- Picard 4.x users get the `main` branch

**When to use `update` vs `switch-ref`:**
- Use `update` to get the latest version (works for both branches and tags)
- Use `switch-ref` to change to a different branch/tag, or to switch from commit to branch/tag

**Examples:**
```bash
# Install from registry (auto-selects appropriate ref)
picard-cli plugins install my-plugin

# Install specific ref from registry
picard-cli plugins install my-plugin --ref beta

# Show available refs for registered plugin
picard-cli plugins info my-plugin
# Output:
#   Available refs:
#     - main (default) - Stable release for Picard 4.x
#     - beta - Testing new features
#     - picard-v3 - Maintenance branch for Picard 3.x

# Install from tag
picard-cli plugins install https://github.com/user/plugin --ref v1.0.0

# Install from branch
picard-cli plugins install https://github.com/user/plugin --ref dev

# Switch to different branch
picard-cli plugins switch-ref myplugin dev

# Switch to beta ref (for registered plugin)
picard-cli plugins switch-ref myplugin beta

# Switch to tag
picard-cli plugins switch-ref myplugin v1.1.0
```

**Ref validation:**

When using `switch-ref`, Picard validates the ref exists:

- **With `versioning_scheme`**: Validates tag matches pattern and exists
  ```bash
  picard-cli plugins switch-ref my-plugin v1.0.0
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
  picard-cli plugins switch-ref my-plugin beta
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
   picard-cli plugins switch-ref my-plugin beta

   # Switch back to stable
   picard-cli plugins switch-ref my-plugin main
   ```

2. **Staying on older Picard version:**
   ```bash
   # If you're on Picard 3.x and plugin moved to 4.x API
   picard-cli plugins switch-ref my-plugin picard-v3
   ```

3. **Pinning to specific version:**
   ```bash
   # Pin to specific tag
   picard-cli plugins switch-ref my-plugin v2.1.0
   ```

---

### List Available Refs

**Command:** `picard-cli plugins refs <identifier>`

**Description:** List all available git refs (branches and tags) for a plugin

**Works with:**
- Installed plugin name
- Registry plugin ID
- UUID (for both installed and registry plugins)
- Git URL (for non-installed plugins)

**Example output for registry plugin:**
```bash
$ picard-cli plugins refs additional-artists-variables

Plugin: Additional Artists Variables
Source: https://github.com/rdswift/picard-plugin-additional-artists-variables
Current: v1.0.0 (@27f19f8)

Released Versions (semver):
  v1.0.0 (current)

Branches:
  main

Tags (1 total):
  v1.0.0 (current)
```

**Example output for non-registry plugin:**
```bash
$ picard-cli plugins refs https://github.com/user/my-plugin

Plugin: https://github.com/user/my-plugin
Source: https://github.com/user/my-plugin

Branches:
  main
  dev
  experimental

Tags (5 total):
  v2.0.0
  v1.5.0
  v1.0.0
```

**Use cases:**

1. **Before installing - see what versions are available:**
   ```bash
   picard-cli plugins refs view-script-variables
   picard-cli plugins install view-script-variables --ref v2.0.0
   ```

2. **Using UUID (works for both installed and registry plugins):**
   ```bash
   picard-cli plugins refs 2eae631a-1696-4bdc-841f-f75aaa3ae294
   ```

3. **Before switching - see what refs exist:**
   ```bash
   picard-cli plugins refs my-plugin
   picard-cli plugins switch-ref my-plugin beta
   ```

4. **Check for new releases:**
   ```bash
   picard-cli plugins refs my-plugin
   # See if newer version tags are available
   ```

**Notes:**
- Registry refs show API version constraints to help choose compatible ref (if available)
- Released versions are filtered by `versioning_scheme` (semver/calver/regex)
- All branches and tags are shown from git remote
- Annotated tag references (^{}) are filtered out for cleaner display
- Current ref is marked with `(current)` for installed plugins
- Updates version tag cache for faster subsequent operations

---

### Reinstall Plugin

**Command:** `picard-cli plugins install <url|registry-id|uuid> --reinstall`

**Description:** Force reinstall of an already installed plugin. Useful for:
- Recovering from corrupted plugin files
- Resetting plugin to clean state
- Testing plugin installation process

**Examples:**
```bash
# Reinstall plugin from same URL
picard-cli plugins install https://github.com/user/plugin --reinstall

# Reinstall by registry ID
picard-cli plugins install view-script-variables --reinstall

# Reinstall by UUID
picard-cli plugins install aa0f0588-84e0-4f5b-aa32-17657b4434a1 --reinstall

# Reinstall with different ref
picard-cli plugins install https://github.com/user/plugin --ref v2.0.0 --reinstall

# Reinstall without prompts (automation)
picard-cli plugins install https://github.com/user/plugin --reinstall --yes
```

**Behavior:**
1. If using UUID or registry ID, looks up the installed plugin's source
2. Checks if plugin is already installed from the same URL
3. If plugin has uncommitted changes, prompts to discard them (or auto-discards with `--reinstall --yes`)
4. Uninstalls existing plugin
5. Installs fresh copy from git repository
6. Preserves plugin saved options (unless `--purge` is used)

**Note:** When using `--reinstall --yes`, uncommitted local changes will be automatically discarded. Without `--yes`, you'll be prompted to confirm.

---

### Trust Community Plugins

**Command:** `picard-cli plugins install <url> --trust-community`

**Description:** Skip warnings when installing community plugins. This flag only affects **community** trust level plugins - unregistered plugins will still show warnings.

**Trust Levels:**
- **Official** (🛡️) - No warnings (Picard team maintained)
- **Trusted** (✓) - No warnings (Known authors)
- **Community** (⚠️) - Warnings shown (unless `--trust-community` used)
- **Unregistered** (🔓) - Warnings always shown (not in registry)

**Examples:**
```bash
# Install community plugin with warnings (default)
picard-cli plugins install https://github.com/user/community-plugin
# Output: WARNING: This is a community plugin
#         Community plugins are not reviewed by the Picard team
#         Only install plugins from sources you trust
#         Do you want to continue? [y/N]

# Install community plugin without warnings
picard-cli plugins install https://github.com/user/community-plugin --trust-community

# Unregistered plugins still show warnings
picard-cli plugins install https://github.com/unknown/plugin --trust-community
# Output: WARNING: This plugin is not in the official registry
#         Installing unregistered plugins may pose security risks
#         ...
```

**Use case:** Useful for automation or when you've already reviewed the plugin and trust the author.

**Security note:** Only use this flag if you understand the risks. Community plugins are not reviewed by the Picard team. See [SECURITY.md](SECURITY.md) for details on the trust model.

---

### Browse Official Plugins

**Command:** `picard-cli plugins browse`

**Description:** Browse official plugin registry

**Examples:**
```bash
# Browse all plugins
picard-cli plugins browse

# Browse by category
picard-cli plugins browse --category metadata

# Browse by trust level
picard-cli plugins browse --trust official

# Browse official + trusted
picard-cli plugins browse --trust official,trusted
```

---

### Search Plugins

**Command:** `picard-cli plugins search <term>`

**Description:** Search official plugin registry

**Examples:**
```bash
# Search by name
picard-cli plugins search listenbrainz

# Search by keyword
picard-cli plugins search "cover art"

# Search with filters
picard-cli plugins search metadata --category metadata
picard-cli plugins search script --trust official
```

---

### Check Blacklist

**Command:** `picard-cli plugins check-blacklist [url] [--uuid <uuid>]`

**Description:** Check if a plugin URL and/or UUID is blacklisted before installing. At least one of URL or `--uuid` must be provided.

**Examples:**
```bash
# Check URL only
picard-cli plugins check-blacklist https://github.com/user/plugin

# Check URL and UUID together
picard-cli plugins check-blacklist https://github.com/user/plugin --uuid a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# Check UUID only
picard-cli plugins check-blacklist --uuid a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# Example output (not blacklisted):
# ✓ Not blacklisted

# Example output (blacklisted):
# ✗ Blacklisted: Security vulnerability CVE-2024-1234
```

**Exit codes:**
- `0` - URL is not blacklisted (safe to install)
- `1` - URL is blacklisted (do not install)

**Note:** Blacklisted plugins are blocked during installation unless `--force-blacklisted` is used (not recommended).

---

### Refresh Registry

**Command:** `picard-cli plugins refresh-registry`

**Description:** Force refresh of plugin registry cache

**Examples:**
```bash
# Refresh registry cache
picard-cli plugins refresh-registry

# After changing PICARD_PLUGIN_REGISTRY_URL
export PICARD_PLUGIN_REGISTRY_URL="https://example.com/custom-registry.toml"
picard-cli plugins refresh-registry
picard-cli plugins browse
```

**Use cases:**
- Switching to a different registry URL
- Testing with custom registries
- Forcing immediate update of registry data
- Clearing stale cache

**Note:** The registry is cached locally. Use `refresh-registry` to bypass the cache and fetch the latest version immediately. Run it before other registry commands (`browse`, `search`, `install`) if you need fresh data.

---

## Common Workflows

### Discover and Install
```bash
picard-cli plugins search "listenbrainz.org"
picard-cli plugins info listenbrainz
picard-cli plugins install listenbrainz
```

### Validate Plugin

**Command:** `picard-cli plugins validate <url> [--ref <ref>]`

**Description:** Validate a plugin's MANIFEST.toml without installing it

**Use cases:**
- Plugin developers testing their MANIFEST
- Registry maintainers validating submissions
- Users checking plugin before installation

**Example:**
```bash
# Validate main branch
picard-cli plugins validate https://github.com/user/my-plugin

# Validate specific branch
picard-cli plugins validate https://github.com/user/my-plugin --ref dev

# Validate specific tag
picard-cli plugins validate https://github.com/user/my-plugin --ref v1.0.0
```

**Success output:**
```text
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
```text
Validating plugin from: https://github.com/user/bad-plugin
Cloning repository...
✓ MANIFEST.toml found

✗ Validation failed with 3 error(s):

  • Missing required field: version
  • Field 'description' must be 1-200 characters (got 250)
  • Section 'name_i18n' is present but empty
```

### Show MANIFEST

**Command:** `picard-cli plugins manifest [plugin|path|url]`

**Description:** Display MANIFEST.toml template or from a plugin

**Use cases:**
- Get a template for creating new plugins (no argument)
- View MANIFEST from installed plugin
- View MANIFEST from local plugin directory
- View MANIFEST from remote git repository

**Examples:**
```bash
# Show template (for creating new plugins)
picard-cli plugins manifest

# Show MANIFEST from installed plugin
picard-cli plugins manifest listenbrainz

# Show MANIFEST from local directory
picard-cli plugins manifest ~/dev/my-plugin

# Show MANIFEST from git repository
picard-cli plugins manifest https://github.com/user/plugin
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
picard-cli plugins check-updates
picard-cli plugins update --all
```

### Create a New Plugin

**Command:** `picard-cli plugins init [NAME]`

**Description:** Create a new plugin project with all required files and a git
repository.

**Use cases:**

- Scaffold a new plugin project interactively (no argument)
- Create a plugin project non-interactively with a name

**Generated files:**

- `MANIFEST.toml` — Plugin metadata with a generated UUID
- `__init__.py` — Plugin code with `enable()`/`disable()` stubs
- `README.md` — Basic readme with plugin name
- `.gitignore` — Python-specific ignore rules

With `--with-translations`, the following are also generated or modified:

- `MANIFEST.toml` includes `source_locale` and commented `[name_i18n]`/`[description_i18n]` sections
- `__init__.py` includes `t_` and `api.tr()` usage examples
- `locale/en.toml` — Source locale translation file

A git repository is always initialized. In interactive mode, you are asked
whether to create an initial commit. In non-interactive mode, the initial
commit is created automatically.

**Interactive mode prompts:**

When run without a name (`picard-cli plugins init`), the following prompts
appear in order:

1. Plugin name (required)
2. Destination directory — shows computed default, can be overridden
3. Author name — defaults to last used value or git config
4. Author email — shown only if author is provided
5. Short description
6. Categories — comma-separated numbers for multiple (e.g. `1,3`)
7. License — defaults to last used value or GPL-2.0-or-later
8. Initialize git repository? — yes/no (default: yes)
9. Create initial git commit? — yes/no (default: yes) — only if "Initialize git repository?" is yes.

Author name, email, and license are persisted across runs.

**Options:**

| Flag | Description |
|------|-------------|
| `--target-dir NAME` | Override project directory name (relative to `--parent-dir`, default: `picard-plugin-<slug>`) |
| `--parent-dir DIR` | Parent directory where the project is created (default: current directory) |
| `--author NAME` | Author name for MANIFEST.toml |
| `--category CATEGORY` | Plugin category (metadata, coverart, ui, etc.) |
| `--with-translations` | Include translation support (locale files and examples) |
| `--no-git` | Skip initialization of the git repository (works in both interactive and non-interactive modes) |
| `--no-commit` | Skip initial git commit (works in both interactive and non-interactive modes) |

**Examples:**

```bash
# Interactive mode - prompts for all fields
picard-cli plugins init

# Non-interactive with just a name
picard-cli plugins init "My Cool Plugin"

# Non-interactive with all options
picard-cli plugins init "My Cool Plugin" --author "Jane Doe" --category metadata

# Create in a specific parent directory
picard-cli plugins init "My Cool Plugin" --parent-dir ~/dev

# Override the directory name
picard-cli plugins init "My Cool Plugin" --target-dir my-plugin

# Both: custom name inside custom parent (creates ~/dev/my-plugin)
picard-cli plugins init "My Cool Plugin" --parent-dir ~/dev --target-dir my-plugin

# With translation support
picard-cli plugins init "My Cool Plugin" --with-translations

# Skip initializing the git repository
picard-cli plugins init "My Cool Plugin" --no-git

# Skip initial git commit
picard-cli plugins init "My Cool Plugin" --no-commit
```

**Output:**

```text
✓ Created plugin My Cool Plugin in /home/user/picard-plugin-my-cool-plugin
  MANIFEST.toml
  __init__.py
  README.md
  .gitignore
✓ Git repository initialized with initial commit

Next steps:
  cd /home/user/picard-plugin-my-cool-plugin
  Edit __init__.py to add your plugin code
  Edit MANIFEST.toml to update metadata
  Run picard-cli plugins validate . to check your plugin
```

### Testing Workflow
```bash
picard-cli plugins install <url> --ref dev
picard-cli plugins disable plugin
picard-cli plugins enable plugin
picard-cli plugins switch-ref plugin main
```

### Cleanup Workflow
```bash
picard-cli plugins list
picard-cli plugins disable old-plugin
picard-cli plugins remove old-plugin --purge
```

### Clean Plugin Configuration

**Command:** `picard-cli plugins clean-config [plugin]`

**Description:** Delete saved options for a plugin, or list orphaned configurations

**Use cases:**
- Clean up settings from uninstalled plugins
- Reset plugin to default settings
- Find and remove orphaned configurations

**Examples:**
```bash
# List all orphaned plugin configurations
picard-cli plugins clean-config

# Clean specific plugin configuration by name (with confirmation)
picard-cli plugins clean-config listenbrainz

# Clean by UUID (for orphaned configs)
picard-cli plugins clean-config ae5ef1ed-0195-4014-a113-6090de7cf8b7

# Clean without confirmation (automation)
picard-cli plugins clean-config listenbrainz --yes
```

**List orphaned configs output:**
```text
Orphaned plugin configurations (no plugin installed):
  • ae5ef1ed-0195-4014-a113-6090de7cf8b7
  • f8a9c2b1-3d4e-5f6a-7b8c-9d0e1f2a3b4c
  • 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d

Clean with: picard-cli plugins clean-config <uuid>
```

**When cleaning non-existent plugin:**
```bash
$ picard-cli plugins clean-config nonexistent

✗ No saved options found for "nonexistent"

Orphaned plugin configurations (no plugin installed):
  • ae5ef1ed-0195-4014-a113-6090de7cf8b7
  • f8a9c2b1-3d4e-5f6a-7b8c-9d0e1f2a3b4c

Clean with: picard-cli plugins clean-config <uuid>
```

**Notes:**
- Works even if the plugin is uninstalled
- Requires confirmation unless `--yes` is used
- Shows list of orphaned configs when plugin not found
- Orphaned configs are settings from plugins that are no longer installed
- For installed plugins, use plugin name or UUID
- For orphaned configs, use the UUID shown in the list

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
