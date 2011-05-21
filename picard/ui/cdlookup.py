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

from PyQt4 import QtCore, QtGui
from picard.ui.ui_cdlookup import Ui_Dialog
from picard.mbxml import artist_credit_from_node

class CDLookupDialog(QtGui.QDialog):

    def __init__(self, releases, disc, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.releases = releases
        self.disc = disc
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.release_list.setHeaderLabels([_(u"Score"), _(u"Album"), _(u"Artist")])
        self.ui.release_list.header().resizeSection(0, 40)
        if self.releases:
            for release in self.releases:
                item = QtGui.QTreeWidgetItem(self.ui.release_list)
                #item.setText(0, release.score)
                item.setText(1, release.title[0].text)
                item.setText(2, artist_credit_from_node(release.artist_credit[0])[0])
                item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(release.id))
            self.ui.release_list.setCurrentItem(self.ui.release_list.topLevelItem(0))
            self.ui.ok_button.setEnabled(True)
        self.connect(self.ui.lookup_button, QtCore.SIGNAL("clicked()"), self.lookup)

    def accept(self):
        release_id = str(self.ui.release_list.currentItem().data(0, QtCore.Qt.UserRole).toString())
        self.tagger.load_album(release_id, discid=self.disc.id)
        QtGui.QDialog.accept(self)

    def lookup(self):
        lookup = self.tagger.get_file_lookup()
        lookup.discLookup(self.disc.submission_url)
        QtGui.QDialog.accept(self)
