# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import (
    config,
    log,
)
from picard.mbjson import (
    artist_credit_from_node,
    label_info_from_node,
    release_dates_and_countries_from_node,
)
from picard.util import (
    compare_barcodes,
    restore_method,
)

from picard.ui import PicardDialog
from picard.ui.ui_cdlookup import Ui_Dialog


class CDLookupDialog(PicardDialog):

    defaultsize = QtCore.QSize(720, 360)
    autorestore = False
    dialog_header_state = "cdlookupdialog_header_state"

    options = [
        config.Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, releases, disc, parent=None):
        super().__init__(parent)
        self.releases = releases
        self.disc = disc
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.release_list.setSortingEnabled(True)
        self.ui.release_list.setAlternatingRowColors(True)
        self.ui.release_list.setHeaderLabels([_("Album"), _("Artist"), _("Date"), _("Country"),
                                              _("Labels"), _("Catalog #s"), _("Barcode")])
        if self.releases:
            def myjoin(l):
                return "\n".join(l)

            selected = None
            for release in self.releases:
                labels, catalog_numbers = label_info_from_node(release['label-info'])
                dates, countries = release_dates_and_countries_from_node(release)
                barcode = release['barcode'] if "barcode" in release else ""
                item = QtWidgets.QTreeWidgetItem(self.ui.release_list)
                if disc.mcn and compare_barcodes(barcode, disc.mcn):
                    selected = item
                item.setText(0, release['title'])
                item.setText(1, artist_credit_from_node(release['artist-credit'])[0])
                item.setText(2, myjoin(dates))
                item.setText(3, myjoin(countries))
                item.setText(4, myjoin(labels))
                item.setText(5, myjoin(catalog_numbers))
                item.setText(6, barcode)
                item.setData(0, QtCore.Qt.UserRole, release['id'])
            self.ui.release_list.setCurrentItem(selected or self.ui.release_list.topLevelItem(0))
            self.ui.ok_button.setEnabled(True)
        for i in range(self.ui.release_list.columnCount() - 1):
            self.ui.release_list.resizeColumnToContents(i)
        # Sort by descending date, then ascending country
        self.ui.release_list.sortByColumn(3, QtCore.Qt.AscendingOrder)
        self.ui.release_list.sortByColumn(2, QtCore.Qt.DescendingOrder)
        self.ui.lookup_button.clicked.connect(self.lookup)
        self.restore_geometry()
        self.restore_header_state()
        self.finished.connect(self.save_header_state)

    def accept(self):
        release_id = self.ui.release_list.currentItem().data(0, QtCore.Qt.UserRole)
        self.tagger.load_album(release_id, discid=self.disc.id)
        super().accept()

    def lookup(self):
        lookup = self.tagger.get_file_lookup()
        lookup.disc_lookup(self.disc.submission_url)
        super().accept()

    @restore_method
    def restore_header_state(self):
        if self.ui.release_list:
            header = self.ui.release_list.header()
            state = config.persist[self.dialog_header_state]
            if state:
                header.restoreState(state)
                log.debug("restore_state: %s" % self.dialog_header_state)

    def save_header_state(self):
        if self.ui.release_list:
            state = self.ui.release_list.header().saveState()
            config.persist[self.dialog_header_state] = state
            log.debug("save_state: %s" % self.dialog_header_state)
