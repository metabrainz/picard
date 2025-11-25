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
   - Contains `plugins.json` (the registry)
   - CLI tool to manipulate registry
   - Validation scripts
   - CI/CD for validation

2. **picard.musicbrainz.org** (Website)
   - Serves `plugins.json` at `/api/v3/plugins.json`
   - Displays plugin browser (HTML pages)
   - Fetches from GitHub (cached)

3. **Picard Client**
   - Downloads `plugins.json` from website
   - Caches locally
   - Uses for plugin discovery and blacklist checking

### Data Flow

```
1. Admin runs: registry plugin add <url> --trust community
   ↓
2. CLI updates plugins.json in local git repo
   ↓
3. Admin commits and pushes to GitHub
   ↓
4. GitHub hosts the JSON file
   ↓
5. Website fetches from GitHub (cached)
   ↓
6. Website serves at /api/v3/plugins.json
   ↓
7. Picard downloads and caches
```

---

## Repository Structure

### picard-plugins-registry

```
picard-plugins-registry/
├── plugins.json              # The registry (generated/managed)
├── registry                  # CLI tool (executable)
├── registry_lib/
│   ├── __init__.py
│   ├── cli.py               # CLI argument parsing
│   ├── registry.py          # Registry manipulation
│   ├── plugin.py            # Plugin operations
│   ├── blacklist.py         # Blacklist operations
│   ├── manifest.py          # MANIFEST.toml fetching/parsing
│   ├── constants.py         # Trust levels, categories (copied from Picard)
│   ├── validate.py          # Validation logic
│   └── utils.py             # Utilities
├── README.md
├── requirements.txt
└── .github/
    └── workflows/
        └── validate.yml     # CI validation
```

**Note:** `manifest.py` and `constants.py` contain minimal code copied from Picard to keep the tool standalone.

---

## Registry CLI Tool

### Commands

```bash
# Plugin management
registry plugin add <git-url> --trust <level> [--category <cat>]
registry plugin remove <plugin-id>
registry plugin update <plugin-id>
registry plugin set-trust <plugin-id> <level>
registry plugin list [--trust <level>] [--category <cat>]
registry plugin show <plugin-id>

# Blacklist management
registry blacklist add <git-url> --reason <reason> [--pattern]
registry blacklist remove <git-url>
registry blacklist list
registry blacklist show <git-url>

# Utilities
registry validate
registry stats
```

### Usage Examples

**Add a plugin:**
```bash
cd picard-plugins-registry

# Add new community plugin
./registry plugin add https://github.com/user/awesome-plugin \
    --trust community \
    --category metadata

# Output:
# Fetching MANIFEST.toml from https://github.com/user/awesome-plugin...
# Plugin: Awesome Plugin
# Version: 1.0.0
# Authors: John Doe
# API: 3.0
#
# Added plugin 'awesome-plugin' to registry
# Trust level: community
# Categories: metadata

# Validate
./registry validate

# Commit
git add plugins.json
git commit -m "Add plugin: Awesome Plugin"
git push
```

**Promote plugin to trusted:**
```bash
./registry plugin set-trust awesome-plugin trusted
git add plugins.json
git commit -m "Promote awesome-plugin to trusted"
git push
```

**Blacklist a plugin:**
```bash
./registry blacklist add https://github.com/badactor/malware \
    --reason "Contains malicious code"

git add plugins.json
git commit -m "Blacklist malicious plugin"
git push
```

**Blacklist entire organization:**
```bash
./registry blacklist add https://github.com/badorg/* \
    --reason "Compromised account" \
    --pattern

git add plugins.json
git commit -m "Blacklist organization: badorg"
git push
```

---

## Registry Manipulation

### Registry Class

```python
# registry_lib/registry.py
import json
from datetime import datetime
from pathlib import Path
from .manifest import fetch_manifest, validate_manifest
from .utils import derive_plugin_id

class Registry:
    def __init__(self, path='plugins.json'):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if not self.path.exists():
            return {
                'api_version': '3.0',
                'last_updated': datetime.now().isoformat(),
                'plugins': [],
                'blacklist': []
            }
        with open(self.path) as f:
            return json.load(f)

    def save(self):
        self.data['last_updated'] = datetime.now().isoformat()
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Trailing newline

    def add_plugin(self, git_url, trust_level, categories=None):
        # Fetch and validate MANIFEST
        manifest = fetch_manifest(git_url)
        validate_manifest(manifest)

        # Derive plugin ID
        plugin_id = derive_plugin_id(git_url)

        # Check if exists
        if self.find_plugin(plugin_id):
            raise ValueError(f"Plugin {plugin_id} already exists")

        # Build plugin entry
        plugin = {
            'id': plugin_id,
            'name': manifest['name'],
            'description': manifest['description'],
            'git_url': git_url,
            'categories': categories or manifest.get('categories', []),
            'trust_level': trust_level,
            'authors': manifest['authors'],
            'min_api_version': manifest['api'][0],
            'added_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add translations if present
        if 'name_i18n' in manifest:
            plugin['name_i18n'] = manifest['name_i18n']
        if 'description_i18n' in manifest:
            plugin['description_i18n'] = manifest['description_i18n']

        # Add max_api_version if multiple versions
        if len(manifest['api']) > 1:
            plugin['max_api_version'] = manifest['api'][-1]

        self.data['plugins'].append(plugin)
        return plugin

    def remove_plugin(self, plugin_id):
        self.data['plugins'] = [p for p in self.data['plugins'] if p['id'] != plugin_id]

    def update_plugin(self, plugin_id):
        plugin = self.find_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        # Fetch latest MANIFEST
        manifest = fetch_manifest(plugin['git_url'])
        validate_manifest(manifest)

        # Update fields
        plugin['name'] = manifest['name']
        plugin['description'] = manifest['description']
        plugin['authors'] = manifest['authors']
        plugin['min_api_version'] = manifest['api'][0]
        plugin['updated_at'] = datetime.now().isoformat()

        # Update translations
        if 'name_i18n' in manifest:
            plugin['name_i18n'] = manifest['name_i18n']
        elif 'name_i18n' in plugin:
            del plugin['name_i18n']

        if 'description_i18n' in manifest:
            plugin['description_i18n'] = manifest['description_i18n']
        elif 'description_i18n' in plugin:
            del plugin['description_i18n']

    def set_trust_level(self, plugin_id, trust_level):
        plugin = self.find_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")
        plugin['trust_level'] = trust_level
        plugin['updated_at'] = datetime.now().isoformat()

    def find_plugin(self, plugin_id):
        for plugin in self.data['plugins']:
            if plugin['id'] == plugin_id:
                return plugin
        return None

    def add_blacklist(self, git_url, reason, pattern=False):
        entry = {
            'git_url': git_url,
            'reason': reason,
            'blacklisted_at': datetime.now().isoformat()
        }
        if pattern:
            entry['pattern'] = 'repository'
        self.data['blacklist'].append(entry)

    def remove_blacklist(self, git_url):
        self.data['blacklist'] = [e for e in self.data['blacklist'] if e['git_url'] != git_url]
```

### Manifest Fetching

```python
# registry_lib/manifest.py
import tomli  # or tomllib in Python 3.11+
import requests

def fetch_manifest(git_url):
    """Fetch MANIFEST.toml from git repository"""
    # Convert GitHub URL to raw content URL
    if 'github.com' in git_url:
        raw_url = git_url.replace('github.com', 'raw.githubusercontent.com')
        raw_url = raw_url.rstrip('/') + '/main/MANIFEST.toml'
    else:
        raise ValueError(f"Unsupported git host: {git_url}")

    response = requests.get(raw_url, timeout=10)
    response.raise_for_status()

    return tomli.loads(response.text)

def validate_manifest(manifest):
    """Validate MANIFEST.toml structure"""
    from .constants import REQUIRED_MANIFEST_FIELDS, TRUST_LEVELS, CATEGORIES

    # Check required fields
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            raise ValueError(f"Missing required field: {field}")

    # Validate types
    if not isinstance(manifest['name'], str):
        raise ValueError("name must be a string")
    if not isinstance(manifest['authors'], list):
        raise ValueError("authors must be an array")
    if not isinstance(manifest['api'], list):
        raise ValueError("api must be an array")

    # Validate categories if present
    if 'categories' in manifest:
        for cat in manifest['categories']:
            if cat not in CATEGORIES:
                raise ValueError(f"Invalid category: {cat}")

    return True
```

### Constants (Copied from Picard)

```python
# registry_lib/constants.py
# NOTE: This file is kept in sync with picard/plugin3/constants.py

TRUST_LEVELS = ['official', 'trusted', 'community']

CATEGORIES = [
    'metadata',
    'coverart',
    'ui',
    'scripting',
    'formats',
    'other'
]

REQUIRED_MANIFEST_FIELDS = [
    'name',
    'version',
    'description',
    'api',
    'authors',
    'license',
    'license_url'
]
```

---

## Website Integration

### Serving the Registry

**Simple approach - proxy to GitHub:**

```python
# In Flask/Django app
import requests
from datetime import datetime, timedelta
from pathlib import Path

REGISTRY_URL = "https://raw.githubusercontent.com/metabrainz/picard-plugins-registry/main/plugins.json"
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

@app.route('/api/v3/plugins.json')
def plugins_json():
    """Serve plugin registry"""
    data = get_registry()
    return Response(data, mimetype='application/json')
```

**With webhook (optional):**

```python
@app.route('/api/v3/registry-webhook', methods=['POST'])
def registry_webhook():
    """GitHub webhook to invalidate cache"""
    # Verify GitHub signature
    if verify_github_signature(request):
        # Invalidate cache
        Path(CACHE_FILE).unlink(missing_ok=True)
        return jsonify({'status': 'cache invalidated'})
    return jsonify({'error': 'invalid signature'}), 403
```

---

## Plugin Submission Process

### Via Pull Request (Recommended)

```
1. Developer forks picard-plugins-registry
2. Developer runs:
   ./registry plugin add https://github.com/me/my-plugin --trust community
3. Developer creates PR with the change
4. CI validates:
   - JSON is valid
   - Plugin URL is accessible
   - MANIFEST.toml is valid
   - No duplicates
   - Trust level is valid
5. Picard team reviews PR
6. Picard team merges
7. Plugin appears in registry within 1 hour (cache refresh)
```

### Via Web Form (Future)

```
1. Developer submits form on picard.musicbrainz.org
2. Website validates input
3. Website creates PR automatically via GitHub API
4. Same validation and review process
5. Picard team merges
```

---

## CI/CD Validation

### GitHub Actions Workflow

```yaml
# .github/workflows/validate.yml
name: Validate Registry

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Validate registry
        run: |
          ./registry validate

      - name: Check for duplicates
        run: |
          python -c "
          import json
          with open('plugins.json') as f:
              data = json.load(f)
          ids = [p['id'] for p in data['plugins']]
          urls = [p['git_url'] for p in data['plugins']]
          assert len(ids) == len(set(ids)), 'Duplicate plugin IDs'
          assert len(urls) == len(set(urls)), 'Duplicate git URLs'
          print('✓ No duplicates')
          "

      - name: Validate plugin URLs
        run: |
          python -c "
          import json, requests
          with open('plugins.json') as f:
              data = json.load(f)
          for plugin in data['plugins']:
              url = plugin['git_url']
              # Check if repo exists (HEAD request)
              r = requests.head(url, timeout=5)
              assert r.status_code == 200, f'Invalid URL: {url}'
          print('✓ All URLs valid')
          "
```

---

## Plugin Marketplace / Browser (Future)

### Overview

A web-based plugin browser for discovering registered plugins.

**Community Feedback:**
> **rdswift:** "If the plugin browser is only displaying information for plugins in the registry, then the system can be automated to use the information provided via the registry item manifests, and serve the pages based upon the results of API queries. In this case, the plugin browser could (and should) be served from the picard.musicbrainz.org domain. A rudimentary list of plugins not included in the official plugin list is currently available on a Picard Resources page in the MusicBrainz Wiki. My recommendation is to continue using the Wiki for this purpose, curated by the users, which would allow rudimentary discovery of the 'unofficial' unregistered plugins."

### Implementation

**For Registered Plugins:**
- Web browser at picard.musicbrainz.org/plugins
- Reads from plugins.json (same source as API)
- Filter by: category, trust level, author
- Search by: name, description
- Display: name, description, authors, trust level, categories
- Link to: repository, documentation
- Show install command

**For Unregistered Plugins:**
- Continue using MusicBrainz Wiki
- User-curated list
- Clear indication these are not in official registry

**Example page:**
```html
<h1>Picard Plugins</h1>

<input type="search" placeholder="Search plugins...">
<select name="category">
  <option>All Categories</option>
  <option>Metadata</option>
  <option>Cover Art</option>
</select>
<select name="trust">
  <option>All Trust Levels</option>
  <option>Official</option>
  <option>Trusted</option>
  <option>Community</option>
</select>

<div class="plugin-list">
  <div class="plugin official">
    <h3>🛡️ ListenBrainz Submitter</h3>
    <p>Submit your music to ListenBrainz</p>
    <p>Authors: MusicBrainz Picard Team</p>
    <p>Categories: metadata</p>
    <code>picard plugins --install listenbrainz</code>
  </div>

  <div class="plugin trusted">
    <h3>✓ Discogs</h3>
    <p>Get metadata from Discogs</p>
    <p>Authors: Bob Swift</p>
    <p>Categories: metadata</p>
    <code>picard plugins --install discogs</code>
  </div>
</div>
```

---

## Benefits of Git-Based Approach

1. **No Database**
   - No database to maintain, backup, or migrate
   - No connection pooling, no ORM
   - Git is the database

2. **Version Control**
   - Full history of all changes
   - Easy rollback (git revert)
   - Audit trail built-in
   - Diff shows exactly what changed

3. **Simple Deployment**
   - Website just serves static JSON
   - Can use CDN for plugins.json
   - Website can be stateless
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
   - Clear approval process

6. **Reliability**
   - Git is the source of truth
   - GitHub provides hosting and CDN
   - Simple backup (git clone)
   - Easy disaster recovery

7. **Scalability**
   - Static JSON can be CDN-cached
   - No database queries
   - Handles high traffic easily
   - Expected scale: <1000 plugins

---

## Code Sharing with Picard

### Shared Code

The registry tool contains minimal code copied from Picard:

**registry_lib/constants.py** (~20 lines)
- Trust levels
- Categories
- Required MANIFEST fields

**registry_lib/manifest.py** (~50 lines)
- MANIFEST.toml fetching
- Basic validation

**Total duplication: ~70 lines**

### Keeping in Sync

1. **Documentation**: Both files marked with comment:
   ```python
   # NOTE: This file is kept in sync with picard/plugin3/constants.py
   ```

2. **Infrequent changes**: MANIFEST format is stable

3. **Manual sync**: When changing MANIFEST format in Picard, update registry tool

4. **Test reminder**: Could add test in Picard that documents the sync requirement

### Why Not Share via Package?

- Registry tool should be **standalone**
- Avoids dependency management
- Simpler deployment
- Duplication is minimal (~70 lines)
- Changes are infrequent

---

## See Also

- **[REGISTRY.md](REGISTRY.md)** - Registry JSON schema and client integration
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[SECURITY.md](SECURITY.md)** - Security model
- **[DECISIONS.md](DECISIONS.md)** - Design decisions
