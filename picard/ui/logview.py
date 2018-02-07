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


import os

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
    WIDTH = 570
    HEIGHT = 400

    def __init__(self, log_tail, *args, **kwargs):
        self.displaying = False
        self.prev = -1
        self.log_tail = log_tail
        self.log_tail.updated.connect(self._updated)
        super().__init__(*args, **kwargs)

    def show(self):
        self.display(clear=True)
        super().show()

    def _updated(self):
        if self.displaying:
            return
        self.display()

    def display(self, clear=False):
        self.displaying = True
        if clear:
            self.prev = -1
            self.doc.clear()
            self.textCursor.movePosition(QtGui.QTextCursor.Start)
        for logitem in self.log_tail.contents(self.prev):
            self._add_entry(logitem)
            self.prev = logitem.pos
        self.displaying = False

    def _add_entry(self, logitem):
        self.textCursor.movePosition(QtGui.QTextCursor.End)
        self.textCursor.insertText(logitem.message)
        self.textCursor.insertBlock()
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())


class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, string, parent=None):
        super().__init__(parent)

        self.fmt = QtGui.QTextCharFormat()
        self.fmt.setBackground(QtCore.Qt.lightGray)

        self.reg = QtCore.QRegExp()
        self.reg.setPatternSyntax(QtCore.QRegExp.Wildcard)
        self.reg.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.reg.setPattern(string)

    def highlightBlock(self, text):
        expression = self.reg
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length, self.fmt)
            index = expression.indexIn(text, index + length)


class LogView(LogViewCommon):

    options = [
        config.Option("persist", "logview_position", QtCore.QPoint()),
        config.Option("persist", "logview_size", QtCore.QSize(
            LogViewCommon.WIDTH, LogViewCommon.HEIGHT)),
        config.Option("persist", "logview_verbosity",
                      set(log.levels_features)),
    ]

    def __init__(self, parent=None):
        super().__init__(log.main_tail, _("Log"), w=self.WIDTH,
                         h=self.HEIGHT, parent=parent)
        self.verbosity = config.persist['logview_verbosity']
        self.restoreWindowState("logview_position", "logview_size")

        self._setup_formats()
        self.hidden_domains = set()
        self.show_only_domains = set()
        self.hl_text = ''
        self.filter_enabled = False
        self.domains_menu_can_update = True
        self.hl = None

        self.hbox = QtWidgets.QHBoxLayout(self)
        self.vbox.addLayout(self.hbox)

        # debug mode
        cb = QtWidgets.QCheckBox(_('Debug mode'), self)
        cb.setChecked(QtCore.QObject.tagger._debug)
        cb.stateChanged.connect(self.toggleDebug)
        self.hbox.addWidget(cb)

        # Verbosity
        self.verbosity_menu_button = QtWidgets.QPushButton(_("Verbosity"), self)
        self.hbox.addWidget(self.verbosity_menu_button)

        self.verbosity_menu = QtWidgets.QMenu(self)
        for level, feat in log.levels_features.items():
            act = QtWidgets.QAction(_(feat.name), self.verbosity_menu)
            act.setCheckable(True)
            act.setChecked(level in self.verbosity)
            act.triggered.connect(partial(self._verbosity_changed, level))
            self.verbosity_menu.addAction(act)
        self.verbosity_menu_button.setMenu(self.verbosity_menu)

        # Domains
        self.domains_menu = QtWidgets.QMenu(self)
        self.domains_menu_button = QtWidgets.QPushButton(_("Domains"), self)
        self.domains_menu_button.setMenu(self.domains_menu)
        self.domains_menu.aboutToShow.connect(
            partial(self.set_domains_menu_can_update, False))
        self.domains_menu.aboutToHide.connect(
            partial(self.set_domains_menu_can_update, True))
        self.hbox.addWidget(self.domains_menu_button)

        # Show only
        self.show_only_domains_menu = QtWidgets.QMenu(self)
        self.show_only_domains_menu_button = QtWidgets.QPushButton(
            _("Show Only"), self)
        self.show_only_domains_menu_button.setMenu(self.show_only_domains_menu)
        self.show_only_domains_menu.aboutToShow.connect(
            partial(self.set_domains_menu_can_update, False))
        self.show_only_domains_menu.aboutToHide.connect(
            partial(self.set_domains_menu_can_update, True))
        self.hbox.addWidget(self.show_only_domains_menu_button)

        # highlight input
        self.highlight_text = QtWidgets.QLineEdit(self)
        self.highlight_text.setPlaceholderText(_("String to highlight"))
        self.highlight_text.textEdited.connect(self._highlight_text_edited)
        self.hbox.addWidget(self.highlight_text)

        # highlight button
        self.highlight_button = QtWidgets.QPushButton(_("Highlight"), self)
        self.hbox.addWidget(self.highlight_button)
        self.highlight_button.setDefault(True)
        self.highlight_button.setEnabled(False)
        self.highlight_button.clicked.connect(self._highlight_do)

        self.highlight_text.returnPressed.connect(self.highlight_button.click)

        # clear highlight button
        self.clear_highlight_button = QtWidgets.QPushButton(_("Clear Highlight"), self)
        self.hbox.addWidget(self.clear_highlight_button)
        self.clear_highlight_button.setEnabled(False)
        self.clear_highlight_button.clicked.connect(self._clear_highlight_do)

        # clear log
        self.clear_log_button = QtWidgets.QPushButton(_("Clear Log"), self)
        self.hbox.addWidget(self.clear_log_button)
        self.clear_log_button.clicked.connect(self._clear_log_do)

        # save as
        self.save_log_as_button = QtWidgets.QPushButton(_("Save As..."), self)
        self.hbox.addWidget(self.save_log_as_button)
        self.save_log_as_button.clicked.connect(self._save_log_as_do)

        # ------

        self.log_tail.domains_updated.connect(self.menu_domains_rebuild)

    def _clear_highlight_do(self):
        self.highlight_text.setText('')
        self.highlight_button.setEnabled(False)
        self._highlight_do()

    def _highlight_text_edited(self, text):
        if text and self.hl_text != text:
            self.highlight_button.setEnabled(True)
        else:
            self.highlight_button.setEnabled(False)
        if not text:
            self.clear_highlight_button.setEnabled(bool(self.hl))

    def _highlight_do(self):
        new_hl_text = self.highlight_text.text()
        if new_hl_text != self.hl_text:
            self.hl_text = new_hl_text
            if self.hl is not None:
                self.hl.setDocument(None)
                self.hl = None
            if self.hl_text:
                self.hl = Highlighter(self.hl_text, parent=self.doc)
            self.clear_highlight_button.setEnabled(bool(self.hl))

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

    def _save_log_as_do(self):
        path, ok = QtWidgets.QFileDialog.getSaveFileName(
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
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
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
        known_domains = sorted(self.log_tail.known_domains)
        self.filter_enabled = bool(known_domains)
        self.show_only_domains_menu_button.setEnabled(self.filter_enabled)
        self.domains_menu_button.setEnabled(self.filter_enabled)
        for domain in known_domains:
            act = QtWidgets.QAction(domain, self.domains_menu)
            act.setCheckable(True)
            act.setChecked(domain not in self.hidden_domains)
            act.triggered.connect(partial(self._domains_changed, domain))
            self.domains_menu.addAction(act)

            act = QtWidgets.QAction(domain, self.show_only_domains_menu)
            act.setCheckable(True)
            act.setChecked(domain in self.show_only_domains)
            act.triggered.connect(
                partial(self._show_only_domains_changed, domain))
            self.show_only_domains_menu.addAction(act)

    def show(self):
        self.menu_domains_rebuild()
        self.highlight_text.setFocus(QtCore.Qt.OtherFocusReason);
        super().show()

    def _clear_log_do(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            _("Clear Log"),
            _("Are you sure you want to clear the log?"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        self.log_tail.clear()
        self.menu_domains_rebuild()
        self.display(clear=True)

    def is_shown(self, logitem):
        if logitem.level not in self.verbosity:
            return False
        show_set = self.show_only_domains
        hide_set = self.hidden_domains
        show = True
        if show_set and (not logitem.domains or
                         logitem.domains.isdisjoint(show_set)):
            show = False
        if hide_set and logitem.domains and logitem.domains.intersection(hide_set):
            return False
        return show

    def _add_entry(self, logitem):
        if not self.is_shown(logitem):
            return
        fmt = self.textCursor.blockCharFormat()
        self.textCursor.setBlockCharFormat(self._format(logitem.level))
        super()._add_entry(logitem)
        self.textCursor.setBlockCharFormat(fmt)
        if not self.filter_enabled:
            self.menu_domains_rebuild()

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
        self.display(clear=True)

    def _show_only_domains_changed(self, domain, checked):
        if not checked:
            self.show_only_domains.discard(domain)
        else:
            self.show_only_domains.add(domain)
        self.display(clear=True)

    def _domains_changed(self, domain, checked):
        if checked:
            self.hidden_domains.discard(domain)
        else:
            self.hidden_domains.add(domain)
        self.display(clear=True)


class HistoryView(LogViewCommon):
    options = [
        config.Option("persist", "historyview_position", QtCore.QPoint()),
        config.Option("persist", "historyview_size", QtCore.QSize(LogViewCommon.WIDTH,
                                                                  LogViewCommon.HEIGHT)),
    ]

    def __init__(self, parent=None):
        super().__init__(log.history_tail, _("Activity History"), w=self.WIDTH,
                         h=self.HEIGHT, parent=parent)
        self.restoreWindowState("historyview_position", "historyview_size")

    def closeEvent(self, event):
        self.saveWindowState("historyview_position", "historyview_size")
        super().closeEvent(event)
