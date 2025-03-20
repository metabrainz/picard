# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2009, 2018-2023, 2025 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013-2014, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
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

from html import escape

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.mbjson import (
    artist_credit_from_node,
    label_info_from_node,
    media_formats_from_node,
    release_dates_and_countries_from_node,
)
from picard.util import (
    compare_barcodes,
    restore_method,
)

from picard.ui import PicardDialog
from picard.ui.columns import (
    Column,
    Columns,
)
from picard.ui.formattedtextdelegate import FormattedTextDelegate
from picard.ui.forms.ui_cdlookup import Ui_CDLookupDialog


_COLUMNS = Columns((
    Column(N_("Album"), 'album'),
    Column(N_("Artist"), 'artist'),
    Column(N_("Date"), 'dates'),
    Column(N_("Country"), 'countries'),
    Column(N_("Labels"), 'labels'),
    Column(N_("Catalog #s"), 'catnos'),
    Column(N_("Barcode"), 'barcode'),
    Column(N_("Format"), 'format'),
    Column(N_("Disambiguation"), 'disambiguation'),
))

_DATA_COLUMN = _COLUMNS.pos('album')
_FORMAT_COLUMN = _COLUMNS.pos('format')


class CDLookupDialog(PicardDialog):

    dialog_header_state = 'cdlookupdialog_header_state'

    def __init__(self, releases, disc, parent=None):
        super().__init__(parent=parent)
        self.releases = releases
        self.disc = disc
        self.ui = Ui_CDLookupDialog()
        self.ui.setupUi(self)
        release_list = self.ui.release_list
        release_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        release_list.setSortingEnabled(True)
        release_list.setAlternatingRowColors(True)
        labels = [_(c.title) for c in _COLUMNS]
        release_list.setHeaderLabels(labels)
        delegate = FormattedTextDelegate(release_list)
        release_list.setItemDelegateForColumn(_FORMAT_COLUMN, delegate)
        self.ui.submit_button.setIcon(QtGui.QIcon(":/images/cdrom.png"))
        if self.releases:
            def myjoin(values):
                return "\n".join(values)

            self.ui.results_view.setCurrentIndex(0)
            selected = None
            for release in self.releases:
                labels, catalog_numbers = label_info_from_node(release['label-info'])
                dates, countries = release_dates_and_countries_from_node(release)
                barcode = release.get('barcode', '')
                item = QtWidgets.QTreeWidgetItem(release_list)
                if disc.mcn and compare_barcodes(barcode, disc.mcn):
                    selected = item
                values = {
                    'album': release['title'],
                    'artist': artist_credit_from_node(release['artist-credit'])[0],
                    'dates': myjoin(dates),
                    'countries': myjoin(countries),
                    'labels': myjoin(labels),
                    'catnos': myjoin(catalog_numbers),
                    'barcode': barcode,
                    'format': self._get_format(release),
                    'disambiguation': release.get('disambiguation', ''),
                }
                for i, column in enumerate(_COLUMNS):
                    item.setText(i, values.get(column.key, ""))
                item.setData(_DATA_COLUMN, QtCore.Qt.ItemDataRole.UserRole, release['id'])
            release_list.setCurrentItem(selected or release_list.topLevelItem(0))
            self.ui.ok_button.setEnabled(True)
            for i in range(release_list.columnCount() - 1):
                release_list.resizeColumnToContents(i)
            # Sort by descending date, then ascending country
            release_list.sortByColumn(_COLUMNS.pos('countries'), QtCore.Qt.SortOrder.AscendingOrder)
            release_list.sortByColumn(_COLUMNS.pos('dates'), QtCore.Qt.SortOrder.DescendingOrder)
        else:
            self.ui.results_view.setCurrentIndex(1)
        if self.disc.submission_url:
            self.ui.lookup_button.clicked.connect(self.lookup)
            self.ui.submit_button.clicked.connect(self.lookup)
        else:
            self.ui.lookup_button.hide()
            self.ui.submit_button.hide()
        self.restore_header_state()
        self.finished.connect(self.save_header_state)

    def accept(self):
        release_list = self.ui.release_list
        for index in release_list.selectionModel().selectedRows():
            release_id = release_list.itemFromIndex(index).data(_DATA_COLUMN, QtCore.Qt.ItemDataRole.UserRole)
            self.tagger.load_album(release_id, discid=self.disc.id)
        super().accept()

    def lookup(self):
        submission_url = self.disc.submission_url
        if submission_url:
            lookup = self.tagger.get_file_lookup()
            lookup.discid_submission(submission_url)
        else:
            log.error("No submission URL for disc ID %s", self.disc.id)
        super().accept()

    @restore_method
    def restore_header_state(self):
        if self.ui.release_list:
            header = self.ui.release_list.header()
            config = get_config()
            state = config.persist[self.dialog_header_state]
            if state:
                header.restoreState(state)
                log.debug("restore_state: %s", self.dialog_header_state)

    def save_header_state(self):
        if self.ui.release_list:
            state = self.ui.release_list.header().saveState()
            config = get_config()
            config.persist[self.dialog_header_state] = state
            log.debug("save_state: %s", self.dialog_header_state)

    def _get_format(self, release):
        format = escape(media_formats_from_node(release.get('media', [])))
        selected_medium = self._get_selected_medium(release)
        if selected_medium:
            selected_format = escape(selected_medium.get('format', format))
            format = format.replace(selected_format, f"<b>{selected_format}</b>")
        return format

    def _get_selected_medium(self, release):
        for medium in release.get('media', []):
            if any(disc.get('id') == self.disc.id for disc in medium.get('discs', [])):
                return medium
