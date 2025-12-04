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
from typing import (
    Callable,
    Type,
)

from picard.album import Album
from picard.cluster import Cluster
from picard.config import (
    Config,
    ConfigSection,
    get_config,
)
from picard.coverart.image import CoverArtImage
from picard.coverart.providers import CoverArtProvider
from picard.extension_points.cover_art_filters import (
    register_cover_art_filter,
    register_cover_art_metadata_filter,
)
from picard.extension_points.cover_art_processors import (
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
)
from picard.extension_points.formats import register_format
from picard.extension_points.item_actions import (
    BaseAction,
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
from picard.extension_points.script_functions import register_script_function
from picard.extension_points.script_variables import register_script_variable
from picard.extension_points.ui_init import register_ui_init
from picard.file import File
from picard.metadata import Metadata
from picard.plugin3.i18n import (
    PluginTranslator,
    get_plural_form,
)
from picard.plugin3.manifest import PluginManifest
from picard.track import Track
from picard.webservice import WebService
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.options import OptionsPage


# Classes that plugins can import directly for inheritance
__all__ = [
    'PluginApi',
    'BaseAction',
    'OptionsPage',
    'File',
    'CoverArtProvider',
]


class PluginApi:
    # Class references for plugins to use
    Album = Album
    Track = Track
    File = File
    Cluster = Cluster
    Metadata = Metadata
    CoverArtImage = CoverArtImage
    CoverArtProvider = CoverArtProvider
    BaseAction = BaseAction
    OptionsPage = OptionsPage

    def __init__(self, manifest: PluginManifest, tagger) -> None:
        from picard.tagger import Tagger

        self._tagger: Tagger = tagger
        self._manifest = manifest
        full_name = f'plugin.{self._manifest.module_name}'
        self._logger = getLogger(f'main.{full_name}')
        self._api_config = ConfigSection(get_config(), full_name)
        self._translations = {}
        self._source_locale = manifest.source_locale
        self._plugin_dir = None
        self._qt_translator = None

    def _install_qt_translator(self) -> None:
        """Install Qt translator for .ui file translations."""
        from PyQt6.QtCore import QCoreApplication

        if not self._translations:
            return

        self._qt_translator = PluginTranslator(self._translations, self._source_locale)
        self._qt_translator._current_locale = self.get_locale()
        QCoreApplication.installTranslator(self._qt_translator)

    def _load_translations(self) -> None:
        """Load translation files from locale/ directory."""
        if not self._plugin_dir:
            return

        locale_dir = Path(self._plugin_dir) / 'locale'
        if not locale_dir.exists():
            return

        for json_file in locale_dir.glob('*.json'):
            locale = json_file.stem
            try:
                with open(json_file, encoding='utf-8') as f:
                    self._translations[locale] = json.load(f)
            except Exception as e:
                self._logger.warning(f"Failed to load translation file {json_file}: {e}")

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
    def global_config(self) -> Config:
        return get_config()

    @property
    def plugin_config(self) -> ConfigSection:
        """Configuration private to the plugin"""
        return self._api_config

    def get_locale(self) -> str:
        """Get the current locale used by Picard.

        Returns:
            str: Current locale code (e.g., 'en', 'de_DE', 'pt_BR')
        """
        from PyQt6.QtCore import QLocale

        return QLocale().name()

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

        # Fall back to text parameter or key
        if result is None:
            result = text if text is not None else key

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
            **kwargs: Placeholder values for string formatting (should include n)

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
    def register_album_metadata_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_album_metadata_processor(wrapped, priority)

    def register_track_metadata_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_track_metadata_processor(wrapped, priority)

    # Event hooks
    def register_album_post_removal_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_album_post_removal_processor(wrapped, priority)

    def register_file_post_load_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_load_processor(wrapped, priority)

    def register_file_post_addition_to_track_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_addition_to_track_processor(wrapped, priority)

    def register_file_post_removal_from_track_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_removal_from_track_processor(wrapped, priority)

    def register_file_post_save_processor(self, function: Callable, priority: int = 0) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_file_post_save_processor(wrapped, priority)

    # Cover art
    def register_cover_art_provider(self, provider: CoverArtProvider) -> None:
        return register_cover_art_provider(provider)

    def register_cover_art_filter(self, filter: Callable) -> None:
        wrapped = partial(filter, self)
        update_wrapper(wrapped, filter)
        return register_cover_art_filter(wrapped)

    def register_cover_art_metadata_filter(self, filter: Callable) -> None:
        wrapped = partial(filter, self)
        update_wrapper(wrapped, filter)
        return register_cover_art_metadata_filter(wrapped)

    def register_cover_art_processor(self, processor_class: Type) -> None:
        return register_cover_art_processor(processor_class)

    # File formats
    def register_format(self, format: File) -> None:
        return register_format(format)

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
        return register_script_variable(name, documentation)

    # Context menu actions
    def register_album_action(self, action: BaseAction) -> None:
        return register_album_action(action, self)

    def register_cluster_action(self, action: BaseAction) -> None:
        return register_cluster_action(action, self)

    def register_clusterlist_action(self, action: BaseAction) -> None:
        return register_clusterlist_action(action, self)

    def register_track_action(self, action: BaseAction) -> None:
        return register_track_action(action, self)

    def register_file_action(self, action: BaseAction) -> None:
        return register_file_action(action, self)

    # UI
    def register_options_page(self, page_class: Type[OptionsPage]) -> None:
        return register_options_page(page_class, self)

    def register_ui_init(self, function: Callable) -> None:
        wrapped = partial(function, self)
        update_wrapper(wrapped, function)
        return register_ui_init(wrapped)

    # Other ideas
    # Implement status indicators as an extension point. This allows plugins
    # that use alternative progress displays
    # def register_status_indicator(self, function: Callable) -> None:
    #     pass

    # Register page for file properties. Same for track and album
    # def register_file_info_page(self, page_class):
    #     pass
