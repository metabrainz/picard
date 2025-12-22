# Plugin API Reference

This document provides a complete reference for the `PluginApi` class, which is the main interface for plugins to interact with Picard.

---

## Overview

The `PluginApi` object is passed to your plugin's `enable()` function and provides access to all Picard functionality:

```python
def enable(api):
    """Entry point for the plugin (required)."""
    api.logger.info("Plugin loaded")
    api.register_track_metadata_processor(my_processor)

def disable():
    """Optional cleanup when plugin is disabled."""
    # Custom cleanup code here
    pass
```

**Required**: `enable(api)` - Called when plugin is enabled
**Optional**: `disable()` - Called when plugin is disabled (before automatic cleanup)

**Note**: All registrations (`api.register_*`) are automatically removed when the plugin is disabled. The `disable()` function is only needed for custom cleanup (closing connections, stopping threads, etc.).

---

## Getting API Instance

### `PluginApi.get_api()` (class method)

Get the `PluginApi` instance from anywhere in your plugin code without explicitly passing it around.

```python
from picard.plugin3.api import PluginApi

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Get API instance without passing it through constructors
        api = PluginApi.get_api()
        api.logger.info("Widget initialized")

        # Use API methods
        self.plugin_config = api.plugin_config
        self.logger = api.logger
```

**Returns**: `PluginApi` - The API instance for the calling plugin module

**Raises**: `RuntimeError` - If called from outside a plugin context

**How it works**:
- Inspects the call stack to determine which plugin module is calling
- Returns the cached API instance for that module
- Works from main plugin module and any submodules
- First call per module does stack inspection, subsequent calls use cache

**Use cases**:
- Classes that don't receive `api` parameter (widgets, dialogs, utility classes)
- Avoiding passing `api` through multiple constructor levels
- Accessing API from helper modules

**Note**: This is a convenience method. For the main `enable()` function and classes that naturally receive the API (like `BaseAction`), use the passed `api` parameter directly.

---

## Class References

The following classes are available through the `api` module:

- `Album` - Album object
- `Track` - Track object
- `File` - File base class (for custom formats)
- `Cluster` - Cluster object
- `Metadata` - Metadata container for tags
- `BaseAction` - Base class for UI actions
- `OptionsPage` - Base class for options pages
- `CoverArtImage` - Cover art image object
- `CoverArtProvider` - Base class for cover art providers
- `ProviderOptions` - Base class for cover art provider option pages
- `ScriptParser` - A parser for parsing tagger scripts

**Example**:
```python
from picard.plugin3.api import BaseAction, OptionsPage, File, CoverArtProvider, Metadata

class MyProvider(CoverArtProvider):
    NAME = "My Provider"

class MyFormat(File):
    NAME = "Custom Format"
    EXTENSIONS = [".custom"]

    def _load(self, filename):
        metadata = Metadata()
        # Load tags into metadata
        return metadata
```

**Note**: Classes that are considered part of the API like `Metadata`, `Track`, `Album`,
etc. should be imported directly from `picard.plugin3.api` instead from elsewhere
in Picard.

---

## Properties

### `tagger`

Access to the main Tagger instance.

```python
def enable(api):
    # Get files from objects
    files = api.tagger.get_files_from_objects(objs)

    # Access window
    window = api.tagger.window
```

**Common uses**:
- `api.tagger.get_files_from_objects(objs)` - Convert UI objects to files
- `api.tagger.window` - Access main window for dialogs

---

### `plugin_id: str`

Plugin identifier (module name).

```python
def enable(api):
    api.logger.info(f"Plugin {api.plugin_id} loaded")
```

**Value**: The plugin's module name (e.g., `'listenbrainz'`, `'my-plugin'`)

---

### `logger: Logger`

Plugin-specific logger instance.

```python
def enable(api):
    api.logger.debug("Debug message")
    api.logger.info("Info message")
    api.logger.warning("Warning message")
    api.logger.error("Error message")
```

**Namespace**: Logs are prefixed with `plugin.{module_name}`

---

### `global_config: Config`

Access to Picard's global configuration.

```python
def my_processor(api, album, metadata, release):
    # Read settings
    enabled = api.global_config.setting.get('my_plugin_enabled', False)

    # Write settings
    api.global_config.setting['my_plugin_enabled'] = True
```

**Common settings**:
- `api.global_config.setting['server_host']` - MusicBrainz server
- `api.global_config.setting['server_port']` - Server port
- `api.global_config.setting['username']` - MusicBrainz username

---

### `plugin_config: ConfigSection`

Plugin-private configuration section.

```python
def enable(api):
    # Register options with default value
    api.plugin_config.register_option('text_option', 'value')
    api.plugin_config.register_option('bool_option', True)
    api.plugin_config.register_option('int_option', 42)
    api.plugin_config.register_option('list_option', ['a', 'b', 'c'])

    # Write values (any JSON-serializable type)
    api.plugin_config['text_option'] = 'value'
    api.plugin_config['bool_option'] = True
    api.plugin_config['int_option'] = 42
    api.plugin_config['list_option'] = ['a', 'b', 'c']

    # Read values, will return the registered default if not set
    text = api.plugin_config['text_option']
    enabled = api.plugin_config['bool_option']
    count = api.plugin_config['int_option']
    items = api.plugin_config['list_option']

    # Read with explicit defaults
    text = api.plugin_config.get('text_option', 'default')
    enabled = api.plugin_config.get('bool_option', False)
    count = api.plugin_config.get('int_option', 0)
    items = api.plugin_config.get('list_option', [])

    # Check if key exists
    if 'my_option' in api.plugin_config:
        value = api.plugin_config['my_option']

    # Remove a key
    api.plugin_config.remove('old_option')
```

**In OptionsPage:**
```python
from picard.plugin3.api import PluginApi, OptionsPage

class MyOptionsPage(OptionsPage):
    def __init__(self):
        super().__init__()
        # Initialize the UI here

    def load(self):
        # Load from plugin config
        enabled = self.api.plugin_config.get('enabled', True)
        self.checkbox.setChecked(enabled)

    def save(self):
        # Save to plugin config
        self.api.plugin_config['enabled'] = self.checkbox.isChecked()
```

**Benefits**:
- Isolated from other plugins
- Automatically namespaced under `plugin.{module_name}`
- Persisted in Picard config
- Supports any JSON-serializable type

**Note**: Values are stored in Qt settings format. Complex types (lists, dicts) are automatically serialized.

---

### `plugin_dir: Path`

Path to the plugin directory (read-only).

```python
from pathlib import Path
import json

def enable(api):
    # Access plugin directory
    plugin_dir = api.plugin_dir

    # Load data files
    data_file = plugin_dir / 'data' / 'config.json'
    with open(data_file) as f:
        config = json.load(f)

    # Load text files
    readme = plugin_dir / 'README.md'
    if readme.exists():
        with open(readme) as f:
            content = f.read()

    # List files in directory
    for file in (plugin_dir / 'templates').glob('*.txt'):
        api.logger.info(f"Found template: {file.name}")
```

**Use cases**:
- Load configuration files
- Read data files (JSON, CSV, etc.)
- Access templates or resources
- Load UI files (.ui)

**Returns**: `Path` object or `None` if plugin directory is not available

**Important**: This is for **reading** files only. Do not write to the plugin directory:
- Use `api.plugin_config` for storing plugin settings
- Use standard user directories for cache/data files

---

### `web_service: WebService`

Access to Picard's web service for HTTP requests.

```python
def my_processor(api, album, metadata, release):
    def response_handler(response, reply, error):
        if error:
            api.logger.error(f"Request failed: {error}")
        else:
            data = response.json()
            # Process data

    api.web_service.get(
        'example.com',
        '/api/endpoint',
        response_handler,
        priority=True,
        important=False
    )
```

---

### `mb_api: MBAPIHelper`

Helper for MusicBrainz API requests.

```python
def my_processor(api, album, metadata, release):
    # Simplified MusicBrainz API access
    api.mb_api.get_release_by_id(
        release_id,
        handler,
        inc=['artists', 'recordings']
    )
```

---

## Translation Methods

### `get_locale() -> str`

Get the current locale used by Picard.

```python
def enable(api):
    locale = api.get_locale()  # e.g., 'en_US', 'de_DE', 'pt_BR'
    api.logger.info(f"Current locale: {locale}")
```

---

### `tr(key, text=None, **kwargs) -> str`

Translate a string for the plugin.

```python
def enable(api):
    # With fallback text
    greeting = api.tr('greeting', 'Hello')

    # With placeholders
    message = api.tr('welcome', 'Welcome {name}', name='User')

    # Key only (returns key if no translation)
    label = api.tr('submit_button')
```

**See**: [TRANSLATIONS.md](TRANSLATIONS.md) for complete translation system documentation.

---

### `get_plugin_version() -> str`

Get the plugin's own version as displayed in CLI and GUI.

```python
def enable(api):
    version = api.get_plugin_version()
    api.logger.info(f"Running version: {version}")

    # Examples of returned formats:
    # "v1.2.3 @abc1234" - version tag with commit
    # "@abc1234" - commit only (no version tag)
    # "1.0.0" - manifest version (no git metadata)
    # "Unknown" - no version information available
```

**Returns**: Version string in format "ref @commit", "@commit", manifest version, or "Unknown"

**Use cases**:
- Logging current plugin version
- Version-specific behavior
- Debugging and support

---

### `trn(key, singular=None, plural=None, n=0, **kwargs) -> str`

Translate a string with plural forms.

```python
def enable(api):
    # Plural translation
    count_msg = api.trn('files', '{n} file', '{n} files', n=5)
    # Result: "5 files" (English) or "5 Dateien" (German)
```

**Parameters:**
- `n`: Required parameter to determine the correct plural form
- Use `{n}` in format strings (automatically available for substitution)

**See**: [TRANSLATIONS.md](TRANSLATIONS.md) for plural forms and CLDR rules.

---

### `t_(key, text=None, plural=None)` (module-level function)

Mark a string for translation extraction without translating it immediately.

This is a marker function that allows you to define translatable strings at module level or in data structures before the API is available. At runtime, it simply returns the key (or tuple for plurals) unchanged.

```python
from picard.plugin3.api import PluginApi, BaseAction, t_

# Define translatable strings at module level
ERROR_MESSAGES = {
    404: t_('error.not_found', 'Not found'),
    500: t_('error.server', 'Server error'),
}

# Define plural forms
FILE_COUNT = t_('files.count', '{n} file', '{n} files')

# Use in class definitions
class MyAction(BaseAction):
    TITLE = "My Custom Action"

    def __init__(self):
        super().__init__()
        self.setText(self.api.tr("action.name", "My Custom Action"))

def enable(api):
    # Translate at runtime
    error_msg = api.tr(ERROR_MESSAGES[404], 'Not found')

    # Use plural forms (unpacks to key, singular, plural)
    count_msg = api.trn(*FILE_COUNT, n=5)
```

**Parameters:**
- `key`: Translation key
- `text`: Default text (singular form) - used by extraction tool
- `plural`: Plural form (optional) - used by extraction tool

**Returns:**
- If no plural: returns `key`
- If plural: returns `(key, text, plural)` tuple

**Benefits:**
- Define translations once, use multiple times
- No repetition of translation strings
- Works at module/class level before `enable()` is called
- Zero runtime overhead (just returns key/tuple)
- Extractor finds and extracts all marked strings

**See**: [TRANSLATIONS.md](TRANSLATIONS.md) for complete translation system documentation.

---

## Registration Methods

### Metadata Processors

#### `register_track_metadata_processor(function, priority=0)`

Register a function to process track metadata.

**Signature**: `function(api, track, metadata, track_node, release_node=None)`

```python
def process_track(api, track, metadata, track_node, release_node=None):
    """Process track metadata."""
    api.logger.info(f"Processing: {metadata['title']}")
    metadata['custom_tag'] = 'value'

def enable(api):
    api.register_track_metadata_processor(process_track)
    # With priority
    api.register_track_metadata_processor(process_track, priority=100)
```

**Parameters**:
- `function`: Processor function (receives `api`, `track`, `metadata`, `track_node`, `release_node`)
- `priority`: Execution priority (higher = earlier, default: 0)

---

#### `register_album_metadata_processor(function, priority=0)`

Register a function to process album metadata.

**Signature**: `function(api, album, metadata, release_node)`

```python
def process_album(api, album, metadata, release_node):
    """Process album metadata."""
    metadata['custom_album_tag'] = 'value'

def enable(api):
    api.register_album_metadata_processor(process_album)
```

---

### Event Hooks

#### `register_file_post_load_processor(function, priority=0)`

Called after a file is loaded.

**Signature**: `function(api, file)`

```python
def on_file_loaded(api, file):
    api.logger.info(f"File loaded: {file.filename}")

def enable(api):
    api.register_file_post_load_processor(on_file_loaded)
```

---

#### `register_file_pre_save_processor(function, priority=0)`

Called just before a file is saved.

**Signature**: `function(api, file)`

```python
def on_file_saved(api, file):
    api.logger.info(f"File saved: {file.filename}")

def enable(api):
    api.register_file_pre_save_processor(on_file_saved)
```

---

#### `register_file_post_save_processor(function, priority=0)`

Called after a file is saved.

**Signature**: `function(api, file)`

```python
def on_file_saved(api, file):
    api.logger.info(f"File saved: {file.filename}")

def enable(api):
    api.register_file_post_save_processor(on_file_saved)
```

---

#### `register_file_post_addition_to_track_processor(function, priority=0)`

Called when a file is added to a track.

**Signature**: `function(api, track, file)`

---W

#### `register_file_post_removal_from_track_processor(function, priority=0)`

Called when a file is removed from a track.

**Signature**: `function(api, track, file)`

---

#### `register_album_post_removal_processor(function, priority=0)`

Called when an album is removed.

**Signature**: `function(api, album)`

---

### Script Functions

#### `register_script_function(function, name=None, eval_args=True, check_argcount=True, documentation=None)`

Register a custom tagger script function.

```python
def my_script_func(parser, arg1, arg2):
    """Custom script function."""
    return f"{arg1}-{arg2}"

def enable(api):
    api.register_script_function(
        my_script_func,
        name="my_func",  # Optional: defaults to function name
        documentation="Combines two arguments with a dash"
    )
```

**Usage in scripts**: `$my_func(value1,value2)`

**Parameters**:
- `function`: Function to register (first arg is always `parser`)
- `name`: Function name in scripts (default: function's `__name__`)
- `eval_args`: Whether to evaluate arguments (default: True)
- `check_argcount`: Whether to check argument count (default: True)
- `documentation`: Help text for the function

---

#### `register_script_variable(name, documentation=None)`

Register a variable name for script autocomplete.

```python
def enable(api):
    api.register_script_variable(
        "my_plugin_var",
        documentation="A custom variable from my plugin"
    )
```

**Parameters**:
- `name`: Variable name (without % symbols)
- `documentation`: Optional help text for the variable

---

### UI Actions

Context menu actions:

#### `register_album_action(action)`
#### `register_track_action(action)`
#### `register_file_action(action)`
#### `register_cluster_action(action)`
#### `register_clusterlist_action(action)`

Plugin Tools menu actions:

#### `register_tools_menu_action(action)`

Register menu actions for different object types.

```python
from picard.plugin3.api import BaseAction

class MyAction(BaseAction):
    TITLE = "My Custom Action"

    def callback(self, objs):
        for obj in objs:
            self.api.logger.info(f"Action on: {obj}")

def enable(api):
    # Context menus
    api.register_file_action(MyAction)
    api.register_track_action(MyAction)
    api.register_album_action(MyAction)
    api.register_cluster_action(MyAction)
    api.register_clusterlist_action(MyAction)

    # Plugin Tools menu
    register_tools_menu_action(action)
```

**Note**: Pass the class, not an instance. Picard makes `self.api` available inside
the class to access the `PluginApi` instance of the plugin.

---

### Options Pages

#### `register_options_page(page_class)`

Register a settings page in Picard's options dialog.

```python
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    NAME = "my_plugin"
    TITLE = "My Plugin"
    PARENT = "plugins"

    def __init__(self):
        super().__init__()
        # Build UI

    def load(self):
        # Load settings from self.api.plugin_config or self.api.global_config
        pass

    def save(self):
        # Save settings to self.api.plugin_config or self.api.global_config
        pass

def enable(api):
    api.register_options_page(MyOptionsPage)
```

**Required attributes**:
- `NAME`: Unique identifier
- `TITLE`: Display name
- `PARENT`: Parent page (usually "plugins")

**Required methods**:
- `load()`: Load settings into UI
- `save()`: Save settings from UI

---

### Cover Art Providers

#### `register_cover_art_provider(provider)`

Register a custom cover art provider.

```python
from picard.plugin3.api import CoverArtProvider

class MyProvider(CoverArtProvider):
    NAME = "My Provider"

    def queue_images(self):
        # Queue cover art images
        pass

def enable(api):
    api.register_cover_art_provider(MyProvider)
```

---

#### `register_cover_art_filter(filter)`

Register a filter to process cover art images.

```python
def my_cover_filter(api, metadata, image):
    """Filter cover art images."""
    # Return True to keep, False to discard
    return image.width >= 500

def enable(api):
    api.register_cover_art_filter(my_cover_filter)
```

**Signature**: `function(api, metadata, image) -> bool`

---

#### `register_cover_art_metadata_filter(filter)`

Register a filter to process cover art metadata.

```python
def my_metadata_filter(api, metadata, image_metadata):
    """Filter cover art by metadata."""
    return image_metadata.get('type') == 'front'

def enable(api):
    api.register_cover_art_metadata_filter(my_metadata_filter)
```

**Signature**: `function(api, metadata, image_metadata) -> bool`

---

#### `register_cover_art_processor(processor_class)`

Register a processor to modify cover art images.

```python
class MyProcessor:
    def save_to_tags(self):
        return True

    def save_to_file(self):
        return True

    def same_processing(self):
        return True

    def run(self, image):
        # Modify image
        return image

def enable(api):
    api.register_cover_art_processor(MyProcessor)
```

---

### File Formats

#### `register_format(format)`

Register support for a custom file format.

```python
from picard.plugin3.api import File

class MyFormat(File):
    EXTENSIONS = [".myformat"]
    NAME = "My Format"

    def _load(self, filename):
        # Load file
        pass

    def _save(self, filename):
        # Save file
        pass

def enable(api):
    api.register_format(MyFormat)
```

---

## Album Background Task Management

Plugins can track asynchronous operations (like web requests) without blocking album loading.

### `add_album_task(album, task_id, description, timeout=None, request_factory=None)`

Add a plugin task to an album. Plugin tasks are always non-blocking and won't prevent the album from being marked as loaded.

**Parameters**:
- `album`: The Album object
- `task_id`: Unique identifier (automatically prefixed with plugin_id)
- `description`: Human-readable description
- `timeout`: Optional timeout in seconds
- `request_factory`: Callable that creates and returns a PendingRequest. Use this to register network requests for automatic cancellation when the album is removed.

**Example - Fetching additional album data**:
```python
from functools import partial

def fetch_album_data(api, album, metadata, release):
    artist_id = metadata.get('musicbrainz_artistid')
    if not artist_id:
        return

    task_id = f'bio_{album.id}'

    def create_request():
        return api.web_service.get_url(
            url=f'https://api.example.com/artist/{artist_id}',
            handler=partial(handle_response, api, album, metadata, task_id)
        )

    api.add_album_task(
        album, task_id,
        f'Fetching artist bio for {artist_id}',
        request_factory=create_request
    )

def handle_response(api, album, metadata, task_id, data, error):
    try:
        if not error and data:
            metadata['~artist_bio'] = data.get('biography', '')
    finally:
        api.complete_album_task(album, task_id)

def enable(api):
    api.register_album_metadata_processor(fetch_album_data)
```

**Note**: If your task doesn't involve a network request, you can omit `request_factory`. However, if you're making a web request, you should always provide `request_factory` to ensure the request is properly cancelled if the album is removed.

---

### `complete_album_task(album, task_id)`

Mark a plugin task as complete.

**Parameters**:
- `album`: The Album object
- `task_id`: Same ID used in add_album_task (without plugin prefix)

**Example - Fetching cover art from external source**:
```python
def fetch_custom_cover(api, album, metadata, release):
    album_id = metadata.get('musicbrainz_albumid')
    if not album_id:
        return

    task_id = f'cover_{album_id}'
    api.add_album_task(album, task_id, 'Fetching custom cover art', timeout=10.0)

    request = api.web_service.download_url(
        url=f'https://covers.example.com/{album_id}.jpg',
        handler=lambda data, http, error: handle_cover(api, album, task_id, data, error)
    )
    api.set_album_task_request(album, task_id, request)

def handle_cover(api, album, task_id, data, error):
    try:
        if not error and data:
            # Process cover art data
            api.logger.info(f"Downloaded cover art: {len(data)} bytes")
    finally:
        api.complete_album_task(album, task_id)

def enable(api):
    api.register_album_metadata_processor(fetch_custom_cover)
```

**Important**: Always call `complete_album_task()` in a `finally` block to ensure the task is marked complete even if an error occurs.

---

## API Parameter Injection

### How It Works

Picard uses `functools.partial` to automatically inject the `api` parameter:

**For Processors**:
```python
def my_processor(api, track, metadata, track_node, release=None):
    # api is automatically injected as first parameter
    api.logger.info("Processing")

def enable(api):
    # Picard wraps this as: partial(my_processor, api)
    api.register_track_metadata_processor(my_processor)
```

**For Classes**:
```python
from picard.plugin3.api import OptionsPage

class MyPage(OptionsPage):
    def load(self):
        self.api.logger.info("Loading")

def enable(api):
    api.register_options_page(MyPage)
```

---

## Priority System

Many registration methods accept a `priority` parameter:

- **Higher priority** = executed earlier
- **Default**: 0
- **Range**: Typically -100 to 100

```python
def enable(api):
    # Run first
    api.register_track_metadata_processor(important_processor, priority=100)

    # Run normally
    api.register_track_metadata_processor(normal_processor)

    # Run last
    api.register_track_metadata_processor(cleanup_processor, priority=-100)
```

**Use cases**:
- High priority: Data fetching, critical preprocessing
- Normal priority: Most processors
- Low priority: Cleanup, formatting, final touches

---

## Complete Example

```python
from PyQt6.QtWidgets import QCheckBox
from picard.plugin3.api import PluginApi, BaseAction, OptionsPage, t_


class MyOptionsPage(OptionsPage):
    NAME = "example"
    TITLE = t_("Example Plugin")
    PARENT = "plugins"

    def __init__(self):
        super().__init__()
        self.checkbox = QCheckBox("Enable processing")
        self.layout().addWidget(self.checkbox)

    def load(self):
        enabled = self.api.global_config.setting.get('example_enabled', False)
        self.checkbox.setChecked(enabled)

    def save(self):
        self.api.global_config.setting['example_enabled'] = self.checkbox.isChecked()


def process_track(api, track, metadata, track_node, release=None):
    """Process track metadata."""
    if api.global_config.setting.get('example_enabled', False):
        api.logger.info(f"Processing: {metadata.get('title', 'Unknown')}")
        metadata['example_tag'] = 'processed'


def on_file_saved(api, file):
    """Called after file is saved."""
    api.logger.info(f"Saved: {file.filename}")


class MyAction(BaseAction):
    TITLE = t_("Example Action")

    def callback(self, objs):
        self.api.logger.info(f"Action on {len(objs)} objects")


def enable(api):
    """Plugin entry point."""
    api.logger.info("Example plugin loaded")

    # Register processors
    api.register_track_metadata_processor(process_track)
    api.register_file_post_save_processor(on_file_saved)

    # Register UI
    api.register_options_page(MyOptionsPage)
    api.register_file_action(MyAction)
```

---

## Best Practices

1. **Always use the api parameter**: Don't import Picard internals directly
2. **Use plugin_config for plugin settings**: Keeps your config isolated
3. **Log appropriately**: Use `debug` for verbose, `info` for important events
4. **Handle errors gracefully**: Wrap risky operations in try/except
5. **Set priorities wisely**: Only use non-zero priorities when order matters
6. **Pass api to parent classes**: You can use `self.api` in classes inherited from
   base classes meant to be subclassed and imported from `picard.plugin3.api`,
   like `BaseAction` or `OptionsPage`.

---

## See Also

- [Migration Guide](MIGRATION.md) - Migrating from V2 to V3
- [MANIFEST.toml](MANIFEST.md) - Plugin manifest format
- [Translations](TRANSLATIONS.md) - Internationalization
