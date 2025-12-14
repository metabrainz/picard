# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
# Copyright (C) 2025 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from picard.const.tags import ALL_TAGS
from picard.extension_points.script_variables import get_plugin_variable_documentation
from picard.i18n import gettext as _
from picard.tags.tagvar import (
    TEXT_NO_DESCRIPTION,
    _markdown,
)


def display_tag_tooltip(tagname):
    name, tagdesc, _search_name, item = ALL_TAGS.item_from_name(tagname)
    content = ALL_TAGS.tooltip_content(item) if item else None
    return _finalize_content(name, content, tagdesc)


def display_tag_full_description(tagname):
    name, tagdesc, _search_name, item = ALL_TAGS.item_from_name(tagname)
    content = ALL_TAGS.full_description_content(item) if item else None
    return _finalize_content(name, content, tagdesc)


def _finalize_content(name, content, tagdesc):
    if not content:
        content = _markdown(get_plugin_variable_documentation(name) or _(TEXT_NO_DESCRIPTION))
    return _format_display(name, content, tagdesc)


def _format_display(name, content, tagdesc):
    fmt_tagdesc = _("<p><em>%{name}%</em> [{tagdesc}]</p>{content}")
    fmt_normal = _("<p><em>%{name}%</em></p>{content}")
    fmt = fmt_tagdesc if tagdesc else fmt_normal
    return fmt.format(name=name, content=content, tagdesc=tagdesc)
