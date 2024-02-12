# Picard Plugin API v3 (Proposal)

## Introduction / Motivation

Picard's plugin system has made Picard very extensible and there exist many
plugins that extend Picard's functionality in various ways.

However, the current plugin system has multiple shortcomings. This document
proposes a new plugin system for Picard 3 to address those shortcomings.


## Scope

This document discusses the structure and API for Picard plugins and the
basics of distributing, installing and updating plugins.

> ***Note:** This document builds upon the extended discussion of requirements
> for a new plugin system on
> [the wiki](https://github.com/rdswift/picard-plugins/wiki/Picard-Plugins-System-Proposal).
> It proposes a specific implementation which tries to address the various ideas
> brought up in the above discussion.*


## Limitations of the old plugin system

- **No separation of metadata and code:** As the metadata, such as plugin name
  and description, but also supported API versions, is part of the Python code,
  each installed plugin's code was executed regardless of whether the plugin
  is enabled or even compatible with the current Picard version.

- **No defined API:** Apart from a few methods to register plugin hooks there
  is no actual API provided. This makes it both difficult for plugin developers
  to decide what parts of Picard can be safely used as well for Picard developers
  to decide which internal change should be considered a breaking change for plugins.

- **Imports scattered over the codebase:** The different functions for registering
  plugin hooks as well as the objects provided by Picard that are actually useful
  for plugins are all scattered over the Picard code base. While this follows a
  system that is logical if you are familiar with Picard's code base, this is not
  transparent to plugin developers.

- **Many supported plugin formats:** The old system allowed multiple ways how a
  plugin can be structured. The following formats where supported:
  - A single Python module (`example.py`)
  - A Python package (`example/__init__.py`)
  - A ZIP archive (`example.zip`) containing a single Python module
  - A ZIP archive (`example.zip`) containing a Python package
  - A ZIP archive (`example.picard.zip`) with either a Python module or package
    and an additional metadata file `MANIFEST.json`.
  This variation leeds to extra complexity in the implementation and increases
  maintenance and testing effort. It also increased complexity for users, as they
  needed to decide whether a plugin file needs to be placed at the top level
  or inside a directory.

- **Single central repository:** All official plugins must be located in the
  official [picard-plugins](https://github.com/metabrainz/picard-plugins) git
  repository. Only plugins located there can be installed directly from the UI
  and can receive automated updates. This makes it difficult for third-party
  developers to provide plugins and keep them updated. It also adds additional
  work on the Picard developers to maintain and update all submitted plugins.


## Format

A Picard plugin MUST be a Python package, that is a directory with a valid Python
package name containing at least a single `__init__.py` file. The package directory
MUST also contain a manifest file which provides metadata about the plugin.

The package directory MAY contain additional files, such as Python modules to load.

A basic plugin `example` could have the following structure:


```
example/
  __init__.py
  MANIFEST.toml
```


### File system locations

User plugins will be stored in a system specific location for application data
inside the `MusicBrainz/Picard/plugins3` directory. On the primary operating
systems those are:

- **Linux:** `~/.local/share/MusicBrainz/Picard/plugins3`
- **macOS:** `~/Library/Application Support/MusicBrainz/Picard/plugins3`
- **Windows:** `~/AppData/Roaming/MusicBrainz/Picard/plugins3`

System wide plugins will be loaded from Picard's install location from the
`plugins3` directory.


### Package structure and implemented API

The package MUST define the following top-level functions:

- `enable` gets called when the plugin gets enabled. This happens on startup for
  all enabled plugins and also if the user enables a previously disabled plugin.
  The function gets passed an instance of `picard.plugin.PluginApi`, which
  provides access to Picard's official plugin API and allows to register plugin hooks.

The package MAY define the following top-level functions:

- `disable` gets called when the plugin gets disabled. The plugin should stop all
  processing and free required resources. The plugin does not need to de-register
  plugin hooks, as those get disabled automatically.
  After being disabled the plugin can always be enabled again (the `enable`
  function gets called).

> ***Discussion:** Are `install` and `uninstall` hooks needed?*


A basic plugin structure could be:

```python
from picard.plugin3.api import PluginApi

def enable(api: PluginApi) -> None:
    # api can be used to register plugin hooks and to access essential Picard APIs.
    pass

def disable() -> None:
    pass
```

The plugin MUST NOT perform any actual work, apart from defining types and
functions, on import. All actual processing must be performed only as part of
the `enable` and `disable` functions and any plugin hooks registered in `enable`.


### Manifest format
The plugin's package directory MUST contain a file `MANIFEST.toml`.

> ***Discussion:** Is TOML the proper format, or should something like JSON or YAML be preferred?*

The file MUST define the following mandatory metadata fields:

| Field name     | Type   | Description                                                      |
|----------------|--------|------------------------------------------------------------------|
| id             | string | The plugin's unique name. Must be a valid Python package name and only consist of the characters `[a-z0-9_]` |
| name           | table  | Table of multi-lingual display names. The keys are locale names. At least an English description is mandatory. |
| author         | string | The plugin author                                                |
| description    | table  | Table of multi-lingual detailed plugin descriptions. The keys are locale names. At least an English description is mandatory. Supports Markdown formatting. |
| version        | string | Plugin version. Use semantic versioning in the format "x.y.z"    |
| api            | list   | The Picard API versions supported by the plugin                  |
| license        | string | License, should be a [SPDX license name](https://spdx.org/licenses/) and GPLv2 compatible |

The file MAY define any of the following optional fields:

| Field name     | Type   | Description                                                      |
|----------------|--------|------------------------------------------------------------------|
| license-url    | string | URL to the full license text                                     |
| user-guide-url | string | URL to the plugin's documentation                                |


Example `MANIFEST.toml`:

```toml
id          = "example"
name.en     = "Example plugin"
name.de     = "Beispiel-Plugin"
name.fr     = "Exemple de plugin"
author      = "Philipp Wolfer"
version     = "1.0.0"
api         = ["3.0", "3.1"]
license     = "CC0-1.0"
license-url = "https://creativecommons.org/publicdomain/zero/1.0/"
user-guide-url = "https://example.com/"

[description]
en = """
This is an example plugin showcasing the new **Picard 3** plugin API.

You can use [Markdown](https://daringfireball.net/projects/markdown/) for formatting."""
de = """
Dies ist ein Beispiel-Plugin, das die neue **Picard 3** Plugin-API vorstellt.

Du kannst [Markdown](https://daringfireball.net/projects/markdown/) für die Formatierung verwenden.
"""
fr = """
Ceci est un exemple de plugin présentant la nouvelle API de plugin **Picard 3**.

Vous pouvez utiliser [Markdown](https://daringfireball.net/projects/markdown/) pour la mise en forme.
"""
```


### Picard Plugin API

As described above the plugin's `enable` function gets called with an instance
of `picard.plugin.PluginApi`. `PluginApi` provides access to essential Picard
APIs and also allows registering plugin hooks.

`PluginApi` implements the interface below:

```python
from typing import (
    Callable,
    Type,
)
from logging import Logger

from picard.config import (
    Config,
    ConfigSection,
)
from picard.coverart.providers import CoverArtProvider
from picard.file import File
from picard.plugin import PluginPriority
from picard.webservice import WebService
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.itemviews import BaseAction
from picard.ui.options import OptionsPage

class PluginApi:
    @property
    def web_service(self) -> WebService:
        pass

    @property
    def mb_api(self) -> MBAPIHelper:
        pass

    @property
    def logger(self) -> Logger:
        pass

    @property
    def global_config(self) -> Config:
        pass

    @property
    def plugin_config(self) -> ConfigSection:
        """Configuration private to the plugin"""
        pass

    # Metadata processors
    def register_album_metadata_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    def register_track_metadata_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    # Event hooks
    def register_album_post_removal_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    def register_file_post_load_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    def register_file_post_addition_to_track_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    def register_file_post_removal_from_track_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    def register_file_post_save_processor(function: Callable, priority: PluginPriority = PluginPriority.NORMAL) -> None:
        pass

    # Cover art
    def register_cover_art_provider(provider: CoverArtProvider) -> None:
        pass

    # File formats
    def register_format(format: File) -> None:
        pass

    # Scripting
    def register_script_function(function: Callable, name: str = None, eval_args: bool = True,
                                 check_argcount: bool = True, documentation: str = None) -> None:
        pass

    # Context menu actions
    def register_album_action(action: BaseAction) -> None:
        pass

    def register_cluster_action(action: BaseAction) -> None:
        pass

    def register_clusterlist_action(action: BaseAction) -> None:
        pass

    def register_track_action(action: BaseAction) -> None:
        pass

    def register_file_action(action: BaseAction) -> None:
        pass

    # UI
    def register_options_page(page_class: Type[OptionsPage]) -> None:
        pass

    # TODO: Replace by init function in plugin
    # def register_ui_init(function: Callable) -> None:
    #     pass

    # Other ideas
    # Implement status indicators as an extension point. This allows plugins
    # that use alternative progress displays
    # def register_status_indicator(function: Callable) -> None:
    #     pass

    # Register page for file properties. Same for track and album
    # def register_file_info_page(page_class):
    #     pass

    # For the media player toolbar?
    # def register_toolbar(toolbar_class):
    #     pass
```


### Localization
TBD


### Plugin life cycle
TBD


## Distribution

In order to both simplify third-party development of plugins and distribute
the maintenance work there will no longer be a single plugin repository. Instead
each plugin SHOULD be provided in a separate git repository. Plugins also CAN
be installed locally without a git repository by placing the plugin package
inside the plugin directory.


### Repository structure

A Picard plugin repository MUST be a git repository containing exactly one
plugin. The content of the git repository MUST match the plugin file structure
as described above, containing at least the `__init__.py` and `MANIFEST.toml`
files.


### Installation and upgrade

Plugin installation is performed directly from git by cloning the git repository.
Likewise updates are performed by updating the repository and checking out the
requested git ref.

For plugins installed from git the version will be shown as a combination of
the version from the manifest and the git ref (`{VERSION}-{GITREF}`).


### Official plugins

The Picard website will provide a list of officially supported plugins and their
git location. Those plugins will be offered in the Picard user interface for
installation. Plugins can be added to the official list after a review. The
Picard website must provide an API endpoint for querying the metadata for all
the plugins. The metadata consists of both the information from the plugin
manifests and the git URL for each plugin.

The exact implementation for submitting plugins for the Picard website is
outside the scope of this document and will be discussed separately. It could
e.g. both be handled by opening tickets on the MetaBrainz Jira or by
implementing an actual plugin submission interface directly on the Picard
website.


### Installing plugins from unofficial sources

Picard must provide a user interface for installing third-party plugins which
are not provided in the official plugin list. The user needs to enter the
plugin's git URL and Picard will verify the manifest and offer to install and
activate the plugin. The UI must make it clear that the user is installing the
plugin at their own risk and that the plugin can execute arbitrary code.


## To be discussed

### Localization

Existing plugins in Picard 2 cannot be localized. The new plugin system should
allow plugins to provide translations for user facing strings.

Plugins could provide gettext `.mo` files that will be loaded under a plugin
specific translation domain.

Also the description from `MANIFEST.json` should be localizable.


### Categorization

See [PW-12](https://tickets.metabrainz.org/browse/PW-12)


### Extra data files

Does the Plugin API need to expose functions to allow plugins to easily load
additional data files shipped as part of the plugins? E.g. for loading
configuration from JSON files.


### Additional extension points

Which additional extension points should be supported?


### Support for ZIP compressed plugins:

As before plugins in a single ZIP archive could also be supported. The "Format"
section above could be extended with:

> The plugin package MAY be put into a ZIP archive. In this case the filename
> must be the same as the plugin package name followed by `.picard.zip`, e.g.
> `example.picard.zip`.

It needs to be discussed whether such plugins should be extracted by default
or whether module loading from ZIP should be retained.

The advantage of loading directly from ZIP is the simplicity of plugin handling,
as the user can move around a single plugin file.

Disadvantages are:

- Additional complexity in the module loader
- Inability of accessing shared libraries shipped as part of the plugin
- No bytecode caching


## Implementation considerations

- All objects exposed by `picard.plugin.PluginApi` SHOULD provide
  full type hinting for all methods and properties that are considered
  public API.
- It might be advisable in some cases that `picard.plugin.PluginApi` exposes
  only wrappers instead of the actual object to limit the exposed API.
