# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018-2022 Laurent Monin
# Copyright (C) 2018-2023 Philipp Wolfer
# Copyright (C) 2020 Ray Bouchard
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


from collections import namedtuple

from PyQt5 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
)

from picard.config import get_config
from picard.util import (
    icontheme,
    restore_method,
)

from picard.ui.tablebaseddialog import TableBasedDialog
from picard.ui.util import StandardButton


class SearchBox(QtWidgets.QWidget):

    def __init__(self, parent, force_advanced_search=None):
        super().__init__(parent)
        self.search_action = QtWidgets.QAction(icontheme.lookup('system-search'), _("Search"), self)
        self.search_action.setEnabled(False)
        self.search_action.triggered.connect(self.search)
        if force_advanced_search is None:
            config = get_config()
            self.force_advanced_search = False
            self.use_advanced_search = config.setting["use_adv_search_syntax"]
        else:
            self.force_advanced_search = True
            self.use_advanced_search = force_advanced_search
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
        self.search_edit.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
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
        self.adv_opt_row_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.adv_opt_row_layout.setContentsMargins(1, 1, 1, 1)
        self.adv_opt_row_layout.setSpacing(1)
        self.use_adv_search_syntax = QtWidgets.QCheckBox(self.adv_opt_row_widget)
        self.use_adv_search_syntax.setText(_("Use advanced query syntax"))
        self.use_adv_search_syntax.setChecked(self.use_advanced_search)
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
        self.use_adv_search_syntax.setChecked(self.use_advanced_search)

    def update_advanced_syntax_setting(self):
        self.use_advanced_search = self.use_adv_search_syntax.isChecked()
        if not self.force_advanced_search:
            config = get_config()
            config.setting["use_adv_search_syntax"] = self.use_advanced_search

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


class SearchDialog(TableBasedDialog):
    accept_button_title = ""

    def __init__(self, parent, accept_button_title, show_search=True, search_type=None, force_advanced_search=None):
        self.accept_button_title = accept_button_title
        self.search_results = []
        self.show_search = show_search
        self.search_type = search_type
        self.force_advanced_search = force_advanced_search
        self.search_box = None
        super().__init__(parent)

    @property
    def use_advanced_search(self):
        if self.show_search:
            return self.search_box.use_advanced_search
        elif self.force_advanced_search is not None:
            return self.force_advanced_search
        else:
            config = get_config()
            return config.setting["use_adv_search_syntax"]

    def get_value_for_row_id(self, row, value):
        return row

    def setupUi(self):
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("vertical_layout")
        if self.show_search:
            self.search_box = SearchBox(self, force_advanced_search=self.force_advanced_search)
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
                QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
            self.search_browser_button.clicked.connect(self.search_browser)
        self.accept_button = QtWidgets.QPushButton(
            self.accept_button_title,
            self.buttonBox)
        self.accept_button.setEnabled(False)
        self.buttonBox.addButton(
            self.accept_button,
            QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonBox.addButton(
            StandardButton(StandardButton.CANCEL),
            QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def show_progress(self):
        progress_widget = QtWidgets.QWidget(self)
        progress_widget.setObjectName("progress_widget")
        layout = QtWidgets.QVBoxLayout(progress_widget)
        text_label = QtWidgets.QLabel(_('<strong>Loading…</strong>'), progress_widget)
        text_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom)
        gif_label = QtWidgets.QLabel(progress_widget)
        movie = QtGui.QMovie(":/images/loader.gif")
        gif_label.setMovie(movie)
        movie.start()
        gif_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(text_label)
        layout.addWidget(gif_label)
        layout.setContentsMargins(1, 1, 1, 1)
        progress_widget.setLayout(layout)
        self.add_widget_to_center_layout(progress_widget)

    def show_error(self, error, show_retry_button=False):
        """Display the error string.

        Args:
            error -- Error string
            show_retry_button -- Whether to display retry button or not
        """
        error_widget = QtWidgets.QWidget(self)
        error_widget.setObjectName("error_widget")
        layout = QtWidgets.QVBoxLayout(error_widget)
        error_label = QtWidgets.QLabel(error, error_widget)
        error_label.setWordWrap(True)
        error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        error_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(error_label)
        if show_retry_button:
            retry_widget = QtWidgets.QWidget(error_widget)
            retry_layout = QtWidgets.QHBoxLayout(retry_widget)
            retry_button = QtWidgets.QPushButton(_("Retry"), error_widget)
            retry_button.clicked.connect(self.retry)
            retry_button.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed))
            retry_layout.addWidget(retry_button)
            retry_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
            retry_widget.setLayout(retry_layout)
            layout.addWidget(retry_widget)
        error_widget.setLayout(layout)
        self.add_widget_to_center_layout(error_widget)

    def network_error(self, reply, error):
        params = {
            'url': reply.request().url().toString(QtCore.QUrl.UrlFormattingOption.RemoveUserInfo),
            'error': reply.errorString(),
            'qtcode': error,
            'statuscode': reply.attribute(
                QtNetwork.QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        }
        error_msg = _("<strong>Following error occurred while fetching results:<br><br></strong>"
                      "Network request error for %(url)s:<br>%(error)s (QT code %(qtcode)d, HTTP code %(statuscode)r)<br>") % params
        self.show_error(error_msg, show_retry_button=True)

    def no_results_found(self):
        error_msg = _("<strong>No results found. Please try a different search query.</strong>")
        self.show_error(error_msg)

    def search_browser(self):
        self.tagger.search(self.search_box.query, self.search_type,
                           adv=self.use_advanced_search, force_browser=True)

    @restore_method
    def restore_state(self):
        super().restore_state()
        if self.show_search:
            self.search_box.restore_checkbox_state()

    def search_box_text(self, text):
        if self.search_box:
            self.search_box.query = text
