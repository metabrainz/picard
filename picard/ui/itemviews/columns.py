# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2007 Robert Kaye
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2011, 2014-2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011 Tim Blechmann
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Your Name
# Copyright (C) 2012-2013 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2024 Laurent Monin
# Copyright (C) 2013-2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2023 certuna
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Suryansh Shakya
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


from picard.i18n import N_
from picard.util import icontheme

from picard.ui.columns import (
    Column,
    ColumnAlign,
    Columns,
    ColumnSortType,
    DefaultColumn,
    IconColumn,
)


def _sortkey_length(obj):
    return obj.metadata.length or 0


def _sortkey_filesize(obj):
    try:
        return int(obj.metadata['~filesize'] or obj.orig_metadata['~filesize'])
    except ValueError:
        return 0


_fingerprint_column = IconColumn(N_("Fingerprint status"), '~fingerprint')
_fingerprint_column.header_icon_func = lambda: icontheme.lookup('fingerprint-gray', icontheme.ICON_SIZE_MENU)
_fingerprint_column.set_header_icon_size(16, 16, 1)


DEFAULT_COLUMNS = Columns((
    DefaultColumn(N_("Title"), 'title', sort_type=ColumnSortType.NAT, size=250),
    DefaultColumn(N_("Length"), '~length', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.SORTKEY, sortkey=_sortkey_length, size=50),
    DefaultColumn(N_("Artist"), 'artist', size=200),
    Column(N_("Album Artist"), 'albumartist'),
    Column(N_("Composer"), 'composer'),
    Column(N_("Album"), 'album', sort_type=ColumnSortType.NAT),
    Column(N_("Disc Subtitle"), 'discsubtitle', sort_type=ColumnSortType.NAT),
    Column(N_("Track No."), 'tracknumber', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.NAT),
    Column(N_("Disc No."), 'discnumber', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.NAT),
    Column(N_("Catalog No."), 'catalognumber', sort_type=ColumnSortType.NAT),
    Column(N_("Barcode"), 'barcode'),
    Column(N_("Media"), 'media'),
    Column(N_("Size"), '~filesize', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.SORTKEY, sortkey=_sortkey_filesize),
    Column(N_("Genre"), 'genre'),
    _fingerprint_column,
    Column(N_("Date"), 'date'),
    Column(N_("Original Release Date"), 'originaldate'),
    Column(N_("Release Date"), 'releasedate'),
    Column(N_("Cover"), 'covercount'),
    Column(N_("Cover Dimensions"), 'coverdimensions')
))


ITEM_ICON_COLUMN = DEFAULT_COLUMNS.pos('title')
