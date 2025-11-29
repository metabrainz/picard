# Git Refs Support - Feature Summary

This document summarizes the git refs feature added to the plugin registry system.

## Overview

The plugin registry now supports multiple git refs (branches/tags) per plugin, enabling:
- **Beta testing channels** - Users can opt into beta/development versions
- **Smooth major version transitions** - Maintain separate branches for different Picard versions
- **Flexible branch naming** - No assumptions about `main` vs `master` vs custom names

## Schema Changes

### Before (Implicit)
```json
{
  "id": "my-plugin",
  "git_url": "https://github.com/user/plugin",
  "min_api_version": "3.0"
  // Implicitly assumed "main" branch
}
```

### After (Explicit with Defaults)
```json
{
  "id": "my-plugin",
  "git_url": "https://github.com/user/plugin",
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
  ]
}
```

### Simple Case (90% of plugins)
```json
{
  "id": "simple-plugin",
  "git_url": "https://github.com/user/plugin"
  // refs omitted = defaults to [{"name": "main"}]
}
```

## Key Features

### 1. Default Behavior
- If `refs` field is omitted, defaults to `[{"name": "main"}]`
- Most plugins don't need to specify refs explicitly
- Backward compatible with existing assumptions

### 2. Auto-Selection
- Picard automatically selects the most appropriate ref based on API version
- Users on Picard 3.x get `picard-v3` branch
- Users on Picard 4.x get `main` branch
- No manual intervention needed for version transitions

### 3. Explicit Override
- Users can explicitly choose any available ref
- Useful for beta testing or pinning to specific versions
- Commands: `--ref` flag and `--switch-ref` command

### 4. Validation
- Registry tool validates all refs exist before accepting plugin
- CI/CD checks all refs are accessible
- Prevents broken installations

## Use Cases

### Use Case 1: Smooth Major Version Transition

**Problem:** Picard 4.0 introduces breaking API changes. Plugin author wants to:
- Support Picard 3.x users with bug fixes
- Develop new features for Picard 4.x
- Avoid maintaining two separate repositories

**Solution:**
```json
{
  "id": "my-plugin",
  "refs": [
    {
      "name": "main",
      "description": "For Picard 4.x and later",
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

**Result:**
- Picard 3.x users automatically get `picard-v3-stable` branch
- Picard 4.x users automatically get `main` branch
- Both groups receive updates on their respective branches
- No user intervention required

### Use Case 2: Beta Testing Channel

**Problem:** Plugin author wants to test new features with power users before stable release.

**Solution:**
```json
{
  "id": "my-plugin",
  "refs": [
    {
      "name": "stable",
      "description": "Stable releases"
    },
    {
      "name": "beta",
      "description": "Testing new features (may be unstable)"
    }
  ]
}
```

**Usage:**
```bash
# Regular users get stable
picard plugins --install my-plugin

# Power users opt into beta
picard plugins --install my-plugin --ref beta

# Switch between channels
picard plugins --switch-ref my-plugin beta
picard plugins --switch-ref my-plugin stable
```

### Use Case 3: Custom Branch Names

**Problem:** Repository uses `master` instead of `main`, or uses gitflow with `develop` branch.

**Solution:**
```json
{
  "id": "old-plugin",
  "refs": [{"name": "master"}]
}
```

or

```json
{
  "id": "gitflow-plugin",
  "refs": [
    {"name": "master"},
    {"name": "develop", "description": "Development branch"}
  ]
}
```

**Result:** No assumptions about branch names - plugin author explicitly declares what's available.

## Implementation Details

### Registry Tool Changes

**Command:**
```bash
# Simple case (auto-detects default branch)
./registry plugin add https://github.com/user/plugin --trust community

# Explicit single ref
./registry plugin add https://github.com/user/plugin --trust community --refs master

# Multiple refs (API versions read from each ref's MANIFEST.toml)
./registry plugin add https://github.com/user/plugin --trust community --refs 'main,picard-v3'

# Multiple refs with explicit API versions (overrides MANIFEST.toml)
./registry plugin add https://github.com/user/plugin --trust community \
    --refs 'main:4.0,picard-v3:3.0-3.99'
```

**How API versions are determined:**

1. **Auto-detection (recommended):** Registry tool fetches MANIFEST.toml from each ref
   ```bash
   ./registry plugin add https://github.com/user/plugin --refs 'main,picard-v3'

   # Fetches:
   # - main/MANIFEST.toml → api = ["4.0"] → min_api_version: "4.0"
   # - picard-v3/MANIFEST.toml → api = ["3.0", "3.1"] → min: "3.0", max: "3.1"
   ```

2. **Explicit specification (override):** Manually specify API versions
   ```bash
   ./registry plugin add https://github.com/user/plugin --refs 'main:4.0,picard-v3:3.0-3.99'

   # Uses specified versions, ignores MANIFEST.toml api field
   # Useful for being more restrictive than plugin declares
   ```

**Validation:**
- Fetches MANIFEST.toml from each ref to verify it exists
- Validates MANIFEST.toml structure for each ref
- Extracts API versions from each ref's MANIFEST (unless explicitly provided)
- Rejects plugin if any ref is missing or invalid

### Client Changes

**Auto-selection algorithm:**
```python
def select_ref(plugin, picard_api_version):
    refs = plugin.get('refs', [{'name': 'main'}])

    for ref in refs:
        min_ver = ref.get('min_api_version', '0.0')
        max_ver = ref.get('max_api_version', '99.0')

        if min_ver <= picard_api_version <= max_ver:
            return ref['name']

    return refs[0]['name']  # fallback to default
```

**Commands:**
```bash
# Install with auto-selection
picard plugins --install my-plugin

# Install specific ref
picard plugins --install my-plugin --ref beta

# Show available refs
picard plugins --info my-plugin

# Switch ref
picard plugins --switch-ref my-plugin beta
```

## Benefits

1. **No Breaking Changes**
   - Default behavior (omit `refs`) works for 90% of plugins
   - Existing assumptions about `main` branch preserved as default
   - Gradual adoption - plugins can add refs when needed

2. **Smooth Transitions**
   - Plugin authors can support multiple Picard versions simultaneously
   - Users automatically get the right version for their Picard
   - No manual intervention or documentation reading required

3. **Flexibility**
   - Supports any branch naming convention
   - Enables beta testing channels
   - Allows version pinning
   - Power users get control, regular users get simplicity

4. **Validation**
   - All refs validated before acceptance
   - CI/CD ensures refs remain accessible
   - Prevents broken installations

5. **Transparency**
   - Available refs shown in `--info` command
   - Clear descriptions of what each ref is for
   - Users can make informed choices

## Migration Path

Since plugins v3 is still in development, no migration is needed. The feature is designed from the start with:
- Sensible defaults (omit `refs` = use `main`)
- Explicit validation (all refs must exist)
- Clear documentation (examples for all use cases)

## Documentation Updates

The following documents have been updated:
- **REGISTRY.md** - Added Git Refs section with schema, examples, and use cases
- **CLI.md** - Enhanced Git Ref Management section with registry refs info
- **WEBSITE.md** - Updated registry tool commands and validation to support refs

## Examples in Documentation

All three documents now include:
- Simple case examples (omit refs, use defaults)
- Custom branch examples (master, develop, etc.)
- Multi-ref examples (stable + beta)
- Version-specific examples (main for v4, picard-v3 for v3)
- Complete command examples for registry tool and CLI
