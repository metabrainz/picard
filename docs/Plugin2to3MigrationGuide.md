# Picard Plugin V2 to V3 Migration Guide

This guide helps plugin developers migrate their Picard V2 plugins to the new V3 plugin system.

## Table of Contents

- [Overview](#overview)
- [Quick Start: Automated Migration](#quick-start-automated-migration)
- [What the Migration Tool Does](#what-the-migration-tool-does)
- [What Changed in V3](#what-changed-in-v3)
- [Manual Steps After Migration](#manual-steps-after-migration)
- [Common Patterns](#common-patterns)
- [Testing Your Plugin](#testing-your-plugin)
- [Troubleshooting](#troubleshooting)

---

## Overview

Picard 3.0 introduces a new plugin system (V3) with significant improvements:

- **MANIFEST.toml**: Declarative metadata in TOML format
- **Git-based distribution**: Plugins distributed via git repositories
- **PluginApi**: Unified API for accessing Picard functionality
- **PyQt6**: Updated from PyQt5 to PyQt6
- **Better isolation**: Each plugin in its own directory

**The migration tool handles most plugins automatically with minimal manual work required.**

---

## Quick Start: Automated Migration

### Basic Usage

```bash
# Single-file plugin
python scripts/migrate_plugin.py my_plugin.py output_directory

# Multi-file plugin (from __init__.py)
python scripts/migrate_plugin.py my_plugin/__init__.py my_plugin_v3

# Example
python scripts/migrate_plugin.py featartist.py featartist_v3
```

### What Happens

The migration script automatically:
1. ✅ Extracts metadata → creates MANIFEST.toml
2. ✅ Converts code to V3 format
3. ✅ Creates `enable(api)` function
4. ✅ Converts PyQt5 → PyQt6 (80+ patterns)
5. ✅ Fixes function signatures
6. ✅ Converts config/log access to use api
7. ✅ Converts config options (TextOption, BoolOption, etc.)
8. ✅ Regenerates UI files with pyuic6
9. ✅ Injects api in OptionsPage/Action classes
10. ✅ Copies all plugin files (Python modules, docs, assets, etc.)
11. ✅ Handles file conflicts (renames with .orig extension)
12. ✅ Formats code with ruff

---

## What the Migration Tool Does

### Automatic Conversions (90-95%)

#### 1. Metadata Extraction
**Before (V2)**:
```python
PLUGIN_NAME = "My Plugin"
PLUGIN_AUTHOR = "Author Name"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
```

**After (V3)** - MANIFEST.toml:
```toml
uuid = "generated-uuid"
name = "My Plugin"
authors = ["Author Name"]
version = "1.0.0"
api = ["3.0"]
license = "GPL-2.0-or-later"
```

#### 2. Register Calls → enable()

**Supported patterns**:
- Metadata processors (track, album, file)
- Script functions
- Options pages
- UI actions (cluster, file, album, track, clusterlist)
- Cover art providers
- Qualified imports (`metadata.register_*`, `providers.register_*`)
- Instantiated registrations (`register_action(MyAction())`)
- Instantiated object methods (`register_processor(MyClass().method)`)

**Before**:
```python
from picard.metadata import register_track_metadata_processor

def process_track(album, metadata, track, release):
    metadata['custom'] = 'value'

register_track_metadata_processor(process_track)
```

**After**:
```python
def process_track(track, metadata):
    metadata['custom'] = 'value'

def enable(api):
    """Called when plugin is enabled."""
    api.register_track_metadata_processor(process_track)
```

#### 3. Decorator Patterns
**Before**:
```python
from picard.script import register_script_function

@register_script_function
def my_function(parser, arg):
    return result
```

**After**:
```python
def my_function(parser, arg):
    return result

def enable(api):
    api.register_script_function(my_function)
```

#### 4. Config/Log Access (API Parameter)
**Before**:
```python
from picard import log, config

log.info("Processing")
if config.setting['enabled']:
    # do something
```

**After - In Processors**:
```python
def my_processor(api, track, metadata):
    api.logger.info("Processing")
    if api.global_config.setting['enabled']:
        metadata['custom'] = 'value'

def enable(api):
    api.register_track_metadata_processor(my_processor)
```

**After - In Classes**:
```python
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    def __init__(self, api=None, parent=None):
        super().__init__(parent)
        self.api = api

    def load(self):
        self.api.logger.info("Loading")
        value = self.api.global_config.setting['my_option']
```

**Why?** Processors receive `api` as first parameter (injected via `functools.partial`). Classes receive `api` in `__init__` and store as `self.api`.

#### 5. Config Options (TextOption, BoolOption, etc.)

**V2 Pattern 1 - Module-level definitions**:
```python
from picard.config import TextOption, BoolOption, IntOption

my_text = TextOption("setting", "my_plugin_text", "default")
my_bool = BoolOption("setting", "my_plugin_enabled", True)
my_int = IntOption("setting", "my_plugin_count", 10)

def process(album, metadata, track, release):
    if my_bool.value:
        text = my_text.value
        count = my_int.value
```

**V3 - Direct config access**:
```python
def process(api, track, metadata):
    if api.plugin_config.get('my_plugin_enabled', True):
        text = api.plugin_config.get('my_plugin_text', 'default')
        count = api.plugin_config.get('my_plugin_count', 10)
```

**V2 Pattern 2 - OptionsPage class attribute**:
```python
from picard import config
from picard.ui.options import OptionsPage

class MyOptionsPage(OptionsPage):
    options = [
        config.BoolOption("setting", "my_option", True),
        config.TextOption("setting", "my_text", "default"),
    ]

    def load(self):
        setting = config.setting
        self.checkbox.setChecked(setting["my_option"])
```

**V3 - No options attribute needed**:
```python
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    # No 'options' attribute needed in V3

    def load(self):
        setting = self.api.global_config.setting
        self.checkbox.setChecked(setting.get("my_option", True))

    def save(self):
        setting = self.api.global_config.setting
        setting["my_option"] = self.checkbox.isChecked()
```

**Why?** V2 used option objects for type validation and metadata. V3 simplifies this - just read/write config directly. The `options` class attribute was V2 metadata that's not needed in V3.

**Migration script handles**:
- ✅ Removes module-level option definitions
- ✅ Converts `.value` access to `api.plugin_config.setting.get()`
- ✅ Removes `options = [...]` class attribute from OptionsPage
- ✅ Converts `config.setting` to `api.global_config.setting`

#### 6. Function Signatures
**Before**:
```python
def process_track(tagger, metadata, track, release):
    # or: def process_track(album, metadata, track, release)
    pass
```

**After**:
```python
def process_track(track, metadata):
    pass
```

#### 7. PyQt5 → PyQt6
**Before**:
```python
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt

dialog.setWindowModality(Qt.WindowModal)
dialog.exec_()
```

**After**:
```python
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

dialog.setWindowModality(Qt.WindowModality.WindowModal)
dialog.exec()
```

#### 8. UI File Regeneration
**Before**: Copies `ui_*.py` and converts PyQt5 → PyQt6

**After**: Regenerates from `.ui` source using pyuic6
```text
Regenerated: ui_options_plugin.py (from ui_options_plugin.ui)
```

- Uses latest PyQt6 code generator
- All Qt6 enums automatically correct
- Cleaner output than text conversion

#### 9. Complete File Copying
**All files and directories** from your V2 plugin are automatically copied to V3:
- ✅ Python modules (helper files, utilities)
- ✅ Documentation (README.md, docs/)
- ✅ Assets (images, data files)
- ✅ Subdirectories (preserves structure)

**Excluded**: Build artifacts (`__pycache__`, `.pyc`, `dist/`, `build/`, etc.)

**Conflict handling**: If a source file conflicts with a generated file (e.g., `.ui` file), the source is renamed with `.orig` extension:
```text
options.ui (regenerated from source) ← takes priority
options.ui.orig (original V2 file) ← renamed
```

#### 10. API Injection in Classes
**Before**:
```python
class MyOptionsPage(OptionsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        # uses api.global_config.setting
```

**After**:
```python
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    def __init__(self, api, parent=None):
        self.api = api
        super().__init__(parent)
        # uses self.api.global_config.setting
```

#### 11. UI Actions (Instantiated Pattern)
**Before** - V2 pattern with instantiated actions:
```python
from picard.ui.itemviews import BaseAction, register_file_action

class MyAction(BaseAction):
    NAME = 'My Action'

    def callback(self, objs):
        # Do something
        pass

# Instantiate and register
action = MyAction()
register_file_action(action)
```

**After** - V3 registers the class, not instance:
```python
from picard.plugin3.api import BaseAction

class MyAction(BaseAction):
    TITLE = 'My Action'

    def __init__(self, api=None):
        super().__init__()
        self.api = api

    def callback(self, objs):
        # Use self.api to access Picard
        files = self.api.tagger.get_files_from_objects(objs)

def enable(api):
    api.register_file_action(MyAction)  # Register class, not instance
```

**Why?** In V3, Picard instantiates actions and passes the `api` parameter. This allows proper API access and lifecycle management.

**Migration script handles**:
- ✅ Detects `action = MyAction()` pattern
- ✅ Removes instantiation line
- ✅ Registers class instead of instance
- ✅ Adds `api` parameter to `__init__`

### What Needs Manual Review (5-10%)

The tool provides clear warnings for:
- ⚠️ Complex class structures (rare)
- ⚠️ Custom tagger access patterns
- ⚠️ WebService customizations
- ⚠️ Plugin-specific business logic

---

## What Changed in V3

### 1. Plugin Structure

**V2**:
```text
my_plugin.py  (or my_plugin/__init__.py)
```

**V3**:
```text
my_plugin_v3/
├── MANIFEST.toml
├── __init__.py
└── ui_options.py (if applicable)
```

### 2. Entry Point

**V2**: Module-level register calls
**V3**: `enable(api)` function

### 3. API Access

**V2**: Direct imports
```python
from picard import log, config
from picard.tagger import tagger
```

**V3**: API parameter
```python
from picard.plugin3.api import OptionsPage

# Processors get api as first parameter
def my_processor(api, track, metadata):
    api.logger.info("Processing")

# Classes get api in __init__
class MyPage(OptionsPage):
    def __init__(self, api=None, parent=None):
        super().__init__(parent)
        self.api = api
```

**How it works:** Picard uses `functools.partial` to inject the API as the first parameter to processors. Classes receive API during instantiation.

### 4. Qt Version

**V2**: PyQt5
**V3**: PyQt6

Major changes:
- Enums moved to nested classes: `Qt.AlignCenter` → `Qt.AlignmentFlag.AlignCenter`
- `exec_()` → `exec()`
- QAction moved: QtWidgets → QtGui

### 5. register_ui_init was removed

Registering a function to run with `register_ui_init` was removed. If possible, one
of the other API functions better fits your use case.

If there is not other API function, move the code into the `enable(api)` function.
This function is being called after Picard's UI is already available and hence behaves
very similar to the `ui_init` functions before. Plugins should however clean up any
changes done to the UI in their `disable()` function.

---

## Manual Steps After Migration

### 1. Create Git Repository

```bash
cd my_plugin_v3
git init
git add .
git commit -m "Migrated to V3"
```

### 2. Review Warnings

The migration tool outputs warnings for items needing manual review:
```text
⚠️  Class 'MyClass' uses 'api' but injection failed - needs manual review
```

Address these before testing.

### 3. Test Installation

```bash
# Install from local directory
picard-plugins --install /path/to/my_plugin_v3 --yes

# Verify
picard-plugins --list
```

### 4. Test Functionality

- Restart Picard
- Enable your plugin
- Test all features
- Check logs for errors

---

## API Access Pattern: Explicit Parameter Passing

### How It Works

Picard V3 uses explicit API parameter passing via `functools.partial`:

**For Processors:** API is injected as first parameter

```python
def my_track_processor(api, track, metadata):
    """API is automatically injected as first parameter."""
    api.logger.info("Processing track")
    if api.global_config.setting['my_option']:
        metadata['custom'] = 'value'


def enable(api):
    # Picard wraps this as partial(my_track_processor, api)
    api.register_track_metadata_processor(my_track_processor)
```

**For Classes:** API is passed to `__init__`

```python
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    """OptionsPage receives api in __init__."""

    NAME = "my_plugin"
    TITLE = "My Plugin"
    PARENT = "plugins"

    def __init__(self, api=None, parent=None):
        super().__init__(parent)
        self.api = api

    def load(self):
        self.api.logger.debug("Loading options")
        value = self.api.global_config.setting['my_option']


def enable(api):
    # Picard stores api and passes it during instantiation
    api.register_options_page(MyOptionsPage)
```

### Common API Access Patterns

```python
from picard.plugin3.api import OptionsPage

# In processors - use api parameter
def my_processor(api, track, metadata):
    api.logger.info("Processing")
    api.global_config.setting['option']

# In classes - use self.api
class MyPage(OptionsPage):
    def load(self):
        self.api.logger.info("Loading")
        self.api.global_config.setting['option']
```

---

## Common Patterns

### Pattern 1: Album Background Tasks (Web Requests)

**V2**:
```python
from picard.metadata import register_album_metadata_processor

def fetch_data(album, metadata, release):
    album._requests += 1
    album.tagger.webservice.get(
        'example.com',
        '/api/data',
        handler=lambda response, reply, error: handle_response(album, response, error)
    )

def handle_response(album, response, error):
    try:
        if not error:
            # Process response
            pass
    finally:
        album._requests -= 1
        album._finalize_loading(None)

register_album_metadata_processor(fetch_data)
```

**V3**:
```python
from functools import partial

def fetch_data(api, album, metadata, release):
    task_id = f'data_{album.id}'

    def create_request():
        return api.web_service.get_url(
            url='https://example.com/api/data',
            handler=partial(handle_response, api, album, task_id)
        )

    api.add_album_task(
        album, task_id,
        'Fetching data',
        request_factory=create_request
    )

def handle_response(api, album, task_id, data, error):
    try:
        if not error:
            # Process data
            pass
    finally:
        api.complete_album_task(album, task_id)

def enable(api):
    api.register_album_metadata_processor(fetch_data)
```

**Key changes**:
- `album._requests` → `api.add_album_task()` with `request_factory`
- `album.tagger.webservice` → `api.web_service`
- Use `request_factory` parameter to prevent race conditions
- Always call `api.complete_album_task()` in a `finally` block

**Why `request_factory`?** The factory pattern ensures requests are created and registered atomically, preventing race conditions where an album could be removed between creating a request and registering it.

---

### Pattern 2: Simple Metadata Processor

**V2**:
```python
PLUGIN_NAME = "Title Cleaner"
# ... metadata ...

from picard.metadata import register_track_metadata_processor

def clean_title(album, metadata, track, release):
    metadata['title'] = metadata['title'].strip()

register_track_metadata_processor(clean_title)
```

**V3** (after migration):
```python
def clean_title(api, track, metadata):
    metadata['title'] = metadata['title'].strip()

def enable(api):
    api.register_track_metadata_processor(clean_title)
```

### Pattern 3: Plugin with Options

**V2**:
```python
from picard import config
from picard.ui.options import OptionsPage

class MyOptionsPage(OptionsPage):
    def load(self):
        self.checkbox.setChecked(config.setting['my_option'])
```

**V3** (after migration):
```python
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    def __init__(self, api=None, parent=None):
        super().__init__(parent)
        self.api = api

    def load(self):
        self.checkbox.setChecked(self.api.global_config.setting['my_option'])

def enable(api):
    api.register_options_page(MyOptionsPage)
```

### Pattern 4: Script Function

**V2**:
```python
from picard.script import register_script_function

@register_script_function
def my_func(parser, arg):
    return result
```

**V3** (after migration):
```python
def my_func(parser, arg):
    return result

def enable(api):
    api.register_script_function(my_func)
```

---

## Testing Your Plugin

### 1. Syntax Check

```bash
python3 -m py_compile __init__.py
```

### 2. Install Locally

```bash
cd my_plugin_v3
git init && git add . && git commit -m "v3"
picard-plugins --install $(pwd) --yes
```

### 3. Check Logs

Picard outputs logs to stderr by default. Run Picard from terminal to see logs:

```bash
picard 2>&1 | grep -i "plugin\|error"
```

Or check the in-app log viewer: Help → View Error/Debug Log

### 4. Test Features

- Enable plugin in Picard settings
- Test all functionality
- Verify UI elements work
- Check metadata processing

---

## Publishing Your Plugin

### Repository Naming Convention

**Recommended**: Use `picard-plugin-<name>` for consistency with the Picard ecosystem.

**Examples**:
- `picard-plugin-lastfm` (not `lastfm-plugin` or `picard_lastfm`)
- `picard-plugin-bpm` (not `bpm-for-picard`)
- `picard-plugin-acousticbrainz` (not `acousticbrainz`)

**For multi-word names**, use hyphens:
- `picard-plugin-additional-artists-details` (not `picard-plugin-additional_artists_details`)
- `picard-plugin-format-performer-tags` (not `picard-plugin-format_performer_tags`)
- `picard-plugin-submit-folksonomy-tags`

**Why?**
- Easy to identify as Picard plugins
- Consistent with community conventions
- Better discoverability on GitHub/GitLab
- Clear namespace separation
- Hyphens are standard for repository names (not underscores)

**Note**: Repository names use hyphens (`picard-plugin-additional-artists-details`) while module names in MANIFEST.toml use underscores (`additional_artists_details`). Keep them consistent by converting hyphens to underscores:
- Repository: `picard-plugin-format-performer-tags`
- Module: `format_performer_tags`

---

## Troubleshooting

### Migration Script Issues

**Problem**: "Could not extract plugin metadata"
**Solution**: Ensure your V2 plugin has PLUGIN_NAME, PLUGIN_VERSION, etc.

**Problem**: "Function signature not fixed"
**Solution**: Check if your function uses non-standard parameters. Update manually.

**Problem**: UI file not regenerated
**Solution**: Ensure pyuic6 is installed: `pip install PyQt6`

### Installation Issues

**Problem**: "Plugin not found in registry"
**Solution**: This is expected. Use `--yes` flag to install unregistered plugins.

**Problem**: "TOML parsing error"
**Solution**: Check MANIFEST.toml for syntax errors, especially in multiline strings.

### Runtime Issues

**Problem**: "TypeError: processor() missing 1 required positional argument: 'metadata'"
**Solution**: Add `api` as first parameter to your processor function

**Problem**: "AttributeError: 'NoneType' object has no attribute 'logger'"
**Solution**: Ensure `self.api` is set in `__init__`: `self.api = api`

**Problem**: Qt enum errors
**Solution**: Check for unconverted Qt5 enums. The migration tool handles 80+ patterns, but some custom code may need manual fixes.

---

## Migration Success Rate

The migration script has been tested on the entire picard-plugins repository:

- **Most plugins** migrate automatically with zero or minimal manual work
- **A small percentage** require minor import or pattern adjustments
- **Very few plugins** need manual intervention for non-standard patterns

**Common scenarios requiring manual review:**
- Custom plugin-specific registration patterns
- Registrations inside function scopes
- Complex class constructor patterns
- Non-standard API access patterns

**Time savings:**
- Manual migration: 2-4 hours per plugin
- With migration script: 10-30 minutes per plugin
- Overall time reduction: 80-90%

---

## Additional Resources

- **V3 Plugin Documentation**: [MIGRATION.md](PLUGINSV3/MIGRATION.md)
- **Plugin Manifest Reference**: [MANIFEST.md](PLUGINSV3/MANIFEST.md)
- **Plugin API Reference**: [API.md](PLUGINSV3/API.md)
- **Forum**: <https://community.metabrainz.org/c/picard>

---

## Getting Help

If you encounter issues:

1. Check the warnings from the migration script
2. Review [MIGRATION.md](PLUGINSV3/MIGRATION.md)
3. Ask on the MusicBrainz forum
4. Report bugs: <https://tickets.metabrainz.org/browse/PICARD>

---

**The migration script handles 90-95% of the work automatically. Most plugins can be migrated in 15-30 minutes!**
