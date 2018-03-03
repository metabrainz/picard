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

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from functools import partial
from picard import config, log
from picard.util import load_json
from picard.mbjson import (
    release_to_metadata,
    release_group_to_metadata,
    media_formats_from_node,
    country_list_from_node
)
from picard.metadata import Metadata
from picard.webservice.api_helpers import escape_lucene_query
from picard.const import CAA_HOST, CAA_PORT, QUERY_LIMIT
from picard.coverart.image import CaaThumbnailCoverArtImage
from picard.ui.searchdialog import SearchDialog, Retry, BY_NUMBER


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

    dialog_header_state = "albumsearchdialog_header_state"

    options = [
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
            self.set_table_item(row, 'tracks',   release, "tracks", sort=BY_NUMBER)
            self.set_table_item(row, 'date',     release, "date")
            self.set_table_item(row, 'country',  release, "country")
            self.set_table_item(row, 'labels',   release, "label")
            self.set_table_item(row, 'catnums',  release, "catalognumber")
            self.set_table_item(row, 'barcode',  release, "barcode", sort=BY_NUMBER)
            self.set_table_item(row, 'language', release, "~releaselanguage")
            self.set_table_item(row, 'type',     release, "releasetype")
            self.set_table_item(row, 'status',   release, "releasestatus")
            self.set_table_item(row, 'score',    release, "score", sort=BY_NUMBER)
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
