# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009, 2018-2021, 2023, 2025-2026 Philipp Wolfer
# Copyright (C) 2011 Johannes Weißl
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013-2014, 2019-2021, 2023-2026 Laurent Monin
# Copyright (C) 2013-2015, 2017 Sophist-UK
# Copyright (C) 2019 Zenara Daley
# Copyright (C) 2023 certuna
# Copyright (C) 2023, 2025 Bob Swift
# Copyright (C) 2024 Arnab Chakraborty
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Serial
# Copyright (C) 2025 Khoa Nguyen
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


from collections.abc import Iterator
import re

from picard.const.tags import ALL_TAGS
from picard.tags.tagvar import TagVar


RE_COMMENT_LANG = re.compile('^([a-zA-Z]{3}):')


def parse_comment_tag(name):
    """
    Parses a tag name like "comment:XXX:desc", where XXX is the language.
    If language is not set ("comment:desc") "eng" is assumed as default.
    Returns a (lang, desc) tuple.
    """
    lang = 'eng'
    desc = ''

    split = name.split(':', 1)
    if len(split) > 1:
        desc = split[1]

    match_ = RE_COMMENT_LANG.match(desc)
    if match_:
        lang = match_.group(1)
        desc = desc[4:]
        return lang, desc

    # Special case for unspecified language + empty description
    if desc == 'XXX':
        lang = 'XXX'
        desc = ''

    return lang, desc


def parse_subtag(name):
    """
    Parses a tag name like "lyrics:XXX:desc", where XXX is the language.
    If language is not set, the colons are still mandatory, and "eng" is
    assumed by default.
    """
    split = name.split(':')
    if len(split) > 1 and split[1]:
        lang = split[1]
    else:
        lang = 'eng'

    if len(split) > 2:
        desc = split[2]
    else:
        desc = ''

    return lang, desc


def all_tag_vars() -> Iterator[TagVar]:
    # Inline import to avoid circular dependency: script_variables imports from this module.
    from picard.extension_points.script_variables import ext_point_script_variables

    yield from ALL_TAGS
    yield from ext_point_script_variables


def tag_names():
    """Tag names available for user assignment: built-in tags + plugin-provided tags."""
    yield from (var.name for var in all_tag_vars() if var.is_tag and not var.is_hidden)


def filterable_tag_names():
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_filterable)


def preserved_tag_names():
    """Tags that should be preserved by default"""
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_preserved)


def calculated_tag_names():
    """
    Tags that got generated in some way from the audio content.
    Those can be set by Picard but the new values usually should be kept
    when moving the file between tags.
    """
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_calculated)


def file_info_tag_names():
    """Tags that contains infos related to files"""
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_file_info)


def script_variable_tag_names():
    """Tag names available to scripts (used by script editor completer)"""
    yield from (var.script_name() for var in all_tag_vars() if var.is_script_variable)


def display_tag_name(name):
    display = ALL_TAGS.display_name(name)
    # If ALL_TAGS didn't have a shortdesc (returns raw name), check plugin variables
    if display == name:
        from picard.extension_points.script_variables import get_plugin_variable_title

        title = get_plugin_variable_title(name)
        if title:
            return title
    return display
