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
        #obj can be a track/file object
        PicardDialog.__init__(self, parent)
        self.selected_object = None
        self.setupUi()
        metadata = obj.metadata
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
        self.tracksTable = QtGui.QTableWidget(0, 5)
        self.tracksTable.setHorizontalHeaderLabels([_("Name"), _("Length"),
            _("Artist"), _("Release"), _("Type")])
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
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

    def load_selection(self):
        self

    def show_tracks(self, obj, document, http, error):
        try:
            tracks = document.metadata[0].recording_list[0].recording
        except (AttributeError, IndexError):
            tracks = None

        sorted_data = sorted((obj.metadata.compare_to_track(
            track, File.comparison_weights) for track in tracks),
            reverse=True, key=itemgetter(0))
        #Value returned by `compare_to_track` is of type tuple
        #(similarity, release_group, release, track)

        tracks = [item[3] for item in sorted_data]

        def insert_values_in_row(row, values):
            self.tracksTable.insertRow(row)
            item = QtGui.QTableWidgetItem
            for i in range(self.tracksTable.columnCount()):
                self.tracksTable.setItem(row, i, item(values[i]))

        for row, track in enumerate(tracks):
            title = track.title[0].text
            artist = artist_credit_from_node(track.artist_credit[0])[0]

            try:
                length = format_time(track.length[0].text)
            except AttributeError:
                length = ""

            releases = track.release_list[0].release
            for release in releases:
                release_title = release.title[0].text
                try:
                    release_type = release.release_group[0].type
                except AttributeError:
                    release_type = ""
                insert_values_in_row(row, (title, length, artist, release_title, release_type))
