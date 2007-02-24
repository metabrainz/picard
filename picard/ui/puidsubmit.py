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

import os.path
from PyQt4 import QtCore, QtGui

class PUIDSubmitDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        from picard.ui.ui_puidsubmit import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.puid_list.setHeaderLabels(
            [_(u"File"), _(u"PUID"), _(u"Track"), _(u"Release"), _(u"Release ID")])
        self.ui.puid_list.header().setStretchLastSection(False)
        for file in self.tagger.files.values():
            item = QtGui.QTreeWidgetItem(self.ui.puid_list)
            if file.metadata["musicip_puid"] == file.orig_metadata["musicip_puid"]:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            else:
                item.setCheckState(0, QtCore.Qt.Checked)
            item.setText(0, os.path.basename(file.filename))
            item.setText(1, file.metadata["musicip_puid"])
            item.setText(2, file.metadata["title"])
            item.setText(3, file.metadata["album"])
            item.setText(4, file.metadata["musicbrainz_albumid"])
