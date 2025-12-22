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
from logging import (
    Logger,
    getLogger,
)
from pathlib import Path
import sys
import types

from picard.util.display_title_base import HasDisplayTitle
from picard.util.imageinfo import ImageInfo


try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from picard.tagger import Tagger


from picard.album import Album
from picard.album_requests import TaskType
from picard.config import (
    Config,
    ConfigSection,
    get_config,
)
from picard.coverart.image import CoverArtImage
from picard.coverart.providers import (
    CoverArtProvider as _CoverArtProvider,
    ProviderOptions as _ProviderOptions,
)
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
from picard.webservice import (
    PendingRequest,
    WebService,
)
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.options import OptionsPage as _OptionsPage


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


class PluginApi:
    # Class-level registries for get_api()
    _instances: dict[str, 'PluginApi'] = {}  # Maps module name -> PluginApi instance
    _module_cache: dict[str, 'PluginApi'] = {}  # Maps module name -> PluginApi instance (for faster lookup)
    _deprecation_warnings_emitted: set[tuple[str, str, int]] = set()  # Track emitted deprecation warnings

    def __init__(self, manifest: PluginManifest, tagger: 'Tagger') -> None:
        self._tagger: 'Tagger' = tagger
        self._manifest = manifest
        self._plugin_module: types.ModuleType | None = None  # Will be set when plugin is enabled
        self._plugin_id = manifest.module_name
        full_name = f'plugin.{self._manifest.uuid}'
        self._logger = getLogger(f'main.plugin.{self._manifest.module_name}')
        self._api_config = ConfigSection(get_config(), full_name)
        self._translations: dict[str, dict] = {}
        self._source_locale = manifest.source_locale
        self._plugin_dir: Path | None = None
        self._qt_translator: PluginTranslator | None = None

    @staticmethod
    def _get_caller_info(frame_depth=2):
        """Get caller information for deprecation warnings.

        Args:
            frame_depth: Number of frames to go back (default 2)

        Returns:
            Tuple of (plugin_name, filename, lineno)
        """
        import sys

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
        from picard import log

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
            if hasattr(self._tagger, 'window') and self._tagger.window:
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
        import re

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
                import json

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
    def tagger(self):
        """Access to the main Tagger instance."""
        return self._tagger

    @property
    def web_service(self) -> WebService:
        return self._tagger.webservice

    @property
    def mb_api(self) -> MBAPIHelper:
        return MBAPIHelper(self._tagger.webservice)

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def plugin_id(self) -> str:
        """Plugin identifier (module name)."""
        return self._manifest.module_name

    @property
    def global_config(self) -> Config:
        return get_config()

    @property
    def plugin_config(self) -> ConfigSection:
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
        from PyQt6.QtCore import QLocale

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
                    else:
                        self._logger.debug("tr() no translation found for key '%s' in any locale", key)

        # Fall back to text parameter or key
        if result is None:
            result = text if text is not None else key
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

            # Try exact locale match
            if locale in self._translations and key in self._translations[locale]:
                trans = self._translations[locale][key]
                if isinstance(trans, dict) and plural_form in trans:
                    result = trans[plural_form]
                elif isinstance(trans, dict) and 'other' in trans:
                    result = trans['other']
            else:
                # Try language without region
                lang = locale.split('_')[0]
                if lang in self._translations and key in self._translations[lang]:
                    trans = self._translations[lang][key]
                    if isinstance(trans, dict) and plural_form in trans:
                        result = trans[plural_form]
                    elif isinstance(trans, dict) and 'other' in trans:
                        result = trans['other']
                else:
                    # Try source locale as fallback
                    if self._source_locale in self._translations and key in self._translations[self._source_locale]:
                        trans = self._translations[self._source_locale][key]
                        source_plural_form = get_plural_form(self._source_locale, n)
                        if isinstance(trans, dict) and source_plural_form in trans:
                            result = trans[source_plural_form]
                        elif isinstance(trans, dict) and 'other' in trans:
                            result = trans['other']

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
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_album_metadata_processor(wrapped, priority)

    def register_track_metadata_processor(
        self, function: Callable[['PluginApi', Track, Metadata, dict, dict | None], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_track_metadata_processor(wrapped, priority)

    # Event hooks
    def register_album_post_removal_processor(
        self, function: Callable[['PluginApi', Album], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_album_post_removal_processor(wrapped, priority)

    def register_file_post_load_processor(
        self, function: Callable[['PluginApi', File], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_load_processor(wrapped, priority)

    def register_file_post_addition_to_track_processor(
        self, function: Callable[['PluginApi', Track, File], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_addition_to_track_processor(wrapped, priority)

    def register_file_post_removal_from_track_processor(
        self, function: Callable[['PluginApi', Track, File], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_removal_from_track_processor(wrapped, priority)

    def register_file_post_save_processor(
        self, function: Callable[['PluginApi', File], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_save_processor(wrapped, priority)

    def register_file_pre_save_processor(
        self, function: Callable[['PluginApi', File], None], priority: int = 0
    ) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_pre_save_processor(wrapped, priority)

    # Cover art
    def register_cover_art_provider(self, provider_class: type[CoverArtProvider]) -> None:
        provider_class.api = self
        self._set_class_name_and_title(provider_class)
        if hasattr(provider_class, 'OPTIONS') and provider_class.OPTIONS:
            provider_class.OPTIONS.api = self
        return register_cover_art_provider(provider_class)

    def register_cover_art_filter(
        self, filter: Callable[['PluginApi', bytes, ImageInfo, Album | None, CoverArtImage], bool]
    ) -> None:
        wrapped = partial(filter, self)
        update_wrapper(wrapped, filter)
        return register_cover_art_filter(wrapped)

    def register_cover_art_metadata_filter(self, filter: Callable[['PluginApi', dict], bool]) -> None:
        wrapped = partial(filter, self)
        update_wrapper(wrapped, filter)
        return register_cover_art_metadata_filter(wrapped)

    def register_cover_art_processor(self, processor_class: type[ImageProcessor]) -> None:
        processor_class.api = self
        return register_cover_art_processor(processor_class)

    # File formats
    def register_format(self, format: type[File]) -> None:
        return self._tagger.format_registry.register(format)

    # Scripting
    def register_script_function(
        self,
        function: Callable,
        name: str | None = None,
        eval_args: bool = True,
        check_argcount: bool = True,
        documentation: str | None = None,
    ) -> None:
        return register_script_function(function, name, eval_args, check_argcount, documentation)

    def register_script_variable(self, name: str, documentation: str | None = None) -> None:
        return register_script_variable(name, documentation, self)

    # Menu actions
    def register_album_action(self, action: type[BaseAction]) -> None:
        action.api = self
        return register_album_action(action)

    def register_cluster_action(self, action: type[BaseAction]) -> None:
        action.api = self
        return register_cluster_action(action)

    def register_clusterlist_action(self, action: type[BaseAction]) -> None:
        action.api = self
        return register_clusterlist_action(action)

    def register_track_action(self, action: type[BaseAction]) -> None:
        action.api = self
        return register_track_action(action)

    def register_file_action(self, action: type[BaseAction]) -> None:
        action.api = self
        return register_file_action(action)

    def register_tools_menu_action(self, action: type[BaseAction]) -> None:
        action.api = self
        return register_tools_menu_action(action)

    # UI
    def register_options_page(self, page_class: type[OptionsPage]) -> None:
        page_class.api = self
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
    ) -> None:
        """Add a plugin task to an album.

        Plugin tasks are always non-blocking (TaskType.PLUGIN) and will not
        prevent the album from being marked as loaded. This allows plugins to fetch
        additional data asynchronously without blocking the user interface.

        Args:
            album: The Album object to add the task to
            task_id: Unique identifier for this task (will be prefixed with plugin_id)
            description: Human-readable description of what the task does
            timeout: Optional timeout in seconds
            request_factory: Optional callable that creates and returns a PendingRequest.
                           If provided, the request is created and registered atomically.

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
        full_task_id = f'{self.plugin_id}_{task_id}'
        album.add_task(
            full_task_id,
            TaskType.PLUGIN,
            f'[{self.plugin_id}] {description}',
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

        return self._manifest.version or "Unknown"

    def _set_class_name_and_title(self, cls: type[HasDisplayTitle]):
        if not hasattr(cls, 'NAME') or not cls.NAME:
            cls.NAME = f'{self.plugin_id}.{cls.__name__}'
        if not hasattr(cls, 'TITLE') or not cls.TITLE:
            cls.TITLE = self.manifest.name_i18n()
