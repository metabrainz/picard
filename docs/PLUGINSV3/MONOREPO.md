# Multiple Plugins in Single Repository (Monorepo)

**Status**: Design Discussion
**Last Updated**: 2025-11-25

---

## Overview

Currently, the V3 plugin system assumes **one plugin per repository**. This document explores supporting **multiple plugins in a single repository** (monorepo pattern).

### Current State

```text
https://github.com/user/plugin.git
→ Installs one plugin
```

### Proposed Monorepo Support

```text
https://github.com/metabrainz/picard-plugins.git#lastfm
https://github.com/metabrainz/picard-plugins.git#bpm
→ Installs specific plugin from collection
```

---

## Pros

### Ecosystem Benefits
- **Matches existing pattern**: Official `picard-plugins` repo already has 73 plugins
- **Easier migration**: Can keep V2 repo structure
- **Familiar to developers**: Standard pattern in plugin ecosystems

### Maintenance Benefits
- **Single CI/CD pipeline** for all plugins
- **Shared tooling** and scripts
- **One place** for issues/PRs
- **Consistent versioning** across related plugins

### Organization Benefits
- **Thematic grouping**: Related plugins together (e.g., classical music plugins)
- **Shared dependencies**: Common utilities in one place
- **Reduced overhead**: Fewer repos to manage
- **Cross-plugin documentation**: Easier to maintain

### Discovery Benefits
- **Browse collections**: See all plugins from one source
- **Official collection**: Clear distinction
- **Related plugins**: Easier to find complementary plugins

---

## Cons

### Technical Complexity
- **URL syntax**: Need to specify which plugin (`#fragment` or `?plugin=name`)
- **Version management**: Individual plugin versions vs repo tags
- **Update granularity**: Pull entire repo for one plugin update
- **Larger downloads**: Can't fetch just one plugin's files

### Dependency Issues
- **Shared code**: If plugins share utilities, installation becomes complex
- **Testing matrix**: Changes affect multiple plugins
- **Breaking changes**: Shared code impacts all plugins

### Trust Model Complexity
- **Trust granularity**: Per-repo or per-plugin?
- **Mixed trust levels**: Official repo with community plugins?
- **Blacklist scope**: Block one plugin or entire repo?

### Registry Complexity
- **Indexing**: Must scan repos for plugins
- **Metadata structure**: More complex schema
- **Caching**: Harder to optimize

---

## Proposed Solution

### URL Syntax: Fragment Identifier

Use standard URL fragment to specify plugin:

```text
https://github.com/user/plugins.git#plugin-name
```

**Rationale**:
- Standard URL syntax
- Works with existing tools
- Clear and explicit
- Backward compatible (no fragment = single plugin)

### Auto-Detection

If repository contains only one plugin, fragment is optional:

```text
https://github.com/user/single-plugin.git
→ Auto-detects and installs the plugin
```

### Plugin Discovery

When cloning a repository:
1. Scan for `MANIFEST.toml` files recursively (up to 3 levels deep)
2. Identify all valid plugins
3. If no plugin specified and multiple found, list them
4. Require explicit selection for multi-plugin repos

---

## Hierarchical Trust Model

### Trust Level Rules

**Rule**: `effective_trust = min(repo_trust, plugin_trust)`

**Trust Levels** (highest to lowest):
1. **Official** (🛡️) - MusicBrainz maintained
2. **Trusted** (✓) - Verified developers
3. **Community** (⚠️) - Community contributions
4. **Untrusted** (🔓) - Not reviewed (default for new plugins)
5. **Unregistered** (❓) - Not in registry

### Key Principles

1. **Repository trust sets ceiling**: Plugin trust cannot exceed repo trust
2. **Explicit trust required**: New plugins default to untrusted
3. **Independent plugin trust**: Each plugin has its own trust level
4. **Security by default**: Must be explicitly marked as trusted

### Examples

| Repo Trust | Plugin Trust | Effective | Notes |
|------------|--------------|-----------|-------|
| Official | Official | Official | ✅ Fully trusted |
| Official | Community | Community | ⚠️ Community plugin in official repo |
| Official | (not set) | Untrusted | 🔓 New plugin, not reviewed |
| Community | Official | Community | ⚠️ Cannot escalate above repo |
| Trusted | Trusted | Trusted | ✓ Verified developer |
| (not registered) | Official | Unregistered | ❓ Repo not in registry |

### Benefits

- **Clear security boundaries**: Repo trust is maximum ceiling
- **Explicit review**: New plugins must be marked as trusted
- **Flexible official repo**: Can host community contributions
- **Defense in depth**: Two-level verification
- **Gradual trust**: Plugins can earn trust over time

---

## Registry Redirection

### Problem: Plugin Moves Between Repos

Plugin relocates from one repository to another.

### Solution: Registry Tracks Redirects

```json
{
  "id": "my-plugin",
  "url": "https://github.com/user/new-repo.git#my-plugin",
  "redirect_from": [
    "https://github.com/user/old-repo.git#my-plugin"
  ]
}
```

### Redirect Scenarios

1. **Plugin moves repos**: `repo-a.git#plugin` → `repo-b.git#plugin`
2. **Plugin renamed**: `repo.git#old-name` → `repo.git#new-name`
3. **Repo renamed**: GitHub handles automatically, registry tracks
4. **Plugin split**: One plugin becomes multiple
5. **Plugin merged**: Multiple plugins become one

### Benefits

- **Centralized control**: Registry manages redirects
- **Transparent**: Works automatically for users
- **Flexible**: Handles all reorganization patterns
- **Auditable**: Track plugin history

---

## Code Implications

### Changes Required

#### URL Parsing
- Parse fragment identifier from git URLs
- Extract plugin name from `#plugin-name`
- Handle URLs with and without fragments
- Validate fragment syntax

#### Plugin Discovery
- Recursive scan for `MANIFEST.toml` files
- Depth limit to prevent excessive scanning
- Ignore dotfiles and hidden directories
- Build plugin index from discovered manifests

#### Storage Structure
- Store plugin source metadata (repo URL + path)
- Track which plugins come from same repo
- Cache cloned repositories
- Map plugin ID to source location

#### Update Logic
- Fetch repo once for multiple plugins
- Extract only needed plugin directories
- Detect when plugins share source repo
- Optimize batch updates from same repo

#### Registry Schema
- Add `repository` and `path` fields
- Support `redirect_from` array
- Store per-plugin trust levels
- Index by both plugin ID and URL

#### Trust Level Resolution
- Query repo trust level
- Query plugin trust level
- Calculate `min(repo_trust, plugin_trust)`
- Handle missing trust levels (default to untrusted)

#### CLI Commands
- Accept fragment in URLs
- List plugins from monorepo
- Show source repo in `--list`
- Group by repo in `--browse`

#### Validation
- Validate plugin path exists in repo
- Check for plugin ID conflicts
- Verify trust level constraints
- Detect circular redirects

---

## Edge Cases

### Critical (Must Handle)

1. **Plugin moves between repos**: Registry redirect
2. **Same plugin ID in different repos**: Enforce global uniqueness
3. **Shared code between plugins**: Copy or forbid
4. **Plugin depends on another in same repo**: Auto-install dependencies
5. **Trust level per plugin**: Hierarchical model
6. **Repo restructuring**: Registry redirects with new paths
7. **Version conflicts**: MANIFEST.toml is source of truth

### Important (Should Handle)

1. **Partial update failure**: Atomic updates or rollback
2. **Local modifications**: Detect and warn before overwrite
3. **Large repos**: Sparse checkout or shallow clone
4. **Cache management**: TTL and cleanup
5. **Registry unavailable**: Fallback to direct URLs
6. **Stale cache**: Fetch before updates
7. **Multiple plugins from same repo**: Batch operations

### Nice to Have (Could Handle)

1. **Git LFS support**: Detect and handle large files
2. **Submodules**: Clone recursively or ignore
3. **Nested directories**: Scan depth limit
4. **Hidden plugins**: Respect `.pluginignore`
5. **Performance optimization**: Parallel operations
6. **Circular dependencies**: Detect and reject

---

## Open Questions

### Technical Decisions

1. **Shared code handling**: Copy into each plugin, or forbid shared dependencies?
2. **Version tagging**: How to tag individual plugins in monorepo? (`plugin-v1.0.0` vs `v1.0.0`)
3. **Scan depth**: How deep to search for plugins? (Currently: 3 levels)
4. **Cache strategy**: Per-repo cache with TTL, or per-plugin?
5. **Sparse checkout**: Use git sparse-checkout for large repos?

### Trust and Security

1. **Trust inheritance**: Should plugins inherit repo trust by default, or start untrusted?
2. **Blacklist scope**: Block individual plugin or entire repo?
3. **Code signing**: Future requirement for official plugins?
4. **Review process**: Who can mark plugins as trusted?

### User Experience

1. **Default behavior**: If no fragment specified and multiple plugins found, list or error?
2. **Update notifications**: Per-plugin or per-repo?
3. **Conflict resolution**: What if user tries to install same plugin ID from different repos?
4. **Migration path**: How to migrate existing single-repo plugins to monorepo?

### Registry Design

1. **Registry structure**: Flat list or hierarchical (repos → plugins)?
2. **Redirect chains**: How many redirects to follow? (Currently: unlimited with cycle detection)
3. **Plugin removal**: How to handle plugins removed from repo?
4. **Metadata sync**: How often to update registry from repos?

### Performance

1. **Clone optimization**: Always shallow clone? Depth limit?
2. **Bandwidth**: How to minimize for large repos?
3. **Parallel operations**: Install multiple plugins from same repo in parallel?

---

## Implementation Strategy

### Phase 1: Basic Monorepo Support
- Fragment identifier parsing
- Plugin discovery in repos
- Storage with source tracking
- Basic trust model (repo-level only)

### Phase 2: Enhanced Features
- Hierarchical trust model (repo + plugin)
- Registry redirects
- Shared code handling
- Cache optimization

### Phase 3: Advanced Features
- Sparse checkout for large repos
- Batch operations
- Advanced dependency resolution
- Performance optimization

---

## Recommendation

**Implement monorepo support** using the hybrid approach:

1. **Support both patterns**: Single-plugin and multi-plugin repos
2. **Use fragment identifier**: Standard URL syntax
3. **Auto-detect single plugin**: Backward compatible
4. **Hierarchical trust**: Repo ceiling + plugin level
5. **Registry redirects**: Handle plugin moves
6. **Start simple**: Basic support first, optimize later

**Rationale**: Matches existing ecosystem (picard-plugins repo), provides flexibility, and maintains security through hierarchical trust model.

---

## References

- Current implementation: Single plugin per repo
- Official plugins: <https://github.com/metabrainz/picard-plugins> (73 plugins)
- Trust model: `docs/PLUGINSV3/SECURITY.md`
- Registry design: `docs/PLUGINSV3/WEBSITE.md`
