# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023-2024 Philipp Wolfer
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from collections.abc import Callable
from functools import (
    partial,
    update_wrapper,
)
import json
from logging import (
    Logger,
    getLogger,
)
from pathlib import Path
import re
import sys
import types
from typing import (
    TYPE_CHECKING,
    Any,
)

from PyQt6.QtCore import QLocale

from picard import log
from picard.album import Album
from picard.album_requests import TaskType
from picard.config import (
    Config,
    ProfileConfigSection,
    get_config,
)
from picard.coverart.image import CoverArtImage
from picard.coverart.providers import (
    CoverArtProvider as _CoverArtProvider,
    ProviderOptions as _ProviderOptions,
)
from picard.debug_opts import DebugOpt
from picard.extension_points.cover_art_filters import (
    register_cover_art_filter,
    register_cover_art_metadata_filter,
)
from picard.extension_points.cover_art_processors import (
    ImageProcessor as _ImageProcessor,
    register_cover_art_processor,
)
from picard.extension_points.cover_art_providers import (
    register_cover_art_provider,
)
from picard.extension_points.event_hooks import (
    register_album_post_removal_processor,
    register_file_post_addition_to_track_processor,
    register_file_post_load_processor,
    register_file_post_removal_from_track_processor,
    register_file_post_save_processor,
    register_file_pre_save_processor,
)
from picard.extension_points.item_actions import (
    BaseAction as _BaseAction,
    register_album_action,
    register_cluster_action,
    register_clusterlist_action,
    register_file_action,
    register_track_action,
)
from picard.extension_points.metadata import (
    register_album_metadata_processor,
    register_track_metadata_processor,
)
from picard.extension_points.metadata_tag_actions import register_metadata_tag_action
from picard.extension_points.options_pages import register_options_page
from picard.extension_points.plugin_tools_menu import register_tools_menu_action
from picard.extension_points.script_functions import register_script_function
from picard.extension_points.script_variables import register_script_variable
from picard.file import File
from picard.metadata import Metadata
from picard.plugin3.i18n import (
    PluginTranslator,
    get_plural_form,
)
from picard.plugin3.manifest import PluginManifest
from picard.track import Track
from picard.util.display_title_base import HasDisplayTitle
from picard.util.imageinfo import ImageInfo
from picard.webservice import (
    PendingRequest,
    WebService,
)
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.options import OptionsPage as _OptionsPage


try:
    import tomllib  # type: ignore[unresolved-import]
except (ImportError, ModuleNotFoundError):
    import tomli as tomllib  # type: ignore[no-redef]


if TYPE_CHECKING:
    from picard.tagger import Tagger


def t_(key: str, text: str | None = None, plural: str | None = None) -> str | tuple[str, str, str]:
    """Mark a string for translation extraction (no-op at runtime).

    This is a marker function for the translation extractor. At runtime,
    it returns the arguments in a format suitable for tr() or trn().

    Args:
        key: Translation key
        text: Default text (singular form)
        plural: Plural form (optional)

    Returns:
        - If no plural: returns key
        - If plural: returns (key, text, plural) tuple

    Example:
        # Simple translation
        ERROR_MSG = t_('error.not_found', 'Not found')
        # Use: api.tr(ERROR_MSG, 'Not found')

        # Plural translation
        FILE_COUNT = t_('files.count', '{n} file', '{n} files')
        # Use: api.trn(*FILE_COUNT, n=count)
    """
    if plural is not None:
        return (key, str(text), plural)
    return key


class BaseAction(_BaseAction):
    """Base class for plugin actions"""

    api: 'PluginApi'


class CoverArtProvider(_CoverArtProvider):
    """Base class for cover art providers"""

    api: 'PluginApi'


class ImageProcessor(_ImageProcessor):
    """Base class for cover art image processors"""

    api: 'PluginApi'


class OptionsPage(_OptionsPage):
    """Base class for plugin option pages"""

    # Default to have the parent set as plugins
    PARENT = 'plugins'

    api: 'PluginApi'


class ProviderOptions(_ProviderOptions):
    """Base class for plugin cover art option pages"""

    api: 'PluginApi'


class MetadataTagAction(HasDisplayTitle):
    """Base class for metadata tag context menu actions."""

    TITLE: str = ""
    api: 'PluginApi'

    def callback(self, tags: list[str], objects: set) -> None:
        raise NotImplementedError

    def is_visible(self, tags: list[str], objects: set) -> bool:
        return True


class PluginApi:
    # Class-level registries for get_api()
    _instances: dict[str, 'PluginApi'] = {}  # Maps module name -> PluginApi instance
    _module_cache: dict[str, 'PluginApi'] = {}  # Maps module name -> PluginApi instance (for faster lookup)
    _deprecation_warnings_emitted: set[tuple[str, str, int]] = set()  # Track emitted deprecation warnings

    def __init__(self, manifest: PluginManifest, tagger: 'Tagger') -> None:
        self._tagger: Tagger = tagger
        self._manifest = manifest
        self._plugin_module: types.ModuleType | None = None  # Will be set when plugin is enabled
        self._plugin_id = manifest.module_name
        full_name = f'plugin.{self._manifest.uuid}'
        self._logger = getLogger(f'main.plugin.{self._manifest.module_name}')
        self._api_config = ProfileConfigSection(get_config(), full_name)
        self._api_config.display_name = manifest.name()
        self._translations: dict[str, dict] = {}
        self._source_locale = manifest.source_locale
        self._plugin_dir: Path | None = None
        self._qt_translator: PluginTranslator | None = None
        self._mb_api: MBAPIHelper | None = None

    @staticmethod
    def _get_caller_info(frame_depth=2):
        """Get caller information for deprecation warnings.

        Args:
            frame_depth: Number of frames to go back (default 2)

        Returns:
            Tuple of (plugin_name, filename, lineno)
        """
        frame = sys._getframe(frame_depth)
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        plugin_name = "unknown"
        if 'plugins3' in filename:
            parts = filename.split('/')
            try:
                idx = parts.index('plugins3')
                plugin_name = parts[idx + 1]
                # Truncate to show only relative path within plugin directory
                filename = '/'.join(parts[idx + 2 :])
            except (ValueError, IndexError):
                pass

        return plugin_name, filename, lineno

    @classmethod
    def deprecation_warning(cls, message, *args, frame_depth=3):
        """Emit a deprecation warning once per unique caller location.

        Args:
            message: Warning message format string
            *args: Arguments for message formatting
            frame_depth: Number of frames to go back (default 3)
        """
        plugin_name, filename, lineno = cls._get_caller_info(frame_depth=frame_depth)
        warning_key = (plugin_name, filename, lineno)
        if warning_key not in cls._deprecation_warnings_emitted:
            cls._deprecation_warnings_emitted.add(warning_key)
            log.warning(
                "Plugin '%s' at %s:%d: " + message,
                plugin_name,
                filename,
                lineno,
                *args,
            )

    def _install_qt_translator(self) -> None:
        """Install Qt translator for .ui file translations."""
        if not self._translations:
            return
        self._logger.debug(
            f"Installing Qt translator with {len(self._translations)} locales: {list(self._translations.keys())}"
        )
        has_qt_keys = any(k.startswith('qt.') for trans_dict in self._translations.values() for k in trans_dict)
        if has_qt_keys:
            self._qt_translator = PluginTranslator(self._translations, self._source_locale, self._plugin_id)
            self._qt_translator._current_locale = self.get_locale()
            self._tagger._qt_translators.add_translator(self._qt_translator)

            # Only emit signal if application is already running (not during startup)
            # This ensures UI retranslation when plugins are installed dynamically
            if getattr(self._tagger, 'window', None):
                self._tagger._qt_translators_updated.emit()

    def _remove_qt_translator(self) -> None:
        """Remove Qt translator for .ui file translations."""
        if not self._qt_translator:
            return

        self._tagger._qt_translators.remove_translator(self._qt_translator)
        self._qt_translator = None

    def reload_translations(self) -> None:
        """Reload translations and reinstall Qt translator.

        Used when plugin is updated to refresh translations without recreating API instance.
        """
        # Clear existing translations
        self._translations.clear()

        # Remove old Qt translator
        self._remove_qt_translator()

        # Reload translations from disk
        self._load_translations()

        # Reinstall Qt translator with new translations
        self._install_qt_translator()

        # Emit signal to trigger Qt translator reinstall and UI retranslation
        # This is only called during plugin updates, not normal installation
        self._tagger._qt_translators_updated.emit()

    def _is_valid_locale(self, locale: str) -> bool:
        """Check if locale string is valid (basic sanity check).

        Valid locales are 2-5 characters, alphanumeric with optional underscore.
        Examples: en, de, pt_BR, zh_CN
        Case-insensitive to work on case-insensitive filesystems.
        """
        return bool(re.match(r'^[a-z]{2,3}(_[a-z]{2})?$', locale, re.IGNORECASE))

    def _find_translation_file(self, locale: str) -> tuple[Path | None, str | None]:
        """Find translation file for locale, preferring TOML over JSON.

        Returns:
            (file_path, format) or (None, None) if not found
        """
        if not self._plugin_dir:
            return None, None

        locale_dir = self._plugin_dir / 'locale'
        if not locale_dir.exists():
            return None, None

        # Check TOML first, then JSON
        toml_file = locale_dir / f'{locale}.toml'
        if toml_file.exists():
            return toml_file, 'toml'

        json_file = locale_dir / f'{locale}.json'
        if json_file.exists():
            return json_file, 'json'

        return None, None

    def _load_translation_file(self, file_path: Path, format: str, locale: str) -> dict | None:
        """Load a single translation file."""
        try:
            if format == 'toml':
                with open(file_path, 'rb') as f:
                    data = tomllib.load(f)
                    self._check_toml_structure(data, locale)
                    self._logger.debug(f"Loaded {format.upper()} translation file: {file_path}")
                    return data
            elif format == 'json':
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                    self._logger.debug(f"Loaded {format.upper()} translation file: {file_path}")
                    return data
        except Exception as e:
            self._logger.warning(f"Failed to load translation file {file_path}: {e}")
        return None

    def _check_toml_structure(self, data: dict, locale: str) -> None:
        """Check for nested structure in TOML and warn about unquoted keys."""

        def find_nested_keys(d: dict, path: str = '') -> list:
            nested = []
            for k, v in d.items():
                current_path = f'{path}.{k}' if path else k
                if isinstance(v, dict) and not self._is_plural_dict(v):
                    # Found nested dict - this means unquoted keys were used
                    nested.append(current_path)
                    # Recursively check deeper nesting
                    nested.extend(find_nested_keys(v, current_path))
            return nested

        nested_keys = find_nested_keys(data)
        if nested_keys:
            self._logger.warning(
                f"Translation file for locale '{locale}' uses nested structure. "
                f"Keys with dots should be quoted in TOML. Found nested keys: {', '.join(nested_keys[:3])}"
                f"{' and more...' if len(nested_keys) > 3 else ''}. "
                f"Example: use [\"message.test\"] instead of [message.test]"
            )

    def _is_plural_dict(self, d: dict) -> bool:
        """Check if dict is a plural forms dict (has keys like 'one', 'other', etc.)."""
        plural_keys = {'zero', 'one', 'two', 'few', 'many', 'other'}
        return bool(d.keys() & plural_keys)

    def _load_translations(self) -> None:
        """Load translation files from locale/ directory.

        Only loads translations for the current locale to avoid unnecessary I/O.
        """
        if not self._plugin_dir:
            return

        locale_dir = self._plugin_dir / 'locale'
        if not locale_dir.exists():
            return

        # Get current locale
        current_locale = self.get_locale()

        # Try to load current locale and source locale as fallback
        for locale in {current_locale, self._source_locale}:
            loaded = self._load_translation_file_for_locale(locale)
            if not loaded:
                # Fallback: try language without region (e.g., 'de' from 'de_DE')
                if '_' in locale:
                    lang = locale.split('_')[0]
                    loaded = self._load_translation_file_for_locale(lang)

            if not loaded:
                if locale == current_locale:
                    self._logger.debug(f"No translation file for ({current_locale}).")
                elif locale == self._source_locale:
                    self._logger.warning(f"Missing translation file for source locale ({self._source_locale}).")

    def _load_translation_file_for_locale(self, locale: str) -> bool:
        """Try to load translation file for given locale."""
        file_path, format = self._find_translation_file(locale)
        if file_path:
            assert format is not None
            data = self._load_translation_file(file_path, format, locale)
            if data:
                self._translations[locale] = data
                self._logger.debug(
                    "Loaded %d translations for locale '%s': %s", len(data), locale, list(data.keys())[:10]
                )
                return True
        return False

    @property
    def tagger(self) -> 'Tagger':
        """Access to the main Tagger instance."""
        return self._tagger

    @property
    def web_service(self) -> WebService:
        """Access to Picard's web service for HTTP requests.

        Use this to perform asynchronous HTTP requests. Results are delivered
        to a handler callback rather than returned directly.

        Returns:
            WebService: The web service instance.

        Example:
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
                    important=False,
                )
        """
        return self._tagger.webservice

    @property
    def mb_api(self) -> MBAPIHelper:
        """Helper for MusicBrainz API requests.

        Provides simplified access to the MusicBrainz web service, wrapping
        common lookups such as fetching a release by its MBID.

        Returns:
            MBAPIHelper: The MusicBrainz API helper instance.

        Example:
            def my_processor(api, album, metadata, release):
                api.mb_api.get_release_by_id(
                    release_id,
                    handler,
                    inc=['artists', 'recordings'],
                )
        """
        if not self._mb_api:
            self._mb_api = MBAPIHelper(self._tagger.webservice)
        return self._mb_api

    @property
    def logger(self) -> Logger:
        """Plugin-specific logger instance.

        Log messages are namespaced under ``plugin.{module_name}`` so that
        output can be attributed to the originating plugin.

        Returns:
            Logger: The logger instance for this plugin.

        Example:
            def enable(api):
                api.logger.debug("Debug message")
                api.logger.info("Info message")
                api.logger.warning("Warning message")
                api.logger.error("Error message")
        """
        return self._logger

    @property
    def plugin_id(self) -> str:
        """Plugin identifier (module name)."""
        return self._manifest.module_name

    @property
    def global_config(self) -> Config:
        """Access to Picard's global configuration.

        Use this to read or write Picard's shared settings. For settings
        private to the plugin, use :attr:`plugin_config` instead.

        Returns:
            Config: Picard's global configuration object.

        Example:
            def my_processor(api, album, metadata, release):
                # Read settings
                enabled = api.global_config.setting.get('my_plugin_enabled', False)

                # Write settings
                api.global_config.setting['my_plugin_enabled'] = True
        """
        return get_config()

    @property
    def plugin_config(self) -> ProfileConfigSection:
        """Configuration private to the plugin"""
        return self._api_config

    @property
    def plugin_dir(self) -> Path | None:
        """Path to the plugin directory.

        Returns:
            Path: Plugin directory path, or None if not available
        """
        return self._plugin_dir

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin's manifest."""
        return self._manifest

    def get_locale(self) -> str:
        """Get the current locale used by Picard.

        Returns:
            str: Current locale code (e.g., 'en', 'de_DE', 'pt_BR')
        """
        # Use Picard's UI language setting if available
        config = get_config()
        ui_language = config.setting['ui_language']
        if ui_language:
            return ui_language

        # Fall back to system locale
        return QLocale().name()

    @classmethod
    def get_api(cls) -> 'PluginApi':
        """Get the PluginApi instance for the calling plugin module.

        This is a convenience method for accessing the API instance from
        anywhere in plugin code without explicitly passing it around.

        Returns:
            PluginApi: The API instance for the calling plugin

        Raises:
            RuntimeError: If called from outside a plugin context

        Example:
            class MyWidget(QWidget):
                def __init__(self):
                    super().__init__()
                    api = PluginApi.get_api()
                    api.logger.info("Widget initialized")
        """
        frame = sys._getframe(1)
        module_name = frame.f_globals.get('__name__')
        if module_name is None:
            raise RuntimeError(f"No module_name found in {frame}")

        # Check cache first
        if module_name in cls._module_cache:
            return cls._module_cache[module_name]

        # Cache miss - do the lookup
        # Try exact match first
        if module_name in cls._instances:
            api = cls._instances[module_name]
        else:
            # Try to find parent module (for submodules)
            api = None
            for registered_module in cls._instances:
                if module_name.startswith(registered_module + '.'):
                    api = cls._instances[registered_module]
                    break

            if api is None:
                raise RuntimeError(f"No PluginApi instance found for module {module_name}")

        # Cache the result
        assert api is not None
        cls._module_cache[module_name] = api
        return api

    # Translation
    def tr(self, key: str, text: str | None = None, **kwargs) -> str:
        """Translate a string for the plugin.

        Args:
            key: Translation key
            text: Default text (fallback if no translation found)
            **kwargs: Placeholder values for string formatting

        Returns:
            Translated string with placeholders substituted
        """
        result = None

        # Try to get translation from loaded files
        if self._translations:
            locale = self.get_locale()
            # Try exact locale match (e.g., de_DE)
            if locale in self._translations and key in self._translations[locale]:
                result = self._translations[locale][key]
            else:
                # Try language without region (e.g., de from de_DE)
                lang = locale.split('_')[0]
                if lang in self._translations and key in self._translations[lang]:
                    result = self._translations[lang][key]
                else:
                    # Try source locale as fallback
                    if self._source_locale in self._translations and key in self._translations[self._source_locale]:
                        result = self._translations[self._source_locale][key]
                    elif DebugOpt.PLUGIN_TRANSLATIONS.enabled:
                        self._logger.debug("tr() no translation found for key '%s' in any locale", key)

        # Fall back to text parameter or key
        if result is None:
            result = text if text is not None else key
            if DebugOpt.PLUGIN_TRANSLATIONS.enabled:
                self._logger.debug("tr() using fallback: '%s' -> '%s'", key, result)

        # Apply placeholder substitution
        if kwargs:
            result = result.format(**kwargs)

        return result

    def trn(self, key: str, singular: str | None = None, plural: str | None = None, n: int = 0, **kwargs) -> str:
        """Translate a string with plural forms.

        Args:
            key: Translation key
            singular: Default singular text (for n=1 in English)
            plural: Default plural text (for n!=1 in English)
            n: Number to determine plural form
            **kwargs: Placeholder values for string formatting

        Returns:
            Translated string with placeholders substituted
        """
        # Ensure n is in kwargs for formatting
        if 'n' not in kwargs:
            kwargs['n'] = n

        result = None

        # Try to get translation from loaded files
        if self._translations:
            locale = self.get_locale()
            plural_form = get_plural_form(locale, n)

            def get_plural_translation(trans: Any, plural_form: str) -> str | None:
                if isinstance(trans, dict):
                    if plural_form in trans:
                        return trans[plural_form]
                    elif 'other' in trans:
                        return trans['other']
                return None

            # Try exact locale match
            if locale in self._translations and key in self._translations[locale]:
                trans = self._translations[locale][key]
                result = get_plural_translation(trans, plural_form)
            else:
                # Try language without region
                lang = locale.split('_')[0]
                if lang in self._translations and key in self._translations[lang]:
                    trans = self._translations[lang][key]
                    result = get_plural_translation(trans, plural_form)
                else:
                    # Try source locale as fallback
                    if self._source_locale in self._translations and key in self._translations[self._source_locale]:
                        trans = self._translations[self._source_locale][key]
                        source_plural_form = get_plural_form(self._source_locale, n)
                        result = get_plural_translation(trans, source_plural_form)

        # Fall back to singular/plural parameters
        if result is None:
            if n == 1 and singular is not None:
                result = singular
            elif plural is not None:
                result = plural
            elif singular is not None:
                result = singular
            else:
                result = key

        # Apply placeholder substitution
        if kwargs:
            result = result.format(**kwargs)

        return result

    # Metadata processors
    def register_album_metadata_processor(
        self, function: Callable[['PluginApi', Album, Metadata, dict], None], priority: int = 0
    ) -> None:
        """Register a function to process album metadata.

        The registered function is called for each album that is loaded,
        allowing it to inspect or modify the album's metadata.

        Args:
            function: The processor function to register. The ``api`` argument
                is injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``album``: The :class:`Album` being processed.
                - ``metadata``: The :class:`Metadata` to read from and modify.
                - ``release_node``: The raw MusicBrainz release data as a dict.

                Expected signature::

                    def function(api, album, metadata, release_node):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def process_album(api, album, metadata, release_node):
                metadata['custom_album_tag'] = 'value'

            def enable(api):
                api.register_album_metadata_processor(process_album)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_album_metadata_processor(wrapped, priority)

    def register_track_metadata_processor(
        self, function: Callable[['PluginApi', Track, Metadata, dict, dict | None], None], priority: int = 0
    ) -> None:
        """Register a function to process track metadata.

        The registered function is called for each track that is loaded,
        allowing it to inspect or modify the track's metadata.

        Args:
            function: The processor function to register. The ``api`` argument
                is injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``track``: The :class:`Track` being processed.
                - ``metadata``: The :class:`Metadata` to read from and modify.
                - ``track_node``: The raw MusicBrainz track data as a dict.
                - ``release_node``: The raw MusicBrainz release data as a dict,
                  or ``None`` if not available.

                Expected signature::

                    def function(api, track, metadata, track_node, release_node=None):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def process_track(api, track, metadata, track_node, release_node=None):
                api.logger.info(f"Processing: {metadata['title']}")
                metadata['custom_tag'] = 'value'

            def enable(api):
                api.register_track_metadata_processor(process_track)
                # With priority
                api.register_track_metadata_processor(process_track, priority=100)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_track_metadata_processor(wrapped, priority)

    # Event hooks
    def register_album_post_removal_processor(
        self, function: Callable[['PluginApi', Album], None], priority: int = 0
    ) -> None:
        """Register a function called after an album is removed.

        Args:
            function: The function to register. The ``api`` argument is
                injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``album``: The :class:`Album` that was removed.

                Expected signature::

                    def function(api, album):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def on_album_removed(api, album):
                api.logger.info(f"Album removed: {album.id}")

            def enable(api):
                api.register_album_post_removal_processor(on_album_removed)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_album_post_removal_processor(wrapped, priority)

    def register_file_post_load_processor(
        self, function: Callable[['PluginApi', File], None], priority: int = 0
    ) -> None:
        """Register a function called after a file is loaded.

        Args:
            function: The function to register. The ``api`` argument is
                injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``file``: The :class:`File` that was loaded.

                Expected signature::

                    def function(api, file):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def on_file_loaded(api, file):
                api.logger.info(f"File loaded: {file.filename}")

            def enable(api):
                api.register_file_post_load_processor(on_file_loaded)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_load_processor(wrapped, priority)

    def register_file_post_addition_to_track_processor(
        self, function: Callable[['PluginApi', Track, File], None], priority: int = 0
    ) -> None:
        """Register a function called when a file is added to a track.

        Args:
            function: The function to register. The ``api`` argument is
                injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``track``: The :class:`Track` the file was added to.
                - ``file``: The :class:`File` that was added.

                Expected signature::

                    def function(api, track, file):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def on_file_added(api, track, file):
                api.logger.info(f"{file.filename} added to {track}")

            def enable(api):
                api.register_file_post_addition_to_track_processor(on_file_added)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_addition_to_track_processor(wrapped, priority)

    def register_file_post_removal_from_track_processor(
        self, function: Callable[['PluginApi', Track, File], None], priority: int = 0
    ) -> None:
        """Register a function called when a file is removed from a track.

        Args:
            function: The function to register. The ``api`` argument is
                injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``track``: The :class:`Track` the file was removed from.
                - ``file``: The :class:`File` that was removed.

                Expected signature::

                    def function(api, track, file):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def on_file_removed(api, track, file):
                api.logger.info(f"{file.filename} removed from {track}")

            def enable(api):
                api.register_file_post_removal_from_track_processor(on_file_removed)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_removal_from_track_processor(wrapped, priority)

    def register_file_post_save_processor(
        self, function: Callable[['PluginApi', File], None], priority: int = 0
    ) -> None:
        """Register a function called after a file is saved.

        Args:
            function: The function to register. The ``api`` argument is
                injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``file``: The :class:`File` that was saved.

                Expected signature::

                    def function(api, file):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def on_file_saved(api, file):
                api.logger.info(f"File saved: {file.filename}")

            def enable(api):
                api.register_file_post_save_processor(on_file_saved)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_save_processor(wrapped, priority)

    def register_file_pre_save_processor(
        self, function: Callable[['PluginApi', File], None], priority: int = 0
    ) -> None:
        """Register a function called just before a file is saved.

        Args:
            function: The function to register. The ``api`` argument is
                injected automatically, so the function receives the
                following parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``file``: The :class:`File` that is about to be saved.

                Expected signature::

                    def function(api, file):
                        ...

            priority: Execution priority. Higher values run earlier
                (default: 0).

        Example:
            def on_file_saving(api, file):
                api.logger.info(f"About to save: {file.filename}")

            def enable(api):
                api.register_file_pre_save_processor(on_file_saving)
        """
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_pre_save_processor(wrapped, priority)

    # Cover art
    def register_cover_art_provider(self, provider_class: type[CoverArtProvider]) -> None:
        """Register a custom cover art provider.

        The provider supplies cover art images from a custom source. Pass the
        class, not an instance; Picard makes ``self.api`` available inside the
        class to access the :class:`PluginApi` instance.

        Args:
            provider_class: A subclass of :class:`CoverArtProvider`. It should
                define a ``NAME`` attribute and implement ``queue_images()`` to
                queue the cover art images it provides.

        Example:
            from picard.plugin3.api import CoverArtProvider

            class MyProvider(CoverArtProvider):
                NAME = "My Provider"

                def queue_images(self):
                    # Queue cover art images
                    pass

            def enable(api):
                api.register_cover_art_provider(MyProvider)
        """
        provider_class.api = self
        self._set_class_name_and_title(provider_class)
        if getattr(provider_class, 'OPTIONS', None):
            provider_class.OPTIONS.api = self  # type: ignore[attr-defined]
            provider_class.OPTIONS.OPTION_SECTION = self._api_config.section_name
        return register_cover_art_provider(provider_class)

    def register_cover_art_filter(
        self, filter: Callable[['PluginApi', bytes, ImageInfo, Album | None, CoverArtImage], bool]
    ) -> None:
        """Register a filter to decide which cover art images to keep.

        The filter is called for each downloaded cover art image. Return
        ``True`` to keep the image or ``False`` to discard it.

        Args:
            filter: The filter function to register. The ``api`` argument is
                injected automatically, so the function receives the following
                parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``data``: The raw image data as ``bytes``.
                - ``image_info``: An :class:`ImageInfo` describing the image
                  (e.g. ``width``, ``height``, ``mime``).
                - ``album``: The :class:`Album` the image belongs to, or
                  ``None``.
                - ``image``: The :class:`CoverArtImage` object.

                Expected signature::

                    def filter(api, data, image_info, album, image) -> bool:
                        ...

        Example:
            def my_cover_filter(api, data, image_info, album, image) -> bool:
                # Keep only images that are at least 500px wide
                return image_info.width >= 500

            def enable(api):
                api.register_cover_art_filter(my_cover_filter)
        """
        wrapped = partial(filter, self)
        update_wrapper(wrapped, filter)
        return register_cover_art_filter(wrapped)

    def register_cover_art_metadata_filter(self, filter: Callable[['PluginApi', dict[str, Any]], bool]) -> None:
        """Register a filter to decide which cover art to keep by its metadata.

        The filter is called with the cover art's metadata before the image is
        downloaded. Return ``True`` to keep the image or ``False`` to discard
        it.

        Args:
            filter: The filter function to register. The ``api`` argument is
                injected automatically, so the function receives the following
                parameters:

                - ``api``: The :class:`PluginApi` instance.
                - ``image_metadata``: A dict with the cover art metadata
                  (e.g. its ``type``).

                Expected signature::

                    def filter(api, image_metadata) -> bool:
                        ...

        Example:
            def my_metadata_filter(api, image_metadata) -> bool:
                return image_metadata.get('type') == 'front'

            def enable(api):
                api.register_cover_art_metadata_filter(my_metadata_filter)
        """
        wrapped = partial(filter, self)
        update_wrapper(wrapped, filter)
        return register_cover_art_metadata_filter(wrapped)

    def register_cover_art_processor(self, processor_class: type[ImageProcessor]) -> None:
        """Register a processor to modify cover art images.

        The processor can transform cover art images before they are saved to
        tags or to a file. Pass the class, not an instance; Picard makes
        ``self.api`` available inside the class.

        Args:
            processor_class: A subclass of :class:`ImageProcessor`. It should
                implement ``run(image)`` to modify the image and may override
                ``save_to_tags()``, ``save_to_file()`` and ``same_processing()``
                to control when it is applied.

        Example:
            from picard.plugin3.api import ImageProcessor

            class MyProcessor(ImageProcessor):
                def save_to_tags(self):
                    return True

                def save_to_file(self):
                    return True

                def run(self, image):
                    # Modify the image in place
                    pass

            def enable(api):
                api.register_cover_art_processor(MyProcessor)
        """
        processor_class.api = self
        return register_cover_art_processor(processor_class)

    # File formats
    def register_format(self, format: type[File]) -> None:
        """Register support for a custom file format.

        Args:
            format: A subclass of :class:`File` implementing the custom format.
                It should define ``NAME`` and ``EXTENSIONS`` attributes and
                implement ``_load()`` and ``_save()``.

        Example:
            from picard.plugin3.api import File

            class MyFormat(File):
                NAME = "My Format"
                EXTENSIONS = [".myformat"]

                def _load(self, filename):
                    # Load file and return its Metadata
                    pass

                def _save(self, filename):
                    # Save metadata to file
                    pass

            def enable(api):
                api.register_format(MyFormat)
        """
        return self._tagger.format_registry.register(format)

    # Scripting
    def register_script_function(
        self,
        function: Callable,
        name: str | None = None,
        eval_args: bool = True,
        check_argcount: bool = True,
        documentation: str | None = None,
        signature: str | None = None,
    ) -> None:
        """Register a custom tagger script function.

        Once registered, the function can be used in tagger scripts as
        ``$name(...)``.

        Args:
            function: The function to register. Its first argument is always
                the script ``parser``, followed by the script arguments.

                Expected signature::

                    def function(parser, arg1, arg2, ...):
                        ...

            name: The function name to use in scripts. Defaults to the
                function's ``__name__``.
            eval_args: Whether to evaluate the arguments before passing them to
                the function (default: ``True``).
            check_argcount: Whether to validate the number of arguments
                (default: ``True``).
            documentation: Optional help text shown for the function.
            signature: Optional signature string shown in the documentation
                (e.g. ``"$my_func(arg1,arg2)"``).

        Example:
            def my_script_func(parser, arg1, arg2):
                return f"{arg1}-{arg2}"

            def enable(api):
                api.register_script_function(
                    my_script_func,
                    name="my_func",  # Optional: defaults to function name
                    documentation="Combines two arguments with a dash",
                    signature="$my_func(arg1,arg2)",
                )

            # Usage in scripts: $my_func(value1,value2)
        """
        return register_script_function(function, name, eval_args, check_argcount, documentation, signature)

    def register_script_variable(self, name: str, documentation: str | None = None, title: str | None = None) -> None:
        """Register a variable name for script autocomplete.

        Args:
            name: The variable name without the surrounding ``%`` symbols.
            documentation: Optional help text shown for the variable.
            title: Optional display title for the metadata box (e.g.,
                "Pinned Tags"). If provided, the tag shows this title
                instead of the raw name.

        Example:
            def enable(api):
                api.register_script_variable(
                    "my_plugin_var",
                    documentation="A custom variable from my plugin",
                    title="My Variable",
                )
        """
        return register_script_variable(name, documentation, self, title=title)

    # Menu actions
    def register_album_action(self, action: type[BaseAction]) -> None:
        """Register a context menu action for albums.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class to access the :class:`PluginApi` instance. The
        action's ``callback(objs)`` is invoked with the selected albums.

        Args:
            action: A subclass of :class:`BaseAction` defining a ``TITLE`` and
                a ``callback(self, objs)`` method.

        Example:
            from picard.plugin3.api import BaseAction

            class MyAction(BaseAction):
                TITLE = "My Custom Action"

                def callback(self, objs):
                    for obj in objs:
                        self.api.logger.info(f"Action on: {obj}")

            def enable(api):
                api.register_album_action(MyAction)
        """
        action.api = self
        return register_album_action(action)

    def register_cluster_action(self, action: type[BaseAction]) -> None:
        """Register a context menu action for clusters.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class. The action's ``callback(objs)`` is invoked with the
        selected clusters.

        Args:
            action: A subclass of :class:`BaseAction` defining a ``TITLE`` and
                a ``callback(self, objs)`` method.

        Example:
            from picard.plugin3.api import BaseAction

            class MyAction(BaseAction):
                TITLE = "My Custom Action"

                def callback(self, objs):
                    for obj in objs:
                        self.api.logger.info(f"Action on: {obj}")

            def enable(api):
                api.register_cluster_action(MyAction)
        """
        action.api = self
        return register_cluster_action(action)

    def register_clusterlist_action(self, action: type[BaseAction]) -> None:
        """Register a context menu action for the cluster list.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class. The action's ``callback(objs)`` is invoked with the
        selected cluster list items.

        Args:
            action: A subclass of :class:`BaseAction` defining a ``TITLE`` and
                a ``callback(self, objs)`` method.

        Example:
            from picard.plugin3.api import BaseAction

            class MyAction(BaseAction):
                TITLE = "My Custom Action"

                def callback(self, objs):
                    for obj in objs:
                        self.api.logger.info(f"Action on: {obj}")

            def enable(api):
                api.register_clusterlist_action(MyAction)
        """
        action.api = self
        return register_clusterlist_action(action)

    def register_track_action(self, action: type[BaseAction]) -> None:
        """Register a context menu action for tracks.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class. The action's ``callback(objs)`` is invoked with the
        selected tracks.

        Args:
            action: A subclass of :class:`BaseAction` defining a ``TITLE`` and
                a ``callback(self, objs)`` method.

        Example:
            from picard.plugin3.api import BaseAction

            class MyAction(BaseAction):
                TITLE = "My Custom Action"

                def callback(self, objs):
                    for obj in objs:
                        self.api.logger.info(f"Action on: {obj}")

            def enable(api):
                api.register_track_action(MyAction)
        """
        action.api = self
        return register_track_action(action)

    def register_file_action(self, action: type[BaseAction]) -> None:
        """Register a context menu action for files.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class. The action's ``callback(objs)`` is invoked with the
        selected files.

        Args:
            action: A subclass of :class:`BaseAction` defining a ``TITLE`` and
                a ``callback(self, objs)`` method.

        Example:
            from picard.plugin3.api import BaseAction

            class MyAction(BaseAction):
                TITLE = "My Custom Action"

                def callback(self, objs):
                    for obj in objs:
                        self.api.logger.info(f"Action on: {obj}")

            def enable(api):
                api.register_file_action(MyAction)
        """
        action.api = self
        return register_file_action(action)

    def register_tools_menu_action(self, action: type[BaseAction]) -> None:
        """Register an action in the plugin Tools menu.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class. The action's ``callback(objs)`` is invoked when the
        menu item is triggered.

        Args:
            action: A subclass of :class:`BaseAction` defining a ``TITLE`` and
                a ``callback(self, objs)`` method.

        Example:
            from picard.plugin3.api import BaseAction

            class MyAction(BaseAction):
                TITLE = "My Custom Action"

                def callback(self, objs):
                    self.api.logger.info("Triggered from Tools menu")

            def enable(api):
                api.register_tools_menu_action(MyAction)
        """
        action.api = self
        return register_tools_menu_action(action)

    def register_metadata_tag_action(self, action: type[MetadataTagAction]) -> None:
        """Register a context menu action for metadata tags.

        The action appears in the context menu when right-clicking a tag in
        the metadata view. Pass the class, not an instance. Picard makes
        ``self.api`` available inside the class.

        Args:
            action: A subclass of :class:`MetadataTagAction` defining:

                - ``TITLE``: str — The menu item label. Use ``t_()`` for
                  plugin translations (see :class:`HasDisplayTitle`).
                - ``callback(self, tags, objects)``: Called when the action is
                  triggered. Receives the list of selected tag names and the
                  set of selected objects (files, tracks, albums).
                - ``is_visible(self, tags, objects)`` (optional): Return
                  ``True`` to show the action, ``False`` to hide it.
                  Defaults to ``True``.

        Example:
            from picard.plugin3.api import (
                MetadataTagAction,
                t_,
            )

            class PinTagAction(MetadataTagAction):
                TITLE = t_("action.pin_tag", "Pin Tag")

                def callback(self, tags, objects):
                    for tag in tags:
                        self.api.logger.info(f"Pinning tag: {tag}")

                def is_visible(self, tags, objects):
                    return all(not tag.startswith('~') for tag in tags)

            def enable(api):
                api.register_metadata_tag_action(PinTagAction)
        """
        action.api = self
        return register_metadata_tag_action(action)

    # UI
    def register_options_page(self, page_class: type[OptionsPage]) -> None:
        """Register a settings page in Picard's options dialog.

        Pass the class, not an instance. Picard makes ``self.api`` available
        inside the class to access the :class:`PluginApi` instance.

        Args:
            page_class: A subclass of :class:`OptionsPage`. It should define the
                ``NAME``, ``TITLE`` and ``PARENT`` (usually ``"plugins"``)
                attributes and implement ``load()`` and ``save()`` to load
                settings into the UI and persist them again.

        Example:
            from picard.plugin3.api import OptionsPage

            class MyOptionsPage(OptionsPage):
                NAME = "my_plugin"
                TITLE = "My Plugin"
                PARENT = "plugins"

                def __init__(self):
                    super().__init__()
                    # Build UI

                def load(self):
                    enabled = self.api.plugin_config.get('enabled', True)

                def save(self):
                    self.api.plugin_config['enabled'] = True

            def enable(api):
                api.register_options_page(MyOptionsPage)
        """
        page_class.api = self
        page_class.OPTION_SECTION = self._api_config.section_name
        # The options page needs a unique name if no name was given
        self._set_class_name_and_title(page_class)
        return register_options_page(page_class)

    # Album task management for plugins
    def add_album_task(
        self,
        album: Album,
        task_id: str,
        description: str,
        timeout: float | None = None,
        request_factory: Callable[[], PendingRequest] | None = None,
        blocking: bool = False,
    ) -> None:
        """Add a plugin task to an album.

        Plugin tasks default to non-blocking (TaskType.PLUGIN) and will not prevent
        the album from being marked as loaded unless blocking=True is set. This allows
        plugins to fetch additional data asynchronously without blocking the user interface.

        Args:
            album: The Album object to add the task to
            task_id: Unique identifier for this task (will be prefixed with plugin_id)
            description: Human-readable description of what the task does
            timeout: Optional timeout in seconds. When blocking=True, capped at 30 seconds
                     maximum (defaults to 30s if not specified) to prevent UI freezing during
                     album loading. When blocking=False, no plugin-level cap is applied. Note
                     that all timeouts are ultimately capped by the user-configurable
                     network_transfer_timeout_seconds setting (default 30s).
            request_factory: Optional callable that creates and returns a PendingRequest.
                           If provided, the request is created and registered atomically.
            blocking: If True, prevents the album from being marked as loaded until this
                      task completes (uses TaskType.CRITICAL). Use with caution as this
                      blocks album loading. Always specify a reasonable timeout when using
                      blocking=True. Defaults to False (TaskType.PLUGIN).

        Example:
            def fetch_extra_data(api, album, metadata, release):
                task_id = f'extra_data_{album.id}'
                api.add_album_task(
                    album, task_id, 'Fetching artist biography',
                    request_factory=lambda: api.web_service.get_url(
                        url=f'https://example.com/artist/{artist_id}',
                        handler=lambda data, http, error: api.complete_album_task(album, task_id)
                    )
                )
        """
        # Hard limit for blocking tasks to prevent UI freezing during album loading,
        # independent of user-configurable network timeout setting
        MAX_TIMEOUT = 30.0
        full_task_id = f'{self.plugin_id}_{task_id}'

        if blocking:
            task_type = TaskType.CRITICAL
            blocking_text = ' [BLOCKING]'
            if timeout is None:
                timeout = MAX_TIMEOUT
            else:
                timeout = min(timeout, MAX_TIMEOUT)
        else:
            task_type = TaskType.PLUGIN
            blocking_text = ''

        album.add_task(
            task_id=full_task_id,
            task_type=task_type,
            description=f'[{self.plugin_id}] {description}{blocking_text}',
            timeout=timeout,
            plugin_id=self.plugin_id,
            request_factory=request_factory,
        )

    def complete_album_task(self, album: Album, task_id: str) -> None:
        """Mark a plugin task as complete.

        Args:
            album: The Album object the task was added to
            task_id: The same task_id used in add_album_task (without plugin prefix)

        Example:
            api.complete_album_task(album, 'extra_data')
        """
        full_task_id = f'{self.plugin_id}_{task_id}'
        album.complete_task(full_task_id)

    # Other ideas
    # Implement status indicators as an extension point. This allows plugins
    # that use alternative progress displays
    # def register_status_indicator(self, function: Callable) -> None:
    #     pass

    # Register page for file properties. Same for track and album
    # def register_file_info_page(self, page_class):
    #     pass

    def get_plugin_version(self) -> str:
        """Get the plugin's own version as displayed in CLI and GUI.

        Returns:
            str: Version string in format "ref @commit", "@commit", manifest version,
                 or "Unknown" if version cannot be determined
        """
        plugin_manager = self._tagger.get_plugin_manager()
        if not plugin_manager or not self._manifest.uuid:
            return "Unknown"

        metadata = plugin_manager._get_plugin_metadata(self._manifest.uuid)
        if metadata:
            return plugin_manager.get_plugin_git_info(metadata)

        return str(self._manifest.version) if self._manifest.version else "Unknown"

    def _set_class_name_and_title(self, cls: type[HasDisplayTitle]):
        if not hasattr(cls, 'NAME') or not cls.NAME:
            cls.NAME = f'{self.plugin_id}.{cls.__name__}'  # type: ignore[attr-defined]
        if not hasattr(cls, 'TITLE') or not cls.TITLE:
            cls.TITLE = self.manifest.name_i18n()  # type: ignore[attr-defined]
