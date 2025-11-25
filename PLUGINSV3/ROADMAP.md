# Picard Plugin v3 Development Roadmap

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Status:** Work in Progress

---

## Overview

This document outlines the development roadmap for Picard's Plugin v3 system. The new system uses git-based plugin distribution, TOML manifests, and a centralized registry.

## Related Documents

- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification and plugin development guide
- **[REGISTRY.md](REGISTRY.md)** - Registry JSON schema, trust levels, blacklist
- **[WEBSITE.md](WEBSITE.md)** - Website implementation for registry generation
- **[CLI.md](CLI.md)** - CLI commands reference
- **[TRANSLATIONS.md](TRANSLATIONS.md)** - Translation system design
- **[SECURITY.md](SECURITY.md)** - Security model and rationale
- **[DECISIONS.md](DECISIONS.md)** - Design decisions and Q&A
- **[MIGRATION.md](MIGRATION.md)** - Migration guide from v2 to v3

---

## Table of Contents

- [Current State](#current-state)
- [Phase 1: Functional CLI-Only System](#phase-1-functional-cli-only-system)
- [Phase 2: Polish & Robustness](#phase-2-polish--robustness)
- [Phase 3: Official Plugin Repository](#phase-3-official-plugin-repository)
- [Phase 4: GUI](#phase-4-gui)
- [Success Metrics](#success-metrics)
- [Timeline Estimate](#timeline-estimate)
- [Next Actions](#next-actions)

---

## Current State

### Branch Status

| Branch | Owner | Status | Description |
|--------|-------|--------|-------------|
| `phw/plugins-v3` | phw | Active WIP | Core plugin infrastructure, manifest parsing, PluginApi, basic manager |
| `phw/plugins-v3-cli` | phw | Reference | Basic CLI implementation with install/uninstall/enable/disable |
| `master` | - | Stable | Production code with legacy plugin system |

### What Works Now

**Core Infrastructure (phw/plugins-v3):**
- ✅ Plugin discovery from `plugins3/` directory
- ✅ MANIFEST.toml parsing with metadata
- ✅ PluginApi with all major extension points
- ✅ Plugin loading and module execution
- ✅ Git-based plugin sources (pygit2)
- ✅ Basic unit tests

**CLI (phw/plugins-v3-cli):**
- ✅ `picard plugins --list`
- ✅ `picard plugins --install <url>`
- ✅ `picard plugins --uninstall <name>`
- ✅ `picard plugins --enable <name>`
- ✅ `picard plugins --disable <name>`

### What Doesn't Work

**Critical Gaps:**
- ❌ Plugin state not persisted (enable/disable forgotten on restart)
- ❌ All plugins auto-load on startup regardless of state
- ❌ No API version compatibility checking
- ❌ No plugin updates (must uninstall/reinstall)
- ❌ No plugin info/details command
- ❌ No official plugin repository/discovery
- ❌ No error handling or user feedback
- ❌ No GUI

---

## Phase 1: Functional CLI-Only System

**Goal:** Make plugin system usable for developers and power users via CLI only.

### 1.1 Configuration Persistence (CRITICAL)

**Priority:** P0 - Blocker
**Effort:** 2-3 days

**Tasks:**
- [ ] Add `plugins3` section to config schema
- [ ] Store enabled plugin list: `config.setting['plugins3']['enabled_plugins'] = []`
- [ ] Store plugin metadata cache: version, git ref, last update
- [ ] Implement `PluginManager.save_config()` / `load_config()`
- [ ] Update `enable_plugin()` to persist state
- [ ] Update `disable_plugin()` to persist state
- [ ] Update `init_plugins()` to only load enabled plugins

**Files to modify:**
- `picard/const/defaults.py` - add default config structure
- `picard/plugin3/manager.py` - add config load/save methods
- `picard/config.py` - may need schema updates

**Acceptance criteria:**
- Enabled plugins survive restart
- Disabled plugins don't load on startup
- Config file contains plugin state

---

### 1.2 Version Compatibility Checking

**Priority:** P0 - Blocker
**Effort:** 1 day

**Tasks:**
- [ ] Implement `_compatible_api_versions()` check in manager
- [ ] Add warning log for incompatible plugins
- [ ] Skip loading incompatible plugins
- [ ] Add `--force` flag to enable incompatible plugins (at user risk)
- [ ] Show compatibility status in `--list` output

**Files to modify:**
- `picard/plugin3/manager.py` - enhance `_load_plugin()`
- `picard/plugin3/cli.py` - add compatibility info to list

**Acceptance criteria:**
- Plugins with wrong API version don't load
- Clear error message explains why
- User can see which API versions plugin requires

---

### 1.3 Enhanced CLI Output & Error Handling

**Priority:** P1 - High
**Effort:** 2 days

**Tasks:**
- [ ] Improve `--list` output: show version, status (enabled/disabled), API versions, description
- [ ] Add `--info <name|url>` command to show full plugin details
- [ ] Add error handling for all operations (network, git, file system)
- [ ] Add confirmation prompts for destructive operations (uninstall)
- [ ] Add `--yes` flag to skip confirmations
- [ ] Show progress for git clone operations
- [ ] Return proper exit codes (0=success, 1=error)
- [ ] Add clear messages that changes require Picard restart

**Files to modify:**
- `picard/plugin3/cli.py` - enhance all methods
- `picard/plugin3/plugin.py` - better error messages

**Note:** Phase 1 commands modify config/files only. Changes take effect on Picard restart. Remote commands for hot-reload will be added in Phase 2.

**Example output:**
```
$ picard plugins --list
Installed plugins:
  example (enabled)
    Version: 1.0.0
    API: 3.0, 3.1
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/example
    Description: This is an example plugin

  listenbrainz (disabled)
    Version: 2.1.0
    API: 3.0
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/listenbrainz
    Description: ListenBrainz integration
```

---

### 1.4 Plugin Updates

**Priority:** P1 - High
**Effort:** 1-2 days

**Tasks:**
- [ ] Add `--update <name>` command to update single plugin
- [ ] Add `--update-all` command to update all plugins
- [ ] Add `--check-updates` command to check without installing
- [ ] Store git remote URL in config for each plugin
- [ ] Implement `PluginSourceGit.update()` method (fetch + reset)
- [ ] Show what changed (old version → new version)
- [ ] Handle update failures gracefully (rollback?)

**Files to modify:**
- `picard/plugin3/cli.py` - add update commands
- `picard/plugin3/manager.py` - add update methods
- `picard/plugin3/plugin.py` - enhance PluginSourceGit

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to initially do manually checking only (for Phase 1) and ultimately implement automatic checking during startup (Phase 4). I suggest that there be a menu item, either from the main menu or on the 'Plugins' option page, to always allow initiation of a manual update check. I also recommend that the option setting to disable the automatic checking during startup, which exists in the current release of Picard, be retained. Another option might be to automatically perform the update check (if enabled) in the background, and display a notice (possibly right-justified on the same line as the main menu bar) indicating that an update is available. This is the approach that some other applications take (e.g. Calibre). I also suggest that a user setting regarding optional notification of pre-release versions could be included."

**Future enhancements (Phase 2+):**
- Menu item for manual update check
- Automatic background check on startup (with disable option)
- Notification area indicator (like Calibre)
- Setting for pre-release version notifications

**Acceptance criteria:**
- Can update installed plugins from git
- Shows version changes
- Handles network failures

---

### 1.5 Plugin State Management

**Priority:** P1 - High
**Effort:** 1 day

**Tasks:**
- [ ] Add plugin state enum: `DISCOVERED`, `LOADED`, `ENABLED`, `DISABLED`, `ERROR`
- [ ] Track state in `Plugin` class
- [ ] Prevent double-enable, double-disable
- [ ] Add `--status` command to show detailed state
- [ ] Log state transitions

**Files to modify:**
- `picard/plugin3/plugin.py` - add state tracking
- `picard/plugin3/manager.py` - check state before operations

---

### 1.6 Git Ref/Branch Support

**Priority:** P2 - Medium
**Effort:** 1-2 days

**Goal:** Allow developers to install and test specific branches, tags, or commits.

**Tasks:**
- [ ] Add `--ref <branch|tag|commit>` option to install command
- [ ] Store ref in config per plugin
- [ ] Update to specific ref
- [ ] Show current ref in `--list` and `--info`
- [ ] Add `--switch-ref <plugin> <ref>` command to change ref without reinstalling
- [ ] Handle ref changes on update
- [ ] Support local git repositories for development

**Files to modify:**
- `picard/plugin3/cli.py` - add --ref argument
- `picard/plugin3/plugin.py` - pass ref to PluginSourceGit
- `picard/plugin3/manager.py` - store ref in config

**Usage examples:**
```bash
# Install from specific branch
picard plugins --install https://github.com/user/plugin --ref dev

# Install from local git repository
picard plugins --install ~/dev/my-plugin

# Switch to different ref
picard plugins --switch-ref myplugin v1.0.0

# Update to latest on current ref
picard plugins --update myplugin
```

**Acceptance criteria:**
- Can install from any branch, tag, or commit
- Can install from local git repositories
- Can switch between refs without reinstalling
- Config stores current ref and commit
- List/info shows ref information

---

### 1.7 Better Install Logic

**Priority:** P2 - Medium
**Effort:** 1 day

**Tasks:**
- [ ] Derive plugin name from MANIFEST.toml, not URL basename
- [ ] Use plugin ID from MANIFEST for directory name (after clone)
- [ ] Fallback to URL basename if MANIFEST read fails
- [ ] Check if plugin already installed before cloning
- [ ] Add `--reinstall` flag to force reinstall
- [ ] Validate MANIFEST.toml before completing install
- [ ] Clean up on install failure
- [ ] Add `--purge` flag for uninstall to delete configuration
- [ ] Prompt user during uninstall about configuration cleanup
- [ ] Add `--clean-config <name>` command for later cleanup

**Files to modify:**
- `picard/plugin3/manager.py` - enhance `install_plugin()` and `uninstall_plugin()`
- `picard/plugin3/cli.py` - add `--purge` and `--clean-config` options

**Community Feedback:**
> **rdswift (on directory naming):** "I agree with the recommendation to use the plugin ID from MANIFEST after clone, with the fallback to use URL basename."
>
> **rdswift (on config cleanup):** "I suggest a combination of options C and D. The process would allow the user to delete the configuration immediately by prompting upon uninstall, and allow for later deletion if the user changes their mind about their decision to keep the configuration during the uninstall."

**Plugin directory naming logic:**
1. Clone to temporary directory using URL basename
2. Read MANIFEST.toml to get plugin ID
3. Rename directory to plugin ID
4. If MANIFEST read fails, keep URL basename

**Configuration cleanup behavior:**
```bash
# Uninstall with prompt
$ picard plugins --uninstall myplugin
Uninstalling myplugin...
Delete plugin configuration? [y/N] n
✓ Plugin uninstalled (configuration kept)

# Uninstall with purge flag
$ picard plugins --uninstall myplugin --purge
Uninstalling myplugin and deleting configuration...
✓ Plugin and configuration removed

# Clean config later
$ picard plugins --clean-config myplugin
Delete configuration for myplugin? [y/N] y
✓ Configuration deleted
```

---

### 1.8 Basic Blacklist Support (Safety Critical)

**Priority:** P1 - High (Security)
**Effort:** 1 day

**Tasks:**
- [ ] Add `PluginRegistry` class with blacklist checking
- [ ] Fetch plugin registry from website (with caching)
- [ ] Check blacklist before install
- [ ] Show warning and refuse install if blacklisted
- [ ] Add `--force-blacklisted` flag to override (with big warning)
- [ ] Check installed plugins on startup, disable if blacklisted

**Files to create:**
- `picard/plugin3/registry.py`

**Files to modify:**
- `picard/plugin3/manager.py` - add blacklist checks

**Note:** Full registry features (browse, search) come in Phase 3. This task only implements safety-critical blacklist checking.

See [REGISTRY.md](REGISTRY.md) for registry schema and [SECURITY.md](SECURITY.md) for security model.

---

## Phase 2: Polish & Robustness

**Goal:** Make CLI system production-ready.

### 2.1 Comprehensive Testing

**Priority:** P1 - High
**Effort:** 3-4 days

**Tasks:**
- [ ] Unit tests for all manager operations
- [ ] Integration tests for CLI commands
- [ ] Test error conditions (network failure, invalid manifest, etc.)
- [ ] Test config persistence
- [ ] Test version compatibility logic
- [ ] Mock git operations for faster tests

---

### 2.2 Documentation

**Priority:** P1 - High
**Effort:** 2 days

**Tasks:**
- [ ] Update documentation with implementation decisions
- [ ] Write CLI usage guide
- [ ] Document plugin development workflow
- [ ] Add examples for common operations
- [ ] Document config file format

See [CLI.md](CLI.md) for command reference and [MANIFEST.md](MANIFEST.md) for plugin development.

---

### 2.3 Remote Commands for Hot Reload

**Priority:** P2 - Medium
**Effort:** 1-2 days

**Tasks:**
- [ ] Add plugin remote commands to `picard/remotecommands/handlers.py`
- [ ] Implement `PLUGIN_ENABLE <name>` - enable and load immediately
- [ ] Implement `PLUGIN_DISABLE <name>` - disable and unload immediately
- [ ] Implement `PLUGIN_LIST` - list with runtime state
- [ ] Implement `PLUGIN_STATUS <name>` - show detailed runtime status
- [ ] Implement `PLUGIN_RELOAD <name>` - reload after update
- [ ] Update documentation with remote command usage

**Files to modify:**
- `picard/remotecommands/handlers.py` - add plugin commands

**Usage:**
```bash
# Enable plugin in running Picard
picard -e "PLUGIN_ENABLE listenbrainz"

# Show runtime status
picard -e "PLUGIN_STATUS listenbrainz"
```

**Acceptance criteria:**
- Can enable/disable plugins without restart
- Can view runtime plugin state
- Commands work with running Picard instance

---

### 2.4 Migration from Legacy Plugins

**Priority:** P1 - High
**Effort:** 3-4 days

**Tasks:**
- [ ] Write comprehensive migration guide
- [ ] Create automated migration script (`picard-plugin-migrate`)
- [ ] Test migration script on popular v2 plugins
- [ ] Document breaking changes
- [ ] Create before/after examples
- [ ] Provide migration checklist
- [ ] Announce breaking change to plugin developers
- [ ] Offer migration assistance to popular plugin authors

**Files to create:**
- `scripts/migrate-plugin.py` - Migration tool

See [MIGRATION.md](MIGRATION.md) for complete migration guide.

---

## Phase 3: Official Plugin Repository

**Goal:** Centralized plugin discovery and distribution.

### 3.1 Website Plugin Registry API

**Priority:** P2 - Medium
**Effort:** 4-5 days

**Tasks:**
- [ ] Design registry JSON schema
- [ ] Implement registry generation from plugin repositories
- [ ] Add trust level system (official/trusted/community)
- [ ] Add blacklist management
- [ ] Extract translations from MANIFEST.toml
- [ ] Implement caching and versioning
- [ ] Create admin interface

See [REGISTRY.md](REGISTRY.md) and [WEBSITE.md](WEBSITE.md) for details.

---

### 3.2 Picard Client Integration

**Priority:** P2 - Medium
**Effort:** 3-4 days

**Tasks:**
- [ ] Implement `PluginRegistry` class
- [ ] Fetch and cache registry JSON
- [ ] Add trust level checking
- [ ] Show trust level badges in UI
- [ ] Implement repository-level blacklist patterns

See [REGISTRY.md](REGISTRY.md) for client integration details.

---

### 3.3 Enhanced CLI Commands

**Priority:** P2 - Medium
**Effort:** 2 days

**Tasks:**
- [ ] Add `--browse` command to list official plugins
- [ ] Add `--search <query>` command
- [ ] Add `--install <plugin-id>` (install by name from registry)
- [ ] Add `--filter` options (category, trust level)
- [ ] Show plugin ratings/downloads if available

See [CLI.md](CLI.md) for command specifications.

---

### 3.4 Blacklist Enforcement

**Priority:** P1 - High (Security)
**Effort:** 1 day

**Tasks:**
- [ ] Check blacklist on startup
- [ ] Disable blacklisted plugins automatically
- [ ] Show warning to user
- [ ] Support repository-level wildcard patterns

---

## Phase 4: GUI

**Goal:** User-friendly plugin management in Picard UI.

### 4.1 Options Page

**Priority:** P3 - Low
**Effort:** 5-7 days

**Tasks:**
- [ ] Create new plugin options page
- [ ] List installed plugins with enable/disable toggles
- [ ] Add install/uninstall buttons
- [ ] Show plugin details panel
- [ ] Add update notifications
- [ ] Integrate with registry for browsing
- [ ] Show trust level badges

---

## Success Metrics

### Phase 1 Complete When:
- [ ] Can install plugin from git URL
- [ ] Can enable/disable plugin
- [ ] Plugin state persists across restarts
- [ ] Can update plugins
- [ ] Can uninstall plugins
- [ ] Incompatible plugins are rejected
- [ ] Blacklisted plugins are blocked (with override option)
- [ ] All operations have proper error handling
- [ ] CLI provides useful feedback

### Phase 2 Complete When:
- [ ] Test coverage >80%
- [ ] Documentation complete
- [ ] Migration guide published
- [ ] No known critical bugs

### Phase 3 Complete When:
- [ ] Website serves plugin registry JSON
- [ ] Picard fetches and caches registry
- [ ] Can browse official plugins via CLI
- [ ] Can search official plugins
- [ ] Can install official plugins by name
- [ ] Blacklist is enforced on install and startup
- [ ] Admin interface exists for managing plugins/blacklist

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1.1 | 2-3 days | None |
| Phase 1.2 | 1 day | None |
| Phase 1.3 | 2 days | 1.1, 1.2 |
| Phase 1.4 | 1-2 days | 1.1 |
| Phase 1.5 | 1 day | 1.1 |
| Phase 1.6 | 1-2 days | None |
| Phase 1.7 | 1 day | 1.1 |
| Phase 1.8 | 1 day | None |
| **Phase 1 Total** | **10-13 days** | |
| Phase 2 | 5-6 days | Phase 1 |
| **MVP Total** | **15-19 days** | |
| Phase 3 | 6-9 days | Phase 2 |
| **Full CLI Total** | **21-28 days** | |
| Phase 4 | 5-7 days | Phase 3 |
| **Complete System** | **26-35 days** | |

---

## Next Actions

### Immediate (This Week)
1. **Merge phw/plugins-v3-cli into phw/plugins-v3** - consolidate branches
2. **Implement Phase 1.1** - config persistence (blocker for everything else)
3. **Implement Phase 1.2** - version checking (safety critical)

### Short Term (Next 2 Weeks)
4. Implement Phase 1.3 - better CLI output
5. Implement Phase 1.4 - updates
6. Implement Phase 1.5 - state management

### Medium Term (Next Month)
7. Complete Phase 1 (1.6, 1.7, 1.8)
8. Start Phase 2 - testing and docs

---

## Notes

- Focus on CLI-only for now - GUI can wait
- Prioritize robustness over features
- Make decisions on open questions as needed, document them in [DECISIONS.md](DECISIONS.md)
- Keep implementation simple - can enhance later
- Test with real plugins early and often
- See [SECURITY.md](SECURITY.md) for security model rationale
