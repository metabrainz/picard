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

from PyQt4 import QtGui
from operator import itemgetter
from functools import partial
from picard.file import File
from picard.ui import PicardDialog
from picard.ui.util import StandardButton
from picard.util import format_time
from picard.mbxml import artist_credit_from_node

class SearchDialog(PicardDialog):

    def __init__(self, obj, parent=None):
        PicardDialog.__init__(self, parent)
        self.obj = obj
        self.search_results = []
        self.setupUi()
        metadata = obj.orig_metadata
        self.tagger.xmlws.find_tracks(partial(self.show_tracks, obj),
                track=metadata['title'],
                artist=metadata['artist'],
                release=metadata['tracknumber'],
                tnum=metadata['totaltracks'],
                tracks=metadata['totaltracks'],
                qdur=str(metadata.length / 2000),
                isrc=metadata['isrc'],
                limit=25)

    def setupUi(self):
        self.setObjectName(_("SearchDialog"))
        self.setWindowTitle(_("Track Search Results"))
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_("verticalLayout"))
        self.tracksTable = QtGui.QTableWidget(0, 7)
        self.tracksTable.setHorizontalHeaderLabels([_("Name"), _("Length"),
            _("Artist"), _("Release"), _("Date"), _("Country"), _("Type")])
        self.tracksTable.setSelectionMode(
                QtGui.QAbstractItemView.SingleSelection)
        self.tracksTable.setSelectionBehavior(
                QtGui.QAbstractItemView.SelectRows)
        self.tracksTable.setEditTriggers(
                QtGui.QAbstractItemView.NoEditTriggers)
        self.verticalLayout.addWidget(self.tracksTable)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(
                StandardButton(StandardButton.OK),
                QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(
                StandardButton(StandardButton.CANCEL),
                QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.load_selection)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def load_selection(self):
        sel_row = self.tracksTable.selectionModel().selectedRows()[0].row()
        track_id, release_id, rg_id = self.search_results[sel_row][:3]
        if release_id:
            album = self.obj.parent.album
            self.tagger.get_release_group_by_id(rg_id).loaded_albums.add(release_id)
            self.tagger.move_file_to_track(self.obj, release_id, track_id)
            self.tagger.remove_album(album)
        self.accept()

    def parse_recording_node(self, track):
        result = []
        rec_id = track.id
        rec_title = track.title[0].text
        artist = artist_credit_from_node(track.artist_credit[0])[0]
        try:
            length = format_time(track.length[0].text)
        except AttributeError:
            length = ""
        if "release_list" in track.children and "release" in \
                track.release_list[0].children:
            releases = track.release_list[0].release
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

                result.append((rec_id, rel_id, rg_id, rec_title, artist,
                    length, rel_title, date, country, types))
        else:
            result.append((rec_id, "", "", rec_title, artist, length, "", "",
                "", ""))
        self.search_results.extend(result)
        return result

    def show_tracks(self, obj, document, http, error):
        try:
            tracks = document.metadata[0].recording_list[0].recording
        except (AttributeError, IndexError):
            tracks = []

        cur_row = 0
        for track in tracks:
            result = self.parse_recording_node(track)
            for item in result:
                self.tracksTable.insertRow(cur_row)
                title, artist, length, release, date, country, type = item[3:]
                table_item = QtGui.QTableWidgetItem
                self.tracksTable.setItem(cur_row, 0, table_item(title))
                self.tracksTable.setItem(cur_row, 1, table_item(length))
                self.tracksTable.setItem(cur_row, 2, table_item(artist))
                self.tracksTable.setItem(cur_row, 3, table_item(release))
                self.tracksTable.setItem(cur_row, 4, table_item(date))
                self.tracksTable.setItem(cur_row, 5, table_item(country))
                self.tracksTable.setItem(cur_row, 6, table_item(type))
                cur_row += 1
