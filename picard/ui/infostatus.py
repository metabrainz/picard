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

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.util import icontheme

from picard.ui.ui_infostatus import Ui_InfoStatus


class InfoStatus(QtWidgets.QWidget, Ui_InfoStatus):

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        Ui_InfoStatus.__init__(self)
        self.setupUi(self)

        self._size = QtCore.QSize(16, 16)
        self._create_icons()
        self._init_labels()

    def _init_labels(self):
        size = self._size
        self.label1.setPixmap(self.icon_file.pixmap(size))
        self.label2.setPixmap(self.icon_cd.pixmap(size))
        self.label3.setPixmap(self.icon_file_pending.pixmap(size))
        self.label4.setPixmap(self.icon_download.pixmap(size, QtGui.QIcon.Disabled))
        self._init_tooltips()

    def _create_icons(self):
        self.icon_cd = icontheme.lookup('media-optical')
        self.icon_file = QtGui.QIcon(":/images/file.png")
        self.icon_file_pending = QtGui.QIcon(":/images/file-pending.png")
        self.icon_download = QtGui.QIcon(":/images/16x16/action-go-down-16.png")

    def _init_tooltips(self):
        t1 = _("Files")
        t2 = _("Albums")
        t3 = _("Pending files")
        t4 = _("Pending requests")
        self.val1.setToolTip(t1)
        self.label1.setToolTip(t1)
        self.val2.setToolTip(t2)
        self.label2.setToolTip(t2)
        self.val3.setToolTip(t3)
        self.label3.setToolTip(t3)
        self.val4.setToolTip(t4)
        self.label4.setToolTip(t4)

    def setFiles(self, num):
        self.val1.setText(str(num))

    def setAlbums(self, num):
        self.val2.setText(str(num))

    def setPendingFiles(self, num):
        self.val3.setText(str(num))

    def setPendingRequests(self, num):
        if num <= 0:
            enabled = QtGui.QIcon.Disabled
        else:
            enabled = QtGui.QIcon.Normal
        self.label4.setPixmap(self.icon_download.pixmap(self._size, enabled))
        self.val4.setText(str(num))
