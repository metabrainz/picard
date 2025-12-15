# MANIFEST.toml Specification and Plugin Development Guide

This document describes the MANIFEST.toml format and how to develop plugins for Picard v3.

---

## Quick Start

### Minimal Plugin Structure

```text
my-plugin/
├── MANIFEST.toml
└── __init__.py
```

### Minimal MANIFEST.toml

```toml
uuid = "550e8400-e29b-41d4-a716-446655440000"  # Generate with: uuidgen or python -c "import uuid; print(uuid.uuid4())"
name = "My Plugin"
description = "Short description of what the plugin does"
api = ["3.0"]
```

**Note:** For more complex plugins, consider adding `long_description` to provide detailed information about features, requirements, and usage. See [Description Fields](#description-fields-short-vs-long) below.

### Minimal Plugin Code

```python
# __init__.py
from picard.plugin3.api import PluginApi

def enable(api: PluginApi):
    """Called when plugin is enabled"""

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

def disable():
    """Called when plugin is disabled (optional)"""
    # Clean up resources if needed
    pass
```

---

## MANIFEST.toml Field Reference

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `uuid` | string | Unique plugin identifier (UUID v4) | `"550e8400-e29b-41d4-a716-446655440000"` |
| `name` | string | Plugin display name | `"ListenBrainz Submitter"` |
| `description` | string | Short description (one line, 1-200 chars) | `"Submit your music to ListenBrainz"` |
| `api` | array | Supported API versions | `["3.0", "3.1"]` |

**UUID Field:**
- Must be a valid UUID v4 (RFC 4122)
- Generated once when creating the plugin (use `uuidgen` or `uuid.uuid4()`)
- Never changes, even if plugin is renamed or moved to different repository
- Used for plugin identity, blacklisting, and tracking across repository changes
- Ensures global uniqueness and prevents name collision attacks

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `authors` | array | Plugin author/contributor names | `["John Doe", "Jane Smith"]` |
| `maintainers` | array | Plugin maintainer names | `["John Doe"]` |
| `license` | string | SPDX license identifier | `"GPL-2.0-or-later"` |
| `license_url` | string | URL to license text | `"https://..."` |
| `long_description` | string | Detailed description (multi-line, 1-2000 chars, Python-Markdown supported) | See below |
| `categories` | array | Plugin categories | `["metadata", "coverart"]` |
| `homepage` | string | Plugin homepage URL | `"https://..."` |
| `min_python_version` | string | Minimum Python version | `"3.9"` |
| `source_locale` | string | Source language for translations | `"en"` (default) |

### Translation Fields (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `name_i18n` | table | Translated names (locale → string) |
| `description_i18n` | table | Translated short descriptions (locale → string) |
| `long_description_i18n` | table | Translated long descriptions (locale → string) |

---

## Complete MANIFEST.toml Example

```toml
uuid = "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"
name = "ListenBrainz Submitter"
description = "Submit your music to ListenBrainz"
long_description = """
This plugin integrates with ListenBrainz to submit your music listening history.

Features:
- Real-time submitting listens as you play
- Batch submission of past plays
- Love/unlove tracks directly from Picard
- Configurable submitting listens rules
- Support for multiple ListenBrainz accounts

Requirements:
- Free ListenBrainz account (sign up at https://listenbrainz.org)
- Network access for API communication

The plugin respects your privacy and only sends data you explicitly choose to submit listens.
"""
api = ["3.0", "3.1"]
authors = ["MusicBrainz Picard Team", "Philipp Wolfer"]
maintainers = ["Philipp Wolfer"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
homepage = "https://github.com/metabrainz/picard-plugin-listenbrainz"
categories = ["metadata"]
min_python_version = "3.9"
source_locale = "en"

[name_i18n]
de = "ListenBrainz-Submitter"
fr = "Soumetteur ListenBrainz"
ja = "ListenBrainzサブミッター"

[description_i18n]
de = "Submit listens deine Musik zu ListenBrainz"
fr = "Submit listensz votre musique sur ListenBrainz"
ja = "ListenBrainzに音楽をスクロブルする"

[long_description_i18n]
de = """
Dieses Plugin integriert sich mit ListenBrainz, um deine Musikhörhistorie zu Hördaten übermitteln.

Funktionen:
- Echtzeit-Übermittlung während du hörst
- Batch-Übermittlung vergangener Wiedergaben
- Tracks direkt aus Picard lieben/nicht mehr lieben
- Konfigurierbare Übermittlungsregeln
- Unterstützung für mehrere ListenBrainz-Konten

Anforderungen:
- Kostenloses ListenBrainz-Konto (Anmeldung unter https://listenbrainz.org)
- Netzwerkzugriff für API-Kommunikation

Das Plugin respektiert deine Privatsphäre und sendet nur Daten, die du explizit Hördaten übermitteln möchtest.
"""
fr = """
Ce plugin s'intègre avec ListenBrainz pour submit listensr votre historique d'écoute musicale.

Fonctionnalités:
- Soumission en temps réel pendant l'écoute
- Soumission par lots des lectures passées
- Aimer/ne plus aimer les pistes directement depuis Picard
- Règles de submitting listens configurables
- Support de plusieurs comptes ListenBrainz

Exigences:
- Compte ListenBrainz gratuit (inscription sur https://listenbrainz.org)
- Accès réseau pour la communication API

Le plugin respecte votre vie privée et n'envoie que les données que vous choisissez explicitement de submit listensr.
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
```text
🛡️ ListenBrainz Submitter
   Submit your music to ListenBrainz
   Authors: Picard Team | Category: metadata
```

**Search Results (uses `description`):**
```text
$ picard-plugins --search submit listens

Found 1 plugin:
  🛡️ listenbrainz - ListenBrainz Submitter
     Submit your music to ListenBrainz
```

**Plugin Detail Page (uses `long_description` if available):**
```text
ListenBrainz Submitter 🛡️

This plugin integrates with ListenBrainz to submit your music listening history.

Features:
- Real-time submitting listens as you play
- Batch submission of past plays
- Love/unlove tracks directly from Picard
- Configurable submitting listens rules

Requirements:
- Free ListenBrainz account
- Network access

[Install] [View on GitHub]
```

**CLI Info Command (uses `long_description` if available):**
```text
$ picard-plugins --info listenbrainz

Plugin: ListenBrainz Submitter
Status: enabled
Version: v2.1.0 (ref: v2.1.0, commit: a1b2c3d)

Description:
  This plugin integrates with ListenBrainz to submit your music
  listening history.

  Features:
  - Real-time submitting listens as you play
  - Batch submission of past plays
  - Love/unlove tracks directly from Picard

  Requirements:
  - Free ListenBrainz account
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
description = "Submit your music to ListenBrainz"
long_description = """
Full English description here...
"""

[description_i18n]
de = "Submit listens deine Musik zu ListenBrainz"

[long_description_i18n]
de = """
Vollständige deutsche Beschreibung hier...
"""
```

### Best Practices

1. **Keep `description` concise**: One clear sentence is better than cramming multiple ideas
2. **Use `long_description` for details**: Features, requirements, configuration steps
3. **Structure `long_description`**: Use blank lines to separate sections
4. **Use Markdown formatting**: `long_description` supports Markdown (bold, lists, code blocks, etc.)
5. **Translate both**: Provide translations for both fields if possible
6. **Avoid redundancy**: Don't repeat the short description in the long one
7. **Be specific**: Mention actual features, not vague promises
8. **Include requirements**: List any accounts, network access, or dependencies needed

**Markdown Support:**
- `long_description` supports Markdown via Python-Markdown (no HTML)
- Use `**bold**`, `*italic*`, `- lists`, `` `code` ``, etc.
- Follows original Markdown syntax (not CommonMark)
- Markdown is rendered in plugin detail pages and documentation
- Keep formatting simple and readable as plain text

---

## Field Validation Rules

### `name`
- Required
- String, 1-100 characters
- Should be human-readable display name
- Can contain spaces and special characters

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
- Supports **Markdown formatting** (Python-Markdown syntax, no HTML)
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
- Optional
- Array of strings
- At least one author if present
- Can be names or "Organization Name"
- Informative only - for attribution

### `maintainers`
- Optional
- Array of strings
- At least one maintainer if present
- Can be names or "Organization Name"
- Informative only - indicates who actively maintains the plugin

### `license`
- Optional (recommended)
- SPDX license identifier
- Common values: `"GPL-2.0-or-later"`, `"MIT"`, `"Apache-2.0"`
- See <https://spdx.org/licenses/>

### `license_url`
- Optional
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

### `source_locale`
- Optional
- Source language for plugin translations
- Default: `"en"`
- Used by translation system to determine fallback language
- Format: locale code like `"en"`, `"de"`, `"fr"`, `"pt_BR"`, etc.
- See [TRANSLATIONS.md](TRANSLATIONS.md) for details on plugin translation system

---

## Plugin Development Guide

### Plugin Entry Point

Every plugin must have an `__init__.py` file with an `enable()` function:

```python
from picard.plugin3.api import PluginApi

def enable(api: PluginApi):
    """
    Called when plugin is enabled.
    This is where you register hooks, actions, and initialize the plugin.

    Args:
        api: PluginApi instance providing access to Picard
    """
    # Your plugin initialization code here
    pass

def disable():
    """
    Called when plugin is disabled (optional).
    Use this to clean up resources, stop threads, close connections, etc.
    """
    # Your cleanup code here (if needed)
    pass
```

**Plugin Lifecycle:**

1. **Plugin discovered** - Picard finds plugin directory and reads MANIFEST.toml
2. **Module loaded** - Python imports the `__init__.py` module
3. **`enable(api)` called** when:
   - Plugin is installed and enabled
   - User enables the plugin
   - Picard starts with plugin in enabled list
4. **`disable()` called** when:
   - User disables the plugin
   - Plugin is uninstalled
   - Picard shuts down (optional)

**Note:** The `disable()` function is optional. Only implement it if your plugin needs to clean up resources (close files, stop threads, disconnect from services, etc.). Most simple plugins don't need it.

### Using PluginApi

The `PluginApi` object provides access to all Picard functionality:

```python
def enable(api: PluginApi):
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
def enable(api: PluginApi):
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

```text
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

```text
my-plugin/
├── MANIFEST.toml
├── __init__.py
└── data/
    ├── config.json
    └── rules.txt
```

Access data files:

```python
def enable(api: PluginApi):
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
from picard.plugin3.api import PluginApi

def enable(api: PluginApi):
    @api.on_album_metadata_loaded
    def add_custom_tag(album, metadata):
        # Add custom tag to all tracks
        metadata['custom_tag'] = 'My Value'
```

### Cover Art Provider

```python
# __init__.py
from picard.plugin3.api import PluginApi

def enable(api: PluginApi):
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
from picard.plugin3.api import PluginApi

def enable(api: PluginApi):
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
7. **Version properly** - Use git tags for releases (e.g., v1.0.0, v2.1.0)
8. **Declare dependencies** - Document required Python packages

---

## Testing Your Plugin

### Local Development

```bash
# Install from local directory
picard-plugins --install ~/dev/my-plugin

# Test changes
picard-plugins --update my-plugin

# Switch to development branch
picard-plugins --switch-ref my-plugin dev
```

### Debugging

```python
def enable(api: PluginApi):
    # Use logging
    api.log.info("Plugin loaded")
    api.log.debug("Debug message")
    api.log.error("Error message")

    # Check plugin info
    # picard-plugins --info <plugin-name>
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
