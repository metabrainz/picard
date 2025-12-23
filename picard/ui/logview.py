# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2008-2009, 2019-2023 Philipp Wolfer
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016, 2018 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2022 Kamil
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


from functools import partial
import logging
import os
import re

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.debug_opts import DebugOpt
from picard.i18n import gettext as _
from picard.util import (
    reconnect,
    wildcards_to_regex_pattern,
)

from picard.ui import (
    FONT_FAMILY_MONOSPACE,
    PicardDialog,
)
from picard.ui.colors import interface_colors
from picard.ui.util import FileDialog


class LogViewDialog(PicardDialog):
    defaultsize = QtCore.QSize(570, 400)

    def __init__(self, title, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setWindowTitle(title)
        self.doc = QtGui.QTextDocument()
        self.textCursor = QtGui.QTextCursor(self.doc)
        self.browser = QtWidgets.QTextBrowser()
        self.browser.setDocument(self.doc)
        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox)
        self.vbox.addWidget(self.browser)


class LogViewCommon(LogViewDialog):
    def __init__(self, log_tail, title, parent=None):
        super().__init__(title, parent=parent)
        self.displaying = False
        self.log_tail = log_tail
        self._init_doc()

    def _init_doc(self):
        self.prev = -1
        self.doc.clear()
        self.textCursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)

    def closeEvent(self, event):
        self.save_geometry()
        event.ignore()
        self.hide()

    def hideEvent(self, event):
        reconnect(self.log_tail.updated, None)
        super().hideEvent(event)

    def showEvent(self, event):
        self.display()
        reconnect(self.log_tail.updated, self._updated)
        super().showEvent(event)

    def _updated(self):
        if self.displaying:
            return
        self.display()

    def display(self, clear=False):
        self.displaying = True
        if clear:
            self._init_doc()
        for logitem in self.log_tail.contents(self.prev):
            self._add_entry(logitem)
            self.prev = logitem.pos
        self.displaying = False

    def _add_entry(self, logitem):
        self.textCursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        self.textCursor.insertText(logitem.message)
        self.textCursor.insertBlock()
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self):
        self.log_tail.clear()
        self.display(clear=True)


class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, string, parent):
        super().__init__(parent)

        self.fmt = QtGui.QTextCharFormat()
        self.fmt.setBackground(QtCore.Qt.GlobalColor.lightGray)
        self.reg = re.compile(wildcards_to_regex_pattern(string), re.IGNORECASE)

    def highlightBlock(self, text):
        for match in self.reg.finditer(text):
            index = match.start()
            length = match.end() - match.start()
            self.setFormat(index, length, self.fmt)


class VerbosityMenu(QtWidgets.QMenu):
    verbosity_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.action_group = QtGui.QActionGroup(self)
        self.actions = {}
        for level, feat in log.levels_features.items():
            action = QtGui.QAction(_(feat.name), self)
            action.setCheckable(True)
            action.triggered.connect(partial(self.verbosity_changed.emit, level))
            self.action_group.addAction(action)
            self.addAction(action)
            self.actions[level] = action

    def set_verbosity(self, level):
        self.actions[level].setChecked(True)


class DebugOptsMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.actions = {}
        for debug_opt in DebugOpt:
            action = QtGui.QAction(_(debug_opt.title), self, checkable=True, checked=debug_opt.enabled)
            action.setToolTip(_(debug_opt.description))
            action.triggered.connect(partial(self.debug_opt_changed, debug_opt))
            self.addAction(action)
            self.actions[debug_opt] = action

    def debug_opt_changed(self, debug_opt, checked):
        debug_opt.enabled = checked


class LogView(LogViewCommon):
    def __init__(self, parent=None):
        super().__init__(log.main_tail, _("Log"), parent=parent)
        self.verbosity = log.get_effective_level()

        self._setup_formats()
        self.hl_text = ''
        self.hl = None

        self.hbox = QtWidgets.QHBoxLayout()
        self.vbox.addLayout(self.hbox)

        self.verbosity_menu_button = QtWidgets.QPushButton()
        self.verbosity_menu_button.setAccessibleName(_("Verbosity"))
        self.hbox.addWidget(self.verbosity_menu_button)

        self.verbosity_menu = VerbosityMenu()
        self.verbosity_menu.verbosity_changed.connect(self._verbosity_changed)
        self.verbosity_menu_button.setMenu(self.verbosity_menu)

        self.debug_opts_menu_button = QtWidgets.QPushButton(_("Debug Options"))
        self.debug_opts_menu_button.setAccessibleName(_("Debug Options"))
        self.hbox.addWidget(self.debug_opts_menu_button)

        self.debug_opts_menu = DebugOptsMenu()
        self.debug_opts_menu_button.setMenu(self.debug_opts_menu)

        self._set_verbosity(self.verbosity)

        # highlight input
        self.highlight_text = QtWidgets.QLineEdit()
        self.highlight_text.setPlaceholderText(_("String to highlight"))
        self.highlight_text.textEdited.connect(self._highlight_text_edited)
        self.hbox.addWidget(self.highlight_text)

        # highlight button
        self.highlight_button = QtWidgets.QPushButton(_("Highlight"))
        self.hbox.addWidget(self.highlight_button)
        self.highlight_button.setDefault(True)
        self.highlight_button.setEnabled(False)
        self.highlight_button.clicked.connect(self._highlight_do)

        self.highlight_text.returnPressed.connect(self.highlight_button.click)

        # clear highlight button
        self.clear_highlight_button = QtWidgets.QPushButton(_("Clear Highlight"))
        self.hbox.addWidget(self.clear_highlight_button)
        self.clear_highlight_button.setEnabled(False)
        self.clear_highlight_button.clicked.connect(self._clear_highlight_do)

        # clear log
        self.clear_log_button = QtWidgets.QPushButton(_("Clear Log…"))
        self.hbox.addWidget(self.clear_log_button)
        self.clear_log_button.clicked.connect(self._clear_log_do)

        # save as
        self.save_log_as_button = QtWidgets.QPushButton(_("Save As…"))
        self.hbox.addWidget(self.save_log_as_button)
        self.save_log_as_button.clicked.connect(self._save_log_as_do)

        self._prev_logitem_level = logging.NOTSET

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
                self.hl = Highlighter(self.hl_text, self.doc)
            self.clear_highlight_button.setEnabled(bool(self.hl))

    def _setup_formats(self):
        interface_colors.load_from_config()
        self.formats = {}
        for level, feat in log.levels_features.items():
            text_fmt = QtGui.QTextCharFormat()
            text_fmt.setFontFamilies([FONT_FAMILY_MONOSPACE])
            text_fmt.setForeground(interface_colors.get_qcolor(feat.color_key))
            self.formats[level] = text_fmt

    def _format(self, level):
        return self.formats[level]

    def _save_log_as_do(self):
        path, ok = FileDialog.getSaveFileName(
            parent=self,
            caption=_("Save Log View to File"),
            options=QtWidgets.QFileDialog.Option.DontConfirmOverwrite,
        )
        if ok and path:
            if os.path.isfile(path):
                reply = QtWidgets.QMessageBox.question(
                    self,
                    _("Save Log View to File"),
                    _("File already exists, do you really want to save to this file?"),
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                )
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return

            writer = QtGui.QTextDocumentWriter(path)
            writer.setFormat(b'plaintext')
            success = writer.write(self.doc)
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    _("Failed to save Log View to file"),
                    _("Something prevented data to be written to '%s'") % writer.fileName(),
                )

    def show(self):
        self.highlight_text.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
        super().show()

    def display(self, clear=False):
        if clear:
            self._prev_logitem_level = logging.NOTSET
        super().display(clear=clear)

    def _clear_log_do(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            _("Clear Log"),
            _("Are you sure you want to clear the log?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.log_tail.clear()
        self.display(clear=True)

    def is_shown(self, logitem):
        return logitem.level >= self.verbosity

    def _add_entry(self, logitem):
        if not self.is_shown(logitem):
            return
        if self._prev_logitem_level != logitem.level:
            self.textCursor.setBlockCharFormat(self._format(logitem.level))
            self._prev_logitem_level = logitem.level
        super()._add_entry(logitem)

    def _set_verbosity(self, level):
        self.verbosity = level
        self.verbosity_menu.set_verbosity(self.verbosity)
        self._update_verbosity_label()

    def _verbosity_changed(self, level):
        if level != self.verbosity:
            log.set_verbosity(level, save_to_config=True)
            self.verbosity = level
            self._update_verbosity_label()
            self.display(clear=True)

    def _update_verbosity_label(self):
        feat = log.levels_features.get(self.verbosity)
        label = _(feat.name) if feat else _("Verbosity")
        self.verbosity_menu_button.setText(label)
        self.debug_opts_menu_button.setEnabled(self.verbosity == logging.DEBUG)


class HistoryView(LogViewCommon):
    def __init__(self, parent=None):
        super().__init__(log.history_tail, _("Activity History"), parent=parent)
