# Plugin Registry System

This document describes the plugin registry JSON schema, trust levels, blacklist system, and client integration.

---

## Overview

The plugin registry is a centralized JSON file served by the Picard website that contains:
- List of official, trusted, and community plugins
- Plugin metadata (name, description, authors, etc.)
- Trust level assignments
- Blacklist of malicious/broken plugins
- Translations for plugin names and descriptions

**Registry URL:** `https://picard.musicbrainz.org/api/v3/plugins.json`

**Configuration:**
- Default URL is defined in `DEFAULT_PLUGIN_REGISTRY_URL` constant in `picard/const/defaults.py`
- Can be overridden via environment variable: `PICARD_PLUGIN_REGISTRY_URL`
- Useful for testing, development, or using alternative registries

**Example:**
```bash
# Use custom registry URL
export PICARD_PLUGIN_REGISTRY_URL="https://test.example.com/plugins.json"
picard plugins --browse

# Use local registry file for testing
export PICARD_PLUGIN_REGISTRY_URL="file:///path/to/local/registry.json"
picard plugins --install my-plugin
```

---

## Registry JSON Schema

### Top-Level Structure

```json
{
  "api_version": "3.0",
  "last_updated": "2025-11-24T15:30:00Z",
  "plugins": [ /* array of plugin objects */ ],
  "blacklist": [ /* array of blacklist entries */ ]
}
```

### Plugin Entry

```json
{
  "id": "listenbrainz",
  "uuid": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "ListenBrainz Submitter",
  "description": "Submit your music to ListenBrainz",
  "name_i18n": {
    "de": "ListenBrainz-Submitter",
    "fr": "Soumetteur ListenBrainz",
    "ja": "ListenBrainzサブミッター"
  },
  "description_i18n": {
    "de": "Submit listens deine Musik zu ListenBrainz",
    "fr": "Submit listensz votre musique sur ListenBrainz",
    "ja": "ListenBrainzに音楽をスクロブルする"
  },
  "git_url": "https://github.com/metabrainz/picard-plugin-listenbrainz",
  "refs": [
    {
      "name": "main",
      "description": "Stable release for Picard 4.x",
      "min_api_version": "4.0"
    },
    {
      "name": "picard-v3",
      "description": "Maintenance branch for Picard 3.x",
      "min_api_version": "3.0",
      "max_api_version": "3.99"
    }
  ],
  "categories": ["metadata"],
  "trust_level": "official",
  "authors": ["Philipp Wolfer"],
  "maintainers": ["Philipp Wolfer"],
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-24T15:00:00Z"
}
```

**Plugin Identity:**
- Plugins are uniquely identified by **UUID** (from MANIFEST.toml)
- The `id` field is a human-readable short identifier for CLI/URL usage
- The `git_url` specifies where to fetch the plugin (can change via redirects)
- Together, UUID + git_url provide stable identity and source tracking

**Git Refs:**
- The `refs` field specifies which git branches/tags are available for the plugin
- If omitted, defaults to `[{"name": "main"}]`
- First ref in array is the default for new installations
- Picard auto-selects compatible ref based on API version
- Users can explicitly choose a different ref with `--ref` flag

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Short identifier for CLI/URL usage (lowercase, alphanumeric + hyphens) |
| `uuid` | string | Yes | Unique plugin identifier (UUID v4 from MANIFEST.toml) |
| `name` | string | Yes | Display name of the plugin (English) |
| `description` | string | Yes | Short description (one line, English) |
| `name_i18n` | object | No | Translated names (locale → string) |
| `description_i18n` | object | No | Translated descriptions (locale → string) |
| `git_url` | string | Yes | Git repository URL (https) |
| `refs` | array | No | Git refs (branches/tags) available for this plugin (defaults to `[{"name": "main"}]`). Each ref can have `min_api_version` and `max_api_version` fields. |
| `categories` | array | Yes | Plugin categories |
| `trust_level` | string | Yes | Trust level: `official`, `trusted`, or `community` |
| `authors` | array | No | Plugin author/contributor names (from MANIFEST.toml) |
| `maintainers` | array | No | Plugin maintainer names (from MANIFEST.toml) |
| `added_at` | string | Yes | ISO 8601 timestamp when added to registry |
| `updated_at` | string | Yes | ISO 8601 timestamp of last update |

**Note:** API version constraints (`min_api_version`, `max_api_version`) are specified per-ref within the `refs` array, not at the top level. This allows different branches to support different Picard versions.

### Categories

Valid category values:
- `metadata` - Metadata providers and processors
- `coverart` - Cover art providers
- `ui` - User interface enhancements
- `scripting` - Script functions and variables
- `formats` - File format support
- `other` - Miscellaneous

---

## Git Refs

The `refs` field allows plugins to specify multiple git branches or tags that users can install from. This enables:
- **Beta testing channels** - Users can opt into beta/development versions
- **Smooth major version transitions** - Maintain separate branches for different Picard versions
- **Flexible branch naming** - No assumptions about `main` vs `master` vs custom names

### Refs Field Structure

```json
{
  "refs": [
    {
      "name": "main",
      "description": "Stable release for Picard 4.x",
      "min_api_version": "4.0"
    },
    {
      "name": "beta",
      "description": "Testing new features",
      "min_api_version": "4.0"
    }
  ]
}
```

**Ref Object Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Git ref name (branch or tag) |
| `description` | string | No | Human-readable description of this ref |
| `min_api_version` | string | No | Minimum Picard API version for this ref |
| `max_api_version` | string | No | Maximum Picard API version for this ref |

### Default Behavior

If `refs` is omitted, it defaults to:
```json
{
  "refs": [{"name": "main"}]
}
```

This means most plugins don't need to specify `refs` explicitly.

### Examples

**Simple plugin (uses defaults):**
```json
{
  "id": "simple-plugin",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "git_url": "https://github.com/user/plugin",
  "categories": ["metadata"],
  "trust_level": "community",
  "authors": ["Plugin Author"],
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-24T15:00:00Z"
  // refs omitted, defaults to [{"name": "main"}]
}
```

**Plugin using master branch:**
```json
{
  "id": "old-plugin",
  "uuid": "650e8400-e29b-41d4-a716-446655440001",
  "git_url": "https://github.com/user/plugin",
  "refs": [{"name": "master"}],
  "categories": ["metadata"],
  "trust_level": "community",
  "authors": ["Plugin Author"],
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-24T15:00:00Z"
}
```

**Plugin with beta channel:**
```json
{
  "id": "my-plugin",
  "uuid": "750e8400-e29b-41d4-a716-446655440002",
  "git_url": "https://github.com/user/plugin",
  "refs": [
    {
      "name": "stable",
      "description": "Stable releases only"
    },
    {
      "name": "beta",
      "description": "Testing new features (may be unstable)"
    }
  ],
  "categories": ["metadata"],
  "trust_level": "community",
  "authors": ["Plugin Author"],
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-24T15:00:00Z"
}
```

**Plugin supporting multiple Picard versions:**
```json
{
  "id": "my-plugin",
  "uuid": "850e8400-e29b-41d4-a716-446655440003",
  "git_url": "https://github.com/user/plugin",
  "refs": [
    {
      "name": "main",
      "description": "For Picard 4.x and later",
      "min_api_version": "4.0"
    },
    {
      "name": "picard-v3",
      "description": "Maintenance branch for Picard 3.x",
      "min_api_version": "3.0",
      "max_api_version": "3.99"
    }
  ],
  "categories": ["metadata"],
  "trust_level": "community",
  "authors": ["Plugin Author"],
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-24T15:00:00Z"
}
```

### Client Behavior

**Auto-selection:**
When installing a plugin, Picard automatically selects the most appropriate ref based on the current Picard API version:

```bash
# Picard 3.x user
$ picard plugins --install my-plugin
# Auto-selects 'picard-v3' branch

# Picard 4.x user
$ picard plugins --install my-plugin
# Auto-selects 'main' branch
```

**Explicit selection:**
Users can override auto-selection:

```bash
# Install from specific ref
$ picard plugins --install my-plugin --ref beta

# List available refs
$ picard plugins --info my-plugin
# Shows: Available refs: main (default), beta, picard-v3

# Switch to different ref
$ picard plugins --switch-ref my-plugin beta
```

**Update behavior:**
- Updates only check the currently installed ref
- To switch refs, use `--switch-ref` command
- Each ref is tracked independently

### Use Cases

**1. Smooth Major Version Transitions**

When Picard releases a new major version with breaking API changes, plugin authors can maintain separate branches:

```json
{
  "refs": [
    {
      "name": "main",
      "description": "For Picard 4.x",
      "min_api_version": "4.0"
    },
    {
      "name": "picard-v3-stable",
      "description": "For Picard 3.x (bug fixes only)",
      "min_api_version": "3.0",
      "max_api_version": "3.99"
    }
  ]
}
```

Users on Picard 3.x continue receiving bug fixes on the `picard-v3-stable` branch, while users on Picard 4.x get new features on `main`.

**2. Beta Testing**

Plugin authors can offer beta versions for testing:

```json
{
  "refs": [
    {
      "name": "stable",
      "description": "Stable releases"
    },
    {
      "name": "beta",
      "description": "Beta releases (may contain bugs)"
    }
  ]
}
```

Power users can opt into beta testing with `--ref beta`.

**3. Custom Branch Names**

Plugins can use any branch naming convention:

```json
{
  "refs": [
    {"name": "master"},      // Old GitHub default
    {"name": "develop"},     // Gitflow workflow
    {"name": "trunk"}        // Some projects use this
  ]
}
```

No assumptions are made about branch names - the plugin author explicitly declares what's available.

### Validation

The registry validates that all refs exist in the repository:
- Registry generation tool fetches MANIFEST.toml from each ref
- Each ref can have its own MANIFEST.toml with different metadata
- If any ref is missing or has invalid MANIFEST.toml, the plugin is rejected
- This ensures users can always install from listed refs

**Important:** Each ref's MANIFEST.toml is independent:
- The `main` branch might have `api = ["4.0"]`
- The `picard-v3` branch might have `api = ["3.0", "3.1"]`
- The registry stores API version constraints per ref, not globally

**Example workflow:**
```bash
# Registry tool fetches MANIFEST.toml from each ref
./registry plugin add https://github.com/user/plugin --refs 'main,picard-v3'

# Fetches and validates:
# - https://github.com/user/plugin/main/MANIFEST.toml
# - https://github.com/user/plugin/picard-v3/MANIFEST.toml

# If main/MANIFEST.toml has: api = ["4.0"]
# And picard-v3/MANIFEST.toml has: api = ["3.0", "3.1"]
# Then registry stores:
{
  "refs": [
    {"name": "main", "min_api_version": "4.0"},
    {"name": "picard-v3", "min_api_version": "3.0", "max_api_version": "3.1"}
  ]
}
```

---

## Trust Levels

The registry categorizes plugins into **three trust levels**. A fourth level (`unregistered`) is used client-side for plugins not in the registry.

### 1. Official (`official`)

**Definition:** Plugins maintained by the MusicBrainz Picard team

**Characteristics:**
- Repository under `metabrainz` or `musicbrainz` GitHub organizations
- Full code review by Picard team before acceptance
- Updates reviewed before being listed
- Highest trust level
- No warnings on install

**Badge:** 🛡️ "Official"

**Examples:**
- ListenBrainz plugin
- AcoustID plugin
- Cover Art Archive plugin

### 2. Trusted (`trusted`)

**Definition:** Plugins by well-known authors with established reputation

**Characteristics:**
- Long-term contributors to Picard or MusicBrainz
- History of quality plugins
- Manually approved by Picard team
- NOT reviewed by Picard team
- Updates automatically listed (no review)
- Minimal warning on first install

**Badge:** ✓ "Trusted"

**Examples:**
- Plugins by Bob Swift (rdswift)
- Plugins by Philipp Wolfer (phw)
- Plugins by other long-term contributors

### 3. Community (`community`)

**Definition:** Plugins by other authors

**Characteristics:**
- Valid MANIFEST.toml
- Not blacklisted
- Submitted to registry
- NOT reviewed
- Updates automatically listed
- Clear warning on install

**Badge:** ⚠️ "Community"

**Examples:**
- New plugins by unknown authors
- Experimental plugins
- Personal/niche plugins

### 4. Unregistered (`unregistered`) - Client-side Only

**Definition:** Plugins not in the official registry

**Important:** This trust level does NOT appear in the registry JSON. It's assigned by Picard client-side when a plugin's git URL is not found in the registry.

**Characteristics:**
- URL not found in registry
- Could be in development
- Could be from unknown source
- Could be private/personal plugin
- NOT reviewed
- Not tracked by registry
- Strongest warning on install

**Badge:** 🔓 "Unregistered"

**Use cases:**
- Developer testing during development
- Private company plugins
- Personal forks
- Experimental proof-of-concept plugins

---

## Blacklist System

### Blacklist Entry Types

**By UUID (recommended):**
```json
{
  "uuid": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "reason": "Contains malicious code",
  "blacklisted_at": "2025-11-20T10:00:00Z"
}
```

**By URL:**
```json
{
  "url": "https://github.com/badactor/malicious-plugin",
  "reason": "Contains malicious code",
  "blacklisted_at": "2025-11-20T10:00:00Z"
}
```

**By URL regex:**
```json
{
  "url_regex": "^https://github\\.com/badorg/.*",
  "reason": "Entire organization blacklisted for malicious activity",
  "blacklisted_at": "2025-11-22T10:00:00Z"
}
```

### Blacklist Methods Comparison

| Method | Purpose | Scope | Evasion Risk |
|--------|---------|-------|--------------|
| **UUID** | Block specific plugin | All sources, past and future | None - UUID is permanent |
| **url** | Block specific repository | Single URL only | High - can move repos |
| **url_regex** | Block organization/pattern | Multiple URLs matching regex | Medium - can change hosting |

**Recommendation**: Use **UUID** for blacklisting malicious plugins, as it blocks the plugin regardless of where it's hosted or if it moves repositories.

### Repository-Level Blacklisting

The blacklist supports regex patterns to block entire organizations:

```json
{
  "url_regex": "^https://github\\.com/badorg/.*",
  "reason": "Entire organization blacklisted for malicious activity",
  "blacklisted_at": "2025-11-22T10:00:00Z"
}
```

**Pattern matching:**
- **Specific URL:** `https://github.com/user/plugin` - blocks only that repository
- **Regex pattern:** `^https://github\.com/badorg/.*` - blocks all repositories from that organization
- Uses Python regex matching on normalized URLs

---

## Registry Redirects

### Purpose

Redirects handle plugin repository changes transparently:
- **Plugin moves repositories**: Author migrates from personal to organization account
- **Repository renamed**: GitHub/GitLab URL changes
- **Plugin reorganization**: Plugin moves into or out of monorepo
- **Ownership transfer**: Plugin transferred to new maintainer

### Redirect Entry

```json
{
  "uuid": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "id": "my-plugin",
  "git_url": "https://github.com/neworg/plugin-repo",
  "refs": [{"name": "main", "min_api_version": "3.0"}],
  "redirect_from": [
    "https://github.com/olduser/old-repo",
    "https://github.com/olduser/plugin-collection#my-plugin"
  ],
  "trust_level": "community",
  "authors": ["Author Name"],
  "categories": ["metadata"],
  "added_at": "2025-11-24T15:00:00Z",
  "updated_at": "2025-11-26T10:00:00Z"
}
```

### How Redirects Work

1. **User has old URL**: Plugin installed from `https://github.com/olduser/old-repo`
2. **Registry lookup**: Client checks registry for plugin by old URL
3. **Redirect found**: Registry returns new URL `https://github.com/neworg/plugin-repo`
4. **Transparent update**: Client fetches updates from new URL automatically
5. **Metadata updated**: Local metadata updated to track new URL

### Benefits

- **Seamless migration**: Users get updates without manual intervention
- **Centralized control**: Registry manages all URL changes
- **Audit trail**: Track plugin history and moves
- **No broken updates**: Old URLs continue to work

### UUID Role in Redirects

- **UUID remains constant** across repository moves
- Redirects map old URLs → new URL for same UUID
- Blacklist by UUID blocks plugin at all URLs (old and new)
- Prevents malicious plugins from evading blacklist by moving repos

### Implementation Notes

**Redirect Types:**

The registry supports two types of redirects:

1. **URL redirects** - Plugin moved to different repository:
```json
{
  "uuid": "a1b2c3d4-...",
  "git_url": "https://github.com/neworg/plugin",
  "redirect_from": [
    "https://github.com/olduser/plugin"
  ]
}
```

2. **UUID redirects** - Plugin was forked/replaced (rare):
```json
{
  "uuid": "new-uuid-...",
  "git_url": "https://github.com/org/plugin",
  "redirect_from_uuid": [
    "old-uuid-..."
  ]
}
```

**Lookup Algorithm:**

1. Search plugins by current UUID (exact match)
2. If not found, search plugins by current git_url (exact match)
3. If not found, search all plugins' `redirect_from` arrays for URL
4. If not found, search all plugins' `redirect_from_uuid` arrays for UUID
5. If found via redirect, update local metadata with current UUID/URL

**Registry Guarantees:**

- No circular redirects (registry validation prevents)
- No duplicate URLs in `redirect_from` across plugins
- Redirect chains limited to reasonable length (<50 hops)
- Registry always contains current metadata (current UUID, current URL)

**Client Behavior:**

- Registry refreshed: manually by user, periodically, or at Picard restart
- Redirects resolved transparently during update checks
- User notified if installed plugin moved (info message, non-blocking)
- Local metadata updated to track new UUID/URL after redirect

### Local Metadata Storage

When a plugin is installed or updated, Picard stores metadata locally in the configuration:

**Standard metadata:**
- `url`: Current git repository URL
- `ref`: Git ref (branch/tag/commit) being tracked
- `commit`: Current commit SHA
- `uuid`: Plugin UUID from MANIFEST

**Redirect tracking (added when redirect is followed):**
- `original_url`: The URL the plugin was originally installed from (before redirect)
- `original_uuid`: The UUID the plugin had when originally installed (before UUID redirect)

This allows users to:
- See the plugin's migration history
- Understand where the plugin came from originally
- Potentially rollback to original source if needed

**Example metadata after redirect:**
```json
{
  "test_plugin_a1b2c3d4": {
    "url": "https://github.com/neworg/plugin",
    "ref": "main",
    "commit": "def456...",
    "uuid": "new-uuid-5678",
    "original_url": "https://github.com/olduser/plugin",
    "original_uuid": "old-uuid-1234"
  }
}
```

---

## Client Integration

### PluginRegistry Class

```python
class PluginRegistry:
    REGISTRY_URL = "https://picard.musicbrainz.org/api/v3/plugins.json"
    CACHE_FILE = "plugin_registry.json"
    CACHE_TTL = 86400  # 24 hours

    # Registry trust levels (in registry JSON)
    REGISTRY_TRUST_LEVELS = ['official', 'trusted', 'community']

    # Client-side trust level values (includes unregistered for local plugins)
    TRUST_LEVELS = {
        'official': 3,      # Highest trust - in registry
        'trusted': 2,       # High trust - in registry
        'community': 1,     # Low trust - in registry
        'unregistered': 0   # Lowest trust - NOT in registry (client-side only)
    }

    def fetch_registry(self):
        """Fetch plugin list from website, use cache if fresh"""

    def is_blacklisted(self, git_url):
        """Check if git URL is blacklisted (supports patterns)"""
        registry = self.fetch_registry()
        for entry in registry.get('blacklist', []):
            blacklist_url = entry['url']
            # Check for exact match
            if blacklist_url == git_url:
                return True
            # Check for pattern match (e.g., https://github.com/badorg/*)
            if blacklist_url.endswith('/*'):
                pattern_base = blacklist_url[:-2]  # Remove /*
                if git_url.startswith(pattern_base + '/'):
                    return True
        return False

    def get_blacklist_reason(self, git_url):
        """Get reason for blacklisting (checks patterns too)"""
        registry = self.fetch_registry()
        for entry in registry.get('blacklist', []):
            blacklist_url = entry['url']
            # Check for exact match
            if blacklist_url == git_url:
                return entry
            # Check for pattern match
            if blacklist_url.endswith('/*'):
                pattern_base = blacklist_url[:-2]
                if git_url.startswith(pattern_base + '/'):
                    return entry
        return None

    def get_trust_level(self, git_url):
        """Get trust level for plugin by git URL"""
        plugin = self.find_plugin_by_url(git_url)
        if not plugin:
            return 'unregistered'
        return plugin.get('trust_level', 'community')

    def find_plugin(self, name_or_id):
        """Find official plugin by name or ID"""

    def list_official_plugins(self, category=None, trust_level=None):
        """List all official plugins, optionally filtered by category and trust level"""

    def should_warn_on_install(self, git_url):
        """Determine if warning should be shown based on trust level"""
        plugin = self.find_plugin_by_url(git_url)
        if not plugin:
            return True, "Plugin not in official registry (unregistered)"

        trust = plugin.get('trust_level')
        if trust == 'official':
            return False, None
        elif trust == 'trusted':
            return True, "not reviewed by Picard team"
        else:  # community
            return True, "not reviewed or endorsed by Picard team"
```

---

## Installation Warnings

### Official Plugin - No Warning

```bash
$ picard plugins --install listenbrainz
Installing ListenBrainz (Official)...
✓ Installed successfully
```

### Trusted Plugin - Minimal Warning

```bash
$ picard plugins --install discogs
Installing Discogs by Bob Swift (Trusted)...
Note: This plugin is not reviewed by the Picard team.
Continue? [Y/n] y
✓ Installed successfully
```

### Community Plugin - Clear Warning

```bash
$ picard plugins --install custom-tagger
Installing Custom Tagger by John Doe (Community)...

⚠️  WARNING: This plugin is not reviewed or endorsed by the Picard team.
   It may contain bugs or security issues.
   Only install if you trust the author.

Continue? [y/N] y
✓ Installed successfully
```

### Unregistered Plugin - Strongest Warning

```bash
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

---

## Caching Strategy

- Registry cached locally for 24 hours
- Cache file: `~/.local/share/MusicBrainz/Picard/plugin_registry.json`
- Automatic refresh on cache expiry
- Manual refresh: `picard plugins --refresh-registry`
- Fallback to cache if network unavailable

---

## Update Detection

The registry uses git refs to track and detect plugin updates. Unlike semantic versioning, updates are detected by comparing git commit hashes.

### How It Works

**1. Registry stores available refs**

Each plugin entry in `plugins.json` has a `refs` array listing available branches/tags. If omitted, defaults to `[{"name": "main"}]`.

**2. Local installation stores commit hash**

When a plugin is installed or updated, Picard records:
- The git URL
- The ref being tracked (e.g., `main`, `beta`, `v1.8.0`)
- The actual commit SHA that was fetched (e.g., `abc123def456...`)

**3. Update check process**

To check for updates:
1. Fetch the latest commit SHA for the installed ref from the remote repository
2. Compare it to the locally stored commit SHA
3. If different → update available

### Examples

**Branch tracking:**
```
Registry entry:
  git_url: https://github.com/user/plugin
  refs: [{"name": "main"}]  // or omitted (defaults to main)

Local installation:
  commit: abc123def456
  ref: main

Update check:
  $ git ls-remote https://github.com/user/plugin main
  → returns: def456789abc (different!)
  → Update available: abc123 -> def456 (5 commits ahead)
```

**Tag tracking:**
```
Registry entry:
  git_url: https://github.com/user/plugin
  refs: [{"name": "v1.8.0"}]

Local installation:
  commit: abc123def456
  ref: v1.8.0

Update check:
  $ git ls-remote --tags https://github.com/user/plugin
  → shows v1.9.0 exists (newer than v1.8.0)
  → Update available: v1.8.0 -> v1.9.0
```

### Update Display

The client displays updates differently based on ref type:

- **Branch refs:** Show commit hashes and commit count
  - Example: `abc123 -> def456 (5 commits)`

- **Tag refs:** Show tag names
  - Example: `v1.8.0 -> v1.9.0`

- **Mixed:** Show branch and commit
  - Example: `main @ 7d8e9f -> main @ 1a2b3c`

### Implementation Notes

**Checking for updates:**
```python
def check_for_updates(self, plugin):
    """Check if plugin has updates available"""
    local_commit = plugin.installed_commit
    local_ref = plugin.installed_ref
    git_url = plugin.git_url

    # Fetch latest commit for the ref
    remote_commit = git_ls_remote(git_url, local_ref)

    if remote_commit != local_commit:
        return {
            'available': True,
            'local': local_commit[:7],
            'remote': remote_commit[:7],
            'ref': local_ref
        }
    return {'available': False}
```

**Batch update checks:**
- Use `git ls-remote` to fetch all refs in one call
- Cache results to avoid repeated network requests
- Run checks in background to avoid blocking UI

---

## Translation Handling

The registry includes translations extracted from plugin MANIFEST.toml files:

**In MANIFEST.toml:**
```toml
name = "ListenBrainz Submitter"
description = "Submit your music to ListenBrainz"

[name_i18n]
de = "ListenBrainz-Submitter"
fr = "Soumetteur ListenBrainz"

[description_i18n]
de = "Submit listens deine Musik zu ListenBrainz"
fr = "Submit listensz votre musique sur ListenBrainz"
```

**In registry JSON:**
```json
{
  "name": "ListenBrainz Submitter",
  "description": "Submit your music to ListenBrainz",
  "name_i18n": {
    "de": "ListenBrainz-Submitter",
    "fr": "Soumetteur ListenBrainz"
  },
  "description_i18n": {
    "de": "Submit listens deine Musik zu ListenBrainz",
    "fr": "Submit listensz votre musique sur ListenBrainz"
  }
}
```

See [TRANSLATIONS.md](TRANSLATIONS.md) for details on the translation system.

---

## Trust Level Management

### Upgrading Trust Level

Using the registry CLI tool:

```bash
# Change trust level
registry plugin edit <plugin-id> --trust trusted

# Commit the change
git add plugins.json
git commit -m "Promote <plugin-id> to trusted"
git push
```

Process:
1. Review plugin code and history
2. Run `registry plugin edit <plugin-id> --trust <new-level>`
3. Commit and push to registry repository
4. Plugin trust level updates in registry
5. Users see new trust level on next registry refresh

### Promoting to Official

1. Plugin moved to `metabrainz` organization
2. Code reviewed by team
3. Run: `registry plugin edit <plugin-id> --trust official`
4. Commit and push
5. Plugin gets official badge

### Downgrading Trust Level

1. If plugin has security issue or quality problems
2. Run: `registry plugin edit <plugin-id> --trust community`
3. Commit and push
4. Users see appropriate warning on next update

**Note:** Trust level is per-plugin, not per-author. Same author can have plugins at different trust levels.

---

## See Also

- **[WEBSITE.md](WEBSITE.md)** - Website implementation for registry generation
- **[SECURITY.md](SECURITY.md)** - Security model rationale
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[CLI.md](CLI.md)** - CLI commands for browsing registry
