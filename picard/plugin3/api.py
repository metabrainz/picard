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

from logging import (
    Logger,
    getLogger,
)
from typing import (
    Callable,
    Type,
)

from picard.config import (
    Config,
    ConfigSection,
    config,
    get_config,
)
from picard.coverart.providers import CoverArtProvider
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
from picard.file import File
from picard.plugin3.manifest import PluginManifest
from picard.webservice import WebService
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.options import OptionsPage


class PluginApi:
    def __init__(self, manifest: PluginManifest, tagger) -> None:
        from picard.tagger import Tagger

        self._tagger: Tagger = tagger
        self._manifest = manifest
        full_name = f'plugin.{self._manifest.module_name}'
        self._logger = getLogger(full_name)
        self._api_config = ConfigSection(config, full_name)

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

    # Metadata processors
    def register_album_metadata_processor(self, function: Callable, priority: int = 0) -> None:
        return register_album_metadata_processor(function, priority)

    def register_track_metadata_processor(self, function: Callable, priority: int = 0) -> None:
        return register_track_metadata_processor(function, priority)

    # Event hooks
    def register_album_post_removal_processor(self, function: Callable, priority: int = 0) -> None:
        return register_album_post_removal_processor(function, priority)

    def register_file_post_load_processor(self, function: Callable, priority: int = 0) -> None:
        return register_file_post_load_processor(function, priority)

    def register_file_post_addition_to_track_processor(self, function: Callable, priority: int = 0) -> None:
        return register_file_post_addition_to_track_processor(function, priority)

    def register_file_post_removal_from_track_processor(self, function: Callable, priority: int = 0) -> None:
        return register_file_post_removal_from_track_processor(function, priority)

    def register_file_post_save_processor(self, function: Callable, priority: int = 0) -> None:
        return register_file_post_save_processor(function, priority)

    # Cover art
    def register_cover_art_provider(self, provider: CoverArtProvider) -> None:
        return register_cover_art_provider(provider)

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

    # Context menu actions
    def register_album_action(self, action: BaseAction) -> None:
        return register_album_action(action)

    def register_cluster_action(self, action: BaseAction) -> None:
        return register_cluster_action(action)

    def register_clusterlist_action(self, action: BaseAction) -> None:
        return register_clusterlist_action(action)

    def register_track_action(self, action: BaseAction) -> None:
        return register_track_action(action)

    def register_file_action(self, action: BaseAction) -> None:
        return register_file_action(action)

    # UI
    def register_options_page(self, page_class: Type[OptionsPage]) -> None:
        return register_options_page(page_class)

    # TODO: Replace by init function in plugin
    # def register_ui_init(self, function: Callable) -> None:
    #     pass

    # Other ideas
    # Implement status indicators as an extension point. This allows plugins
    # that use alternative progress displays
    # def register_status_indicator(self, function: Callable) -> None:
    #     pass

    # Register page for file properties. Same for track and album
    # def register_file_info_page(self, page_class):
    #     pass
