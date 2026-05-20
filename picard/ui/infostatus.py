# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2019, 2021-2022 Philipp Wolfer
# Copyright (C) 2021 Gabriel Ferreira
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


import time

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _
from picard.util import icontheme
from picard.util.time import get_timestamp

from picard.ui.forms.ui_infostatus import Ui_InfoStatus


class InfoStatus(QtWidgets.QWidget, Ui_InfoStatus):
    stop_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        Ui_InfoStatus.__init__(self)
        self.setupUi(self)

        self._size = QtCore.QSize(16, 16)
        self._create_icons()
        self._init_labels()
        self._init_stop_button()

        self.reset_counters()

    def _init_labels(self):
        size = self._size
        self.eta_icon.setPixmap(self.icon_eta.pixmap(size))
        self.eta_icon.hide()
        self.files_icon.setPixmap(self.icon_file.pixmap(size))
        self.albums_icon.setPixmap(self.icon_cd.pixmap(size))
        self.pending_files_icon.setPixmap(self.icon_file_pending.pixmap(size))
        self.pending_requests_icon.setPixmap(self.icon_download.pixmap(size, QtGui.QIcon.Mode.Disabled))
        self._init_tooltips()

    def _init_stop_button(self):
        self.stop_button.setFixedSize(16, 16)
        self.stop_button.setIconSize(self._size)
        self.stop_button.setIcon(self.stop_button.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserStop))
        self.stop_button.setEnabled(False)
        self.stop_button.setToolTip(_("Stop all pending network requests"))
        self.stop_button.clicked.connect(self.stop_requested.emit)

    def _create_icons(self):
        self.icon_eta = QtGui.QIcon(":/images/22x22/hourglass.png")
        self.icon_cd = icontheme.lookup('media-optical')
        self.icon_file = QtGui.QIcon(":/images/file.png")
        self.icon_file_pending = QtGui.QIcon(":/images/file-pending.png")
        self.icon_download = QtGui.QIcon(":/images/16x16/action-go-down-16.png")

    def _init_tooltips(self):
        t1 = _("Estimated Time")
        t2 = _("Files")
        t3 = _("Albums")
        t4 = _("Pending files")
        t5 = _("Pending requests")
        self.eta_value.setToolTip(t1)
        self.eta_icon.setToolTip(t1)
        self.files_value.setToolTip(t2)
        self.files_icon.setToolTip(t2)
        self.albums_value.setToolTip(t3)
        self.albums_icon.setToolTip(t3)
        self.pending_files_value.setToolTip(t4)
        self.pending_files_icon.setToolTip(t4)
        self.pending_requests_value.setToolTip(t5)
        self.pending_requests_icon.setToolTip(t5)

    def update(self, progress_status):
        self.set_files(progress_status.files)
        self.set_albums(progress_status.albums)
        self.set_pending_files(progress_status.pending_files)
        self.set_pending_requests(progress_status.pending_requests)

        # estimate eta
        total_pending = progress_status.pending_files + progress_status.pending_requests
        last_pending = self._last_pending_files + self._last_pending_requests

        # Reset the counters if we had no pending progress before and receive new pending items.
        # This resets the starting timestamp and starts a new round of measurement.
        if total_pending > 0 and last_pending == 0:
            self.reset_counters()

        previous_done_files = max(0, self._max_pending_files - self._last_pending_files)
        previous_done_requests = max(0, self._max_pending_requests - self._last_pending_requests)
        self._max_pending_files = max(self._max_pending_files, previous_done_files + progress_status.pending_files)
        self._max_pending_requests = max(
            self._max_pending_requests, previous_done_requests + progress_status.pending_requests
        )
        self._last_pending_files = progress_status.pending_files
        self._last_pending_requests = progress_status.pending_requests

        if total_pending == 0 or (self._max_pending_files + self._max_pending_requests <= 1):
            self.reset_counters()
            self.hide_eta()
            return

        if total_pending != last_pending:
            current_time = time.time()

            # time since we started processing this batch
            diff_time = max(0.1, current_time - self._prev_time)  # denominator can't be 0
            previous_done_files = max(1, previous_done_files)  # denominator can't be 0

            # we estimate based on the time per file * number of pending files + 1 second per additional request
            file_eta_seconds = (
                diff_time / previous_done_files
            ) * progress_status.pending_files + progress_status.pending_requests

            # we assume additional network requests based on the ratio of requests/files * pending files
            # to estimate an upper bound (e.g. fetch cover, lookup, scan)
            network_eta_seconds = (
                progress_status.pending_requests
                + (previous_done_requests / previous_done_files) * progress_status.pending_files
            )

            # general eta (biased towards whatever takes longer)
            eta_seconds = max(network_eta_seconds, file_eta_seconds)

            # estimate progress
            self._last_progress = diff_time / (diff_time + eta_seconds)
            self.set_eta(eta_seconds)

    def reset_counters(self):
        self._last_progress = 0
        self._max_pending_requests = 0
        self._last_pending_requests = 0
        self._max_pending_files = 0
        self._last_pending_files = 0
        self._prev_time = time.time()

    def get_progress(self):
        return self._last_progress

    def set_eta(self, eta_seconds):
        if eta_seconds > 0:
            self.eta_value.setText(get_timestamp(eta_seconds))
            self.eta_value.show()
            self.eta_icon.show()
        else:
            self.hide_eta()

    def hide_eta(self):
        self.eta_value.hide()
        self.eta_icon.hide()

    def set_files(self, num):
        self.files_value.setText(str(num))

    def set_albums(self, num):
        self.albums_value.setText(str(num))

    def set_pending_files(self, num):
        self.pending_files_value.setText(str(num))

    def set_pending_requests(self, num):
        has_requests = num > 0
        if has_requests:
            mode = QtGui.QIcon.Mode.Normal
        else:
            mode = QtGui.QIcon.Mode.Disabled
        self.pending_requests_icon.setPixmap(self.icon_download.pixmap(self._size, mode))
        self.stop_button.setEnabled(has_requests)
        self.pending_requests_value.setText(str(num))
