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


class Track(object):

    def __init__(self, **kwargs):
        self.id = kwargs.get("track_id")
        self.release_id = kwargs.get("release_id")
        self.rg_id = kwargs.get("rg_id")
        self.title = kwargs.get("title")
        self.length = kwargs.get("length")
        self.release = kwargs.get("release")
        self.artist = kwargs.get("artist")
        self.date = kwargs.get("date")
        self.country = kwargs.get("country")
        self.release_type = kwargs.get("release_type")


class ResultTable(QtGui.QTableWidget):

    def __init__(self, column_titles):
        QtGui.QTableWidget.__init__(self, 0, len(column_titles))
        self.setHorizontalHeaderLabels(column_titles)
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
        self.parent.search(self.search_edit.text())


class SearchDialog(PicardDialog):

    options = [
        config.Option("persist", "searchdialog_window_size", QtCore.QSize(720, 360)),
        config.Option("persist", "searchdialog_header_state", QtCore.QByteArray())
    ]

    def __init__(self, parent=None):
        PicardDialog.__init__(self, parent)
        self.search_results = []
        self.setupUi()
        self.restore_window_state()

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

    def show_error(self, error):
        self.error_widget = QtGui.QLabel(_("<strong>" + error + "</strong>"))
        self.error_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.error_widget.setWordWrap(True)
        self.add_widget_to_center_layout(self.error_widget)

    def row_double_clicked(self, row):
        self.load_selection(row)
        self.accept()

    def accept(self):
        try:
            sel_rows = self.table.selectionModel().selectedRows()
            if sel_rows:
                sel_row = sel_rows[0].row()
                self.load_selection(sel_row)
            self.save_state(True)
        except AttributeError:
            self.save_state(False)

        QtGui.QDialog.accept(self)

    def restore_window_state(self):
        size = config.persist["searchdialog_window_size"]
        if size:
            self.resize(size)

    def restore_table_header_state(self):
        header = self.table.horizontalHeader()
        state = config.persist["searchdialog_header_state"]
        if state:
            header.restoreState(state)
        header.setResizeMode(QtGui.QHeaderView.Interactive)

    def save_state(self, table_loaded=True):
        if table_loaded:
            header = self.table.horizontalHeader()
            config.persist["searchdialog_header_state"] = header.saveState()
        config.persist["searchdialog_window_size"] = self.size()


class TrackSearchDialog(SearchDialog):

    def __init__(self, parent):
        super(TrackSearchDialog, self).__init__(parent)
        self.file_ = None
        self.setWindowTitle(_("Track Search Results"))
        self.table_headers = [
                _("Name"),
                _("Length"),
                _("Artist"),
                _("Release"),
                _("Date"),
                _("Country"),
                _("Type")
        ]

    def search(self, text):
        self.show_progress()
        self.tagger.xmlws.find_tracks(self.handle_reply,
                track=text,
                search=True,
                limit=25)

    def load_similar_tracks(self, file_):
        self.file_ = file_
        metadata = file_.orig_metadata
        self.show_progress()
        self.tagger.xmlws.find_tracks(
                self.handle_reply,
                track=metadata['title'],
                artist=metadata['artist'],
                release=metadata['tracknumber'],
                tnum=metadata['totaltracks'],
                tracks=metadata['totaltracks'],
                qdur=str(metadata.length / 2000),
                isrc=metadata['isrc'],
                limit=25)

    def handle_reply(self, document, http, error):
        if error:
            error_msg = _("Unable to fetch results. Close the dialog and try "
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
            tmp = sorted((self.file_.orig_metadata.compare_to_track(
                track, File.comparison_weights) for track in tracks),
                reverse=True,
                key=itemgetter(0))
            tracks = [item[3] for item in tmp]

        del self.search_results[:]  # Clear existing data
        self.parse_tracks_from_xml(tracks)
        self.display_results()

    def show_table(self):
        self.table = ResultTable(self.table_headers)
        self.table.cellDoubleClicked.connect(self.row_double_clicked)
        self.restore_table_header_state()
        self.add_widget_to_center_layout(self.table)

    def display_results(self):
        self.show_table()
        for row, obj in enumerate(self.search_results):
            track = obj[0]
            table_item = QtGui.QTableWidgetItem
            self.table.insertRow(row)
            self.table.setItem(row, 0, table_item(track.title))
            self.table.setItem(row, 1, table_item(track.length))
            self.table.setItem(row, 2, table_item(track.artist))
            self.table.setItem(row, 3, table_item(track.release))
            self.table.setItem(row, 4, table_item(track.date))
            self.table.setItem(row, 5, table_item(track.country))
            self.table.setItem(row, 6, table_item(track.release_type))

    def parse_tracks_from_xml(self, tracks_xml):
        for node in tracks_xml:
            rec_id = node.id
            rec_title = node.title[0].text
            artist = artist_credit_from_node(node.artist_credit[0])[0]
            try:
                length = format_time(node.length[0].text)
            except AttributeError:
                length = ""
            try:
                releases = node.release_list[0].release
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

                    track = Track(
                            id=rec_id,
                            release_id=rel_id,
                            rg_id=rg_id,
                            title=rec_title,
                            artist=artist,
                            length=length,
                            release=rel_title,
                            date=date,
                            country=country,
                            release_type=types)
                    self.search_results.append((track, node))

            except AttributeError:
                track = Track(
                        id=rec_id,
                        artist=artist,
                        length=length,
                        title=rec_title,
                        release="(Standalone Recording)")
                self.search_results.append((track, node))

    def load_selection(self, row=None):
        track, node = self.search_results[row]
        if track.release_id:
        # The track is not an NAT
            self.tagger.get_release_group_by_id(track.rg_id).loaded_albums.add(
                    track.release_id)
            if self.file_:
            # Search is performed for a file
            # Have to move that file from its existing album to the new one
                if type(self.file_.parent).__name__ == "Track":
                    album = self.file_.parent.album
                    self.tagger.move_file_to_track(self.file_, track.release_id, track.id)
                    if album._files == 0:
                        # Remove album if it has no more files associated
                        self.tagger.remove_album(album)
                else:
                    self.tagger.move_file_to_track(self.file_, track.release_id, track.id)
            else:
            # No files associated. Just a normal search.
                self.tagger.load_album(track.release_id)
        else:
        # The track is an NAT
            if self.file_:
                album = self.file_.parent.album
                self.tagger.move_file_to_nat(track.id)
                if album._files == 0:
                    self.tagger.remove_album(album)
            else:
                self.tagger.load_nat(track.id, node)
