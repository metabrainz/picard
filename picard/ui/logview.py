# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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
from picard.log import log


class LogView(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(_("Log"))
        self.doc = QtGui.QTextDocument(self)
        self.browser = QtGui.QTextBrowser(self)
        self.browser.setDocument(self.doc)
        vbox = QtGui.QHBoxLayout(self)
        vbox.addWidget(self.browser)
        for prefix, msg in log.entries:
            self.add_entry(prefix, msg)
        log.add_receiver(self.add_entry)

    def add_entry(self, prefix, msg):
        # FIXME this is just ugly
        self.doc.setHtml(self.doc.toHtml() + '<div style="white-space:pre;"><code>' + prefix + ' ' + str(QtCore.QThread.currentThreadId()) + ' ' + QtCore.QTime.currentTime().toString() + ' ' + msg.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>') + '</code></div>')
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())
