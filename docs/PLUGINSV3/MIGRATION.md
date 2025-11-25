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

---

## Quick Migration Checklist

### Structure
- [ ] Create git repository
- [ ] Create MANIFEST.toml with metadata
- [ ] Remove metadata from `__init__.py`
- [ ] Create `locale/` directory for translations (if needed)

### Code Changes
- [ ] Change `register()` to `enable(api: PluginApi)`
- [ ] Update all API calls to use `api.` prefix
- [ ] Replace `from picard import config` with `api.config`
- [ ] Replace `from picard import log` with `api.log`
- [ ] Update Qt5 imports to Qt6 (PyQt5 → PyQt6)
- [ ] Add JSON translations (Plugin v2 had no translation support)

### Testing
- [ ] Test with Picard 3.0
- [ ] Verify all functionality works
- [ ] Check for deprecation warnings
- [ ] Test enable/disable

### Distribution
- [ ] Push to GitHub/GitLab
- [ ] Submit to plugin registry
- [ ] Update documentation

---

## Step-by-Step Migration

### Step 1: Create Git Repository

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
name = "Example Plugin"
version = "1.0.0"
description = "Example plugin for demonstration"
api = ["3.0"]
authors = ["John Doe"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
categories = ["metadata"]
```

### Step 3: Update Plugin Entry Point

**Old (v2):**
```python
from picard import log, config
from picard.metadata import register_track_metadata_processor

def process_track(album, metadata, track, release):
    log.info("Processing track")
    if config.setting['example_enabled']:
        metadata['example'] = 'value'

def register():
    register_track_metadata_processor(process_track)
```

**New (v3):**
```python
from picard.plugin3 import PluginApi

def enable(api: PluginApi):
    """Entry point for the plugin"""

    @api.on_track_metadata_loaded
    def process_track(track, metadata):
        api.log.info("Processing track")
        if api.config.setting['example_enabled']:
            metadata['example'] = 'value'
```

### Step 4: Update API Calls

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

### Step 6: Add Translations (New in v3)

**Old (v2) - No translation support:**
Plugin v2 did not have a translation system for plugins.

**New (v3) - JSON:**
```
locale/
  en.json
  de.json
  fr.json
```

**locale/en.json:**
```json
{
  "ui.button.process": "Process Files",
  "error.network": "Network error: {error}",
  "status.complete": "Processing complete"
}
```

**Usage:**
```python
def enable(api: PluginApi):
    _ = api.gettext

    button_text = _('ui.button.process')
    error_msg = _('error.network', error='Connection timeout')
```

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
  locale/
    de/LC_MESSAGES/
      example.mo
      example.po
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
  locale/
    en.json
    de.json
```

**MANIFEST.toml:**
```toml
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
from picard.plugin3 import PluginApi
from PyQt6.QtWidgets import QCheckBox
from picard.ui.options import OptionsPage

class ExampleOptionsPage(OptionsPage):
    NAME = "example"
    TITLE = "Example Plugin"
    PARENT = "plugins"

    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self.checkbox = QCheckBox("Enable processing")
        self.layout().addWidget(self.checkbox)

    def load(self):
        enabled = self.api.config.setting.get('example_plugin', {}).get('enabled', False)
        self.checkbox.setChecked(enabled)

    def save(self):
        if 'example_plugin' not in self.api.config.setting:
            self.api.config.setting['example_plugin'] = {}
        self.api.config.setting['example_plugin']['enabled'] = self.checkbox.isChecked()

def enable(api: PluginApi):
    """Entry point for the plugin"""
    api.log.info("Example Plugin loaded")

    @api.on_track_metadata_loaded
    def process_track(track, metadata):
        api.log.info(f"Processing track: {track}")
        enabled = api.config.setting.get('example_plugin', {}).get('enabled', False)
        if enabled:
            metadata['example'] = 'processed'

    @api.register_options_page
    def create_options_page(parent):
        return ExampleOptionsPage(api, parent)
```

**locale/en.json:**
```json
{
  "options.enable": "Enable processing",
  "status.processing": "Processing track: {track}"
}
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

A migration tool will be provided to automate common changes:

```bash
# Install migration tool
pip install picard-plugin-migrate

# Migrate plugin
picard-plugin-migrate /path/to/old-plugin /path/to/new-plugin

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
