# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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

from PyQt4 import QtGui, QtCore
from operator import itemgetter
from functools import partial
from picard import config
from picard.file import File
from picard.ui import PicardDialog
from picard.ui.util import StandardButton, ButtonLineEdit
from picard.util import format_time, icontheme
from picard.mbxml import artist_credit_from_node


class TracksTable(QtGui.QTableWidget):

    def __init__(self, parent=None):
        QtGui.QTableWidget.__init__(self, 0, 7)
        self.setHorizontalHeaderLabels([_("Name"), _("Length"),
            _("Artist"), _("Release"), _("Date"), _("Country"), _("Type")])

        self.setSelectionMode(
                QtGui.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(
                QtGui.QAbstractItemView.SelectRows)
        self.setEditTriggers(
                QtGui.QAbstractItemView.NoEditTriggers)

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(
                QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(
                QtGui.QHeaderView.Interactive)


class SearchBox(QtGui.QWidget):

    def __init__(self, parent):
        self.parent = parent
        QtGui.QWidget.__init__(self, parent)
        self.search_action = QtGui.QAction(icontheme.lookup('system-search'),
                _(u"Search"), self)
        self.search_action.triggered.connect(self.search)
        self.setupUi()

    def setupUi(self):
        self.setMaximumHeight(35)
        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(1)
        layout.setSpacing(1)
        self.search_edit = ButtonLineEdit(self)
        layout.addWidget(self.search_edit)
        self.search_button = QtGui.QToolButton(self)
        self.search_button.setAutoRaise(True)
        self.search_button.setDefaultAction(self.search_action)
        self.search_button.setIconSize(QtCore.QSize(22, 22))
        layout.addWidget(self.search_button)
        self.setLayout(layout)

    def search(self):
        text = self.search_edit.text()
        self.parent.search(text)


class SearchDialog(PicardDialog):

    options = [
        config.Option("persist", "searchdialog_window_size", QtCore.QSize(720, 360)),
        config.Option("persist", "searchdialog_header_state", QtCore.QByteArray())
    ]

    def __init__(self, parent=None):
        PicardDialog.__init__(self, parent)
        self.setObjectName(_("SearchDialog"))
        self.setWindowTitle(_("Track Search Results"))
        self.file_ = None
        self.search_results = []
        self.setupUi()
        self.restore_window_state()

    def search(self, text):
        self.show_progress()
        self.tagger.xmlws.find_tracks(self.handle_reply,
                query=text,
                dismax=True,
                search=True,
                adv=config.setting["use_adv_search_syntax"],
                limit=25)

    def load_similar_tracks(self, file_):
        self.file_ = file_
        metadata = file_.orig_metadata
        self.show_progress()
        self.tagger.xmlws.find_tracks(self.handle_reply,
                track=metadata['title'],
                artist=metadata['artist'],
                release=metadata['tracknumber'],
                tnum=metadata['totaltracks'],
                tracks=metadata['totaltracks'],
                qdur=str(metadata.length / 2000),
                isrc=metadata['isrc'],
                limit=25)

    def setupUi(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_("verticalLayout"))

        self.search_box = SearchBox(self)
        self.verticalLayout.addWidget(self.search_box)
        self.center_widget = QtGui.QWidget(self)
        self.center_layout = QtGui.QVBoxLayout(self.center_widget)
        self.center_widget.setLayout(self.center_layout)
        self.verticalLayout.addWidget(self.center_widget)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.addButton(
                StandardButton(StandardButton.OK),
                QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(
                StandardButton(StandardButton.CANCEL),
                QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def add_widget_to_center_layout(self, widget):
        wid = self.center_layout.itemAt(0)
        if wid:
            wid.widget().deleteLater()
        self.center_layout.addWidget(widget)

    def show_progress(self):
        self.progress_widget = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout(self.progress_widget)
        text_label = QtGui.QLabel('<strong>Fetching results...</strong>', self.progress_widget)
        text_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        gif_label = QtGui.QLabel(self.progress_widget)
        movie = QtGui.QMovie(":/images/loader.gif")
        gif_label.setMovie(movie)
        movie.start()
        gif_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        layout.addWidget(text_label)
        layout.addWidget(gif_label)
        layout.setMargin(1)
        self.progress_widget.setLayout(layout)
        self.add_widget_to_center_layout(self.progress_widget)

    def show_table(self):
        self.tracksTable = TracksTable()
        self.tracksTable.cellDoubleClicked.connect(self.track_double_clicked)
        self.restore_table_header_state()
        self.add_widget_to_center_layout(self.tracksTable)

    def show_error(self, error):
        self.error_widget = QtGui.QLabel(_("<strong>" + error + "</strong>"))
        self.error_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.error_widget.setWordWrap(True)
        self.add_widget_to_center_layout(self.error_widget)

    def load_selection(self, row=None):
        track_id, release_id, rg_id = self.search_results[row][:3]
        if release_id:
            self.tagger.get_release_group_by_id(rg_id).loaded_albums.add(
                    release_id)
            if self.file_:
                album = self.file_.parent.album
                self.tagger.move_file_to_track(self.file_, release_id, track_id)
                if album._files == 0:
                    # Remove album if the selected file was the only one in album
                    # Compared to 0 because file has already moved to another album
                    # by move_file_to_track
                    self.tagger.remove_album(album)
            else:
                self.tagger.load_album(release_id)

    def track_double_clicked(self, row):
        self.load_selection(row)
        self.accept()

    def accept(self):
        try:
            sel_rows = self.tracksTable.selectionModel().selectedRows()
            if sel_rows:
                sel_row = sel_rows[0].row()
                self.load_selection(sel_row)
            self.save_state(True)
            QtGui.QDialog.accept(self)
        except AttributeError:
            self.save_state(False)
            QtGui.QDialog.accept(self)

    def parse_tracks(self, tracks):
        for track in tracks:
            rec_id = track.id
            rec_title = track.title[0].text
            artist = artist_credit_from_node(track.artist_credit[0])[0]
            try:
                length = format_time(track.length[0].text)
            except AttributeError:
                length = ""
            try:
                releases = track.release_list[0].release
            except AttributeError:
                pass
            if releases:
                for release in releases:
                    rel_id = release.id
                    rel_title = release.title[0].text
                    if "date" in release.children:
                        date = release.date[0].text
                    else:
                        date = None
                    if "country" in release.children:
                        country = release.country[0].text
                    else:
                        country = ""
                    rg = release.release_group[0]
                    rg_id = rg.id
                    types_list = []
                    if "primary_type" in rg.children:
                        types_list.append(rg.primary_type[0].text)
                    if "secondary_type_list" in rg.children:
                        for sec in rg.secondary_type_list:
                            types_list.append(sec.secondary_type[0].text)
                    types = "+".join(types_list)

                    result = (rec_id, rel_id, rg_id, rec_title, artist, length,
                            rel_title, date, country, types)
                    self.search_results.append(result)
            else:
                result = (rec_id, "", "", rec_title, artist, length, "", "",  "",
                        "")
                self.search_results.append(result)

    def handle_reply(self, document, http, error):
        if error:
            error_msg = _("Unable to fetch results. Close the dialog and try"
                    "again. See debug logs for more details.")
            self.show_error(error_msg)
            return

        try:
            tracks = document.metadata[0].recording_list[0].recording
        except (AttributeError, IndexError):
            error_msg = _("No results found. Please try a different search query.")
            self.show_error(error_msg)
            return

        if self.file_:
            tmp = sorted((self.file_.orig_metadata.compare_to_track(track,
                File.comparison_weights) for track in tracks), reverse=True,
                key=itemgetter(0))
            tracks = [item[3] for item in tmp]

        del self.search_results[:]  # Clear existing data
        self.parse_tracks(tracks)
        self.display_results()

    def display_results(self):
        self.show_table()
        for row, tup in enumerate(self.search_results):
            title, artist, length, release, date, country, type = tup[3:]
            table_item = QtGui.QTableWidgetItem
            self.tracksTable.insertRow(row)
            self.tracksTable.setItem(row, 0, table_item(title))
            self.tracksTable.setItem(row, 1, table_item(length))
            self.tracksTable.setItem(row, 2, table_item(artist))
            self.tracksTable.setItem(row, 3, table_item(release))
            self.tracksTable.setItem(row, 4, table_item(date))
            self.tracksTable.setItem(row, 5, table_item(country))
            self.tracksTable.setItem(row, 6, table_item(type))

    def restore_window_state(self):
        size = config.persist["searchdialog_window_size"]
        if size:
            self.resize(size)

    def restore_table_header_state(self):
        header = self.tracksTable.horizontalHeader()
        state = config.persist["searchdialog_header_state"]
        if state:
            header.restoreState(state)
        header.setResizeMode(QtGui.QHeaderView.Interactive)

    def save_state(self, table_loaded=True):
        if table_loaded:
            header = self.tracksTable.horizontalHeader()
            config.persist["searchdialog_header_state"] = header.saveState()
        config.persist["searchdialog_window_size"] = self.size()
