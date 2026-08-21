# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
# Copyright (C) 2025-2026 Laurent Monin
# Copyright (C) 2025-2026 Philipp Wolfer
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
from picard.i18n import gettext as _
from picard.tags.tagvar import (
    TEXT_NO_DESCRIPTION,
    TagVar,
    _markdown,
)


def display_tag_tooltip(tagname):
    name, item, tagdesc = _get_tagvar_item(tagname)
    content = ALL_TAGS.tooltip_content(item) if item else None
    return _finalize_tooltip_content(name, content, tagdesc)


def display_tag_full_description(item: TagVar) -> str:
    content = ALL_TAGS.full_description_content(item) if item else None
    if not content:
        content = _markdown(_(TEXT_NO_DESCRIPTION))
    return content


def _get_tagvar_item(tagname):
    if ':' in tagname:
        tagname, tagdesc = tagname.split(':', 1)
    else:
        tagdesc = None

    # O(1) lookup for built-in tags
    item = ALL_TAGS.tagvar_from_name(tagname)

    # Linear scan for plugin variables (typically very few)
    if not item:
        # Inline import to avoid circular dependency: script_variables imports from this module.
        from picard.extension_points.script_variables import ext_point_script_variables

        bare_name = tagname[1:] if tagname[:1] in ('~', '_') else tagname
        item = next((var for var in ext_point_script_variables if var.name == bare_name), None)

    if item:
        return item.script_name(), item, tagdesc
    return tagname, None, None


def _finalize_tooltip_content(name, content, tagdesc=None):
    if not content:
        content = _markdown(_(TEXT_NO_DESCRIPTION))
    return _format_tooltip(name, content, tagdesc)


def _format_tooltip(name, content, tagdesc=None):
    fmt_tagdesc = _("<p><em>%{name}%</em> [{tagdesc}]</p>{content}")
    fmt_normal = _("<p><em>%{name}%</em></p>{content}")
    fmt = fmt_tagdesc if tagdesc else fmt_normal
    return fmt.format(name=name, content=content, tagdesc=tagdesc)
