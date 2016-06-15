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
from picard.ui.util import StandardButton
from picard.util import format_time
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

    def search(self, query):
        self.show_progress()
        self.tagger.xmlws.find_tracks(self.handle_reply,
                track=query,
                dismax="true",
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

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.addButton(
                StandardButton(StandardButton.OK),
                QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(
                StandardButton(StandardButton.CANCEL),
                QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.track_selected)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def show_progress(self):
        self.label = QtGui.QLabel('Loading....')
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.insertWidget(0, self.label)

    def show_table(self):
        self.tracksTable = TracksTable()
        self.tracksTable.cellDoubleClicked.connect(self.track_double_clicked)
        self.verticalLayout.removeWidget(self.label)
        self.verticalLayout.insertWidget(0, self.tracksTable)
        self.restore_table_header_state()

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
        self.save_state()
        self.closeEvent()

    def track_double_clicked(self, row):
        self.load_selection(row)

    def track_selected(self):
        sel_rows = self.tracksTable.selectionModel().selectedRows()
        if sel_rows:
            sel_row = sel_rows[0].row()
            self.load_selection(sel_row)
        else:
            self.closeEvent()

    def closeEvent(self, event=None):
        self.save_state()
        self.accept()

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
        try:
            tracks = document.metadata[0].recording_list[0].recording
        except (AttributeError, IndexError):
            # No results to show
            # To be done: Notify user about that, or just close the dialog
            return

        if self.file_:
            tmp = sorted((self.file_.orig_metadata.compare_to_track(track,
                File.comparison_weights) for track in tracks), reverse=True,
                key=itemgetter(0))
            tracks = [item[3] for item in tmp]

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

    def save_state(self):
        header = self.tracksTable.horizontalHeader()
        config.persist["searchdialog_header_state"] = header.saveState()
        config.persist["searchdialog_window_size"] = self.size()
