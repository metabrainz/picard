# Picard Plugin v3 Development Roadmap

**Document Version:** 1.1
**Last Updated:** 2025-11-26
**Status:** Phase 1 Complete, Phase 2 In Progress

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
| `plugins_roadmap` | - | Active | Phase 1 complete - full CLI implementation with all features |
| `phw/plugins-v3` | phw | Merged | Core plugin infrastructure (merged into plugins_roadmap) |
| `phw/plugins-v3-cli` | phw | Merged | Basic CLI implementation (merged into plugins_roadmap) |
| `master` | - | Stable | Production code with legacy plugin system |

### What Works Now (Phase 1 Complete ✅)

**Core Infrastructure:**
- ✅ Plugin discovery from `plugins3/` directory
- ✅ MANIFEST.toml parsing with metadata and translations
- ✅ PluginApi with all major extension points
- ✅ Plugin loading and module execution with logging
- ✅ Git-based plugin sources (pygit2) with ref/branch/tag support
- ✅ Comprehensive unit tests (101 tests, all passing)
- ✅ Test helpers for reduced code duplication

**Configuration & State Management:**
- ✅ Config persistence - plugins remember enabled/disabled state across restarts
- ✅ Plugin metadata storage (URL, ref, commit ID)
- ✅ Plugin state tracking (DISCOVERED, LOADED, ENABLED, DISABLED, ERROR)
- ✅ State transition validation (prevent double-enable/disable)

**CLI Commands:**
- ✅ `picard-plugins --list` - List all plugins with details
- ✅ `picard-plugins --info <name>` - Show detailed plugin information and status
- ✅ `picard-plugins --install <url>` - Install from git URL
- ✅ `picard-plugins --install <url> --ref <branch|tag|commit>` - Install specific ref
- ✅ `picard-plugins --uninstall <name>` - Uninstall with config cleanup prompt
- ✅ `picard-plugins --uninstall <name> --purge` - Uninstall and delete config
- ✅ `picard-plugins --enable <name>` - Enable plugin
- ✅ `picard-plugins --disable <name>` - Disable plugin
- ✅ `picard-plugins --update <name>` - Update plugin to latest version
- ✅ `picard-plugins --update-all` - Update all plugins
- ✅ `picard-plugins --check-updates` - Check for available updates
- ✅ `picard-plugins --switch-ref <name> <ref>` - Switch to different git ref
- ✅ `picard-plugins --clean-config <name>` - Delete plugin configuration
- ✅ `picard-plugins --reinstall` - Force reinstall flag
- ✅ `picard-plugins --yes` - Skip confirmation prompts
- ✅ `picard-plugins --force-blacklisted` - Bypass blacklist (dangerous!)

**Features:**
- ✅ API version compatibility checking (rejects incompatible plugins)
- ✅ Enhanced CLI output with colors, success/error indicators
- ✅ Exit codes (SUCCESS=0, ERROR=1, NOT_FOUND=2, CANCELLED=130)
- ✅ Plugin updates without uninstall/reinstall
- ✅ Version change tracking (old → new)
- ✅ Git commit tracking
- ✅ Plugin directory naming with full UUID (guarantees uniqueness)
- ✅ Two-stage install with validation and cleanup on failure
- ✅ Duplicate installation prevention
- ✅ Security blacklist checking (URL, pattern, plugin ID)
- ✅ Automatic blacklist enforcement on startup
- ✅ Plugin initialization logging for debugging

**Security:**
- ✅ PluginRegistry with blacklist support
- ✅ Pre-install URL blacklist check
- ✅ Post-MANIFEST plugin ID blacklist check
- ✅ Startup blacklist check (auto-disable blacklisted plugins)
- ✅ Registry caching to reduce network requests
- ✅ Pattern matching for repository-level blacklists

### What Doesn't Work Yet

**Phase 2 - Polish & Robustness:**
- ⏳ Comprehensive error handling for all edge cases
- ⏳ Full test coverage (>80%)
- ⏳ Complete documentation
- ⏳ Migration guide and tooling
- ⏳ Remote commands for hot-reload

**Phase 3 - Official Plugin Repository:**
- ⏳ Website plugin registry generation
- ⏳ Trust level system (official/trusted/community)
- ⏳ Plugin browsing and search
- ⏳ Install by plugin name from registry

**Phase 4 - GUI:**
- ⏳ Plugin options page in Picard UI
- ⏳ Visual plugin management
- ⏳ Update notifications

---

## Phase 1: Functional CLI-Only System ✅ COMPLETE

**Goal:** Make plugin system usable for developers and power users via CLI only.

**Status:** ✅ All tasks complete (2025-11-25)
**Test Coverage:** 37 tests, all passing
**Commits:** 8 implementation commits

### 1.1 Configuration Persistence ✅ COMPLETE

**Priority:** P0 - Blocker
**Effort:** 2-3 days (Actual: 1 day)

**Tasks:**
- ✅ Add `plugins3` section to config schema
- ✅ Store enabled plugin list: `config.setting['plugins3']['enabled_plugins'] = []`
- ✅ Store plugin metadata: URL, git ref, commit ID
- ✅ Implement `PluginManager._save_config()` / `_load_config()`
- ✅ Update `enable_plugin()` to persist state
- ✅ Update `disable_plugin()` to persist state
- ✅ Update `init_plugins()` to only load enabled plugins

**Files modified:**
- `picard/plugin3/manager.py` - added config load/save methods
- `test/test_plugins3.py` - added persistence tests

**Acceptance criteria:**
- ✅ Enabled plugins survive restart
- ✅ Disabled plugins don't load on startup
- ✅ Config file contains plugin state

---

### 1.2 Version Compatibility Checking ✅ COMPLETE

**Priority:** P0 - Blocker
**Effort:** 1 day (Actual: 1 day)

**Tasks:**
- ✅ Implement API version compatibility check in `_load_plugin()`
- ✅ Add detailed logging for incompatible plugins
- ✅ Skip loading incompatible plugins
- ✅ Show compatibility status in `--list` output

**Files modified:**
- `picard/plugin3/manager.py` - enhanced `_load_plugin()` with version checking
- `test/test_plugins3.py` - added compatibility tests

**Acceptance criteria:**
- ✅ Plugins with wrong API version don't load
- ✅ Clear error message explains why
- ✅ User can see which API versions plugin requires

---

### 1.3 Enhanced CLI Output & Error Handling ✅ COMPLETE

**Priority:** P1 - High
**Effort:** 2 days (Actual: 1 day)

**Tasks:**
- ✅ Improve `--list` output: show version, status, API versions, description
- ✅ Add `--info <name>` command to show full plugin details
- ✅ Add error handling for all operations
- ✅ Add confirmation prompts for destructive operations
- ✅ Add `--yes` flag to skip confirmations
- ✅ Return proper exit codes (ExitCode enum: SUCCESS, ERROR, NOT_FOUND, CANCELLED)
- ✅ Add clear messages that changes require Picard restart
- ✅ Create PluginOutput wrapper with color support

**Files modified:**
- `picard/plugin3/cli.py` - enhanced all methods with PluginOutput
- `picard/plugin3/output.py` - created output wrapper with colors
- `picard/tagger.py` - added --info argument

**Note:** Phase 1 commands modify config/files only. Changes take effect on Picard restart. Remote commands for hot-reload will be added in Phase 2.

---

### 1.4 Plugin Updates ✅ COMPLETE

**Priority:** P1 - High
**Effort:** 1-2 days (Actual: 1 day)

**Tasks:**
- ✅ Add `--update <name>` command to update single plugin
- ✅ Add `--update-all` command to update all plugins
- ✅ Add `--check-updates` command to check without installing
- ✅ Store git remote URL, ref, and commit in config metadata
- ✅ Implement `PluginSourceGit.update()` method (fetch + reset)
- ✅ Show what changed (old version → new version, commit hashes)
- ✅ Handle update failures gracefully

**Files modified:**
- `picard/plugin3/cli.py` - added update commands
- `picard/plugin3/manager.py` - added update_plugin(), update_all_plugins(), check_updates()
- `picard/plugin3/plugin.py` - added update() method to PluginSourceGit
- `picard/tagger.py` - added update arguments

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
---

### 1.5 Plugin State Management ✅ COMPLETE

**Priority:** P1 - High
**Effort:** 1 day (Actual: 1 day)

**Tasks:**
- ✅ Add plugin state enum: `DISCOVERED`, `LOADED`, `ENABLED`, `DISABLED`, `ERROR`
- ✅ Track state in `Plugin` class
- ✅ Prevent double-enable, double-disable with ValueError
- ✅ State information integrated into `--info` and `--list` commands
- ✅ Log state transitions

**Files modified:**
- `picard/plugin3/plugin.py` - added PluginState enum and state tracking
- `picard/plugin3/manager.py` - added state transition logging
- `picard/plugin3/cli.py` - enhanced --info and --list to show state
- `picard/tagger.py` - updated argument parser

---

### 1.6 Git Ref/Branch Support ✅ COMPLETE

**Priority:** P2 - Medium
**Effort:** 1-2 days (Actual: 1 day)

**Goal:** Allow developers to install and test specific branches, tags, or commits.

**Tasks:**
- ✅ Add `--ref <branch|tag|commit>` option to install command
- ✅ Store ref in config per plugin
- ✅ Update to specific ref
- ✅ Show current ref in `--list` and `--info`
- ✅ Add `--switch-ref <plugin> <ref>` command to change ref without reinstalling
- ✅ Handle ref changes on update
- ✅ Support local git repositories for development

**Files modified:**
- `picard/plugin3/cli.py` - added --ref argument and --switch-ref command
- `picard/plugin3/plugin.py` - passed ref to PluginSourceGit
- `picard/plugin3/manager.py` - added switch_ref() method, stored ref in config
- `picard/tagger.py` - added --ref and --switch-ref arguments

**Usage examples:**
```bash
# Install from specific branch
picard-plugins --install https://github.com/user/plugin --ref dev

# Install from local git repository
picard-plugins --install ~/dev/my-plugin

# Switch to different ref
picard-plugins --switch-ref myplugin v1.0.0

# Update to latest on current ref
picard-plugins --update myplugin
```

**Acceptance criteria:**
- ✅ Can install from any branch, tag, or commit
- ✅ Can install from local git repositories
- ✅ Can switch between refs without reinstalling
- ✅ Config stores current ref and commit
- ✅ List/info shows ref information

---

### 1.7 Better Install Logic ✅ COMPLETE

**Priority:** P2 - Medium
**Effort:** 1 day (Actual: 1 day)

**Tasks:**
- ✅ Derive plugin name from MANIFEST.toml, not URL basename
- ✅ Use plugin ID from MANIFEST for directory name (after clone)
- ✅ Clone to temp directory first, then move to final location
- ✅ Check if plugin already installed before cloning
- ✅ Add `--reinstall` flag to force reinstall
- ✅ Validate MANIFEST.toml before completing install
- ✅ Clean up on install failure
- ✅ Add `--purge` flag for uninstall to delete configuration
- ✅ Prompt user during uninstall about configuration cleanup
- ✅ Add `--clean-config <name>` command for later cleanup
- ✅ Remove plugin metadata on uninstall

**Files modified:**
- `picard/plugin3/manager.py` - enhanced install_plugin() with two-stage install, added _clean_plugin_config()
- `picard/plugin3/cli.py` - added --purge, --clean-config, config cleanup prompts
- `picard/tagger.py` - added --reinstall, --purge, --yes, --clean-config arguments

**Community Feedback:**
> **rdswift (on directory naming):** "I agree with the recommendation to use the plugin ID from MANIFEST after clone, with the fallback to use URL basename."
>
> **rdswift (on config cleanup):** "I suggest a combination of options C and D. The process would allow the user to delete the configuration immediately by prompting upon uninstall, and allow for later deletion if the user changes their mind about their decision to keep the configuration during the uninstall."

**Plugin directory naming logic:**
1. ✅ Clone to temporary directory using URL basename
2. ✅ Read MANIFEST.toml to get plugin ID
3. ✅ Move directory to plugin ID location
4. ✅ Clean up temp directory on failure

**Configuration cleanup behavior:**
```bash
# Uninstall with prompt
$ picard-plugins --uninstall myplugin
Uninstalling myplugin...
Delete plugin configuration? [y/N] n
✓ Plugin uninstalled (configuration kept)

# Uninstall with purge flag
$ picard-plugins --uninstall myplugin --purge
Uninstalling myplugin and deleting configuration...
✓ Plugin and configuration removed

# Clean config later
$ picard-plugins --clean-config myplugin
Delete configuration for myplugin? [y/N] y
✓ Configuration deleted
```

---

### 1.8 Basic Blacklist Support ✅ COMPLETE (Safety Critical)

**Priority:** P1 - High (Security)
**Effort:** 1 day (Actual: 1 day)

**Tasks:**
- ✅ Add `PluginRegistry` class with blacklist checking
- ✅ Fetch plugin registry from website (with caching)
- ✅ Check blacklist before install (URL match)
- ✅ Check blacklist after MANIFEST read (plugin ID match)
- ✅ Show warning and refuse install if blacklisted
- ✅ Add `--force-blacklisted` flag to override (with big warning)
- ✅ Check installed plugins on startup, disable if blacklisted
- ✅ Support URL patterns (regex) for repository-level blacklists

**Files created:**
- `picard/plugin3/registry.py` - PluginRegistry class

**Files modified:**
- `picard/plugin3/manager.py` - added blacklist checks in install_plugin() and init_plugins()
- `picard/plugin3/cli.py` - added --force-blacklisted support with warning
- `picard/tagger.py` - added --force-blacklisted argument

**Security checks:**
1. ✅ Pre-install: Check URL against blacklist before cloning
2. ✅ Post-MANIFEST: Check plugin ID against blacklist after reading manifest
3. ✅ Startup: Check all installed plugins and auto-disable if blacklisted

**Note:** Full registry features (browse, search) come in Phase 3. This task only implements safety-critical blacklist checking.

See [REGISTRY.md](REGISTRY.md) for registry schema and [SECURITY.md](SECURITY.md) for security model.

---

## Phase 2: Polish & Robustness

**Goal:** Make CLI system production-ready.

### 2.1 Comprehensive Testing ✅ COMPLETE

**Priority:** P1 - High
**Effort:** 3-4 days (Actual: 4 days)
**Status:** ✅ Complete

**Tasks:**
- [x] Unit tests for all manager operations
- [x] Integration tests for CLI commands
- [x] Test error conditions (network failure, invalid manifest, etc.)
- [x] Test config persistence
- [x] Test version compatibility logic
- [x] Git integration tests with real repositories
- [x] MANIFEST validation tests
- [x] Translation system tests

**Implementation notes:**
- Split tests into 6 logical files for maintainability
- Added 82 comprehensive tests (75 core + 11 git + 3 validation + 3 translation)
- Test coverage: 76% overall
- Real git repository tests using pygit2
- MANIFEST validation with detailed error reporting
- Added `--validate` CLI command for plugin developers and registry maintainers

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
**Status:** ✅ Complete

**Tasks:**
- [x] Write comprehensive migration guide
- [x] Create automated migration script (`picard-plugin-migrate`)
- [x] Test migration script on popular v2 plugins
- [ ] Document breaking changes
- [ ] Create before/after examples
- [ ] Provide migration checklist
- [ ] Announce breaking change to plugin developers
- [ ] Offer migration assistance to popular plugin authors

**Files created:**
- `scripts/migrate-plugin.py` - Migration tool with TOML escaping, description splitting, PLUGIN_NAME replacement
- `test/test_plugins3_migration.py` - Comprehensive migration tests

**Implementation notes:**
- Migration tool extracts V2 metadata (PLUGIN_*) and generates V3 MANIFEST.toml
- Automatically escapes quotes/backslashes in TOML strings
- Splits long descriptions (>200 chars) into description + long_description fields
- Replaces all PLUGIN_NAME references with actual plugin name string
- Converts register_*_processor() calls to enable(api) function
- Successfully tested with abbreviate_artistsort V2 plugin
- Validates generated MANIFEST.toml to ensure compliance

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

### 3.2 Picard Client Integration ✅ COMPLETE

**Priority:** P2 - Medium
**Effort:** 3-4 days (Actual: 1 day)
**Status:** ✅ Complete

**Tasks:**
- [x] Implement `PluginRegistry` class
- [x] Fetch and cache registry TOML
- [x] Add trust level checking
- [ ] Show trust level badges in UI (Phase 4)
- [x] Implement repository-level blacklist patterns

**Implementation notes:**
- PluginRegistry class with full trust level support
- get_trust_level() returns official/trusted/community/unregistered
- find_plugin() searches by ID or URL
- list_plugins() with category and trust level filters
- Trust levels: official (🛡️), trusted (✓), community (⚠️), unregistered (🔓)
- 85 tests passing (82 + 3 new registry tests)

See [REGISTRY.md](REGISTRY.md) for client integration details.

---

### 3.3 Enhanced CLI Commands ✅ COMPLETE

**Priority:** P2 - Medium
**Effort:** 2 days (Actual: 1 day)
**Status:** ✅ Complete

**Tasks:**
- [x] Add `--browse` command to list official plugins
- [x] Add `--search <query>` command
- [x] Add `--install <plugin-id>` (install by name from registry)
- [x] Add `--filter` options (category, trust level)
- [ ] Show plugin ratings/downloads if available (not available yet)

**Implementation notes:**
- --browse lists plugins with optional --category and --trust filters
- --search performs case-insensitive search in name/description/ID
- --install now accepts plugin IDs and looks them up in registry
- Trust level badges: 🛡️ official, ✓ trusted, ⚠️ community, 🔓 unregistered
- 89 tests passing (85 + 4 new CLI tests)

See [CLI.md](CLI.md) for command specifications.

---

### 3.4 Blacklist Enforcement ✅ COMPLETE

**Priority:** P1 - High (Security)
**Effort:** 1 day (Actual: 1 day)
**Status:** ✅ Complete

**Tasks:**
- [x] Check blacklist on startup
- [x] Disable blacklisted plugins automatically
- [x] Show warning to user
- [x] Support repository-level wildcard patterns

**Implementation notes:**
- _check_blacklisted_plugins() runs on startup via init_plugins()
- Automatically disables blacklisted plugins and saves config
- Shows QMessageBox warning with plugin names and reasons
- Supports URL exact match, URL pattern (regex), and plugin ID blacklisting
- 90 tests passing (89 + 1 new blacklist warning test)

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

### Phase 1 Complete
- [ ] Can install plugin from git URL
- [ ] Can enable/disable plugin
- [ ] Plugin state persists across restarts
- [ ] Can update plugins
- [ ] Can uninstall plugins
- [ ] Incompatible plugins are rejected
- [ ] Blacklisted plugins are blocked (with override option)
- [ ] All operations have proper error handling
- [ ] CLI provides useful feedback

### Phase 2 Complete
- [ ] Test coverage >80%
- [ ] Documentation complete
- [ ] Migration guide published
- [ ] No known critical bugs

### Phase 3 Complete
- [ ] Website serves plugin registry TOML
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
1. Implement Phase 1.3 - better CLI output
2. Implement Phase 1.4 - updates
3. Implement Phase 1.5 - state management

### Medium Term (Next Month)
1. Complete Phase 1 (1.6, 1.7, 1.8)
2. Start Phase 2 - testing and docs

---

## Notes

- Focus on CLI-only for now - GUI can wait
- Prioritize robustness over features
- Make decisions on open questions as needed, document them in [DECISIONS.md](DECISIONS.md)
- Keep implementation simple - can enhance later
- Test with real plugins early and often
- See [SECURITY.md](SECURITY.md) for security model rationale
