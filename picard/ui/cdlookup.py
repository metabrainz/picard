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

from PyQt5 import QtCore, QtWidgets
from picard.ui import PicardDialog
from picard.ui.ui_cdlookup import Ui_Dialog
from picard.mbjson import artist_credit_from_node, label_info_from_node


class CDLookupDialog(PicardDialog):

    def __init__(self, releases, disc, parent=None):
        PicardDialog.__init__(self, parent)
        self.releases = releases
        self.disc = disc
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.release_list.setSortingEnabled(True)
        self.ui.release_list.setHeaderLabels([_("Album"), _("Artist"), _("Date"), _("Country"),
                                              _("Labels"), _("Catalog #s"), _("Barcode")])
        if self.releases:
            for release in self.releases:
                labels, catalog_numbers = label_info_from_node(release['label-info'])
                date = release['date'] if "date" in release else ""
                country = release['country'] if "country" in release else ""
                barcode = release['barcode'] if "barcode" in release else ""
                item = QtWidgets.QTreeWidgetItem(self.ui.release_list)
                item.setText(0, release['title'])
                item.setText(1, artist_credit_from_node(release['artist_credit']))
                item.setText(2, date)
                item.setText(3, country)
                item.setText(4, ", ".join(labels))
                item.setText(5, ", ".join(catalog_numbers))
                item.setText(6, barcode)
                item.setData(0, QtCore.Qt.UserRole, release.id)
            self.ui.release_list.setCurrentItem(self.ui.release_list.topLevelItem(0))
            self.ui.ok_button.setEnabled(True)
        for i in range(self.ui.release_list.columnCount() - 1):
            self.ui.release_list.resizeColumnToContents(i)
        # Sort by descending date, then ascending country
        self.ui.release_list.sortByColumn(3, QtCore.Qt.AscendingOrder)
        self.ui.release_list.sortByColumn(2, QtCore.Qt.DescendingOrder)
        self.ui.lookup_button.clicked.connect(self.lookup)

    def accept(self):
        release_id = self.ui.release_list.currentItem().data(0, QtCore.Qt.UserRole)
        self.tagger.load_album(release_id, discid=self.disc.id)
        QtWidgets.QDialog.accept(self)

    def lookup(self):
        lookup = self.tagger.get_file_lookup()
        lookup.disc_lookup(self.disc.submission_url)
        QtWidgets.QDialog.accept(self)
