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


import logging
import os

from collections import OrderedDict
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets
from picard import config, log
from picard.ui import PicardDialog


class LogViewDialog(PicardDialog):

    def __init__(self, title, w, h, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(w, h)
        self.setWindowTitle(title)
        self.doc = QtGui.QTextDocument(self)
        self.textCursor = QtGui.QTextCursor(self.doc)
        self.browser = QtWidgets.QTextBrowser(self)
        self.browser.setDocument(self.doc)
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.addWidget(self.browser)

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

    def closeEvent(self, event):
        return super().closeEvent(event)


class LogViewCommon(LogViewDialog):

    def __init__(self, title, logger, w=740, h=340, parent=None):
        super().__init__(title, w, h, parent=parent)
        self.logger = logger
        self._setup_formats()
        self.verbosity = set(log.levels_features)
        self.hidden_domains = set()
        self.show_only_domains = set()
        self.hl_text = ''

    def _setup_formats(self):
        self.formats = {}
        font = QtGui.QFont()
        font.setFamily("Monospace")
        for level, feat in log.levels_features.items():
            text_fmt = QtGui.QTextCharFormat()
            text_fmt.setFont(font)
            text_fmt.setForeground(QtGui.QColor(feat.fgcolor))
            self.formats[level] = text_fmt

    def _format(self, level):
        return self.formats[level]

    def _unregister_add_entry(self):
        try:
            self.logger.unregister_receiver(self._add_entry)
        except ValueError:
            pass

    def display(self):
        self._unregister_add_entry()
        self.doc.clear()
        self.textCursor.movePosition(QtGui.QTextCursor.Start)
        for message_obj in self.logger.entries:
            self._add_entry(message_obj)
        if self.hl_text:
            self.highlight(self.hl_text)
        self.logger.register_receiver(self._add_entry)

    def _add_entry(self, message_obj):
        if not message_obj.is_shown(verbosity=self.verbosity,
                                    hide_set=self.hidden_domains,
                                    show_set=self.show_only_domains):
            return
        if self.hl_text:
            cursor = QtGui.QTextCursor(self.doc)
            # FIXME: not sure about this, but -1 is needed
            pos = max(0, self.textCursor.position()-1)
            cursor.setPosition(pos)
            cursor.setKeepPositionOnInsert(True)

        self.textCursor.movePosition(QtGui.QTextCursor.End)
        self.textCursor.insertText(self._formatted_log_line(message_obj),
                                   self._format(message_obj.level))
        self.textCursor.insertBlock()
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())
        if self.hl_text:
            self.highlight(self.hl_text, cursor)

    def _formatted_log_line(self, message_obj):
        return log.formatted_log_line(message_obj)

    def closeEvent(self, event):
        self._unregister_add_entry()
        super().closeEvent(event)

    def highlight(self, searchString, cursor=None):
        # adapted from http://doc.qt.io/qt-5/qtuitools-textfinder-example.html
        if cursor:
            highlightCursor = cursor
        else:
            highlightCursor = QtGui.QTextCursor(self.doc)

        colorFormat = highlightCursor.charFormat()
        colorFormat.setForeground(QtGui.QColor('green'))

        while not highlightCursor.isNull() and not highlightCursor.atEnd():
            highlightCursor = self.doc.find(searchString, highlightCursor)
            if not highlightCursor.isNull():
                highlightCursor.movePosition(QtGui.QTextCursor.WordRight,
                                             QtGui.QTextCursor.KeepAnchor)
                highlightCursor.mergeCharFormat(colorFormat)



class LogView(LogViewCommon):

    options = [
        config.Option("persist", "logview_position", QtCore.QPoint()),
        config.Option("persist", "logview_size", QtCore.QSize(560, 400)),
        config.Option("persist", "logview_verbosity", set(log.levels_features)),
    ]

    def __init__(self, parent=None):
        title = _("Log")
        logger = log.main_logger
        super().__init__(title, logger, parent=parent)
        self.verbosity = config.persist['logview_verbosity']
        self.restoreWindowState("logview_position", "logview_size")
        self.hbox = QtWidgets.QHBoxLayout(self)
        self.vbox.addLayout(self.hbox)

        cb = QtWidgets.QCheckBox(_('Debug mode'), self)
        cb.setChecked(QtCore.QObject.tagger._debug)
        cb.stateChanged.connect(self.toggleDebug)
        self.hbox.addWidget(cb)

        self.verbosity_menu = QtWidgets.QMenu(self)
        for level, feat in log.levels_features.items():
            act = QtWidgets.QAction(_(feat.name), self.verbosity_menu)
            act.setCheckable(True)
            act.setChecked(level in self.verbosity)
            act.triggered.connect(partial(self._verbosity_changed, level))
            self.verbosity_menu.addAction(act)

        self.verbosity_menu_button = QtWidgets.QPushButton(_("Verbosity"))
        self.verbosity_menu_button.setMenu(self.verbosity_menu)
        self.hbox.addWidget(self.verbosity_menu_button)

        self.domains_menu_can_update = True

        self.domains_menu = QtWidgets.QMenu(self)
        self.domains_menu_button = QtWidgets.QPushButton(_("Domains"))
        self.domains_menu_button.setMenu(self.domains_menu)
        self.domains_menu.aboutToShow.connect(partial(self.set_domains_menu_can_update, False))
        self.domains_menu.aboutToHide.connect(partial(self.set_domains_menu_can_update, True))

        self.show_only_domains_menu = QtWidgets.QMenu(self)
        self.show_only_domains_menu_button = QtWidgets.QPushButton(_("Show Only"))
        self.show_only_domains_menu_button.setMenu(self.show_only_domains_menu)
        self.show_only_domains_menu.aboutToShow.connect(partial(self.set_domains_menu_can_update, False))
        self.show_only_domains_menu.aboutToHide.connect(partial(self.set_domains_menu_can_update, True))

        self.hbox.addWidget(self.domains_menu_button)
        self.hbox.addWidget(self.show_only_domains_menu_button)

        self.highlight_text = QtWidgets.QLineEdit()
        self.hbox.addWidget(self.highlight_text)

        self.highlight_button = QtWidgets.QPushButton(_("Highlight"))
        self.hbox.addWidget(self.highlight_button)
        self.highlight_button.clicked.connect(self._highlight_do)

        self.clear_log_button = QtWidgets.QPushButton(_("Clear Log"))
        self.hbox.addWidget(self.clear_log_button)
        self.clear_log_button.clicked.connect(self._clear_log_do)

        self.save_log_as_button = QtWidgets.QPushButton(_("Save As..."))
        self.hbox.addWidget(self.save_log_as_button)
        self.save_log_as_button.clicked.connect(self._save_log_as_do)

        logger.domains_updated.connect(self.menu_domains_rebuild)
        self.display()

    def _save_log_as_do(self):
        path, ok =  QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption=_("Save Log View to File"),
            filter=_("Text Files (*.txt *.TXT)"),
            options=QtWidgets.QFileDialog.DontConfirmOverwrite
        )
        if ok and path:
            if os.path.isfile(path):
                reply = QtWidgets.QMessageBox.question(
                    self,
                    _("Save Log View to File"),
                    _("File already exists, do you really want to save to this file?"),
                     QtWidgets.QMessageBox.Yes |  QtWidgets.QMessageBox.No
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return

            writer = QtGui.QTextDocumentWriter(path)
            success = writer.write(self.doc)
            # FIXME: handle errors

    def set_domains_menu_can_update(self, can_update):
        self.domains_menu_can_update = can_update

    def menu_domains_rebuild(self):
        if not self.domains_menu_can_update:
            return
        self.domains_menu.clear()
        self.show_only_domains_menu.clear()
        for domain in sorted(self.logger.known_domains):
            act = QtWidgets.QAction(domain, self.domains_menu)
            act.setCheckable(True)
            act.setChecked(domain not in self.hidden_domains)
            act.triggered.connect(partial(self._domains_changed, domain))
            self.domains_menu.addAction(act)

            act = QtWidgets.QAction(domain, self.show_only_domains_menu)
            act.setCheckable(True)
            act.setChecked(domain in self.show_only_domains)
            act.triggered.connect(partial(self._show_only_domains_changed, domain))
            self.show_only_domains_menu.addAction(act)

    def show(self):
        self.menu_domains_rebuild()
        super().show()

    def _clear_log_do(self):
        self.logger.reset()
        self.menu_domains_rebuild()
        self.display()

    def _highlight_do(self):
        self.hl_text = self.highlight_text.text()
        self.display()

    def toggleDebug(self, state):
        QtCore.QObject.tagger.debug(state == QtCore.Qt.Checked)

    def closeEvent(self, event):
        config.persist['logview_verbosity'] = self.verbosity
        self.saveWindowState("logview_position", "logview_size")
        super().closeEvent(event)

    def _verbosity_changed(self, level, checked):
        if checked:
            self.verbosity.add(level)
        else:
            self.verbosity.discard(level)
        self.display()

    def _show_only_domains_changed(self, domain, checked):
        if not checked:
            self.show_only_domains.discard(domain)
        else:
            self.show_only_domains.add(domain)
        self.display()

    def _domains_changed(self, domain, checked):
        if checked:
            self.hidden_domains.discard(domain)
        else:
            self.hidden_domains.add(domain)
        self.display()

class HistoryView(LogViewCommon):

    options = [
        config.Option("persist", "historyview_position", QtCore.QPoint()),
        config.Option("persist", "historyview_size", QtCore.QSize(560, 400)),
    ]

    def __init__(self, parent=None):
        title = _("Activity History")
        logger = log.history_logger
        super().__init__(title, logger, parent=parent)
        self.restoreWindowState("historyview_position", "historyview_size")
        self.display()

    def _formatted_log_line(self, message_obj):
        return log.formatted_log_line(message_obj, level_prefixes=False)

    def closeEvent(self, event):
        self.saveWindowState("historyview_position", "historyview_size")
        super().closeEvent(event)
