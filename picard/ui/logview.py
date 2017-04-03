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


from PyQt5 import QtCore, QtGui, QtWidgets
from picard import config, log
from picard.ui import PicardDialog


class LogViewCommon(PicardDialog):

    def __init__(self, title, logger, w=740, h=340, parent=None):
        PicardDialog.__init__(self, parent)
        self.logger = logger
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(w, h)
        self.setWindowTitle(title)
        self.doc = QtGui.QTextDocument(self)
        self.textCursor = QtGui.QTextCursor(self.doc)
        self.browser = QtWidgets.QTextBrowser(self)
        self.browser.setDocument(self.doc)
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.addWidget(self.browser)
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
        self.textCursor.insertText(self._formatted_log_line(level, time, msg),
                                   self._format(level))
        self.textCursor.insertBlock()
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _formatted_log_line(self, level, time, msg):
        return log.formatted_log_line(level, time, msg)

    def closeEvent(self, event):
        self.logger.unregister_receiver(self._add_entry)
        return QtWidgets.QDialog.closeEvent(self, event)

    def saveWindowState(self, position, size):
        pos = self.pos()
        if not pos.isNull():
            config.persist[position] = pos
        config.persist[size] = self.size()

    def restoreWindowState(self, position, size):
        pos = config.persist[position]
        if pos.x() > 0 and pos.y() > 0:
            self.move(pos)
        self.resize(config.persist[size])


class LogView(LogViewCommon):

    options = [
        config.Option("persist", "logview_position", QtCore.QPoint()),
        config.Option("persist", "logview_size", QtCore.QSize(560, 400)),
    ]

    def __init__(self, parent=None):
        title = _("Log")
        logger = log.main_logger
        LogViewCommon.__init__(self, title, logger, parent=parent)
        self.restoreWindowState("logview_position", "logview_size")
        cb = QtWidgets.QCheckBox(_('Debug mode'), self)
        cb.setChecked(QtCore.QObject.tagger._debug)
        cb.stateChanged.connect(self.toggleDebug)
        self.vbox.addWidget(cb)

    def toggleDebug(self, state):
        QtCore.QObject.tagger.debug(state == QtCore.Qt.Checked)

    def closeEvent(self, event):
        self.saveWindowState("logview_position", "logview_size")
        event.accept()


class HistoryView(LogViewCommon):

    options = [
        config.Option("persist", "historyview_position", QtCore.QPoint()),
        config.Option("persist", "historyview_size", QtCore.QSize(560, 400)),
    ]

    def __init__(self, parent=None):
        title = _("Activity History")
        logger = log.history_logger
        LogViewCommon.__init__(self, title, logger, parent=parent)
        self.restoreWindowState("historyview_position", "historyview_size")

    def _formatted_log_line(self, level, time, msg):
        return log.formatted_log_line(level, time, msg, level_prefixes=False)

    def closeEvent(self, event):
        self.saveWindowState("historyview_position", "historyview_size")
        event.accept()
