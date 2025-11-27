# Plugin v3 CLI Commands Reference

This document provides a complete reference for the `picard plugins` command-line interface.

---

## Plugin Identification

Most commands accept a plugin identifier, which can be:

- **Display name**: `ListenBrainz Submitter` (case-insensitive, may not be unique)
- **Directory name**: `listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d` (always unique)
- **Full UUID**: `a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d` (always unique)
- **UUID prefix**: `a1b2c3d4` (unique if no collisions)

**Examples:**
```bash
# All of these work (if unique):
picard plugins --info "ListenBrainz Submitter"
picard plugins --info listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d
picard plugins --info a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d
picard plugins --info a1b2c3d4
```

**Note:** If multiple plugins match (e.g., same display name), you'll get an error and must use the full UUID or directory name.

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
  --refresh-registry    force refresh of plugin registry cache
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
| `--install <name>` | ⏳ TODO | 3.3 | Install official plugin by name |
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
| `--browse` | ⏳ TODO | 3.3 | Browse official plugins |
| `--search <term>` | ⏳ TODO | 3.3 | Search official plugins |
| `--check-blacklist <url>` | ✅ Done | 1.8 | Check if URL is blacklisted |
| `--refresh-registry` | ⏳ TODO | 3.2 | Force refresh plugin registry cache |
| `--trust-community` | ⏳ TODO | 3.2 | Skip community plugin warnings |
| `--trust <level>` | ⏳ TODO | 3.3 | Filter by trust level |
| `--category <cat>` | ⏳ TODO | 3.3 | Filter by category |

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

**Command:** `picard plugins --install <url>` or `picard plugins -i <url>`

**Description:** Install plugin from git repository URL

**Examples:**
```bash
# Install from GitHub
picard plugins --install https://github.com/metabrainz/picard-plugin-listenbrainz

# Install from specific ref
picard plugins --install https://github.com/user/plugin --ref v1.0.0

# Install from local repository
picard plugins --install ~/dev/my-plugin

# Install multiple
picard plugins --install url1 url2 url3
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

### Install Official Plugin (Phase 3)

**Command:** `picard plugins --install <name>`

**Description:** Install official plugin by name from registry

**Examples:**
```bash
# Install by name
picard plugins --install listenbrainz

# Install multiple
picard plugins --install listenbrainz discogs acoustid
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
# Enable plugin
picard plugins --enable listenbrainz

# Disable plugin
picard plugins --disable listenbrainz

# Enable multiple
picard plugins --enable listenbrainz discogs acoustid
```

---

### Update Plugin

**Commands:**
- `picard plugins --update <name>` - Update specific plugin
- `picard plugins --update-all` - Update all plugins
- `picard plugins --check-updates` - Check for available updates

**Description:** Update plugin to latest version from git

**Examples:**
```bash
# Update one plugin
picard plugins --update listenbrainz

# Update to specific ref
picard plugins --update listenbrainz --ref v2.0.0

# Update all plugins
picard plugins --update-all

# Check for updates without installing
picard plugins --check-updates
```

**Note on `--check-updates`:** This command checks for updates within the currently installed git ref (branch/tag). If a plugin is installed from a specific branch (e.g., `dev`), it will only check for updates on that branch, not on other branches like `main`. To switch to a different branch, use `--switch-ref` instead.

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

**Command:** `picard plugins --info <name|url|uuid>`

**Description:** Show detailed information about plugin

**Plugin Lookup:** Plugins can be identified by:
- **Directory name**: `listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d`
- **Display name**: `ListenBrainz Submitter` (case-insensitive)
- **Full UUID**: `a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d`
- **UUID prefix**: `a1b2c3d4` (must be unique)
- **Git URL**: `https://github.com/user/plugin` (for registry lookup)

**Examples:**
```bash
# By display name
picard plugins --info listenbrainz

# By full UUID
picard plugins --info a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

# By UUID prefix (first 8 chars)
picard plugins --info a1b2c3d4

# By directory name
picard plugins --info listenbrainz_a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

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

**Description:** Manage git branches, tags, and commits

**Examples:**
```bash
# Install from tag
picard plugins --install https://github.com/user/plugin --ref v1.0.0

# Install from branch
picard plugins --install https://github.com/user/plugin --ref dev

# Switch to different branch
picard plugins --switch-ref myplugin dev

# Switch to tag
picard plugins --switch-ref myplugin v1.1.0
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

### Browse Official Plugins (Phase 3)

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

### Search Plugins (Phase 3)

**Command:** `picard plugins --search <term>`

**Description:** Search official plugin registry

**Examples:**
```bash
# Search by name
picard plugins --search listenbrainz

# Search by keyword
picard plugins --search "cover art"
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
authors = ["Your Name"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"

# Optional fields
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
