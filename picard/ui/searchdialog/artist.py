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

from PyQt5 import QtCore
from picard import config
from picard.mbjson import artist_to_metadata
from picard.metadata import Metadata
from picard.const import QUERY_LIMIT
from picard.ui.searchdialog import SearchDialog, Retry, BY_NUMBER


class ArtistSearchDialog(SearchDialog):

    dialog_header_state = "artistsearchdialog_header_state"

    options = [
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
        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        self.show_progress()
        self.tagger.mb_api.find_artists(self.handle_reply,
                                        query=text,
                                        search=True,
                                        limit=QUERY_LIMIT)

    def retry(self):
        self.retry_params.function(self.retry_params.query)

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
            self.set_table_item(row, 'score',     artist, "score", sort=BY_NUMBER)
        self.show_table(sort_column='score')

    def accept_event(self, row):
        self.load_in_browser(row)

    def load_in_browser(self, row):
        self.tagger.search(self.search_results[row]["musicbrainz_artistid"], "artist")
