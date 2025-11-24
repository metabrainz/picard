# Plugin v3 CLI Commands Reference

This document provides a complete reference for the `picard plugins` command-line interface.

---

## Quick Reference

```bash
# List installed plugins
picard plugins --list

# Install plugin
picard plugins --install https://github.com/user/plugin
picard plugins --install lastfm  # By name (Phase 3)

# Update plugins
picard plugins --update lastfm
picard plugins --update-all

# Enable/disable
picard plugins --enable lastfm
picard plugins --disable lastfm

# Uninstall
picard plugins --uninstall lastfm
picard plugins --uninstall lastfm --purge  # Delete config too

# Get info
picard plugins --info lastfm

# Browse/search (Phase 3)
picard plugins --browse
picard plugins --search "cover art"
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
                      [--refresh-registry] [--check-updates] [--reinstall PLUGIN]
                      [--status] [-y] [--force-blacklisted] [--trust-community]
                      [--trust LEVEL] [--category CATEGORY] [--purge]

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

Git Version Control:
  --ref REF             git ref (branch, tag, or commit) to install/update to
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
  --reinstall PLUGIN    force reinstall of plugin
  -y, --yes             skip all confirmation prompts (for automation)
  --force-blacklisted   install plugin even if blacklisted (DANGEROUS!)
  --trust-community     skip warnings for community plugins
  --trust LEVEL         filter plugins by trust level (official, trusted, community)
  --category CATEGORY   filter plugins by category (metadata, coverart, ui, scripting, formats, other)
  --purge               delete plugin configuration when uninstalling

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
| `--update <name>` | ⏳ TODO | 1.4 | Update specific plugin |
| `--update-all` | ⏳ TODO | 1.4 | Update all plugins |
| `--info <name\|url>` | ⏳ TODO | 1.3 | Show plugin details |
| `--ref <ref>` | ⏳ TODO | 1.6 | Specify git ref (branch/tag/commit) |
| `--switch-ref <name> <ref>` | ⏳ TODO | 1.6 | Switch plugin to different ref |
| `--browse` | ⏳ TODO | 3.3 | Browse official plugins |
| `--search <term>` | ⏳ TODO | 3.3 | Search official plugins |
| `--check-blacklist <url>` | ⏳ TODO | 1.8 | Check if URL is blacklisted |
| `--refresh-registry` | ⏳ TODO | 3.2 | Force refresh plugin registry cache |
| `--check-updates` | ⏳ TODO | 1.4 | Check for available updates |
| `--reinstall <name>` | ⏳ TODO | 1.7 | Reinstall plugin |
| `--status` | ⏳ TODO | 1.5 | Show detailed plugin status |
| `--yes` / `-y` | ⏳ TODO | 1.3 | Skip confirmation prompts |
| `--force-blacklisted` | ⏳ TODO | 1.8 | Override blacklist warning |
| `--trust-community` | ⏳ TODO | 3.2 | Skip community plugin warnings |
| `--trust <level>` | ⏳ TODO | 3.3 | Filter by trust level |
| `--category <cat>` | ⏳ TODO | 3.3 | Filter by category |
| `--purge` | ⏳ TODO | 1.7 | Delete plugin config on uninstall |

---

## Detailed Command Specifications

### List Plugins

**Command:** `picard plugins --list` or `picard plugins -l`

**Description:** List all installed plugins with status and details

**Example output:**
```
Installed plugins:

  lastfm (enabled) 🛡️
    Version: 2.1.0
    Git ref: main @ a1b2c3d
    API: 3.0
    Trust: official
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm
    Description: Scrobble your music to Last.fm

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
picard plugins --install https://github.com/metabrainz/picard-plugin-lastfm

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
picard plugins --install lastfm

# Install multiple
picard plugins --install lastfm discogs acoustid
```

---

### Uninstall Plugin

**Command:** `picard plugins --uninstall <name>` or `picard plugins -u <name>`

**Description:** Uninstall plugin and optionally remove config

**Examples:**
```bash
# Uninstall plugin (keep config)
picard plugins --uninstall lastfm

# Uninstall and delete config
picard plugins --uninstall lastfm --purge

# Uninstall multiple
picard plugins --uninstall lastfm discogs
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
picard plugins --enable lastfm

# Disable plugin
picard plugins --disable lastfm

# Enable multiple
picard plugins --enable lastfm discogs acoustid
```

---

### Update Plugin

**Commands:**
- `picard plugins --update <name>` - Update specific plugin
- `picard plugins --update-all` - Update all plugins

**Description:** Update plugin to latest version from git

**Examples:**
```bash
# Update one plugin
picard plugins --update lastfm

# Update to specific ref
picard plugins --update lastfm --ref v2.0.0

# Update all plugins
picard plugins --update-all

# Check for updates without installing
picard plugins --check-updates
```

---

### Plugin Info

**Command:** `picard plugins --info <name|url>`

**Description:** Show detailed information about plugin

**Examples:**
```bash
# Info for installed plugin
picard plugins --info lastfm

# Info for plugin by URL (not installed)
picard plugins --info https://github.com/user/plugin
```

**Example output:**
```
Plugin: Last.fm Scrobbler
Status: enabled
Version: 2.1.0
Author: MusicBrainz Picard Team
Trust Level: official 🛡️

Git Information:
  URL: https://github.com/metabrainz/picard-plugin-lastfm
  Ref: main
  Commit: a1b2c3d4e5f6 (2025-11-20)
  Message: Fix authentication bug

API Versions: 3.0
Category: metadata
License: GPL-2.0

Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm

Description:
  Scrobble your music to Last.fm and update your listening history.

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
picard plugins --search lastfm

# Search by keyword
picard plugins --search "cover art"
```

---

### Blacklist Check

**Command:** `picard plugins --check-blacklist <url>`

**Description:** Check if plugin URL is blacklisted

**Example:**
```bash
picard plugins --check-blacklist https://github.com/user/plugin
```

---

### Status and Debug

**Command:** `picard plugins --status`

**Description:** Show detailed plugin state for debugging

**Example output:**
```
Plugin Status Report:

lastfm:
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
picard plugins --search "last.fm"
picard plugins --info lastfm
picard plugins --install lastfm
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
