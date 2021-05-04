# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2009, 2018-2021 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013-2014, 2018, 2020 Laurent Monin
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


from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    get_config,
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

    autorestore = False
    dialog_header_state = "cdlookupdialog_header_state"

    options = [
        Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, releases, disc, parent=None):
        super().__init__(parent)
        self.releases = releases
        self.disc = disc
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        release_list = self.ui.release_list
        release_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        release_list.setSortingEnabled(True)
        release_list.setAlternatingRowColors(True)
        release_list.setHeaderLabels([_("Album"), _("Artist"), _("Date"), _("Country"),
                                      _("Labels"), _("Catalog #s"), _("Barcode"),
                                      _("Disambiguation")])
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
                item.setText(0, release['title'])
                item.setText(1, artist_credit_from_node(release['artist-credit'])[0])
                item.setText(2, myjoin(dates))
                item.setText(3, myjoin(countries))
                item.setText(4, myjoin(labels))
                item.setText(5, myjoin(catalog_numbers))
                item.setText(6, barcode)
                item.setText(7, release.get('disambiguation', ''))
                item.setData(0, QtCore.Qt.UserRole, release['id'])
            release_list.setCurrentItem(selected or release_list.topLevelItem(0))
            self.ui.ok_button.setEnabled(True)
            for i in range(release_list.columnCount() - 1):
                release_list.resizeColumnToContents(i)
            # Sort by descending date, then ascending country
            release_list.sortByColumn(3, QtCore.Qt.AscendingOrder)
            release_list.sortByColumn(2, QtCore.Qt.DescendingOrder)
        else:
            self.ui.results_view.setCurrentIndex(1)
        self.ui.lookup_button.clicked.connect(self.lookup)
        self.ui.submit_button.clicked.connect(self.lookup)
        self.restore_geometry()
        self.restore_header_state()
        self.finished.connect(self.save_header_state)

    def accept(self):
        release_list = self.ui.release_list
        for index in release_list.selectionModel().selectedRows():
            release_id = release_list.itemFromIndex(index).data(0, QtCore.Qt.UserRole)
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
            config = get_config()
            state = config.persist[self.dialog_header_state]
            if state:
                header.restoreState(state)
                log.debug("restore_state: %s" % self.dialog_header_state)

    def save_header_state(self):
        if self.ui.release_list:
            state = self.ui.release_list.header().saveState()
            config = get_config()
            config.persist[self.dialog_header_state] = state
            log.debug("save_state: %s" % self.dialog_header_state)
