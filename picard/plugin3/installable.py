# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

from abc import ABC, abstractmethod


class InstallablePlugin(ABC):
    """Common base class for all installable plugins."""

    def __init__(self, source_url=None, plugin_uuid=None, name=None):
        self.source_url = source_url
        self.plugin_uuid = plugin_uuid
        self.name = name
        self.trust_level = 'unregistered'
        self.categories = []
        self.description = ''

    @abstractmethod
    def get_display_name(self):
        """Get display name for this plugin."""
        pass

    @abstractmethod
    def get_install_url(self):
        """Get URL to install this plugin from."""
        pass

    def get_trust_level(self):
        """Get trust level of this plugin."""
        return self.trust_level

    def get_categories(self):
        """Get categories this plugin belongs to."""
        return self.categories

    def get_description(self):
        """Get description of this plugin."""
        return self.description
