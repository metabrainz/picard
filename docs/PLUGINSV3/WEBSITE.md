# Website Plugin Registry Implementation

This document describes the server-side implementation for the plugin registry using a git-based approach.

---

## Overview

The plugin registry uses a **git repository as the database**. No traditional database is needed - the registry is a JSON file in a git repository, managed by a CLI tool.

**Key principle:** Git is the source of truth.

---

## Architecture

### Components

1. **picard-plugins-registry** (Git repository)
   - Contains `plugins.toml` (the registry)
   - CLI tool to manipulate registry
   - Validation scripts
   - CI/CD for validation

2. **picard.musicbrainz.org** (Website)
   - Serves `plugins.toml` at `/api/v3/plugins.toml`
   - Displays plugin browser (HTML pages)
   - Fetches from GitHub (cached)

3. **Picard Client**
   - Downloads `plugins.toml` from website
   - Caches locally
   - Uses for plugin discovery and blacklist checking

### Data Flow

```text
1. Admin runs: registry plugin add <url> --trust community
   ↓
2. CLI updates plugins.toml in local git repo
   ↓
3. Admin commits and pushes to GitHub
   ↓
4. GitHub hosts the JSON file
   ↓
5. Website fetches from GitHub (cached)
   ↓
6. Website serves at /api/v3/plugins.toml
   ↓
7. Picard downloads and caches
```

---

## Repository Structure

### picard-plugins-registry

```text
picard-plugins-registry/
├── plugins.toml              # The registry (generated/managed)
├── registry_lib/
│   ├── __init__.py
│   ├── cli.py               # CLI argument parsing
│   ├── registry.py          # Registry file management
│   ├── plugin.py            # Plugin operations
│   ├── blacklist.py         # Blacklist operations
│   ├── manifest.py          # MANIFEST.toml fetching/parsing
│   ├── utils.py             # Utilities (derive_plugin_id, timestamps)
│   └── picard/              # Files copied from Picard
│       ├── constants.py     # Trust levels, categories
│       └── validator.py     # MANIFEST validation
├── tests/                    # Unit tests
├── pyproject.toml           # Python project config (uv)
├── uv.lock                  # Dependency lock file
├── README.md
└── .github/
    └── workflows/
        └── ci.yml           # CI validation
```

**Note:** `constants.py` and `validator.py` are copied from Picard to keep the tool standalone.

---

## Registry CLI Tool

### Command Structure

```bash
# Plugin management
registry plugin add <git-url> --trust <level> [--categories <cats>] [--refs <refs>]
registry plugin update <plugin-id> [--ref <ref>]
registry plugin edit <plugin-id> [--trust <level>] [--categories <cats>] [--git-url <url>]
registry plugin redirect <plugin-id> <old-url> [--remove] [--list]
registry plugin remove <plugin-id>
registry plugin list [--trust <level>] [--category <cat>] [--verbose]
registry plugin show <plugin-id>

# Ref management (separate from plugin)
registry ref add <plugin-id> <ref-name> [--description <desc>] [--min-api-version <ver>] [--max-api-version <ver>]
registry ref edit <plugin-id> <ref-name> [--name <new-name>] [--description <desc>] [--min-api-version <ver>] [--max-api-version <ver>]
registry ref remove <plugin-id> <ref-name>
registry ref list <plugin-id>

# Blacklist management
registry blacklist add [--url <url>] [--uuid <uuid>] [--url-regex <pattern>] --reason <reason>
registry blacklist remove [--url <url>] [--uuid <uuid>]
registry blacklist list
registry blacklist show [--url <url>] [--uuid <uuid>]

# Utilities
registry validate
registry stats
```

### Usage Examples

**Add a plugin:**
```bash
cd picard-plugins-registry

# Add new community plugin (uses default ref: main)
registry plugin add https://github.com/user/awesome-plugin \
    --trust community \
    --categories metadata

# Output:
# Fetching MANIFEST.toml from https://github.com/user/awesome-plugin (ref: main)...
# Plugin: Awesome Plugin
# UUID: 12345678-1234-4234-8234-123456789abc
# Authors: John Doe
# API: 3.0
#
# Added plugin 'awesome-plugin' to registry

# Add plugin with custom branch
registry plugin add https://github.com/user/old-plugin \
    --trust community \
    --refs master

# Add plugin with multiple refs and API versions
registry plugin add https://github.com/user/multi-version-plugin \
    --trust community \
    --refs 'main:4.0,picard-v3:3.0-3.99'

# The registry will contain:
{
  "refs": [
    {
      "name": "main",
      "min_api_version": "4.0"
    },
    {
      "name": "picard-v3",
      "min_api_version": "3.0",
      "max_api_version": "3.99"
    }
  ]
}

# Validate
registry validate

# Commit
git add plugins.toml
git commit -m "Add plugin: Awesome Plugin"
git push
```

**Update plugin metadata:**
```bash
# Update from default ref (first ref or main)
registry plugin update awesome-plugin

# Update from specific ref
registry plugin update awesome-plugin --ref develop

# Note: UUID must match or update will fail
```

**Edit plugin:**
```bash
# Change trust level
registry plugin edit awesome-plugin --trust trusted

# Change categories
registry plugin edit awesome-plugin --categories metadata,ui

# Change git URL (when plugin permanently moves)
registry plugin edit awesome-plugin --git-url https://github.com/neworg/awesome-plugin

git add plugins.toml
git commit -m "Promote awesome-plugin to trusted"
git push
```

**Manage refs:**
```bash
# Add a ref
registry ref add awesome-plugin develop \
    --description "Development branch" \
    --min-api-version "4.0"

# Edit ref (update description, API versions, or rename)
registry ref edit awesome-plugin develop --max-api-version "4.99"
registry ref edit awesome-plugin develop --name beta

# List refs
registry ref list awesome-plugin

# Remove ref
registry ref remove awesome-plugin develop

git add plugins.toml
git commit -m "Add develop ref to awesome-plugin"
git push
```

**Manage redirects:**
```bash
# Add redirect when plugin moves
registry plugin redirect awesome-plugin https://github.com/olduser/old-repo

# List redirects
registry plugin redirect awesome-plugin --list

# Remove redirect
registry plugin redirect awesome-plugin https://github.com/olduser/old-repo --remove

git add plugins.toml
git commit -m "Add redirect for moved plugin"
git push
```

**Blacklist a plugin:**
```bash
# Blacklist by UUID (recommended - blocks plugin at all URLs)
registry blacklist add --uuid 12345678-1234-4234-8234-123456789abc \
    --reason "Malicious plugin"

# Blacklist by URL
registry blacklist add --url https://github.com/badactor/malware \
    --reason "Contains malicious code"

# Blacklist entire organization
registry blacklist add --url-regex "^https://github\\.com/badorg/.*" \
    --reason "Compromised account"

git add plugins.toml
git commit -m "Blacklist malicious plugin"
git push
```

---

## Implementation Details

### Key Files

**registry_lib/plugin.py:**
- `add_plugin()` - Add plugin with duplicate checking (UUID, URL, ID)
- `update_plugin()` - Refresh metadata from MANIFEST with UUID validation
- `_parse_refs()` - Parse refs string (e.g., "main:4.0,picard-v3:3.0-3.99")
- `_sync_optional_fields()` - Helper for optional MANIFEST fields

**registry_lib/registry.py:**
- `Registry` class - Load/save JSON, find plugins, sort by ID
- `add_plugin()` - Append plugin to registry
- `remove_plugin()` - Remove plugin by ID
- `add_blacklist()` / `remove_blacklist()` - Manage blacklist

**registry_lib/manifest.py:**
- `fetch_manifest()` - Fetch MANIFEST.toml from GitHub raw URL
- `validate_manifest()` - Validate using Picard's validator

**registry_lib/utils.py:**
- `derive_plugin_id()` - Derive ID from git URL (removes prefixes)
- `now_iso8601()` - Generate ISO 8601 timestamps with Z suffix

**registry_lib/cli.py:**
- `get_plugin_or_exit()` - Helper for plugin lookup with error handling
- Command functions for all CLI operations
- Argument parsing with argparse

### Duplicate Detection

When adding a plugin, the system checks for duplicates:

1. **Git URL** - Most direct duplicate (same repository)
2. **UUID** - Prevents same plugin at different URLs
3. **Plugin ID** - Prevents derived ID collisions

All checks include the existing plugin ID in error messages for clarity.

### Validation

The `validate` command checks:
- JSON syntax
- Duplicate IDs, UUIDs, URLs
- Required fields present
- Trust levels valid
- Categories valid

### Testing

- 53 unit tests covering all operations
- Tests use temporary registry files
- Mock MANIFEST fetching for speed
- Pre-commit hooks run tests automatically

---

## CI/CD Validation

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest

      - name: Validate registry
        run: uv run registry validate
```

The CI runs on every PR and push, ensuring:
- All tests pass
- Registry is valid
- No duplicates
- All plugins accessible

---

## Website Integration

**TODO:** Implement `https://picard.musicbrainz.org/registry/plugins.toml` endpoint as fallback for the GitHub URL. This provides:
- Resilience if GitHub is unavailable or blocked
- Ability to intentionally remove GitHub file to force all clients to use proxy
- Control over caching headers and rate limiting
- Analytics on registry usage

### Serving the Registry

**Simple approach - proxy to GitHub:**

```python
# In Flask/Django app
import requests
from datetime import datetime, timedelta
from pathlib import Path

REGISTRY_URL = "https://raw.githubusercontent.com/metabrainz/picard-plugins-registry/main/plugins.toml"
CACHE_FILE = "/tmp/plugins_registry.json"
CACHE_TTL = 3600  # 1 hour

def get_registry():
    """Get registry JSON with caching"""
    cache_path = Path(CACHE_FILE)

    # Check cache
    if cache_path.exists():
        age = datetime.now().timestamp() - cache_path.stat().st_mtime
        if age < CACHE_TTL:
            with open(cache_path) as f:
                return f.read()

    # Fetch from GitHub
    response = requests.get(REGISTRY_URL, timeout=10)
    response.raise_for_status()

    # Cache it
    with open(cache_path, 'w') as f:
        f.write(response.text)

    return response.text

@app.route('/api/v3/plugins.toml')
def plugins_json():
    """Serve plugin registry"""
    data = get_registry()
    return Response(data, mimetype='application/json')
```

---

## Plugin Submission Process

### Via Pull Request (Recommended)

1. Developer forks picard-plugins-registry
2. Developer runs:
   ```bash
   uv sync
   source .venv/bin/activate
   registry plugin add https://github.com/me/my-plugin --trust community --categories metadata
   ```
3. Developer creates PR with the change
4. CI validates:
   - JSON is valid
   - Plugin URL is accessible
   - MANIFEST.toml is valid
   - No duplicates (UUID, URL, ID)
   - Trust level is valid
5. Picard team reviews PR
6. Picard team merges
7. Plugin appears in registry within 1 hour (cache refresh)

### Via Web Form (Future)

1. Developer submits form on picard.musicbrainz.org
2. Website validates input
3. Website creates PR automatically via GitHub API
4. Same validation and review process
5. Picard team merges

---

## Benefits of Git-Based Approach

1. **No Database**
   - No database to maintain, backup, or migrate
   - Git is the database

2. **Version Control**
   - Full history of all changes
   - Easy rollback (git revert)
   - Audit trail built-in

3. **Simple Deployment**
   - Website just serves static JSON
   - Can use CDN for plugins.toml
   - No database connection needed

4. **Collaboration**
   - PRs for plugin submissions
   - Review process via GitHub
   - Community can submit PRs
   - Automated validation via CI

5. **Transparency**
   - Public repository
   - Anyone can see registry contents
   - Anyone can propose changes

6. **Reliability**
   - Git is the source of truth
   - GitHub provides hosting and CDN
   - Simple backup (git clone)

7. **Scalability**
   - Static JSON can be CDN-cached
   - Expected scale: <1000 plugins

---

## Code Sharing with Picard

### Shared Code

The registry tool copies validation code from Picard:

**registry_lib/picard/constants.py** (~60 lines)
- Copy from `picard/plugin3/constants.py`
- Trust levels, categories, required fields

**registry_lib/picard/validator.py** (~120 lines)
- Copy from `picard/plugin3/validator.py`
- Standalone validation function
- Modified imports to use relative imports (`.constants`)

Total: ~180 lines

### Keeping in Sync

- MANIFEST format is stable (changes are rare)
- When format changes, copy updated files from Picard
- Files are designed to be copied with minimal modification

---

## See Also

- **[REGISTRY.md](REGISTRY.md)** - Registry JSON schema and client integration
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[SECURITY.md](SECURITY.md)** - Security model
