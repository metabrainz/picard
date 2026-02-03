# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from collections import (
    OrderedDict,
    namedtuple,
)
from collections.abc import MutableSequence
from enum import IntEnum
import html


try:
    from markdown import markdown  # type: ignore[unresolved-import]
except ImportError:
    markdown = None

from picard.i18n import (
    N_,
    gettext as _,
)
from picard.options import get_option_title


DocumentLink = namedtuple('DocumentLink', ('title', 'link'))


def _markdown(text: str):
    text = html.escape(text)
    if markdown is None:
        return '<p>' + text.replace('\n', '<br />') + '</p>'
    return markdown(text)


class Section(IntEnum):
    notes = 1
    options = 2
    links = 3
    see_also = 4


SectionInfo = namedtuple('Section', ('title', 'tagvar_func'))
SECTIONS = {
    Section.notes: SectionInfo(N_('Notes'), 'notes'),
    Section.options: SectionInfo(N_('Option Settings'), 'related_options_titles'),
    Section.links: SectionInfo(N_('Links'), 'links'),
    Section.see_also: SectionInfo(N_('See Also'), 'see_alsos'),
}

TEXT_NO_DESCRIPTION = N_('No description available.')

ATTRIB2NOTE = OrderedDict(
    is_multi_value=N_('multi-value variable'),
    is_preserved=N_('preserved read-only'),
    not_script_variable=N_('not for use in scripts'),
    is_calculated=N_('calculated'),
    is_file_info=N_('info from audio file'),
    not_from_mb=N_('not provided from MusicBrainz data'),
    not_populated_by_picard=N_('not populated by stock Picard'),
)


class TagVar:
    def __init__(
        self,
        name,
        shortdesc=None,
        longdesc=None,
        additionaldesc=None,
        is_preserved=False,
        is_hidden=False,
        is_script_variable=True,
        is_tag=True,
        is_calculated=False,
        is_file_info=False,
        is_from_mb=True,
        is_populated_by_picard=True,
        is_multi_value=False,
        is_filterable=False,
        see_also=None,
        related_options=None,
        doc_links=None,
    ):
        """
        shortdesc: Short description (typically one or two words) in title case that is suitable
                   for a column header.
        longdesc: Brief description in sentence case describing the tag/variable.  This should
                  be similar (within reasonable length constraints) to the description in the Picard User
                  Guide documentation, and will be used as a tooltip when reviewing a script.  May
                  contain markdown.
        additionaldesc: Additional description which might include more details or examples.  May
                        contain markdown.
        is_preserved: the tag is preserved (boolean, default: False)
        is_hidden: the tag is "hidden", name will be prefixed with "~" (boolean, default: False)
        is_script_variable: the tag can be used as script variable (boolean, default: True)
        is_tag: the tag is an actual tag (not a calculated or derived one) (boolean, default: True)
        is_calculated: the tag is obtained by external calculation (boolean, default: False)
        is_file_info: the tag is a file information, displayed in file info box (boolean, default: False)
        is_from_mb: the tag information is provided from the MusicBrainz database (boolean, default: True)
        is_populated_by_picard: the tag information is populated by stock Picard (boolean, default: True)
        is_multi_value: the tag is a multi-value variable (boolean, default: False)
        is_filterable: the tag can be selected for filtering (boolean, default: False)
        see_also: an iterable containing ids of related tags
        related_options: an iterable containing the related option settings (see picard/options.py)
        doc_links: an iterable containing links to external documentation (DocumentLink tuples)
        """
        self.name = name
        self._shortdesc = shortdesc
        self._longdesc = longdesc
        self._additionaldesc = additionaldesc
        self.is_preserved = is_preserved
        self.is_hidden = is_hidden
        self.is_script_variable = is_script_variable
        self.is_tag = is_tag
        self.is_calculated = is_calculated
        self.is_file_info = is_file_info
        self.is_from_mb = is_from_mb
        self.is_populated_by_picard = is_populated_by_picard
        self.is_multi_value = is_multi_value
        self.is_filterable = is_filterable
        self.see_also = see_also
        self.related_options = related_options
        self.doc_links = doc_links

    @property
    def shortdesc(self):
        """default to name"""
        if self._shortdesc:
            return self._shortdesc.strip()
        return str(self)

    @property
    def longdesc(self):
        """default to shortdesc"""
        if self._longdesc:
            return self._longdesc.strip()
        return self.shortdesc

    @property
    def additionaldesc(self):
        if not self._additionaldesc:
            return ''
        return self._additionaldesc.strip()

    @property
    def not_from_mb(self):
        return not self.is_from_mb

    @property
    def not_script_variable(self):
        return not self.is_script_variable

    @property
    def not_populated_by_picard(self):
        return not self.is_populated_by_picard

    def __str__(self):
        """hidden marked with a prefix"""
        if self.is_hidden:
            return '~' + self.name
        else:
            return self.name

    def script_name(self):
        """In scripts, ~ prefix is replaced with _ for hidden variables"""
        if self.is_hidden:
            return '_' + self.name
        else:
            return self.name


TagInfo = namedtuple('TagInfo', ('name', 'tagdesc', 'search_name', 'item'))


class TagVars(MutableSequence):
    """Mutable sequence for TagVar items
    It maintains an internal dict object for display names.
    Also it doesn't allow to add a TagVar of the same name more than once.
    """

    def __init__(self, *tagvars):
        self._items = []
        self._name2item: dict[str, TagVar] = dict()
        self.extend(tagvars)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def _get_name(self, tagvar):
        if not isinstance(tagvar, TagVar):
            raise TypeError(f"Value isn't a TagVar instance: {tagvar}")
        name = str(tagvar)
        if name in self._name2item:
            raise ValueError(f"Already an item with same name: {name}")
        return name

    def __setitem__(self, index, tagvar):
        name = self._get_name(tagvar)
        self._name2item[name] = self._items[index] = tagvar

    def __delitem__(self, index):
        name = str(self._items[index])
        del self._items[index]
        del self._name2item[name]

    def insert(self, index, tagvar):
        name = self._get_name(tagvar)
        self._items.insert(index, tagvar)
        self._name2item[name] = self._items[index]

    def __repr__(self):
        return f"TagVars({self._items!r})"

    def item_from_name(self, name) -> TagInfo:
        if ':' in name:
            name, tagdesc = name.split(':', 1)
        else:
            tagdesc = None

        if name and name.startswith('_'):
            search_name = name.replace('_', '~', 1)
        elif name and name.startswith('~'):
            search_name = name
            name = name.replace('~', '_')
        else:
            search_name = name

        item = self._name2item.get(search_name, None)

        return TagInfo(name, tagdesc, search_name, item)

    def tagvar_from_name(self, name) -> TagVar | None:
        return self.item_from_name(name).item

    def script_name_from_name(self, name):
        tagname, tagdesc, search_name, item = self.item_from_name(name)
        if item:
            return str(item)
        return None

    def display_name(self, name):
        name, tagdesc, search_name, item = self.item_from_name(name)

        if item and item.shortdesc:
            title = _(item.shortdesc)
        else:
            title = search_name
        if tagdesc:
            return '%s [%s]' % (title, tagdesc)
        else:
            return title

    def notes(self, item: TagVar):
        for attrib, note in ATTRIB2NOTE.items():
            if getattr(item, attrib):
                yield html.escape(_(note))

    def related_options_titles(self, item: TagVar):
        if not item.related_options:
            return
        for setting in item.related_options:
            title = get_option_title(setting)
            if title:
                yield html.escape(_(title))

    def links(self, item: TagVar):
        if not item.doc_links:
            return
        for doclink in item.doc_links:
            translated_title = html.escape(_(doclink.title))
            yield f"<a href='{doclink.link}'>{translated_title}</a>"

    def see_alsos(self, item: TagVar):
        if not item.see_also:
            return
        for tag in item.see_also:
            if self.script_name_from_name(tag):
                yield f'<a href="#{tag}">%{tag}%</a>'

    def _base_description(self, item: TagVar):
        return _markdown(_(item.longdesc) if item.longdesc else _(TEXT_NO_DESCRIPTION))

    def _add_sections(self, item, include_sections):
        # Note: format has to be translatable, for languages not using left-to-right for example
        fmt = _("<p><strong>{title}:</strong> {values}.</p>")
        return ''.join(self._gen_sections(fmt, item, include_sections))

    def _gen_sections(self, fmt, item, include_sections):
        for section_id in include_sections:
            section = SECTIONS[section_id]
            func_for_values = getattr(self, section.tagvar_func)
            values = tuple(func_for_values(item))
            if not values:
                continue
            yield fmt.format(
                title=_(section.title),
                values='; '.join(values),
            )

    def tooltip_content(self, item: TagVar):
        content = self._base_description(item)
        content += self._add_sections(item, (Section.notes,))
        return content

    def full_description_content(self, item: TagVar):
        content = self._base_description(item)

        # Append additional description
        if item.additionaldesc:
            content += _markdown(_(item.additionaldesc))

        # Append additional sections as required
        include_sections = (
            Section.notes,
            Section.options,
            Section.links,
            Section.see_also,
        )
        content += self._add_sections(item, include_sections)

        return content

    def names(self, selector=None):
        for item in self._items:
            if selector is None or selector(item):
                yield str(item)
