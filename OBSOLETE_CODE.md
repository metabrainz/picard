# Obsolete and Modified Code for Picard 3.0 Plugin System

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Purpose:** Track code that will be removed or heavily modified for plugin v3

---

## Files to REMOVE Completely

### 1. Legacy Plugin Manager
**File:** `picard/pluginmanager.py` (621 lines)
**Status:** ❌ DELETE
**Reason:** Replaced by `picard/plugin3/manager.py`

**What it does:**
- Loads plugins from ZIP files
- Handles old plugin metadata format (PLUGIN_NAME, PLUGIN_VERSION, etc.)
- Manages plugin installation/updates via old system
- Provides PluginManager class with Qt signals

**Replacement:** `picard/plugin3/manager.py` with git-based installation

---

### 2. Legacy Plugin Wrapper
**File:** `picard/plugin.py` (200+ lines)
**Status:** ❌ DELETE
**Reason:** Replaced by `picard/plugin3/plugin.py`

**What it does:**
- PluginWrapper class for v2 plugins
- PluginData class for metadata
- PluginPriority enum
- Markdown description rendering

**Replacement:**
- `picard/plugin3/plugin.py` - Plugin class
- `picard/plugin3/manifest.py` - PluginManifest class
- Markdown in MANIFEST.toml descriptions

---

### 3. Old Plugin Options UI
**Files:**
- `picard/ui/options/plugins.py` (722 lines) - ❌ ALREADY DELETED
- `picard/ui/forms/ui_options_plugins.py` - ❌ ALREADY DELETED
- `ui/options_plugins.ui` - ❌ ALREADY DELETED

**Status:** ✅ Already removed in current branch
**Reason:** Will be replaced by new plugin management UI in Phase 4

**What it did:**
- List installed plugins
- Enable/disable plugins
- Install plugins from ZIP
- Check for updates
- Show plugin details

**Replacement:** New UI to be designed in Phase 4 (GUI)

---

### 4. Plugin Update Dialog
**File:** `picard/ui/pluginupdatedialog.py`
**Status:** ⚠️ NEEDS REVIEW - May be obsolete
**Reason:** Old update mechanism won't work with git-based plugins

**What it does:**
- Shows available plugin updates
- Downloads and installs updates from old repository

**Replacement:** New update mechanism via git (Phase 1.4)

---

### 5. Old Plugin Tests
**File:** `test/test_ui_options_plugins.py`
**Status:** ❌ ALREADY DELETED
**Reason:** Tests old UI that no longer exists

**Replacement:** `test/test_plugins3.py` (already exists)

---

## Files to MODIFY Heavily

### 1. Tagger Main Class
**File:** `picard/tagger.py`
**Current state:** Initializes both legacy and v3 plugin managers

**Lines to remove:**
```python
from picard.pluginmanager import PluginManager as LegacyPluginManager

def _init_plugins(self):
    # FIXME: Legacy, remove as soon no longer used by other code
    self.pluginmanager = LegacyPluginManager()  # ❌ REMOVE THIS

    self.pluginmanager3 = PluginManager(self)
    if not self._no_plugins:
        self.pluginmanager3.add_directory(plugin_folder(), primary=True)
```

**After cleanup:**
```python
from picard.plugin3.manager import PluginManager

def _init_plugins(self):
    self.pluginmanager = PluginManager(self)  # Rename pluginmanager3 → pluginmanager
    if not self._no_plugins:
        self.pluginmanager.add_directory(plugin_folder(), primary=True)
```

**Impact:** Any code referencing `tagger.pluginmanager` will break

---

### 2. Constants
**File:** `picard/const/__init__.py`
**Current constants to review:**

```python
USER_PLUGIN_DIR  # May need update for plugins3 directory
PLUGINS_API      # Old API versions, update to v3 only
```

**File:** `picard/const/appdirs.py`
**Already modified:** `plugin_folder()` now returns `plugins3` directory

**Check for:**
- Any references to old plugin directory structure
- Old API version constants

---

### 3. Extension Points
**File:** `picard/extension_points/__init__.py`
**Current state:** Defines PLUGIN_MODULE_PREFIX

**May need updates:**
- Module prefix for v3 plugins
- Registration/unregistration logic
- Compatibility with new plugin structure

**Review needed:** Check if extension point system needs changes for v3

---

### 4. Options Dialog
**File:** `picard/ui/options/dialog.py`
**Current state:** References old plugins options page

**Lines to check:**
```python
# May have imports or references to old plugins.py
from picard.ui.options.plugins import PluginsOptionsPage  # ❌ REMOVE
```

**After cleanup:**
- Remove references to old plugin options page
- Add new plugin options page when implemented (Phase 4)

---

### 5. Config Schema
**File:** `picard/const/defaults.py`
**Current state:** May have old plugin settings

**Check for:**
```python
# Old plugin settings
'plugins': {
    'enabled_plugins': [],  # Old format
    # ...
}
```

**Add new settings:**
```python
'plugins3': {
    'enabled_plugins': [],
    'installed_plugins': {},
    'registry_cache': {},
    'last_registry_update': None,
}
```

---

### 6. Config Upgrade
**File:** `picard/config_upgrade.py`
**Needs:** Migration logic from old plugin config to new

**Add upgrade function:**
```python
def upgrade_to_v3_0_0_final_1(config):
    """Migrate plugin settings from v2 to v3"""
    old_plugins = config.setting.get('plugins', {})

    # Warn user about incompatible plugins
    if old_plugins.get('enabled_plugins'):
        log.warning("Picard 3.0 is not compatible with v2 plugins. "
                   "Please reinstall plugins from the plugin registry.")

    # Clear old plugin settings
    config.setting['plugins'] = {}

    # Initialize new plugin settings
    config.setting['plugins3'] = {
        'enabled_plugins': [],
        'installed_plugins': {},
    }
```

---

## Code References to Update

### 1. Plugin Module Prefix
**Current:** `picard.plugins.*`
**New:** `picard.plugins.*` (same, but different loading mechanism)

**Files that import plugins:**
- Check for any code that directly imports plugin modules
- Should use plugin API instead

---

### 2. Plugin Priority
**Current:** Defined in `picard/plugin.py`
**New:** May need to be in `picard/plugin3/` or keep in shared location

**Check:**
```python
from picard.plugin import PluginPriority  # Still valid?
```

---

### 3. Extension Point Registration
**Current:** Global functions in `picard/extension_points/`
**New:** Called via `PluginApi` instance

**Old way (v2):**
```python
from picard.metadata import register_track_metadata_processor
register_track_metadata_processor(my_function)
```

**New way (v3):**
```python
def enable(api: PluginApi):
    api.register_track_metadata_processor(my_function)
```

**Impact:** Extension point modules may need updates to support both during transition

---

## Constants to Remove/Update

### From `picard/const/__init__.py`:

```python
# Old plugin API versions - UPDATE
PLUGINS_API = {
    'versions': ['2.0', '2.1', '2.2'],  # ❌ REMOVE
    'versions': ['3.0'],  # ✅ NEW
}

# Old plugin directory - REVIEW
USER_PLUGIN_DIR = ...  # May reference old location
```

---

## Test Files to Remove

1. ❌ `test/test_ui_options_plugins.py` - Already deleted
2. ⚠️ Any tests that import `picard.pluginmanager`
3. ⚠️ Any tests that import `picard.plugin` (old wrapper)

---

## Documentation to Update

1. **User documentation:**
   - Plugin installation instructions
   - Plugin management guide
   - Migration guide for users

2. **Developer documentation:**
   - Plugin API reference
   - Plugin development guide
   - Migration guide for developers

---

## Cleanup Checklist

### Phase 1: Remove Legacy Code
- [ ] Delete `picard/pluginmanager.py`
- [ ] Delete `picard/plugin.py`
- [ ] Delete `picard/ui/pluginupdatedialog.py` (if obsolete)
- [ ] Remove legacy plugin manager from `picard/tagger.py`
- [ ] Rename `pluginmanager3` → `pluginmanager` in tagger
- [ ] Remove old plugin constants
- [ ] Remove old plugin tests

### Phase 2: Update References
- [ ] Update all imports of `PluginManager`
- [ ] Update all imports of `PluginWrapper`
- [ ] Update extension point registration if needed
- [ ] Update config schema
- [ ] Add config upgrade function
- [ ] Update constants (PLUGINS_API, etc.)

### Phase 3: Update Documentation
- [ ] Update user docs
- [ ] Update developer docs
- [ ] Add migration guides
- [ ] Update README.md

### Phase 4: Testing
- [ ] Verify no imports of deleted modules
- [ ] Test plugin loading
- [ ] Test plugin enable/disable
- [ ] Test config migration
- [ ] Test with real plugins

---

## Estimated Impact

**Lines of code to delete:** ~1,500-2,000 lines
**Lines of code to modify:** ~500-1,000 lines
**Files to delete:** 5-7 files
**Files to modify:** 10-15 files

**Risk level:** Medium-High
- Breaking change for all existing plugins
- Requires careful testing
- Need migration period

---

## Migration Strategy

**Recommended approach:**

1. **Keep legacy code in Picard 2.x branch**
   - Maintain 2.x for 6-12 months
   - Users can stay on 2.x until plugins migrate

2. **Clean break in Picard 3.0**
   - Remove all legacy plugin code
   - Only support plugin API v3
   - Provide migration tools

3. **Parallel releases**
   - Release 2.x and 3.0 simultaneously
   - Clear communication about breaking changes
   - Support both versions during transition

---

## Code Search Commands

To find remaining references to legacy code:

```bash
# Find imports of legacy plugin manager
grep -r "from picard.pluginmanager import" picard/

# Find imports of legacy plugin wrapper
grep -r "from picard.plugin import" picard/

# Find references to old plugin manager
grep -r "\.pluginmanager\." picard/ | grep -v plugin3

# Find old plugin constants
grep -r "USER_PLUGIN_DIR\|PLUGINS_API" picard/

# Find old plugin options
grep -r "PluginsOptionsPage" picard/
```

---

## Notes

- Some code may be shared between v2 and v3 (e.g., PluginPriority)
- Extension points system may need updates but core should remain
- Config system needs migration logic
- UI will be completely new (Phase 4)

**Last updated:** 2025-11-24
**Review before:** Picard 3.0 release
