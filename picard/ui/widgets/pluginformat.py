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

import html
import time

from picard.const.defaults import DEFAULT_TIME_FORMAT
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.plugin3.ref_item import RefItem


_CURRENT_LABEL = N_("current")
_COMMIT_DATE_LABEL = N_("Commit date: {date}")


def format_commit_date(timestamp: int) -> str:
    """Format a unix timestamp for display."""
    return time.strftime(DEFAULT_TIME_FORMAT, time.localtime(timestamp))


def commit_date_display(timestamp: int) -> str:
    """Format a commit date timestamp as a translatable display string."""
    return _(_COMMIT_DATE_LABEL).format(date=format_commit_date(timestamp))


def html_ref_format(ref_item: RefItem, **kwargs) -> str:
    """Format a RefItem as HTML with bold ref name and italic commit."""
    return ref_item.format(
        ref_formatter=lambda t: f'<b>{html.escape(t)}</b>',
        commit_formatter=lambda t: f'<i>{html.escape(t)}</i>',
        current_formatter=lambda t: f'{t} <i>({html.escape(_(_CURRENT_LABEL))})</i>',
        **kwargs,
    )
