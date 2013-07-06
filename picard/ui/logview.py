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
from picard import log


class LogViewCommon(QtGui.QDialog):

    def __init__(self, title, logger, w=740, h=340, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.logger = logger
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(w, h)
        self.setWindowTitle(title)
        self.doc = QtGui.QTextDocument(self)
        self.textCursor = QtGui.QTextCursor(self.doc)
        self.browser = QtGui.QTextBrowser(self)
        self.browser.setDocument(self.doc)
        vbox = QtGui.QHBoxLayout(self)
        vbox.addWidget(self.browser)
        self._display()

    def _setup_formats(self):
        font = QtGui.QFont()
        font.setFamily("Monospace")
        self.textFormatInfo = QtGui.QTextCharFormat()
        self.textFormatInfo.setFont(font)
        self.textFormatInfo.setForeground(QtGui.QColor('black'))
        self.textFormatDebug = QtGui.QTextCharFormat()
        self.textFormatDebug.setFont(font)
        self.textFormatDebug.setForeground(QtGui.QColor('purple'))
        self.textFormatWarning = QtGui.QTextCharFormat()
        self.textFormatWarning.setFont(font)
        self.textFormatWarning.setForeground(QtGui.QColor('darkorange'))
        self.textFormatError = QtGui.QTextCharFormat()
        self.textFormatError.setFont(font)
        self.textFormatError.setForeground(QtGui.QColor('red'))
        self.formats = {
            log.LOG_INFO: self.textFormatInfo,
            log.LOG_WARNING: self.textFormatWarning,
            log.LOG_ERROR: self.textFormatError,
            log.LOG_DEBUG: self.textFormatDebug,
        }

    def _format(self, level):
        return self.formats[level]

    def _display(self):
        self._setup_formats()
        for level, time, msg in self.logger.entries:
            self._add_entry(level, time, msg)
        self.logger.register_receiver(self._add_entry)

    def _add_entry(self, level, time, msg):
        self.textCursor.movePosition(QtGui.QTextCursor.End)
        self.textCursor.insertText(time.toString() + ' ' + msg,
                                   self._format(level))
        self.textCursor.insertBlock()
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        self.logger.unregister_receiver(self._add_entry)
        return QtGui.QDialog.closeEvent(self, event)


class LogView(LogViewCommon):

    def __init__(self, parent=None):
        title = _("Log")
        logger = log.main_logger
        LogViewCommon.__init__(self, title, logger, parent=parent)
