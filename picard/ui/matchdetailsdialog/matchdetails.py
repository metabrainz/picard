# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2020 Ray Bouchard
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

import os
from pathlib import Path
import re
import traceback

from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog

from picard import (
    PICARD_VERSION_STR,
    config,
    log,
    match_details_log,
)
from picard.const import (
    ACOUSTID_HOST,
    ACOUSTID_KEY,
)
from picard.match_details_log import MatchDetailEntryType
from picard.track import Track

from picard.ui.matchdetailsdialog import MatchDetailsDialogBase


class MatchDetailsDialog(MatchDetailsDialogBase):

    dialog_header_state = "matchdetailsdialog_header_state"
    current_file = ""

    options = [
        config.Option("persist", dialog_header_state, QtCore.QByteArray())
    ]

    def __init__(self, parent):
        """ Initialize the dialog box object with information about itself, including the columns in the table/grid."""
        super().__init__(parent)
        self.file_ = None
        self.setWindowTitle(_("Match Details"))
        self.columns = [
            ('nbr',                  "_Log\nSeq"),
            ('match_dtl_entry_type', "_Entry Type"),
            ('is_new',               "_Better?"),
            ('rec_id',               "_Recording ID"),
            ('rec_title',            "Recording Title"),
            ('rec_len',              "Recording\nLength"),
            ('rec_artist',           "Recording\nArtist"),
            ('rg_id',                "_Release Group ID"),
            ('rg_title',             "Release Group\nTitle"),
            ('rg_pri_type',          "Release Group\nPrimary Type"),
            ('rg_sec_type',          "Release Group\nSecondary Types"),
            ('rel_id',               "_Release ID"),
            ('rel_ctry',             "Release\nCountry"),
            ('rel_dt',               "Release\nDate"),
            ('med_fmt',              "Medium\nFormat"),
            ('med_pos',              "Medium\nPosition"),
            ('med_tot_cnt',          "Medium\nCount"),
            ('trk_id',               "_Track ID"),
            ('trk_pos',              "Track\nPosition"),
            ('med_trk_cnt',          "Medium\nTrack\nCount"),
            ('rel_tot_trk_cnt',      "Release\nTotal Track\nCount"),
            ('parts',                "_Scoring Parts"),
            ('release_parts',        "_Scoring Release Parts"),
            ('recording_base_score', "_Recording\nBase Score\n(Sources Ratio)"),
            ('acoust_id',            "AcoustId ID"),
            ('rec_src_cnt',          "AcoustId\nSource\nCount"),
            ('similarity',           "Similarity")
        ]

    def load_match_details(self, track, file_):
        """ Retrieves data and loads it to the screen/dialog box """
        if file_ is not None:
            selected_entry_nbr = match_details_log.get_file_result_selected_entry_nbr(file_.filename)
            self.set_input_filename_lbl(file_.filename)

            # NOTE: some of the values, like meta, are not exposed as constants
            duration = getattr(file_, 'acoustid_length', '')
            fingerprint = getattr(file_, 'acoustid_fingerprint', None)

            fingerprint_lkp_url = None
            if fingerprint is not None:
                fingerprint_lkp_url = ("https://" + ACOUSTID_HOST + "/v2/lookup"
                                       + "?meta=recordings%20releasegroups%20releases%20tracks%20compress%20sources"
                                       + "&fingerprint=" + fingerprint
                                       + "&duration=" + str(duration)
                                       + "&client=" + ACOUSTID_KEY
                                       + "&clientversion=" + PICARD_VERSION_STR
                                       + "&format=json")
            self.set_acoustid_lookup_url_edit(fingerprint_lkp_url)

        self.current_file = file_
        self.prepare_table()
        self.entries = match_details_log.get_match_dtls(file_.filename)
        display_row_nbr = -1
        selected_row_nbr = -1

        regex = re.compile(r"[\[\]]")
        for entry_nbr, entry in enumerate(self.entries):
            if entry.match_dtl_entry_type == MatchDetailEntryType.candidate:
                display_row_nbr += 1
                if entry_nbr == selected_entry_nbr:
                    selected_row_nbr = display_row_nbr

                secondary_type_csv = str(entry.rg_sec_type)
                if secondary_type_csv is not None:
                    secondary_type_csv = regex.sub("", secondary_type_csv)

                self.table.insertRow(display_row_nbr)
                self.set_table_item_val(display_row_nbr, 'nbr', entry_nbr)
                self.set_table_item_val(display_row_nbr, 'match_dtl_entry_type', entry.match_dtl_entry_type)
                self.set_table_item_val(display_row_nbr, 'is_new', entry.is_new_str)
                self.set_table_item_val(display_row_nbr, 'similarity', "%5.3f" % entry.similarity)
                self.set_table_item_val(display_row_nbr, 'acoust_id', entry.acoust_id)
                self.set_table_item_val(display_row_nbr, 'rec_id', entry.rec_id)
                self.set_table_item_val(display_row_nbr, 'rec_title', entry.rec_title)
                self.set_table_item_val(display_row_nbr, 'rec_len', entry.rec_len_str)
                self.set_table_item_val(display_row_nbr, 'rec_src_cnt', entry.rec_src_cnt)
                self.set_table_item_val(display_row_nbr, 'rec_artist', entry.rec_artist)
                self.set_table_item_val(display_row_nbr, 'rg_id', entry.rg_id)
                self.set_table_item_val(display_row_nbr, 'rg_title', entry.rg_title)
                self.set_table_item_val(display_row_nbr, 'rg_pri_type', entry.rg_pri_type)
                self.set_table_item_val(display_row_nbr, 'rg_sec_type', secondary_type_csv)
                self.set_table_item_val(display_row_nbr, 'rel_id', entry.rel_id)
                self.set_table_item_val(display_row_nbr, 'rel_ctry', entry.rel_ctry)
                self.set_table_item_val(display_row_nbr, 'rel_dt', entry.rel_dt)
                self.set_table_item_val(display_row_nbr, 'med_fmt', entry.med_fmt)
                self.set_table_item_val(display_row_nbr, 'med_pos', entry.med_pos)
                self.set_table_item_val(display_row_nbr, 'med_tot_cnt', entry.med_tot_cnt)
                self.set_table_item_val(display_row_nbr, 'trk_id', entry.trk_id)
                self.set_table_item_val(display_row_nbr, 'trk_pos', entry.trk_pos)
                self.set_table_item_val(display_row_nbr, 'med_trk_cnt', entry.med_trk_cnt)
                self.set_table_item_val(display_row_nbr, 'rel_tot_trk_cnt', entry.rel_tot_trk_cnt)
                self.set_table_item_val(display_row_nbr, 'parts', str(entry.parts))
                self.set_table_item_val(display_row_nbr, 'release_parts', str(entry.release_parts))
                self.set_table_item_val(display_row_nbr, 'recording_base_score', entry.recording_base_score)

        self.show_table(selected_row_nbr=selected_row_nbr, sort_column='similarity', sort_order=QtCore.Qt.DescendingOrder)

    def accept_event(self, selected_rows_user_values):
        if not selected_rows_user_values:
            return

        selected_entry_nbr = selected_rows_user_values[0]
        match_details_log.set_file_result_selected_entry_nbr(self.current_file.filename, selected_entry_nbr)
        self.load_selection(selected_entry_nbr)

    def load_selection(self, entry_nbr):
        """Load the album corresponding to the selected track.

        Allow user to pick from our new screen and use that track instead of one its currently assigned to.
        Based on logic from searchdialog/track.py line 186
        """

        entry = self.entries[entry_nbr]

        if entry.rel_id:
            # The track is not an NAT
            self.tagger.get_release_group_by_id(entry.rg_id).loaded_albums.add(entry.rel_id)

            # Have to move that file from its existing album to the new one.
            if isinstance(self.current_file.parent, Track):
                album = self.current_file.parent.album
                self.tagger.move_file_to_track(self.current_file, entry.rel_id, entry.rec_id)
                if not album._files:
                    # Remove album if it has no more files associated
                    self.tagger.remove_album(album)
            else:
                self.tagger.move_file_to_track(self.current_file, entry.rel_id, entry.rec_id)
        else:
            if self.current_file and getattr(self.current_file.parent, 'album', None):
                album = self.current_file.parent.album
                self.tagger.move_file_to_nat(self.current_file, entry.rec_id, None)
                if album._files == 0:
                    self.tagger.remove_album(album)
            else:
                self.tagger.load_nat(entry.rec_id, None)
                self.tagger.move_file_to_nat(self.current_file, entry.rec_id, None)

        log.debug("using alternative release id:" + entry.rel_id)

    def export_match_dtl_entries_to_file(self):
        """ Export entries to a file that can be viewed in external program
        """
        try:
            # Prompt user for file location to save to
            dir = str(Path.home())
            suggested_file_and_path = os.path.join(dir, "picard_match_results.tsv")
            save_file = QFileDialog.getSaveFileName(None, 'Save File', suggested_file_and_path)
            if save_file[0] == '':
                return
            else:
                filename = save_file[0]

            # Alternatively write to temp dir:
            # filename = tempfile.gettempdir() + os.path.sep + "picard_match_details.tsv"

            with open(filename, "w") as text_file:
                print(match_details_log.MatchDtlEntry.hdr_tsv, file=text_file)

                for row, entry in enumerate(self.entries):
                    output_str = str(row) + "\t" + entry.fmtd_as_tsv + os.linesep
                    text_file.write(output_str)
            log.debug("Wrote file with match details to file:" + text_file.name)
        except IOError:
            filename = ""
            log.error(traceback.format_exc())

        return filename
