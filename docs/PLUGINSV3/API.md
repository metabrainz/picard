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

## Class References

The following classes are available through the `api` object:

- `api.Album` - Album object
- `api.Track` - Track object
- `api.File` - File base class (for custom formats)
- `api.Cluster` - Cluster object
- `api.Metadata` - Metadata container for tags
- `api.CoverArtImage` - Cover art image object
- `api.CoverArtProvider` - Base class for cover art providers
- `api.BaseAction` - Base class for UI actions
- `api.OptionsPage` - Base class for options pages

**Example**:
```python
from picard.plugin3.api import BaseAction, OptionsPage, File, CoverArtProvider
from picard.metadata import Metadata

class MyProvider(CoverArtProvider):
    NAME = "My Provider"

class MyFormat(File):
    EXTENSIONS = [".custom"]

    def _load(self, filename):
        metadata = Metadata()
        # Load tags into metadata
        return metadata
```

**Note**: Base classes for inheritance (`BaseAction`, `OptionsPage`, `File`, `CoverArtProvider`) should be imported directly from `picard.plugin3.api`. Other classes like `Metadata`, `Track`, `Album`, etc. are accessed via the `api` parameter.

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
def my_processor(api, track, metadata):
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
    # Write values (any JSON-serializable type)
    api.plugin_config['text_option'] = 'value'
    api.plugin_config['bool_option'] = True
    api.plugin_config['int_option'] = 42
    api.plugin_config['list_option'] = ['a', 'b', 'c']

    # Read with defaults
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
from picard.plugin3.api import OptionsPage

class MyOptionsPage(OptionsPage):
    def __init__(self, api=None):
        super().__init__(api=api)

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

### `web_service: WebService`

Access to Picard's web service for HTTP requests.

```python
def my_processor(api, track, metadata):
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
def my_processor(api, track, metadata):
    # Simplified MusicBrainz API access
    api.mb_api.get_release_by_id(
        release_id,
        handler,
        inc=['artists', 'recordings']
    )
```

---

## Class References

These classes are available as attributes on the API for type hints and inheritance:

```python
api.Album          # picard.album.Album
api.Track          # picard.track.Track
api.File           # picard.file.File
api.Cluster        # picard.cluster.Cluster
api.CoverArtImage  # picard.coverart.image.CoverArtImage
api.BaseAction     # picard.extension_points.item_actions.BaseAction
api.OptionsPage    # picard.ui.options.OptionsPage
```

**Usage**:
```python
from picard.plugin3.api import BaseAction

class MyAction(BaseAction):
    NAME = "My Action"

    def __init__(self, api=None):
        super().__init__(api=api)

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, self.api.Track):
                # Handle track
                pass
```

---

## Registration Methods

### Metadata Processors

#### `register_track_metadata_processor(function, priority=0)`

Register a function to process track metadata.

**Signature**: `function(api, track, metadata)`

```python
def process_track(api, track, metadata):
    """Process track metadata."""
    api.logger.info(f"Processing: {metadata['title']}")
    metadata['custom_tag'] = 'value'

def enable(api):
    api.register_track_metadata_processor(process_track)
    # With priority
    api.register_track_metadata_processor(process_track, priority=100)
```

**Parameters**:
- `function`: Processor function (receives `api`, `track`, `metadata`)
- `priority`: Execution priority (higher = earlier, default: 0)

---

#### `register_album_metadata_processor(function, priority=0)`

Register a function to process album metadata.

**Signature**: `function(api, album, metadata)`

```python
def process_album(api, album, metadata):
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

---

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

#### `register_album_action(action)`
#### `register_track_action(action)`
#### `register_file_action(action)`
#### `register_cluster_action(action)`
#### `register_clusterlist_action(action)`

Register context menu actions for different object types.

```python
from picard.plugin3.api import BaseAction

class MyAction(BaseAction):
    NAME = "My Custom Action"

    def __init__(self, api=None):
        super().__init__(api=api)

    def callback(self, objs):
        for obj in objs:
            self.api.logger.info(f"Action on: {obj}")

def enable(api):
    api.register_file_action(MyAction)
    api.register_track_action(MyAction)
    api.register_album_action(MyAction)
    api.register_cluster_action(MyAction)
    api.register_clusterlist_action(MyAction)
```

**Note**: Pass the class, not an instance. Picard instantiates it with `api` parameter. Always call `super().__init__(api=api)` to properly initialize the parent class, which automatically sets `self.api` for you.

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

    def __init__(self, api=None):
        super().__init__(api=api)
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

#### `register_ui_init(function)`

Register a function to be called when the main window UI is initialized.

```python
def setup_ui(api):
    """Called when main window is ready."""
    api.logger.info("UI initialized")
    # Access api.window for main window

def enable(api):
    api.register_ui_init(setup_ui)
```

**Signature**: `function(api)`

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

## API Parameter Injection

### How It Works

Picard uses `functools.partial` to automatically inject the `api` parameter:

**For Processors**:
```python
def my_processor(api, track, metadata):
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
    def __init__(self, api=None):
        super().__init__(api=api)
        # self.api is automatically set by parent class

    def load(self):
        self.api.logger.info("Loading")

def enable(api):
    # Picard instantiates as: MyPage(api=api)
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
from picard.plugin3.api import OptionsPage, BaseAction


class MyOptionsPage(OptionsPage):
    NAME = "example"
    TITLE = "Example Plugin"
    PARENT = "plugins"

    def __init__(self, api=None):
        super().__init__(api=api)
        self.checkbox = QCheckBox("Enable processing")
        self.layout().addWidget(self.checkbox)

    def load(self):
        enabled = self.api.global_config.setting.get('example_enabled', False)
        self.checkbox.setChecked(enabled)

    def save(self):
        self.api.global_config.setting['example_enabled'] = self.checkbox.isChecked()


def process_track(api, track, metadata):
    """Process track metadata."""
    if api.global_config.setting.get('example_enabled', False):
        api.logger.info(f"Processing: {metadata.get('title', 'Unknown')}")
        metadata['example_tag'] = 'processed'


def on_file_saved(api, file):
    """Called after file is saved."""
    api.logger.info(f"Saved: {file.filename}")


class MyAction(BaseAction):
    NAME = "Example Action"

    def __init__(self, api=None):
        super().__init__(api=api)

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
6. **Pass api to parent classes**: Always call `super().__init__(api=api)` in BaseAction and OptionsPage subclasses (parent is set automatically by Picard)

---

## See Also

- [Migration Guide](MIGRATION.md) - Migrating from V2 to V3
- [MANIFEST.toml](MANIFEST.md) - Plugin manifest format
- [Translations](TRANSLATIONS.md) - Internationalization
