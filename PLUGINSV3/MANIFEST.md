# MANIFEST.toml Specification and Plugin Development Guide

This document describes the MANIFEST.toml format and how to develop plugins for Picard v3.

---

## Quick Start

### Minimal Plugin Structure

```
my-plugin/
├── MANIFEST.toml
└── __init__.py
```

### Minimal MANIFEST.toml

```toml
name = "My Plugin"
version = "1.0.0"
description = "Short description of what the plugin does"
api = ["3.0"]
authors = ["Your Name"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
```

**Note:** For more complex plugins, consider adding `long_description` to provide detailed information about features, requirements, and usage. See [Description Fields](#description-fields-short-vs-long) below.

### Minimal Plugin Code

```python
# __init__.py
from picard.plugin3 import PluginApi

def plugin_main(api: PluginApi):
    """Entry point for the plugin"""

    # Register hooks
    @api.on_album_metadata_loaded
    def on_album_loaded(album, metadata):
        # Do something with album metadata
        pass

    # Register UI actions
    @api.register_album_action("My Action")
    def my_action(album):
        # Do something when user clicks action
        pass
```

---

## MANIFEST.toml Field Reference

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Plugin display name | `"Last.fm Scrobbler"` |
| `version` | string | Plugin version (semver) | `"1.0.0"` |
| `description` | string | Short description (one line, 1-200 chars) | `"Scrobble your music to Last.fm"` |
| `api` | array | Supported API versions | `["3.0", "3.1"]` |
| `authors` | array | Plugin author names | `["John Doe", "Jane Smith"]` |
| `license` | string | SPDX license identifier | `"GPL-2.0-or-later"` |
| `license_url` | string | URL to license text | `"https://..."` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `long_description` | string | Detailed description (multi-line, 1-2000 chars) | See below |
| `categories` | array | Plugin categories | `["metadata", "coverart"]` |
| `homepage` | string | Plugin homepage URL | `"https://..."` |
| `min_python_version` | string | Minimum Python version | `"3.9"` |

### Translation Fields (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `name_i18n` | table | Translated names (locale → string) |
| `description_i18n` | table | Translated short descriptions (locale → string) |
| `long_description_i18n` | table | Translated long descriptions (locale → string) |

---

## Complete MANIFEST.toml Example

```toml
name = "Last.fm Scrobbler"
version = "2.1.0"
description = "Scrobble your music to Last.fm"
long_description = """
This plugin integrates with Last.fm to scrobble your music listening history.

Features:
- Real-time scrobbling as you listen
- Batch submission of past plays
- Love/unlove tracks directly from Picard
- Configurable scrobbling rules
- Support for multiple Last.fm accounts

Requirements:
- Free Last.fm account (sign up at https://last.fm)
- Network access for API communication

The plugin respects your privacy and only sends data you explicitly choose to scrobble.
"""
api = ["3.0", "3.1"]
authors = ["MusicBrainz Picard Team", "Philipp Wolfer"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
homepage = "https://github.com/metabrainz/picard-plugin-lastfm"
categories = ["metadata"]
min_python_version = "3.9"

[name_i18n]
de = "Last.fm-Scrobbler"
fr = "Scrobbleur Last.fm"
ja = "Last.fmスクロブラー"

[description_i18n]
de = "Scrobble deine Musik zu Last.fm"
fr = "Scrobblez votre musique sur Last.fm"
ja = "Last.fmに音楽をスクロブルする"

[long_description_i18n]
de = """
Dieses Plugin integriert sich mit Last.fm, um deine Musikhörhistorie zu scrobbeln.

Funktionen:
- Echtzeit-Scrobbling während du hörst
- Batch-Übermittlung vergangener Wiedergaben
- Tracks direkt aus Picard lieben/nicht mehr lieben
- Konfigurierbare Scrobbling-Regeln
- Unterstützung für mehrere Last.fm-Konten

Anforderungen:
- Kostenloses Last.fm-Konto (Anmeldung unter https://last.fm)
- Netzwerkzugriff für API-Kommunikation

Das Plugin respektiert deine Privatsphäre und sendet nur Daten, die du explizit scrobbeln möchtest.
"""
fr = """
Ce plugin s'intègre avec Last.fm pour scrobbler votre historique d'écoute musicale.

Fonctionnalités:
- Scrobbling en temps réel pendant l'écoute
- Soumission par lots des lectures passées
- Aimer/ne plus aimer les pistes directement depuis Picard
- Règles de scrobbling configurables
- Support de plusieurs comptes Last.fm

Exigences:
- Compte Last.fm gratuit (inscription sur https://last.fm)
- Accès réseau pour la communication API

Le plugin respecte votre vie privée et n'envoie que les données que vous choisissez explicitement de scrobbler.
"""
```

---

## Description Fields: Short vs Long

### When to Use Each

**`description` (required):**
- Short one-liner (1-200 characters)
- Used in plugin lists, search results, and compact displays
- Should be a complete sentence or phrase
- Focus on what the plugin does, not how

**`long_description` (optional):**
- Detailed explanation (1-2000 characters)
- Used in plugin detail pages and `--info` command
- Can include multiple paragraphs, lists, and details
- Explain features, requirements, usage notes, limitations

### Display Contexts

**Plugin List (uses `description`):**
```
🛡️ Last.fm Scrobbler
   Scrobble your music to Last.fm
   Authors: Picard Team | Category: metadata
```

**Search Results (uses `description`):**
```
$ picard plugins --search scrobble

Found 1 plugin:
  🛡️ lastfm - Last.fm Scrobbler
     Scrobble your music to Last.fm
```

**Plugin Detail Page (uses `long_description` if available):**
```
Last.fm Scrobbler 🛡️

This plugin integrates with Last.fm to scrobble your music listening history.

Features:
- Real-time scrobbling as you listen
- Batch submission of past plays
- Love/unlove tracks directly from Picard
- Configurable scrobbling rules

Requirements:
- Free Last.fm account
- Network access

[Install] [View on GitHub]
```

**CLI Info Command (uses `long_description` if available):**
```
$ picard plugins --info lastfm

Plugin: Last.fm Scrobbler
Status: enabled
Version: 2.1.0

Description:
  This plugin integrates with Last.fm to scrobble your music
  listening history.

  Features:
  - Real-time scrobbling as you listen
  - Batch submission of past plays
  - Love/unlove tracks directly from Picard

  Requirements:
  - Free Last.fm account
  - Network access

[... rest of info ...]
```

### Examples

**Simple plugin (description only):**
```toml
name = "BPM Analyzer"
description = "Analyze and tag BPM (beats per minute)"
```

**Complex plugin (with long_description):**
```toml
name = "Advanced Tagger"
description = "Advanced tagging with custom rules and scripts"
long_description = """
This plugin provides advanced tagging capabilities beyond Picard's built-in features.

Features:
- Custom tagging rules with pattern matching
- Conditional logic for complex scenarios
- Script templates for common tasks
- Batch operations on multiple files
- Preview changes before applying

Use Cases:
- Standardize artist names across your collection
- Apply genre tags based on custom rules
- Clean up inconsistent metadata
- Add custom tags for personal organization

Requirements:
- Basic understanding of Picard's scripting language
- Recommended for advanced users

Configuration:
Access the plugin settings under Options > Plugins > Advanced Tagger
to define your custom rules and scripts.
"""
```

**With translations:**
```toml
description = "Scrobble your music to Last.fm"
long_description = """
Full English description here...
"""

[description_i18n]
de = "Scrobble deine Musik zu Last.fm"

[long_description_i18n]
de = """
Vollständige deutsche Beschreibung hier...
"""
```

### Best Practices

1. **Keep `description` concise**: One clear sentence is better than cramming multiple ideas
2. **Use `long_description` for details**: Features, requirements, configuration steps
3. **Structure `long_description`**: Use blank lines to separate sections
4. **Translate both**: Provide translations for both fields if possible
5. **Avoid redundancy**: Don't repeat the short description in the long one
6. **Be specific**: Mention actual features, not vague promises
7. **Include requirements**: List any accounts, network access, or dependencies needed

---

## Field Validation Rules

### `name`
- Required
- String, 1-100 characters
- Should be human-readable display name
- Can contain spaces and special characters

### `version`
- Required
- Must follow semantic versioning (semver): `MAJOR.MINOR.PATCH`
- Examples: `"1.0.0"`, `"2.1.5"`, `"0.9.0-beta"`

### `description`
- Required
- String, 1-200 characters
- Should be one line (no newlines)
- Brief summary of what the plugin does
- Used in plugin lists and search results

### `long_description`
- Optional
- String, 1-2000 characters
- Can be multi-line (use triple quotes in TOML)
- Detailed description of plugin functionality
- Can include features, requirements, usage notes
- Used in plugin detail pages and `--info` command
- If not provided, `description` is used everywhere

### `api`
- Required
- Array of strings
- Each string is an API version: `"3.0"`, `"3.1"`, etc.
- Plugin will only load if Picard's API version is in this list
- Use multiple versions for compatibility: `["3.0", "3.1"]`

### `authors`
- Required
- Array of strings
- At least one author
- Can be names or "Organization Name"

### `license`
- Required
- SPDX license identifier
- Common values: `"GPL-2.0-or-later"`, `"MIT"`, `"Apache-2.0"`
- See https://spdx.org/licenses/

### `license_url`
- Required
- URL to full license text
- Should be stable URL (not subject to change)

### `categories`
- Optional
- Array of strings
- Valid values: `"metadata"`, `"coverart"`, `"ui"`, `"scripting"`, `"formats"`, `"other"`
- Used for filtering/browsing in registry

### `homepage`
- Optional
- URL to plugin homepage or repository
- Typically GitHub repository URL

### `min_python_version`
- Optional
- Minimum Python version required
- Format: `"3.9"`, `"3.10"`, etc.

---

## Plugin Development Guide

### Plugin Entry Point

Every plugin must have an `__init__.py` file with a `plugin_main()` function:

```python
from picard.plugin3 import PluginApi

def plugin_main(api: PluginApi):
    """
    Entry point for the plugin.
    Called when plugin is loaded.

    Args:
        api: PluginApi instance providing access to Picard
    """
    # Your plugin initialization code here
    pass
```

### Using PluginApi

The `PluginApi` object provides access to all Picard functionality:

```python
def plugin_main(api: PluginApi):
    # Access Picard application
    tagger = api.tagger

    # Access configuration
    config = api.config
    my_setting = config.setting['my_plugin']['my_setting']

    # Register hooks
    @api.on_album_metadata_loaded
    def on_album_loaded(album, metadata):
        # Modify metadata
        metadata['custom_tag'] = 'value'

    # Register UI actions
    @api.register_album_action("My Action")
    def my_action(album):
        # Do something with album
        pass

    # Register file processors
    @api.register_file_processor
    def process_file(file, metadata):
        # Process file
        pass
```

### Available Extension Points

See the PluginApi documentation for complete list of extension points:

- `@api.on_album_metadata_loaded` - Album metadata loaded
- `@api.on_file_metadata_loaded` - File metadata loaded
- `@api.register_album_action(name)` - Add album context menu action
- `@api.register_file_action(name)` - Add file context menu action
- `@api.register_file_processor` - Process files
- `@api.register_cover_art_provider` - Provide cover art
- `@api.register_metadata_provider` - Provide metadata
- `@api.register_script_function(name)` - Add script function
- `@api.register_script_variable(name)` - Add script variable

### Configuration

Plugins can store configuration:

```python
def plugin_main(api: PluginApi):
    config = api.config

    # Read setting
    value = config.setting['my_plugin']['my_setting']

    # Write setting
    config.setting['my_plugin']['my_setting'] = 'new value'

    # Register options page (for GUI)
    @api.register_options_page
    class MyPluginOptions:
        def __init__(self, parent=None):
            # Create options UI
            pass
```

### Translations

Plugins can provide translations using JSON files:

```
my-plugin/
├── MANIFEST.toml
├── __init__.py
└── locale/
    ├── de.json
    ├── fr.json
    └── ja.json
```

See [TRANSLATIONS.md](TRANSLATIONS.md) for details.

### Data Files

Plugins can include additional data files:

```
my-plugin/
├── MANIFEST.toml
├── __init__.py
└── data/
    ├── config.json
    └── rules.txt
```

Access data files:

```python
def plugin_main(api: PluginApi):
    # Get plugin directory
    plugin_dir = api.plugin_dir

    # Read data file
    data_file = plugin_dir / 'data' / 'config.json'
    with open(data_file) as f:
        data = json.load(f)
```

---

## Example Plugins

### Simple Metadata Plugin

```python
# __init__.py
from picard.plugin3 import PluginApi

def plugin_main(api: PluginApi):
    @api.on_album_metadata_loaded
    def add_custom_tag(album, metadata):
        # Add custom tag to all tracks
        metadata['custom_tag'] = 'My Value'
```

### Cover Art Provider

```python
# __init__.py
from picard.plugin3 import PluginApi

def plugin_main(api: PluginApi):
    @api.register_cover_art_provider
    class MyCoverArtProvider:
        def get_cover_art(self, album):
            # Fetch cover art from external source
            url = f"https://example.com/cover/{album.id}"
            return api.download_image(url)
```

### UI Action Plugin

```python
# __init__.py
from picard.plugin3 import PluginApi

def plugin_main(api: PluginApi):
    @api.register_album_action("Export to CSV")
    def export_to_csv(album):
        # Export album data to CSV
        import csv
        with open('export.csv', 'w') as f:
            writer = csv.writer(f)
            for track in album.tracks:
                writer.writerow([track.title, track.artist])
```

---

## Best Practices

1. **Keep it simple** - Start with minimal functionality
2. **Handle errors** - Use try/except for network and file operations
3. **Be efficient** - Don't block the UI thread
4. **Test thoroughly** - Test with various file types and edge cases
5. **Document** - Add docstrings and comments
6. **Follow conventions** - Use Picard's coding style
7. **Version properly** - Use semantic versioning
8. **Declare dependencies** - Document required Python packages

---

## Testing Your Plugin

### Local Development

```bash
# Install from local directory
picard plugins --install ~/dev/my-plugin

# Test changes
picard plugins --update my-plugin

# Switch to development branch
picard plugins --switch-ref my-plugin dev
```

### Debugging

```python
def plugin_main(api: PluginApi):
    # Use logging
    api.log.info("Plugin loaded")
    api.log.debug("Debug message")
    api.log.error("Error message")

    # Check plugin status
    # picard plugins --status
```

---

## Publishing Your Plugin

1. Create git repository
2. Add MANIFEST.toml and code
3. Tag releases: `git tag v1.0.0`
4. Submit to plugin registry (Phase 3)

See [REGISTRY.md](REGISTRY.md) for registry submission process.

---

## Migration from v2

See [MIGRATION.md](MIGRATION.md) for complete migration guide from Plugin v2 to v3.

---

## See Also

- **[ROADMAP.md](ROADMAP.md)** - Development roadmap
- **[CLI.md](CLI.md)** - CLI commands reference
- **[TRANSLATIONS.md](TRANSLATIONS.md)** - Translation system
- **[REGISTRY.md](REGISTRY.md)** - Plugin registry
