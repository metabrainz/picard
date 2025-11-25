# Plugin v3 GUI Design

This document describes the GUI implementation for plugin management in Picard.

---

## Overview

The plugin GUI provides a user-friendly interface for discovering, installing, and managing plugins without using the command line.

**Implementation:** Phase 4 (after CLI and registry are complete)

---

## UI Sketch

### Main Plugins Options Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ Options > Plugins                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [Search plugins...]                       [Check for Updates]       │
│                                                                     │
│ Filter: [All Categories ▼] [All Trust Levels ▼]                     │
│                                                                     │
├───────────────────────────────┬─────────────────────────────────────┤
│ Installed Plugins             │ Plugin Details                      │
│                               │                                     │
│ [x] ListenBrainz (Official)   │ ListenBrainz Submitter              │
│     abc123 (Update available) │                                     │
│                               │ Submit your music to ListenBrainz   │
│ [ ] Discogs (Trusted)         │                                     │
│     v1.8.0                    │ Ref: abc123 (def456 available)      │
│                               │ Authors: MusicBrainz Picard Team    │
│ [x] Custom Tagger (Community) │ Trust: Official                     │
│     main @ 7d8e9f             │ Category: metadata                  │
│                               │ License: GPL-2.0-or-later           │
│ [+ Install Plugin]            │                                     │
│                               │ This plugin integrates with         │
│                               │ ListenBrainz to submit your music   │
│                               │ listening history.                  │
│                               │                                     │
│                               │ Features:                           │
│                               │ - Real-time listen submission       │
│                               │ - Batch submission                  │
│                               │ - Multiple accounts support         │
│                               │                                     │
│                               │ [Update] [Configure] [Uninstall]    │
└───────────────────────────────┴─────────────────────────────────────┘
```

### Install Plugin Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│ Install Plugin                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ( ) Install from Registry                                           │
│     [Search or browse plugins...]                                   │
│                                                                     │
│     Results:                                                        │
│     ListenBrainz (Official) - Submit your music to ListenBrainz     │
│     Discogs (Trusted) - Get metadata from Discogs                   │
│     Custom Tagger (Community) - Apply custom tagging rules          │
│                                                                     │
│ ( ) Install from URL                                                │
│     Git URL: [https://github.com/user/plugin                    ]   │
│     Ref/Tag: [main                                              ]   │
│                                                                     │
│     Warning: This plugin is not in the official registry.           │
│              Only install if you trust the source.                  │
│                                                                     │
│                                           [Cancel]  [Install]       │
└─────────────────────────────────────────────────────────────────────┘
```

### Browse Plugins Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│ Browse Plugins                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [Search...]  Category: [All ▼]  Trust: [All ▼]                      │
│                                                                     │
│ Official Plugins (5)                                                │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │ ListenBrainz Submitter                      [Installed]       │   │
│ │ Submit your music to ListenBrainz                             │   │
│ │ abc123 - metadata                                             │   │
│ ├───────────────────────────────────────────────────────────────┤   │
│ │ AcoustID                                    [Install]         │   │
│ │ Identify files using audio fingerprints                       │   │
│ │ v1.5.0 - metadata                                             │   │
│ └───────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ Trusted Plugins (12)                                                │
│ ┌───────────────────────────────────────────────────────────────┐   │
│ │ Discogs                                     [Installed]       │   │
│ │ Get metadata from Discogs                                     │   │
│ │ v1.8.0 - metadata - by Bob Swift                              │   │
│ └───────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                                                      [Close]        │
└─────────────────────────────────────────────────────────────────────┘
```

### Update Notification

```
┌─────────────────────────────────────────────────────────────────────┐
│ Plugin Updates Available                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ The following plugins have updates available:                       │
│                                                                     │
│ [x] ListenBrainz Submitter  abc123 -> def456 (5 commits)            │
│ [x] Discogs                 v1.8.0 -> v1.9.0 (tag)                  │
│ [ ] Custom Tagger           main @ 7d8e9f -> main @ 1a2b3c          │
│                                                                     │
│ [Select All]  [Select None]                                         │
│                                                                     │
│                                    [Later]  [Update Selected]       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## UI Components

### 1. Plugin List (Left Panel)

**Displays:**
- Plugin name with trust level label (Official/Trusted/Community/Unregistered)
- Git ref (commit hash, tag, or branch@commit)
- Enabled/disabled checkbox
- Update indicator if available
- Sorted by: enabled first, then alphabetically

**Actions:**
- Click to select and show details
- Checkbox to enable/disable
- Right-click context menu

**Context Menu:**
- Enable/Disable
- Update
- Configure (if has options)
- Uninstall
- View on GitHub
- Check for Updates

### 2. Plugin Details (Right Panel)

**Displays:**
- Plugin name with trust level badge
- Short description
- Long description (if available)
- Git ref (current and available)
- Authors
- Trust level
- Category
- License
- Repository link

**Actions:**
- [Update] - Update to latest ref
- [Configure] - Open plugin settings (if available)
- [Uninstall] - Remove plugin
- [View Repository] - Open in browser

### 3. Toolbar Actions

**Buttons:**
- [Search] - Search installed and registry plugins
- [+ Install Plugin] - Open install dialog
- [Check for Updates] - Check all plugins for updates
- [Settings] - Plugin system settings

**Filters:**
- Category dropdown (All, Metadata, Cover Art, UI, etc.)
- Trust level dropdown (All, Official, Trusted, Community)

### 4. Install Plugin Dialog

**Two modes:**

**From Registry:**
- Search/browse official plugins
- Shows trust level, description, authors
- One-click install

**From URL:**
- Enter git repository URL
- Optional: specify ref/tag/branch
- Warning for unregistered plugins
- Blacklist check before install

### 5. Browse Plugins Dialog

**Features:**
- Search box
- Category filter
- Trust level filter
- Grouped by trust level
- Shows install status
- One-click install for uninstalled plugins

### 6. Update Notification

**Triggers:**
- On Picard startup (if enabled in settings)
- Manual check via toolbar button

**Features:**
- List of available updates
- Select which to update
- Batch update
- Show changelog/release notes (future)

---

## Functionality Mapping

### Core Actions

| Action | Function | Remote Command | Notes |
|--------|----------|----------------|-------|
| Enable plugin | `manager.enable_plugin(name)` | `PLUGIN_ENABLE` | Immediate effect |
| Disable plugin | `manager.disable_plugin(name)` | `PLUGIN_DISABLE` | Immediate effect |
| Install plugin | `manager.install_plugin(url)` | `PLUGIN_INSTALL` | Immediate effect in GUI |
| Uninstall plugin | `manager.uninstall_plugin(name)` | `PLUGIN_UNINSTALL` | Immediate effect in GUI |
| Update plugin | `manager.update_plugin(name)` | `PLUGIN_RELOAD` | Immediate reload in GUI |
| Configure plugin | Open plugin options page | - | If plugin has options |

### Discovery Actions

| Action | Function | Notes |
|--------|----------|-------|
| Browse registry | `registry.list_plugins()` | Fetch from cache |
| Search plugins | `registry.search(query)` | Local search |
| Check updates | `registry.check_updates()` | Compare git refs |
| Refresh registry | `registry.refresh()` | Download latest |

### Information Display

| Data | Source | Notes |
|------|--------|-------|
| Plugin list | `manager.plugins` | Installed plugins |
| Plugin details | `plugin.manifest` | From MANIFEST.toml |
| Trust level | `registry.get_trust_level()` | From registry |
| Update available | `registry.get_latest_ref()` | Compare with installed |
| Blacklist status | `registry.is_blacklisted()` | Check before install |

---

## Settings

### Plugin System Settings

```
┌─────────────────────────────────────────────────────────────────────┐
│ Plugin Settings                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Updates:                                                            │
│ [x] Check for plugin updates on startup                             │
│ [ ] Automatically download updates                                  │
│                                                                     │
│ Security:                                                           │
│ [x] Check blacklist before installing                               │
│ [x] Warn when installing community plugins                          │
│ [x] Warn when installing unregistered plugins                       │
│                                                                     │
│ Registry:                                                           │
│ Cache duration: [24] hours                                          │
│ [Refresh Registry Now]                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Notes

### Phase 4.1: Basic GUI

**Priority:** P3 - Low
**Effort:** 5-7 days

**Tasks:**
- [ ] Create plugin options page
- [ ] Implement plugin list view
- [ ] Implement plugin details panel
- [ ] Add enable/disable toggles
- [ ] Add install/uninstall buttons
- [ ] Show trust level badges
- [ ] Integrate with registry for browsing

**Files to create:**
- `picard/ui/options/plugins3.py` - Main options page
- `picard/ui/widgets/pluginlist.py` - Plugin list widget
- `picard/ui/dialogs/installplugin.py` - Install dialog
- `picard/ui/dialogs/browseplugins.py` - Browse dialog

### Phase 4.2: Advanced Features

**Tasks:**
- [ ] Add update notifications
- [ ] Add search functionality
- [ ] Add filtering by category/trust
- [ ] Add plugin configuration integration
- [ ] Add context menus
- [ ] Add keyboard shortcuts

---

## User Workflows

### Install Official Plugin

1. Click [+ Install Plugin]
2. Select "Install from Registry"
3. Search or browse for plugin
4. Click plugin to see details
5. Click [Install]
6. Plugin downloads and installs
7. Plugin loads immediately (no restart needed)

### Install from URL

1. Click [+ Install Plugin]
2. Select "Install from URL"
3. Enter git repository URL
4. (Optional) Specify ref/tag
5. See warning if unregistered
6. Click [Install]
7. Plugin downloads and installs
8. Plugin loads immediately (no restart needed)

### Update Plugins

1. Click [Check for Updates]
2. See list of available updates
3. Select plugins to update
4. Click [Update Selected]
5. Plugins download updates
6. Plugins reload immediately (no restart needed)

### Enable/Disable Plugin

1. Find plugin in list
2. Click checkbox to toggle
3. Plugin enables/disables immediately
4. No restart required

### Configure Plugin

1. Select plugin in list
2. Click [Configure] button
3. Plugin options page opens
4. Modify settings
5. Click [OK] to save

---

## Trust Level Indicators

**Visual Design:**

- **Official** - Shield icon or [Official] badge, blue/green color
- **Trusted** - Checkmark icon or [Trusted] badge, green color
- **Community** - Warning icon or [Community] badge, yellow/orange color
- **Unregistered** - Lock icon or [Unregistered] badge, red color

**Tooltips:**
- Official: "Maintained and reviewed by Picard team"
- Trusted: "By known author, not reviewed by team"
- Community: "Not reviewed or endorsed by team"
- Unregistered: "Not in official registry - use caution"

---

## Error Handling

### Common Errors

**Network Error:**
```
Failed to download plugin
Unable to connect to repository.
Check your internet connection and try again.
```

**Blacklisted Plugin:**
```
Plugin Blocked
This plugin is blacklisted for security reasons:
"Contains malicious code"

Do not install this plugin.
```

**Incompatible API Version:**
```
Incompatible Plugin
This plugin requires API version 3.2
Your Picard version supports API 3.0-3.1

Update Picard or find a compatible plugin ref.
```

**Install Failed:**
```
Installation Failed
Could not install plugin: Invalid MANIFEST.toml

Check the plugin repository and try again.
```

---

## Accessibility

- Keyboard navigation support
- Screen reader compatible
- Tooltips for all icons
- Clear error messages
- Confirmation dialogs for destructive actions

---

## See Also

- **[ROADMAP.md](ROADMAP.md)** - Phase 4 implementation plan
- **[CLI.md](CLI.md)** - CLI commands that GUI wraps
- **[REGISTRY.md](REGISTRY.md)** - Registry integration
- **[SECURITY.md](SECURITY.md)** - Trust levels and warnings
