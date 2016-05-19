# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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

from PyQt4 import QtGui
from picard.ui import PicardDialog

class SearchDialog(PicardDialog):

    def __init__(self, parent=None):
        PicardDialog.__init__(self, parent)
        self.selected_object = None
        self.setupUi()

    def setupUi(self):
        self.setObjectName(_("SearchDialog"))
        self.verticalLayout = QtGui.QVBoxLayout(InfoDialog)
        self.verticalLayout.setObjectName(_("verticalLayout"))
        self.tracksTable = QtGui.QTableWidget(0, 5)
        self.tracksTable.setHorizontalHeaderLabels([_("Name"), _("Length"),
            _("Artist"), _("Release"), _("Type")])
        self.tracksTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tracksTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.verticalLayout.addWidget(self.tracksTable)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(StandardButton(StandardButton.Ok), QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(StandardButton(StandardButton.Cancel), QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted(self.load_selection)
        self.verticalLayout.addWidget(self.buttonBox)
