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
from picard.util import reconnect

from picard.ui import (
    FONT_FAMILY_MONOSPACE,
    PicardDialog,
)
from picard.ui.logviewmodel import (
    FullTextRole,
    LogFilterProxyModel,
    LogItemDelegate,
    LogItemModel,
)
from picard.ui.util import FileDialog


class LogViewDialog(PicardDialog):
    defaultsize = QtCore.QSize(570, 400)

    def __init__(self, title, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setWindowTitle(title)
        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox)
        self.list_view = QtWidgets.QListView()
        self.list_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_view.setFont(QtGui.QFont(FONT_FAMILY_MONOSPACE))
        self.list_view.setWordWrap(False)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu)
        self.vbox.addWidget(self.list_view)

        view_detail_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-properties"), _("&View detail…"), self.list_view
        )
        view_detail_action.triggered.connect(self._show_detail)
        self.list_view.addAction(view_detail_action)

        copy_action = QtGui.QAction(QtGui.QIcon.fromTheme("edit-copy"), _("&Copy"), self.list_view)
        copy_action.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._copy_selection)
        self.list_view.addAction(copy_action)

        select_all_action = QtGui.QAction(QtGui.QIcon.fromTheme("edit-select-all"), _("Select &all"), self.list_view)
        select_all_action.setShortcut(QtGui.QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._select_all)
        self.list_view.addAction(select_all_action)

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self.list_view)
        for action in self.list_view.actions():
            menu.addAction(action)
        menu.exec(self.list_view.viewport().mapToGlobal(pos))

    def _get_selected_text(self):
        indexes = self.list_view.selectionModel().selectedIndexes()
        if not indexes:
            return None
        indexes.sort(key=lambda idx: idx.row())
        return '\n'.join(idx.data(FullTextRole) or '' for idx in indexes)

    def _copy_selection(self):
        text = self._get_selected_text()
        if text:
            QtWidgets.QApplication.clipboard().setText(text)

    def _select_all(self):
        self.list_view.selectAll()

    def _show_detail(self):
        text = self._get_selected_text()
        if not text:
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(_("Log Detail"))
        dlg.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(dlg)
        text_edit = QtWidgets.QPlainTextEdit(dlg)
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
        text_edit.setFont(self.list_view.font())
        text_edit.setPlainText(text)
        layout.addWidget(text_edit)
        dlg.show()


class LogViewCommon(LogViewDialog):
    _UPDATE_INTERVAL_MS = 100

    def __init__(self, log_tail, title, parent=None):
        super().__init__(title, parent=parent)
        self.log_tail = log_tail
        self._model = LogItemModel(log_tail, parent=self)
        self.list_view.setModel(self._model)
        self._following_tail = True
        self._inhibit_scroll_tracking = False
        self.list_view.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.setInterval(self._UPDATE_INTERVAL_MS)
        self._update_timer.timeout.connect(self._flush_updates)

    def _on_scroll(self):
        if self._inhibit_scroll_tracking:
            return
        sb = self.list_view.verticalScrollBar()
        self._following_tail = sb.value() >= sb.maximum() - 1

    def closeEvent(self, event):
        self.save_geometry()
        event.ignore()
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._following_tail:
            self._scroll_to_bottom()

    def hideEvent(self, event):
        reconnect(self.log_tail.updated, None)
        self._update_timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        self._model.append_from_tail()
        self._scroll_to_bottom()
        # Disconnect any previous handler, then reconnect with an explicit
        # QueuedConnection: the signal is emitted from background logging
        # threads and the slot updates the UI, so it must be queued.
        reconnect(self.log_tail.updated, None)
        self.log_tail.updated.connect(self._updated, QtCore.Qt.ConnectionType.QueuedConnection)
        super().showEvent(event)

    def _updated(self):
        if not self._update_timer.isActive():
            self._update_timer.start()

    def _flush_updates(self):
        self._update_timer.stop()
        self._model.append_from_tail()
        if self._following_tail:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        self._inhibit_scroll_tracking = True
        self.list_view.scrollToBottom()
        self._inhibit_scroll_tracking = False

    def clear(self):
        self.log_tail.clear()
        self._model.clear_entries()

    def get_all_text(self):
        """Return all log messages as plain text."""
        return self._model.get_all_text()


class VerbosityMenu(QtWidgets.QMenu):
    verbosity_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.action_group = QtGui.QActionGroup(self)
        self.action_map = {}
        for level, feat in log.levels_features.items():
            action = QtGui.QAction(_(feat.name), self)
            action.setCheckable(True)
            action.triggered.connect(partial(self.verbosity_changed.emit, level))
            self.action_group.addAction(action)
            self.addAction(action)
            self.action_map[level] = action

    def set_verbosity(self, level):
        self.action_map[level].setChecked(True)


class DebugOptsMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.action_map = {}
        for debug_opt in DebugOpt:
            action = QtGui.QAction(_(debug_opt.title), self, checkable=True, checked=debug_opt.enabled)
            action.setToolTip(_(debug_opt.description))
            action.triggered.connect(partial(self.debug_opt_changed, debug_opt))
            self.addAction(action)
            self.action_map[debug_opt] = action

    def debug_opt_changed(self, debug_opt, checked):
        debug_opt.enabled = checked

    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action and action.isCheckable():
            action.trigger()
            return
        super().mouseReleaseEvent(event)


class LogView(LogViewCommon):
    def __init__(self, parent=None):
        super().__init__(log.main_tail, _("Log"), parent=parent)
        self.verbosity = log.get_effective_level()
        self._status_label = None

        # Set up proxy model for level filtering
        self._proxy_model = LogFilterProxyModel(parent=self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.set_min_level(self.verbosity)
        self.list_view.setModel(self._proxy_model)

        self._delegate = LogItemDelegate(parent=self.list_view)
        self.list_view.setItemDelegate(self._delegate)

        clear_log_action = QtGui.QAction(QtGui.QIcon.fromTheme("edit-clear"), _("Clear &log…"), self.list_view)
        clear_log_action.triggered.connect(self._clear_log_do)
        self.list_view.addAction(clear_log_action)

        self._regex_action = QtGui.QAction(_("&Regex filter"), self.list_view)
        self._regex_action.setCheckable(True)
        self._regex_action.toggled.connect(self._on_regex_toggled)
        self.list_view.addAction(self._regex_action)

        self._compact_view_action = QtGui.QAction(_("&Compact view"), self.list_view)
        self._compact_view_action.setCheckable(True)
        self._compact_view_action.setChecked(False)
        self._compact_view_action.toggled.connect(self._on_compact_view_toggled)
        self.list_view.addAction(self._compact_view_action)

        self.hbox = QtWidgets.QHBoxLayout()
        self.vbox.addLayout(self.hbox)

        self.verbosity_menu_button = QtWidgets.QPushButton()
        self.verbosity_menu_button.setAutoDefault(False)
        self.verbosity_menu_button.setAccessibleName(_("Verbosity"))
        self.verbosity_menu_button.setToolTip(
            _(
                "Changes the logging verbosity level for the current session. "
                "The default level configured in Options will be restored on next startup."
            )
        )
        self.hbox.addWidget(self.verbosity_menu_button)

        self.verbosity_menu = VerbosityMenu()
        self.verbosity_menu.verbosity_changed.connect(self._verbosity_changed)
        self.verbosity_menu_button.setMenu(self.verbosity_menu)

        self.debug_opts_menu_button = QtWidgets.QPushButton(_("Debug Options"))
        self.debug_opts_menu_button.setAutoDefault(False)
        self.debug_opts_menu_button.setAccessibleName(_("Debug Options"))
        self.hbox.addWidget(self.debug_opts_menu_button)

        self.debug_opts_menu = DebugOptsMenu()
        self.debug_opts_menu_button.setMenu(self.debug_opts_menu)

        self._set_verbosity(self.verbosity)

        # filter input with embedded clear button
        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setPlaceholderText(_("Filter"))
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        self.filter_input.returnPressed.connect(self._on_filter_return)
        self.hbox.addWidget(self.filter_input)

        # filter toggle button
        self.filter_button = QtWidgets.QToolButton()
        self.filter_button.setText(_("Filter"))
        self.filter_button.setCheckable(True)
        self.filter_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.filter_button.toggled.connect(self._on_filter_toggled)
        self.hbox.addWidget(self.filter_button)

        # save as
        self.save_log_as_button = QtWidgets.QPushButton(_("Save As…"))
        self.save_log_as_button.setAutoDefault(False)
        self.hbox.addWidget(self.save_log_as_button)
        self.save_log_as_button.clicked.connect(self._save_log_as_do)

        # line count status
        self.hbox.addStretch()
        self._status_label = QtWidgets.QLabel()
        self.hbox.addWidget(self._status_label)
        self._model.rowsInserted.connect(self._update_status)
        self._model.modelReset.connect(self._update_status)
        self._update_status()

    def _update_status(self):
        if self._status_label is None:
            return
        visible = self._proxy_model.rowCount()
        total = self._model.rowCount()
        if visible == total:
            self._status_label.setText(str(total))
        else:
            self._status_label.setText(f"{visible}/{total}")

    def _on_filter_changed(self, text):
        if self.filter_button.isChecked():
            self._apply_filter()

    def _on_filter_return(self):
        if self.filter_input.text():
            self.filter_button.setChecked(not self.filter_button.isChecked())

    def _on_filter_toggled(self, checked):
        self._apply_filter()

    def _on_regex_toggled(self, checked):
        if self.filter_button.isChecked():
            self._apply_filter()

    def _on_compact_view_toggled(self, checked):
        self._model.compact_view = checked

    def _apply_filter(self):
        text = self.filter_input.text()
        if self.filter_button.isChecked() and text:
            try:
                if self._regex_action.isChecked():
                    hl_re = re.compile(text, re.IGNORECASE)
                else:
                    hl_re = re.compile(re.escape(text), re.IGNORECASE)
            except re.error:
                hl_re = None
        else:
            hl_re = None
        self._delegate.set_highlight(hl_re)
        self._inhibit_scroll_tracking = True
        self._proxy_model.set_text_filter(hl_re)
        if self._following_tail:
            QtCore.QTimer.singleShot(0, self._deferred_scroll_to_bottom)
        else:
            self._inhibit_scroll_tracking = False
        self.list_view.viewport().update()
        self._update_status()

    def _save_log_as_do(self):
        path, ok = FileDialog.getSaveFileName(
            parent=self,
            caption=_("Save Log View to File"),
            filter=_("Text files (*.txt);;All files (*)"),
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

            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.get_all_text())
            except OSError:
                QtWidgets.QMessageBox.critical(
                    self,
                    _("Failed to save Log View to file"),
                    _('Something prevented data to be written to "%s".') % path,
                )

    def show(self):
        self.filter_input.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
        super().show()

    def _clear_log_do(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            _("Clear Log"),
            _("Are you sure you want to clear the log?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.clear()

    def _deferred_scroll_to_bottom(self):
        self._scroll_to_bottom()
        self._inhibit_scroll_tracking = False

    def _set_verbosity(self, level):
        self.verbosity = level
        self._inhibit_scroll_tracking = True
        self._proxy_model.set_min_level(level)
        if self._following_tail:
            QtCore.QTimer.singleShot(0, self._deferred_scroll_to_bottom)
        else:
            self._inhibit_scroll_tracking = False
        self.verbosity_menu.set_verbosity(self.verbosity)
        self._update_verbosity_label()
        self._update_status()

    def _verbosity_changed(self, level):
        if level != self.verbosity:
            log.set_verbosity(level)
            self._set_verbosity(level)

    def _update_verbosity_label(self):
        feat = log.levels_features.get(self.verbosity)
        label = _(feat.name) if feat else _("Verbosity")
        self.verbosity_menu_button.setText(label)
        self.debug_opts_menu_button.setEnabled(self.verbosity == logging.DEBUG)


class HistoryView(LogViewCommon):
    def __init__(self, parent=None):
        super().__init__(log.history_tail, _("Activity History"), parent=parent)
