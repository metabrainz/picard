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
from musicbrainz2.utils import extractUuid

class CDLookupDialog(QtGui.QDialog):

    def __init__(self, releases, url, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.releases = releases
        self.url = url
        from picard.ui.ui_cdlookup import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.release_list.setHeaderLabels(
            [_(u"Score"), _(u"Title"), _(u"Artist")])
        self.ui.release_list.header().resizeSection(0, 40)
        self.item_to_release = {}
        if self.releases:
            for res in self.releases:
                item = QtGui.QTreeWidgetItem(self.ui.release_list)
                item.setText(0, str(res.score))
                item.setText(1, res.release.title)
                item.setText(2, res.release.artist.name)
                self.item_to_release[item] = extractUuid(res.release.id)
            self.ui.release_list.setCurrentItem(
                self.ui.release_list.topLevelItem(0))
            self.ui.ok_button.setEnabled(True)
        self.connect(self.ui.lookup_button, QtCore.SIGNAL("clicked()"),
                     self.lookup)

    def accept(self):
        release_id = self.item_to_release[self.ui.release_list.currentItem()]
        if release_id:
            self.tagger.load_album(release_id)
        QtGui.QDialog.accept(self)

    def lookup(self):
        lookup = self.tagger.get_file_lookup()
        lookup.discLookup(self.url)
        QtGui.QDialog.accept(self)

