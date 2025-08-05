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

from picard.album import AlbumStatus
from picard.i18n import N_
from picard.util import icontheme

from picard.ui.columns import (
    Column,
    ColumnAlign,
    Columns,
    ColumnSortType,
    DefaultColumn,
    ImageColumn,
)
from picard.ui.itemviews.match_quality_column import MatchQualityColumn


def _sortkey_length(obj):
    return obj.metadata.length or 0


def _sortkey_filesize(obj):
    try:
        return int(obj.metadata['~filesize'] or obj.orig_metadata['~filesize'])
    except ValueError:
        return 0


def _sortkey_bitrate(obj):
    try:
        return float(obj.metadata['~bitrate'] or obj.orig_metadata['~bitrate'] or 0)
    except (ValueError, TypeError):
        return 0


def _sortkey_match_quality(obj):
    """Sort key for match quality column - sort by completion percentage."""
    if hasattr(obj, 'get_num_matched_tracks') and hasattr(obj, 'tracks'):
        # Album object
        # Check if album is still loading - if so, return 0 to avoid premature sorting
        if hasattr(obj, 'status') and obj.status == AlbumStatus.LOADING:
            return 0.0

        matched = obj.get_num_matched_tracks()
        total = len(obj.tracks) if obj.tracks else 0
        if total > 0:
            return matched / total
        return 0.0
    # For track objects, return 0 since we don't show icons at track level
    return 0.0


class IconColumn(ImageColumn):
    _header_icon = None
    header_icon_func = None
    header_icon_size = QtCore.QSize(0, 0)
    header_icon_border = 0

    @property
    def header_icon(self):
        # icon cannot be set before QApplication is created
        # so create it during runtime and cache it
        # Avoid error: QPixmap: Must construct a QGuiApplication before a QPixmap
        if self._header_icon is None:
            self._header_icon = self.header_icon_func()
        return self._header_icon

    def set_header_icon_size(self, width, height, border):
        self.header_icon_size = QtCore.QSize(width, height)
        self.header_icon_border = border
        self.size = QtCore.QSize(width + 2 * border, height + 2 * border)
        self.width = self.size.width()

    def paint(self, painter, rect):
        icon = self.header_icon
        if not icon:
            return
        h = self.header_icon_size.height()
        w = self.header_icon_size.width()
        border = self.header_icon_border
        padding_v = (rect.height() - h) // 2
        target_rect = QtCore.QRect(rect.x() + border, rect.y() + padding_v, w, h)
        painter.drawPixmap(target_rect, icon.pixmap(self.header_icon_size))


_fingerprint_column = IconColumn(N_("Fingerprint status"), '~fingerprint')
_fingerprint_column.header_icon_func = lambda: icontheme.lookup('fingerprint-gray', icontheme.ICON_SIZE_MENU)
_fingerprint_column.set_header_icon_size(16, 16, 1)

_match_quality_column = MatchQualityColumn(N_("Match"), '~match_quality', width=57)
_match_quality_column.sortable = True
_match_quality_column.sort_type = ColumnSortType.SORTKEY
_match_quality_column.sortkey = _sortkey_match_quality
_match_quality_column.always_visible = True


ITEMVIEW_COLUMNS = Columns(
    (
        _match_quality_column,
        DefaultColumn(
            N_("Title"), 'title', sort_type=ColumnSortType.NAT, width=250, always_visible=True, status_icon=True
        ),
        DefaultColumn(
            N_("Length"),
            '~length',
            align=ColumnAlign.RIGHT,
            sort_type=ColumnSortType.SORTKEY,
            sortkey=_sortkey_length,
            width=50,
        ),
        DefaultColumn(N_("Artist"), 'artist', width=200),
        Column(N_("Album Artist"), 'albumartist'),
        Column(N_("Composer"), 'composer'),
        Column(N_("Album"), 'album', sort_type=ColumnSortType.NAT),
        Column(N_("Disc Subtitle"), 'discsubtitle', sort_type=ColumnSortType.NAT),
        Column(N_("Track No."), 'tracknumber', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.NAT),
        Column(N_("Disc No."), 'discnumber', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.NAT),
        Column(N_("Catalog No."), 'catalognumber', sort_type=ColumnSortType.NAT),
        Column(N_("Barcode"), 'barcode'),
        Column(N_("Media"), 'media'),
        Column(
            N_("Size"),
            '~filesize',
            align=ColumnAlign.RIGHT,
            sort_type=ColumnSortType.SORTKEY,
            sortkey=_sortkey_filesize,
        ),
        Column(N_("File Type"), '~format', width=120),
        Column(
            N_("Bitrate"),
            '~bitrate',
            align=ColumnAlign.RIGHT,
            sort_type=ColumnSortType.SORTKEY,
            sortkey=_sortkey_bitrate,
            width=80,
        ),
        Column(N_("Genre"), 'genre'),
        _fingerprint_column,
        Column(N_("Date"), 'date'),
        Column(N_("Original Release Date"), 'originaldate'),
        Column(N_("Release Date"), 'releasedate'),
        Column(N_("Cover"), 'covercount'),
        Column(N_("Cover Dimensions"), 'coverdimensions'),
    ),
    default_width=100,
)
