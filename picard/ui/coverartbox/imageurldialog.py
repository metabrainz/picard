# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2014 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2024 Laurent Monin
# Copyright (C) 2014 Francois Ferrand
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Paul Roub
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 ShubhamBhut
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


from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import gettext as _

from picard.ui import PicardDialog
from picard.ui.util import StandardButton


class ImageURLDialog(PicardDialog):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(_("Enter URL"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(_("Cover art URL:"))
        self.url = QtWidgets.QLineEdit(self)
        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        accept_role = QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole
        self.buttonbox.addButton(StandardButton(StandardButton.OK), accept_role)
        reject_role = QtWidgets.QDialogButtonBox.ButtonRole.RejectRole
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL), reject_role)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.url)
        self.layout.addWidget(self.buttonbox)
        self.setLayout(self.layout)

    @classmethod
    def display(cls, parent=None):
        dialog = cls(parent=parent)
        result = dialog.exec()
        url = QtCore.QUrl(dialog.url.text())
        return (url, result == QtWidgets.QDialog.DialogCode.Accepted)
