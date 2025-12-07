# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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

from picard.const.tags import ALL_PLUGIN_TAGS
from picard.tags.tagvar import TagVar


class PluginTags:
    _plugin_tags = {}
    """Dictionary of sets containing the tags for a plugin by plugin id.
    """

    @classmethod
    def add_tag(cls, plugin_id: str, tag: TagVar) -> None:
        """Add a tag or variable to a plugin for autocompletion.

        Args:
            plugin_id (str): ID of the plugin.
            tag (TagVar): Tag or variable name to add.
        """
        if plugin_id not in cls._plugin_tags:
            cls._plugin_tags[plugin_id] = set()
        tags: set = cls._plugin_tags[plugin_id]
        tags.add(f"~{tag.name}" if tag.is_hidden else tag.name)
        cls._plugin_tags[plugin_id] = tags
        ALL_PLUGIN_TAGS.append(tag)

    @classmethod
    def remove_plugin_tags(cls, plugin: str) -> None:
        """De-register a plugin and remove all of its related tags and variables from the scripting
        autocompletion.

        Args:
            plugin (str): ID of the plugin to de-register.
        """
        tags: set = cls._plugin_tags.pop(plugin.strip(), None)
        if tags:
            for tag in list(tags):
                ALL_PLUGIN_TAGS.delete_by_name(tag)
