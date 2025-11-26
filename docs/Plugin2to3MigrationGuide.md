# Picard Plugin V2 to V3 Migration Guide

This guide helps plugin developers migrate their Picard V2 plugins to the new V3 plugin system.

## Table of Contents

- [Overview](#overview)
- [Quick Start: Automated Migration](#quick-start-automated-migration)
- [What Changed in V3](#what-changed-in-v3)
- [Manual Migration Steps](#manual-migration-steps)
- [Common Patterns](#common-patterns)
- [Testing Your Plugin](#testing-your-plugin)
- [Troubleshooting](#troubleshooting)

---

## Overview

Picard 3.0 introduces a new plugin system (V3) with significant improvements:

- **MANIFEST.toml**: Declarative metadata in TOML format
- **Isolated plugins**: Each plugin in its own directory
- **PluginApi**: Unified API for registering functionality
- **Qt6**: Updated from PyQt5 to PyQt6
- **Better validation**: Automatic validation of plugin metadata

**Migration tool success rate**: 97% of existing plugins (71/73) can be migrated automatically!

---

## Quick Start: Automated Migration

### For Single-File Plugins (Most Common)

```bash
# Migrate your plugin
python scripts/migrate_plugin.py my_plugin.py output_directory

# Example:
python scripts/migrate_plugin.py featartist.py featartist_v3
```

### For Multi-File Plugins

```bash
# Migrate from __init__.py (UI files will be auto-detected and copied)
python scripts/migrate_plugin.py my_plugin/__init__.py my_plugin_v3
```

### What the Tool Does

✅ Extracts V2 metadata (PLUGIN_NAME, PLUGIN_AUTHOR, etc.)
✅ Generates MANIFEST.toml
✅ Converts register calls to enable(api) function
✅ Replaces PLUGIN_NAME references with actual name
✅ Copies and converts UI files (PyQt5 → PyQt6)
✅ Fixes imports (picard.plugins.* → relative imports)
✅ Validates the generated MANIFEST.toml

### After Migration

1. **Review** the generated code in `__init__.py`
2. **Test** with: `picard plugins --validate <path>`
3. **Install** with: `picard plugins --install <path>`

---

## What Changed in V3

### 1. Metadata: Python → TOML

**V2 (Python):**
```python
PLUGIN_NAME = "My Plugin"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_DESCRIPTION = "Does something cool"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
```

**V3 (TOML):**
```toml
uuid = "550e8400-e29b-41d4-a716-446655440000"  # NEW: Required unique identifier
name = "My Plugin"
authors = ["Your Name"]
version = "1.0.0"
description = "Does something cool"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
```

**Key differences:**
- **NEW:** `uuid` field is required (generate with `uuidgen` or `python -c "import uuid; print(uuid.uuid4())"`)
- `author` → `authors` (now an array)
- `description` max 200 characters (use `long_description` for more)
- `api` instead of `PLUGIN_API_VERSIONS`

### 2. Registration: Module-level → enable() Function

**V2:**
```python
from picard.metadata import register_track_metadata_processor

def process_metadata(album, metadata, track, release):
    metadata['custom_tag'] = 'value'

register_track_metadata_processor(process_metadata)
```

**V3:**
```python
def process_metadata(album, metadata, track, release):
    metadata['custom_tag'] = 'value'

def enable(api):
    """Called when plugin is enabled."""
    api.register_track_metadata_processor(process_metadata)
```

**All register functions now use the `api` object:**
- `api.register_track_metadata_processor()`
- `api.register_album_metadata_processor()`
- `api.register_file_action()`
- `api.register_cluster_action()`
- `api.register_options_page()`
- `api.register_script_function()`
- `api.register_cover_art_provider()`
- And more...

### 3. Plugin Structure

**V2 (single file):**
```
my_plugin.py
```

**V3 (directory):**
```
my_plugin/
├── MANIFEST.toml
├── __init__.py
└── ui_options.py (if needed)
```

### 4. Qt5 → Qt6

**V2:**
```python
from PyQt5 import QtCore, QtWidgets
```

**V3:**
```python
from PyQt6 import QtCore, QtWidgets
```

**Common enum changes:**
```python
# V2
QHeaderView.Stretch
QSizePolicy.Expanding

# V3
QHeaderView.ResizeMode.Stretch
QSizePolicy.Policy.Expanding
```

The migration tool handles most of these automatically, but complex UI code may need manual review.

### 5. Imports

**V2:**
```python
from picard.plugins.my_plugin.ui_options import Ui_Options
```

**V3:**
```python
from .ui_options import Ui_Options
```

Use relative imports for files within your plugin.

---

## Manual Migration Steps

For plugins that can't be fully automated (complex multi-file plugins):

### Step 1: Create MANIFEST.toml

You can get a template with:
```bash
picard plugins --manifest
```

Or create it manually:

```toml
uuid = "550e8400-e29b-41d4-a716-446655440000"  # Generate with: uuidgen
name = "Your Plugin Name"
authors = ["Your Name <email@example.com>"]
version = "1.0.0"
description = "Short description (max 200 chars)"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"

# Optional fields
long_description = "Longer description with more details..."
homepage = "https://github.com/yourname/plugin"

# Translations (optional)
[name_i18n]
fr = "Nom du Plugin"
de = "Plugin-Name"

[description_i18n]
fr = "Description courte"
de = "Kurze Beschreibung"
```

### Step 2: Create Plugin Directory

```bash
mkdir my_plugin_v3
cd my_plugin_v3
```

### Step 3: Convert Code

1. **Remove metadata** from Python code (now in MANIFEST.toml)
2. **Create enable() function** and move all register calls into it
3. **Update imports**:
   - Remove register function imports
   - Change `picard.plugins.*` to relative imports
   - Change `PyQt5` to `PyQt6`
4. **Replace PLUGIN_NAME** references with the actual string

### Step 4: Update UI Files

If you have UI files:
1. Change `PyQt5` → `PyQt6`
2. Update enum patterns (see Qt6 section above)
3. Test thoroughly

---

## Common Patterns

### Script Functions

**V2:**
```python
from picard.script import register_script_function

def func_decade(parser, value):
    return value[:3] + "0s"

register_script_function(func_decade, name="decade")
```

**V3:**
```python
def func_decade(parser, value):
    return value[:3] + "0s"

def enable(api):
    api.register_script_function(func_decade, name="decade")
```

### UI Actions

**V2:**
```python
from picard.ui.itemviews import BaseAction, register_file_action

class MyAction(BaseAction):
    NAME = "My Action"

    def callback(self, objs):
        # Do something
        pass

register_file_action(MyAction())
```

**V3:**
```python
from picard.ui.itemviews import BaseAction

class MyAction(BaseAction):
    NAME = "My Action"

    def callback(self, objs):
        # Do something
        pass

def enable(api):
    api.register_file_action(MyAction())
```

### Options Pages

**V2:**
```python
from picard.ui.options import OptionsPage, register_options_page
from picard.plugins.my_plugin.ui_options import Ui_Options

class MyOptionsPage(OptionsPage):
    NAME = "my_plugin"
    TITLE = "My Plugin"
    PARENT = "plugins"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Options()
        self.ui.setupUi(self)

register_options_page(MyOptionsPage)
```

**V3:**
```python
from picard.ui.options import OptionsPage
from .ui_options import Ui_Options

class MyOptionsPage(OptionsPage):
    NAME = "my_plugin"
    TITLE = "My Plugin"
    PARENT = "plugins"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Options()
        self.ui.setupUi(self)

def enable(api):
    api.register_options_page(MyOptionsPage)
```

### Cover Art Providers

**V2:**
```python
from picard.coverart.providers import register_cover_art_provider, CoverArtProvider

class MyCoverArtProvider(CoverArtProvider):
    NAME = "My Provider"
    # ...

register_cover_art_provider(MyCoverArtProvider)
```

**V3:**
```python
from picard.coverart.providers import CoverArtProvider

class MyCoverArtProvider(CoverArtProvider):
    NAME = "My Provider"
    # ...

def enable(api):
    api.register_cover_art_provider(MyCoverArtProvider)
```

---

## Testing Your Plugin

### 1. Validate MANIFEST.toml

```bash
picard plugins --validate /path/to/your/plugin
```

This checks:
- Required fields are present
- Field types are correct
- String lengths are within limits
- No empty translation sections

### 2. Initialize Git Repository

**Important:** Your plugin directory must be a git repository for installation to work.

```bash
cd /path/to/your/plugin
git init
git add .
git commit -m "Initial commit"
```

### 3. Install and Test

```bash
# Install from local directory (must be a git repository)
picard plugins --install /path/to/your/plugin

# Or install from git URL
picard plugins --install https://github.com/yourname/plugin.git
```

### 4. Check Logs

Enable debug logging by using the `--debug` command line option:
```bash
picard --debug
```

See the [documentation](https://picard-docs.musicbrainz.org/en/troubleshooting/troubleshooting.html#getting-a-debug-log) for more details.

### 5. Test All Features

- Test all register functions work
- Test UI components (if any)
- Test with different file types
- Test error handling

---

## Troubleshooting

### "Missing required field: description"

Your description is missing or empty. Add it to MANIFEST.toml:
```toml
description = "Your plugin description here"
```

### "Field 'description' must be 1-200 characters"

Description is too long. Use `long_description` for the full text:
```toml
description = "Short description"
long_description = "Much longer description with all the details..."
```

### "Invalid TOML syntax"

Check for:
- Unescaped quotes in strings: `"Use \"quotes\" like this"`
- Missing closing quotes
- Invalid array syntax: `authors = ["Name"]` not `authors = "Name"`

### Qt6 Import Errors

If you get `ModuleNotFoundError: No module named 'PyQt5'`:
- Change all `PyQt5` imports to `PyQt6`
- Update enum patterns (see Qt6 section)
- The migration tool does this automatically

### Plugin Not Loading

Check:
1. MANIFEST.toml is valid (use `--validate`)
2. `enable(api)` function exists
3. No syntax errors in Python code
4. All imports are correct
5. Check Picard logs for error messages

### "Module has no attribute 'enable'"

You forgot to add the `enable(api)` function. Add it:
```python
def enable(api):
    """Called when plugin is enabled."""
    # Your register calls here
    api.register_track_metadata_processor(my_function)
```

---

## Migration Tool Limitations

The automated migration tool handles **97% of plugins** but has limitations:

### Not Supported (Manual Migration Required)

1. **Very complex multi-file plugins** (7+ files with custom patterns)
2. **Custom registration wrappers** (functions that wrap register calls)
3. **Plugins with separate manifest files** (can extract metadata but needs manual code merge)

### Partially Supported (Review Required)

1. **Complex Qt6 changes** - Basic patterns converted, complex UI may need manual fixes
2. **Multi-line string concatenation** - Handled but verify output
3. **Escaped characters** - Should work but verify special cases

### Always Review

Even for automatically migrated plugins:
- Check Qt6 UI code works correctly
- Verify all imports are correct
- Test all functionality
- Review generated enable() function

---

## Getting Help

- **Documentation**: See `docs/PLUGINSV3/` directory
- **Examples**: Check migrated plugins in the repository
- **Issues**: Report problems on GitHub
- **Community**: Ask on MusicBrainz forums

---

## Checklist

Before releasing your V3 plugin:

- [ ] MANIFEST.toml validates successfully
- [ ] All metadata fields are correct
- [ ] enable(api) function exists and works
- [ ] All imports updated (no PyQt5, no picard.plugins.*)
- [ ] UI files converted to Qt6 (if applicable)
- [ ] Plugin installs without errors
- [ ] All features tested and working
- [ ] Version number updated
- [ ] README updated (if applicable)
- [ ] License information correct

---

## Example: Complete Migration

### Before (V2)

**featartist.py:**
```python
PLUGIN_NAME = "Feat. Artists Removed"
PLUGIN_AUTHOR = "Lukas Lalinsky"
PLUGIN_DESCRIPTION = "Removes feat. artists from track titles"
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.metadata import register_track_metadata_processor
import re

def remove_featartists(album, metadata, track, release):
    if 'title' in metadata:
        metadata['title'] = re.sub(r'\s+feat\..*$', '', metadata['title'])

register_track_metadata_processor(remove_featartists)
```

### After (V3)

**featartist/MANIFEST.toml:**
```toml
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Feat. Artists Removed"
authors = ["Lukas Lalinsky"]
version = "0.2"
description = "Removes feat. artists from track titles"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
```

**featartist/__init__.py:**
```python
import re

def remove_featartists(album, metadata, track, release):
    if 'title' in metadata:
        metadata['title'] = re.sub(r'\s+feat\..*$', '', metadata['title'])

def enable(api):
    """Called when plugin is enabled."""
    api.register_track_metadata_processor(remove_featartists)
```

---

## Additional Resources

- **V3 Plugin Specification**: `docs/PLUGINSV3/MANIFEST.md`
- **API Reference**: `docs/PLUGINSV3/API.md`
- **Roadmap**: `docs/PLUGINSV3/ROADMAP.md`
- **Qt6 Porting Guide**: https://doc.qt.io/qt-6/portingguide.html

---

**Happy migrating! 🎵**
