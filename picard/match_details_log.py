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

from enum import Enum
import numbers
import traceback

from picard import log


__all_file_result_selected_entry_nbr = {}  # dictionary of File name and selected_entry
__all_file_match_dtls = {}  # dictionary of File name and match detail entries associated with it.
__cur_file = None


def set_cur_file(p_file):
    """ set current file we are processing

    Which file is currently being processed and we want to associate log calls to.
    There are better/OO ways to do this, but we don't want to be too intrusive to the existing code flow
    """
    global __cur_file
    __cur_file = p_file


def set_file_result_selected_entry_nbr(p_filename, p_selected_entry_nbr):
    """ Sets the result selected_entry_nbr associated with this file

    This is the entry user last chose from the Match Dialog
    """
    if p_selected_entry_nbr is not None:
        global __all_file_result_selected_entry_nbr
        __all_file_result_selected_entry_nbr[p_filename] = p_selected_entry_nbr


def get_file_result_selected_entry_nbr(filename):
    return __all_file_result_selected_entry_nbr.get(filename, -1)


def get_match_dtls(filename):
    return __all_file_match_dtls.get(filename)


def get_all_match_dtls():
    return __all_file_match_dtls


def can_get_match_dtls(filename):
    return filename in __all_file_match_dtls


def add_match_dtl_entry(match_dtl_entry):

    # Only log if we are being called for a file comparison (AcoustId Scan or Lookup CD) not track comparison (Search Similiar)
    global __cur_file
    if __cur_file is None:
        return

    log.debug("MATCH: %s", str(match_dtl_entry))

    match_dtl_entries = __all_file_match_dtls.get(__cur_file.filename, [])

    match_dtl_entries.append(match_dtl_entry)
    __all_file_match_dtls[__cur_file.filename] = match_dtl_entries


class MatchDetailEntryType(Enum):
    candidate = N_('Recording candidate release score')
    selection = N_('Recording selection score')
    final = N_('Final Match')

    def __str__(self):
        return str(self.value)


class MatchDtlEntry:
    """matching/scoring info for a single track in list of results

    When we get data back from AcoustID or MusicBrainz Picard iterates over the possible matches and has to pick one.
    It does that by scoring each resulting track.
    This class holds the information of each track and its associated scoring info
    For purposes of logging and displaying in dialog.
    """

    hdr_tsv = ("nbr\tmsg\tis_better\tsimilarity\tresult_id\t"
               "recording_id\trec_title\trec_len\trec_src_cnt\trec_artist\t"
               "relgrp_id\trelgrp_title\tprim-type\tsec-type\t"
               "rel_id\tcountry\tdate\t"
               "media_fmt\tmed_pos\tmed_tot_cnt\t"
               "track_id\ttrk_pos\tmedia_trk_cnt\trel_tot_trk_cnt\t"
               "Score components: parts\tScore components: release parts\trecording_base_score")

    def __init__(self, match_dtl_entry_type, track, release, parts=None, release_parts=None, recording_base_score=-1.0, similarity=0.0, is_new=False):
        try:
            if parts is None:
                parts = []
            if release_parts is None:
                release_parts = ""

            self.match_dtl_entry_type = match_dtl_entry_type
            self.is_new_str = " **NEW-BEST**" if is_new else " "

            self.acoust_id = track.get('acoustid', '')
            self.rec_id = track.get('id')
            self.rec_title = track.get('title', '')
            self.rec_src_cnt = track.get('sources', -1)
            self.rec_artist = track['artist-credit'][0]['name'] if 'artist-credit' in track else ''
            self.rec_len_ms = track.get('length', 0)
            self.rec_len_str = "{min:02d}:{sec:02d}".format(min=((int)(self.rec_len_ms / 1000.0 / 60.0)), sec=((int)((self.rec_len_ms / 1000.0) % 60))) if isinstance(self.rec_len_ms, numbers.Number) else 0

            if release is None:
                self.rg_id = self.rg_title = self.rg_pri_type = self.rg_sec_type = self.rel_id = self.rel_ctry = self.rel_dt = self.med_fmt = self.trk_id = ""
                self.med_tot_cnt = self.rel_tot_trk_cnt = self.med_pos = self.med_trk_cnt = self.trk_pos = 0
            else:
                self.rg_id = release['release-group'].get('id', "")
                self.rg_title = release.get('title', '')
                self.rg_pri_type = release['release-group'].get('primary-type', '')
                self.rg_sec_type = str(release['release-group'].get('secondary-types', ''))

                self.rel_id = release['id']
                self.rel_ctry = release.get('country', 'no-ctry')

                if 'date' in release:
                    dt = release['date']
                    if isinstance(dt, dict):
                        if 'year' in dt:
                            self.rel_dt = "%4d" % dt.get('year', 0)
                        if 'month' in dt:
                            self.rel_dt += "-%02d" % dt.get('month', 0)
                        if 'day' in dt:
                            self.rel_dt += "-%02d" % dt.get('day', 0)
                    else:
                        self.rel_dt = dt
                else:
                    self.rel_dt = ""

                self.med_tot_cnt = release.get('medium-count', 0)
                self.rel_tot_trk_cnt = release.get('track-count', 0)

                if 'media' in release:
                    medium = release['media'][0]
                    self.med_fmt = medium.get('format', "")
                    self.med_pos = medium.get('position', 0)
                    self.med_trk_cnt = medium.get('track-count', 0)
                    self.trk_pos = medium['track'][0].get('position', 0) if 'track' in medium and len(medium['track']) >= 1 else 0
                    self.trk_id = medium['track'][0].get('id', '') if 'track' in medium and len(medium['track']) >= 1 else ""
                else:
                    self.med_fmt = ""
                    self.med_pos = 0
                    self.med_trk_cnt = 0
                    self.trk_pos = 0
                    self.trk_id = ""

            self.parts = str(parts)
            self.release_parts = str(release_parts)
            self.recording_base_score = recording_base_score
            self.similarity = similarity

            self.__fmt_as_tsv()
            self.__fmt_with_labels()

            add_match_dtl_entry(self)

        except (KeyError):
            log.error(traceback.format_exc())

    def __str__(self):
        return self.fmtd_with_labels

    def __fmt_as_tsv(self):
        fmt = ("{m.match_dtl_entry_type:s}\t"
               "{m.is_new_str:s}\t"
               "{m.similarity:.4f}\t"
               "{m.acoust_id:s}\t"
               "{m.rec_id:s}\t"
               "{m.rec_title:s}\t"
               "{m.rec_len_str:s}\t"
               "{m.rec_src_cnt:3d}\t"
               "{m.rec_artist:s}\t"
               "{m.rg_id:s}\t"
               "{m.rg_title:s}\t"
               "{m.rg_pri_type:s}\t"
               "{m.rg_sec_type:s}\t"
               "{m.rel_id:s}\t"
               "{m.rel_ctry:s}\t"
               "{m.rel_dt:s}\t"
               "{m.med_fmt:s}\t"
               "{m.med_pos:2d}\t"
               "{m.med_tot_cnt:2d}\t"
               "{m.trk_id:s}\t"
               "{m.trk_pos:2d}\t"
               "{m.med_trk_cnt:2d}\t"
               "{m.rel_tot_trk_cnt:2d}\t"
               "{m.parts:s}\t"
               "{m.release_parts:s}\t"
               "{m.recording_base_score:5.3f}")

        self.fmtd_as_tsv = fmt.format(m=self)

    def __fmt_with_labels(self):
        fmt = ('{m.match_dtl_entry_type:47s}\t'
               '{m.is_new_str:13s},\t'
               'similarity:{m.similarity:.4f},\t'
               'result_id:{m.acoust_id:s},\t'
               'recording_id:{m.rec_id:s},\t'
               'rec_title:{m.rec_title:50s},\t'
               'rec_len:{m.rec_len_str:s},\t'
               'rec_src_cnt:{m.rec_src_cnt:3d},\t'
               'rec_artist:{m.rec_artist:s},\t'
               'release_group_id:{m.rg_id:s},\t'
               'relgrp_title:{m.rg_title:50s},\t'
               'prim-type:{m.rg_pri_type:10s},\t'
               'sec-type:{m.rg_sec_type:s},\t'
               'rel_id:{m.rel_id:s},\t'
               'country:{m.rel_ctry:7s},\t'
               'dt:{m.rel_dt:10s},\t'
               'media_fmt:{m.med_fmt:15s},\t{m.med_pos:2d}\t/\t{m.med_tot_cnt:2d}\t'
               'track id:{m.trk_id:s},\t#:\t{m.trk_pos:2d}\t/\t{m.med_trk_cnt:2d}\t/\t{m.rel_tot_trk_cnt:2d},\t'
               'Score components:'
               '(parts:{m.parts:s}\t+\t'
               'release parts:{m.release_parts:s})\t*\t'
               'recording_base_score:{m.recording_base_score:5.3f})')

        self.fmtd_with_labels = fmt.format(m=self)
