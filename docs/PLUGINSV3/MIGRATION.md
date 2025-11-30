# Plugin Migration Guide: v2 to v3

This document provides a comprehensive guide for migrating plugins from Picard Plugin v2 to v3.

---

## Overview

Plugin v3 introduces significant changes:
- Git-based distribution (no more ZIP files)
- TOML manifest instead of Python metadata
- New PluginApi for accessing Picard functionality
- JSON-based translations (Plugin v2 had no translation support)
- PyQt6 instead of PyQt5

**Good news**: An automated migration tool handles **94.5%** of plugins automatically!

---

## Automated Migration Tool

### Quick Start

```bash
# Migrate your plugin
python scripts/migrate_plugin.py old_plugin.py output_directory

# Example
python scripts/migrate_plugin.py featartist.py featartist_v3
```

### What It Does Automatically

The migration tool (`scripts/migrate_plugin.py`) automatically handles:

1. ✅ **Metadata Extraction** - Creates MANIFEST.toml from PLUGIN_* variables
2. ✅ **Code Conversion** - Converts register calls to `enable(api)`
3. ✅ **PyQt5 → PyQt6** - Converts 80+ enum patterns, imports, methods
4. ✅ **Config/Log Access** - Converts to `api.logger.*` and `api.global_config.*`
5. ✅ **Function Signatures** - Fixes processor signatures (removes extra parameters)
6. ✅ **Decorator Patterns** - Converts `@register_*` decorators
7. ✅ **UI File Regeneration** - Regenerates `ui_*.py` from `.ui` using pyuic6
8. ✅ **API Injection** - Adds `api` parameter to OptionsPage/Action classes
9. ✅ **File Copying** - Copies all plugin files (Python modules, docs, assets)
10. ✅ **Conflict Handling** - Renames conflicting files with .orig extension
11. ✅ **Code Formatting** - Formats output with ruff (handles errors gracefully)

### Supported Registration Patterns

- Metadata processors (track, album, file)
- Script functions
- Options pages
- UI actions (cluster, file, album, track, clusterlist)
- Cover art providers
- Qualified imports (`metadata.register_*`, `providers.register_*`)
- Instantiated registrations (`register_action(MyAction())`)
- Instantiated object methods (`register_processor(MyClass().method)`)

### Success Rate

Based on testing all 73 plugins from picard-plugins repository:
- **34.2%** Perfect (zero manual work) - 25 plugins
- **60.3%** Good (minor import review) - 44 plugins
- **5.5%** Minimal (manual work needed) - 4 edge cases
- **0%** Failed

**Overall: 94.5% success rate** (69/73 automatic or near-automatic)

The 4 plugins requiring manual work use non-standard patterns (custom registration, function-scoped registrations, complex constructors).

### Example Output

```
Migrating plugin: Keep tags
  Author: Wieland Hoffmann
  Version: 1.2.1
  Created: /tmp/keep_v3/MANIFEST.toml
  Created: /tmp/keep_v3/__init__.py
  Regenerated: ui_options.py (from ui_options.ui)

✓ Copied 3 file(s)
✓ Copied 1 directory(ies)

✓ Converted log.* calls to api.logger.*
✓ Converted config.setting to api.global_config.setting
✓ Injected api in MyOptionsPage.__init__

Migration complete! Plugin saved to: /tmp/keep_v3
```

### After Migration

1. Review the generated code
2. Address any warnings
3. Create git repository
4. Test installation

---

## Quick Migration Checklist

### Automated (Done by Tool)
- [x] Extract metadata → MANIFEST.toml
- [x] Remove metadata from `__init__.py`
- [x] Convert register calls → `enable(api)`
- [x] Update Qt5 → Qt6
- [x] Fix function signatures
- [x] Convert config/log access

### Manual (If Needed)
- [ ] Create git repository
- [ ] Review warnings from migration tool
- [ ] Add translations (if needed)
- [ ] Test functionality

---

## Step-by-Step Migration

### Step 1: Run Migration Tool

```bash
# Create new repository
mkdir picard-plugin-myplugin
cd picard-plugin-myplugin
git init

# Copy plugin files
cp -r ~/old-plugin/* .

# Create .gitignore
cat > .gitignore << EOF
__pycache__/
*.pyc
*.pyo
.DS_Store
EOF

# Initial commit
git add .
git commit -m "Initial commit - v2 plugin"
```

### Step 2: Create MANIFEST.toml

**Old (v2) - in `__init__.py`:**
```python
PLUGIN_NAME = "Example Plugin"
PLUGIN_AUTHOR = "John Doe"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0", "2.1"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_DESCRIPTION = "Example plugin for demonstration"
```

**New (v3) - MANIFEST.toml:**
```toml
uuid = "550e8400-e29b-41d4-a716-446655440000"  # Generate with: uuidgen
name = "Example Plugin"
version = "1.0.0"
description = "Example plugin for demonstration"
api = ["3.0"]
authors = ["John Doe"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
categories = ["metadata"]
```

```bash
# Run the migration tool
python scripts/migrate_plugin.py my_plugin.py my_plugin_v3

# Or for multi-file plugins
python scripts/migrate_plugin.py my_plugin/__init__.py my_plugin_v3
```

The tool will:
- Extract all PLUGIN_* metadata
- Create MANIFEST.toml
- Convert code to V3 format
- Handle Qt5 → Qt6 conversions
- Regenerate UI files
- Format code with ruff

### Step 2: Review Generated Code

Check the output for any warnings:

```
⚠️  Class 'MyClass' uses 'api' but injection failed - needs manual review
```

Address these warnings before proceeding.

### Step 3: Create Git Repository

```bash
cd my_plugin_v3
git init
git add .
git commit -m "Migrated to V3"
```

---

## API Access Pattern

### Explicit Parameter Passing

The `PluginApi` is passed explicitly to functions and classes:

**For Processors:** API is injected as first parameter via `functools.partial`

```python
def process_track(api, track, metadata):
    """API is automatically injected as first parameter."""
    api.logger.info("Processing track")
    if api.global_config.setting['example_enabled']:
        metadata['example'] = 'value'


def enable(api):
    # Picard wraps this as partial(process_track, api)
    api.register_track_metadata_processor(process_track)
```

**For Classes:** API is passed to `__init__` and stored as `self.api`

```python
class ExampleOptionsPage(api.OptionsPage):
    NAME = "example"
    TITLE = "Example"
    PARENT = "plugins"

    def __init__(self, api=None, parent=None):
        super().__init__(parent)
        self.api = api

    def load(self):
        self.api.logger.debug("Loading options")
        enabled = self.api.global_config.setting.get('example_enabled', False)


def enable(api):
    """Entry point - register with API."""
    api.register_track_metadata_processor(process_track)
    api.register_options_page(ExampleOptionsPage)
```

**Why this works:**
- Processors receive `api` as first parameter (injected via `functools.partial`)
- Classes receive `api` in `__init__` (passed during instantiation)
- No global variables needed
- Clean, explicit, and testable

---

## Step-by-Step Migration (Manual)

If not using the migration tool, follow these steps:

### Step 1: Create MANIFEST.toml

| v2 | v3 |
|----|-----|
| `from picard import log` | `api.log` |
| `from picard import config` | `api.config` |
| `from picard.tagger import tagger` | `api.tagger` |
| `register_track_metadata_processor()` | `@api.on_track_metadata_loaded` |
| `register_album_metadata_processor()` | `@api.on_album_metadata_loaded` |
| `register_file_action()` | `@api.register_file_action()` |
| `register_album_action()` | `@api.register_album_action()` |

### Step 5: Update Qt Imports

**Old (v2) - PyQt5:**
```python
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QDialog, QPushButton
```

**New (v3) - PyQt6:**
```python
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QDialog, QPushButton
```

**Key PyQt6 changes:**
- `Qt.AlignCenter` → `Qt.AlignmentFlag.AlignCenter`
- `QHeaderView.ResizeToContents` → `QHeaderView.ResizeMode.ResizeToContents`
- `exec_()` → `exec()`

### Step 6: Add Translations (Work in Progress)

Translation system for plugins is still under development.

### Step 7: Update Configuration

**Old (v2):**
```python
from picard import config

# Read setting
value = config.setting['example_plugin_setting']

# Write setting
config.setting['example_plugin_setting'] = 'new value'
```

**New (v3):**
```python
def enable(api: PluginApi):
    # Read setting
    value = api.config.setting['example_plugin']['setting']

    # Write setting
    api.config.setting['example_plugin']['setting'] = 'new value'
```

---

## Complete Example: Before and After

### Before (v2)

**Directory structure:**
```
example-plugin/
  __init__.py
  ui_options.py
```

**__init__.py:**
```python
PLUGIN_NAME = "Example Plugin"
PLUGIN_AUTHOR = "John Doe"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_DESCRIPTION = "Example plugin"

from picard import log, config
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from PyQt5.QtWidgets import QCheckBox

class ExampleOptionsPage(OptionsPage):
    NAME = "example"
    TITLE = "Example Plugin"
    PARENT = "plugins"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkbox = QCheckBox("Enable processing")
        self.layout().addWidget(self.checkbox)

    def load(self):
        self.checkbox.setChecked(config.setting['example_enabled'])

    def save(self):
        config.setting['example_enabled'] = self.checkbox.isChecked()

def process_track(album, metadata, track, release):
    log.info("Processing track: %s", track)
    if config.setting['example_enabled']:
        metadata['example'] = 'processed'

def register():
    log.info("Registering Example Plugin")
    register_track_metadata_processor(process_track)
    register_options_page(ExampleOptionsPage)
```

### After (v3)

**Directory structure:**
```
picard-plugin-example/
  MANIFEST.toml
  __init__.py
  ui_options.py
```

**MANIFEST.toml:**
```toml
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Example Plugin"
version = "1.0.0"
description = "Example plugin for demonstration"
api = ["3.0"]
authors = ["John Doe"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
categories = ["metadata"]
```

**__init__.py:**
```python
from PyQt6.QtWidgets import QCheckBox


class ExampleOptionsPage(api.OptionsPage):
    NAME = "example"
    TITLE = "Example Plugin"
    PARENT = "plugins"

    def __init__(self, api=None, parent=None):
        super().__init__(parent)
        self.api = api
        self.checkbox = QCheckBox("Enable processing")
        self.layout().addWidget(self.checkbox)

    def load(self):
        enabled = self.api.global_config.setting.get('example_enabled', False)
        self.checkbox.setChecked(enabled)

    def save(self):
        self.api.global_config.setting['example_enabled'] = self.checkbox.isChecked()


def process_track(api, track, metadata):
    api.logger.info(f"Processing track: {track}")
    if api.global_config.setting.get('example_enabled', False):
        metadata['example'] = 'processed'


def enable(api):
    """Entry point for the plugin."""
    api.logger.info("Example Plugin loaded")
    api.register_track_metadata_processor(process_track)
    api.register_options_page(ExampleOptionsPage)
```

---

## Breaking Changes

### Removed Features
- ZIP-based distribution
- Python metadata in `__init__.py`
- Direct `tagger` access
- PyQt5 support

### New Features
- JSON-based translations (Plugin v2 had no translation support)

### Changed Behavior
- Plugins must be in git repositories
- Entry point is `enable()` instead of `register()`
- All Picard access through PluginApi
- Configuration namespaced under plugin name
- Translations use JSON instead of .mo files

---

## Migration Tool

A migration tool is available in the Picard repository:

```bash
# Migrate plugin
python scripts/migrate_plugin.py /path/to/old-plugin.py /path/to/new-plugin

# Review changes
cd /path/to/new-plugin
git diff
```

The tool will:
- Create MANIFEST.toml from Python metadata
- Update entry point to `enable()`
- Convert common API calls
- Update Qt imports
- Create git repository structure

**Note:** Manual review and testing still required.

---

## Testing Your Migrated Plugin

```bash
# Install from local directory
picard plugins --install ~/dev/picard-plugin-example

# Test in Picard
picard

# Check logs for errors
tail -f ~/.config/MusicBrainz/Picard/picard.log

# Uninstall
picard plugins --uninstall example
```

---

## Publishing Your Plugin

1. Push to GitHub/GitLab
2. Tag release: `git tag v1.0.0 && git push --tags`
3. Submit to plugin registry (Phase 3)
4. Update plugin documentation

---

## Getting Help

- **Documentation:** https://picard-docs.musicbrainz.org/
- **Forum:** https://community.metabrainz.org/c/picard
- **GitHub:** https://github.com/metabrainz/picard

---

## See Also

- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[TRANSLATIONS.md](TRANSLATIONS.md)** - Translation system
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap
- **[DECISIONS.md](DECISIONS.md)** - Design decisions
