# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""Configuration dataclass for plugin project scaffolding."""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from picard.plugin3.constants import DEFAULT_SOURCE_LOCALE


@dataclass
class PluginProjectConfig:
    """Configuration describing a plugin project to scaffold.

    Groups all plugin metadata fields that flow through write_plugin_project,
    generate_manifest, and _create_plugin_project.
    """

    name: str
    description: str = ''
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    license_id: str = ''
    license_url: str = ''
    long_description: str = ''
    report_bugs_to: str = ''
    with_i18n: bool = False
    source_locale: str = DEFAULT_SOURCE_LOCALE
    init_py_content: str = ''
    locale_toml_content: str = ''
