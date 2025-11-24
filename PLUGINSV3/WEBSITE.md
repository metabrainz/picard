# Website Plugin Registry Implementation

This document describes the server-side implementation for generating and serving the plugin registry.

---

## Overview

The Picard website generates the plugin registry JSON by:
1. Scanning configured plugin repositories
2. Extracting metadata from MANIFEST.toml files
3. Extracting translations from MANIFEST.toml
4. Applying trust level assignments
5. Including blacklist entries
6. Serving as JSON endpoint

---

## Registry Generation

### Workflow

```
1. Scheduled task (daily/hourly)
   ↓
2. For each plugin repository:
   - Clone/pull repository
   - Read MANIFEST.toml
   - Extract metadata
   - Extract translations
   ↓
3. Apply trust levels (from admin database)
   ↓
4. Add blacklist entries (from admin database)
   ↓
5. Generate plugins.json
   ↓
6. Serve at /api/v3/plugins.json
```

### Pseudocode

```python
def generate_registry():
    plugins = []

    for plugin_repo_url in get_registered_plugins():
        # Clone or update repository
        repo_path = clone_or_update(plugin_repo_url)

        # Read MANIFEST.toml
        manifest = read_toml(repo_path / 'MANIFEST.toml')

        # Build plugin entry
        plugin = {
            'id': derive_id(plugin_repo_url),
            'name': manifest['name'],
            'description': manifest['description'],
            'git_url': plugin_repo_url,
            'categories': normalize_to_array(manifest.get('categories') or manifest.get('category')),
            'authors': normalize_to_array(manifest.get('authors') or manifest.get('author')),
            'min_api_version': manifest['api'][0],
            'trust_level': get_trust_level(plugin_repo_url),  # Set by admin
            'added_at': get_added_timestamp(plugin_repo_url),
            'updated_at': datetime.now().isoformat()
        }

        # Include translations if present
        if 'name_i18n' in manifest:
            plugin['name_i18n'] = manifest['name_i18n']
        if 'description_i18n' in manifest:
            plugin['description_i18n'] = manifest['description_i18n']

        # Optional: max_api_version
        if len(manifest['api']) > 1:
            plugin['max_api_version'] = manifest['api'][-1]

        plugins.append(plugin)

    # Get blacklist from database
    blacklist = get_blacklist_entries()

    # Generate final JSON
    registry = {
        'api_version': '3.0',
        'last_updated': datetime.now().isoformat(),
        'plugins': plugins,
        'blacklist': blacklist
    }

    # Write to file
    write_json('plugins.json', registry)

    return registry
```

---

## Admin Interface

### Plugin Management

**Add Plugin:**
1. Admin enters git repository URL
2. System validates repository (checks for MANIFEST.toml)
3. System extracts metadata
4. Admin assigns trust level (default: `community`)
5. Plugin added to registry

**Update Plugin:**
- Automatic: Daily sync pulls latest MANIFEST.toml
- Manual: Admin can force refresh

**Remove Plugin:**
1. Admin marks plugin as removed
2. Plugin removed from next registry generation
3. Optionally add to blacklist

### Trust Level Management

**Interface:**
```
Plugin: Last.fm Scrobbler
Repository: https://github.com/metabrainz/picard-plugin-lastfm
Current Trust Level: [official ▼]
  - official (Picard Team)
  - trusted (Trusted Author)
  - community (Community)

[Save] [Cancel]
```

**Workflow:**
1. Admin selects plugin
2. Changes trust level dropdown
3. Adds reason for change (optional)
4. Saves
5. Next registry generation includes new trust level

### Blacklist Management

**Add to Blacklist:**
```
Git URL: https://github.com/badactor/malicious-plugin
Reason: Contains malicious code
Pattern Type:
  ( ) Specific repository
  (•) Organization pattern (blocks all repos from this org)

[Add to Blacklist]
```

**Blacklist Entry Types:**
1. **Specific repository:** Exact URL match
2. **Organization pattern:** Wildcard pattern (e.g., `https://github.com/badorg/*`)

**Remove from Blacklist:**
1. Admin selects blacklist entry
2. Confirms removal
3. Plugin can be installed again

---

## Translation Extraction

### From MANIFEST.toml

The website extracts translations directly from MANIFEST.toml:

**Input (MANIFEST.toml):**
```toml
name = "Last.fm Scrobbler"
description = "Scrobble your music to Last.fm"

[name_i18n]
de = "Last.fm-Scrobbler"
fr = "Scrobbleur Last.fm"

[description_i18n]
de = "Scrobble deine Musik zu Last.fm"
fr = "Scrobblez votre musique sur Last.fm"
```

**Output (registry JSON):**
```json
{
  "name": "Last.fm Scrobbler",
  "description": "Scrobble your music to Last.fm",
  "name_i18n": {
    "de": "Last.fm-Scrobbler",
    "fr": "Scrobbleur Last.fm"
  },
  "description_i18n": {
    "de": "Scrobble deine Musik zu Last.fm",
    "fr": "Scrobblez votre musique sur Last.fm"
  }
}
```

### Benefits

- Single source of truth (MANIFEST.toml)
- No separate translation files needed for registry
- Plugin developers manage translations
- Website automatically includes them

---

## API Endpoints

### GET /api/v3/plugins.json

**Description:** Returns complete plugin registry

**Response:** JSON object with plugins and blacklist

**Caching:**
- Cache-Control: public, max-age=3600 (1 hour)
- ETag support for conditional requests
- Last-Modified header

**Example:**
```bash
curl https://picard.musicbrainz.org/api/v3/plugins.json
```

### Future Endpoints (Optional)

- `GET /api/v3/plugins/<id>` - Single plugin details
- `GET /api/v3/plugins/search?q=<term>` - Search plugins
- `GET /api/v3/plugins/category/<category>` - Filter by category

---

## Submission Workflow

### Plugin Submission

**Option 1: GitHub PR**
1. Developer creates PR to add plugin to registry
2. PR includes git repository URL
3. Picard team reviews
4. Assigns trust level
5. Merges PR
6. Plugin appears in next registry generation

**Option 2: Web Form**
1. Developer fills out submission form
2. Provides git repository URL
3. System validates MANIFEST.toml
4. Creates pending submission
5. Picard team reviews
6. Approves with trust level assignment
7. Plugin added to registry

### Validation

Before accepting submission:
- ✅ Repository is accessible
- ✅ MANIFEST.toml exists and is valid
- ✅ Required fields present
- ✅ API version is supported
- ✅ License is valid SPDX identifier
- ✅ Not already in registry
- ✅ Not blacklisted

---

## Database Schema

### plugins table

```sql
CREATE TABLE plugins (
    id SERIAL PRIMARY KEY,
    plugin_id VARCHAR(100) UNIQUE NOT NULL,
    git_url VARCHAR(500) UNIQUE NOT NULL,
    trust_level VARCHAR(20) NOT NULL,
    added_at TIMESTAMP NOT NULL,
    added_by INTEGER REFERENCES users(id),
    enabled BOOLEAN DEFAULT TRUE
);
```

### blacklist table

```sql
CREATE TABLE blacklist (
    id SERIAL PRIMARY KEY,
    git_url VARCHAR(500) NOT NULL,
    reason TEXT NOT NULL,
    blacklisted_at TIMESTAMP NOT NULL,
    blacklisted_by INTEGER REFERENCES users(id),
    pattern_type VARCHAR(20) DEFAULT 'specific'
);
```

### trust_level_history table

```sql
CREATE TABLE trust_level_history (
    id SERIAL PRIMARY KEY,
    plugin_id INTEGER REFERENCES plugins(id),
    old_trust_level VARCHAR(20),
    new_trust_level VARCHAR(20) NOT NULL,
    reason TEXT,
    changed_at TIMESTAMP NOT NULL,
    changed_by INTEGER REFERENCES users(id)
);
```

---

## Security Considerations

1. **Repository validation:** Verify git URLs before cloning
2. **Sandboxed cloning:** Clone repositories in isolated environment
3. **TOML parsing:** Use safe TOML parser (no code execution)
4. **Rate limiting:** Limit registry generation frequency
5. **Access control:** Only admins can modify trust levels and blacklist
6. **Audit log:** Track all changes to registry

---

## Monitoring

### Metrics to Track

- Registry generation time
- Number of plugins per trust level
- Blacklist size
- Failed repository clones
- Invalid MANIFEST.toml files
- API endpoint response times
- Cache hit rates

### Alerts

- Registry generation failures
- Sudden increase in blacklist entries
- Repository clone failures
- Invalid MANIFEST.toml in registered plugins

---

## Plugin Marketplace / Browser (Future)

### Overview

A web-based plugin browser for discovering and learning about registered plugins.

**Community Feedback:**
> **rdswift:** "My short answer to this is 'Yes', even though it may require significant curation effort depending on the extent of the plugins included. I believe that there is significant value in users being able to access a list of available plugins from a common site, especially if they can filter by category and/or plugin author, and search within the plugin descriptions.
>
> If the plugin browser is only displaying information for plugins in the registry, then the system can be automated to use the information provided via the registry item manifests (or a database built from the manifest information), and serve the pages based upon the results of API queries. In this case, the plugin browser could (and should) be served from the picard.musicbrainz.org domain.
>
> If the plugin browser is intended to also include plugins not included in the registry, then the complexity (and curation effort) increases significantly.
>
> A rudimentary list of plugins not included in the official plugin list is currently available on a Picard Resources page in the MusicBrainz Wiki. My recommendation is to continue using the Wiki for this purpose, curated by the users, which would allow rudimentary discovery of the 'unofficial' unregistered plugins. The full 'plugin browser' experience would be reserved for registered plugins."

### Recommended Approach

**For Registered Plugins:**
- Web-based browser at picard.musicbrainz.org/plugins
- Automated from registry JSON data
- Filter by: category, trust level, author
- Search by: name, description, keywords
- Display: name, description, authors, trust level, categories
- Link to: repository, documentation (if provided)
- One-click install command shown

**For Unregistered Plugins:**
- Continue using MusicBrainz Wiki
- User-curated list
- Minimal information (name, URL, description)
- Clear indication these are not in official registry

### Plugin Browser Features

**Browse Page:**
```
Picard Plugins

[Search: ____________] [Filter ▼]

Official Plugins (5)
  🛡️ Last.fm Scrobbler
     Scrobble your music to Last.fm
     Authors: MusicBrainz Picard Team
     Categories: metadata
     [Install: picard plugins --install lastfm]

Trusted Plugins (12)
  ✓ Discogs
     Get metadata from Discogs
     Authors: Bob Swift
     Categories: metadata
     [Install: picard plugins --install discogs]

Community Plugins (45)
  ⚠️ Custom Tagger
     Apply custom tagging rules
     Authors: John Doe
     Categories: metadata
     [Install: picard plugins --install https://github.com/user/plugin]
```

**Plugin Detail Page:**
```
Last.fm Scrobbler 🛡️

Scrobble your music to Last.fm and update your listening history.

Trust Level: Official (Picard Team)
Authors: MusicBrainz Picard Team, Philipp Wolfer
Categories: metadata
License: GPL-2.0-or-later
Repository: https://github.com/metabrainz/picard-plugin-lastfm
Documentation: https://picard-docs.musicbrainz.org/plugins/lastfm

Installation:
  picard plugins --install lastfm

Requirements:
  - Picard 3.0+
  - API version: 3.0

[View on GitHub] [Report Issue]
```

### Implementation

**Technology:**
- Static site generation from registry JSON
- Or dynamic pages from database
- Served from picard.musicbrainz.org
- Responsive design for mobile

**Data Source:**
- Registry JSON (plugins.json)
- No additional curation needed
- Automatic updates when registry updates

**Submission Process:**
1. Developer submits plugin via GitHub PR or web form
2. Picard team reviews
3. Assigns trust level
4. Plugin appears in registry and browser

### Benefits

- Easy plugin discovery
- No manual curation for registered plugins
- Clear trust level indicators
- Simple installation instructions
- Links to documentation and source

---

## See Also

- **[REGISTRY.md](REGISTRY.md)** - Registry JSON schema and client integration
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[SECURITY.md](SECURITY.md)** - Security model
