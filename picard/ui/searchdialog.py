# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2016 Rahul Raturi
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

from collections import namedtuple, OrderedDict
from functools import partial
from operator import itemgetter

from PyQt5 import QtGui, QtCore, QtNetwork, QtWidgets
from PyQt5.QtCore import pyqtSignal

from picard import config, log
from picard.const import CAA_HOST, CAA_PORT, QUERY_LIMIT
from picard.coverart.image import CaaThumbnailCoverArtImage
from picard.file import File
from picard.mbjson import (
    artist_to_metadata,
    recording_to_metadata,
    release_to_metadata,
    release_group_to_metadata,
    media_formats_from_node,
    country_list_from_node
)
from picard.metadata import Metadata
from picard.track import Track
from picard.ui import PicardDialog
from picard.ui.util import StandardButton, ButtonLineEdit
from picard.util import icontheme, load_json, throttle
from picard.webservice.api_helpers import escape_lucene_query


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
        #only emit scrolled signal once per second
        @throttle(1000)
        def emit_scrolled(x):
            parent.scrolled.emit()
        self.horizontalScrollBar().valueChanged.connect(emit_scrolled)
        self.verticalScrollBar().valueChanged.connect(emit_scrolled)


class SearchBox(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.search_action = QtWidgets.QAction(icontheme.lookup('system-search'),
                                               _("Search"), self)
        self.search_action.setEnabled(False)
        self.search_action.triggered.connect(self.search)
        self.setupUi()

    def focus_in_event(self, event):
        # When focus is on search edit box (ButtonLineEdit), need to disable
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
        self.search_edit = ButtonLineEdit(self.search_row_widget)
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
        self.parent().search(self.search_edit.text())

    def restore_checkbox_state(self):
        self.use_adv_search_syntax.setChecked(config.setting["use_adv_search_syntax"])

    def update_advanced_syntax_setting(self):
        config.setting["use_adv_search_syntax"] = self.use_adv_search_syntax.isChecked()

    def enable_search(self):
        if self.search_edit.text():
            self.search_action.setEnabled(True)
        else:
            self.search_action.setEnabled(False)

    def trigger_search_action(self):
        if self.search_action.isEnabled():
            self.search_action.trigger()


class CoverWidget(QtWidgets.QWidget):

    shown = pyqtSignal()

    def __init__(self, parent, width=100, height=100):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_gif_label = QtWidgets.QLabel(self)
        self.loading_gif_label.setAlignment(QtCore.Qt.AlignCenter)
        loading_gif = QtGui.QMovie(":/images/loader.gif")
        self.loading_gif_label.setMovie(loading_gif)
        loading_gif.start()
        self.layout.addWidget(self.loading_gif_label)
        self.__sizehint = self.__size = QtCore.QSize(width, height)
        self.setStyleSheet("padding: 0")

    def set_pixmap(self, pixmap):
        wid = self.layout.takeAt(0)
        if wid:
            wid.widget().deleteLater()
        cover_label = QtWidgets.QLabel(self)
        pixmap = pixmap.scaled(self.__size, QtCore.Qt.KeepAspectRatio,
                               QtCore.Qt.SmoothTransformation)
        self.__sizehint = pixmap.size()
        cover_label.setPixmap(pixmap)
        self.layout.addWidget(cover_label)

    def not_found(self):
        """Update the widget with a blank image."""
        shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.set_pixmap(shadow)

    def sizeHint(self):
        return self.__sizehint

    def showEvent(self, event):
        super().showEvent(event)
        self.shown.emit()


Retry = namedtuple("Retry", ["function", "query"])


class SearchDialog(PicardDialog):

    scrolled = pyqtSignal()

    def __init__(self, parent, accept_button_title, show_search=True):
        super().__init__(parent)
        self.search_results = []
        self.table = None
        self.show_search = show_search
        self.search_box = None
        self.setupUi(accept_button_title)
        self.restore_state()
        # self.columns has to be an ordered dict, with column name as keys, and
        # matching label as values
        self.columns = None

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

    def set_table_item(self, row, colname, obj, key, default="", conv=None):
        item = QtWidgets.QTableWidgetItem()
        # QVariant remembers the original type of the data
        # matching comparison operator will be used when sorting
        # get() will return a string, force conversion if asked to
        value = obj.get(key, default)
        if conv is not None:
            value = conv(value)
        item.setData(QtCore.Qt.EditRole, value)
        self.table.setItem(row, self.colpos(colname), item)

    def setupUi(self, accept_button_title):
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_("vertical_layout"))
        if self.show_search:
            self.search_box = SearchBox(self)
            self.search_box.setObjectName(_("search_box"))
            self.verticalLayout.addWidget(self.search_box)
        self.center_widget = QtWidgets.QWidget(self)
        self.center_widget.setObjectName(_("center_widget"))
        self.center_layout = QtWidgets.QVBoxLayout(self.center_widget)
        self.center_layout.setObjectName(_("center_layout"))
        self.center_layout.setContentsMargins(1, 1, 1, 1)
        self.center_widget.setLayout(self.center_layout)
        self.verticalLayout.addWidget(self.center_widget)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
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
        self.table.setSortingEnabled(True)
        if sort_column:
            self.table.sortItems(self.colpos(sort_column), sort_order)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

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

    def accept(self):
        if self.table:
            row = self.table.selectionModel().selectedRows()[0].row()
            self.accept_event(row)
        self.save_state()
        QtWidgets.QDialog.accept(self)

    def reject(self):
        self.save_state()
        QtWidgets.QDialog.reject(self)

    def restore_state(self):
        size = config.persist[self.dialog_window_size]
        if size:
            self.resize(size)
        if self.show_search:
            self.search_box.restore_checkbox_state()
        log.debug("restore_state: %s" % self.dialog_window_size)

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
        config.persist[self.dialog_window_size] = self.size()
        log.debug("save_state: %s" % self.dialog_window_size)

    def save_table_header_state(self):
        state = self.table.horizontalHeader().saveState()
        config.persist[self.dialog_header_state] = state
        log.debug("save_state: %s" % self.dialog_header_state)

    def search_box_text(self, text):
        if self.search_box:
            self.search_box.search_edit.setText(text)


class TrackSearchDialog(SearchDialog):

    dialog_window_size = "tracksearchdialog_window_size"
    dialog_header_state = "tracksearchdialog_header_state"

    options = [
        config.Option("persist", dialog_window_size, QtCore.QSize(720, 360)),
        config.Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, parent):
        super().__init__(
            parent,
            accept_button_title=_("Load into Picard"))
        self.file_ = None
        self.setWindowTitle(_("Track Search Results"))
        self.columns = [
            ('name',    _("Name")),
            ('length',  _("Length")),
            ('artist',  _("Artist")),
            ('release', _("Release")),
            ('date',    _("Date")),
            ('country', _("Country")),
            ('type',    _("Type")),
            ('score',   _("Score")),
        ]

    def search(self, text):
        """Perform search using query provided by the user."""
        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        self.show_progress()
        self.tagger.mb_api.find_tracks(self.handle_reply,
                                       query=text,
                                       search=True,
                                       limit=QUERY_LIMIT)

    def load_similar_tracks(self, file_):
        """Perform search using existing metadata information
        from the file as query."""
        self.retry_params = Retry(self.load_similar_tracks, file_)
        self.file_ = file_
        metadata = file_.orig_metadata
        query = {
            'track': metadata['title'],
            'artist': metadata['artist'],
            'release': metadata['album'],
            'tnum': metadata['tracknumber'],
            'tracks': metadata['totaltracks'],
            'qdur': string_(metadata.length // 2000),
            'isrc': metadata['isrc'],
        }

        # Generate query to be displayed to the user (in search box).
        # If advanced query syntax setting is enabled by user, display query in
        # advanced syntax style. Otherwise display only track title.
        if config.setting["use_adv_search_syntax"]:
            query_str = ' '.join(['%s:(%s)' % (item, escape_lucene_query(value))
                                  for item, value in query.items() if value])
        else:
            query_str = query["track"]

        query["limit"] = QUERY_LIMIT
        self.search_box_text(query_str)
        self.show_progress()
        self.tagger.mb_api.find_tracks(
            self.handle_reply,
            **query)

    def retry(self):
        self.retry_params.function(self.retry_params.query)

    def handle_reply(self, document, http, error):
        if error:
            self.network_error(http, error)
            return

        try:
            tracks = document['recordings']
        except (KeyError, TypeError):
            self.no_results_found()
            return

        if self.file_:
            sorted_results = sorted(
                (self.file_.orig_metadata.compare_to_track(
                    track,
                    File.comparison_weights)
                 for track in tracks),
                reverse=True,
                key=itemgetter(0))
            tracks = [item[3] for item in sorted_results]

        del self.search_results[:]  # Clear existing data
        self.parse_tracks(tracks)
        self.display_results()

    def display_results(self):
        self.prepare_table()
        for row, obj in enumerate(self.search_results):
            track = obj[0]
            self.table.insertRow(row)
            self.set_table_item(row, 'name',    track, "title")
            self.set_table_item(row, 'length',  track, "~length")
            self.set_table_item(row, 'artist',  track, "artist")
            self.set_table_item(row, 'release', track, "album")
            self.set_table_item(row, 'date',    track, "date")
            self.set_table_item(row, 'country', track, "country")
            self.set_table_item(row, 'type',    track, "releasetype")
            self.set_table_item(row, 'score',   track, "score", conv=int)
        self.show_table(sort_column='score')

    def parse_tracks(self, tracks):
        for node in tracks:
            if "releases" in node:
                for rel_node in node['releases']:
                    track = Metadata()
                    recording_to_metadata(node, track)
                    track['score'] = node['score']
                    release_to_metadata(rel_node, track)
                    rg_node = rel_node['release-group']
                    release_group_to_metadata(rg_node, track)
                    countries = country_list_from_node(rel_node)
                    if countries:
                        track["country"] = ", ".join(countries)
                    self.search_results.append((track, node))
            else:
                # This handles the case when no release is associated with a track
                # i.e. the track is an NAT
                track = Metadata()
                recording_to_metadata(node, track)
                track['score'] = node['score']
                track["album"] = _("Standalone Recording")
                self.search_results.append((track, node))

    def accept_event(self, arg):
        self.load_selection(arg)

    def load_selection(self, row):
        """Load the album corresponding to the selected track.
        If the search is performed for a file, also associate the file to
        corresponding track in the album.
        """

        track, node = self.search_results[row]
        if track.get("musicbrainz_albumid"):
            # The track is not an NAT
            self.tagger.get_release_group_by_id(track["musicbrainz_releasegroupid"]).loaded_albums.add(
                track["musicbrainz_albumid"])
            if self.file_:
                # Search is performed for a file.
                # Have to move that file from its existing album to the new one.
                if isinstance(self.file_.parent, Track):
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
            if self.file_:
                album = self.file_.parent.album
                self.tagger.move_file_to_nat(track["musicbrainz_recordingid"])
                if album._files == 0:
                    self.tagger.remove_album(album)
            else:
                self.tagger.load_nat(track["musicbrainz_recordingid"], node)


class CoverCell:

    def __init__(self, parent, release, row, colname, on_show=None):
        self.parent = parent
        self.release = release
        self.fetched = False
        self.fetch_task = None
        self.row = row
        self.column = self.parent.colpos(colname)
        widget = CoverWidget(self.parent.table)
        if on_show is not None:
            widget.shown.connect(partial(on_show, self))
        self.parent.table.setCellWidget(row, self.column, widget)

    def widget(self):
        if not self.parent.table:
            return None
        return self.parent.table.cellWidget(self.row, self.column)

    def is_visible(self):
        widget = self.widget()
        if not widget:
            return False
        return not widget.visibleRegion().isEmpty()

    def set_pixmap(self, pixmap):
        widget = self.widget()
        if widget:
            widget.set_pixmap(pixmap)

    def not_found(self):
        widget = self.widget()
        if widget:
            widget.not_found()


class AlbumSearchDialog(SearchDialog):

    dialog_window_size = "albumsearchdialog_window_size"
    dialog_header_state = "albumsearchdialog_header_state"

    options = [
        config.Option("persist", dialog_window_size, QtCore.QSize(720, 360)),
        config.Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, parent):
        super().__init__(
            parent,
            accept_button_title=_("Load into Picard"))
        self.cluster = None
        self.setWindowTitle(_("Album Search Results"))
        self.columns = [
            ('name',     _("Name")),
            ('artist',   _("Artist")),
            ('format',   _("Format")),
            ('tracks',   _("Tracks")),
            ('date',     _("Date")),
            ('country',  _("Country")),
            ('labels',   _("Labels")),
            ('catnums',  _("Catalog #s")),
            ('barcode',  _("Barcode")),
            ('language', _("Language")),
            ('type',     _("Type")),
            ('status',   _("Status")),
            ('cover',    _("Cover")),
            ('score',    _("Score")),
        ]
        self.cover_cells = []
        self.fetching = False
        self.scrolled.connect(self.fetch_coverarts)

    def search(self, text):
        """Perform search using query provided by the user."""
        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        self.show_progress()
        self.tagger.mb_api.find_releases(self.handle_reply,
                                         query=text,
                                         search=True,
                                         limit=QUERY_LIMIT)

    def show_similar_albums(self, cluster):
        """Perform search by using existing metadata information
        from the cluster as query."""
        self.retry_params = Retry(self.show_similar_albums, cluster)
        self.cluster = cluster
        metadata = cluster.metadata
        query = {
            "artist": metadata["albumartist"],
            "release": metadata["album"],
            "tracks": string_(len(cluster.files))
        }

        # Generate query to be displayed to the user (in search box).
        # If advanced query syntax setting is enabled by user, display query in
        # advanced syntax style. Otherwise display only album title.
        if config.setting["use_adv_search_syntax"]:
            query_str = ' '.join(['%s:(%s)' % (item, escape_lucene_query(value))
                                  for item, value in query.items() if value])
        else:
            query_str = query["release"]

        query["limit"] = QUERY_LIMIT
        self.search_box_text(query_str)
        self.show_progress()
        self.tagger.mb_api.find_releases(
            self.handle_reply,
            **query)

    def retry(self):
        self.retry_params.function(self.retry_params.query)

    def handle_reply(self, document, http, error):
        if error:
            self.network_error(http, error)
            return

        try:
            releases = document['releases']
        except (KeyError, TypeError):
            self.no_results_found()
            return

        del self.search_results[:]
        self.parse_releases(releases)
        self.display_results()
        self.fetch_coverarts()

    def fetch_coverarts(self):
        if self.fetching:
            return
        self.fetching = True
        for cell in self.cover_cells:
            self.fetch_coverart(cell)
        self.fetching = False

    def fetch_coverart(self, cell):
        """Queue cover art jsons from CAA server for each album in search
        results.
        """
        if cell.fetched:
            return
        if not cell.is_visible():
            return
        cell.fetched = True
        caa_path = "/release/%s" % cell.release["musicbrainz_albumid"]
        cell.fetch_task = self.tagger.webservice.download(
            CAA_HOST,
            CAA_PORT,
            caa_path,
            partial(self._caa_json_downloaded, cell)
        )

    def _caa_json_downloaded(self, cover_cell, data, http, error):
        """Handle json reply from CAA server.
        If server replies without error, try to get small thumbnail of front
        coverart of the release.
        """
        if not self.table:
            return

        cover_cell.fetch_task = None

        if error:
            cover_cell.not_found()
            return

        try:
            caa_data = load_json(data)
        except ValueError:
            cover_cell.not_found()
            return

        front = None
        for image in caa_data["images"]:
            if image["front"]:
                front = image
                break

        if front:
            url = front["thumbnails"]["small"]
            coverartimage = CaaThumbnailCoverArtImage(url=url)
            cover_cell.fetch_task = self.tagger.webservice.download(
                coverartimage.host,
                coverartimage.port,
                coverartimage.path,
                partial(self._cover_downloaded, cover_cell),
            )
        else:
            cover_cell.not_found()

    def _cover_downloaded(self, cover_cell, data, http, error):
        """Handle cover art query reply from CAA server.
        If server returns the cover image successfully, update the cover art
        cell of particular release.

        Args:
            row -- Album's row in results table
        """
        if not self.table:
            return

        cover_cell.fetch_task = None

        if error:
            cover_cell.not_found()
        else:
            pixmap = QtGui.QPixmap()
            try:
                pixmap.loadFromData(data)
                cover_cell.set_pixmap(pixmap)
            except Exception as e:
                cover_cell.not_found()
                log.error(e)

    def fetch_cleanup(self):
        for cell in self.cover_cells:
            if cell.fetch_task is not None:
                log.debug("Removing cover art fetch task for %s",
                          cell.release['musicbrainz_albumid'])
                self.tagger.webservice.remove_task(cell.fetch_task)

    def closeEvent(self, event):
        if self.cover_cells:
            self.fetch_cleanup()
        super().closeEvent(event)

    def parse_releases(self, releases):
        for node in releases:
            release = Metadata()
            release_to_metadata(node, release)
            release['score'] = node['score']
            rg_node = node['release-group']
            release_group_to_metadata(rg_node, release)
            if "media" in node:
                media = node['media']
                release["format"] = media_formats_from_node(media)
                release["tracks"] = node['track-count']
            countries = country_list_from_node(node)
            if countries:
                release["country"] = ", ".join(countries)
            self.search_results.append(release)

    def display_results(self):
        self.prepare_table()
        self.cover_cells = []
        for row, release in enumerate(self.search_results):
            self.table.insertRow(row)
            self.set_table_item(row, 'name',     release, "album")
            self.set_table_item(row, 'artist',   release, "albumartist")
            self.set_table_item(row, 'format',   release, "format")
            self.set_table_item(row, 'tracks',   release, "tracks")
            self.set_table_item(row, 'date',     release, "date")
            self.set_table_item(row, 'country',  release, "country")
            self.set_table_item(row, 'labels',   release, "label")
            self.set_table_item(row, 'catnums',  release, "catalognumber")
            self.set_table_item(row, 'barcode',  release, "barcode")
            self.set_table_item(row, 'language', release, "~releaselanguage")
            self.set_table_item(row, 'type',     release, "releasetype")
            self.set_table_item(row, 'status',   release, "releasestatus")
            self.set_table_item(row, 'score',    release, "score", conv=int)
            self.cover_cells.append(CoverCell(self, release, row, 'cover',
                                              on_show=self.fetch_coverart))
        self.show_table(sort_column='score')

    def accept_event(self, arg):
        self.load_selection(arg)

    def load_selection(self, row):
        release = self.search_results[row]
        self.tagger.get_release_group_by_id(
            release["musicbrainz_releasegroupid"]).loaded_albums.add(
                release["musicbrainz_albumid"])
        album = self.tagger.load_album(release["musicbrainz_albumid"])
        if self.cluster:
            files = self.tagger.get_files_from_objects([self.cluster])
            self.tagger.move_files_to_album(files, release["musicbrainz_albumid"],
                                            album)


class ArtistSearchDialog(SearchDialog):

    dialog_window_size = "artistsearchdialog_window_size"
    dialog_header_state = "artistsearchdialog_header_state"

    options = [
        config.Option("persist", dialog_window_size, QtCore.QSize(720, 360)),
        config.Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, parent):
        super().__init__(
            parent,
            accept_button_title=_("Show in browser"))
        self.setWindowTitle(_("Artist Search Dialog"))
        self.columns = [
            ('name',        _("Name")),
            ('type',        _("Type")),
            ('gender',      _("Gender")),
            ('area',        _("Area")),
            ('begindate',   _("Begin")),
            ('beginarea',   _("Begin Area")),
            ('enddate',     _("End")),
            ('endarea',     _("End Area")),
            ('score',       _("Score")),
        ]

    def search(self, text):
        self.retry_params = (self.search, text)
        self.search_box_text(text)
        self.show_progress()
        self.tagger.mb_api.find_artists(self.handle_reply,
                                        query=text,
                                        search=True,
                                        limit=QUERY_LIMIT)

    def retry(self):
        self.retry_params[0](self.retry_params[1])

    def handle_reply(self, document, http, error):
        if error:
            self.network_error(http, error)
            return

        try:
            artists = document['artists']
        except (KeyError, TypeError):
            self.no_results()
            return

        del self.search_results[:]
        self.parse_artists(artists)
        self.display_results()

    def parse_artists(self, artists):
        for node in artists:
            artist = Metadata()
            artist_to_metadata(node, artist)
            artist['score'] = node['score']
            self.search_results.append(artist)

    def display_results(self):
        self.prepare_table()
        for row, artist in enumerate(self.search_results):
            self.table.insertRow(row)
            self.set_table_item(row, 'name',      artist, "name")
            self.set_table_item(row, 'type',      artist, "type")
            self.set_table_item(row, 'gender',    artist, "gender")
            self.set_table_item(row, 'area',      artist, "area")
            self.set_table_item(row, 'begindate', artist, "begindate")
            self.set_table_item(row, 'beginarea', artist, "beginarea")
            self.set_table_item(row, 'enddate',   artist, "enddate")
            self.set_table_item(row, 'endarea',   artist, "endarea")
            self.set_table_item(row, 'score',     artist, "score", conv=int)
        self.show_table(sort_column='score')

    def accept_event(self, row):
        self.load_in_browser(row)

    def load_in_browser(self, row):
        self.tagger.search(self.search_results[row]["musicbrainz_artistid"], "artist")
