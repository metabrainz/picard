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

from PyQt4 import QtGui, QtCore, QtNetwork
from operator import itemgetter
from functools import partial
from picard import config
from picard.file import File
from picard.ui import PicardDialog
from picard.ui.util import StandardButton, ButtonLineEdit
from picard.util import format_time, icontheme
from picard.mbxml import (
    recording_to_metadata,
    release_to_metadata,
    release_group_to_metadata
)
from picard.i18n import ugettext_attr
from picard.metadata import Metadata


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
        self.layout = QtGui.QVBoxLayout(self)
        self.search_row_widget = QtGui.QWidget(self)
        self.search_row_layout = QtGui.QHBoxLayout(self.search_row_widget)
        self.search_row_layout.setContentsMargins(1, 1, 1, 1)
        self.search_row_layout.setSpacing(1)
        self.search_edit = ButtonLineEdit(self.search_row_widget)
        self.search_row_layout.addWidget(self.search_edit)
        self.search_button = QtGui.QToolButton(self.search_row_widget)
        self.search_button.setAutoRaise(True)
        self.search_button.setDefaultAction(self.search_action)
        self.search_button.setIconSize(QtCore.QSize(22, 22))
        self.search_row_layout.addWidget(self.search_button)
        self.search_row_widget.setLayout(self.search_row_layout)
        self.layout.addWidget(self.search_row_widget)
        self.adv_opt_row_widget = QtGui.QWidget(self)
        self.adv_opt_row_layout = QtGui.QHBoxLayout(self.adv_opt_row_widget)
        self.adv_opt_row_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.adv_opt_row_layout.setContentsMargins(1, 1, 1, 1)
        self.adv_opt_row_layout.setSpacing(1)
        self.use_adv_search_syntax = QtGui.QCheckBox(self.adv_opt_row_widget)
        self.use_adv_search_syntax.setText(_("Use advance query syntax"))
        self.adv_opt_row_layout.addWidget(self.use_adv_search_syntax)
        self.adv_syntax_help = QtGui.QLabel(self.adv_opt_row_widget)
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
        self.parent.search(self.search_edit.text())

    def restore_checkbox_state(self):
        self.use_adv_search_syntax.setChecked(config.setting["use_adv_search_syntax"])

    def save_checkbox_state(self):
        config.setting["use_adv_search_syntax"] = self.use_adv_search_syntax.isChecked()


class SearchDialog(PicardDialog):

    options = [
        config.Option("persist", "searchdialog_window_size", QtCore.QSize(720, 360)),
        config.Option("persist", "searchdialog_header_state", QtCore.QByteArray())
    ]

    def __init__(self, parent=None):
        PicardDialog.__init__(self, parent)
        self.search_results = []
        self.setupUi()
        self.restore_state()

    def setupUi(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_("vertical_layout"))
        self.search_box = SearchBox(self)
        self.search_box.setObjectName(_("search_box"))
        self.verticalLayout.addWidget(self.search_box)
        self.center_widget = QtGui.QWidget(self)
        self.center_widget.setObjectName(_("center_widget"))
        self.center_layout = QtGui.QVBoxLayout(self.center_widget)
        self.center_layout.setObjectName(_("center_layout"))
        self.center_layout.setContentsMargins(1, 1, 1, 1)
        self.center_widget.setLayout(self.center_layout)
        self.verticalLayout.addWidget(self.center_widget)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setObjectName(_("button_box"))
        self.load_button = QtGui.QPushButton(_("Load into Picard"))
        self.load_button.setEnabled(False)
        self.buttonBox.addButton(
                self.load_button,
                QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(
                StandardButton(StandardButton.CANCEL),
                QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def add_widget_to_center_layout(self, widget):
        """Updates child widget of center_widget.

        Child widgets represent dialog's current state, like progress,
        error, and displaying fetched results.
        """

        wid = self.center_layout.itemAt(0)
        if wid:
            if wid.widget().objectName() == "results_table":
                self.table = None
            wid.widget().deleteLater()
        self.center_layout.addWidget(widget)

    def show_progress(self):
        """Displays feedback while results are being fetched from server."""

        self.progress_widget = QtGui.QWidget(self)
        self.progress_widget.setObjectName("progress_widget")
        layout = QtGui.QVBoxLayout(self.progress_widget)
        text_label = QtGui.QLabel(_('<strong>Loading...</strong>'), self.progress_widget)
        text_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        gif_label = QtGui.QLabel(self.progress_widget)
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
        """Displays error inside the dialog.

        Args:
            error -- Error string
            show_retry_button -- Whether to display retry button or not
        """

        self.error_widget = QtGui.QWidget(self)
        self.error_widget.setObjectName("error_widget")
        layout = QtGui.QVBoxLayout(self.error_widget)
        error_label = QtGui.QLabel(error)
        error_label.setWordWrap(True)
        error_label.setAlignment(QtCore.Qt.AlignCenter)
        error_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(error_label)
        if show_retry_button:
            retry_widget = QtGui.QWidget(self.error_widget)
            retry_layout = QtGui.QHBoxLayout(retry_widget)
            retry_button = QtGui.QPushButton(_("Retry"), self.error_widget)
            retry_button.clicked.connect(self.retry)
            retry_button.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed))
            retry_layout.addWidget(retry_button)
            retry_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
            retry_widget.setLayout(retry_layout)
            layout.addWidget(retry_widget)
        self.error_widget.setLayout(layout)
        self.add_widget_to_center_layout(self.error_widget)

    def show_table(self, column_headers):
        """Displays results table inside the dialog."""

        self.table = ResultTable(self.table_headers)
        self.table.setObjectName("results_table")
        self.table.cellDoubleClicked.connect(self.row_double_clicked)
        self.table.horizontalHeader().sectionResized.connect(
                self.save_table_header_state)
        self.restore_table_header_state()
        self.add_widget_to_center_layout(self.table)
        def enable_loading_button():
            self.load_button.setEnabled(True)
        self.table.itemSelectionChanged.connect(
                enable_loading_button)

    def row_double_clicked(self, row):
        """Handle function for double click event inside the table."""

        self.load_selection(row)
        self.accept()

    def network_error(self, reply, error):
        error_msg = _("<strong>Following error occurred while fetching results:<br></strong>"
                      "Network request error for %s: %s (QT code %d, HTTP code %s)<br>" % (
                          reply.request().url().toString(QtCore.QUrl.RemoveUserInfo),
                          reply.errorString(),
                          error,
                          repr(reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)))
                      )
        self.show_error(error_msg, show_retry_button=True)

    def no_results_found(self):
        error_msg = _("<strong>No results found. Please try a different search query.</strong>")
        self.show_error(error_msg)

    def accept(self):
        if getattr(self, "table", None):
            sel_rows = self.table.selectionModel().selectedRows()
            if sel_rows:
                sel_row = sel_rows[0].row()
                self.load_selection(sel_row)
            self.save_state(True)
        else:
            self.save_state(False)

        QtGui.QDialog.accept(self)

    def reject(self):
        if getattr(self, "table", None):
            self.save_state(True)
        else:
            self.save_state(False)

        QtGui.QDialog.reject(self)

    def restore_state(self):
        size = config.persist["searchdialog_window_size"]
        if size:
            self.resize(size)
        self.search_box.restore_checkbox_state()

    def restore_table_header_state(self):
        header = self.table.horizontalHeader()
        state = config.persist["searchdialog_header_state"]
        if state:
            header.restoreState(state)
        header.setResizeMode(QtGui.QHeaderView.Interactive)

    def save_state(self, table_loaded=True):
        """Saves dialog state i.e. window size, checkbox state, and table
        header size.

        Args:
            table_loaded -- Whether table widget is loaded or not
        """
        if table_loaded:
            self.save_table_header_state()
        config.persist["searchdialog_window_size"] = self.size()
        self.search_box.save_checkbox_state()

    def save_table_header_state(self):
        state = self.table.horizontalHeader().saveState()
        config.persist["searchdialog_header_state"] = state


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
        """Performs search using query provided by the user."""
        self.retry_params = (self.search, text)
        self.search_box.search_edit.setText(text)
        self.show_progress()
        self.tagger.xmlws.find_tracks(self.handle_reply,
                query=text,
                search=True,
                limit=25)

    def load_similar_tracks(self, file_):
        """Performs search by using existing metadata information
        from the file."""
        self.retry_params = (self.load_similar_tracks, file_)
        self.file_ = file_
        metadata = file_.orig_metadata
        query = {
                'track': metadata['title'],
                'artist': metadata['artist'],
                'release': metadata['album'],
                'tnum': metadata['tracknumber'],
                'tracks': metadata['totaltracks'],
                'qdur': str(metadata.length / 2000),
                'isrc': metadata['isrc'],
        }
        if config.setting["use_adv_search_syntax"]:
            # Display the query in advance syntax format.
            query_str = ' '.join(['%s:(%s)' % (item, value) for item, value in query.iteritems() if value])
        else:
            # Display only the track title
            query_str = query["track"]
        # `query_str` is used only for presenting purpose. Actual query consists of all filters and follows
        # advanced query syntax.
        query["limit"] = 25
        self.search_box.search_edit.setText(query_str)
        self.show_progress()
        self.tagger.xmlws.find_tracks(
                self.handle_reply,
                **query)

    def retry(self):
        """Retries the search using information from `retry_params`.

        `retry_params` is a tuple having search information.
        retry_params[0] -- Method to be used to perform search
                        -- Can be `self.search()` or `self.load_similar_tracks()`
        retry_params[1] -- Search query information
                        -- Can be a text string, or a File object
        """
        self.retry_params[0](self.retry_params[1])

    def handle_reply(self, document, http, error):
        if error:
            self.network_error(http, error)
            return

        try:
            tracks = document.metadata[0].recording_list[0].recording
        except (AttributeError, IndexError):
            self.no_results_found()
            return

        if self.file_:
            # Sort the results by comparing them to original metadata tags
            tmp = sorted((self.file_.orig_metadata.compare_to_track(
                track, File.comparison_weights) for track in tracks),
                reverse=True,
                key=itemgetter(0))
            tracks = [item[3] for item in tmp]

        del self.search_results[:]  # Clear existing data
        self.parse_tracks_from_xml(tracks)
        self.display_results()

    def display_results(self):
        self.show_table(self.table_headers)
        for row, obj in enumerate(self.search_results):
            track = obj[0]
            table_item = QtGui.QTableWidgetItem
            self.table.insertRow(row)
            self.table.setItem(row, 0, table_item(track.get("title", "")))
            self.table.setItem(row, 1, table_item(track.get("~length", "")))
            self.table.setItem(row, 2, table_item(track.get("artist", "")))
            self.table.setItem(row, 3, table_item(track.get("album", "")))
            self.table.setItem(row, 4, table_item(track.get("date", "")))
            self.table.setItem(row, 5, table_item(track.get("country", "")))
            self.table.setItem(row, 6, table_item(track.get("releasetype", "")))

    def parse_tracks_from_xml(self, tracks_xml):
        """Extracts track information from XmlNode objects and stores that into Metadata objects.

        Args:
            tracks_xml -- list of XmlNode objects
        """
        for node in tracks_xml:
            if "release_list" in node.children and "release" in node.release_list[0].children:
                for rel_node in node.release_list[0].release:
                    track = Metadata()
                    recording_to_metadata(node, track)
                    release_to_metadata(rel_node, track)
                    rg_node = rel_node.release_group[0]
                    release_group_to_metadata(rg_node, track)
                    if "release_event_list" in rel_node.children:
                        # Extract contries list from `release_event_list` element
                        # Don't use `country` element as it contains information of a single release
                        # event and is basically for backward compatibility.
                        country = []
                        for re in rel_node.release_event_list[0].release_event:
                            try:
                                country.append(
                                        re.area[0].iso_3166_1_code_list[0].iso_3166_1_code[0].text)
                            except AttributeError:
                                pass
                        track["country"] = ", ".join(country)
                    self.search_results.append((track, node))
            else:
                # This handles the case when no release is associated with a track
                # i.e. the track is a NAT
                track = Metadata()
                recording_to_metadata(node, track)
                track["album"] = _("Standalone Recording")
                self.search_results.append((track, node))

    def load_selection(self, row):
        """Loads album corresponding to selected track.
        If the search is performed for a file, also associates the file to
        corresponding track in the album.
        """
        track, node = self.search_results[row]
        if track.get("musicbrainz_albumid"):
        # The track is not an NAT
            self.tagger.get_release_group_by_id(track["musicbrainz_releasegroupid"]).loaded_albums.add(
                    track["musicbrainz_albumid"])
            if self.file_:
            # Search is performed for a file
            # Have to move that file from its existing album to the new one
                if type(self.file_.parent).__name__ == "Track":
                    album = self.file_.parent.album
                    self.tagger.move_file_to_track(self.file_, track["musicbrainz_albumid"], track["musicbrainz_recordingid"])
                    if album._files == 0:
                        # Remove album if it has no more files associated
                        self.tagger.remove_album(album)
                else:
                    self.tagger.move_file_to_track(self.file_, track["musicbrainz_albumid"], track["musicbrainz_recordingid"])
            else:
            # No files associated. Just a normal search.
                self.tagger.load_album(track["musicbrainz_albumid"])
        else:
        # The track is a NAT
            if self.file_:
                album = self.file_.parent.album
                self.tagger.move_file_to_nat(track["musicbrainz_recordingid"])
                if album._files == 0:
                    self.tagger.remove_album(album)
            else:
                self.tagger.load_nat(track["musicbrainz_recordingid"], node)
