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

from operator import itemgetter

from PyQt5 import QtCore

from picard import config
from picard.const import QUERY_LIMIT
from picard.file import File
from picard.mbjson import (
    country_list_from_node,
    recording_to_metadata,
    release_group_to_metadata,
    release_to_metadata,
)
from picard.metadata import Metadata
from picard.track import Track
from picard.webservice.api_helpers import escape_lucene_query

from picard.ui.searchdialog import (
    BY_DURATION,
    BY_NUMBER,
    Retry,
    SearchDialog,
)


class TrackSearchDialog(SearchDialog):

    dialog_header_state = "tracksearchdialog_header_state"

    options = [
        config.Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, parent):
        super().__init__(
            parent,
            accept_button_title=_("Load into Picard"),
            search_type="track")
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
            'qdur': str(metadata.length // 2000),
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
            self.set_table_item(row, 'length',  track, "~length", sort=BY_DURATION)
            self.set_table_item(row, 'artist',  track, "artist")
            self.set_table_item(row, 'release', track, "album")
            self.set_table_item(row, 'date',    track, "date")
            self.set_table_item(row, 'country', track, "country")
            self.set_table_item(row, 'type',    track, "releasetype")
            self.set_table_item(row, 'score',   track, "score", sort=BY_NUMBER)
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
            if self.file_ and getattr(self.file_.parent, 'album', None):
                album = self.file_.parent.album
                self.tagger.move_file_to_nat(self.file_, track["musicbrainz_recordingid"], node)
                if album._files == 0:
                    self.tagger.remove_album(album)
            else:
                self.tagger.load_nat(track["musicbrainz_recordingid"], node)
                self.tagger.move_file_to_nat(self.file_, track["musicbrainz_recordingid"], node)
