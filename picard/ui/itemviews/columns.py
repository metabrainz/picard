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

from PyQt6 import QtCore

from picard.i18n import N_
from picard.util import icontheme

from picard.ui.columns import (
    Column,
    ColumnAlign,
    Columns,
    ColumnSortType,
)
from picard.ui.itemviews.custom_columns import (
    make_delegate_column,
    make_field_column,
    make_numeric_field_column,
)
from picard.ui.itemviews.custom_columns.factory import make_icon_header_column
from picard.ui.itemviews.custom_columns.providers import LazyHeaderIconProvider
from picard.ui.itemviews.custom_columns.sorting_adapters import NumericSortAdapter
from picard.ui.itemviews.custom_columns.utils import (
    parse_bitrate,
    parse_file_size,
    parse_time_format,
)
from picard.ui.itemviews.match_quality_column import MatchQualityProvider


def create_match_quality_column():
    """Create a match quality delegate column with proper sorting.

    Returns
    -------
    DelegateColumn
        The configured match quality column.
    """
    base_provider = MatchQualityProvider()
    sorter = NumericSortAdapter(base_provider)
    column = make_delegate_column(
        N_("Match"),
        '~match_quality',
        base_provider,
        width=57,
        sort_type=ColumnSortType.SORTKEY,
        size=QtCore.QSize(16, 16),
        sort_provider=sorter,
    )
    column.is_default = True
    return column


def create_fingerprint_status_column():
    """Create the fingerprint status icon header column.

    Returns
    -------
    IconColumn
        The configured fingerprint status column.
    """
    provider = LazyHeaderIconProvider(lambda: icontheme.lookup('fingerprint-gray', icontheme.ICON_SIZE_MENU))
    column = make_icon_header_column(
        N_("Fingerprint status"),
        '~fingerprint',
        provider,
        icon_width=16,
        icon_height=16,
        border=1,
    )
    return column


def create_common_columns() -> tuple[Column, ...]:
    """Create the built-in common columns using factories.

    Returns
    -------
    tuple
        Tuple of configured column objects for both views.
    """
    # Title (status icon column)
    title_col = make_field_column(
        N_("Title"),
        'title',
        sort_type=ColumnSortType.NAT,
        width=250,
        always_visible=True,
        status_icon=True,
        is_default=True,
    )

    # Length with numeric sort key from metadata.length
    length_col = make_numeric_field_column(
        N_("Length"),
        '~length',
        parse_time_format,
        width=50,
        align=ColumnAlign.RIGHT,
        is_default=True,
    )

    # Artist
    artist_col = make_field_column(N_("Artist"), 'artist', width=200, is_default=True)

    # Others (mostly field columns)
    album_artist = make_field_column(N_("Album Artist"), 'albumartist')
    composer = make_field_column(N_("Composer"), 'composer')
    album = make_field_column(N_("Album"), 'album', sort_type=ColumnSortType.NAT)
    discsubtitle = make_field_column(N_("Disc Subtitle"), 'discsubtitle', sort_type=ColumnSortType.NAT)
    trackno = make_field_column(N_("Track No."), 'tracknumber', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.NAT)
    discno = make_field_column(N_("Disc No."), 'discnumber', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.NAT)
    catalognumber = make_field_column(N_("Catalog No."), 'catalognumber', sort_type=ColumnSortType.NAT)
    barcode = make_field_column(N_("Barcode"), 'barcode')
    media = make_field_column(N_("Media"), 'media')

    # Size with numeric sort key
    size_col = make_numeric_field_column(
        N_("Size"),
        '~filesize',
        parse_file_size,
        align=ColumnAlign.RIGHT,
    )

    # File Type
    filetype = make_field_column(N_("File Type"), '~format', width=120)

    # Bitrate
    bitrate = make_numeric_field_column(
        N_("Bitrate"),
        '~bitrate',
        parse_bitrate,
        width=80,
        align=ColumnAlign.RIGHT,
    )

    genre = make_field_column(N_("Genre"), 'genre')

    fingerprint = create_fingerprint_status_column()

    date = make_field_column(N_("Date"), 'date')
    originaldate = make_field_column(N_("Original Release Date"), 'originaldate')
    releasedate = make_field_column(N_("Release Date"), 'releasedate')
    cover = make_field_column(N_("Cover"), 'covercount')
    coverdims = make_field_column(N_("Cover Dimensions"), 'coverdimensions')

    return (
        title_col,
        length_col,
        artist_col,
        album_artist,
        composer,
        album,
        discsubtitle,
        trackno,
        discno,
        catalognumber,
        barcode,
        media,
        size_col,
        filetype,
        bitrate,
        genre,
        fingerprint,
        date,
        originaldate,
        releasedate,
        cover,
        coverdims,
    )


# Common columns used by both views
_common_columns = create_common_columns()

# File view columns (without match quality column)
FILEVIEW_COLUMNS = Columns(_common_columns, default_width=100)

# Album view columns (with match quality column)
# Insert `_match_quality_column` after Title, Length, Artist, Album Artist
ALBUMVIEW_COLUMNS = Columns(_common_columns, default_width=100)
_match_quality_column = create_match_quality_column()
ALBUMVIEW_COLUMNS.insert(ALBUMVIEW_COLUMNS.pos('albumartist') + 1, _match_quality_column)
