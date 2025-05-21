# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2018-2022 Philipp Wolfer
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


from picard.config import get_config
from picard.i18n import N_
from picard.mbjson import artist_to_metadata
from picard.metadata import Metadata

from picard.ui.columns import (
    Column,
    ColumnAlign,
    Columns,
    ColumnSortType,
)
from picard.ui.searchdialog import (
    Retry,
    SearchDialog,
)


class ArtistSearchDialog(SearchDialog):

    dialog_header_state = 'artistsearchdialog_header_state'

    def __init__(self, parent):
        self.columns = Columns((
            Column(N_("Name"), 'name', sort_type=ColumnSortType.NAT, width=150),
            Column(N_("Type"), 'type'),
            Column(N_("Gender"), 'gender'),
            Column(N_("Area"), 'area'),
            Column(N_("Begin"), 'begindate'),
            Column(N_("Begin Area"), 'beginarea'),
            Column(N_("End"), 'enddate'),
            Column(N_("End Area"), 'endarea'),
            Column(N_("Score"), 'score', sort_type=ColumnSortType.NAT, align=ColumnAlign.RIGHT, width=50),
        ), default_width=100)
        super().__init__(
            parent,
            N_("Artist Search Dialog"),
            accept_button_title=N_("Show in browser"),
            search_type='artist')

    def search(self, text):
        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        self.show_progress()
        config = get_config()
        self.tagger.mb_api.find_artists(self.handle_reply,
                                        query=text,
                                        search=True,
                                        advanced_search=self.use_advanced_search,
                                        limit=config.setting['query_limit'])

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
            for pos, c in enumerate(self.columns):
                self.set_table_item_value(row, pos, c, artist)
        self.show_table(sort_column='score')

    def accept_event(self, rows):
        for row in rows:
            self.load_in_browser(row)

    def load_in_browser(self, row):
        self.tagger.search(self.search_results[row]['musicbrainz_artistid'], 'artist')
