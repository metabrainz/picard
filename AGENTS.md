# AI Assistant Context for MusicBrainz Picard

**Last Updated:** 2026-03-03
**Git Commit:** 2c1780c8abc983ec1b2e4782d267e9c5ed1fbe27

> **Purpose:** Essential patterns, conventions, and gotchas for AI assistants.
> For architecture, dependencies, and component details, explore the codebase
> or read existing docs (`README.md`, `CONTRIBUTING.md`, `INSTALL.md`).

**What is Picard?** Cross-platform audio tagger for MusicBrainz. Tags music files using the MusicBrainz database, supports fingerprinting (AcoustID), and has a powerful plugin system.

---

## Quick Facts

- **Language:** Python 3.8+, PyQt6, Mutagen
- **Size:** ~174k LOC, event-driven MVC with plugin system
- **Entry Point:** `picard/tagger.py:main()` → `Tagger` singleton
- **Tests:** `test/` directory (pytest)
- **Docs:** <https://picard-docs.musicbrainz.org/>
- **Tickets:** <https://tickets.metabrainz.org/projects/PICARD>
- **Chat:** [Matrix #musicbrainz-picard-dev](https://matrix.to/#/#musicbrainz-picard-dev:chatbrainz.org)

---

## Critical Patterns & Gotchas

### Threading Rules
```python
# ❌ NEVER access UI from background threads
def background_task():
    self.label.setText("Done")  # CRASH!

# ✅ Use signals or run_task callback
from picard.util.thread import run_task

def callback(result):
    self.label.setText(result)  # Safe - runs in main thread

run_task(heavy_operation, callback=callback)
```

### Metadata Changes
```python
# ❌ Silent changes won't update UI
metadata['artist'] = 'New Artist'

# ✅ Always emit signals
metadata['artist'] = 'New Artist'
file.metadata_updated.emit()
```

### Configuration Access
```python
# ✅ Always use config.setting
from picard import config
value = config.setting['option_name']

# ❌ Don't access internal structures directly
```

### Async Operations
```python
# ✅ Use thread pool for I/O
from picard.util.thread import run_task

run_task(process_file, file, callback)

# ❌ Don't block the main thread
result = slow_network_call()  # UI freezes!
```

---

## Plugin System (v3)

### Structure
```text
my_plugin/
├── __init__.py       # Plugin code
├── MANIFEST.toml     # Metadata (UPPERCASE!)
└── ui_options.py     # Optional settings
```

### MANIFEST.toml
```toml
uuid = "unique-uuid"
name = "Plugin Name"
authors = ["Your Name"]
description = "Description"
api = ["3.0"]
categories = ["metadata"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
```

### Plugin Code
```python
from picard.plugin3.api import PluginApi

def enable(api: PluginApi):
    """Called when plugin is enabled."""
    api.plugin_config.register_option("my_option", "default")
    api.register_track_metadata_processor(process_metadata)

def process_metadata(api, album, metadata, track, release):
    metadata['custom'] = api.plugin_config['my_option']
```

### Plugin Management CLI
```bash
# List installed plugins
picard-plugins list

# Install plugin from registry
picard-plugins install plugin-name

# Install from URL or local path
picard-plugins install https://github.com/user/plugin.git
picard-plugins install /path/to/plugin

# Update plugins
picard-plugins update plugin-name

# Remove plugin
picard-plugins remove plugin-name

# Search registry
picard-plugins search keyword
```

**Key Files:**
- API: `picard/plugin3/api_impl.py`
- Manager: `picard/plugin3/manager/__init__.py`
- CLI: `picard/plugin3/cli.py`
- Example: <https://github.com/rdswift/picard-plugin-format-performer-tags>

**Documentation:**
- Plugin v3 docs: `docs/PLUGINSV3/` (API, CLI, manifest, translations, etc.)
- Migration guide: `docs/Plugin2to3MigrationGuide.md`
- Plugin registry: <https://github.com/metabrainz/picard-plugins-registry>

---

## Development Workflow

### Setup
```bash
git clone https://github.com/metabrainz/picard.git
cd picard

# Preferred
uv sync

# Alternative
pip install -r requirements.txt

python setup.py build_ui  # Compile Qt forms
python tagger.py          # Run from source
```

### Before Committing
```bash
# 1. Format code
ruff format picard/

# 2. Check for issues
ruff check picard/

# 3. Run tests
pytest test/

# Or specific tests
pytest test/test_metadata.py
```

### Contributing
1. **Create ticket first:** <https://tickets.metabrainz.org/projects/PICARD>
2. Create feature branch
3. Make changes
4. Run pre-commit checks (above)
5. **PR title must start with:** `PICARD-XXXX:` (ticket number)
6. **Don't auto-create tickets/PRs** - let humans handle this

---

## Code Style

### Conventions
- **Standard:** PEP 8, 120 char lines (flexible)
- **Linter:** Ruff
- **Type hints:** Recommended for new code (existing code has limited coverage)
- **Naming:** `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE` constants

### Internationalization (i18n)
```python
# Import translation functions
from picard.i18n import gettext as _
from picard.i18n import N_

# Translatable strings (runtime)
message = _("Save file")
error = _("Failed to load: %s") % filename

# Mark for extraction only (constants, class attributes)
TITLE = N_("Options")  # Translated at usage: _(TITLE)

# Plugin translations (Plugin v3)
from picard.plugin3.api import t_

class ManifestTranslations:
    NAME = t_("manifest.name", "My Plugin")
    DESC = t_("manifest.description", "Plugin description")
```

**Translation workflow:**
- Strings marked with `_()` or `N_()` are extracted to `po/picard.pot`
- Regenerate: `python setup.py regen_pot_file`
- Translations managed via [Weblate](https://translations.metabrainz.org/projects/picard/)
- See `po/README.md` for details

### Qt UI Files
```bash
# ❌ Don't edit picard/ui/ui_*.py directly (auto-generated)

# ✅ Edit .ui files with Qt Designer
qtdesigner ui/options_metadata.ui

# ✅ Regenerate Python files
python setup.py build_ui
```

### Qt Signals
```python
from PyQt6.QtCore import pyqtSignal

class MyWidget(QWidget):
    # Define signals
    value_changed = pyqtSignal(str)
    item_selected = pyqtSignal(object)

    def some_action(self):
        # Emit signals
        self.value_changed.emit("new value")
```

### Readability
- Use descriptive names
- Comment complex logic
- Break long functions
- Follow existing style in the file

---

## Key Locations

### Core Components
- **Main app:** `picard/tagger.py` (1,851 LOC)
- **File handling:** `picard/file.py` (1,175 LOC)
- **Album/Track:** `picard/album.py`, `picard/track.py`
- **Metadata:** `picard/metadata.py`

### Format Handlers
- **Registry:** `picard/formats/registry.py`
- **ID3 (MP3):** `picard/formats/id3.py` (1,144 LOC)
- **Vorbis (FLAC/Ogg):** `picard/formats/vorbis.py`
- **MP4:** `picard/formats/mp4.py`

### Plugin System
- **API:** `picard/plugin3/api_impl.py` (862 LOC)
- **Manager:** `picard/plugin3/manager/__init__.py` (1,092 LOC)
- **Registry:** `picard/plugin3/registry.py`

### UI
- **Main window:** `picard/ui/mainwindow/` (2,233 LOC)
- **Options:** `picard/ui/options/` (20+ pages)
- **Metadata box:** `picard/ui/metadatabox/` (906 LOC)
- **Script editor:** `picard/ui/scripteditor/` (1,106 LOC)

### Scripting
- **Parser:** `picard/script/parser.py` (420 LOC)
- **Functions:** `picard/script/functions.py` (1,595 LOC, 80+ functions)

### Web Services
- **HTTP client:** `picard/webservice/__init__.py` (748 LOC)
- **APIs:** `picard/webservice/api_helpers.py` (352 LOC)

---

## Common Tasks

### Add Audio Format
1. Create handler in `picard/formats/`
2. Inherit from `File`
3. Implement `_load()` and `_save()`
4. Define `EXTENSIONS` and `NAME`
5. Call `register_format(MyFormat)`

### Add Script Function
```python
from picard.script import script_function

@script_function
def func_myfunction(parser, arg1, arg2='default'):
    """%myfunction(arg1,arg2)% - Description"""
    return result
```

### Add Option
1. Define in `picard/options.py`
2. Create UI page in `picard/ui/options/`
3. Implement `load()` and `save()` methods
4. Register with `register_options_page()`

### Add Metadata Processor
```python
from picard.plugin3.api import register_track_metadata_processor

def my_processor(album, metadata, track, release):
    metadata['custom'] = 'value'

register_track_metadata_processor(my_processor)
```

---

## Testing

```bash
# All tests
pytest test/

# Specific file
pytest test/test_metadata.py

# With coverage
pytest --cov=picard test/
```

### Test Structure
```python
from test.picardtestcase import PicardTestCase

class TestMyFeature(PicardTestCase):
    def setUp(self):
        super().setUp()

    def test_something(self):
        self.assertEqual(expected, actual)
```

---

## Debugging

```bash
# Enable debug logging
picard --debug

# Enable specific debug options (comma-separated)
picard --debug-opts=option1,option2
```

```python
# In code
from picard import log
log.debug('Debug: %s', value)
log.error('Error', exc_info=True)
```

---

## Resources

- **User Docs:** <https://picard-docs.musicbrainz.org/>
- **Website:** <https://picard.musicbrainz.org/>
- **GitHub:** <https://github.com/metabrainz/picard>
- **Forum:** <https://community.metabrainz.org/c/picard>
- **Contributing:** See `CONTRIBUTING.md`
- **Installation:** See `INSTALL.md`

---

**Note:** This file contains only essential patterns. For architecture, dependencies, and component details, explore the codebase directly or read existing documentation (`README.md`, `CONTRIBUTING.md`, `INSTALL.md`, user docs).
