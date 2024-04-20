# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018 Antonio Larrosa
# Copyright (C) 2018-2021, 2023-2024 Laurent Monin
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


from PyQt6 import QtCore

from picard.config import (
    Option,
    get_config,
)
from picard.file import FILE_COMPARISON_WEIGHTS
from picard.mbjson import (
    countries_from_node,
    recording_to_metadata,
    release_group_to_metadata,
    release_to_metadata,
)
from picard.metadata import Metadata
from picard.track import Track
from picard.util import (
    countries_shortlist,
    sort_by_similarity,
)
from picard.webservice.api_helpers import build_lucene_query

from picard.ui.searchdialog import (
    Retry,
    SearchDialog,
)


class TrackSearchDialog(SearchDialog):

    dialog_header_state = 'tracksearchdialog_header_state'

    options = [
        Option('persist', dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, parent, force_advanced_search=None):
        super().__init__(
            parent,
            accept_button_title=_("Load into Picard"),
            search_type='track',
            force_advanced_search=force_advanced_search)
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
        config = get_config()
        self.tagger.mb_api.find_tracks(self.handle_reply,
                                       query=text,
                                       search=True,
                                       advanced_search=self.use_advanced_search,
                                       limit=config.setting['query_limit'])

    def show_similar_tracks(self, file_):
        """Perform search using existing metadata information
        from the file as query."""
        self.file_ = file_
        metadata = file_.orig_metadata
        query = {
            'track': metadata['title'],
            'artist': metadata['artist'],
            'release': metadata['album'],
            'tnum': metadata['tracknumber'],
            'tracks': metadata['totaltracks'],
            'qdur': str(metadata.length // 2000),
            'isrc': metadata['isrc'],
        }

        # If advanced query syntax setting is enabled by user, query in
        # advanced syntax style. Otherwise query only track title.
        if self.use_advanced_search:
            query_str = build_lucene_query(query)
        else:
            query_str = query['track']
        self.search(query_str)

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
            metadata = self.file_.orig_metadata
            candidates = (
                metadata.compare_to_track(track, FILE_COMPARISON_WEIGHTS)
                for track in tracks
            )
            tracks = (result.track for result in sort_by_similarity(candidates))

        del self.search_results[:]  # Clear existing data
        self.parse_tracks(tracks)
        self.display_results()

    def display_results(self):
        self.prepare_table()
        for row, obj in enumerate(self.search_results):
            track = obj[0]
            self.table.insertRow(row)
            self.set_table_item(row, 'name',    track, 'title')
            self.set_table_item(row, 'length',  track, '~length', sortkey=track.length)
            self.set_table_item(row, 'artist',  track, 'artist')
            self.set_table_item(row, 'release', track, 'album')
            self.set_table_item(row, 'date',    track, 'date')
            self.set_table_item(row, 'country', track, 'country')
            self.set_table_item(row, 'type',    track, 'releasetype')
            self.set_table_item(row, 'score',   track, 'score')
        self.show_table(sort_column='score')

    def parse_tracks(self, tracks):
        for node in tracks:
            if 'releases' in node:
                for rel_node in node['releases']:
                    track = Metadata()
                    recording_to_metadata(node, track)
                    track['score'] = node['score']
                    release_to_metadata(rel_node, track)
                    rg_node = rel_node['release-group']
                    release_group_to_metadata(rg_node, track)
                    countries = countries_from_node(rel_node)
                    if countries:
                        track['country'] = countries_shortlist(countries)
                    self.search_results.append((track, node))
            else:
                # This handles the case when no release is associated with a track
                # i.e. the track is an NAT
                track = Metadata()
                recording_to_metadata(node, track)
                track['score'] = node['score']
                track["album"] = _("Standalone Recording")
                self.search_results.append((track, node))

    def accept_event(self, rows):
        for row in rows:
            self.load_selection(row)

    def _load_selection_non_nat(self, track, node):
        recording_id = track['musicbrainz_recordingid']
        album_id = track['musicbrainz_albumid']
        releasegroup_id = track['musicbrainz_releasegroupid']

        self.tagger.get_release_group_by_id(releasegroup_id).loaded_albums.add(album_id)
        if self.file_:
            # Search is performed for a file.
            if isinstance(self.file_.parent, Track):
                # Have to move that file from its existing album to the new one.
                album = self.file_.parent.album
                self.tagger.move_file_to_track(self.file_, album_id, recording_id)
                if album.get_num_total_files() == 0:
                    # Remove album if it has no more files associated
                    self.tagger.remove_album(album)
            else:
                # No parent album
                self.tagger.move_file_to_track(self.file_, album_id, recording_id)
        else:
            # No files associated. Just a normal search.
            self.tagger.load_album(album_id)

    def _load_selection_nat(self, track, node):
        recording_id = track['musicbrainz_recordingid']

        if self.file_:
            # Search is performed for a file.
            if getattr(self.file_.parent, 'album', None):
                # Have to move that file from its existing album to NAT.
                album = self.file_.parent.album
                self.tagger.move_file_to_nat(self.file_, recording_id, node)
                if album.get_num_total_files() == 0:
                    self.tagger.remove_album(album)
            else:
                # No parent album
                self.tagger.move_file_to_nat(self.file_, recording_id, node)
        else:
            # No files associated. Just a normal search
            self.tagger.load_nat(recording_id, node)

    def load_selection(self, row):
        """Load the album corresponding to the selected track.
        If the search is performed for a file, also associate the file to
        corresponding track in the album.
        """

        track, node = self.search_results[row]
        if track.get('musicbrainz_albumid'):
            # The track is not an NAT
            self._load_selection_non_nat(track, node)
        else:
            # Track is a Non Album Track (NAT)
            self._load_selection_nat(track, node)
