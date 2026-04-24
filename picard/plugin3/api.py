# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Picard Team
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Public Plugin API for Picard plugins v3.

Import plugin-facing classes and helpers from this module only:

    from picard.plugin3.api import PluginApi, Metadata

This module is the supported import surface for plugin authors. Names listed in
``__all__`` are part of the public API contract for plugins. Imports from
internal modules (for example ``picard.plugin3.api_impl``) are implementation
details and may change without notice.

Exported names:
- Core API: ``PluginApi``
- Data models: ``Album``, ``Track``, ``File``, ``Metadata``, ``Cluster``
- Actions and options: ``BaseAction``, ``OptionsPage``
- Cover art: ``CoverArtProvider``, ``CoverArtImage``, ``ImageProcessor``,
  ``ImageInfo``, ``ProcessingImage``, ``ProviderOptions``
- Utilities: ``ScriptParser``, ``t_``
"""

from picard.cluster import Cluster
from picard.extension_points.cover_art_processors import ProcessingImage
from picard.plugin3.api_impl import (
    Album,
    BaseAction,
    CoverArtImage,
    CoverArtProvider,
    File,
    ImageInfo,
    ImageProcessor,
    Metadata,
    OptionsPage,
    PluginApi,
    ProviderOptions,
    Track,
    t_,
)
from picard.script import ScriptParser


__all__ = [
    'Album',
    'BaseAction',
    'Cluster',
    'CoverArtImage',
    'CoverArtProvider',
    'File',
    'ImageInfo',
    'ImageProcessor',
    'Metadata',
    'OptionsPage',
    'PluginApi',
    'ProcessingImage',
    'ProviderOptions',
    'ScriptParser',
    'Track',
    't_',
]
