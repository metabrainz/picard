# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018 Laurent Monin
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

from collections import (
    OrderedDict,
    namedtuple,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
)
from PyQt5.QtCore import pyqtSignal

from picard import (
    config,
    log,
)
from picard.util import (
    icontheme,
    restore_method,
    throttle,
)

from picard.ui import PicardDialog
from picard.ui.util import (
    StandardButton,
)


class ResultTable(QtWidgets.QTableWidget):

    def __init__(self, parent, column_titles):
        super().__init__(0, len(column_titles), parent)
        self.setHorizontalHeaderLabels(column_titles)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        # only emit scrolled signal once per second

        @throttle(1000)
        def emit_scrolled(x):
            parent.scrolled.emit()
        self.horizontalScrollBar().valueChanged.connect(emit_scrolled)
        self.verticalScrollBar().valueChanged.connect(emit_scrolled)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)


class SearchBox(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.search_action = QtWidgets.QAction(icontheme.lookup('system-search'),
                                               _("Search"), self)
        self.search_action.setEnabled(False)
        self.search_action.triggered.connect(self.search)
        self.setupUi()

    def focus_in_event(self, event):
        # When focus is on search edit box, need to disable
        # dialog's accept button. This would avoid closing of dialog when user
        # hits enter.
        parent = self.parent()
        if parent.table:
            parent.table.clearSelection()
        parent.accept_button.setEnabled(False)

    def setupUi(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.search_row_widget = QtWidgets.QWidget(self)
        self.search_row_layout = QtWidgets.QHBoxLayout(self.search_row_widget)
        self.search_row_layout.setContentsMargins(1, 1, 1, 1)
        self.search_row_layout.setSpacing(1)
        self.search_edit = QtWidgets.QLineEdit(self.search_row_widget)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(self.trigger_search_action)
        self.search_edit.textChanged.connect(self.enable_search)
        self.search_edit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.search_edit.focusInEvent = self.focus_in_event
        self.search_row_layout.addWidget(self.search_edit)
        self.search_button = QtWidgets.QToolButton(self.search_row_widget)
        self.search_button.setAutoRaise(True)
        self.search_button.setDefaultAction(self.search_action)
        self.search_button.setIconSize(QtCore.QSize(22, 22))
        self.search_row_layout.addWidget(self.search_button)
        self.search_row_widget.setLayout(self.search_row_layout)
        self.layout.addWidget(self.search_row_widget)
        self.adv_opt_row_widget = QtWidgets.QWidget(self)
        self.adv_opt_row_layout = QtWidgets.QHBoxLayout(self.adv_opt_row_widget)
        self.adv_opt_row_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.adv_opt_row_layout.setContentsMargins(1, 1, 1, 1)
        self.adv_opt_row_layout.setSpacing(1)
        self.use_adv_search_syntax = QtWidgets.QCheckBox(self.adv_opt_row_widget)
        self.use_adv_search_syntax.setText(_("Use advanced query syntax"))
        self.use_adv_search_syntax.stateChanged.connect(self.update_advanced_syntax_setting)
        self.adv_opt_row_layout.addWidget(self.use_adv_search_syntax)
        self.adv_syntax_help = QtWidgets.QLabel(self.adv_opt_row_widget)
        self.adv_syntax_help.setOpenExternalLinks(True)
        self.adv_syntax_help.setText(_(
            "&#160;(<a href='https://musicbrainz.org/doc/Indexed_Search_Syntax'>"
            "Syntax Help</a>)"))
        self.adv_opt_row_layout.addWidget(self.adv_syntax_help)
        self.adv_opt_row_widget.setLayout(self.adv_opt_row_layout)
        self.layout.addWidget(self.adv_opt_row_widget)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(1)
        self.setMaximumHeight(60)

    def search(self):
        self.parent().search(self.query)

    def restore_checkbox_state(self):
        self.use_adv_search_syntax.setChecked(config.setting["use_adv_search_syntax"])

    def update_advanced_syntax_setting(self):
        config.setting["use_adv_search_syntax"] = self.use_adv_search_syntax.isChecked()

    def enable_search(self):
        if self.query:
            self.search_action.setEnabled(True)
        else:
            self.search_action.setEnabled(False)

    def trigger_search_action(self):
        if self.search_action.isEnabled():
            self.search_action.trigger()

    def get_query(self):
        return self.search_edit.text()

    def set_query(self, query):
        return self.search_edit.setText(query)

    query = property(get_query, set_query)


Retry = namedtuple("Retry", ["function", "query"])


BY_NUMBER, BY_DURATION = range(2)


class SortableTableWidgetItem(QtWidgets.QTableWidgetItem):

    def __init__(self, sort_key):
        super().__init__()
        self.sort_key = sort_key

    def __lt__(self, other):
        return self.sort_key < other.sort_key


def to_seconds(timestr):
    if not timestr:
        return 0
    seconds = 0
    for part in timestr.split(':'):
        seconds = seconds * 60 + int(part)
    return seconds


class SearchDialog(PicardDialog):

    defaultsize = QtCore.QSize(720, 360)
    autorestore = False
    scrolled = pyqtSignal()

    def __init__(self, parent, accept_button_title, show_search=True, search_type=None):
        super().__init__(parent)
        self.search_results = []
        self.table = None
        self.show_search = show_search
        self.search_type = search_type
        self.search_box = None
        self.setupUi(accept_button_title)
        self.restore_state()
        # self.columns has to be an ordered dict, with column name as keys, and
        # matching label as values
        self.columns = None
        self.sorting_enabled = True
        self.finished.connect(self.save_state)

    @property
    def columns(self):
        return self.__columns

    @columns.setter
    def columns(self, list_of_tuples):
        if not list_of_tuples:
            list_of_tuples = []
        self.__columns = OrderedDict(list_of_tuples)
        self.__colkeys = list(self.columns.keys())

    @property
    def table_headers(self):
        return list(self.columns.values())

    def colpos(self, colname):
        return self.__colkeys.index(colname)

    def set_table_item(self, row, colname, obj, key, default="", sort=None):
        # QVariant remembers the original type of the data
        # matching comparison operator will be used when sorting
        # get() will return a string, force conversion if asked to
        value = obj.get(key, default)
        if sort == BY_DURATION:
            item = SortableTableWidgetItem(to_seconds(value))
        elif sort == BY_NUMBER:
            try:
                sortkey = float(value)
            except ValueError:
                sortkey = 0.0
            item = SortableTableWidgetItem(sortkey)
        else:
            item = QtWidgets.QTableWidgetItem()
        item.setData(QtCore.Qt.DisplayRole, value)
        pos = self.colpos(colname)
        if pos == 0:
            item.setData(QtCore.Qt.UserRole, row)
        self.table.setItem(row, pos, item)

    def setupUi(self, accept_button_title):
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("vertical_layout")
        if self.show_search:
            self.search_box = SearchBox(self)
            self.search_box.setObjectName("search_box")
            self.verticalLayout.addWidget(self.search_box)
        self.center_widget = QtWidgets.QWidget(self)
        self.center_widget.setObjectName("center_widget")
        self.center_layout = QtWidgets.QVBoxLayout(self.center_widget)
        self.center_layout.setObjectName("center_layout")
        self.center_layout.setContentsMargins(1, 1, 1, 1)
        self.center_widget.setLayout(self.center_layout)
        self.verticalLayout.addWidget(self.center_widget)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        if self.show_search and self.search_type:
            self.search_browser_button = QtWidgets.QPushButton(
                _("Search in browser"), self.buttonBox)
            self.buttonBox.addButton(
                self.search_browser_button,
                QtWidgets.QDialogButtonBox.ActionRole)
            self.search_browser_button.clicked.connect(self.search_browser)
        self.accept_button = QtWidgets.QPushButton(
            accept_button_title,
            self.buttonBox)
        self.accept_button.setEnabled(False)
        self.buttonBox.addButton(
            self.accept_button,
            QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(
            StandardButton(StandardButton.CANCEL),
            QtWidgets.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def add_widget_to_center_layout(self, widget):
        """Update center widget with new child. If child widget exists,
        schedule it for deletion."""
        wid = self.center_layout.takeAt(0)
        if wid:
            if wid.widget().objectName() == "results_table":
                self.table = None
            wid.widget().deleteLater()
        self.center_layout.addWidget(widget)

    def show_progress(self):
        self.progress_widget = QtWidgets.QWidget(self)
        self.progress_widget.setObjectName("progress_widget")
        layout = QtWidgets.QVBoxLayout(self.progress_widget)
        text_label = QtWidgets.QLabel(_('<strong>Loading...</strong>'), self.progress_widget)
        text_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        gif_label = QtWidgets.QLabel(self.progress_widget)
        movie = QtGui.QMovie(":/images/loader.gif")
        gif_label.setMovie(movie)
        movie.start()
        gif_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        layout.addWidget(text_label)
        layout.addWidget(gif_label)
        layout.setContentsMargins(1, 1, 1, 1)
        self.progress_widget.setLayout(layout)
        self.add_widget_to_center_layout(self.progress_widget)

    def show_error(self, error, show_retry_button=False):
        """Display the error string.

        Args:
            error -- Error string
            show_retry_button -- Whether to display retry button or not
        """
        self.error_widget = QtWidgets.QWidget(self)
        self.error_widget.setObjectName("error_widget")
        layout = QtWidgets.QVBoxLayout(self.error_widget)
        error_label = QtWidgets.QLabel(error, self.error_widget)
        error_label.setWordWrap(True)
        error_label.setAlignment(QtCore.Qt.AlignCenter)
        error_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(error_label)
        if show_retry_button:
            retry_widget = QtWidgets.QWidget(self.error_widget)
            retry_layout = QtWidgets.QHBoxLayout(retry_widget)
            retry_button = QtWidgets.QPushButton(_("Retry"), self.error_widget)
            retry_button.clicked.connect(self.retry)
            retry_button.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed))
            retry_layout.addWidget(retry_button)
            retry_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
            retry_widget.setLayout(retry_layout)
            layout.addWidget(retry_widget)
        self.error_widget.setLayout(layout)
        self.add_widget_to_center_layout(self.error_widget)

    def prepare_table(self):
        self.table = ResultTable(self, self.table_headers)
        self.table.verticalHeader().setDefaultSectionSize(100)
        self.table.setSortingEnabled(False)
        self.table.setObjectName("results_table")
        self.table.cellDoubleClicked.connect(self.accept)
        self.restore_table_header_state()
        self.add_widget_to_center_layout(self.table)

        def enable_accept_button():
            self.accept_button.setEnabled(True)
        self.table.itemSelectionChanged.connect(
            enable_accept_button)

    def show_table(self, sort_column=None, sort_order=QtCore.Qt.DescendingOrder):
        self.table.horizontalHeader().setSortIndicatorShown(self.sorting_enabled)
        self.table.setSortingEnabled(self.sorting_enabled)
        if self.sorting_enabled and sort_column:
            self.table.sortItems(self.colpos(sort_column), sort_order)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setAlternatingRowColors(True)

    def network_error(self, reply, error):
        error_msg = _("<strong>Following error occurred while fetching results:<br><br></strong>"
                      "Network request error for %s:<br>%s (QT code %d, HTTP code %s)<br>") % (
                          reply.request().url().toString(QtCore.QUrl.RemoveUserInfo),
                          reply.errorString(),
                          error,
                          repr(reply.attribute(
                              QtNetwork.QNetworkRequest.HttpStatusCodeAttribute))
        )
        self.show_error(error_msg, show_retry_button=True)

    def no_results_found(self):
        error_msg = _("<strong>No results found. Please try a different search query.</strong>")
        self.show_error(error_msg)

    def search_browser(self):
        self.tagger.search(self.search_box.query, self.search_type,
                           adv=config.setting["use_adv_search_syntax"], force_browser=True)

    def accept(self):
        if self.table:
            idx = self.table.selectionModel().selectedRows()[0]
            row = self.table.itemFromIndex(idx).data(QtCore.Qt.UserRole)
            self.accept_event(row)
        super().accept()

    @restore_method
    def restore_state(self):
        self.restore_geometry()
        if self.show_search:
            self.search_box.restore_checkbox_state()

    @restore_method
    def restore_table_header_state(self):
        header = self.table.horizontalHeader()
        state = config.persist[self.dialog_header_state]
        if state:
            header.restoreState(state)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        log.debug("restore_state: %s" % self.dialog_header_state)

    def save_state(self):
        if self.table:
            self.save_table_header_state()

    def save_table_header_state(self):
        state = self.table.horizontalHeader().saveState()
        config.persist[self.dialog_header_state] = state
        log.debug("save_state: %s" % self.dialog_header_state)

    def search_box_text(self, text):
        if self.search_box:
            self.search_box.query = text
